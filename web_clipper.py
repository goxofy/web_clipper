import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from github import Github
import openai
from notion_client import Client
import telegram
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, Request, Body
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
from pathlib import Path
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import CONFIG  # 添加这行在文件开头
import re
from bs4 import BeautifulSoup  # 添加到导入部分
from fastapi.responses import JSONResponse
import html2text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置 httpx 日志级别为 WARNING，隐藏请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)

# 配置限制
MAX_FILE_SIZE = CONFIG.get('max_file_size', 10 * 1024 * 1024)  # 从配置中获取最大文件大小
#ALLOWED_EXTENSIONS = {'.html', '.htm'}
ALLOWED_EXTENSIONS = set(CONFIG.get('allowed_extensions', ['.html', '.htm']))
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# 替换原来的 API_KEY_NAME 和 api_key_header
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 Bearer 令牌"""
    token = credentials.credentials
    if token != CONFIG.get('api_key'):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

def verify_file(file: UploadFile):
    """验证文件"""
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 检查文件大小
    file.file.seek(0, 2)  # 移到文件末尾
    size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 重置文件指针
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE/1024/1024}MB"
        )

def parse_filename(filename):
    """从文件名解析URL
    filename format: {random_prefix}_url.html (其中url中的/被替换为$)
    """
    try:
        # 移除 .html 后缀
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # 移除随机前缀（如果存在）
        if '_' in name_without_ext:
            name_without_ext = name_without_ext.split('_', 1)[1]
        
        # 恢复URL中的斜杠
        original_url = name_without_ext.replace('$', '/')
        
        logger.info(f"从文件名解析出原始URL: {original_url}")
        return {
            'original_url': original_url
        }
    except Exception as e:
        logger.error(f"解析文件名失败: {str(e)}")
        return {
            'original_url': ''
        }

class WebClipperHandler:
    def __init__(self, config):
        self.config = config
        self.github_client = Github(config['github_token'])
        self.notion_client = Client(auth=config['notion_token'])
        self.telegram_bot = telegram.Bot(token=config['telegram_token'])
        

    async def process_file(self, file_path: Path, original_url: str = ''):
        """处理上传的文件"""
        try:
            logger.info("🔄 开始处理新的网页剪藏...")
            
            # 1. 上传到 GitHub Pages
            filename, github_url = self.upload_to_github(str(file_path))
            logger.info(f"📤 GitHub 上传成功: {github_url}")

            # Github URL 转换为 Markdown
            md_content = self.url2md(github_url)
            
            # 2. 获取页面标题
            title = self.get_page_content_by_md(md_content)
            logger.info(f"📑 页面标题: {title}")
            
            # 如果没有提供原始 URL，则从文件名解析
            if not original_url:
                file_info = parse_filename(filename)
                original_url = file_info['original_url']
            
            # 3. 生成摘要和标签
            summary, tags = self.generate_summary_tags(md_content)
            logger.info(f"📝 摘要: {summary[:100]}...")
            logger.info(f"🏷️ 标签: {', '.join(tags)}")
            
            # 4. 保存到 Notion
            notion_url = self.save_to_notion({
                'title': title,
                'original_url': original_url,
                'snapshot_url': github_url,
                'summary': summary,
                'tags': tags,
                'created_at': time.time()
            })
            logger.info(f"📓 Notion 保存成功")
            
            # 5. 发送 Telegram 通知
            notification = (
                f"✨ 新的网页剪藏\n\n"
                f"📑 {title}\n\n"
                f"📝 {summary}\n\n"
                f"🔗 原始链接：{original_url}\n"
                f"📚 快照链接：{github_url}\n"
                f"📚 Notion笔记: {notion_url}"
            )
            await self.send_telegram_notification(notification)
            
            logger.info("=" * 50)
            logger.info("✨ 网页剪藏处理完成!")
            logger.info(f"📍 原始链接: {original_url}")
            logger.info(f"🔗 GitHub预览: {github_url}")
            logger.info(f"📚 Notion笔记: {notion_url}")
            logger.info("=" * 50)
            
            return {
                "status": "success",
                "github_url": github_url,
                "notion_url": notion_url
            }
            
        except Exception as e:
            error_msg = f"❌ 处理失败: {str(e)}"
            logger.error(error_msg)
            logger.error("=" * 50)
            await self.send_telegram_notification(error_msg)
            raise

    def upload_to_github(self, html_path):
        """上传 HTML 文件到 GitHub Pages"""
        filename = os.path.basename(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        repo = self.github_client.get_repo(self.config['github_repo'])
        file_path = f"clips/{filename}"
        repo.create_file(
            file_path,
            f"Add web clip: {filename}",
            content,
            branch="main"
        )
        
        github_url = f"https://{self.config['github_pages_domain']}/{self.config['github_repo'].split('/')[1]}/clips/{filename}"
        
        # 等待 GitHub Pages 部署
        max_retries = self.config.get('github_pages_max_retries', 60)
        for attempt in range(max_retries):
            try:
              
    def url2md(self, url, max_retries=30):
        """将 URL 转换为 Markdown"""
        try:
            for attempt in range(max_retries):
                try:
                    md_url = f"https://r.jina.ai/{url}"
                    response = requests.get(md_url)
                    if response.status_code == 200:
                        md_content = response.text
                        return md_content
                except Exception:
                    time.sleep(10)
        except Exception:
            md_content = self.get_page_content_by_bs(url)
            return md_content

    def generate_summary_tags(self, content):
        """使用 AI 生成摘要和标签"""
        try:

    def get_page_content_by_md(self, md_content):
        """从 markdown 获取标题"""
        lines = md_content.splitlines()
        for line in lines:
            if line.startswith("Title:"):
                return line.replace("Title:", "").strip()
        return "未知标题"

    def get_page_content_by_bs(self, url, max_retries=60):
        """从部署的页面获取标题和内容"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 获取标题
                    title = None
                    if soup.title:
                        title = soup.title.string
                    if not title and soup.h1:
                        title = soup.h1.get_text(strip=True)
                    if not title:
                        for tag in ['h2', 'h3', 'h4', 'h5', 'h6']:
                            if soup.find(tag):
                                title = soup.find(tag).get_text(strip=True)
                                break

                    # 提取正文内容
                    html2markdown = html2text.HTML2Text()
                    html2markdown.ignore_links = True
                    html2markdown.ignore_images = True
                    content = html2markdown.handle(soup.prettify())
                    
                    return f"Title: {title} \n\n {content}"
                    
                time.sleep(5)
                
            except Exception:
                time.sleep(5)
        
        return os.path.basename(url), ""

    async def send_telegram_notification(self, message):
        """发送 Telegram 通知"""
        await self.telegram_bot.send_message(
            chat_id=self.config['telegram_chat_id'],
            text=message
        )

@limiter.limit("10/minute", key_func=get_remote_address)
async def upload_file(
    request: Request,
    token: str = Depends(verify_token)
):
    """文件上传接口"""
    try:
        form = await request.form()
        original_url = form.get('url', '')
        
        # 获取文件内容
        file = None
        for field_name, field_value in form.items():
            if hasattr(field_value, 'filename') and hasattr(field_value, 'read'):
                file = field_value
                break
        
        if not file:
            raise HTTPException(
                status_code=400,
                detail="No file content found in form data"
            )
        
        filename = file.filename
        content = await file.read()
        
        # 验证和保存文件
        file_ext = Path(filename).suffix.lower()
        if not file_ext:
            filename += '.html'
        elif file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE/1024/1024}MB"
            )
        
        # 保存文件
        safe_filename = f"{secrets.token_hex(8)}_{filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        try:
            result = await handler.process_file(file_path, original_url)
            return result
        finally:
            if file_path.exists():
                file_path.unlink()  # 这里会删除单个处理完的文件
                
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"上传失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def start_server(host="0.0.0.0", port=8000):
    """启动服务器"""
    uvicorn.run(app, host=host, port=port) 
