import os
import time
import requests
from github import Github
import openai
from notion_client import Client
import telegram
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, Request, Body
import uvicorn
import shutil
from pathlib import Path
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import CONFIG  # 添加这行在文件开头
from bs4 import BeautifulSoup  # 添加到导入部分
import html2text
from contextlib import asynccontextmanager
import asyncio
import google.generativeai as genai

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置 httpx 日志级别为 WARNING，隐藏请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)

# 定义全局变量
handler = None
UPLOAD_DIR = Path("uploads")

# 配置限制
MAX_FILE_SIZE = CONFIG.get('max_file_size', 10 * 1024 * 1024)  # 从配置中获取最大文件大小
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
        
        # 配置 AI 服务
        self.ai_provider = config.get('ai_provider', 'openai').lower()
        
        if self.ai_provider == 'azure':
            # Azure OpenAI 配置
            self.client = openai.AzureOpenAI(
                api_key=config['azure_api_key'],
                api_version=config.get('azure_api_version', '2024-02-15-preview'),
                azure_endpoint=config['azure_api_base']
            )
            logger.info(f"使用 Azure OpenAI API: {config['azure_api_base']}")
        elif self.ai_provider == 'deepseek':
            # Deepseek 配置
            self.client = openai.OpenAI(
                api_key=config['deepseek_api_key'],
                base_url=config.get('deepseek_base_url', 'https://api.deepseek.com/v1')
            )
            logger.info(f"使用 Deepseek API: {config['deepseek_base_url']}")
        elif self.ai_provider == 'gemini':
            # Gemini 配置
            genai.configure(api_key=config['gemini_api_key'])
            self.client = genai.GenerativeModel(
                model_name=config.get('gemini_model', 'gemini-1.5-flash')
            )
            logger.info(f"使用 Gemini API")
        else:
            # 标准 OpenAI 配置
            self.client = openai.OpenAI(
                api_key=config['openai_api_key'],
                base_url=config.get('openai_base_url', 'https://api.openai.com/v1')
            )
            logger.info(f"使用 OpenAI API")

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
        max_retries = 5
        retry_delay = 3  # 秒
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for attempt in range(max_retries):
            try:
                repo = self.github_client.get_repo(self.config['github_repo'])
                file_path = f"clips/{filename}"
                
                # 直接创建新文件，因为文件名包含随机前缀，不可能重复
                repo.create_file(
                    file_path,
                    f"Add web clip: {filename}",
                    content,
                    branch="main"
                )
                
                github_url = f"https://{self.config['github_pages_domain']}/{self.config['github_repo'].split('/')[1]}/clips/{filename}"
                logger.info(f"📑 文件已上传到 GitHub: {github_url}")
                
                # 等待 GitHub Pages 部署
                max_deploy_retries = self.config.get('github_pages_max_retries', 60)
                deploy_retry_interval = 5  # 秒
                total_wait_time = max_deploy_retries * deploy_retry_interval
                
                logger.info(f"⏳ 等待 GitHub Pages 部署 (最长等待 {total_wait_time} 秒)")
                start_time = time.time()
                
                # 使用同步方式检查部署
                session = requests.Session()
                for deploy_attempt in range(max_deploy_retries):
                    try:
                        response = session.get(
                            github_url,
                            timeout=10,
                            verify=True,
                            headers={
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            }
                        )
                        
                        if response.status_code == 200:
                            elapsed_time = time.time() - start_time
                            logger.info(f"✅ GitHub Pages 部署完成! 耗时: {elapsed_time:.1f} 秒")
                            return filename, github_url
                        
                        # 每30秒输出一次等待状态
                        if deploy_attempt % 6 == 0:
                            elapsed_time = time.time() - start_time
                            remaining_time = total_wait_time - elapsed_time
                            logger.info(
                                f"⏳ 正在等待部署... "
                                f"已等待: {elapsed_time:.1f}秒, "
                                f"剩余最长等待时间: {remaining_time:.1f}秒"
                            )
                        
                        time.sleep(deploy_retry_interval)
                        
                    except requests.RequestException as e:
                        if deploy_attempt % 6 == 0:
                            logger.warning(
                                f"部署检查失败 ({deploy_attempt + 1}/{max_deploy_retries}): "
                                f"{e.__class__.__name__}: {str(e)}"
                            )
                        time.sleep(deploy_retry_interval)
                
                logger.warning(
                    "⚠️ GitHub Pages 部署超时，但将继续处理。"
                    "页面可能需要几分钟后才能访问。"
                )
                return filename, github_url
                
            except Exception as e:
                error_msg = f"GitHub 上传尝试 {attempt + 1}/{max_retries} 失败: {e.__class__.__name__}: {str(e)}"
                if attempt < max_retries - 1:
                    logger.warning(f"{error_msg} - 将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(f"GitHub 上传失败: {str(e)}") from e

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
            prompt = """请为以下网页内容生成简短摘要和相关标签。

要求：
1. 无论原文是中文还是英文，都必须用中文回复
2. 摘要控制在100字以内
3. 生成3-5个中文标签
4. 严格按照以下格式返回：

摘要：[100字以内的中文摘要]
标签：tag1，tag2，tag3，tag4，tag5

网页内容：
""" + content[:5000] + "..."

            max_retries = self.config.get('openai_max_retries', 3)
            for attempt in range(max_retries):
                try:
                    if self.ai_provider == 'azure':
                        response = self.client.chat.completions.create(
                            model=self.config['azure_deployment_name'],
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result = response.choices[0].message.content
                    elif self.ai_provider == 'deepseek':
                        response = self.client.chat.completions.create(
                            model=self.config.get('deepseek_model', 'deepseek-chat'),
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result = response.choices[0].message.content
                    elif self.ai_provider == 'gemini':
                        # 修改 Gemini 调用方式
                        try:
                            response = self.client.generate_content(
                                prompt,
                                generation_config={
                                    "temperature": 0.7,
                                    "top_p": 0.8,
                                    "top_k": 40,
                                    "max_output_tokens": 1024,
                                },
                                safety_settings=[
                                    {
                                        "category": "HARM_CATEGORY_HARASSMENT",
                                        "threshold": "BLOCK_NONE",
                                    },
                                    {
                                        "category": "HARM_CATEGORY_HATE_SPEECH",
                                        "threshold": "BLOCK_NONE",
                                    },
                                    {
                                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                        "threshold": "BLOCK_NONE",
                                    },
                                    {
                                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                        "threshold": "BLOCK_NONE",
                                    },
                                ]
                            )
                            
                            if response.prompt_feedback.block_reason:
                                raise Exception(f"Content blocked: {response.prompt_feedback.block_reason}")
                                
                            result = response.text
                            
                            # 如果返回为空，抛出异常
                            if not result.strip():
                                raise Exception("Empty response from Gemini")
                                
                        except Exception as e:
                            logger.error(f"Gemini API error: {str(e)}")
                            raise
                    else:
                        response = self.client.chat.completions.create(
                            model=self.config.get('openai_model', 'gpt-3.5-turbo'),
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result = response.choices[0].message.content

                    logger.info(f"AI 生成结果: {result}")

                    # 解析摘要和标签
                    summary = ""
                    tags = []
                    
                    for line in result.split('\n'):
                        if line.startswith('摘要：'):
                            summary = line.replace('摘要：', '').strip()
                        elif line.startswith('标签：'):
                            tags = [tag.strip() for tag in line.replace('标签：', '').split('，')]
                    
                    if not summary or not tags:
                        raise ValueError("AI 响应格式不正确")
                    
                    return summary, tags

                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"AI 生成失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(2 ** attempt)  # 指数退避

        except Exception as e:
            logger.error(f"AI 服务失败: {str(e)}")
            if self.config.get('notify_on_ai_error', True):
                try:
                    asyncio.create_task(self.send_telegram_notification(
                        f"⚠️ AI 服务失效提醒\n\n错误信息：{str(e)}"
                    ))
                except Exception as notify_error:
                    logger.error(f"发送 AI 失效通知失败: {str(notify_error)}")

            if self.config.get('skip_ai_on_error', True):
                return (
                    self.config.get('default_summary', "无法生成摘要"),
                    self.config.get('default_tags', ["未分类"])
                )
            raise

    def save_to_notion(self, data):
        """保存到 Notion 数据库"""
        max_retries = 3
        retry_delay = 2  # 初始延迟2秒
        
        for attempt in range(max_retries):
            try:
                tags = data.get('tags', [])
                if not tags:
                    tags = ["未分类"]
                
                current_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', 
                                           time.gmtime(data['created_at']))
                
                properties = {
                    "Title": {"title": [{"text": {"content": data['title']}}]},
                    "OriginalURL": {"url": data['original_url'] if data['original_url'] else None},
                    "SnapshotURL": {"url": data['snapshot_url']},
                    "Summary": {"rich_text": [{"text": {"content": data['summary']}}]},
                    "Tags": {"multi_select": [{"name": tag} for tag in tags if tag.strip()]},
                    "Created": {"date": {"start": current_time}}
                }
                
                # 设置超时时间
                response = self.notion_client.pages.create(
                    parent={"database_id": self.config['notion_database_id']},
                    properties=properties
                )
                
                return response['url']
                
            except Exception as e:
                logger.error(f"保存到 Notion 尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Notion API 响应: {e.response.text}")
                
                if attempt < max_retries - 1:
                    # 使用指数退避策略
                    sleep_time = retry_delay * (2 ** attempt)
                    logger.info(f"等待 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                    continue
                else:
                    # 所有重试都失败了，发送通知
                    error_msg = f"❌ Notion 保存失败: {str(e)}"
                    try:
                        asyncio.create_task(self.send_telegram_notification(error_msg))
                    except Exception as notify_error:
                        logger.error(f"发送 Notion 失败通知失败: {str(notify_error)}")
                    
                    # 如果配置了跳过错误，返回一个占位 URL
                    if self.config.get('skip_notion_on_error', True):
                        logger.warning("跳过 Notion 保存错误，继续处理...")
                        return "https://www.notion.so/error-saving"
                    raise

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

async def cleanup_old_files():
    """定期清理超过一定时间的临时文件"""
    while True:
        try:
            current_time = time.time()
            for file_path in UPLOAD_DIR.glob('*'):
                # 清理超过1小时的文件
                if current_time - file_path.stat().st_mtime > 3600:
                    try:
                        file_path.unlink()
                        logger.info(f"已清理过期文件: {file_path}")
                    except Exception as e:
                        logger.error(f"清理文件失败 {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"清理任务执行失败: {str(e)}")
        
        await asyncio.sleep(1800)  # 每30分钟执行一次

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理器"""
    global handler
    handler = WebClipperHandler(CONFIG)
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # 启动清理任务
    cleanup_task = asyncio.create_task(cleanup_old_files())
    
    yield
    
    # 关闭时取消清理任务
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # 清理所有临时文件
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)

# 创建应用和限速器
app = FastAPI(lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/")  # 支持根路径
@app.post("/upload")  # 支持不带斜杠的 /upload
@app.post("/upload/")  # 保持原有的 /upload/
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
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Upload endpoints: /, /upload, /upload/")
    logger.info(f"API Key required in Bearer token")
    uvicorn.run(app, host=host, port=port)