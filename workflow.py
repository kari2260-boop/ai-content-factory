"""
每日自动化工作流
早上8:00自动采集选题 → 8:30审核 → 8:35生成内容 → 8:40发布
"""
import schedule
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.collector.main import TopicCollector
from modules.generator.openclaw_bridge import OpenClawBridge
from modules.publisher.main import ContentPublisher
from modules.utils import setup_logger, DATA_DIR

logger = setup_logger('workflow', 'workflow.log')


class DailyWorkflow:
    """每日自动化工作流"""

    def __init__(self):
        self.collector = TopicCollector()
        self.openclaw = OpenClawBridge()
        self.publisher = ContentPublisher()

        # 工作流状态文件
        self.state_file = DATA_DIR / 'workflow_state.json'

    def step1_collect_topics(self):
        """Step 1: 早上8:00 - 自动采集选题"""
        logger.info("=" * 80)
        logger.info(f"🌅 Step 1: 开始采集今日选题 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        try:
            topics = self.collector.run()
            logger.info(f"✅ 采集完成！共获得 {len(topics)} 个选题")

            # 统计高分选题
            high_score = [t for t in topics if t.get('total_score', 0) >= 25]
            logger.info(f"📊 高分选题（>=25分）: {len(high_score)} 个")

            # 打印前5个推荐选题
            logger.info("\n📋 推荐选题（前5个）:")
            for i, topic in enumerate(high_score[:5], 1):
                logger.info(f"  {i}. {topic['title']}")
                logger.info(f"     总分: {topic.get('total_score', 0)}/40")
                logger.info(f"     建议角度: {', '.join(topic.get('suggested_angles', []))}")
                logger.info("")

            # 保存状态
            import json
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'step': 1,
                    'timestamp': datetime.now().isoformat(),
                    'topics_count': len(topics),
                    'high_score_count': len(high_score)
                }, f, ensure_ascii=False, indent=2)

            logger.info("💡 下一步：请在 Streamlit 界面选择 2-3 个选题并写下观点")
            logger.info("   或者运行: python workflow.py --step2")

            return True

        except Exception as e:
            logger.error(f"❌ 采集失败: {str(e)}")
            return False

    def step2_generate_content(self, topic_ids: list = None, user_opinion: str = None):
        """
        Step 2: 早上8:35 - 生成内容

        Args:
            topic_ids: 选中的选题ID列表（如果为None，则从最新选题中自动选择）
            user_opinion: 用户观点（如果为None，则使用默认观点）
        """
        logger.info("=" * 80)
        logger.info(f"✍️ Step 2: 开始生成内容 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        if not self.openclaw.available:
            logger.error("❌ OpenClaw 不可用，无法生成内容")
            logger.info("💡 请先启动 OpenClaw: openclaw gateway")
            return False

        try:
            # 获取最新选题
            topics = self.collector.get_latest_topics()

            if not topics:
                logger.error("❌ 没有可用的选题")
                return False

            # 如果没有指定选题，自动选择高分选题
            if not topic_ids:
                high_score = [t for t in topics if t.get('total_score', 0) >= 30]
                if not high_score:
                    high_score = sorted(topics, key=lambda x: x.get('total_score', 0), reverse=True)

                selected_topics = high_score[:2]  # 自动选择前2个
                logger.info(f"📌 自动选择了 {len(selected_topics)} 个高分选题")
            else:
                selected_topics = [t for t in topics if t.get('id') in topic_ids]
                logger.info(f"📌 使用指定的 {len(selected_topics)} 个选题")

            # 为每个选题生成内容
            all_results = []

            for i, topic in enumerate(selected_topics, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📝 正在处理选题 {i}/{len(selected_topics)}: {topic['title']}")
                logger.info(f"{'='*60}")

                # 使用用户观点或默认观点
                opinion = user_opinion or self._generate_default_opinion(topic)
                logger.info(f"💭 核心观点: {opinion}")

                # 使用 OpenClaw 生成所有格式
                results = self.openclaw.generate_all_formats(topic, opinion)
                all_results.append(results)

                # 保存草稿
                draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{topic['title'][:20]}"
                draft_file = DATA_DIR / 'drafts' / f"{draft_id}.json"

                import json
                with open(draft_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 草稿已保存: {draft_file.name}")

            # 更新状态
            import json
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'step': 2,
                    'timestamp': datetime.now().isoformat(),
                    'generated_count': len(all_results)
                }, f, ensure_ascii=False, indent=2)

            logger.info("\n" + "=" * 80)
            logger.info(f"✅ 内容生成完成！共生成 {len(all_results)} 个选题的内容")
            logger.info("=" * 80)
            logger.info("💡 下一步：请在 Streamlit 界面审核内容")
            logger.info("   或者运行: python workflow.py --step3")

            return True

        except Exception as e:
            logger.error(f"❌ 生成失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _generate_default_opinion(self, topic: Dict) -> str:
        """根据选题生成默认观点"""
        # 简单的默认观点生成逻辑
        angles = topic.get('suggested_angles', [])
        if angles:
            return f"我认为这个话题可以从{angles[0]}来分析，结合人生杠杆的方法论"
        else:
            return "我认为这个话题值得从人生杠杆和从弱变强的角度来分析"

    def step3_publish_content(self):
        """Step 3: 早上8:40 - 发布内容"""
        logger.info("=" * 80)
        logger.info(f"📤 Step 3: 开始发布内容 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        try:
            # 获取最新的草稿
            drafts_dir = DATA_DIR / 'drafts'
            draft_files = sorted(drafts_dir.glob('draft_*.json'), key=lambda x: x.stat().st_mtime, reverse=True)

            if not draft_files:
                logger.error("❌ 没有可发布的草稿")
                return False

            # 发布最新的草稿
            import json
            published_count = 0

            for draft_file in draft_files[:3]:  # 最多发布最新的3个
                logger.info(f"\n📄 正在发布: {draft_file.name}")

                with open(draft_file, 'r', encoding='utf-8') as f:
                    draft = json.load(f)

                # 发布到 Notion
                try:
                    results = self.publisher.publish_draft(draft)
                    logger.info(f"✅ 发布成功")
                    published_count += 1
                except Exception as e:
                    logger.error(f"❌ 发布失败: {str(e)}")

                # 导出文件
                try:
                    exported = self.publisher.export_files(draft)
                    logger.info(f"💾 已导出 {len(exported)} 个文件")
                except Exception as e:
                    logger.error(f"❌ 导出失败: {str(e)}")

            # 更新状态
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'step': 3,
                    'timestamp': datetime.now().isoformat(),
                    'published_count': published_count
                }, f, ensure_ascii=False, indent=2)

            logger.info("\n" + "=" * 80)
            logger.info(f"✅ 发布完成！共发布 {published_count} 个内容")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"❌ 发布失败: {str(e)}")
            return False

    def run_full_workflow(self):
        """运行完整工作流（测试用）"""
        logger.info("🚀 开始运行完整工作流")

        # Step 1: 采集选题
        if not self.step1_collect_topics():
            logger.error("❌ Step 1 失败，终止工作流")
            return

        logger.info("\n⏸️ 暂停30秒，模拟用户审核选题...")
        time.sleep(30)

        # Step 2: 生成内容
        if not self.step2_generate_content():
            logger.error("❌ Step 2 失败，终止工作流")
            return

        logger.info("\n⏸️ 暂停30秒，模拟用户审核内容...")
        time.sleep(30)

        # Step 3: 发布内容
        if not self.step3_publish_content():
            logger.error("❌ Step 3 失败，终止工作流")
            return

        logger.info("\n🎉 完整工作流执行完成！")


def schedule_daily_workflow():
    """设置每日定时任务"""
    workflow = DailyWorkflow()

    logger.info("🚀 每日自动化工作流启动")
    logger.info("=" * 80)

    # 每天早上8:00执行Step 1
    schedule.every().day.at("08:00").do(workflow.step1_collect_topics)

    # 每天早上8:35执行Step 2（需要用户在8:30前选择选题）
    schedule.every().day.at("08:35").do(workflow.step2_generate_content)

    # 每天早上8:40执行Step 3（需要用户在8:40前审核内容）
    schedule.every().day.at("08:40").do(workflow.step3_publish_content)

    logger.info("📅 已设置每日定时任务:")
    logger.info("  - 08:00: 自动采集选题")
    logger.info("  - 08:35: 自动生成内容")
    logger.info("  - 08:40: 自动发布内容")
    logger.info("=" * 80)

    # 询问是否立即测试
    test = input("\n是否立即测试完整工作流？(y/n): ").lower()
    if test == 'y':
        workflow.run_full_workflow()

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
    import sys
    from typing import Dict

    if len(sys.argv) > 1:
        workflow = DailyWorkflow()

        if sys.argv[1] == '--step1':
            workflow.step1_collect_topics()

        elif sys.argv[1] == '--step2':
            workflow.step2_generate_content()

        elif sys.argv[1] == '--step3':
            workflow.step3_publish_content()

        elif sys.argv[1] == '--test':
            workflow.run_full_workflow()

        elif sys.argv[1] == '--schedule':
            schedule_daily_workflow()

        else:
            print("用法:")
            print("  python workflow.py --step1      # 执行Step 1: 采集选题")
            print("  python workflow.py --step2      # 执行Step 2: 生成内容")
            print("  python workflow.py --step3      # 执行Step 3: 发布内容")
            print("  python workflow.py --test       # 测试完整工作流")
            print("  python workflow.py --schedule   # 启动定时调度器")
    else:
        schedule_daily_workflow()
