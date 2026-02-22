#!/usr/bin/env python3
"""
使用 Claude API 直接测试内容生成
"""
import sys
import os
sys.path.insert(0, '/Users/k/ai-content-factory')

from modules.generator.openclaw_bridge import OpenClawBridge
from modules.generator.claude_client import ClaudeClient

# 创建桥接和 Claude 客户端
bridge = OpenClawBridge()
claude = ClaudeClient()

print("=" * 60)
print("🧪 测试内容生成（使用 Claude API）")
print("=" * 60)

# 测试选题
test_topic = {
    'title': 'AI时代，孩子该学什么才不会被淘汰？',
    'excerpt': '随着AI技术的快速发展，家长们越来越焦虑...',
    'source': '测试',
    'ai_reason': '这个话题非常符合K博士的专业领域',
    'suggested_angles': ['从人生杠杆角度分析', '结合真实案例']
}

test_opinion = "我认为AI时代最重要的是培养孩子从弱变强的能力和做决策的能力"

# 构建 prompt
print("\n📝 使用 K博士的风格生成朋友圈文案...")
prompt = bridge._build_prompt(test_topic, test_opinion, 'moments')

try:
    # 使用 Claude 生成
    content = claude.generate(prompt, max_tokens=500)

    print("\n✅ 生成成功！")
    print("=" * 60)
    print(content)
    print("=" * 60)
    print(f"\n📊 字数: {len(content)} 字")

    # 检查是否符合要求
    print("\n✅ 质量检查:")
    print(f"  - 字数合适: {'✅' if 150 <= len(content) <= 250 else '❌'} ({len(content)}/150-200)")
    print(f"  - 包含观点: {'✅' if '从弱变强' in content or '决策' in content else '⚠️'}")
    print(f"  - 有话题标签: {'✅' if '#' in content else '⚠️'}")

except Exception as e:
    print(f"\n❌ 生成失败: {str(e)}")
    import traceback
    traceback.print_exc()
