"""
Claude 打分器
使用 Claude API 对选题进行智能打分和筛选
"""
import os
from typing import List, Dict

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from modules.utils import setup_logger
from modules.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL

logger = setup_logger('scorer', 'collector.log')


class TopicScorer:
    """选题打分器"""

    STRONG_EDU_KEYWORDS = [
        '教育', '留学', '科研', '论文', '申请', '国际学校', '课程', '考试', '升学', '招生',
        '班主任', '作业', '育儿', '家校', '学术', '老师', '校长', '教育局',
        '课堂', '学习', '托育', '幼儿园', '文书', '课后', '录取',
        '毕业典礼', '新生', '校内', '校园', '教育政策', '中小学', '基础教育'
    ]

    FAMILY_CONTEXT_KEYWORDS = [
        '孩子', '家长', '家庭', '育儿', '儿童', '青少年'
    ]

    LEARNING_CONTEXT_KEYWORDS = [
        '教育', '学校', '大学', '学习', '作业', '考试', '升学',
        '留学', '课程', '课堂', '老师', '班主任', '学生', '家校', '幼儿园', '培训',
        '毕业', '录取', '文书', '校长'
    ]

    COLLEGE_CONTEXT_KEYWORDS = [
        '毕业', '毕业典礼', '录取', '申请', '文书', '招生', '考试',
        '课程', '课堂', '老师', '班主任', '学生', '家长', '教育', '升学',
        '高考', '中考', '考研', '上大学'
    ]

    AI_CONTEXT_KEYWORDS = [
        'AI教育', '人工智能教育', 'AI 时代', 'AI时代', 'ChatGPT', 'DeepSeek',
        '大模型', 'AI作业', 'AI辅导', 'AI学习', 'AI导师', 'AI老师', 'AI Tutor'
    ]

    REJECT_KEYWORDS = [
        '同性恋', '婚姻', '离婚', '出轨', '谈恋爱', '恋爱', '娱乐圈', '明星', '八卦',
        '车企', '汽车', '房价', '股市', '基金', '投资', '游戏', '体育',
        '外交', '政治', '法律', '犯罪', '战争', '天气', '航班',
        'Nature', 'ECCV', 'CVPR', 'ICML', 'NeurIPS', '机器之心', 'AI芯片', '模型', '算法', '框架', 'Oral'
    ]

    def __init__(self):
        self.client = None
        self.use_gemini = False

        # 优先使用 Claude
        if ANTHROPIC_API_KEY and Anthropic:
            try:
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY, base_url=ANTHROPIC_BASE_URL)
                self.model = "claude-sonnet-4-5-20250929"
                logger.info("使用 Claude API 进行打分")
            except Exception as e:
                logger.warning(f"Claude API 初始化失败: {e}")
        elif ANTHROPIC_API_KEY and not Anthropic:
            logger.warning("已配置 Claude API，但未安装 anthropic 包，将使用备用打分")

        # 降级使用 Gemini
        if not self.client:
            try:
                from modules.generator.gemini_client import GeminiClient
                gemini_client = GeminiClient()
                if gemini_client.available:
                    self.gemini_client = gemini_client
                    self.use_gemini = True
                    logger.info("使用 Gemini API 进行打分")
                else:
                    logger.warning("未配置 AI API，将使用默认分数")
            except Exception as e:
                logger.warning(f"Gemini API 初始化失败: {e}")
                logger.warning("将使用默认分数")

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

    def score_topics_fast(self, topics: List[Dict]) -> List[Dict]:
        """本地快速打分，不调用外部 AI，避免采集页面长时间无响应。"""
        scored_topics = []
        for topic in topics:
            title = topic.get('title', '')
            excerpt = topic.get('excerpt', '')
            source = topic.get('source', '')
            text = f"{title} {excerpt}"

            strong_hits = sum(1 for keyword in self.STRONG_EDU_KEYWORDS if keyword.lower() in text.lower())
            family_hits = sum(1 for keyword in self.FAMILY_CONTEXT_KEYWORDS if keyword.lower() in text.lower())
            learning_hits = sum(1 for keyword in self.LEARNING_CONTEXT_KEYWORDS if keyword.lower() in text.lower())
            ai_hits = sum(1 for keyword in self.AI_CONTEXT_KEYWORDS if keyword.lower() in text.lower())
            rejected = any(keyword.lower() in text.lower() for keyword in self.REJECT_KEYWORDS)
            college_hit = any(keyword in text for keyword in ('大学', '学校')) and any(
                keyword in text for keyword in self.COLLEGE_CONTEXT_KEYWORDS
            )

            if rejected:
                relevance = 0
            elif strong_hits > 0:
                relevance = min(10, 5 + strong_hits * 2 + (1 if ai_hits else 0))
            elif college_hit:
                relevance = 6
            elif family_hits > 0 and learning_hits > 0:
                relevance = 5
            elif ai_hits > 0 and learning_hits > 0:
                relevance = 4
            elif ai_hits > 0:
                relevance = 3
            else:
                relevance = 2

            timeliness = 8 if any(word in text for word in ['最新', '刚刚', '今日', '今年', '2026', '发布', '曝光', '热议']) else 6
            engagement = self._keyword_score(text, [
                '争议', '造假', '焦虑', '举报', '取消', '爆', '为什么', '如何看待', '家长', '孩子'
            ], base=5, cap=10)
            uniqueness = self._keyword_score(text, [
                'Nature', 'AI', '科研', '留学', '国际', '新政', '机制', '底层逻辑', '教育'
            ], base=5, cap=9)
            emotion = self._keyword_score(text, [
                '焦虑', '担心', '价值', '真相', '公平', '未来', '阶层', '举报', '造假', '孩子'
            ], base=5, cap=10)

            # 相关度不够时，其他维度不能把分数硬抬上去
            if relevance <= 3:
                timeliness = min(timeliness, 4)
                engagement = min(engagement, 4)
                uniqueness = min(uniqueness, 4)
                emotion = min(emotion, 4)

            if source in ('手动添加', '教育观察'):
                timeliness = max(timeliness, 7)

            total = relevance + timeliness + engagement + uniqueness + emotion
            if relevance <= 2:
                total = min(total, 18)
            elif relevance <= 3:
                total = min(total, 22)

            topic.update({
                'relevance_score': relevance,
                'timeliness_score': timeliness,
                'engagement_score': engagement,
                'uniqueness_score': uniqueness,
                'emotion_score': emotion,
                'total_score': total,
                'ai_reason': '快速本地评分，未调用 AI',
                'audience_pain_point': '待生成内容时进一步识别',
                'core_insight': '',
                'viral_hook': '',
                'suggested_angles': []
            })
            scored_topics.append(topic)

        scored_topics.sort(key=lambda x: x['total_score'], reverse=True)
        return scored_topics

    def is_relevant_topic(self, topic: Dict) -> bool:
        """判断一个选题是否满足教育/家庭/留学语境。"""
        text = f"{topic.get('title', '')} {topic.get('excerpt', '')}".strip()
        if not text:
            return False

        if any(keyword in text for keyword in self.REJECT_KEYWORDS):
            return False

        strong_hit = any(keyword in text for keyword in self.STRONG_EDU_KEYWORDS)
        family_hit = any(keyword in text for keyword in self.FAMILY_CONTEXT_KEYWORDS)
        learning_hit = any(keyword in text for keyword in self.LEARNING_CONTEXT_KEYWORDS)
        ai_hit = any(keyword in text for keyword in self.AI_CONTEXT_KEYWORDS)
        college_hit = any(keyword in text for keyword in ('大学', '学校')) and any(
            keyword in text for keyword in self.COLLEGE_CONTEXT_KEYWORDS
        )

        if strong_hit or college_hit:
            return True
        if family_hit and learning_hit:
            return True
        if ai_hit and learning_hit:
            return True
        return False

    def _keyword_score(self, text: str, keywords: List[str], base: int = 5, cap: int = 10) -> int:
        hits = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        return min(cap, base + hits)

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

        # 如果没有可用的 AI API，返回默认分数
        if not self.client and not self.use_gemini:
            logger.warning("没有可用的 AI API，使用默认分数")
            return {
                'relevance_score': 5,
                'timeliness_score': 5,
                'engagement_score': 5,
                'uniqueness_score': 5,
                'emotion_score': 5,
                'total_score': 25,
                'ai_reason': '未配置 AI API，使用默认分数',
                'suggested_angles': [],
                'audience_pain_point': '未识别',
                'core_insight': '',
                'viral_hook': ''
            }

        # 使用 Claude API
        if self.client:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            result_text = response.content[0].text.strip()

        # 使用 Gemini API
        elif self.use_gemini:
            response_text = self.gemini_client.generate(prompt, max_tokens=500)
            result_text = response_text.strip()

        # 解析 JSON
        import json

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
