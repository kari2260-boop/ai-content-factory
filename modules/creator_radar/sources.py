"""
Creator/video data sources.

YouTube uses the official Data API. Bilibili uses public web endpoints.
Xiaohongshu and WeChat Channels are intentionally handled through manual CSV
imports unless a compliant third-party export/API is configured.
"""
import csv
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from modules.creator_radar.models import clean_text, parse_count, stable_id
from modules.utils import PROJECT_ROOT, setup_logger

logger = setup_logger("creator_radar_sources", "creator_radar.log")


MANUAL_COLUMNS = [
    "platform",
    "creator_handle",
    "creator_name",
    "profile_url",
    "follower_count",
    "creator_bio",
    "niche",
    "video_id",
    "video_url",
    "title",
    "published_at",
    "view_count",
    "like_count",
    "comment_count",
    "share_count",
    "description",
    "transcript",
    "source_note",
]


class SourceBase:
    name = "base"

    def __init__(self, config: Dict):
        self.config = config
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
            )
        }

    def fetch(self, keywords: Iterable[str]) -> List[Dict]:
        raise NotImplementedError


class ManualCSVSource(SourceBase):
    name = "manual_csv"

    def fetch(self, keywords: Iterable[str] = ()) -> List[Dict]:
        import_dir = self.config.get("import_dir", "data/creator_radar/imports")
        folder = Path(import_dir)
        if not folder.is_absolute():
            folder = PROJECT_ROOT / folder
        folder.mkdir(parents=True, exist_ok=True)

        items: List[Dict] = []
        for path in sorted(folder.glob("*.csv")):
            if path.name.startswith("_"):
                continue
            logger.info(f"读取人工导入文件: {path}")
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not (row.get("title") and row.get("platform")):
                        continue
                    items.append(_manual_row_to_item(row, path.name))

        logger.info(f"人工导入采集完成，共 {len(items)} 条")
        return items


class YouTubeSource(SourceBase):
    name = "youtube"

    def fetch(self, keywords: Iterable[str]) -> List[Dict]:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            logger.warning("未配置 YOUTUBE_API_KEY，跳过 YouTube 采集")
            return []

        max_results = int(self.config.get("max_results_per_keyword", 3))
        order = self.config.get("order", "relevance")
        published_after_days = int(self.config.get("published_after_days", 30))
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=published_after_days)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        video_ids: List[str] = []
        for keyword in keywords:
            params = {
                "part": "snippet",
                "type": "video",
                "q": keyword,
                "maxResults": max_results,
                "order": order,
                "publishedAfter": published_after,
                "key": api_key,
            }
            data = _get_json("https://www.googleapis.com/youtube/v3/search", params)
            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id and video_id not in video_ids:
                    video_ids.append(video_id)
            time.sleep(0.2)

        if not video_ids:
            return []

        videos = self._fetch_videos(api_key, video_ids)
        channel_ids = sorted({v["snippet"]["channelId"] for v in videos if "snippet" in v})
        channels = self._fetch_channels(api_key, channel_ids)
        channel_map = {c["id"]: c for c in channels}

        items = []
        for video in videos:
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            channel = channel_map.get(snippet.get("channelId"), {})
            channel_snippet = channel.get("snippet", {})
            channel_stats = channel.get("statistics", {})
            channel_id = snippet.get("channelId")
            video_id = video.get("id")
            description = clean_text(snippet.get("description", ""))

            items.append(
                {
                    "platform": "YouTube",
                    "source": self.name,
                    "creator": {
                        "creator_id": f"youtube:{channel_id}",
                        "handle": channel_snippet.get("customUrl") or channel_id,
                        "display_name": snippet.get("channelTitle"),
                        "profile_url": f"https://www.youtube.com/channel/{channel_id}",
                        "follower_count": channel_stats.get("subscriberCount"),
                        "bio": clean_text(channel_snippet.get("description", "")),
                    },
                    "video": {
                        "video_id": f"youtube:{video_id}",
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": clean_text(snippet.get("title")),
                        "published_at": snippet.get("publishedAt"),
                        "description": description,
                        "transcript": "",
                        "view_count": stats.get("viewCount"),
                        "like_count": stats.get("likeCount"),
                        "comment_count": stats.get("commentCount"),
                    },
                }
            )

        logger.info(f"YouTube 采集完成，共 {len(items)} 条视频")
        return items

    def _fetch_videos(self, api_key: str, video_ids: List[str]) -> List[Dict]:
        videos: List[Dict] = []
        for chunk in _chunks(video_ids, 50):
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(chunk),
                "key": api_key,
            }
            data = _get_json("https://www.googleapis.com/youtube/v3/videos", params)
            videos.extend(data.get("items", []))
        return videos

    def _fetch_channels(self, api_key: str, channel_ids: List[str]) -> List[Dict]:
        channels: List[Dict] = []
        for chunk in _chunks(channel_ids, 50):
            params = {
                "part": "snippet,statistics",
                "id": ",".join(chunk),
                "key": api_key,
            }
            data = _get_json("https://www.googleapis.com/youtube/v3/channels", params)
            channels.extend(data.get("items", []))
        return channels


class BilibiliSource(SourceBase):
    name = "bilibili"

    def fetch(self, keywords: Iterable[str]) -> List[Dict]:
        max_results = int(self.config.get("max_results_per_keyword", 5))
        cookie = os.getenv("BILIBILI_COOKIE", "")
        headers = self.headers.copy()
        if cookie:
            headers["Cookie"] = cookie
        headers["Referer"] = "https://search.bilibili.com/"

        items: List[Dict] = []
        seen = set()
        for keyword in keywords:
            url = (
                "https://api.bilibili.com/x/web-interface/search/type"
                f"?search_type=video&keyword={quote_plus(keyword)}&page=1"
            )
            try:
                data = requests.get(url, headers=headers, timeout=15).json()
            except Exception as exc:
                logger.warning(f"B 站搜索失败: {keyword} - {exc}")
                continue

            for raw in data.get("data", {}).get("result", [])[:max_results]:
                bvid = raw.get("bvid")
                if not bvid or bvid in seen:
                    continue
                seen.add(bvid)
                detail = self._fetch_video_detail(bvid, headers)
                items.append(self._build_bilibili_item(raw, detail, headers))
            time.sleep(0.5)

        logger.info(f"B 站采集完成，共 {len(items)} 条视频")
        return items

    def _fetch_video_detail(self, bvid: str, headers: Dict) -> Dict:
        try:
            data = requests.get(
                f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
                headers=headers,
                timeout=15,
            ).json()
            return data.get("data", {}) or {}
        except Exception as exc:
            logger.warning(f"B 站视频详情失败: {bvid} - {exc}")
            return {}

    def _fetch_follower_count(self, mid, headers: Dict):
        if not mid:
            return None
        try:
            data = requests.get(
                f"https://api.bilibili.com/x/relation/stat?vmid={mid}",
                headers=headers,
                timeout=10,
            ).json()
            return data.get("data", {}).get("follower")
        except Exception:
            return None

    def _build_bilibili_item(self, raw: Dict, detail: Dict, headers: Dict) -> Dict:
        owner = detail.get("owner", {}) or {}
        stat = detail.get("stat", {}) or {}
        mid = owner.get("mid") or raw.get("mid")
        follower_count = None
        if mid:
            follower_count = self._fetch_follower_count(mid, headers)

        title = clean_text(BeautifulSoup(raw.get("title", ""), "html.parser").get_text(" "))
        bvid = raw.get("bvid") or detail.get("bvid")
        url = raw.get("arcurl") or f"https://www.bilibili.com/video/{bvid}"

        return {
            "platform": "Bilibili",
            "source": self.name,
            "creator": {
                "creator_id": f"bilibili:{mid}" if mid else None,
                "handle": raw.get("author") or owner.get("name"),
                "display_name": raw.get("author") or owner.get("name"),
                "profile_url": f"https://space.bilibili.com/{mid}" if mid else None,
                "follower_count": follower_count,
            },
            "video": {
                "video_id": f"bilibili:{bvid}" if bvid else None,
                "url": url,
                "title": title or clean_text(detail.get("title")),
                "published_at": _timestamp_to_iso(raw.get("pubdate") or detail.get("pubdate")),
                "description": clean_text(detail.get("desc") or raw.get("description")),
                "transcript": "",
                "view_count": stat.get("view") or parse_count(raw.get("play")),
                "like_count": stat.get("like"),
                "comment_count": stat.get("reply"),
                "share_count": stat.get("share"),
            },
        }


def build_sources(config: Dict, only: Iterable[str] = ()) -> List[SourceBase]:
    platforms = config.get("platforms", {})
    selected = set(only or [])
    source_classes = {
        "manual_csv": ManualCSVSource,
        "youtube": YouTubeSource,
        "bilibili": BilibiliSource,
    }
    sources: List[SourceBase] = []

    for name, cls in source_classes.items():
        source_config = platforms.get(name, {})
        if selected and name not in selected:
            continue
        if not source_config.get("enabled", True):
            continue
        sources.append(cls(source_config))

    return sources


def write_manual_template(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANUAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "platform": "小红书",
                "creator_handle": "example_handle",
                "creator_name": "示例博主",
                "profile_url": "https://example.com/profile",
                "follower_count": "82000",
                "creator_bio": "ADHD / 特殊教育 / 个人成长",
                "niche": "ADHD",
                "video_id": "example-video-001",
                "video_url": "https://example.com/video",
                "title": "我终于知道自己为什么总是和别人不一样",
                "published_at": "2026-06-28",
                "view_count": "360000",
                "like_count": "22000",
                "comment_count": "1800",
                "share_count": "900",
                "description": "用个人经历解释 ADHD 的注意力和社会适应差异。",
                "transcript": "这里粘贴视频口播、字幕、笔记正文或第三方转写文本。",
                "source_note": "人工导入示例，真实导入后可删除这一行。",
            }
        )
    return path


def _manual_row_to_item(row: Dict, source_name: str) -> Dict:
    platform = clean_text(row.get("platform")) or "manual"
    handle = clean_text(row.get("creator_handle")) or clean_text(row.get("creator_name"))
    creator_id = stable_id(platform, handle, row.get("profile_url"))
    video_id = clean_text(row.get("video_id")) or stable_id(platform, row.get("video_url"), row.get("title"))

    return {
        "platform": platform,
        "source": f"manual_csv:{source_name}",
        "creator": {
            "creator_id": f"{platform}:{creator_id}",
            "handle": handle,
            "display_name": clean_text(row.get("creator_name")) or handle,
            "profile_url": clean_text(row.get("profile_url")),
            "follower_count": row.get("follower_count"),
            "bio": clean_text(row.get("creator_bio")),
            "niche": clean_text(row.get("niche")),
        },
        "video": {
            "video_id": f"{platform}:{video_id}",
            "url": clean_text(row.get("video_url")),
            "title": clean_text(row.get("title")),
            "published_at": clean_text(row.get("published_at")),
            "description": clean_text(row.get("description")),
            "transcript": clean_text(row.get("transcript")),
            "view_count": row.get("view_count"),
            "like_count": row.get("like_count"),
            "comment_count": row.get("comment_count"),
            "share_count": row.get("share_count"),
        },
    }


def _get_json(url: str, params: Dict) -> Dict:
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _chunks(values: List[str], size: int):
    for i in range(0, len(values), size):
        yield values[i : i + size]


def _timestamp_to_iso(value):
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), timezone.utc).isoformat()
    except Exception:
        return str(value)
