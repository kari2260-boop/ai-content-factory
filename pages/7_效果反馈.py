"""
效果反馈页面
"""
import streamlit as st
from datetime import datetime

from feedback_tracker import FeedbackTracker

st.set_page_config(page_title="效果反馈", page_icon="📊", layout="wide")

# 初始化
@st.cache_resource
def init_feedback_tracker():
    try:
        return FeedbackTracker()
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        return None

ft = init_feedback_tracker()

if not ft:
    st.stop()

st.title("📊 效果反馈与智能回流")

# 四个 Tab
tab1, tab2, tab3, tab4 = st.tabs(["📝 待录入", "📈 效果概览", "🔄 智能回流", "🎯 提示词优化"])

# Tab1: 待录入
with tab1:
    st.markdown("### 待录入效果数据的内容")
    st.info("这里显示已发布但尚未录入效果数据的内容")

    # 模拟待录入列表
    st.markdown("#### 录入效果数据")

    with st.form("feedback_form"):
        col1, col2 = st.columns(2)

        with col1:
            page_id = st.text_input("Notion 页面 ID")
            views = st.number_input("阅读量", min_value=0, value=0)
            interactions = st.number_input("互动数（点赞+评论+转发）", min_value=0, value=0)

        with col2:
            completion_rate = st.slider("完读率 (%)", 0, 100, 50)
            subjective_score = st.select_slider(
                "主观评分",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: "⭐" * x
            )

        submitted = st.form_submit_button("💾 保存效果数据")

        if submitted:
            if not page_id:
                st.error("请输入 Notion 页面 ID")
            else:
                with st.spinner("保存中..."):
                    # 更新指标
                    success1 = ft.update_metrics(
                        page_id,
                        views,
                        interactions,
                        completion_rate / 100
                    )

                    # 更新评分
                    success2 = ft.update_score(page_id, subjective_score)

                    if success1 and success2:
                        st.success("✅ 效果数据已保存")
                        st.rerun()
                    else:
                        st.error("❌ 保存失败，请检查页面 ID 是否正确")

# Tab2: 效果概览
with tab2:
    st.markdown("### 各平台效果数据概览")

    # 平台选择
    platforms = ["全部", "视频号", "公众号", "小红书", "朋友圈"]
    selected_platform = st.selectbox("选择平台", platforms)

    # 显示统计数据
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总发布数", "0")

    with col2:
        st.metric("平均阅读量", "0")

    with col3:
        st.metric("平均互动数", "0")

    with col4:
        st.metric("高质量内容", "0")

    st.markdown("---")

    st.markdown("#### 📊 Top 10 内容")
    st.info("暂无数据，请先录入效果数据")

# Tab3: 智能回流
with tab3:
    st.markdown("### 🔄 智能回流建议")
    st.info("系统会自动分析高质量内容，建议回流到书稿库作为参考样本")

    st.markdown("#### 回流标准")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**客观指标**")
        st.markdown("- 阅读量 ≥ 5,000")
        st.markdown("- 互动数 ≥ 100")

    with col2:
        st.markdown("**主观指标**")
        st.markdown("- 主观评分 ≥ 4 星")

    st.markdown("---")

    st.markdown("#### 待回流内容")

    # 输入页面 ID 进行分析
    with st.form("backflow_analysis_form"):
        analysis_page_id = st.text_input("输入 Notion 页面 ID 进行分析")
        analyze_btn = st.form_submit_button("🔍 分析回流建议")

        if analyze_btn and analysis_page_id:
            with st.spinner("分析中..."):
                result = ft.analyze_and_suggest_backflow(analysis_page_id)

                if result['should_backflow']:
                    st.success(f"✅ 建议回流")
                    st.markdown(f"**理由**: {result['reason']}")

                    # 显示指标
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("阅读量", result['metrics']['views'])
                    with col2:
                        st.metric("互动数", result['metrics']['interactions'])
                    with col3:
                        st.metric("评分", f"{'⭐' * result['metrics']['score']}")

                    # 确认回流按钮
                    if st.button("✅ 确认回流到书稿库"):
                        with st.spinner("处理中..."):
                            success = ft.confirm_backflow(analysis_page_id)
                            if success:
                                st.success("✅ 已标记为参考样本")
                            else:
                                st.error("❌ 回流失败")
                else:
                    st.warning(f"⚠️ 暂不建议回流")
                    st.markdown(f"**理由**: {result['reason']}")

                    # 显示指标
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("阅读量", result['metrics']['views'])
                    with col2:
                        st.metric("互动数", result['metrics']['interactions'])
                    with col3:
                        st.metric("评分", f"{'⭐' * result['metrics']['score']}")

# Tab4: 提示词优化
with tab4:
    st.markdown("### 🎯 提示词优化建议")
    st.info("基于效果数据，AI 分析并给出 Prompt 改进建议")

    platform = st.selectbox(
        "选择平台",
        ["视频号", "公众号", "小红书", "朋友圈", "书稿"],
        key="optimize_platform"
    )

    if st.button("🤖 生成优化建议", key="generate_advice"):
        with st.spinner("AI 分析中，预计需要 30 秒..."):
            advice = ft.generate_prompt_optimization_advice(platform)

            if advice:
                st.markdown("### 📋 优化建议")
                st.markdown(advice)

                # 下载按钮
                st.download_button(
                    label="💾 下载优化建议",
                    data=advice,
                    file_name=f"prompt_optimization_{platform}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
            else:
                st.error("生成失败，请稍后重试")

    st.markdown("---")

    st.markdown("#### 💡 优化建议示例")
    with st.expander("查看示例"):
        st.markdown("""
### 视频号文案优化建议

**当前问题**:
- 开头不够吸引人，前3秒流失率高
- 缺少情感共鸣点
- CTA 不够明确

**优化方向**:
1. **开头优化**: 用反常识问题或冲突场景
2. **情感共鸣**: 增加真实案例和场景描述
3. **节奏控制**: 每30秒一个小高潮
4. **CTA 优化**: 明确引导互动

**Prompt 调整建议**:
- 在开头部分增加"用一个让人意外的问题开场"
- 在主体部分增加"讲述一个真实的家长案例"
- 在结尾增加"用一个开放式问题引导评论"
        """)

st.markdown("---")

st.markdown("### 📚 使用说明")
with st.expander("如何使用效果反馈功能"):
    st.markdown("""
1. **录入数据**: 在「待录入」Tab 中输入发布内容的效果数据
2. **查看概览**: 在「效果概览」Tab 中查看各平台的整体表现
3. **智能回流**: 系统自动分析高质量内容，建议回流到书稿库
4. **优化提示词**: 基于效果数据，AI 给出 Prompt 改进建议

**回流标准**:
- 阅读量 ≥ 5,000 或主观评分 ≥ 4 星的内容会被建议回流
- 回流后的内容会在书稿库中标记为「参考样本」
- 后续生成内容时，AI 会参考这些高质量样本
    """)
