"""
Gemini API 客户端（备用）
支持第三方中转 API，支持文本生成和图片生成
"""
import os
import requests
import google.generativeai as genai
from pathlib import Path
from datetime import datetime

from modules.utils import setup_logger

logger = setup_logger('gemini_client', 'generator.log')


class GeminiClient:
    """Gemini API 客户端"""

    def __init__(self):
        from modules.config import GEMINI_API_KEY

        if not GEMINI_API_KEY:
            logger.warning("未找到 GEMINI_API_KEY 环境变量，Gemini 客户端不可用")
            self.available = False
            return

        self.api_key = GEMINI_API_KEY

        # 检查是否使用第三方中转
        self.base_url = os.getenv('GEMINI_BASE_URL')
        self.use_proxy = bool(self.base_url)

        # 图片输出目录
        self.output_dir = Path('data/images/gemini')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.use_proxy:
            logger.info(f"使用第三方中转 API: {self.base_url}")
            self.available = True
        else:
            # 使用官方 API
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """生成内容"""
        if not self.available:
            raise ValueError("Gemini 客户端不可用")

        try:
            logger.info("调用 Gemini API 生成内容")

            if self.use_proxy:
                # 使用第三方中转 API
                content = self._generate_via_proxy(prompt, max_tokens)
            else:
                # 使用官方 API
                response = self.model.generate_content(prompt)
                content = response.text

            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"Gemini API 调用失败: {str(e)}")
            raise

    def _generate_via_proxy(self, prompt: str, max_tokens: int = 4096) -> str:
        """通过第三方中转 API 生成内容（OpenAI 兼容格式）"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': 'gemini-2.5-pro',  # 使用中转支持的模型
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()
        content = data['choices'][0]['message']['content']
        return content

    def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """
        生成图片（通过第三方中转 API）

        Args:
            prompt: 图片描述
            size: 图片尺寸

        Returns:
            图片文件路径
        """
        if not self.available:
            raise ValueError("Gemini 客户端不可用")

        if not self.use_proxy:
            raise ValueError("Gemini 图片生成需要使用第三方中转 API")

        try:
            logger.info(f"Gemini 生成图片: {prompt[:50]}...")

            url = f"{self.base_url}/v1/images/generations"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            payload = {
                'model': 'imagen-3.0-generate-001',  # Gemini 图片生成模型
                'prompt': prompt,
                'n': 1,
                'size': size,
                'response_format': 'url'
            }

            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()

            data = response.json()
            image_url = data['data'][0]['url']

            # 下载图片
            image_path = self._download_image(image_url)
            logger.info(f"✅ Gemini 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"Gemini 图片生成失败: {str(e)}")
            raise

    def _download_image(self, url: str) -> Path:
        """下载图片到本地"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gemini_{timestamp}.png"
        filepath = self.output_dir / filename

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath


if __name__ == '__main__':
    # 测试
    client = GeminiClient()
    if client.available:
        result = client.generate("写一句关于AI教育的金句")
        print(f"生成结果: {result}")
    else:
        print("Gemini 客户端不可用")
