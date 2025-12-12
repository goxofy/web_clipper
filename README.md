# Web Clipper Backend

一个网页剪藏后端服务，支持将网页保存到 GitHub Pages 并同步到 Notion 数据库，同时通过 Telegram 发送通知。

## 特性

- 🚀 支持上传 HTML 文件到 GitHub Pages
- 📚 自动同步到 Notion 数据库
- 🤖 使用 AI 自动生成摘要和标签
- 📱 通过 Telegram 发送剪藏通知
- 🔒 API 密钥认证
- 🔄 自动重试机制

## Screenshots

![789d062a91a4a96ae435a4b0b679598314c836b5](https://github.com/user-attachments/assets/2dbdc209-f80c-46b5-964e-532f5484829f)

![3294e5d991e4c0a060bc4af5d212b159e6a53863 (1)](https://github.com/user-attachments/assets/ef89bf3a-3f7b-402c-b883-03c2cc66f170)

![c02394e52fea94b4b8bb8d9032ffa0f31617ad26 (1)](https://github.com/user-attachments/assets/772edbbf-54f3-466e-bf0f-caefe70a19e9)


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

## 部署与运行

### 方式一：Docker 部署（推荐）

直接使用 `docker-compose` 启动，无需安装 Python 环境。

1. 确保已安装 Docker 和 Docker Compose。
2. 修改 `docker-compose.yml` 中的环境变量（参考上方[配置说明](#配置说明)）。
3. 启动服务：
   ```bash
   docker-compose up -d
   ```

### 方式二：源码运行

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 创建 `.env` 文件并在其中配置环境变量。
3. 启动服务：
   ```bash
   python main.py
   ```

## 快速测试

可以使用 curl 命令测试服务是否正常运行：



```bash
curl -X POST "http://your-instance-url/upload" \
     -H "Authorization: Bearer your-api-key" \
     -F "singlehtmlfile=@webpage.html" \
     -F "url=https://original-url.com"
```

## API 文档

### 上传接口

- 端点：`/upload`
- 方法：POST
- 认证：Bearer Token
- 参数：
  - singlehtmlfile: HTML 文件
  - url: 原始网页 URL
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



CDN acceleration and security protection for this project are sponsored by Tencent EdgeOne.
