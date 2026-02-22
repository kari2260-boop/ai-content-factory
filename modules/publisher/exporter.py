"""
导出工具
将生成的内容导出为各种格式
"""
import json
from pathlib import Path
from datetime import datetime

from modules.utils import setup_logger, DATA_DIR

logger = setup_logger('exporter', 'publisher.log')


class ContentExporter:
    """内容导出工具"""

    def __init__(self):
        self.export_dir = DATA_DIR / 'published'
        self.export_dir.mkdir(exist_ok=True)

    def export_to_txt(self, content: str, filename: str) -> Path:
        """导出为 TXT 文件"""
        filepath = self.export_dir / f"{filename}.txt"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"导出 TXT: {filepath}")
        return filepath

    def export_to_markdown(self, content: str, filename: str) -> Path:
        """导出为 Markdown 文件"""
        filepath = self.export_dir / f"{filename}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"导出 Markdown: {filepath}")
        return filepath

    def export_all_formats(self, draft: dict) -> dict:
        """导出所有格式"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        topic_title = draft['topic']['title'][:20].replace('/', '_').replace(' ', '_')

        exported_files = {}

        for format_key, content_data in draft['contents'].items():
            if content_data.get('error'):
                continue

            filename = f"{timestamp}_{topic_title}_{format_key}"

            # 导出为 TXT
            txt_path = self.export_to_txt(content_data['content'], filename)
            exported_files[format_key] = str(txt_path)

        logger.info(f"导出完成，共 {len(exported_files)} 个文件")
        return exported_files


if __name__ == '__main__':
    # 测试
    exporter = ContentExporter()
    test_content = "这是测试内容\n\n## 标题\n\n正文..."
    path = exporter.export_to_txt(test_content, "test")
    print(f"导出到: {path}")
