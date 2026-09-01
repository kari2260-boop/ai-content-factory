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

# 尝试导入 OpenClaw 现成采集器（优先）
try:
    from modules.collector.openclaw_final_collector import OpenClawFinalCollector
    OPENCLAW_FINAL_AVAILABLE = True
except:
    OPENCLAW_FINAL_AVAILABLE = False
    logger.warning("OpenClaw Final 采集器不可用")

# 尝试导入 OpenClaw Agent 采集器（备用）
try:
    from modules.collector.openclaw_agent_collector import OpenClawAgentCollector
    OPENCLAW_AGENT_AVAILABLE = True
except:
    OPENCLAW_AGENT_AVAILABLE = False
    logger.warning("OpenClaw Agent 采集器不可用")

# 导入 Claude 备用采集器
try:
    from modules.collector.claude_collector import ClaudeCollector
    CLAUDE_AVAILABLE = True
except:
    CLAUDE_AVAILABLE = False
    logger.warning("Claude 备用采集器不可用")


class TopicCollector:
    """选题采集器"""

    STRONG_TOPIC_KEYWORDS = [
        '教育', '留学', '学校', '大学', '学生', '孩子', '家长', '家庭',
        '科研', '论文', '申请', '国际学校', '课程', '考试', '升学', '招生',
        '班主任', '作业', '育儿', '家校', '学术'
    ]

    def __init__(self, user_id: str = 'dr_k'):
        self.user_id = user_id
        # 使用用户专属数据目录
        from modules.utils import DATA_DIR
        self.topics_dir = DATA_DIR / 'users' / user_id / 'topics'
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self.scorer = TopicScorer()

    def run(self, use_openclaw: bool = False, ai_scoring: bool = False) -> List[Dict]:
        """运行完整的采集流程"""
        logger.info("=" * 50)
        logger.info("开始选题采集流程")
        logger.info("=" * 50)

        # 优先尝试 OpenClaw 现成定时任务/采集器
        if use_openclaw and OPENCLAW_FINAL_AVAILABLE:
            logger.info("尝试使用 OpenClaw Final 采集器")
            try:
                final_collector = OpenClawFinalCollector(user_id=self.user_id)
                topics = final_collector.run()
                if topics:
                    logger.info(f"OpenClaw Final 采集成功，共 {len(topics)} 个选题")
                    return topics
                else:
                    logger.warning("OpenClaw Final 选题不足，切换到 OpenClaw Agent")
            except Exception as e:
                logger.error(f"OpenClaw Final 采集异常: {str(e)}，切换到 OpenClaw Agent")

        # 备用：OpenClaw Agent 采集
        if use_openclaw and OPENCLAW_AGENT_AVAILABLE:
            logger.info("尝试使用 OpenClaw Agent 采集选题")
            try:
                agent_collector = OpenClawAgentCollector(user_id=self.user_id)
                topics = agent_collector.run()
                if topics:
                    logger.info(f"OpenClaw Agent 采集成功，共 {len(topics)} 个选题")
                    return topics
                else:
                    logger.warning("OpenClaw Agent 选题不足，切换到传统方式")
            except Exception as e:
                logger.error(f"OpenClaw Agent 采集异常: {str(e)}，切换到传统方式")

        # 1. 采集所有数据源（传统方式）
        logger.info("步骤 1/4: 采集数据源（传统方式）")
        raw_topics = collect_all_sources()

        # 优先保留本轮新抓到的题目，避免每次手动采集都返回上一轮同一批内容
        raw_topics = self._prefer_fresh_topics(raw_topics)

        # 如果相关题目太少，补入本地教育兜底题，避免返回一堆泛科技热榜
        if self._count_strong_topics(raw_topics) < 8:
            logger.warning("强教育相关题目不足，补充本地教育兜底题")
            raw_topics = self._merge_with_fallback_topics(raw_topics)

        # 如果传统数据源失败，快速模式优先返回缓存/本地兜底，避免页面长时间无响应
        if not raw_topics:
            if not use_openclaw:
                cached_topics = self._load_cached_topics()
                if cached_topics:
                    logger.warning("传统数据源采集失败，返回最近一次缓存选题")
                    return cached_topics

                logger.warning("传统数据源采集失败，使用本地兜底选题")
                fallback_topics = self.scorer.score_topics_fast(self._fallback_topics())
                self._save_topics(fallback_topics)
                return fallback_topics

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

        # 2.5 过滤掉明显不属于教育/留学/家庭学习语境的选题
        relevant_topics = [topic for topic in unique_topics if self.scorer.is_relevant_topic(topic)]
        filtered_out = len(unique_topics) - len(relevant_topics)
        if filtered_out > 0:
            logger.info(f"相关性过滤移除 {filtered_out} 个不匹配选题，保留 {len(relevant_topics)} 个")

        if len(relevant_topics) < 8:
            logger.warning("相关题目不足，补充本地兜底题")
            relevant_topics = self._merge_with_fallback_topics(relevant_topics)

        # 3. 打分
        if ai_scoring:
            logger.info("步骤 3/4: AI 打分")
            scored_topics = self.scorer.score_topics(relevant_topics)
        else:
            logger.info("步骤 3/4: 快速本地打分")
            scored_topics = self.scorer.score_topics_fast(relevant_topics)

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

    def _load_cached_topics(self) -> List[Dict]:
        """加载最近一次缓存选题。"""
        try:
            return self.get_latest_topics()
        except Exception as e:
            logger.warning(f"读取缓存选题失败: {e}")
            return []

    def _prefer_fresh_topics(self, topics: List[Dict], keep_limit: int = 20) -> List[Dict]:
        """优先保留本轮新出现的题目，减少重复采集同一批旧题。"""
        if not topics:
            return topics

        recent_topics = self._load_cached_topics()
        if not recent_topics:
            return topics

        recent_signatures = set()
        for item in recent_topics:
            title = (item.get('title') or '').strip()
            if not title:
                continue
            recent_signatures.add(title)
            recent_signatures.add(title[:20])

        fresh_topics: List[Dict] = []
        repeated_topics: List[Dict] = []
        seen_signatures = set()

        for topic in topics:
            title = (topic.get('title') or '').strip()
            if not title:
                continue

            signature = title[:20]
            if title in seen_signatures:
                continue
            seen_signatures.add(title)

            if title in recent_signatures or signature in recent_signatures:
                repeated_topics.append(topic)
            else:
                fresh_topics.append(topic)

        if fresh_topics:
            logger.info(
                f"本轮采集中过滤掉 {len(repeated_topics)} 个近期重复题目，保留 {len(fresh_topics)} 个新题目"
            )

        # 新题不够时，用重复题补齐，但优先把新题排前面
        merged = fresh_topics + repeated_topics
        return merged[:keep_limit] if keep_limit else merged

    def _count_strong_topics(self, topics: List[Dict]) -> int:
        """统计强教育相关题目数量。"""
        return sum(1 for topic in topics if self.scorer.is_relevant_topic(topic))

    def _merge_with_fallback_topics(self, topics: List[Dict]) -> List[Dict]:
        """用本地兜底题补足主题相关性。"""
        merged: List[Dict] = []
        seen_titles = set()

        for item in self._fallback_topics() + topics:
            title = (item.get('title') or '').strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            merged.append(item)

        return merged[:20]

    def _fallback_topics(self) -> List[Dict]:
        """网络不可用时的本地兜底选题，保证采集页面不会空转。"""
        now = datetime.now().isoformat()
        topics = [
            {
                'title': 'AI 时代，孩子到底该学什么才不会被工具替代？',
                'excerpt': '从刷题、编程到提问能力、判断力和项目制学习，讨论家庭教育在 AI 时代的真正转向。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '论文造假频发，普通家长该如何理解大学和科研评价体系？',
                'excerpt': '从学术信用、名校光环和评价机制切入，解释科研新闻背后的教育价值观。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '越来越多学生用 AI 写作业，学校到底该堵还是该教？',
                'excerpt': 'AI 作业不是简单作弊问题，而是学习目标、评价方式和教师角色的变化。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '留学申请进入 AI 时代，文书和背景提升会发生什么变化？',
                'excerpt': '当文书生产门槛下降，真正稀缺的是学生经历、判断力和长期成长线索。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '家长最该警惕的不是孩子不会用 AI，而是只会复制答案',
                'excerpt': 'AI 工具普及后，孩子的差距会体现在问题定义、信息验证和作品表达上。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '国际学校和公立体系的差距，正在被 AI 工具重新改写吗？',
                'excerpt': '从资源、语言、项目学习和个性化辅导角度，讨论 AI 是否会改变教育公平。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '为什么越是 AI 时代，孩子越需要真实世界的项目经验？',
                'excerpt': '项目经验能训练观察、协作、表达和解决问题能力，是单纯刷题难以替代的部分。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
            {
                'title': '当名校标签越来越贵，普通家庭还要不要卷名校？',
                'excerpt': '从投入产出、孩子适配度和长期竞争力角度，重新讨论名校路径的价值。',
                'source': '本地兜底',
                'url': '',
                'heat_score': '中',
                'collected_at': now
            },
        ]
        return topics


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
