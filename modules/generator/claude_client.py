"""
Claude API 客户端
负责调用 Claude API 生成各种格式的内容
"""
import os
from typing import Dict, List
from anthropic import Anthropic

from modules.utils import setup_logger
from modules.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL

logger = setup_logger('claude_client', 'generator.log')


class ClaudeClient:
    """Claude API 客户端"""

    def __init__(self):
        self.available = False
        self.client = None

        if ANTHROPIC_API_KEY:
            try:
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)
                self.model = "claude-sonnet-4-6"
                self.available = True
                logger.info("Claude API 初始化成功")
            except Exception as e:
                logger.warning(f"Claude API 初始化失败: {e}")
                self.available = False
        else:
            logger.warning("未配置 ANTHROPIC_AUTH_TOKEN，Claude API 不可用")

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """生成内容"""
        if not self.available:
            raise RuntimeError("Claude API 不可用，请检查配置或使用其他 AI 服务")

        try:
            logger.info(f"调用 Claude API 生成内容 (max_tokens={max_tokens})")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text
            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"Claude API 调用失败: {str(e)}")
            raise

    def generate_with_context(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """带系统提示词生成内容"""
        try:
            logger.info(f"调用 Claude API 生成内容（带系统提示词）")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            content = response.content[0].text
            logger.info(f"生成成功，内容长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"Claude API 调用失败: {str(e)}")
            raise


if __name__ == '__main__':
    # 测试
    client = ClaudeClient()
    result = client.generate("写一句关于AI教育的金句", max_tokens=100)
    print(f"生成结果: {result}")
