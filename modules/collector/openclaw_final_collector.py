"""
最终版本：通过 OpenClaw Agent 使用 web_search 采集实时热点
"""
import subprocess
import json
from typing import List, Dict
from datetime import datetime

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('openclaw_final_collector', 'collector.log')


class OpenClawFinalCollector:
    """通过 OpenClaw Agent web_search 采集实时热点"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)

    def collect_via_agent(self) -> List[Dict]:
        """通过 OpenClaw Agent 采集选题"""
        logger.info("通过 OpenClaw Agent web_search 执行选题采集")

        task_prompt = """请帮我采集今日教育领域的实时热点选题。

使用 web_search 工具搜索以下关键词，获取最新热点：
- "教育热点 2026"
- "留学申请 最新"
- "AI教育 讨论"
- "家庭教育 话题"

要求：
1. 采集 15-20 个选题
2. 必须是最近3天内的热点
3. 与留学规划、AI教育、家庭教育、教育政策相关
4. 输出 JSON 数组格式：

[
  {
    "title": "选题标题",
    "excerpt": "简短摘要（100字内）",
    "url": "来源链接",
    "source": "数据源名称",
    "heat_score": "高/中/低"
  }
]

直接返回 JSON 数组，不要其他说明。"""

        try:
            result = subprocess.run(
                ['openclaw', 'agent', '--agent', 'main', '--local', '--json', '-m', task_prompt],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"OpenClaw Agent 执行失败: {result.stderr}")
                return []

            # 解析 JSON 输出
            try:
                output_json = json.loads(result.stdout)
                # 提取 payloads 中的文本
                payloads = output_json.get('payloads', [])
                response_text = ' '.join([p.get('text', '') for p in payloads if p.get('text')])
            except:
                response_text = result.stdout

            # 提取选题 JSON
            topics = self._extract_json_from_output(response_text)

            if topics and len(topics) >= 10:
                logger.info(f"OpenClaw Agent 采集成功，获得 {len(topics)} 个选题")
                return topics
            else:
                logger.warning(f"OpenClaw Agent 返回选题不足: {len(topics) if topics else 0}")
                return []

        except subprocess.TimeoutExpired:
            logger.error("OpenClaw Agent 执行超时")
            return []
        except Exception as e:
            logger.error(f"OpenClaw Agent 采集异常: {str(e)}")
            return []

    def _extract_json_from_output(self, output: str) -> List[Dict]:
        """从输出中提取 JSON"""
        import re

        # 尝试直接解析
        try:
            data = json.loads(output)
            if isinstance(data, list):
                return data
        except:
            pass

        # 查找 JSON 代码块
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\[\s*\{[^\]]*"title"[^\]]*\}\s*\]'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, output, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list) and len(data) > 0:
                        return data
                except:
                    continue

        return []

    def run(self) -> List[Dict]:
        """运行采集流程"""
        logger.info("=" * 50)
        logger.info("开始 OpenClaw Agent 实时选题采集")
        logger.info("=" * 50)

        # 采集选题
        topics = self.collect_via_agent()

        if not topics or len(topics) < 10:
            logger.warning(f"采集到的选题不足（{len(topics) if topics else 0}个）")
            return []

        # 添加时间戳
        for topic in topics:
            topic['collected_at'] = datetime.now().isoformat()

        # 保存结果
        self._save_topics(topics)

        logger.info("=" * 50)
        logger.info(f"OpenClaw Agent 采集完成，共 {len(topics)} 个选题")
        logger.info("=" * 50)

        return topics

    def _save_topics(self, topics: List[Dict]):
        """保存选题"""
        date_str = get_date_str()

        save_json({
            'date': date_str,
            'total_count': len(topics),
            'topics': topics
        }, self.topics_dir / f"topics_{date_str}.json")

        save_json({
            'date': date_str,
            'total_count': len(topics),
            'topics': topics
        }, self.topics_dir / 'latest.json')

        logger.info(f"选题已保存")


if __name__ == '__main__':
    collector = OpenClawFinalCollector()
    topics = collector.run()

    if topics:
        print(f"\n✅ 采集成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:10], 1):
            print(f"{i}. {topic['title']}")
            print(f"   来源: {topic.get('source', '未知')}")
            print()
    else:
        print("\n❌ 采集失败，将使用备用数据")
