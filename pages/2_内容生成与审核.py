"""
两段式审核流 - 第二阶段：完整内容生成与审核
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from modules.generator.main import ContentGenerator
from modules.processor.feedback_loop import FeedbackLearner
from modules.utils import DATA_DIR

st.set_page_config(
    page_title="内容审核 - AI内容工厂",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ 内容生成与审核（两段式审核 - 第二阶段）")
st.markdown("---")

# 初始化
if 'generator' not in st.session_state:
    st.session_state.generator = ContentGenerator()

if 'feedback_learner' not in st.session_state:
    st.session_state.feedback_learner = FeedbackLearner()

if 'generated_contents' not in st.session_state:
    st.session_state.generated_contents = {}


def load_approved_outlines() -> List[Dict]:
    """加载已审核通过的大纲"""
    approved_dir = DATA_DIR / 'approved_outlines'
    if not approved_dir.exists():
        return []

    outlines = []
    for file in sorted(approved_dir.glob('outline_*.json'), reverse=True):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['filename'] = file.name
                outlines.append(data)
        except Exception as e:
            st.error(f"加载文件失败 {file.name}: {str(e)}")

    return outlines


def generate_full_content(outline_data: Dict, format_type: str) -> str:
    """根据大纲生成完整内容"""
    topic = outline_data['topic']
    core_angle = outline_data['core_angle']
    outline_points = outline_data['outline']

    # 根据格式类型选择不同的 prompt
    if format_type == "视频文案":
        prompt = f"""你是专业的短视频文案创作者。请根据以下大纲生成完整的视频文案。

**核心切入点：** {core_angle}

**内容大纲：**
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(outline_points)])}

**要求：**
1. 每段落必须包含 [画面建议] 和 [BGM情绪] 标签
2. 口语化表达，避免书面语
3. 总时长3-5分钟（900-1500字）
4. 包含2-3个金句

请生成完整的视频文案。"""

    elif format_type == "小红书":
        prompt = f"""你是小红书爆款内容创作者。请根据以下大纲生成小红书图文。

**核心切入点：** {core_angle}

**内容大纲：**
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(outline_points)])}

**要求：**
1. 首图大标题：12字以内，极具痛点
2. 正文400-800字，重度使用 Emoji
3. 采用高干货 List 体
4. 结尾带8-12个流量标签

请生成完整的小红书图文。"""

    elif format_type == "公众号文章":
        prompt = f"""你是公众号内容创作者。请根据以下大纲生成公众号文章。

**核心切入点：** {core_angle}

**内容大纲：**
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(outline_points)])}

**要求：**
1. 1200-1800字
2. 专业但易懂，有温度有深度
3. 包含小标题分段
4. 结尾有行动建议

请生成完整的公众号文章。"""

    else:  # 朋友圈
        prompt = f"""你是朋友圈内容创作者。请根据以下大纲生成朋友圈文案。

**核心切入点：** {core_angle}

**内容大纲：**
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(outline_points)])}

**要求：**
1. 200-300字
2. 口语化，像和朋友聊天
3. 引发共鸣和讨论

请生成完整的朋友圈文案。"""

    try:
        content = st.session_state.generator.generate_with_claude(prompt)
        return content
    except Exception as e:
        st.error(f"生成失败: {str(e)}")
        return ""


# 主界面
tab1, tab2 = st.tabs(["📝 生成内容", "📊 修改对比"])

with tab1:
    st.subheader("待生成的大纲")

    # 加载已审核通过的大纲
    approved_outlines = load_approved_outlines()

    if not approved_outlines:
        st.warning("没有待生成的大纲，请先在【大纲审核】页面审核通过选题")
    else:
        st.success(f"找到 {len(approved_outlines)} 个待生成的大纲")

        # 选择要生成的大纲
        selected_outline = st.selectbox(
            "选择大纲",
            approved_outlines,
            format_func=lambda x: f"{x['topic']['title'][:50]}... ({x['approved_at'][:10]})"
        )

        if selected_outline:
            st.markdown("---")
            st.markdown(f"### {selected_outline['topic']['title']}")
            st.markdown(f"**核心切入点：** {selected_outline['core_angle']}")

            st.markdown("**内容大纲：**")
            for i, point in enumerate(selected_outline['outline'], 1):
                st.markdown(f"{i}. {point}")

            st.markdown("---")

            # 选择要生成的格式
            formats_to_generate = st.multiselect(
                "选择要生成的格式",
                selected_outline['formats'],
                default=selected_outline['formats']
            )

            if st.button("🚀 开始生成", type="primary"):
                if not formats_to_generate:
                    st.warning("请至少选择一种格式")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    generated = {}

                    for i, format_type in enumerate(formats_to_generate):
                        status_text.text(f"正在生成 {format_type}...")
                        progress_bar.progress((i + 1) / len(formats_to_generate))

                        content = generate_full_content(selected_outline, format_type)
                        if content:
                            generated[format_type] = {
                                'content': content,
                                'original': content,  # 保存原稿用于对比
                                'generated_at': datetime.now().isoformat()
                            }

                    st.session_state.generated_contents[selected_outline['filename']] = {
                        'outline': selected_outline,
                        'contents': generated
                    }

                    status_text.text("✅ 生成完成！")
                    st.success(f"成功生成 {len(generated)} 种格式的内容")
                    st.rerun()

    # 显示已生成的内容
    if st.session_state.generated_contents:
        st.markdown("---")
        st.subheader("📄 已生成的内容")

        for outline_file, data in st.session_state.generated_contents.items():
            with st.expander(f"📝 {data['outline']['topic']['title'][:50]}..."):
                for format_type, content_data in data['contents'].items():
                    st.markdown(f"#### {format_type}")

                    # 可编辑的内容区域
                    edited_content = st.text_area(
                        f"内容（可编辑）",
                        value=content_data['content'],
                        height=400,
                        key=f"edit_{outline_file}_{format_type}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("💾 保存修改", key=f"save_{outline_file}_{format_type}"):
                            # 更新内容
                            st.session_state.generated_contents[outline_file]['contents'][format_type]['content'] = edited_content
                            st.success("已保存")

                    with col2:
                        if st.button("📊 查看修改对比", key=f"compare_{outline_file}_{format_type}"):
                            st.session_state.current_comparison = {
                                'outline_file': outline_file,
                                'format_type': format_type,
                                'original': content_data['original'],
                                'edited': edited_content
                            }
                            st.info("请切换到【修改对比】标签页查看")

                    with col3:
                        if st.button("📤 发布", key=f"publish_{outline_file}_{format_type}"):
                            # 保存到已发布目录
                            published_dir = DATA_DIR / 'published'
                            published_dir.mkdir(exist_ok=True)

                            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data['outline']['topic']['title'][:20]}_{format_type}.txt"
                            filepath = published_dir / filename

                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(edited_content)

                            st.success(f"已发布到: {filepath}")

                    st.markdown("---")

with tab2:
    st.subheader("📊 修改对比与学习")

    if 'current_comparison' in st.session_state:
        comp = st.session_state.current_comparison

        st.markdown(f"### 格式：{comp['format_type']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🤖 AI 原稿")
            st.text_area("原稿", value=comp['original'], height=400, disabled=True, key="orig_display")

        with col2:
            st.markdown("#### ✏️ 用户修改稿")
            st.text_area("修改稿", value=comp['edited'], height=400, disabled=True, key="edit_display")

        st.markdown("---")

        if st.button("🧠 分析修改规律并学习", type="primary"):
            with st.spinner("AI 正在分析修改规律..."):
                # 使用反馈学习器分析
                analysis = st.session_state.feedback_learner.compare_versions(
                    comp['original'],
                    comp['edited']
                )

                if analysis['has_changes']:
                    st.success("✅ 分析完成！")

                    st.markdown("### 📝 修改总结")
                    st.info(analysis['summary'])

                    st.markdown("### 🔍 提取的修改规律")
                    for i, pattern in enumerate(analysis['patterns'], 1):
                        with st.expander(f"{i}. {pattern['type']}: {pattern['description']}"):
                            st.code(pattern.get('example', '无示例'))

                    # 保存到错题本
                    if st.button("💾 保存到错题本"):
                        correction_entry = st.session_state.feedback_learner.save_to_correction_history(
                            content_type=comp['format_type'],
                            patterns=analysis['patterns'],
                            summary=analysis['summary']
                        )

                        # 保存到文件
                        corrections_dir = DATA_DIR / 'correction_history'
                        corrections_dir.mkdir(exist_ok=True)

                        filename = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{comp['format_type']}.json"
                        filepath = corrections_dir / filename

                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(correction_entry, f, ensure_ascii=False, indent=2)

                        st.success(f"✅ 已保存到错题本: {filepath}")
                else:
                    st.info("内容几乎未修改，无需学习")

    else:
        st.info("请先在【生成内容】标签页中选择要对比的内容")

# 侧边栏：错题本查看
with st.sidebar:
    st.markdown("### 📚 错题本")

    corrections_dir = DATA_DIR / 'correction_history'
    if corrections_dir.exists():
        correction_files = sorted(corrections_dir.glob('correction_*.json'), reverse=True)

        if correction_files:
            st.success(f"共 {len(correction_files)} 条学习记录")

            selected_correction = st.selectbox(
                "查看历史记录",
                correction_files[:10],
                format_func=lambda x: f"{x.stem[11:30]}..."
            )

            if selected_correction:
                with open(selected_correction, 'r', encoding='utf-8') as f:
                    correction_data = json.load(f)

                st.markdown(f"**类型：** {correction_data['content_type']}")
                st.markdown(f"**学习时间：** {correction_data['learned_at'][:10]}")
                st.markdown(f"**总结：** {correction_data['summary'][:100]}...")

                with st.expander("查看详细规律"):
                    for pattern in correction_data['patterns'][:5]:
                        st.markdown(f"- **{pattern['type']}**: {pattern['description']}")
        else:
            st.info("暂无学习记录")
    else:
        st.info("暂无学习记录")
