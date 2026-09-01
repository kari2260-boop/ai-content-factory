"""
Markdown report generation for creator radar.
"""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.creator_radar.models import truncate
from modules.utils import PROJECT_ROOT


class CreatorRadarReporter:
    def __init__(self, config: Dict):
        self.config = config
        report_config = config.get("report", {})
        output_dir = Path(report_config.get("output_dir", "data/creator_radar/reports"))
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, items: List[Dict], run_meta: Dict) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = self.output_dir / f"creator_radar_{date_str}.md"
        content = self.render(items, run_meta)
        path.write_text(content, encoding="utf-8")
        return path

    def render(self, items: List[Dict], run_meta: Dict) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# 神经多样性创作者雷达日报 - {date_str}",
            "",
            "## 今日结论",
        ]

        if not items:
            lines.extend(
                [
                    "",
                    "今天没有达到报告阈值的新样本。",
                    "",
                    "优先检查：是否配置 `YOUTUBE_API_KEY`、是否提供 `BILIBILI_COOKIE`、是否把小红书/视频号导出 CSV 放进 `data/creator_radar/imports/`。",
                ]
            )
            return "\n".join(lines) + "\n"

        platform_counter = Counter(item.get("platform") for item in items)
        bucket_counter = Counter(item.get("follower_bucket") for item in items)
        top = items[0]

        lines.extend(
            [
                "",
                f"- 本期入选 {len(items)} 条视频，覆盖平台：{_counter_text(platform_counter)}。",
                f"- 粉丝层级分布：{_counter_text(bucket_counter)}。",
                f"- 最高优先级样本：{top.get('title')}（{top.get('platform')}，播放 {top.get('view_count') or '未知'}，粉丝 {top.get('follower_count') or '未知'}）。",
                "",
                "## 高优先级视频",
                "",
                "| 排名 | 平台 | 博主 | 粉丝区间 | 播放 | 点赞 | 爆火分 | 主题 | 链接 |",
                "|---:|---|---|---|---:|---:|---:|---|---|",
            ]
        )

        for idx, item in enumerate(items, 1):
            tags = ", ".join(_parse_tags(item.get("topic_tags"))) or "-"
            link = item.get("url") or item.get("profile_url") or ""
            link_text = f"[打开]({link})" if link else "-"
            lines.append(
                "| {idx} | {platform} | {creator} | {bucket} | {views} | {likes} | {score} | {tags} | {link} |".format(
                    idx=idx,
                    platform=item.get("platform") or "-",
                    creator=truncate(item.get("display_name") or item.get("handle") or "-", 24),
                    bucket=item.get("follower_bucket") or "未知",
                    views=item.get("view_count") or 0,
                    likes=item.get("like_count") or 0,
                    score=round(item.get("virality_score") or 0, 1),
                    tags=tags,
                    link=link_text,
                )
            )

        lines.extend(["", "## 逐条拆解", ""])
        for idx, item in enumerate(items, 1):
            lines.extend(self._render_item(idx, item))

        grouped = defaultdict(list)
        for item in items:
            grouped[item.get("follower_bucket") or "未知"].append(item)

        lines.extend(["", "## 粉丝区间观察", ""])
        for bucket, bucket_items in grouped.items():
            best = bucket_items[0]
            lines.append(
                f"- {bucket}：{len(bucket_items)} 条入选。代表样本《{best.get('title')}》，适合观察这个量级账号如何破圈。"
            )

        lines.extend(
            [
                "",
                "## 明日动作",
                "",
                "- 给入选前 3 条补齐完整字幕/口播文本，优先补小红书和视频号。",
                "- 对播放/粉丝比超过 3 的样本做标题、开头 5 秒、评论区高频词拆解。",
                "- 选 1 条改写成自己的视频号脚本，保留结构和观点机制，不复刻原文表达。",
                "",
                "## 运行信息",
                "",
                f"- run_id: `{run_meta.get('run_id', '-')}`",
                f"- sources: `{', '.join(run_meta.get('sources', []))}`",
                f"- collected: creators `{run_meta.get('creators_seen', 0)}`, videos `{run_meta.get('videos_seen', 0)}`",
            ]
        )
        return "\n".join(lines) + "\n"

    def _render_item(self, idx: int, item: Dict) -> List[str]:
        tags = ", ".join(_parse_tags(item.get("topic_tags"))) or "-"
        ratio = item.get("views_to_followers_ratio")
        ratio_text = f"{ratio}x" if ratio is not None else "未知"
        content_text = truncate(item.get("content_text") or "", 900)

        return [
            f"### {idx}. {item.get('title')}",
            "",
            f"- 博主：{item.get('display_name') or item.get('handle') or '-'}",
            f"- 平台：{item.get('platform') or '-'}",
            f"- 粉丝量：{item.get('follower_count') or '未知'}（{item.get('follower_bucket') or '未知'}）",
            f"- 播放/点赞/评论/分享：{item.get('view_count') or 0} / {item.get('like_count') or 0} / {item.get('comment_count') or 0} / {item.get('share_count') or 0}",
            f"- 播放粉丝比：{ratio_text}",
            f"- 主题标签：{tags}",
            f"- 核心主旨：{item.get('core_thesis') or '-'}",
            f"- 为什么好：{item.get('why_good') or '-'}",
            f"- 为什么吸引流量：{item.get('traffic_drivers') or '-'}",
            f"- 我可以借鉴：{item.get('reusable_patterns') or '-'}",
            f"- 建议动作：{item.get('recommended_action') or '-'}",
            "",
            "视频文本/可用文本：",
            "",
            f"> {content_text or '暂无文本。'}",
            "",
        ]


def _counter_text(counter: Counter) -> str:
    return "、".join(f"{key or '未知'} {value}" for key, value in counter.items()) or "无"


def _parse_tags(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                import json

                return json.loads(text)
            except Exception:
                pass
        return [part.strip() for part in text.split(",") if part.strip()]
    return []
