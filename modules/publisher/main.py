"""
发布模块主入口
负责将内容发布到 Notion 和导出文件
"""
from typing import Dict, List
from datetime import datetime

from modules.publisher.notion_client import NotionClient
from modules.publisher.formatter import WechatFormatter
from modules.publisher.exporter import ContentExporter
from modules.utils import setup_logger, save_json, DATA_DIR

logger = setup_logger('publisher_main', 'publisher.log')


class ContentPublisher:
    """内容发布器"""

    def __init__(self):
        try:
            self.notion = NotionClient()
            self.notion_available = True
        except ValueError as e:
            logger.warning(f"Notion 客户端初始化失败: {str(e)}")
            self.notion_available = False

        self.formatter = WechatFormatter()
        self.exporter = ContentExporter()

    def publish_to_notion(self, draft: Dict) -> Dict:
        """发布到 Notion"""
        if not self.notion_available:
            logger.error("Notion 不可用，跳过发布")
            return {'success': False, 'error': 'Notion 未配置'}

        logger.info("=" * 50)
        logger.info("开始发布到 Notion")
        logger.info("=" * 50)

        results = {
            'published_at': datetime.now().isoformat(),
            'pages': {}
        }

        topic_title = draft['topic']['title']

        # 发布每种格式
        for format_key, content_data in draft['contents'].items():
            if content_data.get('error'):
                logger.warning(f"跳过错误内容: {format_key}")
                continue

            try:
                format_name = content_data['format']
                content = content_data['content']

                # 准备元数据
                metadata = {
                    '选题': topic_title,
                    '用户观点': draft['user_opinion'],
                    '字数': content_data['word_count'],
                    '生成时间': content_data['generated_at']
                }

                # 书稿素材添加章节信息
                if format_key == 'book' and 'chapter_id' in content_data:
                    metadata['章节'] = content_data['chapter_id']

                # 创建 Notion 页面
                page_id = self.notion.create_page(
                    title=f"{topic_title[:50]} - {format_name}",
                    format_type=format_name,
                    content=content,
                    metadata=metadata
                )

                results['pages'][format_key] = {
                    'page_id': page_id,
                    'format': format_name,
                    'success': True
                }

                logger.info(f"✅ {format_name} 发布成功")

            except Exception as e:
                logger.error(f"❌ {format_key} 发布失败: {str(e)}")
                results['pages'][format_key] = {
                    'success': False,
                    'error': str(e)
                }

        logger.info("=" * 50)
        logger.info("Notion 发布完成")
        logger.info("=" * 50)

        return results

    def export_files(self, draft: Dict) -> Dict:
        """导出文件"""
        logger.info("开始导出文件")
        exported = self.exporter.export_all_formats(draft)
        logger.info(f"导出完成，共 {len(exported)} 个文件")
        return exported

    def get_wechat_html(self, markdown_content: str) -> str:
        """获取微信公众号 HTML"""
        return self.formatter.markdown_to_wechat_html(markdown_content)

    def publish_draft(self, draft: Dict, export_files: bool = True) -> Dict:
        """发布草稿（完整流程）"""
        results = {
            'draft_id': draft.get('generated_at'),
            'topic': draft['topic']['title']
        }

        # 发布到 Notion
        if self.notion_available:
            notion_results = self.publish_to_notion(draft)
            results['notion'] = notion_results
        else:
            results['notion'] = {'success': False, 'error': 'Notion 未配置'}

        # 导出文件
        if export_files:
            exported = self.export_files(draft)
            results['exported_files'] = exported

        # 保存发布记录
        self._save_publish_record(results)

        return results

    def _save_publish_record(self, results: Dict):
        """保存发布记录"""
        record_file = DATA_DIR / 'published' / 'publish_records.json'

        # 读取现有记录
        if record_file.exists():
            import json
            with open(record_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        else:
            records = []

        # 添加新记录
        records.append(results)

        # 保存
        save_json(records, record_file)
        logger.info(f"发布记录已保存")


def main():
    """主函数 - 测试用"""
    # 模拟草稿数据
    test_draft = {
        'topic': {
            'title': '测试选题：AI时代的教育变革',
            'total_score': 30
        },
        'user_opinion': '我认为AI会改变教育方式',
        'generated_at': datetime.now().isoformat(),
        'contents': {
            'article': {
                'format': '公众号文章',
                'content': '# 测试文章\n\n这是测试内容...',
                'word_count': 100,
                'generated_at': datetime.now().isoformat()
            }
        }
    }

    publisher = ContentPublisher()

    if publisher.notion_available:
        results = publisher.publish_draft(test_draft)
        print(f"发布结果: {results}")
    else:
        print("Notion 未配置，跳过测试")


if __name__ == '__main__':
    main()
