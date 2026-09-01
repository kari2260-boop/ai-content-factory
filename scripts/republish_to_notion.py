#!/usr/bin/env python3
"""
重新发布有完整内容的草稿到 Notion
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, '/Users/k/ai-content-factory')

from modules.publisher.notion_client import NotionClient

# 格式映射
FORMAT_MAP = {
    'video': '视频号',
    'article': '公众号',
    'moments': '朋友圈',
    'xiaohongshu': '小红书',
    'book': '书稿'
}

def republish_draft(draft_file: Path, notion_client: NotionClient):
    """重新发布单个草稿"""
    try:
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft = json.load(f)

        topic_title = draft.get('topic', {}).get('title', '未知标题')
        contents = draft.get('contents', {})

        print(f"\n{'='*60}")
        print(f"重新发布: {topic_title}")
        print(f"{'='*60}")

        published_count = 0

        for format_key, content_data in contents.items():
            format_name = FORMAT_MAP.get(format_key, format_key)

            try:
                # 提取实际内容
                if isinstance(content_data, dict):
                    content = content_data.get('content', '')
                else:
                    content = content_data

                # 跳过空内容
                if not content or content == '生成内容为空' or len(content) < 50:
                    print(f"⏭️  {format_name} - 内容为空，跳过")
                    continue

                print(f"\n发布 {format_name} ({len(content)} 字符)...")

                page_title = f"【重发】{topic_title} - {format_name}"

                page_id = notion_client.create_page(
                    title=page_title,
                    format_type=format_name,
                    content=content
                )

                # 验证内容
                blocks = notion_client.client.blocks.children.list(block_id=page_id, page_size=5)
                block_count = len(blocks['results'])

                print(f"✅ {format_name} 发布成功 ({block_count} blocks)")
                published_count += 1

            except Exception as e:
                print(f"❌ {format_name} 发布失败: {str(e)}")

        print(f"\n完成: {published_count} 个格式成功")
        return published_count

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        return 0


def main():
    print("="*60)
    print("重新发布完整内容的草稿")
    print("="*60)

    notion_client = NotionClient()
    print("✅ Notion 客户端初始化成功\n")

    # 只发布前两个草稿（有完整内容的）
    draft_files = [
        Path('/Users/k/ai-content-factory/data/drafts/draft_20260219_143810_AI时代，孩子该学什么才不会被淘汰？.json'),
        Path('/Users/k/ai-content-factory/data/drafts/draft_20260219_144616_留学申请季，如何避开这些常见误区？.json')
    ]

    total_published = 0
    for i, draft_file in enumerate(draft_files, 1):
        print(f"\n[{i}/{len(draft_files)}]")
        count = republish_draft(draft_file, notion_client)
        total_published += count

    print("\n" + "="*60)
    print(f"重新发布完成！成功: {total_published} 个页面")
    print("="*60)


if __name__ == '__main__':
    main()
