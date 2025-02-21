CONFIG = {
    # 基础配置
    'host': '0.0.0.0',  # 服务器监听地址
    'port': 65331,      # 服务器端口
    'api_key': 'your_api_key',  # API 访问密钥，用于 Bearer 认证

    # GitHub 配置
    'github_repo': 'username/repo',  # GitHub 仓库，格式：用户名/仓库名
    'github_token': 'github_pat_xxxxx',  # GitHub 访问令牌，需要 repo 权限
    'github_pages_domain': 'username.github.io',  # GitHub Pages 域名
    'github_pages_max_retries': 60,  # GitHub Pages 部署等待重试次数（5秒 * 60 = 5分钟）

    # Notion 配置
    'notion_database_id': 'xxxxxxxxxxxxxxxx',  # Notion 数据库 ID
    'notion_token': 'secret_xxxxxx',  # Notion 集成令牌

    # Telegram 配置
    'telegram_token': 'botxxxxx:xxxxxx',  # Telegram Bot Token
    'telegram_chat_id': '123456789',  # Telegram 聊天 ID

    # AI 服务配置（四选一：azure, openai, deepseek, gemini）
    'ai_provider': 'gemini',  # 可选: 'azure', 'openai', 'deepseek', 'gemini'

    # Azure OpenAI 配置
    'azure_api_key': 'azure_api_key',  # Azure OpenAI API 密钥
    'azure_api_base': 'https://your-resource.openai.azure.com/',  # Azure OpenAI 终端点
    'azure_api_version': '2024-02-15-preview',  # API 版本
    'azure_deployment_name': 'gpt-35-turbo',  # 部署的模型名称

    # OpenAI 配置
    'openai_api_key': 'sk-xxxxx',  # OpenAI API 密钥
    'openai_base_url': 'https://api.openai.com/v1',  # API 基础 URL，可选用第三方代理
    'openai_model': 'gpt-3.5-turbo',  # 使用的模型名称

    # Deepseek 配置
    'deepseek_api_key': 'sk-xxxxx',  # Deepseek API 密钥
    'deepseek_base_url': 'https://api.deepseek.com/v1',  # Deepseek API 基础 URL
    'deepseek_model': 'deepseek-chat',  # 使用的模型名称

    # Gemini 配置
    'gemini_api_key': 'your-gemini-api-key',  # Gemini API 密钥
    'gemini_model': 'gemini-1.5-flash',  # 使用的模型名称

    # 文件处理配置
    'max_file_size': 30 * 1024 * 1024,  # 最大文件大小（30MB）
    'allowed_extensions': ['.html', '.htm'],  # 允许的文件扩展名

    # AI 错误处理配置
    'openai_max_retries': 3,  # AI 调用最大重试次数
    'default_summary': '这是一个网页存档',  # AI 失效时的默认摘要
    'default_tags': ['未分类'],  # AI 失效时的默认标签
    'skip_ai_on_error': True,  # AI 失效时是否继续保存
    'notify_on_ai_error': True,  # AI 失效时是否发送通知

    # Notion 错误处理配置
    'skip_notion_on_error': True,  # Notion 保存失败时是否继续处理
    'notion_max_retries': 3,  # Notion API 最大重试次数
    'notion_retry_delay': 2,  # Notion API 重试初始延迟（秒）
}
