"""
两段式审核流 - 第一阶段：大纲审核
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.generator.claude_client import ClaudeClient
from modules.utils import DATA_DIR

st.set_page_config(
    page_title="大纲审核 - AI内容工厂",
    page_icon="📝",
    layout="wide"
)

st.title("📝 大纲审核（两段式审核 - 第一阶段）")
st.markdown("---")

# 初始化
if 'claude_client' not in st.session_state:
    st.session_state.claude_client = ClaudeClient()

if 'outlines' not in st.session_state:
    st.session_state.outlines = {}

if 'approved_topics' not in st.session_state:
    st.session_state.approved_topics = []


def generate_outline(topic: Dict) -> Dict:
    """生成核心切入点和大纲"""
    prompt = f"""你是K博士的内容策划助手。请为以下选题生成核心切入点和内容大纲。

**选题信息：**
标题：{topic['title']}
来源：{topic.get('source', '未知')}
用户痛点：{topic.get('audience_pain_point', '未识别')}
建议角度：{', '.join(topic.get('suggested_angles', []))}

**任务：**
1. 提炼核心切入点（1-2句话，直击痛点）
2. 设计内容大纲（3-5个要点，每个要点1句话说明）

**输出格式（JSON）：**
{{
  "core_angle": "从AI取代白领的焦虑，谈如何培养孩子不可替代的能力",
  "outline": [
    "开场：18个月后白领被AI取代？这不是危言耸听",
    "痛点：传统教育培养的能力正在贬值",
    "解决方案1：培养AI无法替代的创造力",
    "解决方案2：建立终身学习的思维模式",
    "行动建议：家长现在可以做的3件事"
  ],
  "estimated_length": "1200字",
  "target_formats": ["视频文案", "公众号文章", "小红书"]
}}

只返回 JSON，不要其他内容。"""

    try:
        response = st.session_state.claude_client.generate(prompt, max_tokens=800)

        # 解析 JSON
        result_text = response.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        outline_data = json.loads(result_text)
        outline_data['topic_id'] = topic.get('title', '')
        outline_data['generated_at'] = datetime.now().isoformat()

        return outline_data

    except Exception as e:
        st.error(f"生成大纲失败: {str(e)}")
        return None


# 主界面
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 待审核选题")

    # 加载已打分的选题
    topics_dir = DATA_DIR / 'topics'
    scored_files = sorted(topics_dir.glob('scored_topics_*.json'), reverse=True)

    if scored_files:
        with open(scored_files[0], 'r', encoding='utf-8') as f:
            topics = json.load(f)

        st.info(f"加载了 {len(topics)} 个已打分选题")

        # 显示选题列表
        for i, topic in enumerate(topics[:10]):
            with st.expander(f"#{i+1} [{topic['total_score']}/50分] {topic['title'][:40]}..."):
                st.write(f"**平台：** {topic.get('platform', '未知')}")
                st.write(f"**总分：** {topic['total_score']}/50")
                st.write(f"**用户痛点：** {topic.get('audience_pain_point', '未识别')}")

                if st.button(f"生成大纲", key=f"gen_{i}"):
                    with st.spinner("生成中..."):
                        outline = generate_outline(topic)
                        if outline:
                            st.session_state.outlines[topic['title']] = {
                                'topic': topic,
                                'outline': outline,
                                'status': 'pending'
                            }
                            st.rerun()
    else:
        st.warning("没有找到已打分的选题，请先运行采集和打分流程")
        if st.button("运行测试采集"):
            st.info("请在终端运行: python3 test_collect_and_score.py")

with col2:
    st.subheader("📝 大纲审核")

    if st.session_state.outlines:
        # 显示待审核的大纲
        for title, data in st.session_state.outlines.items():
            if data['status'] == 'pending':
                topic = data['topic']
                outline = data['outline']

                st.markdown(f"### {topic['title'][:60]}...")
                st.markdown(f"**总分：** {topic['total_score']}/50 | **平台：** {topic.get('platform', '未知')}")

                # 显示大纲
                st.markdown("#### 🎯 核心切入点")
                core_angle = st.text_area(
                    "核心切入点（可编辑）",
                    value=outline['core_angle'],
                    height=80,
                    key=f"angle_{title}"
                )

                st.markdown("#### 📋 内容大纲")
                outline_points = []
                for i, point in enumerate(outline['outline']):
                    edited_point = st.text_input(
                        f"要点 {i+1}",
                        value=point,
                        key=f"point_{title}_{i}"
                    )
                    outline_points.append(edited_point)

                st.markdown("#### 📊 生成设置")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"预计字数：{outline['estimated_length']}")
                with col_b:
                    formats = st.multiselect(
                        "生成格式",
                        ["视频文案", "公众号文章", "小红书", "朋友圈"],
                        default=outline.get('target_formats', ["视频文案", "公众号文章"]),
                        key=f"formats_{title}"
                    )

                # 操作按钮
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button("✅ 确认大纲，生成内容", key=f"approve_{title}", type="primary"):
                        # 保存审核通过的大纲
                        approved_data = {
                            'topic': topic,
                            'core_angle': core_angle,
                            'outline': outline_points,
                            'formats': formats,
                            'approved_at': datetime.now().isoformat()
                        }

                        # 保存到文件
                        approved_dir = DATA_DIR / 'approved_outlines'
                        approved_dir.mkdir(exist_ok=True)

                        filename = f"outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{topic['title'][:20]}.json"
                        filepath = approved_dir / filename

                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(approved_data, f, ensure_ascii=False, indent=2)

                        st.session_state.outlines[title]['status'] = 'approved'
                        st.session_state.approved_topics.append(approved_data)

                        st.success(f"✅ 大纲已确认！已保存到: {filepath}")
                        st.info("💡 提示：现在可以进入「内容生成」页面生成完整内容")
                        st.rerun()

                with col_btn2:
                    if st.button("🔄 重新生成大纲", key=f"regen_{title}"):
                        with st.spinner("重新生成中..."):
                            new_outline = generate_outline(topic)
                            if new_outline:
                                st.session_state.outlines[title]['outline'] = new_outline
                                st.rerun()

                with col_btn3:
                    if st.button("❌ 放弃此选题", key=f"reject_{title}"):
                        st.session_state.outlines[title]['status'] = 'rejected'
                        st.rerun()

                st.markdown("---")

    else:
        st.info("👈 请从左侧选择选题并生成大纲")

# 显示已确认的大纲
if st.session_state.approved_topics:
    st.markdown("---")
    st.subheader("✅ 已确认的大纲")

    for i, data in enumerate(st.session_state.approved_topics):
        with st.expander(f"#{i+1} {data['topic']['title'][:50]}..."):
            st.write(f"**核心切入点：** {data['core_angle']}")
            st.write(f"**大纲要点：**")
            for j, point in enumerate(data['outline'], 1):
                st.write(f"{j}. {point}")
            st.write(f"**生成格式：** {', '.join(data['formats'])}")
            st.write(f"**确认时间：** {data['approved_at']}")
