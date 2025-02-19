# Web Clipper Backend

一个强大的网页剪藏后端服务，支持将网页保存到 GitHub Pages 并同步到 Notion 数据库，同时通过 Telegram 发送通知。

## 特性

- 🚀 支持上传 HTML 文件到 GitHub Pages
- 📚 自动同步到 Notion 数据库
- 🤖 支持多种 AI 服务自动生成摘要和标签
  - Azure OpenAI
  - OpenAI
  - Deepseek
- 📱 通过 Telegram 发送剪藏通知
- 🔒 API 密钥认证
- ⚡ FastAPI 高性能后端
- 🔄 自动重试机制
- 📝 详细的日志记录
- 🛡️ 完善的错误处理

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/web-clipper-backend.git
cd web-clipper-backend
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置服务：

复制 `config.example.py` 到 `config.py` 并填写配置：

```python
CONFIG = {
'github_repo': 'username/repo', # GitHub 仓库
'github_token': 'your-github-token', # GitHub 访问令牌
'github_pages_domain': 'https://username.github.io', # GitHub Pages 域名
'notion_database_id': 'your-database-id', # Notion 数据库 ID
'notion_token': 'your-notion-token', # Notion 集成令牌
'telegram_token': 'your-telegram-bot-token', # Telegram Bot 令牌
'telegram_chat_id': 'your-chat-id', # Telegram 聊天 ID
'api_key': 'your-api-key', # API 访问密钥
'port': 8000, # 服务端口
# AI 服务配置（二选一）
# OpenAI 配置
'ai_provider': 'openai',
'openai_api_key': 'your-openai-key',
'openai_model': 'gpt-3.5-turbo',
# 或 Azure OpenAI 配置
'ai_provider': 'azure',
'azure_api_key': 'your-azure-key',
'azure_api_base': 'https://your-resource.openai.azure.com/',
'azure_deployment_name': 'your-deployment-name',
}
```

## 配置说明

### GitHub 配置
1. 创建一个 GitHub 仓库（可以是私有的）
2. 开启 GitHub Pages（设置为从 main 分支构建）
3. 生成 GitHub 访问令牌（需要 repo 权限）

### Notion 配置
1. 创建一个新的 Notion 数据库，包含以下字段：
   - Title (标题)
   - OriginalURL (URL)
   - SnapshotURL (URL)
   - Summary (Text)
   - Tags (Multi-select)
   - Created (Date)
2. 创建 Notion 集成并获取令牌
3. 将集成添加到数据库

### Telegram 配置
1. 通过 @BotFather 创建新的 Bot
2. 获取 Bot Token
3. 获取聊天 ID

## 使用方法

1. 启动服务：

```bash
python web_clipper.py
```

2. 发送请求：

```bash
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer your-api-key" \
     -F "file=@webpage.html" \
     -F "url=https://original-url.com"
```

## API 文档

### 上传接口

- 端点：`/`, `/upload`, `/upload/`
- 方法：POST
- 认证：Bearer Token
- 参数：
  - file: HTML 文件
  - url: 原始网页 URL（可选）
- 响应：
```json
{
    "status": "success",
    "github_url": "https://...",
    "notion_url": "https://..."
}
```

## 本地操作
1. 浏览器安装 singlefile 插件 https://chromewebstore.google.com/detail/singlefile/mpiodijhokgodhhofbcjdecpffjipkle
2. 配置插件（只需要配置一次，支持云端同步）： 
	1. 文件名-模版： {url-host}{url-pathname-flat}.{filename-extension}   
	2. 文件名-最大长度：   384字符
	3. 文件名-替换字符：$
	4. 保存位置-保存到 REST 表单 API-网址: 你的服务器 ip，自行解决端口访问问题
	5. 保存位置-保存到 REST 表单 API-授权令牌： 第二步里面配置的 Bearer Key
	6. 保存位置-保存到 REST 表单 API-文件字段名称： singlehtmlfile
	7. 保存位置-保存到 REST 表单 API-网址字段名称： url
3. 保存
4. [Notion 模板](https://www.notion.so/cuiplus/19f32fd5f34e805a9001f2e38fc4ac74?v=19f32fd5f34e810eb20f000c0956c3b9&pvs=4)

## 浏览器配置

1. 安装 SingleFile 插件
2. 配置插件：
   - 文件名模版：`{url-host}{url-pathname-flat}.{filename-extension}`
   - 保存到 REST API：`http://your-server:65331/upload`
   - 授权令牌：配置文件中的 `api_key`

## 注意事项

1. 确保所有 API 密钥和令牌的安全性
2. 建议使用 HTTPS 代理
3. 定期检查日志文件
4. 配置适当的重试策略
5. 根据需要调整超时设置

## 错误处理机制

### AI 服务错误处理
- 支持多次重试，使用指数退避策略
- 可配置失效时是否继续保存
- 失效时使用默认摘要和标签
- 可选择是否发送失效通知

### Notion 同步错误处理
- 支持多次重试，使用指数退避策略
- 可配置保存失败时是否继续处理
- 失败时返回占位 URL
- 发送失败通知到 Telegram

### GitHub 上传错误处理
- 支持多次重试上传
- 自动等待 Pages 部署完成
- 超时后继续处理其他步骤

## 日志

服务会记录详细的操作日志，包括：
- 上传进度
- GitHub Pages 部署状态
- AI 生成结果
- Notion 同步状态
- Telegram 通知发送

## Docker 部署

### 一键部署（推荐）

1. 下载部署脚本并添加执行权限：

```bash
chmod +x deploy.sh
```

2. 运行部署脚本：

```bash
./deploy.sh
```

脚本会自动：
- 检查并安装 Docker 和 Docker Compose
- 检查配置文件
- 构建并启动服务
- 显示部署状态

### 手动部署

1. 确保服务器已安装 Docker 和 Docker Compose

2. 创建 docker-compose.yml 文件：

```yaml
version: '3'

services:
  web-clipper:
    build: .
    container_name: web-clipper
    restart: unless-stopped
    ports:
      - "65331:65331"
    volumes:
      - ./config.py:/app/config.py
```

3. 启动服务：

```bash
docker-compose up -d
```

4. 查看日志：

```bash
docker-compose logs -f
```

5. 停止服务：

```bash
docker-compose down
```

### 使用 Docker 命令行

1. 构建镜像：

```bash
docker build -t web-clipper .
```

2. 运行容器：

```bash
docker run -d \
  --name web-clipper \
  -p 8000:8000 \
  -v $(pwd)/config.py:/app/config.py \
  --restart unless-stopped \
  web-clipper
```

3. 查看日志：

```bash
docker logs -f web-clipper
```

4. 停止容器：

```bash
docker stop web-clipper
```

5. 重启容器：

```bash
docker restart web-clipper
```

### Docker 部署注意事项

1. 确保在运行容器前已正确配置 `config.py`
2. 容器默认使用 8000 端口，可以通过端口映射修改外部访问端口
3. 配置文件通过 volume 挂载，方便修改配置而无需重新构建镜像
4. 容器设置了自动重启策略，服务器重启后会自动启动
5. 建议使用 Docker Compose 来管理容器，更加方便维护


## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！