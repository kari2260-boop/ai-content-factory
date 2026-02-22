"""
Gemini API 客户端（备用）
支持第三方中转 API
"""
import os
import requests
import google.generativeai as genai

from modules.utils import setup_logger
from modules.config import GEMINI_API_KEY

logger = setup_logger('gemini_client', 'generator.log')


class GeminiClient:
    """Gemini API 客户端"""

    def __init__(self):
        if not GEMINI_API_KEY:
            logger.warning("未找到 GEMINI_API_KEY 环境变量，Gemini 客户端不可用")
            self.available = False
            return

        # 检查是否使用第三方中转
        self.base_url = os.getenv('GEMINI_BASE_URL')
        self.use_proxy = bool(self.base_url)

        if self.use_proxy:
            logger.info(f"使用第三方中转 API: {self.base_url}")
            self.available = True
        else:
            # 使用官方 API
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True

    def generate(self, prompt: str) -> str:
        """生成内容"""
        if not self.available:
            raise ValueError("Gemini 客户端不可用")

        try:
            logger.info("调用 Gemini API 生成内容")

            if self.use_proxy:
                # 使用第三方中转 API
                content = self._generate_via_proxy(prompt)
            else:
                # 使用官方 API
                response = self.model.generate_content(prompt)
                content = response.text

            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"Gemini API 调用失败: {str(e)}")
            raise

    def _generate_via_proxy(self, prompt: str) -> str:
        """通过第三方中转 API 生成内容（OpenAI 兼容格式）"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GEMINI_API_KEY}'
        }

        payload = {
            'model': 'gemini-2.5-pro',  # 使用最新的 Gemini 模型
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 4096
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()
        content = data['choices'][0]['message']['content']
        return content


if __name__ == '__main__':
    # 测试
    client = GeminiClient()
    if client.available:
        result = client.generate("写一句关于AI教育的金句")
        print(f"生成结果: {result}")
    else:
        print("Gemini 客户端不可用")
