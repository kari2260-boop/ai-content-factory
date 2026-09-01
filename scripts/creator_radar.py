#!/usr/bin/env python3
"""
Command line entry for creator radar.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.creator_radar.runner import CreatorRadar


def main():
    parser = argparse.ArgumentParser(description="Neurodiversity creator radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create config, database, and manual CSV template")

    run_parser = subparsers.add_parser("run", help="Collect, analyze, and generate daily report")
    run_parser.add_argument(
        "--source",
        action="append",
        choices=["manual_csv", "youtube", "bilibili"],
        help="Run only selected source. Can be repeated.",
    )
    run_parser.add_argument("--skip-collect", action="store_true", help="Only analyze/report existing DB rows")
    run_parser.add_argument("--analyze-limit", type=int, default=80)

    subparsers.add_parser("report", help="Generate report from existing database")

    radar = CreatorRadar()
    try:
        args = parser.parse_args()
        if args.command == "init":
            files = radar.init_files()
            for key, value in files.items():
                print(f"{key}: {value}")
        elif args.command == "run":
            path = radar.run(
                source_names=args.source,
                analyze_limit=args.analyze_limit,
                skip_collect=args.skip_collect,
            )
            print(path)
        elif args.command == "report":
            path = radar.generate_report_only()
            print(path)
    finally:
        radar.close()


if __name__ == "__main__":
    main()
