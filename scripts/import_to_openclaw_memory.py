#!/usr/bin/env python3
"""
将移动硬盘上的文档复制到 OpenClaw memory 目录并索引
"""
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List

# OpenClaw memory 目录
OPENCLAW_MEMORY_DIR = Path.home() / '.openclaw' / 'workspace' / 'memory'
SOURCE_DIR = Path('/Volumes/ORICO')

# 支持的文件类型
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.md']


def find_documents(source_dir: Path) -> List[Path]:
    """查找所有支持的文档"""
    print(f"📂 扫描目录: {source_dir}")
    documents = []

    for ext in SUPPORTED_EXTENSIONS:
        files = list(source_dir.rglob(f'*{ext}'))
        # 过滤掉系统文件
        files = [f for f in files if not any(x in str(f) for x in ['$RECYCLE.BIN', 'System Volume Information', '.Trash'])]
        documents.extend(files)
        print(f"   找到 {len(files)} 个 {ext} 文件")

    print(f"\n✅ 总共找到 {len(documents)} 个文档\n")
    return documents


def copy_documents(documents: List[Path], dest_dir: Path, max_files: int = None):
    """复制文档到 OpenClaw memory 目录"""
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"📋 开始复制文档到: {dest_dir}")

    if max_files:
        documents = documents[:max_files]
        print(f"   限制复制数量: {max_files} 个文件")

    copied = 0
    failed = 0
    skipped = 0

    for i, doc_path in enumerate(documents, 1):
        try:
            # 创建相对路径结构
            rel_path = doc_path.relative_to(SOURCE_DIR)
            dest_path = dest_dir / rel_path

            # 如果文件已存在且大小相同，跳过
            if dest_path.exists() and dest_path.stat().st_size == doc_path.stat().st_size:
                skipped += 1
                if i % 100 == 0:
                    print(f"   进度: {i}/{len(documents)} ({i*100//len(documents)}%) - 已跳过: {skipped}")
                continue

            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(doc_path, dest_path)
            copied += 1

            if i % 100 == 0:
                print(f"   进度: {i}/{len(documents)} ({i*100//len(documents)}%) - 已复制: {copied}")

        except Exception as e:
            failed += 1
            if failed <= 10:  # 只显示前10个错误
                print(f"   ⚠️ 复制失败: {doc_path.name} - {str(e)}")

    print(f"\n✅ 复制完成!")
    print(f"   成功: {copied}")
    print(f"   跳过: {skipped}")
    print(f"   失败: {failed}")
    print(f"   总计: {copied + skipped + failed}\n")

    return copied


def index_memory():
    """索引 OpenClaw memory"""
    print("🔍 开始索引 OpenClaw memory...")

    try:
        result = subprocess.run(
            ['openclaw', 'memory', 'index', '--force', '--verbose'],
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ 索引完成!")
        else:
            print(f"\n⚠️ 索引可能有问题，返回码: {result.returncode}")

        # 显示索引状态
        print("\n📊 索引状态:")
        status_result = subprocess.run(
            ['openclaw', 'memory', 'status'],
            capture_output=True,
            text=True
        )
        print(status_result.stdout)

    except subprocess.TimeoutExpired:
        print("❌ 索引超时（10分钟）")
    except Exception as e:
        print(f"❌ 索引失败: {e}")


def main():
    """主函数"""
    import sys

    print("=" * 70)
    print("OpenClaw 知识库导入工具")
    print("=" * 70)
    print()

    # 检查源目录
    if not SOURCE_DIR.exists():
        print(f"❌ 错误: 源目录不存在 {SOURCE_DIR}")
        return

    # 检查 OpenClaw
    try:
        result = subprocess.run(
            ['openclaw', 'gateway', 'health'],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            print("❌ 错误: OpenClaw 网关未运行")
            return
    except Exception as e:
        print(f"❌ 错误: 无法连接 OpenClaw - {e}")
        return

    print("✅ OpenClaw 网关运行正常\n")

    # 查找文档
    documents = find_documents(SOURCE_DIR)

    if not documents:
        print("❌ 未找到任何文档")
        return

    # 从命令行参数获取选择
    max_files = None
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # 询问用户
        print(f"准备将 {len(documents)} 个文档导入到 OpenClaw 知识库")
        print(f"目标目录: {OPENCLAW_MEMORY_DIR}")
        print()
        print("选项:")
        print("  1. 导入所有文档 (可能需要很长时间)")
        print("  2. 导入前 100 个文档 (测试)")
        print("  3. 导入前 500 个文档")
        print("  4. 导入前 1000 个文档")
        print("  5. 取消")
        print()

        try:
            choice = input("请选择 (1-5): ").strip()
        except EOFError:
            print("\n使用方法: python3 import_to_openclaw_memory.py [1-5]")
            return

    if choice == '2':
        max_files = 100
    elif choice == '3':
        max_files = 500
    elif choice == '4':
        max_files = 1000
    elif choice == '5':
        print("已取消")
        return
    elif choice != '1':
        print("无效选择")
        return

    print()

    # 复制文档
    copied = copy_documents(documents, OPENCLAW_MEMORY_DIR, max_files)

    if copied == 0:
        print("没有新文档需要索引")
        return

    # 索引
    index_memory()

    print()
    print("=" * 70)
    print("✅ 完成！你的文档已导入到 OpenClaw 知识库")
    print("=" * 70)
    print()
    print("现在生成内容时，OpenClaw 会参考你的历史文档和写作风格")


if __name__ == '__main__':
    main()
