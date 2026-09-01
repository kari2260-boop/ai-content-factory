"""
Creator radar orchestration.
"""
from pathlib import Path
from typing import Iterable, List, Optional

from modules.creator_radar.analyzer import CreatorAnalyzer
from modules.creator_radar.config import load_config, save_default_config
from modules.creator_radar.reporter import CreatorRadarReporter
from modules.creator_radar.sources import build_sources, write_manual_template
from modules.creator_radar.storage import CreatorRadarStore
from modules.utils import PROJECT_ROOT, setup_logger

logger = setup_logger("creator_radar", "creator_radar.log")


class CreatorRadar:
    def __init__(self):
        self.config = load_config()
        self.store = CreatorRadarStore()
        self.analyzer = CreatorAnalyzer(self.config)
        self.reporter = CreatorRadarReporter(self.config)

    def init_files(self) -> dict:
        config_file = save_default_config(overwrite=False)
        template = PROJECT_ROOT / "data" / "creator_radar" / "imports" / "_manual_import_template.csv"
        write_manual_template(template)
        return {
            "config": str(config_file),
            "db": str(self.store.db_path),
            "manual_template": str(template),
        }

    def run(
        self,
        source_names: Optional[Iterable[str]] = None,
        analyze_limit: int = 80,
        skip_collect: bool = False,
    ) -> Path:
        source_names = list(source_names or [])
        selected_sources = build_sources(self.config, only=source_names)
        source_labels = [source.name for source in selected_sources]
        if skip_collect:
            source_labels = ["skip_collect"]
        run_id = self.store.start_run(source_labels)
        creators_seen = 0
        videos_seen = 0
        analyses_written = 0
        report_path = None

        try:
            if not skip_collect:
                keywords = self.config.get("keywords", [])
                for source in selected_sources:
                    logger.info(f"开始采集源: {source.name}")
                    items = source.fetch(keywords)
                    ids = self.store.upsert_many(items)
                    creators_seen += len({item["creator_id"] for item in ids})
                    videos_seen += len(ids)

            pending = [row for row in self.store.list_unanalyzed(limit=analyze_limit) if row]
            logger.info(f"待分析视频: {len(pending)}")
            for row in pending:
                analysis = self.analyzer.analyze(row)
                self.store.save_analysis(row["video_id"], analysis)
                analyses_written += 1

            report_config = self.config.get("report", {})
            items = self.store.list_report_items(
                since_days=int(report_config.get("since_days", 7)),
                min_relevance=float(report_config.get("min_relevance_score", 4.0)),
                limit=int(report_config.get("top_n", 20)),
            )
            report_path = self.reporter.write_report(
                items,
                {
                    "run_id": run_id,
                    "sources": source_labels,
                    "creators_seen": creators_seen,
                    "videos_seen": videos_seen,
                },
            )
            self.store.finish_run(
                run_id,
                creators_seen=creators_seen,
                videos_seen=videos_seen,
                analyses_written=analyses_written,
                report_path=str(report_path),
            )
            logger.info(f"创作者雷达日报已生成: {report_path}")
            return report_path
        except Exception as exc:
            self.store.finish_run(
                run_id,
                creators_seen=creators_seen,
                videos_seen=videos_seen,
                analyses_written=analyses_written,
                report_path=str(report_path) if report_path else None,
                status="failed",
                error=str(exc),
            )
            raise

    def generate_report_only(self) -> Path:
        report_config = self.config.get("report", {})
        items = self.store.list_report_items(
            since_days=int(report_config.get("since_days", 7)),
            min_relevance=float(report_config.get("min_relevance_score", 4.0)),
            limit=int(report_config.get("top_n", 20)),
        )
        return self.reporter.write_report(
            items,
            {
                "run_id": "report-only",
                "sources": ["existing-db"],
                "creators_seen": 0,
                "videos_seen": 0,
            },
        )

    def close(self) -> None:
        self.store.close()
