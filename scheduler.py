"""
定时任务调度器
每天早上 7:00 自动运行选题采集
"""
import schedule
import time
import sys
from datetime import datetime

from modules.collector.main import TopicCollector
from modules.creator_radar.runner import CreatorRadar
from modules.utils import setup_logger

try:
    from modules.collector.openclaw_final_collector import OpenClawFinalCollector
    OPENCLAW_FINAL_AVAILABLE = True
except Exception:
    OpenClawFinalCollector = None
    OPENCLAW_FINAL_AVAILABLE = False

try:
    from modules.collector.openclaw_agent_collector import OpenClawAgentCollector
    OPENCLAW_AGENT_AVAILABLE = True
except Exception:
    OpenClawAgentCollector = None
    OPENCLAW_AGENT_AVAILABLE = False

logger = setup_logger('scheduler', 'scheduler.log')


def daily_collection_task():
    """每日选题采集任务"""
    logger.info("=" * 60)
    logger.info(f"开始执行每日选题采集任务 - {datetime.now()}")
    logger.info("=" * 60)

    try:
        topics = []
        if OPENCLAW_FINAL_AVAILABLE:
            try:
                logger.info("优先使用 OpenClaw Final 采集器")
                topics = OpenClawFinalCollector(user_id='dr_k').run()
            except Exception as e:
                logger.error(f"OpenClaw Final 采集失败: {str(e)}")

        if not topics and OPENCLAW_AGENT_AVAILABLE:
            try:
                logger.info("回退使用 OpenClaw Agent 采集器")
                topics = OpenClawAgentCollector(user_id='dr_k').run()
            except Exception as e:
                logger.error(f"OpenClaw Agent 采集失败: {str(e)}")

        if not topics:
            logger.info("OpenClaw 采集未成功，回退到传统 TopicCollector")
            collector = TopicCollector()
            topics = collector.run(use_openclaw=False, ai_scoring=False)

        logger.info(f"✅ 每日选题采集完成，共 {len(topics)} 个选题")

        # 统计高分选题
        high_score = [t for t in topics if t.get('total_score', 0) >= 25]
        logger.info(f"📊 高分选题（>=25分）: {len(high_score)} 个")

        # 打印前3个推荐选题
        logger.info("\n推荐选题（前3个）:")
        for i, topic in enumerate(high_score[:3], 1):
            logger.info(f"{i}. {topic['title']} (总分: {topic.get('total_score', 0)})")

    except Exception as e:
        logger.error(f"❌ 每日选题采集失败: {str(e)}")

    logger.info("=" * 60)


def weekly_book_integration_task():
    """每周书稿整合任务（周日执行）"""
    logger.info("=" * 60)
    logger.info(f"开始执行每周书稿整合任务 - {datetime.now()}")
    logger.info("=" * 60)

    # TODO: 实现书稿整合逻辑
    logger.info("📚 书稿整合功能待实现")

    logger.info("=" * 60)


def daily_creator_radar_task():
    """每日神经多样性创作者雷达日报"""
    logger.info("=" * 60)
    logger.info(f"开始执行创作者雷达日报任务 - {datetime.now()}")
    logger.info("=" * 60)

    radar = CreatorRadar()
    try:
        report_path = radar.run()
        logger.info(f"创作者雷达日报完成: {report_path}")
    except Exception as e:
        logger.error(f"创作者雷达日报失败: {str(e)}")
    finally:
        radar.close()

    logger.info("=" * 60)


def run_scheduler():
    """运行调度器"""
    logger.info("🚀 定时任务调度器启动")

    # 每天早上 7:00 执行选题采集
    schedule.every().day.at("07:00").do(daily_collection_task)

    # 每天早上 8:00 执行创作者雷达日报
    schedule.every().day.at("08:00").do(daily_creator_radar_task)

    # 每周日早上 8:00 执行书稿整合
    schedule.every().sunday.at("08:00").do(weekly_book_integration_task)

    logger.info("📅 已设置定时任务:")
    logger.info("  - 每日 07:00: 选题采集")
    logger.info("  - 每日 08:00: 神经多样性创作者雷达日报")
    logger.info("  - 每周日 08:00: 书稿整合")

    # 立即执行一次（测试用）
    if sys.stdin.isatty():
        choice = input("是否立即执行一次？(y/n/r=创作者雷达): ").lower()
        if choice == 'y':
            daily_collection_task()
        elif choice == 'r':
            daily_creator_radar_task()

    # 持续运行
    logger.info("\n⏰ 调度器运行中，等待定时任务...")
    logger.info("按 Ctrl+C 停止\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    except KeyboardInterrupt:
        logger.info("\n🛑 调度器已停止")


if __name__ == '__main__':
    run_scheduler()
