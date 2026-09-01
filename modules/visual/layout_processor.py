"""
排版处理器 - 将内容转换为不同平台的格式
"""
import os
from pathlib import Path
from typing import Dict, Optional
import markdown
from datetime import datetime

from modules.utils import setup_logger

logger = setup_logger('layout_processor', 'visual.log')


class LayoutProcessor:
    """内容排版处理器"""

    def __init__(self):
        self.output_dir = Path('data/formatted')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format_wechat_article(self, content: Dict, cover_image: Optional[str] = None) -> str:
        """
        格式化公众号文章

        Args:
            content: 内容字典 (包含 title, body 等)
            cover_image: 封面图路径

        Returns:
            格式化后的 HTML
        """
        logger.info(f"格式化公众号文章: {content.get('title', '')[:30]}...")

        title = content.get('title', '')
        body = content.get('body', '')

        # 转换 Markdown 到 HTML
        html_body = markdown.markdown(body, extensions=['extra', 'codehilite'])

        # 应用公众号样式
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 720px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }}
        h1 {{
            font-size: 24px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
        }}
        h2 {{
            font-size: 20px;
            font-weight: bold;
            margin: 18px 0 10px;
            color: #2c3e50;
        }}
        h3 {{
            font-size: 18px;
            font-weight: bold;
            margin: 16px 0 8px;
            color: #34495e;
        }}
        p {{
            margin: 12px 0;
            text-indent: 2em;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 16px;
            margin: 16px 0;
            color: #555;
            background: #f8f9fa;
            padding: 12px 16px;
        }}
        strong {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .cover {{
            width: 100%;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {f'<img class="cover" src="{cover_image}" alt="封面图">' if cover_image else ''}
    {html_body}
</body>
</html>
"""

        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wechat_{timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✅ 公众号文章已保存: {filepath}")
        return str(filepath)

    def format_xiaohongshu(self, content: Dict, cover_image: Optional[str] = None) -> str:
        """
        格式化小红书内容

        Returns:
            纯文本格式 (带 emoji 和排版)
        """
        logger.info(f"格式化小红书内容: {content.get('title', '')[:30]}...")

        title = content.get('title', '')
        body = content.get('body', '')
        tags = content.get('tags', [])

        # 小红书格式: 标题 + emoji + 正文 + 标签
        formatted = f"""📚 {title}

{body}

{''.join([f'#{tag} ' for tag in tags])}
"""

        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"xiaohongshu_{timestamp}.txt"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted)

        logger.info(f"✅ 小红书内容已保存: {filepath}")
        return str(filepath)

    def format_video_script(self, content: Dict, cover_image: Optional[str] = None) -> str:
        """
        格式化视频号脚本

        Returns:
            结构化脚本 (分镜头)
        """
        logger.info(f"格式化视频号脚本: {content.get('title', '')[:30]}...")

        title = content.get('title', '')
        body = content.get('body', '')

        # 视频脚本格式
        formatted = f"""🎬 视频号脚本

【标题】{title}

【封面图】{cover_image if cover_image else '待添加'}

【脚本正文】
{body}

【拍摄提示】
- 时长: 1-3分钟
- 风格: 教育、专业、亲和
- 场景: 书房/办公室
- 字幕: 全程字幕
"""

        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"video_{timestamp}.txt"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted)

        logger.info(f"✅ 视频号脚本已保存: {filepath}")
        return str(filepath)

    def format_book_chapter(self, content: Dict) -> str:
        """
        格式化书稿章节

        Returns:
            Markdown 格式书稿
        """
        logger.info(f"格式化书稿: {content.get('title', '')[:30]}...")

        title = content.get('title', '')
        body = content.get('body', '')
        chapter = content.get('chapter', '未分类')

        # 书稿格式
        formatted = f"""# {title}

> 章节: {chapter}

{body}

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # 保存文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"book_{timestamp}.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted)

        logger.info(f"✅ 书稿已保存: {filepath}")
        return str(filepath)

    def format_all(self, draft: Dict, images: Dict[str, str]) -> Dict[str, str]:
        """
        批量格式化所有平台内容

        Args:
            draft: 草稿内容
            images: 各平台的封面图 {platform: image_path}

        Returns:
            各平台的格式化文件路径
        """
        results = {}

        # 公众号
        if 'wechat_article' in draft:
            wechat_content = {
                'title': draft.get('topic', {}).get('title', ''),
                'body': draft['wechat_article']
            }
            results['wechat'] = self.format_wechat_article(
                wechat_content,
                images.get('wechat')
            )

        # 小红书
        if 'xiaohongshu' in draft:
            xhs_content = {
                'title': draft.get('topic', {}).get('title', ''),
                'body': draft['xiaohongshu'],
                'tags': ['教育', 'AI', '育儿']
            }
            results['xiaohongshu'] = self.format_xiaohongshu(
                xhs_content,
                images.get('xiaohongshu')
            )

        # 视频号
        if 'video_script' in draft:
            video_content = {
                'title': draft.get('topic', {}).get('title', ''),
                'body': draft['video_script']
            }
            results['video'] = self.format_video_script(
                video_content,
                images.get('video')
            )

        # 书稿
        if 'book_material' in draft:
            book_content = {
                'title': draft.get('topic', {}).get('title', ''),
                'body': draft['book_material'],
                'chapter': draft.get('book_chapter', '未分类')
            }
            results['book'] = self.format_book_chapter(book_content)

        return results


# 测试代码
if __name__ == '__main__':
    processor = LayoutProcessor()

    # 测试公众号格式化
    test_content = {
        'title': 'AI时代，如何培养孩子的核心竞争力',
        'body': '''
## 引言

在AI时代，教育的本质发生了变化...

## 核心观点

1. **从弱变强的能力**
2. **做决策的能力**

## 实践方法

具体来说...
'''
    }

    result = processor.format_wechat_article(test_content)
    print(f"格式化结果: {result}")
