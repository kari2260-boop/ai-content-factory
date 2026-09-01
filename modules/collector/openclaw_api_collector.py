"""
通过 OpenClaw Gateway API 执行选题采集
直接调用 Gateway API，不依赖 message send 命令
"""
import requests
import json
from typing import List, Dict
from datetime import datetime

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR
from modules.config import OPENCLAW_GATEWAY_URL

logger = setup_logger('openclaw_api_collector', 'collector.log')


class OpenClawAPICollector:
    """通过 OpenClaw Gateway API 执行采集"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)
        self.gateway_url = OPENCLAW_GATEWAY_URL.replace('ws://', 'http://').replace('wss://', 'https://')

    def collect_via_api(self) -> List[Dict]:
        """通过 Gateway API 采集选题"""
        logger.info("通过 OpenClaw Gateway API 执行选题采集")

        task_prompt = """
请帮我采集今日（2026年2月19日）教育领域的最新热点选题。

**任务要求：**

1. **数据源**（请实时访问）：
   - 知乎教育话题热榜
   - 微博教育热搜
   - 今日头条教育频道
   - 百度热搜教育相关
   - 或其他你能访问的实时教育资讯源

2. **采集数量**：15-25个选题

3. **筛选标准**：
   - 必须是今天或最近3天内的热点
   - 与"留学规划"、"AI教育"、"家庭教育"、"教育政策"相关
   - 有讨论热度和时效性
   - 适合K博士（教育博士）的专业定位

4. **输出格式**（JSON数组）：
```json
[
  {
    "title": "选题标题",
    "excerpt": "简短摘要（100字内）",
    "url": "来源链接",
    "source": "数据源名称（如：知乎、微博、今日头条）",
    "heat_score": "热度描述（如：高、中、低）"
  }
]
```

**重要**：
- 请访问实时数据源，不要编造内容
- 确保选题是今天的最新热点
- 直接返回 JSON 数组，不要其他说明
"""

        try:
            # 调用 Gateway API
            response = requests.post(
                f"{self.gateway_url}/api/chat",
                json={
                    "message": task_prompt,
                    "stream": False
                },
                timeout=90
            )

            if response.status_code != 200:
                logger.error(f"Gateway API 调用失败: {response.status_code}")
                return []

            result = response.json()
            output = result.get('response', '')

            # 提取 JSON
            topics = self._extract_json_from_output(output)

            if topics:
                logger.info(f"OpenClaw API 采集成功，获得 {len(topics)} 个选题")
                return topics
            else:
                logger.warning("OpenClaw API 返回结果无法解析")
                return []

        except Exception as e:
            logger.error(f"OpenClaw API 采集异常: {str(e)}")
            return []

    def _extract_json_from_output(self, output: str) -> List[Dict]:
        """从输出中提取 JSON"""
        try:
            return json.loads(output)
        except:
            pass

        # 尝试查找 JSON 代码块
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, output, re.DOTALL)

        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass

        # 尝试查找数组
        array_pattern = r'\[\s*\{.*?\}\s*\]'
        matches = re.findall(array_pattern, output, re.DOTALL)

        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass

        return []

    def run(self) -> List[Dict]:
        """运行采集流程"""
        logger.info("=" * 50)
        logger.info("开始 OpenClaw API 选题采集")
        logger.info("=" * 50)

        # 采集选题
        topics = self.collect_via_api()

        if not topics or len(topics) < 5:
            logger.warning(f"采集到的选题不足（{len(topics)}个），使用备用方案")
            return self._use_fallback()

        # 添加时间戳
        for topic in topics:
            topic['collected_at'] = datetime.now().isoformat()

        # 保存结果
        self._save_topics(topics)

        return topics

    def _use_fallback(self) -> List[Dict]:
        """使用备用方案"""
        logger.info("使用备用选题数据")

        # 返回空列表，让主采集器使用传统方式
        return []

    def _save_topics(self, topics: List[Dict]):
        """保存选题"""
        date_str = get_date_str()
        filename = f"topics_{date_str}.json"
        filepath = self.topics_dir / filename

        save_json({
            'date': date_str,
            'total_count': len(topics),
            'topics': topics
        }, filepath)

        # 保存 latest.json
        latest_path = self.topics_dir / 'latest.json'
        save_json({
            'date': date_str,
            'total_count': len(topics),
            'topics': topics
        }, latest_path)

        logger.info(f"选题已保存到: {filepath}")


if __name__ == '__main__':
    collector = OpenClawAPICollector()
    topics = collector.run()

    print(f"\n采集到 {len(topics)} 个选题")
    for i, topic in enumerate(topics[:5], 1):
        print(f"\n{i}. {topic['title']}")
        print(f"   来源: {topic['source']}")
