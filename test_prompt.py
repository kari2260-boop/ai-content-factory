#!/usr/bin/env python3
"""
简化测试：验证内容生成 prompt 是否正确
"""
import sys
sys.path.insert(0, '/Users/k/ai-content-factory')

from modules.generator.openclaw_bridge import OpenClawBridge

# 创建桥接
bridge = OpenClawBridge()

print("=" * 60)
print("🧪 测试 OpenClaw 桥接")
print("=" * 60)

# 检查状态
print(f"\n✅ OpenClaw 可用: {bridge.available}")

# 读取配置
profile = bridge.get_kari_profile()
print(f"\n📄 配置文件:")
print(f"  - USER.md: {len(profile['user'])} 字符")
print(f"  - MEMORY.md: {len(profile['memory'])} 字符")
print(f"  - CONTENT_GUIDE.md: {len(profile['content_guide'])} 字符")

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
print("\n📝 生成的 Prompt:")
print("=" * 60)
prompt = bridge._build_prompt(test_topic, test_opinion, 'moments')
print(prompt)
print("=" * 60)

print("\n💡 Prompt 长度:", len(prompt), "字符")
print("\n✅ Prompt 构建成功！")
print("\n📌 下一步:")
print("  1. 配置 OpenClaw API key")
print("  2. 或者使用 Claude API 直接生成")
