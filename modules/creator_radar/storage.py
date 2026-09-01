"""
SQLite storage for long-running creator radar collection.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from modules.creator_radar.models import follower_bucket, parse_count, stable_id, utc_now_iso
from modules.utils import DATA_DIR


class CreatorRadarStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATA_DIR / "creator_radar" / "creator_radar.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS creators (
                creator_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                handle TEXT,
                display_name TEXT,
                profile_url TEXT,
                follower_count INTEGER,
                follower_bucket TEXT,
                niche TEXT,
                bio TEXT,
                source TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                published_at TEXT,
                description TEXT,
                transcript TEXT,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                share_count INTEGER,
                duration_seconds INTEGER,
                collected_at TEXT NOT NULL,
                source TEXT,
                raw_json TEXT,
                FOREIGN KEY (creator_id) REFERENCES creators(creator_id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                video_id TEXT PRIMARY KEY,
                analyzed_at TEXT NOT NULL,
                relevance_score REAL,
                virality_score REAL,
                engagement_rate REAL,
                views_to_followers_ratio REAL,
                topic_tags TEXT,
                core_thesis TEXT,
                why_good TEXT,
                traffic_drivers TEXT,
                reusable_patterns TEXT,
                content_text TEXT,
                recommended_action TEXT,
                raw_json TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            );

            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                sources TEXT,
                creators_seen INTEGER DEFAULT 0,
                videos_seen INTEGER DEFAULT 0,
                analyses_written INTEGER DEFAULT 0,
                report_path TEXT,
                status TEXT,
                error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_videos_collected_at ON videos(collected_at);
            CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform);
            CREATE INDEX IF NOT EXISTS idx_creators_platform ON creators(platform);
            CREATE INDEX IF NOT EXISTS idx_creators_bucket ON creators(follower_bucket);
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def start_run(self, sources: Iterable[str]) -> str:
        run_id = stable_id("run", utc_now_iso(), ",".join(sources))
        self.conn.execute(
            """
            INSERT INTO runs (run_id, started_at, sources, status)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, utc_now_iso(), json.dumps(list(sources), ensure_ascii=False), "running"),
        )
        self.conn.commit()
        return run_id

    def finish_run(
        self,
        run_id: str,
        creators_seen: int,
        videos_seen: int,
        analyses_written: int,
        report_path: Optional[str],
        status: str = "ok",
        error: Optional[str] = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, creators_seen = ?, videos_seen = ?,
                analyses_written = ?, report_path = ?, status = ?, error = ?
            WHERE run_id = ?
            """,
            (
                utc_now_iso(),
                creators_seen,
                videos_seen,
                analyses_written,
                report_path,
                status,
                error,
                run_id,
            ),
        )
        self.conn.commit()

    def upsert_creator_video(self, item: Dict) -> Dict[str, str]:
        now = utc_now_iso()
        platform = item.get("platform") or "unknown"
        creator = item.get("creator") or {}
        video = item.get("video") or {}

        handle = creator.get("handle") or creator.get("display_name") or "unknown"
        creator_id = creator.get("creator_id") or stable_id(platform, handle, creator.get("profile_url"))
        follower_count = parse_count(creator.get("follower_count"))
        bucket = follower_bucket(follower_count)

        self.conn.execute(
            """
            INSERT INTO creators (
                creator_id, platform, handle, display_name, profile_url,
                follower_count, follower_bucket, niche, bio, source,
                first_seen_at, last_seen_at, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(creator_id) DO UPDATE SET
                handle = excluded.handle,
                display_name = excluded.display_name,
                profile_url = COALESCE(excluded.profile_url, creators.profile_url),
                follower_count = COALESCE(excluded.follower_count, creators.follower_count),
                follower_bucket = COALESCE(excluded.follower_bucket, creators.follower_bucket),
                niche = COALESCE(excluded.niche, creators.niche),
                bio = COALESCE(excluded.bio, creators.bio),
                source = excluded.source,
                last_seen_at = excluded.last_seen_at,
                raw_json = excluded.raw_json
            """,
            (
                creator_id,
                platform,
                creator.get("handle"),
                creator.get("display_name"),
                creator.get("profile_url"),
                follower_count,
                bucket,
                creator.get("niche"),
                creator.get("bio"),
                item.get("source"),
                now,
                now,
                json.dumps(creator, ensure_ascii=False),
            ),
        )

        video_id = video.get("video_id") or stable_id(platform, video.get("url"), video.get("title"), creator_id)
        self.conn.execute(
            """
            INSERT INTO videos (
                video_id, platform, creator_id, title, url, published_at,
                description, transcript, view_count, like_count, comment_count,
                share_count, duration_seconds, collected_at, source, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title = excluded.title,
                url = COALESCE(excluded.url, videos.url),
                published_at = COALESCE(excluded.published_at, videos.published_at),
                description = COALESCE(excluded.description, videos.description),
                transcript = COALESCE(excluded.transcript, videos.transcript),
                view_count = COALESCE(excluded.view_count, videos.view_count),
                like_count = COALESCE(excluded.like_count, videos.like_count),
                comment_count = COALESCE(excluded.comment_count, videos.comment_count),
                share_count = COALESCE(excluded.share_count, videos.share_count),
                duration_seconds = COALESCE(excluded.duration_seconds, videos.duration_seconds),
                collected_at = excluded.collected_at,
                source = excluded.source,
                raw_json = excluded.raw_json
            """,
            (
                video_id,
                platform,
                creator_id,
                video.get("title") or "Untitled",
                video.get("url"),
                video.get("published_at"),
                video.get("description"),
                video.get("transcript"),
                parse_count(video.get("view_count")),
                parse_count(video.get("like_count")),
                parse_count(video.get("comment_count")),
                parse_count(video.get("share_count")),
                parse_count(video.get("duration_seconds")),
                now,
                item.get("source"),
                json.dumps(video, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return {"creator_id": creator_id, "video_id": video_id}

    def upsert_many(self, items: Iterable[Dict]) -> List[Dict[str, str]]:
        ids = []
        for item in items:
            ids.append(self.upsert_creator_video(item))
        return ids

    def get_video_context(self, video_id: str) -> Optional[Dict]:
        row = self.conn.execute(
            """
            SELECT v.*, c.handle, c.display_name, c.profile_url, c.follower_count,
                   c.follower_bucket, c.niche, c.bio
            FROM videos v
            JOIN creators c ON c.creator_id = v.creator_id
            WHERE v.video_id = ?
            """,
            (video_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_unanalyzed(self, limit: int = 50) -> List[Dict]:
        rows = self.conn.execute(
            """
            SELECT v.video_id
            FROM videos v
            LEFT JOIN analyses a ON a.video_id = v.video_id
            WHERE a.video_id IS NULL
            ORDER BY v.collected_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self.get_video_context(row["video_id"]) for row in rows]

    def save_analysis(self, video_id: str, analysis: Dict) -> None:
        self.conn.execute(
            """
            INSERT INTO analyses (
                video_id, analyzed_at, relevance_score, virality_score,
                engagement_rate, views_to_followers_ratio, topic_tags,
                core_thesis, why_good, traffic_drivers, reusable_patterns,
                content_text, recommended_action, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                analyzed_at = excluded.analyzed_at,
                relevance_score = excluded.relevance_score,
                virality_score = excluded.virality_score,
                engagement_rate = excluded.engagement_rate,
                views_to_followers_ratio = excluded.views_to_followers_ratio,
                topic_tags = excluded.topic_tags,
                core_thesis = excluded.core_thesis,
                why_good = excluded.why_good,
                traffic_drivers = excluded.traffic_drivers,
                reusable_patterns = excluded.reusable_patterns,
                content_text = excluded.content_text,
                recommended_action = excluded.recommended_action,
                raw_json = excluded.raw_json
            """,
            (
                video_id,
                utc_now_iso(),
                analysis.get("relevance_score"),
                analysis.get("virality_score"),
                analysis.get("engagement_rate"),
                analysis.get("views_to_followers_ratio"),
                json.dumps(analysis.get("topic_tags", []), ensure_ascii=False),
                analysis.get("core_thesis"),
                analysis.get("why_good"),
                analysis.get("traffic_drivers"),
                analysis.get("reusable_patterns"),
                analysis.get("content_text"),
                analysis.get("recommended_action"),
                json.dumps(analysis, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def list_report_items(self, since_days: int, min_relevance: float, limit: int) -> List[Dict]:
        rows = self.conn.execute(
            """
            SELECT
                v.*, c.handle, c.display_name, c.profile_url, c.follower_count,
                c.follower_bucket, c.niche, c.bio,
                a.analyzed_at, a.relevance_score, a.virality_score,
                a.engagement_rate, a.views_to_followers_ratio, a.topic_tags,
                a.core_thesis, a.why_good, a.traffic_drivers,
                a.reusable_patterns, a.content_text, a.recommended_action
            FROM analyses a
            JOIN videos v ON v.video_id = a.video_id
            JOIN creators c ON c.creator_id = v.creator_id
            WHERE datetime(v.collected_at) >= datetime('now', ?)
              AND COALESCE(a.relevance_score, 0) >= ?
            ORDER BY COALESCE(a.virality_score, 0) DESC,
                     COALESCE(v.view_count, 0) DESC
            LIMIT ?
            """,
            (f"-{since_days} days", min_relevance, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def latest_run(self) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
