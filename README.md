# Web Clipper Backend

一个网页剪藏后端服务，支持将网页保存到 GitHub Pages 并同步到 Notion 数据库，同时通过 Telegram 发送通知。

## 特性

- 🚀 支持上传 HTML 文件到 GitHub Pages
- 📚 自动同步到 Notion 数据库
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

## 使用方法

1. 启动服务：

```bash
python main.py
```

2. 发送请求：

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
