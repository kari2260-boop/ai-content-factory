#!/usr/bin/env python3
"""
批量发布历史草稿到 Notion
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, '/Users/k/ai-content-factory')

from modules.publisher.notion_client import NotionClient
from modules.utils import setup_logger

logger = setup_logger('batch_publish', 'publisher.log')

# 格式映射
FORMAT_MAP = {
    'video': '视频号',
    'article': '公众号',
    'moments': '朋友圈',
    'xiaohongshu': '小红书',
    'book': '书稿'
}


def publish_draft_to_notion(draft_file: Path, notion_client: NotionClient):
    """发布单个草稿到 Notion"""
    try:
        # 读取草稿
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft = json.load(f)

        topic_title = draft.get('topic', {}).get('title', '未知标题')
        contents = draft.get('contents', {})

        print(f"\n{'='*60}")
        print(f"发布草稿: {topic_title}")
        print(f"{'='*60}")

        published_count = 0

        # 发布每种格式
        for format_key, content_data in contents.items():
            format_name = FORMAT_MAP.get(format_key, format_key)

            try:
                print(f"\n发布 {format_name}...")

                # 提取实际内容（处理字典格式）
                if isinstance(content_data, dict):
                    content = content_data.get('content', '')
                else:
                    content = content_data

                if not content:
                    print(f"⚠️ {format_name} 内容为空，跳过")
                    continue

                # 创建页面标题
                page_title = f"{topic_title} - {format_name}"

                # 发布到 Notion
                page_id = notion_client.create_page(
                    title=page_title,
                    format_type=format_name,
                    content=content,
                    metadata={
                        'topic': topic_title,
                        'format': format_name,
                        'draft_file': draft_file.name
                    }
                )

                print(f"✅ {format_name} 发布成功: {page_id}")
                published_count += 1

            except Exception as e:
                print(f"❌ {format_name} 发布失败: {str(e)}")

        print(f"\n草稿发布完成: {published_count}/5 个格式成功")
        return published_count

    except Exception as e:
        print(f"❌ 草稿处理失败: {str(e)}")
        return 0


def main():
    """主函数"""
    print("="*60)
    print("批量发布历史草稿到 Notion")
    print("="*60)

    # 初始化 Notion 客户端
    try:
        notion_client = NotionClient()
        print("✅ Notion 客户端初始化成功\n")
    except Exception as e:
        print(f"❌ Notion 客户端初始化失败: {str(e)}")
        return

    # 查找所有草稿
    drafts_dir = Path('/Users/k/ai-content-factory/data/drafts')
    draft_files = sorted(drafts_dir.glob('draft_*.json'))

    if not draft_files:
        print("未找到任何草稿")
        return

    print(f"找到 {len(draft_files)} 个草稿\n")

    # 发布每个草稿
    total_published = 0
    for i, draft_file in enumerate(draft_files, 1):
        print(f"\n[{i}/{len(draft_files)}] 处理: {draft_file.name}")
        count = publish_draft_to_notion(draft_file, notion_client)
        total_published += count

    # 总结
    print("\n" + "="*60)
    print("批量发布完成！")
    print("="*60)
    print(f"总草稿数: {len(draft_files)}")
    print(f"成功发布: {total_published} 个页面")
    print(f"预期页面: {len(draft_files) * 5}")
    print("="*60)


if __name__ == '__main__':
    main()
