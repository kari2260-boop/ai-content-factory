#!/usr/bin/env python3
"""
测试今日热榜采集器
"""
from modules.collector.sources import TopHubSource
import json

def test_tophub():
    """测试 TopHub 采集器"""
    print("="*70)
    print("测试今日热榜采集器")
    print("="*70)

    # 创建采集器实例
    tophub = TopHubSource()

    # 执行采集
    topics = tophub.fetch()

    print(f"\n✅ 采集成功！共获得 {len(topics)} 个相关选题\n")

    # 统计平台分布
    platforms = {}
    for topic in topics:
        platform = topic['platform']
        platforms[platform] = platforms.get(platform, 0) + 1

    print("📊 平台分布:")
    for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform}: {count}条")

    print("\n" + "="*70)
    print("📝 前10条选题预览:\n")

    for i, topic in enumerate(topics[:10], 1):
        print(f"{i}. {topic['title']}")
        print(f"   平台: {topic['platform']}")
        print(f"   来源: {topic['source']}")
        url_display = topic['url'][:65] + '...' if len(topic['url']) > 65 else topic['url']
        print(f"   链接: {url_display}")
        print()

    # 保存到文件
    output_file = 'data/topics/test_tophub_output.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        print(f"💾 完整数据已保存到: {output_file}")
    except Exception as e:
        print(f"⚠️  保存文件失败: {str(e)}")

    print("\n" + "="*70)
    print("✨ 测试完成！")
    print("="*70)

if __name__ == '__main__':
    test_tophub()
