#!/usr/bin/env python3
"""
测试完整流程：采集 → 打分
"""
from modules.collector.sources import TopHubSource
from modules.collector.scorer import TopicScorer
import json
from datetime import datetime

def test_full_pipeline():
    """测试完整的采集和打分流程"""
    print("="*70)
    print("测试完整流程：TopHub采集 → 5维度打分")
    print("="*70)

    # 步骤1: 采集选题
    print("\n【步骤1】从今日热榜采集选题...")
    tophub = TopHubSource()
    topics = tophub.fetch()
    print(f"✅ 采集完成，获得 {len(topics)} 个相关选题")

    # 步骤2: 打分（只打前3个，节省API调用）
    print("\n【步骤2】使用5维度打分器评分（测试前3个）...")
    scorer = TopicScorer()

    scored_topics = []
    for i, topic in enumerate(topics[:3], 1):
        print(f"\n  [{i}/3] 打分中: {topic['title'][:40]}...")
        try:
            score_data = scorer._score_single_topic(topic)
            topic.update(score_data)
            scored_topics.append(topic)
            print(f"      总分: {score_data['total_score']}/50")
        except Exception as e:
            print(f"      ❌ 失败: {str(e)}")

    # 步骤3: 排序
    print("\n【步骤3】按总分排序...")
    scored_topics.sort(key=lambda x: x['total_score'], reverse=True)

    # 步骤4: 展示结果
    print("\n" + "="*70)
    print("📊 打分结果（按总分排序）")
    print("="*70)

    for i, topic in enumerate(scored_topics, 1):
        print(f"\n【第{i}名】总分: {topic['total_score']}/50")
        print(f"标题: {topic['title']}")
        print(f"平台: {topic['platform']}")
        print(f"\n评分明细:")
        print(f"  相关度: {topic['relevance_score']}/10")
        print(f"  时效性: {topic['timeliness_score']}/10")
        print(f"  互动潜力: {topic['engagement_score']}/10")
        print(f"  独特性: {topic['uniqueness_score']}/10")
        print(f"  情绪共鸣: {topic['emotion_score']}/10")
        print(f"\nAI评价: {topic['ai_reason']}")
        print(f"用户痛点: {topic['audience_pain_point']}")
        print(f"建议角度:")
        for angle in topic['suggested_angles']:
            print(f"  • {angle}")
        print("-"*70)

    # 步骤5: 保存结果
    output_file = f"data/topics/scored_topics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scored_topics, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {output_file}")
    except Exception as e:
        print(f"\n⚠️  保存失败: {str(e)}")

    print("\n" + "="*70)
    print("✨ 测试完成！")
    print("="*70)

    return scored_topics

if __name__ == '__main__':
    test_full_pipeline()
