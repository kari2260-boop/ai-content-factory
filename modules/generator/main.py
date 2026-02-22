"""
内容生成器主入口
负责协调 Claude、OpenClaw，生成5种格式的内容
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from modules.generator.claude_client import ClaudeClient
from modules.generator.gemini_client import GeminiClient
from modules.generator.openclaw_bridge import OpenClawBridge
from modules.generator.templates import (
    get_video_script_prompt,
    get_wechat_article_prompt,
    get_moments_prompt,
    get_xiaohongshu_prompt,
    get_book_material_prompt,
    get_chapter_classification_prompt
)
from modules.utils import setup_logger, save_json, get_timestamp, DATA_DIR, load_json
from modules.config import BOOK_STRUCTURE_PATH

logger = setup_logger('generator_main', 'generator.log')


class ContentGenerator:
    """内容生成器"""

    def __init__(self):
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()
        self.openclaw = OpenClawBridge()
        self.drafts_dir = DATA_DIR / 'drafts'
        self.drafts_dir.mkdir(exist_ok=True)

        # 加载书稿结构
        self.book_structure = load_json(BOOK_STRUCTURE_PATH)

    def generate_all_formats(self, topic: Dict, user_opinion: str, use_openclaw: bool = False, selected_formats: List[str] = None) -> Dict:
        """
        生成所有5种格式的内容

        Args:
            topic: 选题信息
            user_opinion: 用户观点
            use_openclaw: 是否优先使用 OpenClaw（默认True）
        """
        logger.info("=" * 50)
        logger.info(f"开始生成内容: {topic['title'][:30]}...")
        logger.info("=" * 50)

        # 优先使用 OpenClaw 生成（如果可用）
        if use_openclaw and self.openclaw.available:
            logger.info("🦞 使用 OpenClaw 生成所有格式内容")
            try:
                results = self.openclaw.generate_all_formats(topic, user_opinion)

                # 保存草稿
                self._save_draft(results)

                logger.info("=" * 50)
                logger.info("✅ OpenClaw 生成完成")
                logger.info("=" * 50)

                return results

            except Exception as e:
                logger.error(f"❌ OpenClaw 生成失败: {str(e)}")
                logger.info("⚠️ 降级使用 Claude 生成")

        # 降级使用 Claude 生成
        logger.info("🤖 使用 Claude 生成内容")

        # 获取 K博士的风格指南（从 OpenClaw workspace）
        logger.info("步骤 1/6: 读取 K博士风格指南")
        context = ""
        if self.openclaw.available:
            try:
                profile = self.openclaw.get_kari_profile()
                # 简化的上下文，只包含核心方法论
                context = f"""
## K博士的核心方法论
- 人生杠杆 = 四大基石 × 五大杠杆
- 从弱变强 × 关键决策 = 更理想的自我
- 风格：温暖有温度、专业但易懂、实践导向
"""
            except:
                pass

        results = {
            'topic': topic,
            'user_opinion': user_opinion,
            'context_used': bool(context),
            'generated_at': datetime.now().isoformat(),
            'provider': 'Claude',
            'contents': {}
        }

        # 生成5种格式
        all_formats = [
            ('video', '视频号文案', get_video_script_prompt, 1500),
            ('article', '公众号文章', get_wechat_article_prompt, 2500),
            ('moments', '朋友圈', get_moments_prompt, 500),
            ('xiaohongshu', '小红书', get_xiaohongshu_prompt, 800),
            ('book', '书稿素材', get_book_material_prompt, 1200)
        ]

        formats = [f for f in all_formats if selected_formats is None or f[0] in selected_formats]

        for i, (format_key, format_name, prompt_func, max_tokens) in enumerate(formats, 2):
            logger.info(f"步骤 {i}/6: 生成{format_name}")

            try:
                prompt = prompt_func(topic, user_opinion, context)
                content = self.claude.generate(prompt, max_tokens=max_tokens)

                results['contents'][format_key] = {
                    'format': format_name,
                    'content': content,
                    'word_count': len(content),
                    'generated_at': datetime.now().isoformat()
                }

                logger.info(f"{format_name}生成成功，字数: {len(content)}")

            except Exception as e:
                logger.error(f"{format_name}生成失败: {str(e)}")
                results['contents'][format_key] = {
                    'format': format_name,
                    'content': f"生成失败: {str(e)}",
                    'error': True
                }

        # 为书稿素材分类章节
        if 'book' in results['contents'] and not results['contents']['book'].get('error'):
            logger.info("步骤 7/6: 书稿章节分类")
            chapter_id = self._classify_chapter(results['contents']['book']['content'])
            results['contents']['book']['chapter_id'] = chapter_id
            logger.info(f"书稿归类到: {chapter_id}")

        # 保存草稿
        self._save_draft(results)

        logger.info("=" * 50)
        logger.info("内容生成完成！")
        logger.info("=" * 50)

        return results

    def _classify_chapter(self, content: str) -> str:
        """使用 Claude 对书稿素材进行章节分类"""
        if not self.book_structure:
            return 'ch01'  # 默认第一章

        try:
            prompt = get_chapter_classification_prompt(content, self.book_structure)
            chapter_id = self.claude.generate(prompt, max_tokens=50).strip()

            # 验证章节ID是否有效
            valid_chapters = [ch['id'] for ch in self.book_structure['chapters']]
            if chapter_id not in valid_chapters:
                logger.warning(f"无效的章节ID: {chapter_id}，使用默认章节")
                return 'ch01'

            return chapter_id

        except Exception as e:
            logger.error(f"章节分类失败: {str(e)}")
            return 'ch01'

    def _save_draft(self, results: Dict):
        """保存草稿"""
        timestamp = get_timestamp()
        topic_title = results['topic']['title'][:30].replace('/', '_')
        filename = f"draft_{timestamp}_{topic_title}.json"
        filepath = self.drafts_dir / filename

        save_json(results, filepath)
        logger.info(f"草稿已保存到: {filepath}")

    def get_latest_drafts(self, limit: int = 10) -> List[Dict]:
        """获取最新的草稿列表"""
        draft_files = sorted(self.drafts_dir.glob('draft_*.json'), reverse=True)[:limit]

        drafts = []
        for filepath in draft_files:
            try:
                draft = load_json(filepath)
                drafts.append(draft)
            except Exception as e:
                logger.error(f"读取草稿失败 {filepath}: {str(e)}")

        return drafts


def main():
    """主函数 - 测试用"""
    # 测试选题
    test_topic = {
        'title': 'AI时代，孩子该学什么才不会被淘汰？',
        'excerpt': '人工智能快速发展，家长焦虑孩子未来就业...',
        'source': 'test',
        'total_score': 32,
        'ai_reason': '话题热度高，与AI教育强相关',
        'suggested_angles': ['培养创造力', '批判性思维']
    }

    test_opinion = "我认为AI时代最重要的是培养孩子的创造力和批判性思维，而不是死记硬背。"

    generator = ContentGenerator()
    results = generator.generate_all_formats(test_topic, test_opinion)

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("📝 内容生成结果")
    print("=" * 60)

    for format_key, content_data in results['contents'].items():
        if content_data.get('error'):
            print(f"\n❌ {content_data['format']}: 生成失败")
        else:
            print(f"\n✅ {content_data['format']}: {content_data['word_count']} 字")
            print(f"   预览: {content_data['content'][:100]}...")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
