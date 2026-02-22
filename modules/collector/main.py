"""
选题采集器主入口
负责协调数据源采集、去重、打分、保存
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from modules.collector.sources import collect_all_sources
from modules.collector.scorer import TopicScorer
from modules.utils import setup_logger, save_json, get_date_str, DATA_DIR

logger = setup_logger('collector_main', 'collector.log')

# 尝试导入 OpenClaw 实时采集器
try:
    from modules.collector.realtime_collector import RealtimeCollector
    OPENCLAW_AVAILABLE = True
except:
    OPENCLAW_AVAILABLE = False
    logger.warning("OpenClaw 实时采集器不可用")

# 导入 Claude 备用采集器
try:
    from modules.collector.claude_collector import ClaudeCollector
    CLAUDE_AVAILABLE = True
except:
    CLAUDE_AVAILABLE = False
    logger.warning("Claude 备用采集器不可用")


class TopicCollector:
    """选题采集器"""

    def __init__(self):
        self.topics_dir = DATA_DIR / 'topics'
        self.topics_dir.mkdir(exist_ok=True)
        self.scorer = TopicScorer()

    def run(self, use_openclaw: bool = True) -> List[Dict]:
        """运行完整的采集流程"""
        logger.info("=" * 50)
        logger.info("开始选题采集流程")
        logger.info("=" * 50)

        # 优先尝试 OpenClaw 实时采集
        if use_openclaw and OPENCLAW_AVAILABLE:
            logger.info("尝试使用 OpenClaw 实时采集全网热点")
            try:
                openclaw_collector = RealtimeCollector()
                topics = openclaw_collector.run()
                if topics and len(topics) >= 10:
                    logger.info(f"OpenClaw 实时采集成功，共 {len(topics)} 个选题")
                    return topics
                else:
                    logger.warning("OpenClaw 实时采集选题不足，切换到传统方式")
            except Exception as e:
                logger.error(f"OpenClaw 实时采集异常: {str(e)}，切换到传统方式")

        # 1. 采集所有数据源（传统方式）
        logger.info("步骤 1/4: 采集数据源（传统方式）")
        raw_topics = collect_all_sources()

        # 如果传统数据源失败，使用 Claude 备用方案
        if not raw_topics:
            logger.warning("传统数据源采集失败，切换到 Claude 备用方案")
            if CLAUDE_AVAILABLE:
                try:
                    claude_collector = ClaudeCollector()
                    topics = claude_collector.run()
                    if topics:
                        logger.info(f"Claude 备用采集成功，共 {len(topics)} 个选题")
                        return topics
                except Exception as e:
                    logger.error(f"Claude 备用采集失败: {str(e)}")

            logger.error("所有采集方式都失败")
            return []

        # 2. 去重
        logger.info("步骤 2/4: 去重处理")
        unique_topics = self._deduplicate(raw_topics)
        logger.info(f"去重后剩余 {len(unique_topics)} 个选题")

        # 3. 打分
        logger.info("步骤 3/4: AI 打分")
        scored_topics = self.scorer.score_topics(unique_topics)

        # 4. 保存结果
        logger.info("步骤 4/4: 保存结果")
        self._save_topics(scored_topics)

        # 筛选高分选题（总分 >= 25）
        high_score_topics = [t for t in scored_topics if t['total_score'] >= 25]
        logger.info(f"高分选题（>=25分）: {len(high_score_topics)} 个")

        logger.info("=" * 50)
        logger.info(f"选题采集完成！共 {len(scored_topics)} 个选题，推荐 {len(high_score_topics)} 个")
        logger.info("=" * 50)

        return scored_topics

    def _deduplicate(self, topics: List[Dict]) -> List[Dict]:
        """去重：基于标题相似度"""
        seen_titles = set()
        unique_topics = []

        for topic in topics:
            title = topic['title'].strip()

            # 简单去重：标题完全相同
            if title in seen_titles:
                continue

            # 检查是否与已有标题高度相似（前20个字符）
            title_prefix = title[:20]
            if any(title_prefix in seen for seen in seen_titles):
                continue

            seen_titles.add(title)
            unique_topics.append(topic)

        return unique_topics

    def _save_topics(self, topics: List[Dict]):
        """保存选题到文件"""
        date_str = get_date_str()
        filename = f"topics_{date_str}.json"
        filepath = self.topics_dir / filename

        save_json({
            'date': date_str,
            'total_count': len(topics),
            'high_score_count': len([t for t in topics if t['total_score'] >= 25]),
            'topics': topics
        }, filepath)

        logger.info(f"选题已保存到: {filepath}")

        # 同时保存一份 latest.json 供 Web 界面使用
        latest_path = self.topics_dir / 'latest.json'
        save_json({
            'date': date_str,
            'total_count': len(topics),
            'high_score_count': len([t for t in topics if t['total_score'] >= 25]),
            'topics': topics
        }, latest_path)

    def get_latest_topics(self) -> List[Dict]:
        """获取最新的选题列表"""
        latest_path = self.topics_dir / 'latest.json'

        if not latest_path.exists():
            logger.warning("未找到最新选题文件")
            return []

        with open(latest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('topics', [])


def main():
    """主函数"""
    collector = TopicCollector()
    topics = collector.run()

    if not topics:
        print("\n❌ 采集失败，未获得任何选题")
        return

    # 打印前 5 个高分选题
    print("\n" + "=" * 60)
    print("📊 今日推荐选题（前5个）")
    print("=" * 60)

    # 检查是否有 total_score 字段（Claude 生成的选题没有打分）
    if topics and 'total_score' in topics[0]:
        high_score_topics = [t for t in topics if t['total_score'] >= 25][:5]
    else:
        # 没有打分的选题，直接取前5个
        high_score_topics = topics[:5]

    for i, topic in enumerate(high_score_topics, 1):
        print(f"\n{i}. {topic['title']}")
        if 'total_score' in topic:
            print(f"   总分: {topic['total_score']}/40")
        if 'heat_score' in topic:
            print(f"   热度: {topic['heat_score']}")
        print(f"   来源: {topic.get('source', '未知')}")
        if 'ai_reason' in topic:
            print(f"   理由: {topic['ai_reason']}")
        if 'excerpt' in topic:
            print(f"   摘要: {topic['excerpt'][:80]}...")
        if 'suggested_angles' in topic:
            print(f"   建议角度: {', '.join(topic['suggested_angles'][:2])}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
