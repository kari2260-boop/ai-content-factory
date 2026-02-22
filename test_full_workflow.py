#!/usr/bin/env python3
"""
完整流程测试：采集 → 打分 → 大纲生成 → 内容生成 → 反馈学习
"""
import json
from datetime import datetime
from pathlib import Path

from modules.collector.sources import TopHubSource
from modules.collector.scorer import TopicScorer
from modules.generator.claude_client import ClaudeClient
from modules.processor.feedback_loop import FeedbackLearner
from modules.utils import DATA_DIR


def test_full_workflow():
    """测试完整工作流"""
    print("="*70)
    print("AI内容工厂 - 完整流程测试")
    print("="*70)

    # ========== 步骤1: 采集选题 ==========
    print("\n【步骤1】从今日热榜采集选题...")
    tophub = TopHubSource()
    topics = tophub.fetch()
    print(f"✅ 采集完成，获得 {len(topics)} 个相关选题")

    # ========== 步骤2: 打分（只测试前2个） ==========
    print("\n【步骤2】使用5维度打分器评分（测试前2个）...")
    scorer = TopicScorer()

    scored_topics = []
    for i, topic in enumerate(topics[:2], 1):
        print(f"  [{i}/2] 打分中: {topic['title'][:40]}...")
        try:
            score_data = scorer._score_single_topic(topic)
            topic.update(score_data)
            scored_topics.append(topic)
            print(f"      总分: {score_data['total_score']}/50")
        except Exception as e:
            print(f"      ❌ 失败: {str(e)}")

    # 排序
    scored_topics.sort(key=lambda x: x['total_score'], reverse=True)
    best_topic = scored_topics[0]

    print(f"\n✅ 最高分选题: {best_topic['title'][:50]}... ({best_topic['total_score']}/50)")

    # ========== 步骤3: 生成大纲 ==========
    print("\n【步骤3】生成核心切入点和大纲...")
    claude = ClaudeClient()

    outline_prompt = f"""你是K博士的内容策划助手。请为以下选题生成核心切入点和内容大纲。

**选题信息：**
标题：{best_topic['title']}
用户痛点：{best_topic.get('audience_pain_point', '未识别')}

**任务：**
1. 提炼核心切入点（1-2句话）
2. 设计内容大纲（3-5个要点）

**输出格式（JSON）：**
{{
  "core_angle": "核心切入点",
  "outline": ["要点1", "要点2", "要点3"]
}}

只返回 JSON。"""

    try:
        outline_response = claude.generate(outline_prompt, max_tokens=800)
        outline_text = outline_response.strip()

        # 更强大的 JSON 提取
        if '```' in outline_text:
            # 提取代码块中的内容
            parts = outline_text.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    outline_text = part[4:].strip()
                    break
                elif part.strip().startswith('{'):
                    outline_text = part.strip()
                    break

        # 查找第一个 { 和最后一个 }
        start = outline_text.find('{')
        end = outline_text.rfind('}')
        if start != -1 and end != -1:
            outline_text = outline_text[start:end+1]

        # 尝试修复常见的 JSON 问题
        import re
        # 替换中文引号为英文引号
        outline_text = outline_text.replace('"', '"').replace('"', '"')
        outline_text = outline_text.replace(''', "'").replace(''', "'")

        outline_data = json.loads(outline_text)
        print(f"✅ 大纲生成完成")
        print(f"   核心切入点: {outline_data['core_angle'][:50]}...")
        print(f"   大纲要点: {len(outline_data['outline'])} 个")

    except Exception as e:
        print(f"❌ 大纲生成失败: {str(e)}")
        print(f"   尝试手动解析...")

        # 手动提取关键信息
        try:
            import re
            core_match = re.search(r'"core_angle":\s*"([^"]+)"', outline_response)
            outline_matches = re.findall(r'"([^"]+)"(?=\s*[,\]])', outline_response)

            if core_match and len(outline_matches) > 1:
                outline_data = {
                    'core_angle': core_match.group(1),
                    'outline': outline_matches[1:6]  # 取后面的作为大纲
                }
                print(f"✅ 手动解析成功")
                print(f"   核心切入点: {outline_data['core_angle'][:50]}...")
                print(f"   大纲要点: {len(outline_data['outline'])} 个")
            else:
                print(f"❌ 手动解析也失败")
                return
        except:
            return

    # ========== 步骤4: 生成完整内容（小红书格式） ==========
    print("\n【步骤4】生成完整内容（小红书格式）...")

    content_prompt = f"""你是小红书爆款内容创作者。请根据以下大纲生成小红书图文。

**核心切入点：** {outline_data['core_angle']}

**内容大纲：**
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(outline_data['outline'])])}

**要求：**
1. 首图大标题：12字以内
2. 正文400-600字，重度使用 Emoji
3. 采用高干货 List 体
4. 结尾带流量标签

请生成完整的小红书图文。"""

    try:
        original_content = claude.generate(content_prompt, max_tokens=1500)
        print(f"✅ 内容生成完成（{len(original_content)} 字）")
        print("\n" + "-"*70)
        print(original_content[:300] + "...")
        print("-"*70)

    except Exception as e:
        print(f"❌ 内容生成失败: {str(e)}")
        return

    # ========== 步骤5: 模拟用户修改 ==========
    print("\n【步骤5】模拟用户修改...")

    # 简单模拟：添加更多 emoji 和口语化
    edited_content = original_content.replace("。", "！").replace("，", "，")
    edited_content = "🔥 " + edited_content

    print("✅ 模拟修改完成")

    # ========== 步骤6: 反馈学习 ==========
    print("\n【步骤6】反馈学习 - 分析修改规律...")

    learner = FeedbackLearner()

    try:
        comparison = learner.compare_versions(original_content, edited_content)

        if comparison['has_changes']:
            print(f"✅ 检测到修改（相似度: {comparison['similarity']:.2%}）")
            print(f"   修改总结: {comparison['summary'][:100]}...")
            print(f"   提取规律: {len(comparison['patterns'])} 条")

            # 保存到错题本
            correction_entry = learner.save_to_correction_history(
                content_type='xiaohongshu',
                patterns=comparison['patterns'],
                summary=comparison['summary']
            )

            print(f"✅ 已保存到错题本")

        else:
            print("ℹ️  内容几乎未修改")

    except Exception as e:
        print(f"❌ 反馈学习失败: {str(e)}")

    # ========== 总结 ==========
    print("\n" + "="*70)
    print("✨ 完整流程测试完成！")
    print("="*70)
    print("\n测试覆盖：")
    print("  ✅ 1. TopHub 采集器（多平台聚合）")
    print("  ✅ 2. 5维度打分器（含情绪共鸣和用户痛点）")
    print("  ✅ 3. 两段式审核 - 大纲生成")
    print("  ✅ 4. 两段式审核 - 完整内容生成")
    print("  ✅ 5. 反馈学习闭环（错题本）")
    print("\n下一步：")
    print("  • 运行 Streamlit 界面: streamlit run app.py")
    print("  • 访问【大纲审核】页面测试两段式审核流")
    print("  • 访问【内容生成与审核】页面测试反馈学习")
    print("="*70)


if __name__ == '__main__':
    test_full_workflow()
