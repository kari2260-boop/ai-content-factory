"""
混合实时采集器
结合 Gemini API（主）+ Claude API（备）生成教育热点选题
"""
import os
import json
from typing import List, Dict
from datetime import datetime

from modules.llm_client import LLMClient
from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR
from modules.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_FAST_MODEL

logger = setup_logger('hybrid_realtime_collector', 'collector.log')


class HybridRealtimeCollector:
    """混合实时采集器 - 优先 Gemini，备用 Claude"""

    def __init__(self, user_id: str = 'dr_k'):
        self.topics_dir = DATA_DIR / 'users' / user_id / 'topics'
        self.topics_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Gemini（主）
        self.gemini = None
        try:
            from modules.generator.gemini_client import GeminiClient
            g = GeminiClient()
            if g.available:
                self.gemini = g
                logger.info("✅ Gemini 客户端初始化成功")
        except Exception as e:
            logger.warning(f"Gemini 初始化失败: {e}")

        # 初始化 Claude（备）
        self.claude_client = None
        self.claude_model = ANTHROPIC_FAST_MODEL
        try:
            if ANTHROPIC_API_KEY:
                self.claude_client = LLMClient(
                    api_key=ANTHROPIC_API_KEY,
                    base_url=ANTHROPIC_BASE_URL,
                    model=self.claude_model,
                )
                logger.info("✅ Claude 客户端初始化成功")
        except Exception as e:
            logger.warning(f"Claude 初始化失败: {e}")
        
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
        """通过 AI 生成热点选题（Gemini 优先，Claude 备用）"""
        logger.info("开始生成教育热点选题")

        prompt = """请生成20个教育热点选题，直接输出JSON数组，不要markdown代码块，不要任何解释说明。

重点领域：
- 留学规划（申请策略、选校、签证政策）
- AI教育（AI工具在教育中的应用）
- 家庭教育（亲子关系、教育焦虑、素质教育）
- 教育政策（双减、教育改革、国际教育）
- 国际教育（IB/AP课程、国际学校）

要求：
1. 选题有争议性和讨论价值，能引发家长共鸣
2. 标题中只使用英文双引号，不要使用中文引号
3. 直接输出JSON数组，格式如下：

[{"title": "标题", "excerpt": "核心摘要100-150字", "source": "教育观察", "heat_score": "高", "keywords": ["关键词1", "关键词2"]}]

只返回JSON数组本身，第一个字符必须是[，最后一个字符必须是]。"""

        # 优先使用 Gemini
        if self.gemini:
            try:
                logger.info("使用 Gemini API 生成选题")
                response_text = self.gemini.generate(prompt)
                logger.info(f"Gemini 响应长度: {len(response_text)} 字符")
                topics = self._extract_json(response_text)
                if topics:
                    logger.info(f"✅ Gemini 生成成功，获得 {len(topics)} 个选题")
                    return topics
                logger.warning("Gemini 未返回有效选题，切换到 Claude")
            except Exception as e:
                logger.error(f"Gemini 生成失败: {str(e)[:200]}，切换到 Claude")

        # 备用 Claude
        if self.claude_client:
            for attempt in range(2):
                try:
                    logger.info(f"使用 Claude API 生成选题 (第 {attempt + 1} 次)")
                    response_text = self.claude_client.generate(
                        prompt,
                        max_tokens=3000,
                    )
                    topics = self._extract_json(response_text)
                    if topics:
                        logger.info(f"✅ Claude 生成成功，获得 {len(topics)} 个选题")
                        return topics
                except Exception as e:
                    logger.error(f"Claude 生成失败 (第 {attempt + 1} 次): {str(e)[:200]}")
                    if attempt == 0:
                        import time
                        time.sleep(3)

        logger.error("所有 AI 生成方式均失败")
        return []

    def _extract_json(self, text: str) -> List[Dict]:
        """从文本中提取 JSON"""
        import re

        # 尝试直接解析
        try:
            data = json.loads(text.strip())
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"直接解析成功，包含 {len(data)} 个选题")
                return data
        except:
            pass

        # 提取从 [ 到 ] 的部分，处理内部引号问题
        try:
            start = text.index('[')
            end = text.rindex(']') + 1
            json_str = text[start:end]
            # 替换 JSON 字符串值内部的未转义中文引号（\u201c/\u201d）为空
            json_str = json_str.replace('\u201c', '').replace('\u201d', '')
            json_str = json_str.replace('\u2018', '').replace('\u2019', '')
            data = json.loads(json_str)
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"提取并解析成功，包含 {len(data)} 个选题")
                return data
        except Exception as e:
            logger.debug(f"提取JSON失败: {e}")

        # 用正则逐个提取 title/excerpt/source/heat_score 字段，手动构建
        try:
            items = []
            # 找所有 title 字段
            title_pattern = re.compile(r'"title"\s*:\s*"((?:[^"\\]|\\.)*?)"')
            excerpt_pattern = re.compile(r'"excerpt"\s*:\s*"((?:[^"\\]|\\.)*?)"')
            source_pattern = re.compile(r'"source"\s*:\s*"((?:[^"\\]|\\.)*?)"')
            heat_pattern = re.compile(r'"heat_score"\s*:\s*"((?:[^"\\]|\\.)*?)"')

            titles = title_pattern.findall(text)
            excerpts = excerpt_pattern.findall(text)
            sources = source_pattern.findall(text)
            heats = heat_pattern.findall(text)

            for i, title in enumerate(titles):
                if title.strip():
                    items.append({
                        'title': title,
                        'excerpt': excerpts[i] if i < len(excerpts) else '',
                        'source': sources[i] if i < len(sources) else '教育观察',
                        'heat_score': heats[i] if i < len(heats) else '中',
                        'collected_at': datetime.now().isoformat()
                    })

            if items:
                logger.info(f"正则提取成功，包含 {len(items)} 个选题")
                return items
        except Exception as e:
            logger.debug(f"正则提取失败: {e}")

        logger.warning("未能从响应中提取有效 JSON")
        logger.warning(f"响应内容前300字符: {text[:300]}")
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
