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

        # 可访问的热点网站列表 - 优化版，包含更多高质量教育资源
        self.sources = [
            # 主流新闻媒体教育频道
            {
                'name': '澎湃新闻教育频道',
                'url': 'https://www.thepaper.cn/channel_25950',
                'keywords': ['教育', '留学', '学校', '学生', '家长', '政策']
            },
            {
                'name': '新浪教育',
                'url': 'https://edu.sina.com.cn/',
                'keywords': ['教育', '留学', 'AI', '培训', '国际教育']
            },
            {
                'name': '搜狐教育',
                'url': 'https://learning.sohu.com/',
                'keywords': ['教育', '留学', '考试', '政策', '家庭教育']
            },
            {
                'name': '腾讯教育',
                'url': 'https://edu.qq.com/',
                'keywords': ['教育', '留学', '培训', '政策', 'AI教育']
            },
            # 垂直教育媒体
            {
                'name': '芥末堆',
                'url': 'https://www.jiemodui.com/',
                'keywords': ['教育科技', '在线教育', 'AI', '留学', '政策']
            },
            {
                'name': '多知网',
                'url': 'http://www.duozhi.com/',
                'keywords': ['教育行业', '留学', '培训', '政策', '趋势']
            },
            # 知识社区热点
            {
                'name': '知乎教育话题',
                'url': 'https://www.zhihu.com/topic/19552832/hot',
                'keywords': ['教育', '留学', '学习方法', '家庭教育', 'AI']
            },
            # 官方教育资讯
            {
                'name': '中国教育在线',
                'url': 'https://www.eol.cn/',
                'keywords': ['教育政策', '留学', '高考', '考研', '国际教育']
            }
        ]

    def collect_from_source(self, source: Dict) -> List[Dict]:
        """从单个数据源采集"""
        logger.info(f"采集数据源: {source['name']}")

        prompt = f"""请使用 web_fetch 工具访问 {source['url']} 并提取今日最热门的教育资讯。

任务要求：
1. 访问该网站首页，抓取最新、最热门的内容
2. 重点关注这些关键词：{', '.join(source['keywords'])}
3. 提取标题、摘要和链接
4. 筛选出 5-8 个最有价值的热点话题
5. 优先选择：
   - 今日或近3天内的新闻
   - 讨论度高、有争议性的话题
   - 与留学规划、AI教育、家庭教育、教育政策相关
   - 能引发家长共鸣的内容

输出格式（纯 JSON 数组）：
[
  {{
    "title": "完整标题",
    "excerpt": "核心内容摘要（80-120字）",
    "url": "原文链接",
    "source": "{source['name']}",
    "heat_score": "高"
  }}
]

注意：只返回 JSON 数组，不要任何解释说明。"""

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

    def run(self, max_sources: int = None) -> List[Dict]:
        """运行完整采集流程

        Args:
            max_sources: 最多采集几个数据源（None=全部）
        """
        logger.info("=" * 60)
        logger.info("开始实时选题采集（OpenClaw + 高质量网站）")
        logger.info("=" * 60)

        all_topics = []
        success_count = 0
        fail_count = 0

        # 选择要采集的数据源
        sources_to_collect = self.sources[:max_sources] if max_sources else self.sources
        logger.info(f"计划采集 {len(sources_to_collect)} 个数据源")

        # 逐个采集数据源
        for i, source in enumerate(sources_to_collect, 1):
            logger.info(f"[{i}/{len(sources_to_collect)}] 采集: {source['name']}")

            topics = self.collect_from_source(source)

            if topics:
                all_topics.extend(topics)
                success_count += 1
                logger.info(f"✓ {source['name']} 成功，获得 {len(topics)} 个选题")
            else:
                fail_count += 1
                logger.warning(f"✗ {source['name']} 失败")

            # 避免请求过快
            import time
            if i < len(sources_to_collect):  # 最后一个不需要等待
                time.sleep(2)

        logger.info(f"采集统计：成功 {success_count} 个，失败 {fail_count} 个")

        if not all_topics:
            logger.error("所有数据源采集失败")
            return []

        # 去重和清洗
        unique_topics = self._deduplicate_and_clean(all_topics)
        logger.info(f"去重后剩余 {len(unique_topics)} 个选题")

        if len(unique_topics) >= 8:  # 降低阈值，更灵活
            # 保存结果
            self._save_topics(unique_topics)
            logger.info(f"✅ 采集成功！共 {len(unique_topics)} 个高质量选题")
            return unique_topics
        else:
            logger.warning(f"选题数量不足（{len(unique_topics)}个，需要至少8个）")
            return []

    def _deduplicate_and_clean(self, topics: List[Dict]) -> List[Dict]:
        """去重和清洗选题"""
        seen_titles = set()
        unique_topics = []

        for topic in topics:
            title = topic.get('title', '').strip()

            # 跳过空标题
            if not title or len(title) < 10:
                continue

            # 标题去重（完全相同）
            if title in seen_titles:
                continue

            # 相似标题去重（前15个字符）
            title_prefix = title[:15]
            if any(title_prefix in seen for seen in seen_titles):
                continue

            seen_titles.add(title)
            topic['collected_at'] = datetime.now().isoformat()

            # 确保必要字段存在
            if 'excerpt' not in topic or not topic['excerpt']:
                topic['excerpt'] = title[:100]
            if 'heat_score' not in topic:
                topic['heat_score'] = '中'

            unique_topics.append(topic)

        return unique_topics

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
