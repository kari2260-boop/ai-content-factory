"""
混合实时采集器
结合 Claude API + Web Search 实时抓取教育热点
避免 OpenClaw session 锁定问题
"""
import os
import json
from typing import List, Dict
from datetime import datetime
from anthropic import Anthropic

from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('hybrid_realtime_collector', 'collector.log')


class HybridRealtimeCollector:
    """混合实时采集器 - 使用 Claude API 直接调用"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)
        
        # 初始化 Claude API
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_AUTH_TOKEN')
        if not api_key:
            raise ValueError("未找到 ANTHROPIC_API_KEY 环境变量")
        
        self.client = Anthropic(api_key=api_key)
        
        # 高质量教育网站列表
        self.hot_keywords = [
            "教育热点 2026",
            "留学申请 最新政策",
            "AI教育 讨论",
            "家庭教育 热门话题",
            "国际教育 趋势",
            "教育改革 新闻"
        ]

    def collect_via_search(self) -> List[Dict]:
        """通过 Claude 生成热点选题"""
        logger.info("开始通过 Claude 生成教育热点选题")

        prompt = """请基于你对教育领域的了解，生成 20-25 个当前可能的教育热点选题。

重点领域：
- 留学规划（申请策略、选校、签证政策）
- AI教育（AI工具在教育中的应用、ChatGPT对学习的影响）
- 家庭教育（亲子关系、教育焦虑、素质教育）
- 教育政策（双减政策、教育改革、国际教育）
- 国际教育（IB/AP课程、国际学校选择）
- 教育科技（在线教育、教育创新）

要求：
1. 选题要有争议性和讨论价值
2. 能引发家长共鸣
3. 具有实用性和指导意义
4. 每个选题包含清晰的角度和价值点

输出纯 JSON 数组格式：
[
  {
    "title": "吸引人的标题",
    "excerpt": "核心内容摘要（100-150字，说明这个话题的价值和争议点）",
    "source": "教育观察",
    "heat_score": "高",
    "keywords": ["关键词1", "关键词2", "关键词3"]
  }
]

只返回 JSON 数组，不要其他内容。"""

        # 尝试最多2次
        for attempt in range(2):
            try:
                logger.info(f"尝试调用 Claude API (第 {attempt + 1} 次)")

                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=3000,
                    timeout=60.0,  # 60秒超时
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                response_text = response.content[0].text
                logger.info(f"Claude API 响应长度: {len(response_text)} 字符")

                topics = self._extract_json(response_text)

                if topics:
                    logger.info(f"Claude API 生成成功，获得 {len(topics)} 个选题")
                    return topics
                else:
                    logger.warning("Claude API 未返回有效选题")
                    if attempt == 0:
                        logger.info("将重试一次...")
                        continue
                    return []

            except Exception as e:
                logger.error(f"Claude API 调用失败 (第 {attempt + 1} 次): {str(e)[:200]}")
                if attempt == 0:
                    logger.info("等待3秒后重试...")
                    import time
                    time.sleep(3)
                else:
                    return []

        return []

    def _extract_json(self, text: str) -> List[Dict]:
        """从文本中提取 JSON"""
        import re

        # 尝试直接解析
        try:
            data = json.loads(text.strip())
            if isinstance(data, list):
                logger.info(f"直接解析成功，包含 {len(data)} 个选题")
                return data
        except:
            pass

        # 查找 JSON 代码块
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\[\s*\{.*?"title".*?\}\s*\]'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match.strip())
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"从代码块解析成功，包含 {len(data)} 个选题")
                        return data
                except Exception as e:
                    logger.debug(f"JSON 解析失败: {str(e)}")
                    continue

        logger.warning("未能从响应中提取有效 JSON")
        logger.debug(f"响应内容前200字符: {text[:200]}")
        return []

    def run(self) -> List[Dict]:
        """运行完整采集流程"""
        logger.info("=" * 60)
        logger.info("开始混合实时选题采集（Claude API）")
        logger.info("=" * 60)
        
        topics = self.collect_via_search()
        
        if not topics:
            logger.error("采集失败")
            return []
        
        unique_topics = self._deduplicate_and_clean(topics)
        logger.info(f"去重后剩余 {len(unique_topics)} 个选题")
        
        if len(unique_topics) >= 10:
            self._save_topics(unique_topics)
            logger.info(f"✅ 采集成功！共 {len(unique_topics)} 个高质量选题")
            return unique_topics
        else:
            logger.warning(f"选题数量不足（{len(unique_topics)}个）")
            return []

    def _deduplicate_and_clean(self, topics: List[Dict]) -> List[Dict]:
        """去重和清洗"""
        seen_titles = set()
        unique_topics = []
        
        for topic in topics:
            title = topic.get('title', '').strip()
            
            if not title or len(title) < 10:
                continue
            
            if title in seen_titles:
                continue
            
            title_prefix = title[:15]
            if any(title_prefix in seen for seen in seen_titles):
                continue
            
            seen_titles.add(title)
            topic['collected_at'] = datetime.now().isoformat()
            
            if 'excerpt' not in topic or not topic['excerpt']:
                topic['excerpt'] = title[:100]
            if 'heat_score' not in topic:
                topic['heat_score'] = '中'
            if 'source' not in topic:
                topic['source'] = '网络采集'
            
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
    collector = HybridRealtimeCollector()
    topics = collector.run()
    
    if topics:
        print(f"\n✅ 实时采集成功！共 {len(topics)} 个选题\n")
        for i, topic in enumerate(topics[:10], 1):
            print(f"{i}. {topic['title']}")
            print(f"   来源: {topic.get('source', '未知')}")
            print()
    else:
        print("\n❌ 实时采集失败")
