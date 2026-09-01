"""
数据源采集模块
支持知乎、Google Trends、RSS 等多个数据源
"""
import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict
from datetime import datetime
import time

from modules.utils import setup_logger

logger = setup_logger('sources', 'collector.log')


class TopicSource:
    """选题数据源基类"""

    def __init__(self, name: str):
        self.name = name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def fetch(self) -> List[Dict]:
        """获取选题列表"""
        raise NotImplementedError


class ZhihuSource(TopicSource):
    """知乎热榜数据源"""

    def __init__(self):
        super().__init__('zhihu')
        self.api_url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total'

    def fetch(self) -> List[Dict]:
        """获取知乎热榜"""
        try:
            logger.info(f"开始采集 {self.name} 数据源")
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            topics = []

            for item in data.get('data', [])[:10]:
                target = item.get('target', {})
                topics.append({
                    'title': target.get('title', ''),
                    'excerpt': target.get('excerpt', ''),
                    'url': f"https://www.zhihu.com/question/{target.get('id', '')}",
                    'source': self.name,
                    'heat_score': item.get('detail_text', '0').replace('万热度', ''),
                    'collected_at': datetime.now().isoformat()
                })

            logger.info(f"{self.name} 采集完成，获得 {len(topics)} 个选题")
            return topics

        except Exception as e:
            logger.error(f"{self.name} 采集失败: {str(e)}")
            return []


class GoogleTrendsSource(TopicSource):
    """Google Trends 数据源（需要 VPN）"""

    def __init__(self):
        super().__init__('google_trends')
        self.rss_url = 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=CN'

    def fetch(self) -> List[Dict]:
        """获取 Google Trends"""
        try:
            logger.info(f"开始采集 {self.name} 数据源")
            feed = feedparser.parse(self.rss_url)
            topics = []

            for entry in feed.entries[:5]:
                topics.append({
                    'title': entry.title,
                    'excerpt': entry.get('description', '')[:200],
                    'url': entry.link,
                    'source': self.name,
                    'heat_score': 'N/A',
                    'collected_at': datetime.now().isoformat()
                })

            logger.info(f"{self.name} 采集完成，获得 {len(topics)} 个选题")
            return topics

        except Exception as e:
            logger.error(f"{self.name} 采集失败（可能需要 VPN）: {str(e)}")
            return []


class RSSSource(TopicSource):
    """RSS 订阅源"""

    def __init__(self, feed_urls: List[str]):
        super().__init__('rss')
        self.feed_urls = feed_urls

    def fetch(self) -> List[Dict]:
        """获取 RSS 订阅内容"""
        topics = []

        for feed_url in self.feed_urls:
            try:
                logger.info(f"开始采集 RSS: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:3]:
                    topics.append({
                        'title': entry.title,
                        'excerpt': entry.get('summary', '')[:200],
                        'url': entry.link,
                        'source': f"{self.name}_{feed.feed.get('title', 'unknown')}",
                        'heat_score': 'N/A',
                        'collected_at': datetime.now().isoformat()
                    })

                time.sleep(1)  # 避免请求过快

            except Exception as e:
                logger.error(f"RSS 采集失败 {feed_url}: {str(e)}")
                continue

        logger.info(f"{self.name} 采集完成，获得 {len(topics)} 个选题")
        return topics


class TopHubSource(TopicSource):
    """今日热榜 - 聚合多平台热点（推荐数据源）"""

    def __init__(self):
        super().__init__('tophub')
        self.base_url = 'https://tophub.today/'

        # 教育相关强关键词，必须能明确落到教育/学习/升学语境
        self.education_strict_keywords = [
            '教育', '留学', '科研', '学术', '学生',
            '班主任', '班级', '申请', '考试', '培训', '课程', '教学',
            '招生', '国际学校', '双减', '作文', '作业', '课外', '升学',
            '家校', '高考', '考研', '课堂', '老师', '校长', '教育局',
            '托育', '幼儿园', '课后', '学习', '教辅', '文书', '录取',
            '毕业典礼', '新生', '校内', '校园', '教育政策', '中小学', '基础教育'
        ]
        self.family_context_keywords = ['孩子', '家长', '育儿', '儿童', '青少年', '家庭']
        self.learning_context_keywords = [
            '学习', '作业', '考试', '升学', '留学', '课程', '课堂',
            '班主任', '老师', '教育', '学生', '家校', '幼儿园', '培训',
            '毕业', '录取', '文书', '校长', '学校', '大学'
        ]
        self.college_context_keywords = [
            '毕业', '毕业典礼', '录取', '申请', '文书', '招生', '考试',
            '课程', '课堂', '老师', '班主任', '学生', '家长', '教育', '升学',
            '高考', '中考', '考研', '上大学'
        ]
        self.ai_context_keywords = [
            'AI教育', '人工智能教育', 'AI 课堂', 'AI学习', 'AI 作业',
            'AI辅导', 'AI导师', 'AI老师', 'AI Tutor', 'AI 时代', 'AI时代',
            'ChatGPT', 'DeepSeek', '大模型'
        ]
        self.rejection_keywords = [
            '同性恋', '婚姻', '离婚', '出轨', '谈恋爱', '恋爱', '娱乐圈', '明星', '八卦',
            '车企', '汽车', '房价', '股市', '基金', '投资', '游戏', '体育',
            '外交', '政治', '法律', '犯罪', '战争', '天气', '航班',
            'Nature', 'ECCV', 'CVPR', 'ICML', 'NeurIPS', '机器之心', 'AI芯片', '模型', '算法', '框架', 'Oral'
        ]

        # 高优先级平台（与教育/AI相关度高）
        self.high_priority_platforms = [
            '知乎', '36氪', '机器之心', '量子位',
            '虎嗅', '少数派', '掘金', '哔哩哔哩'
        ]

    def _is_relevant(self, title: str) -> bool:
        """判断选题是否与教育/AI育儿相关"""
        text = title.strip()
        if not text:
            return False

        if any(keyword in text for keyword in self.rejection_keywords):
            return False

        strict_hit = any(keyword in text for keyword in self.education_strict_keywords)
        family_hit = any(keyword in text for keyword in self.family_context_keywords)
        learning_hit = any(keyword in text for keyword in self.learning_context_keywords)
        ai_hit = any(keyword in text for keyword in self.ai_context_keywords)
        college_hit = any(keyword in text for keyword in ('大学', '学校')) and any(
            keyword in text for keyword in self.college_context_keywords
        )

        # 1. 直接教育语境命中，保留
        if strict_hit or college_hit:
            return True

        # 2. 家庭/孩子类话题，必须同时落在学习、学校、升学、作业等语境里
        if family_hit and learning_hit:
            return True

        # 3. AI 相关话题，必须明确和教育/学习场景相关
        if ai_hit and learning_hit:
            return True

        return False

    def _extract_platform_name(self, text: str) -> str:
        """从文本中提取平台名称"""
        for platform in self.high_priority_platforms:
            if platform in text:
                return platform
        return 'unknown'

    def fetch(self) -> List[Dict]:
        """获取今日热榜聚合数据"""
        try:
            logger.info(f"开始采集 {self.name} 数据源")
            response = requests.get(self.base_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            topics = []

            # 查找所有链接
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                try:
                    title = link.get_text(strip=True)
                    url = link.get('href', '')

                    # 过滤无效链接
                    if not title or len(title) < 5 or not url.startswith('http'):
                        continue

                    # 关键词过滤
                    if not self._is_relevant(title):
                        continue

                    # 尝试识别平台
                    platform = self._extract_platform_name(title)

                    # 如果标题中没有平台名，尝试从URL识别
                    if platform == 'unknown':
                        if 'zhihu.com' in url:
                            platform = '知乎'
                        elif '36kr.com' in url:
                            platform = '36氪'
                        elif 'jiqizhixin.com' in url:
                            platform = '机器之心'
                        elif 'qbitai.com' in url:
                            platform = '量子位'
                        elif 'huxiu.com' in url:
                            platform = '虎嗅'
                        elif 'bilibili.com' in url:
                            platform = '哔哩哔哩'
                        else:
                            continue  # 跳过非目标平台

                    # 去重检查
                    if any(t['title'] == title for t in topics):
                        continue

                    topics.append({
                        'title': title,
                        'excerpt': f'来自{platform}的热门话题',
                        'url': url,
                        'source': f"{self.name}_{platform}",
                        'heat_score': 'N/A',
                        'platform': platform,
                        'collected_at': datetime.now().isoformat()
                    })

                except Exception as e:
                    continue

            logger.info(f"{self.name} 采集完成，获得 {len(topics)} 个相关选题")
            return topics[:20]  # 限制返回前20条

        except Exception as e:
            logger.error(f"{self.name} 采集失败: {str(e)}")
            return []


class PengpaiSource(TopicSource):
    """澎湃新闻教育频道（国内备用源）"""

    def __init__(self):
        super().__init__('pengpai')
        self.rss_url = 'https://www.thepaper.cn/rss_channel_25950.xml'

    def fetch(self) -> List[Dict]:
        """获取澎湃新闻教育频道"""
        try:
            logger.info(f"开始采集 {self.name} 数据源")
            feed = feedparser.parse(self.rss_url)
            topics = []

            for entry in feed.entries[:5]:
                topics.append({
                    'title': entry.title,
                    'excerpt': entry.get('summary', '')[:200],
                    'url': entry.link,
                    'source': self.name,
                    'heat_score': 'N/A',
                    'collected_at': datetime.now().isoformat()
                })

            logger.info(f"{self.name} 采集完成，获得 {len(topics)} 个选题")
            return topics

        except Exception as e:
            logger.error(f"{self.name} 采集失败: {str(e)}")
            return []


def collect_all_sources() -> List[Dict]:
    """采集所有数据源"""
    all_topics = []

    # 【推荐】今日热榜 - 优先采集
    tophub = TopHubSource()
    all_topics.extend(tophub.fetch())

    # 知乎热榜（备用）
    zhihu = ZhihuSource()
    all_topics.extend(zhihu.fetch())

    # Google Trends（可能需要 VPN）
    google = GoogleTrendsSource()
    all_topics.extend(google.fetch())

    # 澎湃新闻（国内备用）
    pengpai = PengpaiSource()
    all_topics.extend(pengpai.fetch())

    # RSS 订阅
    rss_feeds = [
        'https://rss.sciencenet.cn/index.html',  # 科学网
    ]
    rss = RSSSource(rss_feeds)
    all_topics.extend(rss.fetch())

    logger.info(f"所有数据源采集完成，共获得 {len(all_topics)} 个选题")
    return all_topics


if __name__ == '__main__':
    # 测试采集
    topics = collect_all_sources()
    print(f"采集到 {len(topics)} 个选题")
    for i, topic in enumerate(topics[:3], 1):
        print(f"\n{i}. {topic['title']}")
        print(f"   来源: {topic['source']}")
        print(f"   链接: {topic['url']}")
