"""
通过 OpenClaw Agent 命令执行选题采集
使用 openclaw agent --local 本地执行
"""
import subprocess
import json
from typing import List, Dict
from datetime import datetime

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR
from modules.collector.scorer import TopicScorer

logger = setup_logger('openclaw_agent_collector', 'collector.log')


class OpenClawAgentCollector:
    """通过 OpenClaw Agent 本地执行采集"""

    def __init__(self, user_id: str = 'dr_k'):
        self.user_id = user_id
        self.topics_dir = DATA_DIR / 'users' / user_id / 'topics'
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self.scorer = TopicScorer()

    def collect_via_agent(self) -> List[Dict]:
        """通过 OpenClaw Agent 采集选题"""
        logger.info("通过 OpenClaw Agent 本地执行选题采集")

        task_prompt = """请帮我采集今日教育领域的最新热点选题。

任务要求：
1. 数据源：知乎教育热榜、微博教育热搜、今日头条教育频道、百度热搜教育相关
2. 采集数量：15-25个选题
3. 筛选标准：今天或最近3天内的热点，与留学规划、AI教育、家庭教育、教育政策相关
4. 输出格式：JSON数组

[{"title":"选题标题","excerpt":"简短摘要100字内","url":"来源链接","source":"数据源名称","heat_score":"热度"}]

重要：访问实时数据源，确保是今天最新热点，直接返回JSON数组。"""

        try:
            # 使用专用采集 agent，避免落到主会话并因默认模型超时
            result = subprocess.run(
                [
                    'openclaw',
                    'agent',
                    '--local',
                    '--agent',
                    'topic-collector-openai',
                    '--json',
                    '--timeout',
                    '180',
                    '-m',
                    task_prompt,
                ],
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
                response_text = output_json.get('response', '') or output_json.get('content', '')
            except:
                response_text = result.stdout

            # 提取选题 JSON
            topics = self._extract_json_from_output(response_text)

            if topics and len(topics) >= 5:
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
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, output, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass

        # 查找数组
        array_pattern = r'\[\s*\{[^\]]*"title"[^\]]*\}\s*\]'
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
        logger.info("开始 OpenClaw Agent 本地选题采集")
        logger.info("=" * 50)

        # 采集选题
        topics = self.collect_via_agent()

        if not topics:
            logger.warning(f"采集到的选题不足（{len(topics) if topics else 0}个）")
            return []

        # 添加时间戳
        for topic in topics:
            topic['collected_at'] = datetime.now().isoformat()

        if any('total_score' not in topic for topic in topics):
            topics = self.scorer.score_topics_fast(topics)

        # 保存结果
        self._save_topics(topics)

        logger.info("=" * 50)
        logger.info(f"OpenClaw Agent 采集完成，共 {len(topics)} 个选题")
        logger.info("=" * 50)

        return topics

    def _save_topics(self, topics: List[Dict]):
        """保存选题"""
        date_str = get_date_str()
        filename = f"topics_{date_str}.json"
        filepath = self.topics_dir / filename

        save_json({
            'date': date_str,
            'total_count': len(topics),
            'high_score_count': len([t for t in topics if t.get('total_score', 0) >= 25]),
            'topics': topics
        }, filepath)

        # 保存 latest.json
        latest_path = self.topics_dir / 'latest.json'
        save_json({
            'date': date_str,
            'total_count': len(topics),
            'high_score_count': len([t for t in topics if t.get('total_score', 0) >= 25]),
            'topics': topics
        }, latest_path)

        logger.info(f"选题已保存到: {filepath}")


if __name__ == '__main__':
    collector = OpenClawAgentCollector()
    topics = collector.run()

    if topics:
        print(f"\n✅ 采集成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:10], 1):
            print(f"{i}. {topic['title']}")
            print(f"   来源: {topic['source']}")
            print()
    else:
        print("\n❌ 采集失败")
