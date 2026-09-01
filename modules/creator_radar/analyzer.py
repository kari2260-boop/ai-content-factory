"""
Analyze creator/video records into report-ready insights.
"""
import json
import math
import re
from typing import Dict, List, Optional

from modules.config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_FAST_MODEL
from modules.creator_radar.models import clean_text, truncate
from modules.llm_client import LLMClient
from modules.utils import setup_logger

logger = setup_logger("creator_radar_analyzer", "creator_radar.log")


TOPIC_KEYWORDS = {
    "ADHD": ["adhd", "注意力缺陷", "多动", "执行功能", "专注力"],
    "神经多样性": ["neurodiversity", "neurodivergent", "神经多样", "神经发散"],
    "神经科学": ["neuroscience", "brain", "大脑", "脑科学", "神经科学"],
    "特殊教育": ["special education", "iep", "特殊教育", "融合教育", "学习障碍"],
    "自闭症谱系": ["autism", "autistic", "asd", "自闭症", "孤独症", "谱系"],
    "个人成长": ["personal growth", "自我接纳", "成长", "自救", "疗愈", "不一样的我"],
    "社会差异": ["masking", "社会", "不合群", "不一样", "边缘", "身份认同"],
}


class CreatorAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        analysis_config = config.get("analysis", {})
        self.max_text_chars = int(analysis_config.get("max_text_chars", 3500))
        self.use_llm = bool(analysis_config.get("use_llm_if_available", True) and ANTHROPIC_API_KEY)
        self.llm: Optional[LLMClient] = None
        if self.use_llm:
            self.llm = LLMClient(
                api_key=ANTHROPIC_API_KEY,
                base_url=ANTHROPIC_BASE_URL,
                model=ANTHROPIC_FAST_MODEL,
            )

    def analyze(self, row: Dict) -> Dict:
        base = self._rule_based_analysis(row)
        if not self.llm:
            return base

        try:
            llm_fields = self._llm_analysis(row, base)
            base.update({k: v for k, v in llm_fields.items() if v})
        except Exception as exc:
            logger.warning(f"LLM 分析失败，使用规则分析: {row.get('video_id')} - {exc}")
        return base

    def _rule_based_analysis(self, row: Dict) -> Dict:
        title = clean_text(row.get("title"))
        description = clean_text(row.get("description"))
        transcript = clean_text(row.get("transcript"))
        text = clean_text(" ".join([title, description, transcript]))
        tags = self._topic_tags(text)

        view_count = row.get("view_count") or 0
        like_count = row.get("like_count") or 0
        comment_count = row.get("comment_count") or 0
        share_count = row.get("share_count") or 0
        follower_count = row.get("follower_count") or 0

        engagement_total = (like_count or 0) + (comment_count or 0) + (share_count or 0)
        engagement_rate = engagement_total / view_count if view_count else 0
        views_to_followers_ratio = view_count / follower_count if follower_count else None
        virality_score = self._virality_score(view_count, engagement_rate, views_to_followers_ratio)
        relevance_score = min(10.0, 2.5 + len(tags) * 1.6 + (1.5 if transcript else 0))

        core_thesis = self._first_meaningful_sentence(text) or title
        content_text = transcript or f"标题：{title}\n简介：{description}"
        missing_transcript_note = "" if transcript else "当前没有完整口播/字幕，只能基于标题和简介判断。"

        return {
            "relevance_score": round(relevance_score, 1),
            "virality_score": round(virality_score, 1),
            "engagement_rate": round(engagement_rate, 4),
            "views_to_followers_ratio": round(views_to_followers_ratio, 2)
            if views_to_followers_ratio is not None
            else None,
            "topic_tags": tags,
            "core_thesis": truncate(core_thesis, 220),
            "why_good": self._why_good(row, tags, engagement_rate, views_to_followers_ratio),
            "traffic_drivers": self._traffic_drivers(row, tags, engagement_rate, views_to_followers_ratio),
            "reusable_patterns": self._reusable_patterns(row, tags),
            "content_text": truncate(content_text, self.max_text_chars),
            "recommended_action": (
                "优先拆解开头 5 秒、标题承诺、个人经历到专业解释的转折，并补齐完整转写。"
                if missing_transcript_note
                else "可作为结构参考：保留主题和叙事机制，换成自己的经历、观点和证据。"
            ),
        }

    def _llm_analysis(self, row: Dict, base: Dict) -> Dict:
        text = base.get("content_text", "")
        prompt = f"""
你是一个短视频内容研究员，研究神经科学、特殊教育、ADHD、neurodiversity 和个人成长类内容。
请只输出 JSON，不要输出 Markdown。

视频信息：
- 平台：{row.get('platform')}
- 博主：{row.get('display_name') or row.get('handle')}
- 粉丝量：{row.get('follower_count')}，分层：{row.get('follower_bucket')}
- 标题：{row.get('title')}
- 播放：{row.get('view_count')}，点赞：{row.get('like_count')}，评论：{row.get('comment_count')}，分享：{row.get('share_count')}
- 初步标签：{", ".join(base.get('topic_tags', []))}

视频文本：
{text[: self.max_text_chars]}

请分析：
1. core_thesis：核心主旨，一句话。
2. why_good：为什么这个视频好，要具体到选题、结构、表达。
3. traffic_drivers：为什么能吸引流量，要具体到情绪、身份认同、冲突、可转发性。
4. reusable_patterns：如果我要借鉴，可以借鉴什么，不要照搬文本。
5. recommended_action：下一步动作，说明是否值得跟进、适合改成什么内容。
JSON 字段必须是上述 5 个英文键。
"""
        assert self.llm is not None
        raw = self.llm.generate(prompt, max_tokens=1400)
        return _parse_json_object(raw)

    def _topic_tags(self, text: str) -> List[str]:
        lower = text.lower()
        tags = []
        for tag, keywords in TOPIC_KEYWORDS.items():
            if any(keyword.lower() in lower for keyword in keywords):
                tags.append(tag)
        return tags

    def _virality_score(self, views: int, engagement_rate: float, ratio) -> float:
        views_score = min(45.0, math.log10(max(views, 1)) * 8)
        engagement_score = min(25.0, engagement_rate * 250)
        ratio_score = 0.0
        if ratio is not None:
            ratio_score = min(30.0, math.log10(max(ratio, 0.1) + 1) * 24)
        return views_score + engagement_score + ratio_score

    def _why_good(self, row: Dict, tags: List[str], engagement_rate: float, ratio) -> str:
        reasons = []
        if tags:
            reasons.append(f"主题命中 {', '.join(tags)}，属于高身份认同和高解释需求内容")
        if ratio and ratio >= 3:
            reasons.append("播放量显著超过粉丝基数，说明内容有跨圈层传播")
        if engagement_rate >= 0.06:
            reasons.append("互动率较高，标题或表达激发了评论/收藏/转发")
        if not reasons:
            reasons.append("样本具备相关主题，但还需要更多文本和互动数据确认爆点")
        return "；".join(reasons) + "。"

    def _traffic_drivers(self, row: Dict, tags: List[str], engagement_rate: float, ratio) -> str:
        title = clean_text(row.get("title"))
        drivers = []
        if re.search(r"我|自己|不一样|终于|为什么", title):
            drivers.append("标题使用第一人称或自我发现叙事，容易触发代入")
        if {"ADHD", "神经多样性", "社会差异"} & set(tags):
            drivers.append("把个人困惑命名为可解释的差异，降低观众羞耻感")
        if ratio and ratio >= 1:
            drivers.append("小/中腰部账号获得高播放，说明话题本身强于账号分发")
        return "；".join(drivers or ["可能依靠清晰痛点、专业解释和情绪共鸣获得传播"]) + "。"

    def _reusable_patterns(self, row: Dict, tags: List[str]) -> str:
        return (
            "可复用结构：先讲一个反常识/自我困惑场景，再给出神经科学或特殊教育解释，"
            "最后落到一个可执行建议或自我接纳观点。借鉴主题、结构和证据链，不复刻原文。"
        )

    def _first_meaningful_sentence(self, text: str) -> str:
        for part in re.split(r"[。！？.!?\n]", text):
            part = clean_text(part)
            if len(part) >= 12:
                return part
        return clean_text(text)


def _parse_json_object(raw: str) -> Dict:
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if match:
        raw = match.group(0)
    return json.loads(raw)
