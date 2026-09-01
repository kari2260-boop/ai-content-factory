"""
Claude API 客户端
负责调用 Claude API 生成各种格式的内容
"""
import os
from typing import Dict, List

from modules.llm_client import LLMClient
from modules.utils import setup_logger
from modules.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL

logger = setup_logger('claude_client', 'generator.log')


class ClaudeClient:
    """Claude API 客户端"""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("未找到 ANTHROPIC_AUTH_TOKEN 环境变量")

        self.model = ANTHROPIC_MODEL
        self.client = LLMClient(
            api_key=ANTHROPIC_API_KEY,
            base_url=ANTHROPIC_BASE_URL,
            model=self.model,
        )

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """生成内容"""
        try:
            logger.info(f"调用 AI API 生成内容 (model={self.model}, max_tokens={max_tokens})")

            content = self.client.generate(prompt, max_tokens=max_tokens)
            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"AI API 调用失败: {str(e)}")
            raise

    def generate_with_context(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """带系统提示词生成内容"""
        try:
            logger.info(f"调用 AI API 生成内容（带系统提示词，model={self.model}）")

            content = self.client.generate(
                user_prompt,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"AI API 调用失败: {str(e)}")
            raise


if __name__ == '__main__':
    # 测试
    client = ClaudeClient()
    result = client.generate("写一句关于AI教育的金句", max_tokens=100)
    print(f"生成结果: {result}")
