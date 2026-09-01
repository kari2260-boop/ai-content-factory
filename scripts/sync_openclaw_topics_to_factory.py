#!/usr/bin/env python3
"""
把 OpenClaw 已经生成并发送给飞书的选题，同步到 AI 内容工厂。

输入支持 JSON 或 OpenClaw HEARTBEAT.md 里定义的 Markdown 选题格式。
这个脚本不负责重新采集，只负责把同一份输出标准化后写入内容工厂的 latest.json。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


EDU_KEYWORDS = (
    "教育", "留学", "科研", "论文", "申请", "国际学校", "课程", "考试", "升学", "招生",
    "班主任", "作业", "育儿", "家校", "学术", "老师", "校长", "课堂", "学习", "学生",
    "孩子", "家长", "家庭", "AI教育", "人工智能教育", "ChatGPT", "大模型",
)
TIMELY_KEYWORDS = ("最新", "刚刚", "今日", "今年", "2026", "发布", "曝光", "热议", "趋势")
ENGAGEMENT_KEYWORDS = ("争议", "焦虑", "举报", "取消", "爆", "为什么", "如何", "家长", "孩子", "真相")
UNIQUE_KEYWORDS = ("AI", "科研", "留学", "国际", "新政", "机制", "底层逻辑", "教育")
EMOTION_KEYWORDS = ("焦虑", "担心", "价值", "真相", "公平", "未来", "阶层", "孩子")


def read_input(input_path: str) -> str:
    if input_path == "-":
        return sys.stdin.read()
    return Path(input_path).read_text(encoding="utf-8")


def parse_topics(raw_text: str) -> List[Dict[str, Any]]:
    raw_text = raw_text.strip()
    if not raw_text:
        return []

    topics = parse_json_topics(raw_text)
    if topics:
        return topics

    return parse_markdown_topics(raw_text)


def parse_json_topics(raw_text: str) -> List[Dict[str, Any]]:
    candidates = [raw_text]
    candidates.extend(re.findall(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL | re.IGNORECASE))
    candidates.extend(re.findall(r"```\s*(.*?)\s*```", raw_text, re.DOTALL))

    array_match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
    if array_match:
        candidates.append(array_match.group(0))

    object_match = re.search(r"\{\s*\"topics\"\s*:.*\}", raw_text, re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict):
            data = data.get("topics") or data.get("items") or data.get("data") or []

        if isinstance(data, list):
            topics = [item for item in data if isinstance(item, dict) and item.get("title")]
            if topics:
                return topics

    return []


def parse_markdown_topics(raw_text: str) -> List[Dict[str, Any]]:
    pattern = re.compile(
        r"(?:^|\n)##\s*(?:Topic|选题)\s*\d*[:：]\s*(.+?)(?=\n##\s*(?:Topic|选题)\s*\d*[:：]|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    topics: List[Dict[str, Any]] = []

    for match in pattern.finditer(raw_text):
        block = match.group(1).strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        title = lines[0].strip("[] ")
        fields = extract_markdown_fields(lines[1:])
        excerpt_parts = [
            fields.get("Angle") or fields.get("角度") or "",
            fields.get("Why Now") or fields.get("为什么现在") or "",
            fields.get("Key Points") or fields.get("要点") or "",
        ]
        excerpt = "；".join(part for part in excerpt_parts if part)

        topics.append({
            "title": title,
            "excerpt": excerpt[:260],
            "source": "OpenClaw飞书同步",
            "url": "",
            "heat_score": fields.get("Expected Impact") or fields.get("预期影响") or "中",
            "angle": fields.get("Angle") or fields.get("角度") or "",
            "audience": fields.get("Audience") or fields.get("受众") or "",
        })

    return topics


def extract_markdown_fields(lines: List[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in lines:
        cleaned = line.lstrip("- ").strip()
        match = re.match(r"\*\*(.+?)\*\*\s*[:：]\s*(.+)", cleaned)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def normalize_topic(topic: Dict[str, Any], now: str) -> Dict[str, Any]:
    title = str(topic.get("title") or "").strip()
    excerpt = str(
        topic.get("excerpt")
        or topic.get("summary")
        or topic.get("description")
        or topic.get("angle")
        or ""
    ).strip()

    normalized = {
        "title": title,
        "excerpt": excerpt,
        "url": str(topic.get("url") or topic.get("link") or "").strip(),
        "source": str(topic.get("source") or "OpenClaw飞书同步").strip(),
        "heat_score": topic.get("heat_score") or topic.get("expected_impact") or "中",
        "collected_at": topic.get("collected_at") or now,
    }

    normalized.update(score_topic(normalized))
    normalized["ai_reason"] = "OpenClaw 已发送飞书的选题同步入库，使用本地快速评分"
    normalized["audience_pain_point"] = str(topic.get("audience") or "待生成内容时进一步识别")
    normalized["core_insight"] = str(topic.get("core_insight") or "")
    normalized["viral_hook"] = str(topic.get("viral_hook") or "")
    normalized["suggested_angles"] = topic.get("suggested_angles") if isinstance(topic.get("suggested_angles"), list) else []
    return normalized


def score_topic(topic: Dict[str, Any]) -> Dict[str, int]:
    text = f"{topic.get('title', '')} {topic.get('excerpt', '')}"
    relevance_hits = keyword_hits(text, EDU_KEYWORDS)
    relevance = min(10, 4 + relevance_hits * 2) if relevance_hits else 3
    timeliness = min(10, 6 + keyword_hits(text, TIMELY_KEYWORDS))
    engagement = min(10, 5 + keyword_hits(text, ENGAGEMENT_KEYWORDS))
    uniqueness = min(9, 5 + keyword_hits(text, UNIQUE_KEYWORDS))
    emotion = min(10, 5 + keyword_hits(text, EMOTION_KEYWORDS))

    if relevance <= 3:
        timeliness = min(timeliness, 4)
        engagement = min(engagement, 4)
        uniqueness = min(uniqueness, 4)
        emotion = min(emotion, 4)

    total = relevance + timeliness + engagement + uniqueness + emotion
    return {
        "relevance_score": relevance,
        "timeliness_score": timeliness,
        "engagement_score": engagement,
        "uniqueness_score": uniqueness,
        "emotion_score": emotion,
        "total_score": total,
    }


def keyword_hits(text: str, keywords: tuple) -> int:
    lower_text = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lower_text)


def deduplicate(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique_topics = []
    for topic in topics:
        title = topic.get("title", "").strip()
        if not title:
            continue
        key = title[:40]
        if key in seen:
            continue
        seen.add(key)
        unique_topics.append(topic)
    return unique_topics


def save_topics(topics: List[Dict[str, Any]], user_id: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    topics_dir = DATA_DIR / "users" / user_id / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "date": date_str,
        "total_count": len(topics),
        "high_score_count": len([topic for topic in topics if topic.get("total_score", 0) >= 25]),
        "topics": topics,
    }

    dated_path = topics_dir / f"topics_{date_str}.json"
    latest_path = topics_dir / "latest.json"
    dated_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return latest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OpenClaw topic output into AI Content Factory.")
    parser.add_argument("--input", "-i", default="-", help="输入文件路径；使用 - 从 stdin 读取")
    parser.add_argument("--user-id", default="dr_k", help="内容工厂用户 ID")
    args = parser.parse_args()

    raw_text = read_input(args.input)
    topics = deduplicate([normalize_topic(topic, datetime.now().isoformat()) for topic in parse_topics(raw_text)])
    if not topics:
        print("未解析到可同步的选题", file=sys.stderr)
        return 1

    latest_path = save_topics(topics, args.user_id)
    print(f"已同步 {len(topics)} 个 OpenClaw 选题到 {latest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
