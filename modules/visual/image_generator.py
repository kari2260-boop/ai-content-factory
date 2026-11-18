"""
图片生成器 - 通过现有代理调用 OpenAI Images API
"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from modules.utils import setup_logger

logger = setup_logger('image_generator', 'visual.log')


class ImageGenerator:
    """AI 图片生成器"""

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://www.fucheers.top').rstrip('/')
        self.output_dir = Path('data/images')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_cover_image(self, title: str, style: str = "educational", platform: str = "wechat") -> Optional[str]:
        """生成封面图，返回本地文件路径"""
        if not self.available:
            logger.warning("未配置 API key，跳过生图")
            return None

        logger.info(f"生成封面图: {title[:30]}... | 平台: {platform}")
        size = self._get_platform_size(platform)
        prompt = self._build_prompt(title, style, platform)
        return self._generate_via_proxy(prompt, size)

    def _get_platform_size(self, platform: str) -> str:
        sizes = {
            'wechat': '1024x1024',
            'xiaohongshu': '1024x1024',
            'video': '1024x1024',
            'moments': '1024x1024',
        }
        return sizes.get(platform, '1024x1024')

    def _build_prompt(self, title: str, style: str, platform: str) -> str:
        style_prompts = {
            'educational': 'clean professional educational illustration, soft warm colors, modern flat design',
            'modern': 'modern minimalist, gradient colors, abstract geometric shapes',
            'minimalist': 'minimalist, simple clean lines, ivory white background',
            'colorful': 'vibrant trendy lifestyle aesthetic, eye-catching, Instagram-style',
        }
        platform_hints = {
            'xiaohongshu': 'trendy lifestyle aesthetic, warm tones, suitable for Chinese youth audience',
            'wechat': 'professional trustworthy, clean editorial style',
            'video': 'bold attention-grabbing, clear focal point, high contrast',
            'moments': 'casual warm relatable',
        }
        base_style = style_prompts.get(style, style_prompts['educational'])
        platform_hint = platform_hints.get(platform, '')
        return (
            f'Create a {base_style} cover image for Chinese education content titled "{title}". '
            f'{platform_hint}. High quality, no text in the image.'
        )

    def _generate_via_proxy(self, prompt: str, size: str) -> Optional[str]:
        """通过代理调用 Images API"""
        try:
            url = f"{self.base_url}/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "dall-e-2",
                "prompt": prompt[:950],  # DALL-E 2 prompt limit
                "n": 1,
                "size": size,
            }
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            resp.raise_for_status()
            image_url = resp.json()['data'][0]['url']
            return str(self._download_image(image_url))
        except Exception as e:
            logger.error(f"生图失败: {e}")
            return None

    def _download_image(self, url: str) -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.output_dir / f"cover_{timestamp}.png"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        return filepath

    def generate_batch(self, contents: list) -> Dict[str, str]:
        results = {}
        for content in contents:
            path = self.generate_cover_image(content.get('title', ''), platform=content.get('platform', 'wechat'))
            if path:
                results[content.get('platform', 'wechat')] = path
        return results



class ImageGenerator:
    """AI 图片生成器"""

    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.replicate_key = os.getenv('REPLICATE_API_TOKEN')
        self.output_dir = Path('data/images')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_cover_image(self, title: str, style: str = "educational", platform: str = "wechat") -> Optional[str]:
        """
        生成封面图

        Args:
            title: 内容标题
            style: 风格 (educational, modern, minimalist, colorful)
            platform: 平台 (wechat, xiaohongshu, video)

        Returns:
            图片文件路径
        """
        logger.info(f"生成封面图: {title[:30]}... | 平台: {platform}")

        # 根据平台选择尺寸
        size = self._get_platform_size(platform)

        # 构建提示词
        prompt = self._build_prompt(title, style, platform)

        # 优先使用 DALL-E 3
        if self.openai_key:
            return self._generate_dalle3(prompt, size)

        # 降级使用 Replicate (Flux)
        elif self.replicate_key:
            return self._generate_flux(prompt, size)

        else:
            logger.warning("未配置图片生成 API")
            return None

    def _get_platform_size(self, platform: str) -> str:
        """获取平台推荐尺寸"""
        sizes = {
            'wechat': '1024x1024',      # 公众号封面 2.35:1 → 1024x1024 居中裁剪
            'xiaohongshu': '1024x1024', # 小红书 3:4 → 1024x1024
            'video': '1024x1024',       # 视频号 16:9 → 1024x1024
            'moments': '1024x1024'      # 朋友圈 1:1
        }
        return sizes.get(platform, '1024x1024')

    def _build_prompt(self, title: str, style: str, platform: str) -> str:
        """构建图片生成提示词"""

        style_prompts = {
            'educational': 'clean, professional, educational illustration, soft colors, modern design',
            'modern': 'modern, minimalist, gradient colors, abstract shapes',
            'minimalist': 'minimalist, simple, clean lines, white background',
            'colorful': 'vibrant colors, energetic, eye-catching, dynamic composition'
        }

        platform_hints = {
            'xiaohongshu': 'trendy, lifestyle, aesthetic, Instagram-style',
            'wechat': 'professional, trustworthy, clean',
            'video': 'bold, attention-grabbing, clear focal point',
            'moments': 'casual, relatable, warm'
        }

        base_style = style_prompts.get(style, style_prompts['educational'])
        platform_hint = platform_hints.get(platform, '')

        prompt = f"""Create a {base_style} cover image for an article titled "{title}".
{platform_hint}.
High quality, professional, suitable for Chinese education content.
No text in the image."""

        return prompt

    def _generate_dalle3(self, prompt: str, size: str) -> Optional[str]:
        """使用 DALL-E 3 生成图片"""
        try:
            logger.info("使用 DALL-E 3 生成图片")

            url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": "standard"
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            image_url = result['data'][0]['url']

            # 下载图片
            image_path = self._download_image(image_url)
            logger.info(f"✅ 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"DALL-E 3 生成失败: {str(e)}")
            return None

    def _generate_flux(self, prompt: str, size: str) -> Optional[str]:
        """使用 Flux (via Replicate) 生成图片"""
        try:
            logger.info("使用 Flux 生成图片")

            # Replicate API 调用
            # 这里需要安装 replicate 包: pip install replicate
            import replicate

            width, height = map(int, size.split('x'))

            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "num_outputs": 1
                }
            )

            # 下载图片
            image_url = output[0]
            image_path = self._download_image(image_url)
            logger.info(f"✅ 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"Flux 生成失败: {str(e)}")
            return None

    def _download_image(self, url: str) -> Path:
        """下载图片到本地"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cover_{timestamp}.png"
        filepath = self.output_dir / filename

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    def generate_batch(self, contents: list) -> Dict[str, str]:
        """批量生成图片"""
        results = {}

        for content in contents:
            title = content.get('title', '')
            platform = content.get('platform', 'wechat')

            image_path = self.generate_cover_image(title, platform=platform)
            if image_path:
                results[platform] = image_path

        return results


# 测试代码
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    generator = ImageGenerator()

    # 测试生成
    image_path = generator.generate_cover_image(
        title="AI时代，如何培养孩子的核心竞争力",
        style="educational",
        platform="xiaohongshu"
    )

    print(f"生成的图片: {image_path}")
