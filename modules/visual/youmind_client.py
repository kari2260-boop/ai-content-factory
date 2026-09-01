"""
YouMind API 客户端 - 图片生成和文字排版
"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from modules.utils import setup_logger

logger = setup_logger('youmind_client', 'visual.log')


class YouMindClient:
    """YouMind API 客户端"""

    def __init__(self):
        self.api_key = os.getenv('YOUMIND_API_KEY')
        self.base_url = os.getenv('YOUMIND_BASE_URL', 'https://api.youmind.ai/v1')
        self.output_dir = Path('data/images/youmind')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.available = bool(self.api_key)

        if not self.available:
            logger.warning("YouMind API 未配置")
        else:
            logger.info("YouMind API 已就绪")

    def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Optional[str]:
        """
        生成图片

        Args:
            prompt: 图片描述提示词
            style: 风格 (realistic, anime, cartoon, abstract, etc.)
            size: 尺寸 (1024x1024, 1024x768, 768x1024, etc.)
            quality: 质量 (standard, hd)

        Returns:
            图片文件路径
        """
        if not self.available:
            logger.error("YouMind API 未配置")
            return None

        try:
            logger.info(f"YouMind 生成图片: {prompt[:50]}...")

            url = f"{self.base_url}/images/generate"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "prompt": prompt,
                "style": style,
                "size": size,
                "quality": quality,
                "n": 1
            }

            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()

            result = response.json()

            # 根据 API 返回格式调整
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
            elif 'image_url' in result:
                image_url = result['image_url']
            else:
                logger.error(f"无法解析响应: {result}")
                return None

            # 下载图片
            image_path = self._download_image(image_url, prefix="youmind")
            logger.info(f"✅ YouMind 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"YouMind 图片生成失败: {str(e)}")
            return None

    def generate_cover_image(
        self,
        title: str,
        style: str = "educational",
        platform: str = "wechat"
    ) -> Optional[str]:
        """
        生成封面图（针对内容工厂优化）

        Args:
            title: 内容标题
            style: 风格
            platform: 平台

        Returns:
            图片文件路径
        """
        # 构建提示词
        prompt = self._build_cover_prompt(title, style, platform)

        # 获取平台尺寸
        size = self._get_platform_size(platform)

        # 映射风格
        youmind_style = self._map_style(style)

        return self.generate_image(prompt, style=youmind_style, size=size)

    def format_text_layout(
        self,
        title: str,
        content: str,
        layout_type: str = "article",
        template: Optional[str] = None
    ) -> Optional[Dict]:
        """
        文字排版功能

        Args:
            title: 标题
            content: 正文内容
            layout_type: 排版类型 (article, poster, card, story)
            template: 模板名称（可选）

        Returns:
            {
                'formatted_html': str,  # HTML 格式
                'formatted_md': str,    # Markdown 格式
                'preview_url': str      # 预览链接
            }
        """
        if not self.available:
            logger.error("YouMind API 未配置")
            return None

        try:
            logger.info(f"YouMind 文字排版: {title[:30]}...")

            url = f"{self.base_url}/layout/format"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "title": title,
                "content": content,
                "layout_type": layout_type,
                "template": template
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ YouMind 排版成功")
            return result

        except Exception as e:
            logger.error(f"YouMind 排版失败: {str(e)}")
            return None

    def create_poster(
        self,
        title: str,
        subtitle: Optional[str] = None,
        background_image: Optional[str] = None,
        style: str = "modern"
    ) -> Optional[str]:
        """
        创建海报

        Args:
            title: 主标题
            subtitle: 副标题
            background_image: 背景图片路径或 URL
            style: 海报风格

        Returns:
            海报图片路径
        """
        if not self.available:
            logger.error("YouMind API 未配置")
            return None

        try:
            logger.info(f"YouMind 创建海报: {title[:30]}...")

            url = f"{self.base_url}/poster/create"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "title": title,
                "subtitle": subtitle,
                "background_image": background_image,
                "style": style
            }

            response = requests.post(url, headers=headers, json=data, timeout=90)
            response.raise_for_status()

            result = response.json()
            poster_url = result.get('poster_url') or result.get('url')

            if poster_url:
                poster_path = self._download_image(poster_url, prefix="poster")
                logger.info(f"✅ YouMind 海报创建成功: {poster_path}")
                return str(poster_path)
            else:
                logger.error("无法获取海报 URL")
                return None

        except Exception as e:
            logger.error(f"YouMind 海报创建失败: {str(e)}")
            return None

    def _build_cover_prompt(self, title: str, style: str, platform: str) -> str:
        """构建封面图提示词"""
        style_prompts = {
            'educational': '专业教育风格，柔和色彩，现代设计，清晰简洁',
            'modern': '现代简约，渐变色彩，抽象图形',
            'minimalist': '极简主义，简洁线条，白色背景',
            'colorful': '鲜艳色彩，充满活力，吸引眼球'
        }

        platform_hints = {
            'xiaohongshu': '时尚生活风格，美学设计，Instagram 风格',
            'wechat': '专业可信，清晰简洁',
            'video': '醒目大胆，清晰焦点',
            'moments': '轻松亲切，温暖'
        }

        base_style = style_prompts.get(style, style_prompts['educational'])
        platform_hint = platform_hints.get(platform, '')

        prompt = f"""为标题"{title}"创建一个封面图。
风格：{base_style}
平台：{platform_hint}
要求：高质量，专业，适合中文教育内容，图片中不要包含文字。"""

        return prompt

    def _get_platform_size(self, platform: str) -> str:
        """获取平台推荐尺寸"""
        sizes = {
            'wechat': '1024x1024',
            'xiaohongshu': '1024x1024',
            'video': '1024x1024',
            'moments': '1024x1024'
        }
        return sizes.get(platform, '1024x1024')

    def _map_style(self, style: str) -> str:
        """映射风格到 YouMind 支持的风格"""
        style_map = {
            'educational': 'realistic',
            'modern': 'abstract',
            'minimalist': 'minimalist',
            'colorful': 'vibrant'
        }
        return style_map.get(style, 'realistic')

    def _download_image(self, url: str, prefix: str = "image") -> Path:
        """下载图片到本地"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.output_dir / filename

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath


# 测试代码
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    client = YouMindClient()

    if client.available:
        # 测试图片生成
        image_path = client.generate_cover_image(
            title="AI时代，如何培养孩子的核心竞争力",
            style="educational",
            platform="xiaohongshu"
        )
        print(f"生成的图片: {image_path}")

        # 测试文字排版
        layout = client.format_text_layout(
            title="AI时代的教育",
            content="这是一篇关于AI教育的文章...",
            layout_type="article"
        )
        print(f"排版结果: {layout}")
    else:
        print("请先配置 YOUMIND_API_KEY")
