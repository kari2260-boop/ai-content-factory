"""
定时任务调度器
每天早上 7:00 自动运行选题采集
"""
import schedule
import time
from datetime import datetime

from modules.collector.main import TopicCollector
from modules.utils import setup_logger

logger = setup_logger('scheduler', 'scheduler.log')


def daily_collection_task():
    """每日选题采集任务"""
    logger.info("=" * 60)
    logger.info(f"开始执行每日选题采集任务 - {datetime.now()}")
    logger.info("=" * 60)

    try:
        collector = TopicCollector()
        topics = collector.run()

        logger.info(f"✅ 每日选题采集完成，共 {len(topics)} 个选题")

        # 统计高分选题
        high_score = [t for t in topics if t['total_score'] >= 25]
        logger.info(f"📊 高分选题（>=25分）: {len(high_score)} 个")

        # 打印前3个推荐选题
        logger.info("\n推荐选题（前3个）:")
        for i, topic in enumerate(high_score[:3], 1):
            logger.info(f"{i}. {topic['title']} (总分: {topic['total_score']})")

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


def run_scheduler():
    """运行调度器"""
    logger.info("🚀 定时任务调度器启动")

    # 每天早上 7:00 执行选题采集
    schedule.every().day.at("07:00").do(daily_collection_task)

    # 每周日早上 8:00 执行书稿整合
    schedule.every().sunday.at("08:00").do(weekly_book_integration_task)

    logger.info("📅 已设置定时任务:")
    logger.info("  - 每日 07:00: 选题采集")
    logger.info("  - 每周日 08:00: 书稿整合")

    # 立即执行一次（测试用）
    if input("是否立即执行一次选题采集？(y/n): ").lower() == 'y':
        daily_collection_task()

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
