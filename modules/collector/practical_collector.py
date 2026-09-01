"""
实用的实时选题采集器
使用 RSS 源和可访问的静态页面
"""
import subprocess
import json
import re
import feedparser
from typing import List, Dict
from datetime import datetime

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('practical_collector', 'collector.log')


class PracticalCollector:
    """实用的实时采集器"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)

        # RSS 源列表（可直接访问）
        self.rss_sources = [
            {
                'name': '中国教育新闻网',
                'url': 'http://www.jyb.cn/rss/jyxw.xml',
                'keywords': ['教育', '留学', '学校', '学生', '家长', 'AI']
            },
            {
                'name': '新华网教育',
                'url': 'http://education.news.cn/education.xml',
                'keywords': ['教育', '留学', '政策', '学校']
            },
            {
                'name': '人民网教育',
                'url': 'http://edu.people.com.cn/rss/edu.xml',
                'keywords': ['教育', '留学', '考试', '政策']
            }
        ]

    def collect_from_rss(self, source: Dict) -> List[Dict]:
        """从 RSS 源采集"""
        logger.info(f"采集 RSS: {source['name']}")

        try:
            feed = feedparser.parse(source['url'])

            if not feed.entries:
                logger.warning(f"{source['name']} RSS 无内容")
                return []

            topics = []
            for entry in feed.entries[:10]:  # 取前10条
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '')[:100]

                # 关键词过滤
                if any(kw in title for kw in source['keywords']):
                    topics.append({
                        'title': title,
                        'excerpt': summary or f"{title}的相关内容",
                        'url': link,
                        'source': source['name'],
                        'heat_score': '中',
                        'collected_at': datetime.now().isoformat()
                    })

            logger.info(f"{source['name']} 采集到 {len(topics)} 个选题")
            return topics

        except Exception as e:
            logger.error(f"{source['name']} RSS 采集失败: {str(e)}")
            return []

    def collect_via_openclaw(self) -> List[Dict]:
        """通过 OpenClaw 生成补充选题"""
        logger.info("通过 OpenClaw 生成补充选题")

        prompt = """基于当前教育领域的热点趋势，生成 10 个高质量选题。

要求：
1. 与留学规划、AI教育、家庭教育、教育政策相关
2. 符合 2026 年 2 月的时事背景
3. 具有讨论价值和时效性
4. 适合 K博士（教育博士）的专业定位

输出 JSON 格式：
[
  {
    "title": "选题标题",
    "excerpt": "简短摘要（100字内）",
    "url": "https://example.com",
    "source": "AI生成",
    "heat_score": "高"
  }
]

只返回 JSON 数组。"""

        try:
            result = subprocess.run(
                ['openclaw', 'agent', '--agent', 'main', '--local', '--json', '-m', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return []

            output_json = json.loads(result.stdout)
            payloads = output_json.get('payloads', [])
            response_text = ' '.join([p.get('text', '') for p in payloads if p.get('text')])

            topics = self._extract_json(response_text)

            if topics:
                logger.info(f"OpenClaw 生成 {len(topics)} 个补充选题")
                return topics

            return []

        except Exception as e:
            logger.error(f"OpenClaw 生成失败: {str(e)}")
            return []

    def _extract_json(self, text: str) -> List[Dict]:
        """从文本中提取 JSON"""
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
        logger.info("开始实用实时选题采集")
        logger.info("=" * 60)

        all_topics = []

        # 1. 采集 RSS 源
        for source in self.rss_sources:
            topics = self.collect_from_rss(source)
            all_topics.extend(topics)

        # 2. OpenClaw 生成补充选题
        openclaw_topics = self.collect_via_openclaw()
        all_topics.extend(openclaw_topics)

        if not all_topics:
            logger.warning("所有采集方式都失败")
            return []

        # 去重
        seen_titles = set()
        unique_topics = []
        for topic in all_topics:
            title = topic.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_topics.append(topic)

        logger.info(f"采集完成，共 {len(unique_topics)} 个选题（去重后）")

        if len(unique_topics) >= 10:
            self._save_topics(unique_topics)
            return unique_topics
        else:
            logger.warning(f"选题数量不足（{len(unique_topics)}个）")
            return []

    def _save_topics(self, topics: List[Dict]):
        """保存选题"""
        date_str = get_date_str()

        data = {
            'date': date_str,
            'total_count': len(topics),
            'topics': topics
        }

        save_json(data, self.topics_dir / f'topics_{date_str}.json')
        save_json(data, self.topics_dir / 'latest.json')

        logger.info(f"选题已保存: {len(topics)} 个")


if __name__ == '__main__':
    collector = PracticalCollector()
    topics = collector.run()

    if topics:
        print(f"\n✅ 采集成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:15], 1):
            print(f"{i}. {topic['title']}")
            print(f"   来源: {topic.get('source', '未知')}")
            print()
    else:
        print("\n❌ 采集失败")
