"""
Configuration loader for creator radar.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict

from modules.utils import CONFIG_DIR


DEFAULT_CONFIG: Dict[str, Any] = {
    "timezone": "Asia/Shanghai",
    "report_time": "08:00",
    "keywords": [
        "ADHD",
        "neurodiversity",
        "神经多样性",
        "神经科学",
        "特殊教育",
        "注意力缺陷",
        "自闭症谱系",
        "个人成长",
        "不一样的我",
        "我和社会不一样",
    ],
    "target_follower_ranges": [
        {"label": "0-1万", "min": 0, "max": 10_000},
        {"label": "5万-10万", "min": 50_000, "max": 100_000},
    ],
    "platforms": {
        "youtube": {
            "enabled": True,
            "max_results_per_keyword": 3,
            "order": "relevance",
            "published_after_days": 30,
        },
        "bilibili": {
            "enabled": True,
            "max_results_per_keyword": 5,
            "search_type": "video",
        },
        "xiaohongshu": {
            "enabled": False,
            "mode": "manual_csv",
        },
        "wechat_channels": {
            "enabled": False,
            "mode": "manual_csv",
        },
        "manual_csv": {
            "enabled": True,
            "import_dir": "data/creator_radar/imports",
        },
    },
    "analysis": {
        "use_llm_if_available": True,
        "max_text_chars": 3500,
    },
    "report": {
        "since_days": 7,
        "top_n": 20,
        "min_relevance_score": 4.0,
        "output_dir": "data/creator_radar/reports",
    },
}


def config_path() -> Path:
    return CONFIG_DIR / "creator_radar.json"


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    with open(path, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    return _deep_merge(DEFAULT_CONFIG.copy(), user_config)


def save_default_config(overwrite: bool = False) -> Path:
    path = config_path()
    if path.exists() and not overwrite:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    return path


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
