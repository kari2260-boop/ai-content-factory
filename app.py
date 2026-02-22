"""
K博士 AI 内容工厂 - Streamlit 管理后台
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from modules.collector.main import TopicCollector
from modules.generator.main import ContentGenerator
from modules.publisher.main import ContentPublisher
from modules.utils import DATA_DIR

# 页面配置
st.set_page_config(
    page_title="K博士 AI 内容工厂",
    page_icon="🏭",
    layout="wide"
)

# 初始化
@st.cache_resource
def init_modules():
    """初始化各模块"""
    collector = TopicCollector()
    generator = ContentGenerator()
    publisher = ContentPublisher()
    return collector, generator, publisher

collector, generator, publisher = init_modules()


# 侧边栏
st.sidebar.title("🏭 K博士 AI 内容工厂")
st.sidebar.markdown("---")

# 服务状态显示
st.sidebar.markdown("### 🔧 服务状态")

# Claude 状态
try:
    from modules.generator.claude_client import ClaudeClient
    claude = ClaudeClient()
    st.sidebar.success("✅ Claude API")
except:
    st.sidebar.error("❌ Claude API")

# Gemini 状态
try:
    from modules.generator.gemini_client import GeminiClient
    gemini = GeminiClient()
    if gemini.available:
        st.sidebar.success("✅ Gemini API")
    else:
        st.sidebar.warning("⚠️ Gemini API (未配置)")
except:
    st.sidebar.warning("⚠️ Gemini API (未配置)")

# OpenClaw 状态
try:
    from modules.generator.openclaw_bridge import OpenClawBridge
    openclaw = OpenClawBridge()
    if openclaw.available:
        st.sidebar.success("✅ OpenClaw")
    else:
        st.sidebar.warning("⚠️ OpenClaw (未运行)")
except:
    st.sidebar.warning("⚠️ OpenClaw (未运行)")

# Notion 状态
try:
    from modules.publisher.notion_client import NotionClient
    notion = NotionClient()
    st.sidebar.success("✅ Notion API")
except:
    st.sidebar.error("❌ Notion API (未配置)")

# 收件箱状态
try:
    from knowledge_feed import KnowledgeFeed
    kf = KnowledgeFeed()
    if kf.is_watching:
        st.sidebar.success("✅ 收件箱监听")
    else:
        st.sidebar.info("⏸️ 收件箱监听 (未启动)")
except:
    st.sidebar.info("⏸️ 收件箱监听 (未启动)")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "导航",
    ["📊 选题采集", "✍️ 内容生成", "📤 发布管理", "⚙️ 系统设置"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**使用流程：**
1. 采集今日选题
2. 勾选 2-3 个选题
3. 写一句话观点
4. 生成 5 种格式内容
5. 审核并发布
""")


# ==================== 页面1：选题采集 ====================
if page == "📊 选题采集":
    st.title("📊 今日选题采集")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🔄 开始采集选题", type="primary", use_container_width=True):
            with st.spinner("正在采集选题..."):
                try:
                    topics = collector.run()
                    st.success(f"✅ 采集完成！共获得 {len(topics)} 个选题")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 采集失败: {str(e)}")

    with col2:
        st.metric("今日选题数", len(collector.get_latest_topics()))

    st.markdown("---")

    # 显示选题列表
    topics = collector.get_latest_topics()

    if not topics:
        st.info("暂无选题，请先点击「开始采集选题」")
    else:
        # 筛选器
        col1, col2, col3 = st.columns(3)
        with col1:
            # 检查是否有打分字段
            has_scores = any('total_score' in t for t in topics)
            if has_scores:
                min_score = st.slider("最低分数", 0, 40, 25)
            else:
                st.info("当前选题未打分")
                min_score = 0
        with col2:
            source_filter = st.multiselect(
                "数据源",
                options=list(set([t['source'] for t in topics])),
                default=[]
            )
        with col3:
            if has_scores:
                sort_by = st.selectbox("排序", ["总分", "时间"])
            else:
                sort_by = st.selectbox("排序", ["时间"])

        # 过滤和排序
        filtered_topics = [t for t in topics if t.get('total_score', 0) >= min_score]
        if source_filter:
            filtered_topics = [t for t in filtered_topics if t['source'] in source_filter]

        if sort_by == "总分" and has_scores:
            filtered_topics.sort(key=lambda x: x.get('total_score', 0), reverse=True)

        st.markdown(f"### 📋 选题列表（共 {len(filtered_topics)} 个）")

        # 显示选题卡片
        for i, topic in enumerate(filtered_topics):
            # 检查是否有打分
            has_score = 'total_score' in topic
            score_text = f"(总分: {topic['total_score']}/40)" if has_score else ""

            with st.expander(f"**{i+1}. {topic['title']}** {score_text}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**摘要：** {topic.get('excerpt', '无')[:200]}...")
                    st.markdown(f"**来源：** {topic['source']}")
                    if topic.get('url'):
                        st.markdown(f"**原文：** [{topic['url']}]({topic['url']})")
                    if 'heat_score' in topic:
                        st.markdown(f"**热度：** {topic['heat_score']}")
                    if topic.get('core_insight'):
                        st.markdown(f"**核心观点：** {topic['core_insight']}")
                    if topic.get('viral_hook'):
                        st.markdown(f"**爆点：** {topic['viral_hook']}")
                    if 'ai_reason' in topic:
                        st.markdown(f"**AI 评分理由：** {topic['ai_reason']}")
                    if 'suggested_angles' in topic:
                        st.markdown(f"**建议角度：** {', '.join(topic['suggested_angles'])}")

                with col2:
                    if has_score:
                        st.metric("相关度", f"{topic.get('relevance_score', 0)}/10")
                        st.metric("时效性", f"{topic.get('timeliness_score', 0)}/10")
                        st.metric("互动潜力", f"{topic.get('engagement_score', 0)}/10")
                        st.metric("独特性", f"{topic.get('uniqueness_score', 0)}/10")
                    else:
                        st.info("未打分")

                # 保存选中的选题到 session_state
                if st.button(f"✅ 选择这个选题", key=f"select_{i}"):
                    st.session_state['selected_topic'] = topic
                    st.success("已选择，请前往「内容生成」页面")


# ==================== 页面2：内容生成 ====================
elif page == "✍️ 内容生成":
    st.title("✍️ 内容生成工坊")

    # 检查是否有选中的选题
    if 'selected_topic' not in st.session_state:
        st.warning("⚠️ 请先在「选题采集」页面选择一个选题")

        # 显示最近的草稿
        st.markdown("### 📝 最近的草稿")
        drafts = generator.get_latest_drafts(5)

        if drafts:
            for draft in drafts:
                with st.expander(f"{draft['topic']['title'][:50]}... ({draft['generated_at'][:10]})"):
                    st.json(draft)
        else:
            st.info("暂无草稿")

    else:
        topic = st.session_state['selected_topic']

        st.markdown(f"### 📌 当前选题")
        st.info(f"**{topic['title']}** (总分: {topic.get('total_score', topic.get('score', 0))}/40)")

        # 用户输入观点
        user_opinion = st.text_area(
            "💭 写下你的核心观点（一句话）",
            placeholder="例如：我认为AI时代最重要的是培养孩子的创造力和批判性思维...",
            height=100
        )

        # 格式选择
        format_options = {
            'video': '🎬 视频号',
            'article': '📰 公众号',
            'moments': '💬 朋友圈',
            'xiaohongshu': '📱 小红书',
            'book': '📚 书稿'
        }
        selected_formats = st.multiselect(
            "选择生成格式",
            options=list(format_options.keys()),
            default=list(format_options.keys()),
            format_func=lambda x: format_options[x]
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🚀 生成内容", type="primary", use_container_width=True, disabled=not user_opinion or not selected_formats):
                with st.spinner("正在生成内容，预计需要 2-3 分钟..."):
                    try:
                        results = generator.generate_all_formats(topic, user_opinion, selected_formats=selected_formats)
                        st.session_state['current_draft'] = results
                        st.success("✅ 内容生成完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 生成失败: {str(e)}")

        with col2:
            if st.button("🔄 重新选择选题", use_container_width=True):
                del st.session_state['selected_topic']
                st.rerun()

        # 显示生成的内容
        if 'current_draft' in st.session_state:
            st.markdown("---")
            st.markdown("### 📄 生成的内容")

            draft = st.session_state['current_draft']

            tabs = st.tabs(["🎬 视频号", "📰 公众号", "💬 朋友圈", "📱 小红书", "📚 书稿"])

            format_keys = ['video', 'article', 'moments', 'xiaohongshu', 'book']

            for tab, format_key in zip(tabs, format_keys):
                with tab:
                    if format_key in draft['contents']:
                        content_data = draft['contents'][format_key]

                        if content_data.get('error'):
                            st.error(f"生成失败: {content_data['content']}")
                        else:
                            st.markdown(f"**字数：** {content_data['word_count']}")
                            st.markdown("---")
                            st.markdown(content_data['content'])

                            # 编辑功能
                            edited_content = st.text_area(
                                "编辑内容",
                                value=content_data['content'],
                                height=400,
                                key=f"edit_{format_key}"
                            )

                            if edited_content != content_data['content']:
                                if st.button(f"💾 保存修改", key=f"save_{format_key}"):
                                    draft['contents'][format_key]['content'] = edited_content
                                    draft['contents'][format_key]['word_count'] = len(edited_content)
                                    st.success("已保存修改")

            # 发布按钮
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📤 发布到 Notion", type="primary", use_container_width=True):
                    with st.spinner("正在发布..."):
                        try:
                            results = publisher.publish_draft(draft)
                            st.success("✅ 发布成功！")
                            st.json(results)
                        except Exception as e:
                            st.error(f"❌ 发布失败: {str(e)}")

            with col2:
                if st.button("💾 导出文件", use_container_width=True):
                    exported = publisher.export_files(draft)
                    st.success(f"✅ 已导出 {len(exported)} 个文件")
                    st.json(exported)

            with col3:
                if st.button("🗑️ 清空当前草稿", use_container_width=True):
                    del st.session_state['current_draft']
                    del st.session_state['selected_topic']
                    st.rerun()


# ==================== 页面3：发布管理 ====================
elif page == "📤 发布管理":
    st.title("📤 发布管理")

    # 显示发布记录
    record_file = DATA_DIR / 'published' / 'publish_records.json'

    if record_file.exists():
        with open(record_file, 'r', encoding='utf-8') as f:
            records = json.load(f)

        st.markdown(f"### 📊 发布记录（共 {len(records)} 条）")

        for i, record in enumerate(reversed(records[-20:])):  # 最近20条
            with st.expander(f"{i+1}. {record['topic']} ({record.get('draft_id', '')[:10]})"):
                st.json(record)
    else:
        st.info("暂无发布记录")


# ==================== 页面4：系统设置 ====================
elif page == "⚙️ 系统设置":
    st.title("⚙️ 系统设置")

    st.markdown("### 🔑 API 配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Claude API**")
        from modules.config import ANTHROPIC_API_KEY
        if ANTHROPIC_API_KEY:
            st.success("✅ 已配置")
        else:
            st.error("❌ 未配置")

        st.markdown("**Gemini API**")
        from modules.config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            st.success("✅ 已配置")
        else:
            st.warning("⚠️ 未配置（可选）")

    with col2:
        st.markdown("**Notion**")
        from modules.config import NOTION_TOKEN, NOTION_DATABASE_ID
        if NOTION_TOKEN and NOTION_DATABASE_ID:
            st.success("✅ 已配置")
        else:
            st.error("❌ 未配置")

        st.markdown("**OpenClaw**")
        if generator.openclaw.available:
            st.success("✅ 运行中")
        else:
            st.warning("⚠️ 未运行")

    st.markdown("---")
    st.markdown("### 📁 数据目录")
    st.code(str(DATA_DIR))

    st.markdown("### 📊 统计信息")
    col1, col2, col3 = st.columns(3)

    with col1:
        topics_count = len(list((DATA_DIR / 'topics').glob('*.json')))
        st.metric("选题文件", topics_count)

    with col2:
        drafts_count = len(list((DATA_DIR / 'drafts').glob('*.json')))
        st.metric("草稿文件", drafts_count)

    with col3:
        published_count = len(list((DATA_DIR / 'published').glob('*.txt')))
        st.metric("已发布文件", published_count)
