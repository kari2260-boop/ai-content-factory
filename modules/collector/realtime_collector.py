"""
真正的实时选题采集器
通过 OpenClaw Agent 使用 web_fetch 抓取多个热点网站
"""
import subprocess
import json
import re
from typing import List, Dict
from datetime import datetime

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('realtime_collector', 'collector.log')


class RealtimeCollector:
    """实时选题采集器"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)

        # 可访问的热点网站列表
        self.sources = [
            {
                'name': '澎湃新闻教育频道',
                'url': 'https://www.thepaper.cn/channel_25950',
                'keywords': ['教育', '留学', '学校', '学生', '家长']
            },
            {
                'name': '新浪教育',
                'url': 'https://edu.sina.com.cn/',
                'keywords': ['教育', '留学', 'AI', '培训']
            },
            {
                'name': '搜狐教育',
                'url': 'https://learning.sohu.com/',
                'keywords': ['教育', '留学', '考试', '政策']
            },
            {
                'name': '腾讯教育',
                'url': 'https://edu.qq.com/',
                'keywords': ['教育', '留学', '培训', '政策']
            }
        ]

    def collect_from_source(self, source: Dict) -> List[Dict]:
        """从单个数据源采集"""
        logger.info(f"采集数据源: {source['name']}")

        prompt = f"""请访问 {source['url']} 并提取今日教育热点。

任务：
1. 使用 web_fetch 工具访问该网站
2. 提取页面中的新闻标题和链接
3. 筛选与教育相关的内容（关键词：{', '.join(source['keywords'])}）
4. 返回 5-8 个最新的热点

输出 JSON 格式：
[
  {{
    "title": "新闻标题",
    "excerpt": "简短摘要",
    "url": "完整链接",
    "source": "{source['name']}",
    "heat_score": "高"
  }}
]

只返回 JSON 数组，不要其他内容。"""

        try:
            result = subprocess.run(
                ['openclaw', 'agent', '--agent', 'main', '--local', '--json', '-m', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"{source['name']} 采集失败: {result.stderr}")
                return []

            # 解析输出
            output_json = json.loads(result.stdout)
            payloads = output_json.get('payloads', [])
            response_text = ' '.join([p.get('text', '') for p in payloads if p.get('text')])

            # 提取 JSON
            topics = self._extract_json(response_text)

            if topics:
                logger.info(f"{source['name']} 采集到 {len(topics)} 个选题")
                return topics
            else:
                logger.warning(f"{source['name']} 未提取到选题")
                return []

        except subprocess.TimeoutExpired:
            logger.error(f"{source['name']} 采集超时")
            return []
        except Exception as e:
            logger.error(f"{source['name']} 采集异常: {str(e)}")
            return []

    def _extract_json(self, text: str) -> List[Dict]:
        """从文本中提取 JSON"""
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

        # 尝试直接解析
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except:
            pass

        return []

    def run(self) -> List[Dict]:
        """运行完整采集流程"""
        logger.info("=" * 60)
        logger.info("开始实时选题采集")
        logger.info("=" * 60)

        all_topics = []

        # 逐个采集数据源
        for source in self.sources:
            topics = self.collect_from_source(source)
            all_topics.extend(topics)

            # 避免请求过快
            import time
            time.sleep(3)

        if not all_topics:
            logger.warning("所有数据源采集失败")
            return []

        # 去重
        seen_titles = set()
        unique_topics = []
        for topic in all_topics:
            title = topic.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                topic['collected_at'] = datetime.now().isoformat()
                unique_topics.append(topic)

        logger.info(f"采集完成，共 {len(unique_topics)} 个选题（去重后）")

        if len(unique_topics) >= 10:
            # 保存结果
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
    collector = RealtimeCollector()
    topics = collector.run()

    if topics:
        print(f"\n✅ 实时采集成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:15], 1):
            print(f"{i}. {topic['title']}")
            print(f"   来源: {topic.get('source', '未知')}")
            print()
    else:
        print("\n❌ 实时采集失败")
