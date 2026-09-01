"""
反馈学习闭环模块
对比用户修改后的定稿与 AI 原稿，自动学习修改规律
"""
import json
from typing import Dict, List, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from anthropic import Anthropic

from modules.utils import setup_logger
from modules.config import ANTHROPIC_API_KEY

logger = setup_logger('feedback_loop', 'feedback.log')


class FeedbackLearner:
    """反馈学习器 - 从用户修改中学习"""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("未找到 ANTHROPIC_AUTH_TOKEN 环境变量")

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    def compare_versions(self, original: str, edited: str) -> Dict:
        """
        对比原稿和修改稿，提取修改规律

        Args:
            original: AI 生成的原稿
            edited: 用户修改后的定稿

        Returns:
            包含修改分析的字典
        """
        # 计算相似度
        similarity = SequenceMatcher(None, original, edited).ratio()

        # 如果相似度太高（>95%），说明几乎没改
        if similarity > 0.95:
            logger.info("内容几乎未修改，跳过学习")
            return {
                'has_changes': False,
                'similarity': similarity,
                'patterns': []
            }

        logger.info(f"检测到修改，相似度: {similarity:.2%}")

        # 使用 AI 分析修改规律
        analysis = self._analyze_changes_with_ai(original, edited)

        return {
            'has_changes': True,
            'similarity': similarity,
            'patterns': analysis['patterns'],
            'summary': analysis['summary'],
            'analyzed_at': datetime.now().isoformat()
        }

    def _analyze_changes_with_ai(self, original: str, edited: str) -> Dict:
        """使用 AI 分析修改规律"""
        prompt = f"""你是一位内容风格分析专家。请对比以下两个版本的文案，提取用户的修改规律。

**AI 原稿：**
{original[:1000]}...

**用户修改后：**
{edited[:1000]}...

请分析用户做了哪些类型的修改，并提取可复用的规律。

以 JSON 格式返回：
{{
  "patterns": [
    {{
      "type": "tone",
      "description": "将正式表达改为口语化",
      "example": "原文'进行学习' → 改为'去学'"
    }},
    {{
      "type": "structure",
      "description": "增加了小标题分段",
      "example": "原文连续段落 → 改为带【】的小标题"
    }}
  ],
  "summary": "用户倾向于更口语化、更有结构感的表达方式"
}}

只返回 JSON，不要其他内容。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text.strip()

            # 移除可能的 markdown 代码块标记
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]

            analysis = json.loads(result_text)
            return analysis

        except Exception as e:
            logger.error(f"AI 分析失败: {str(e)}")
            return {
                'patterns': [],
                'summary': '分析失败'
            }

    def save_to_correction_history(self,
                                   content_type: str,
                                   patterns: List[Dict],
                                   summary: str) -> Dict:
        """
        将学习到的规律保存到错题本

        Args:
            content_type: 内容类型（video/article/xiaohongshu等）
            patterns: 提取的修改规律列表
            summary: 修改总结

        Returns:
            错题本条目
        """
        correction_entry = {
            'content_type': content_type,
            'patterns': patterns,
            'summary': summary,
            'learned_at': datetime.now().isoformat(),
            'confidence': 0.7  # 初始置信度
        }

        logger.info(f"保存到错题本: {content_type} - {summary}")

        return correction_entry

    def apply_learned_patterns(self,
                               content: str,
                               content_type: str,
                               correction_history: List[Dict]) -> str:
        """
        应用已学习的规律优化内容

        Args:
            content: 待优化的内容
            content_type: 内容类型
            correction_history: 错题本历史

        Returns:
            优化后的内容
        """
        # 筛选相关的修改规律
        relevant_patterns = []
        for entry in correction_history:
            if entry.get('content_type') == content_type:
                relevant_patterns.extend(entry.get('patterns', []))

        if not relevant_patterns:
            logger.info(f"没有找到 {content_type} 的历史修改规律")
            return content

        logger.info(f"找到 {len(relevant_patterns)} 条相关修改规律，应用优化...")

        # 使用 AI 应用这些规律
        optimized = self._apply_patterns_with_ai(content, relevant_patterns)

        return optimized

    def _apply_patterns_with_ai(self, content: str, patterns: List[Dict]) -> str:
        """使用 AI 应用修改规律"""
        patterns_text = "\n".join([
            f"- {p['type']}: {p['description']}"
            for p in patterns[:5]  # 最多应用5条规律
        ])

        prompt = f"""请根据以下用户偏好规律，优化这段内容：

**用户偏好规律：**
{patterns_text}

**待优化内容：**
{content}

请应用这些规律优化内容，保持原意但符合用户风格。直接返回优化后的内容，不要解释。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            optimized = response.content[0].text.strip()
            return optimized

        except Exception as e:
            logger.error(f"应用规律失败: {str(e)}")
            return content


def test_feedback_learner():
    """测试反馈学习器"""
    learner = FeedbackLearner()

    # 模拟原稿和修改稿
    original = """
AI时代，孩子应该学习什么？

随着人工智能技术的快速发展，传统的教育模式正在面临挑战。家长们需要重新思考孩子的教育规划。

首先，编程能力变得越来越重要。其次，批判性思维也是必不可少的。最后，创造力将成为核心竞争力。
"""

    edited = """
AI时代，孩子该学啥才不会被淘汰？🤔

AI发展太快了，传统那套教育已经不够用了！作为家长，咱们得重新想想怎么培养孩子。

【第一点】编程思维必须有 💻
不是说一定要当程序员，但编程思维能帮孩子理解AI时代的底层逻辑。

【第二点】批判性思维不能少 🧠
AI会给答案，但孩子得学会质疑、分析、判断。

【第三点】创造力才是王道 ✨
AI能模仿，但真正的创新还得靠人！
"""

    print("="*70)
    print("测试反馈学习器")
    print("="*70)

    # 对比分析
    print("\n【步骤1】对比原稿和修改稿...")
    result = learner.compare_versions(original, edited)

    print(f"\n相似度: {result['similarity']:.2%}")
    print(f"是否有修改: {result['has_changes']}")

    if result['has_changes']:
        print(f"\n修改总结: {result['summary']}")
        print("\n提取的修改规律:")
        for i, pattern in enumerate(result['patterns'], 1):
            print(f"\n  {i}. 类型: {pattern['type']}")
            print(f"     描述: {pattern['description']}")
            if 'example' in pattern:
                print(f"     示例: {pattern['example']}")

        # 保存到错题本
        print("\n【步骤2】保存到错题本...")
        correction = learner.save_to_correction_history(
            content_type='article',
            patterns=result['patterns'],
            summary=result['summary']
        )
        print(f"✅ 已保存: {json.dumps(correction, ensure_ascii=False, indent=2)}")


if __name__ == '__main__':
    test_feedback_learner()
