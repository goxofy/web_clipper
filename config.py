import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

CONFIG = {
    'host': os.getenv('HOST', '0.0.0.0'),  # 服务器监听地址
    'port': int(os.getenv('PORT', 65331)),       # 服务器端口

    'github_repo': os.getenv('GITHUB_REPO', 'your_github_name/your_github_repo'), # 开一个repo，可以private，填入你的github用户名和repo名称
    'github_token': os.getenv('GITHUB_TOKEN', 'your_github_token'),  # 开一个 token，需要授权到上面那个repo的权限
    'github_pages_domain': os.getenv('GITHUB_PAGES_DOMAIN', 'your_github_pages_domain'), # repo开启pages，然后这里写上域名，类似 https://username.github.io/repo
    'notion_database_id': os.getenv('NOTION_DATABASE_ID', 'notion_database_id'), # 创建一个新页面，格式为table，然后参照这个 https://blog.csdn.net/weixin_46014809/article/details/132631030 拿到id
    'notion_token': os.getenv('NOTION_TOKEN', 'notion_token'), # 在这里 https://www.notion.so/profile/integrations 申请一个notion token，具体步骤自己搜索，并且授权到上面的table，具体教程找一下很多的
    'telegram_token': os.getenv('TELEGRAM_TOKEN', 'telegram_token'), # 在telegram里面 @bot_father 申请一个bot
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', 'telegram_chat_id'), # 按照这个 https://zhuanlan.zhihu.com/p/602213485 拿到 chat id

    'openai_api_key': os.getenv('OPENAI_API_KEY', 'your_openai_api_key'),  #  OpenAI API key
    'openai_base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),  # 如果需要第三方gpt代理，填到这，否则请不要修改
    'openai_model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),  # 模型配置
    'openai_max_retries': int(os.getenv('OPENAI_MAX_RETRIES', 3)),          # gpt最大重试次数

    'api_key': os.getenv('API_KEY', 'your_api_key'),  # singlefile直接上传文件到 restful api 的 Bearer Key
    'max_file_size': int(os.getenv('MAX_FILE_SIZE', 30 * 1024 * 1024)),  # 30MB 最大文件上传尺寸
    'allowed_extensions': os.getenv('ALLOWED_EXTENSIONS', '.html,.htm').split(','), # 允许的格式，不建议修改
    'github_pages_max_retries': int(os.getenv('GITHUB_PAGES_MAX_RETRIES', 60)),    # GitHub Pages 最大等待次数（5秒 * 60 = 5分钟），html 上传到 gh pages 之后，需要一段时间部署才能访问，一般在一分钟以内
}
