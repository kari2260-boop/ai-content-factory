"""
使用 Claude API 直接生成选题的采集器
当外部数据源失效时的备用方案
"""
import os
import json
from typing import List, Dict
from datetime import datetime
from anthropic import Anthropic

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('claude_collector', 'collector.log')


class ClaudeCollector:
    """使用 Claude API 生成选题"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)

        # 初始化 Claude 客户端
        api_key = os.getenv('ANTHROPIC_AUTH_TOKEN')
        if not api_key:
            raise ValueError("未找到 ANTHROPIC_AUTH_TOKEN 环境变量")

        self.client = Anthropic(api_key=api_key)

    def generate_topics(self, count: int = 15) -> List[Dict]:
        """使用 Claude 生成选题"""
        logger.info(f"使用 Claude API 生成 {count} 个选题")

        prompt = f"""你是 K博士的内容策划助手。请基于当前教育领域的热点趋势，生成 {count} 个高质量选题。

要求：
1. 与留学规划、AI教育、家庭教育、教育政策相关
2. 符合 2026 年 2 月的时事背景
3. 具有讨论价值和时效性
4. 适合 K博士（教育博士）的专业定位
5. 选题要有深度，避免泛泛而谈

输出 JSON 格式：
[
  {{
    "title": "选题标题（简洁有力，15字内）",
    "excerpt": "简短摘要（说明为什么这个话题重要，100字内）",
    "url": "https://example.com",
    "source": "AI生成",
    "heat_score": "高/中/低"
  }}
]

只返回 JSON 数组，不要其他内容。"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 提取响应文本
            response_text = response.content[0].text

            # 解析 JSON
            topics = self._extract_json(response_text)

            if not topics:
                logger.error("Claude 返回的内容无法解析为 JSON")
                return []

            # 添加时间戳
            for topic in topics:
                topic['collected_at'] = datetime.now().isoformat()

            logger.info(f"Claude 生成 {len(topics)} 个选题")
            return topics

        except Exception as e:
            logger.error(f"Claude API 调用失败: {str(e)}")
            return []

    def _extract_json(self, text: str) -> List[Dict]:
        """从文本中提取 JSON"""
        import re

        # 尝试多种模式
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\[\s*\{[^\]]*"title"[^\]]*\}\s*\]'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list) and len(data) > 0:
                        return data
                except:
                    continue

        # 直接尝试解析整个文本
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except:
            pass

        return []

    def run(self) -> List[Dict]:
        """运行采集流程"""
        logger.info("=" * 60)
        logger.info("使用 Claude API 生成选题")
        logger.info("=" * 60)

        topics = self.generate_topics(count=15)

        if not topics:
            logger.error("选题生成失败")
            return []

        # 保存选题
        self._save_topics(topics)
        return topics

    def _save_topics(self, topics: List[Dict]):
        """保存选题"""
        date_str = get_date_str()

        data = {
            'date': date_str,
            'total_count': len(topics),
            'topics': topics,
            'method': 'claude_api'
        }

        save_json(data, self.topics_dir / f'topics_{date_str}.json')
        save_json(data, self.topics_dir / 'latest.json')

        logger.info(f"选题已保存: {len(topics)} 个")


if __name__ == '__main__':
    collector = ClaudeCollector()
    topics = collector.run()

    if topics:
        print(f"\n✅ 生成成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:10], 1):
            print(f"{i}. {topic['title']}")
            print(f"   {topic.get('excerpt', '')[:50]}...")
            print()
    else:
        print("\n❌ 生成失败")
