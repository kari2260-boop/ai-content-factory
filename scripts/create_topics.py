#!/usr/bin/env python3
"""
手动创建选题工具
"""
import json
from datetime import datetime
from pathlib import Path

def main():
    print("=" * 60)
    print("📝 手动创建选题")
    print("=" * 60)
    print()
    print("请粘贴今日热点标题（每行一个，输入空行结束）：")
    print()

    titles = []
    while True:
        line = input().strip()
        if not line:
            break
        titles.append(line)

    if not titles:
        print("❌ 未输入任何标题")
        return

    print(f"\n收到 {len(titles)} 个标题，正在生成选题...")

    topics = []
    for i, title in enumerate(titles, 1):
        topic = {
            "title": title,
            "excerpt": f"{title}的相关讨论",
            "url": f"https://example.com/topic{i}",
            "source": "手动输入",
            "heat_score": "高",
            "collected_at": datetime.now().isoformat(),
            "relevance_score": 8,
            "timeliness_score": 9,
            "engagement_score": 8,
            "uniqueness_score": 7,
            "total_score": 32,
            "ai_reason": "手动采集的热点话题",
            "suggested_angles": ["深度分析", "实用建议", "案例分享"]
        }
        topics.append(topic)

    # 保存
    data_dir = Path.home() / 'ai-content-factory' / 'data' / 'topics'
    data_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')

    result = {
        'date': date_str,
        'total_count': len(topics),
        'high_score_count': len(topics),
        'topics': topics
    }

    # 保存到文件
    with open(data_dir / f'topics_{date_str}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(data_dir / 'latest.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已生成 {len(topics)} 个选题")
    print(f"保存到: {data_dir / 'latest.json'}")
    print("\n刷新 Streamlit 页面即可看到新选题！")

if __name__ == '__main__':
    main()
