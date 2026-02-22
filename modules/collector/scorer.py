"""
Claude 打分器
使用 Claude API 对选题进行智能打分和筛选
"""
import os
from typing import List, Dict
from anthropic import Anthropic

from modules.utils import setup_logger
from modules.config import ANTHROPIC_API_KEY

logger = setup_logger('scorer', 'collector.log')


class TopicScorer:
    """选题打分器"""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("未找到 ANTHROPIC_AUTH_TOKEN 环境变量")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    def score_topics(self, topics: List[Dict]) -> List[Dict]:
        """批量打分选题"""
        scored_topics = []

        for topic in topics:
            try:
                score_data = self._score_single_topic(topic)
                topic.update(score_data)
                scored_topics.append(topic)
                logger.info(f"选题打分完成: {topic['title'][:30]}... (总分: {score_data['total_score']})")

            except Exception as e:
                logger.error(f"选题打分失败: {topic['title'][:30]}... - {str(e)}")
                # 失败的选题给默认分数
                topic.update({
                    'relevance_score': 5,
                    'timeliness_score': 5,
                    'engagement_score': 5,
                    'uniqueness_score': 5,
                    'emotion_score': 5,
                    'total_score': 25,
                    'ai_reason': '打分失败，使用默认分数',
                    'suggested_angles': [],
                    'audience_pain_point': '未识别'
                })
                scored_topics.append(topic)

        # 按总分排序
        scored_topics.sort(key=lambda x: x['total_score'], reverse=True)
        return scored_topics

    def _score_single_topic(self, topic: Dict) -> Dict:
        """对单个选题打分"""
        prompt = f"""你是K博士的选题助手。K博士是教育领域博士，专注留学规划和AI时代家庭教育。

请对以下选题进行评分（每项0-10分）：

**选题标题：** {topic['title']}
**选题摘要：** {topic.get('excerpt', '无')}
**来源：** {topic['source']}

评分维度：
1. **相关度** (0-10)：与"留学规划"、"AI教育"、"家庭教育"的相关程度
2. **时效性** (0-10)：话题的新鲜度和时效性
3. **互动潜力** (0-10)：能否引发读者共鸣和讨论
4. **独特性** (0-10)：角度是否新颖，避免老生常谈
5. **情绪共鸣** (0-10)：能否触动家长的焦虑、期待、共鸣等核心情绪

请以 JSON 格式返回：
{{
  "relevance_score": 8,
  "timeliness_score": 7,
  "engagement_score": 9,
  "uniqueness_score": 6,
  "emotion_score": 8,
  "total_score": 38,
  "ai_reason": "简短说明为什么给这个分数（50字内）",
  "audience_pain_point": "家长担心孩子在AI时代失去竞争力，不知道该培养什么技能",
  "core_insight": "这个话题的核心观点是什么（30字内，一句话）",
  "viral_hook": "最能引爆传播的爆点角度（30字内，一句话）",
  "suggested_angles": ["建议的切入角度1", "建议的切入角度2"]
}}

只返回 JSON，不要其他内容。"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 解析 Claude 返回的 JSON
        import json
        result_text = response.content[0].text.strip()

        # 移除可能的 markdown 代码块标记
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        score_data = json.loads(result_text)

        # 确保总分正确（5个维度）
        score_data['total_score'] = (
            score_data['relevance_score'] +
            score_data['timeliness_score'] +
            score_data['engagement_score'] +
            score_data['uniqueness_score'] +
            score_data.get('emotion_score', 0)
        )

        # 确保包含新字段
        if 'audience_pain_point' not in score_data:
            score_data['audience_pain_point'] = '未识别'
        if 'core_insight' not in score_data:
            score_data['core_insight'] = ''
        if 'viral_hook' not in score_data:
            score_data['viral_hook'] = ''

        return score_data


if __name__ == '__main__':
    # 测试打分
    test_topic = {
        'title': 'AI时代，孩子该学什么才不会被淘汰？',
        'excerpt': '人工智能快速发展，家长焦虑孩子未来就业...',
        'source': 'test',
        'url': 'https://example.com'
    }

    scorer = TopicScorer()
    result = scorer._score_single_topic(test_topic)
    print(f"打分结果: {result}")
