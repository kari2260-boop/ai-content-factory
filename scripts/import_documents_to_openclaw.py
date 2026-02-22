#!/usr/bin/env python3
"""
将移动硬盘上的所有文档导入到 OpenClaw 知识库
支持 PDF, DOCX, DOC, TXT, MD 等格式
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, '/Users/k/ai-content-factory')
from modules.utils import setup_logger

logger = setup_logger('document_importer', 'collector.log')


class DocumentImporter:
    """文档导入器"""

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']
        self.imported_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def find_documents(self) -> List[Path]:
        """查找所有支持的文档"""
        logger.info(f"开始扫描目录: {self.source_dir}")
        documents = []

        for ext in self.supported_extensions:
            files = list(self.source_dir.rglob(f'*{ext}'))
            documents.extend(files)
            logger.info(f"找到 {len(files)} 个 {ext} 文件")

        logger.info(f"总共找到 {len(documents)} 个文档")
        return documents

    def import_to_openclaw(self, file_path: Path) -> bool:
        """导入单个文档到 OpenClaw"""
        try:
            # 使用 openclaw ingest 命令导入文档
            cmd = ['openclaw', 'ingest', str(file_path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            if result.returncode == 0:
                logger.info(f"✅ 导入成功: {file_path.name}")
                return True
            else:
                logger.warning(f"⚠️ 导入失败: {file_path.name} - {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"❌ 导入超时: {file_path.name}")
            return False
        except Exception as e:
            logger.error(f"❌ 导入异常: {file_path.name} - {str(e)}")
            return False

    def run(self, batch_size: int = 100, delay: float = 0.5):
        """运行导入流程"""
        logger.info("=" * 60)
        logger.info("开始文档导入流程")
        logger.info("=" * 60)

        # 查找所有文档
        documents = self.find_documents()

        if not documents:
            logger.warning("未找到任何文档")
            return

        total = len(documents)
        logger.info(f"准备导入 {total} 个文档")
        logger.info(f"批次大小: {batch_size}, 延迟: {delay}秒")

        # 分批导入
        for i, doc_path in enumerate(documents, 1):
            # 跳过系统文件和隐藏文件
            if doc_path.name.startswith('.') or '$RECYCLE.BIN' in str(doc_path):
                self.skipped_count += 1
                continue

            logger.info(f"\n[{i}/{total}] 正在导入: {doc_path.name}")

            success = self.import_to_openclaw(doc_path)

            if success:
                self.imported_count += 1
            else:
                self.failed_count += 1

            # 每批次后暂停
            if i % batch_size == 0:
                logger.info(f"\n已完成 {i}/{total} 个文档，暂停 5 秒...")
                time.sleep(5)
            else:
                time.sleep(delay)

            # 每 10 个文档输出一次进度
            if i % 10 == 0:
                logger.info(f"进度: {i}/{total} ({i*100//total}%)")

        # 输出统计
        logger.info("\n" + "=" * 60)
        logger.info("导入完成！")
        logger.info("=" * 60)
        logger.info(f"总文档数: {total}")
        logger.info(f"成功导入: {self.imported_count}")
        logger.info(f"导入失败: {self.failed_count}")
        logger.info(f"跳过文件: {self.skipped_count}")
        logger.info("=" * 60)


def main():
    """主函数"""
    source_dir = '/Volumes/ORICO'

    # 检查目录是否存在
    if not os.path.exists(source_dir):
        print(f"❌ 错误: 目录不存在 {source_dir}")
        sys.exit(1)

    # 检查 OpenClaw 是否可用
    try:
        result = subprocess.run(
            ['openclaw', 'gateway', 'health'],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            print("❌ 错误: OpenClaw 网关未运行")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: 无法连接 OpenClaw - {e}")
        sys.exit(1)

    print("✅ OpenClaw 网关运行正常")
    print(f"📂 源目录: {source_dir}")
    print("\n开始导入文档...")

    # 创建导入器并运行
    importer = DocumentImporter(source_dir)
    importer.run(batch_size=50, delay=0.3)


if __name__ == '__main__':
    main()
