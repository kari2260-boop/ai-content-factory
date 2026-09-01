"""
视觉处理主入口 - 整合图片生成和排版
"""
from typing import Dict, Optional
from pathlib import Path

from modules.visual.image_generator import ImageGenerator
from modules.visual.layout_processor import LayoutProcessor
from modules.utils import setup_logger

logger = setup_logger('visual_main', 'visual.log')


class VisualProcessor:
    """视觉处理器 - 图片生成 + 排版"""

    def __init__(self):
        self.image_gen = ImageGenerator()
        self.layout = LayoutProcessor()

    def process_draft(self, draft: Dict, generate_images: bool = True) -> Dict:
        """
        处理草稿：生成图片 + 排版

        Args:
            draft: 草稿内容
            generate_images: 是否生成图片

        Returns:
            {
                'images': {platform: image_path},
                'formatted': {platform: file_path}
            }
        """
        logger.info("=" * 50)
        logger.info(f"开始视觉处理: {draft.get('topic', {}).get('title', '')[:30]}...")
        logger.info("=" * 50)

        result = {
            'images': {},
            'formatted': {}
        }

        title = draft.get('topic', {}).get('title', '')

        # Step 1: 生成图片
        if generate_images:
            logger.info("步骤 1/2: 生成封面图")

            platforms = ['wechat', 'xiaohongshu', 'video']
            for platform in platforms:
                if platform == 'xiaohongshu':
                    style = 'colorful'
                elif platform == 'video':
                    style = 'modern'
                else:
                    style = 'educational'

                image_path = self.image_gen.generate_cover_image(
                    title=title,
                    style=style,
                    platform=platform
                )

                if image_path:
                    result['images'][platform] = image_path
                    logger.info(f"  ✅ {platform}: {image_path}")
        else:
            logger.info("跳过图片生成")

        # Step 2: 排版
        logger.info("步骤 2/2: 格式化内容")
        result['formatted'] = self.layout.format_all(draft, result['images'])

        for platform, filepath in result['formatted'].items():
            logger.info(f"  ✅ {platform}: {filepath}")

        logger.info("=" * 50)
        logger.info("✅ 视觉处理完成")
        logger.info("=" * 50)

        return result

    def quick_process(self, title: str, content: str, platform: str = 'wechat') -> Dict:
        """
        快速处理单个内容

        Args:
            title: 标题
            content: 内容
            platform: 平台

        Returns:
            {'image': path, 'formatted': path}
        """
        # 生成图片
        image_path = self.image_gen.generate_cover_image(
            title=title,
            platform=platform
        )

        # 格式化
        content_dict = {'title': title, 'body': content}

        if platform == 'wechat':
            formatted_path = self.layout.format_wechat_article(content_dict, image_path)
        elif platform == 'xiaohongshu':
            formatted_path = self.layout.format_xiaohongshu(content_dict, image_path)
        elif platform == 'video':
            formatted_path = self.layout.format_video_script(content_dict, image_path)
        else:
            formatted_path = None

        return {
            'image': image_path,
            'formatted': formatted_path
        }


# 测试代码
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    processor = VisualProcessor()

    # 测试草稿
    test_draft = {
        'topic': {
            'title': 'AI时代，如何培养孩子的核心竞争力'
        },
        'wechat_article': '## 引言\n\n在AI时代...',
        'xiaohongshu': '📚 分享一个重要观点...',
        'video_script': '大家好，今天聊聊...',
        'book_material': '# 第一章\n\n核心内容...'
    }

    result = processor.process_draft(test_draft, generate_images=True)
    print(f"处理结果: {result}")
