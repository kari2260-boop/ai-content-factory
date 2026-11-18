"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 清除 Claude Code 注入的系统环境变量，防止其污染本项目的模型配置
for _key in (
    'ANTHROPIC_MODEL', 'ANTHROPIC_AUTH_TOKEN',
    'ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_SONNET_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL',
    'CLAUDE_MODEL', 'CLAUDE_FAST_MODEL', 'CLAUDE_SCORING_MODEL',
):
    os.environ.pop(_key, None)

# 加载环境变量（override=True：.env 优先于剩余系统环境变量）
load_dotenv(override=True)

# Notion 配置
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# AI API Keys（从系统环境变量读取）
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_AUTH_TOKEN')
ANTHROPIC_BASE_URL = os.getenv('ANTHROPIC_BASE_URL', 'https://www.fucheers.top')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Claude 模型配置
DEFAULT_CLAUDE_MODEL = 'claude-sonnet-4-6'
DEFAULT_FAST_MODEL = 'claude-haiku-4-5-20251001'
ANTHROPIC_MODEL = (
    os.getenv('ANTHROPIC_MODEL')
    or os.getenv('CLAUDE_MODEL')
    or DEFAULT_CLAUDE_MODEL
)
ANTHROPIC_FAST_MODEL = (
    os.getenv('ANTHROPIC_FAST_MODEL')
    or os.getenv('CLAUDE_FAST_MODEL')
    or DEFAULT_FAST_MODEL
)
ANTHROPIC_SCORING_MODEL = (
    os.getenv('ANTHROPIC_SCORING_MODEL')
    or os.getenv('CLAUDE_SCORING_MODEL')
    or DEFAULT_FAST_MODEL
)

# OpenClaw 配置
OPENCLAW_GATEWAY_URL = os.getenv('OPENCLAW_GATEWAY_URL', 'ws://127.0.0.1:18789')

# 日志级别
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 数据源配置
DATA_SOURCES = {
    'zhihu': {
        'enabled': True,
        'topics': ['教育', '留学', 'AI', '家庭教育', '人工智能'],
        'limit': 5
    },
    'google_trends': {
        'enabled': True,
        'keywords': ['AI education', 'study abroad', 'parenting'],
        'geo': 'CN',
        'limit': 3
    },
    'rss': {
        'enabled': True,
        'feeds': [
            'https://www.thepaper.cn/rss_channel_25950.xml',  # 澎湃新闻-教育
            'https://rss.sciencenet.cn/index.html',  # 科学网
        ],
        'limit': 3
    }
}

# 内容格式配置
CONTENT_FORMATS = ['video', 'article', 'moments', 'xiaohongshu', 'book']

# 书稿章节配置文件路径
BOOK_STRUCTURE_PATH = Path(__file__).parent.parent / 'config' / 'book_structure.json'
