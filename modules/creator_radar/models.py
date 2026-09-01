"""
Shared normalization helpers for creator radar.
"""
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Optional


FOLLOWER_BUCKETS = [
    (0, 5_000, "0-5,000"),
    (5_000, 10_000, "5,000-1万"),
    (10_000, 50_000, "1万-5万"),
    (50_000, 100_000, "5万-10万"),
    (100_000, 200_000, "10万-20万"),
    (200_000, 500_000, "20万-50万"),
    (500_000, 1_000_000, "50万-100万"),
    (1_000_000, None, "100万+"),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(*parts: Any) -> str:
    raw = "::".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def parse_count(value: Any) -> Optional[int]:
    """Parse counts like 1.2万, 34K, 5,400 into an int."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text = str(value).strip()
    if not text or text.lower() in {"n/a", "none", "null", "-"}:
        return None

    text = text.replace(",", "").replace("，", "").replace("次", "")
    multiplier = 1
    if text.endswith("万"):
        multiplier = 10_000
        text = text[:-1]
    elif text.endswith("亿"):
        multiplier = 100_000_000
        text = text[:-1]
    elif text.lower().endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif text.lower().endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return int(float(match.group(0)) * multiplier)


def follower_bucket(follower_count: Optional[int]) -> str:
    if follower_count is None:
        return "未知"
    for low, high, label in FOLLOWER_BUCKETS:
        if follower_count >= low and (high is None or follower_count < high):
            return label
    return "未知"


def clean_text(text: Any) -> str:
    if text is None:
        return ""
    value = str(text)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def truncate(text: str, limit: int) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."
