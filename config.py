import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

CONFIG = {
    'host': os.getenv('HOST', '0.0.0.0'),
    'port': int(os.getenv('PORT', 65331)),

    'github_repo': os.getenv('GITHUB_REPO', 'your_github_name/your_github_repo'),
    'github_token': os.getenv('GITHUB_TOKEN', 'your_github_token'),
    'github_pages_domain': os.getenv('GITHUB_PAGES_DOMAIN', 'your_github_pages_domain'),
    'notion_database_id': os.getenv('NOTION_DATABASE_ID', 'notion_database_id'),
    'notion_token': os.getenv('NOTION_TOKEN', 'notion_token'),
    'telegram_token': os.getenv('TELEGRAM_TOKEN', 'telegram_token'),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', 'telegram_chat_id'),

    'openai_api_key': os.getenv('OPENAI_API_KEY', 'your_openai_api_key'),
    'openai_base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
    'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
    'openai_max_retries': int(os.getenv('OPENAI_MAX_RETRIES', 3)),

    'api_key': os.getenv('API_KEY', 'your_api_key'),
    'max_file_size': int(os.getenv('MAX_FILE_SIZE', 30 * 1024 * 1024)),
    'allowed_extensions': os.getenv('ALLOWED_EXTENSIONS', '.html,.htm').split(','),
    'github_pages_max_retries': int(os.getenv('GITHUB_PAGES_MAX_RETRIES', 60)),
}
