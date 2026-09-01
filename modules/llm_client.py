"""
统一大模型客户端。

根据模型名前缀自动选择 Anthropic Messages API 或 OpenAI 兼容 Chat Completions API。
"""
import json
import urllib.request
from typing import Dict, List, Optional

from anthropic import Anthropic


class LLMClient:
    """兼容 Claude 和 OpenAI-compatible 模型的轻量客户端。"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._anthropic_client = None

        if self._uses_anthropic_messages:
            self._anthropic_client = Anthropic(api_key=api_key, base_url=base_url)

    @property
    def _uses_anthropic_messages(self) -> bool:
        return self.model.startswith('claude-')

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本。"""
        if self._uses_anthropic_messages:
            return self._generate_anthropic(prompt, max_tokens, system_prompt)
        return self._generate_openai_compatible(prompt, max_tokens, system_prompt)

    def _generate_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: Optional[str],
    ) -> str:
        payload = {
            'model': self.model,
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if system_prompt:
            payload['system'] = system_prompt

        response = self._anthropic_client.messages.create(**payload)

        for block in response.content:
            if block.type == 'text':
                return block.text

        raise ValueError("API 返回内容中未找到文本块")

    def _generate_openai_compatible(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: Optional[str],
    ) -> str:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        body = json.dumps({
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens,
        }).encode('utf-8')

        request = urllib.request.Request(
            f'{self.base_url}/v1/chat/completions',
            data=body,
            method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
        )

        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode('utf-8'))

        try:
            content = data['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"API 返回格式异常: {data}") from exc

        if not content:
            raise ValueError("API 返回内容为空")

        return content
