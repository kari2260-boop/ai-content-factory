"""
K博士 AI 内容工厂 - Streamlit 管理后台
"""
import streamlit as st
import json
import importlib.util
from datetime import datetime
from pathlib import Path

from modules.collector.main import TopicCollector
from modules.generator.main import ContentGenerator
from modules.publisher.main import ContentPublisher
from modules.utils import DATA_DIR
from modules.user.manager import UserManager
from modules.user.context import UserContext

# 页面配置
st.set_page_config(
    page_title="傲客内容工厂",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 傲客品牌 CSS —— 浅色为主，金线点缀
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Inter:wght@400;500;600&display=swap');

/* ── 全局 ── */
html, body, [class*="css"], * {
    font-family: "Inter","PingFang SC","Hiragino Sans GB",system-ui,sans-serif !important;
    color: #2a241c;
}
.stApp, .main, section.main, [data-testid="stAppViewContainer"] {
    background: #f7f3ec !important;
}

/* ── 顶部黑条隐藏 ── */
[data-testid="stHeader"], header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 1px solid #e8dfc8 !important;
    height: 0 !important;
    min-height: 0 !important;
}
.stDeployButton, [data-testid="stToolbar"] { display: none !important; }

/* ── 隐藏 Streamlit 自带 pages 导航 ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"] > div > div > div:first-child ul,
nav[aria-label="pages navigation"] { display: none !important; }

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: #faf7f2 !important;
    border-right: 1px solid #e0d5be !important;
    min-width: 220px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] * { color: #2a241c !important; background: transparent !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 13px !important; padding: 1px 0 !important; }

/* ── 下拉/select 白底（关键修复） ── */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-testid="stSelectbox"] > div > div,
div[role="listbox"], div[role="option"],
[data-baseweb="popover"] div,
[data-baseweb="menu"], [data-baseweb="menu"] ul,
[data-baseweb="menu"] li {
    background: #fff !important;
    color: #2a241c !important;
}
[data-baseweb="select"] > div { border-color: #d8cdb5 !important; border-radius: 2px !important; }
[data-baseweb="select"] svg { color: #9c7535 !important; }
[data-baseweb="menu"] li:hover { background: #fdf6e8 !important; }

/* ── 多选 tag ── */
[data-baseweb="tag"] {
    background: rgba(201,163,92,.15) !important;
    color: #9c7535 !important;
    border-radius: 2px !important;
}

/* ── 状态小点 ── */
.status-row { display:flex;align-items:center;gap:8px;padding:5px 0;font-size:12px;color:#5f574b;border-bottom:1px solid #ede5d0 }
.dot-on  { width:6px;height:6px;border-radius:50%;background:#22c55e;flex-shrink:0 }
.dot-off { width:6px;height:6px;border-radius:50%;background:#d1c5b0;flex-shrink:0 }
.dot-warn{ width:6px;height:6px;border-radius:50%;background:#f59e0b;flex-shrink:0 }

/* ── 主内容区 ── */
.block-container { padding-top: 2rem !important; max-width: 1080px !important; background: #f7f3ec !important; }

/* ── 标题 ── */
h1 { font-family:"Noto Serif SC",serif !important; font-size:24px !important; font-weight:700 !important;
     color:#1a1510 !important; border-bottom:1px solid #e0d5be; padding-bottom:10px; margin-bottom:18px !important; }
h2 { font-family:"Noto Serif SC",serif !important; font-size:18px !important; font-weight:700 !important; color:#2a241c !important; }
h3 { font-family:"Noto Serif SC",serif !important; font-size:15px !important; font-weight:700 !important; color:#3a3028 !important; }

/* ── 主按钮 ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(100deg,#8a6a35 0%,#c9a35c 55%,#e8c97a 100%) !important;
    color: #fff !important; border: none !important; font-weight:600 !important;
    letter-spacing:.08em !important; border-radius:2px !important;
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.07) !important; }
.stButton > button:not([kind="primary"]) {
    border:1px solid #c9a35c !important; color:#9c7535 !important;
    background:#fff !important; border-radius:2px !important;
}
.stButton > button:not([kind="primary"]):hover { background:#fdf6e8 !important; }

/* ── 展开面板 ── */
[data-testid="stExpander"] { border:1px solid #e0d5be !important; border-radius:2px !important; background:#fff !important; }
[data-testid="stExpander"]:hover { border-color:#c9a35c !important; }
[data-testid="stExpander"] summary { color:#3a3028 !important; font-weight:500 !important; font-size:13px !important; }
[data-testid="stExpander"] > div { background:#fff !important; }

/* ── 指标卡 ── */
[data-testid="stMetric"] { background:#fff !important; border:1px solid #e0d5be !important; border-radius:2px !important; padding:14px !important; }
[data-testid="stMetricValue"] { color:#9c7535 !important; font-family:"Noto Serif SC",serif !important; font-size:26px !important; }
[data-testid="stMetricLabel"] { color:#77716a !important; font-size:11px !important; letter-spacing:.1em !important; }

/* ── 分隔线 ── */
hr { border:none !important; border-top:1px solid #e0d5be !important; margin:12px 0 !important; }

/* ── 标签页 ── */
.stTabs [data-baseweb="tab-list"] { border-bottom:1px solid #e0d5be !important; gap:0 !important; background:transparent !important; }
.stTabs [data-baseweb="tab"] { border-radius:0 !important; font-size:13px !important; padding:8px 18px !important; color:#77716a !important; background:transparent !important; border:none !important; }
.stTabs [aria-selected="true"] { color:#9c7535 !important; border-bottom:2px solid #c9a35c !important; font-weight:600 !important; }
[data-testid="stTabsContent"] { background:#fff !important; border:1px solid #e0d5be !important; border-top:none !important; padding:16px !important; }

/* ── 输入框 ── */
.stTextInput input, .stTextArea textarea {
    border-radius:2px !important; border-color:#d8cdb5 !important;
    background:#fff !important; color:#2a241c !important; font-size:14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color:#c9a35c !important; box-shadow:0 0 0 2px rgba(201,163,92,.15) !important;
}

/* ── 通知 ── */
[data-testid="stAlert"] { border-radius:2px !important; font-size:13px !important; }
div[data-testid="stAlert"][kind="info"]    { background:#fdf9f0 !important; border-left:3px solid #c9a35c !important; }
div[data-testid="stAlert"][kind="success"] { background:#f0fdf4 !important; border-left:3px solid #22c55e !important; }
div[data-testid="stAlert"][kind="warning"] { background:#fffbeb !important; border-left:3px solid #f59e0b !important; }
div[data-testid="stAlert"][kind="error"]   { background:#fef2f2 !important; border-left:3px solid #ef4444 !important; }

/* ── slider ── */
[data-testid="stSlider"] [data-testid="stThumbValue"] { background:#9c7535 !important; color:#fff !important; }

/* ── scrollbar ── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#f0ebe0; }
::-webkit-scrollbar-thumb { background:#c9a35c; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# 初始化
def init_modules(_user_id):
    """初始化各模块（传入用户ID）"""
    collector = TopicCollector(user_id=_user_id)
    generator = ContentGenerator(user_id=_user_id)
    publisher = ContentPublisher(user_id=_user_id)
    return collector, generator, publisher

# 初始化用户管理器
user_manager = UserManager()
users = user_manager.get_active_users()

# 侧边栏品牌标题
st.sidebar.markdown("""
<div style="padding:16px 0 14px; border-bottom:1px solid #e0d5be; margin-bottom:14px">
  <div style="display:flex;align-items:center;gap:8px">
    <div style="width:28px;height:28px;border-radius:6px;background:linear-gradient(135deg,#FFBD47,#F1A12A);display:flex;align-items:center;justify-content:center;flex-shrink:0">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="white" stroke-width="2" fill="none"/>
        <path d="M9 22V12h6v10" stroke="white" stroke-width="2"/>
      </svg>
    </div>
    <div>
      <div style="font-weight:700;font-size:14px;color:#1a1510;letter-spacing:.04em;line-height:1.2">傲客内容工厂</div>
      <div style="font-size:10px;letter-spacing:.18em;color:#9c7535;text-transform:uppercase;margin-top:1px">Content Studio</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# 用户选择器（精简版）
if users:
    user_options = {u['id']: u['name'] for u in users}
    selected_user_id = st.sidebar.selectbox(
        "导师",
        options=list(user_options.keys()),
        format_func=lambda x: user_options[x],
        key='user_selector',
        index=list(user_options.keys()).index(user_manager.get_default_user()) if user_manager.get_default_user() in user_options else 0
    )
    UserContext.set_current_user(selected_user_id)
    current_user = user_manager.get_user(selected_user_id)
else:
    st.sidebar.error("❌ 未找到用户配置")
    selected_user_id = 'dr_k'

# 初始化模块
collector, generator, publisher = init_modules(selected_user_id)

# 今日统计数据
_topics_count = len(collector.get_latest_topics())
_drafts_count = len(list((DATA_DIR / 'users' / selected_user_id / 'drafts').glob('*.json'))) if (DATA_DIR / 'users' / selected_user_id / 'drafts').exists() else 0

# 侧边栏今日统计
st.sidebar.markdown(f"""
<div style="padding:8px 0 12px;border-bottom:1px solid #e0d5be;margin-bottom:12px">
  <div style="font-size:10px;letter-spacing:.18em;color:#9c7535;text-transform:uppercase;margin-bottom:10px">今日概况</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
    <div style="background:#fff;border:1px solid #e8dfc8;padding:10px 12px;border-radius:2px">
      <div style="font-size:22px;font-weight:700;color:#9c7535;font-family:'Noto Serif SC',serif;line-height:1">{_topics_count}</div>
      <div style="font-size:10px;color:#8c8476;margin-top:4px;letter-spacing:.06em">今日选题</div>
    </div>
    <div style="background:#fff;border:1px solid #e8dfc8;padding:10px 12px;border-radius:2px">
      <div style="font-size:22px;font-weight:700;color:#9c7535;font-family:'Noto Serif SC',serif;line-height:1">{_drafts_count}</div>
      <div style="font-size:10px;color:#8c8476;margin-top:4px;letter-spacing:.06em">草稿</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "",
    ["选题采集", "内容生成", "大纲审核", "发布管理", "系统设置", "用户配置", "知识库", "效果反馈"],
    format_func=lambda x: {
        "选题采集": "📋  选题采集",
        "内容生成": "✦  内容生成",
        "大纲审核": "◻  大纲审核",
        "发布管理": "↗  发布管理",
        "系统设置": "◎  系统设置",
        "用户配置": "⊙  用户配置",
        "知识库":   "◈  知识库",
        "效果反馈": "△  效果反馈",
    }[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="font-size:11px;color:#a19b90;padding:4px 0">
  <div style="margin-bottom:4px">导师：<strong style="color:#5f574b">{current_user['name'] if 'current_user' in dir() else 'K博士'}</strong></div>
  <div>模型：<strong style="color:#5f574b">sonnet-4-6</strong></div>
</div>
<div style="margin-top:10px">
  <a href="https://app.awesomic.top/studio" target="_parent"
     style="font-size:11px;color:#9c7535;text-decoration:none;border:1px solid #d8cdb5;padding:5px 10px;border-radius:2px;display:inline-block;letter-spacing:.04em">
    ← 返回工作台
  </a>
</div>
""", unsafe_allow_html=True)


# ==================== 页面1：选题采集 ====================
if page == "选题采集":
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

    # 手动添加选题
    with st.expander("✏️ 手动添加选题"):
        with st.form("manual_topic_form"):
            manual_title = st.text_input("标题 *", placeholder="输入选题标题")
            manual_excerpt = st.text_area("摘要", placeholder="简单描述一下这个选题", height=80)
            manual_url = st.text_input("原文链接", placeholder="https://...")
            manual_source = st.text_input("来源", placeholder="例如：微信、朋友推荐", value="手动添加")
            submitted = st.form_submit_button("➕ 添加到选题列表", type="primary")

            if submitted and manual_title:
                from modules.utils import load_json, save_json
                from datetime import datetime
                latest_path = collector.topics_dir / 'latest.json'
                data = load_json(latest_path) if latest_path.exists() else {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'total_count': 0,
                    'high_score_count': 0,
                    'topics': []
                }
                new_topic = {
                    'title': manual_title,
                    'excerpt': manual_excerpt,
                    'url': manual_url,
                    'source': manual_source,
                    'collected_at': datetime.now().isoformat()
                }
                data['topics'].insert(0, new_topic)
                data['total_count'] = len(data['topics'])
                save_json(data, latest_path)
                st.success("✅ 已添加！")
                st.rerun()

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
                min_score = st.slider("最低分数", 0, 50, 0, help="设置为0可显示所有选题（包括手动添加的）")
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
        # 修复：只有当选题有分数时才应用分数过滤
        if has_scores and min_score > 0:
            filtered_topics = [t for t in topics if t.get('total_score', 0) >= min_score]
        else:
            filtered_topics = topics.copy()

        if source_filter:
            filtered_topics = [t for t in filtered_topics if t['source'] in source_filter]

        if sort_by == "总分" and has_scores:
            filtered_topics.sort(key=lambda x: x.get('total_score', 0), reverse=True)

        st.markdown(f"### 📋 选题列表（共 {len(filtered_topics)} 个）")

        # 显示选题卡片
        for i, topic in enumerate(filtered_topics):
            # 检查是否有打分
            has_score = 'total_score' in topic
            score_text = f"(总分: {topic['total_score']}/50)" if has_score else ""

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
elif page == "内容生成":
    st.title("✍️ 内容生成工坊")

    # 检查是否有选中的选题
    if 'selected_topic' not in st.session_state:
        st.warning("⚠️ 请先在「选题采集」页面选择一个选题")

        # 显示最近的草稿
        st.markdown("### 📝 最近的草稿")
        drafts = generator.get_latest_drafts(5)

        if drafts:
            for i, draft in enumerate(drafts):
                with st.expander(f"{draft['topic']['title'][:50]}... ({draft['generated_at'][:10]})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**选题：** {draft['topic']['title']}")
                        st.markdown(f"**生成时间：** {draft['generated_at']}")
                        st.markdown(f"**观点：** {draft.get('user_opinion', '无')[:100]}...")

                        # 显示已生成的格式
                        formats = list(draft['contents'].keys())
                        format_names = [{'video': '视频号', 'article': '公众号', 'moments': '朋友圈', 'xiaohongshu': '小红书', 'book': '书稿'}.get(f, f) for f in formats]
                        st.markdown(f"**格式：** {', '.join(format_names)}")

                    with col2:
                        # 添加"打开编辑"按钮
                        if st.button("📝 打开编辑", key=f"open_draft_{i}", use_container_width=True):
                            st.session_state['selected_topic'] = draft['topic']
                            st.session_state['current_draft'] = draft
                            st.success("✅ 已加载草稿")
                            st.rerun()
        else:
            st.info("暂无草稿")

    else:
        topic = st.session_state['selected_topic']

        st.markdown(f"### 📌 当前选题")
        st.info(f"**{topic['title']}** (总分: {topic.get('total_score', topic.get('score', 0))}/50)")

        # 用户输入观点
        user_opinion = st.text_area(
            "💭 写下你的核心观点（一句话）",
            placeholder="例如：我认为AI时代最重要的是培养孩子的创造力和批判性思维...",
            height=100
        )

        # 视频号灵魂四问
        with st.expander("🎯 视频号灵魂四问（高信息密度文案必填）", expanded=False):
            st.caption("决定整体观点方向和人群，填写后生成的视频号文案信息密度更高、更有针对性")
            col_a, col_b = st.columns(2)
            with col_a:
                soul_audience = st.text_input("1. 说给谁听", placeholder="例如：有孩子在读高中、焦虑留学的父母")
                soul_impact = st.text_input("3. 产生什么影响", placeholder="例如：让父母从焦虑选校转向关注孩子能力培养")
            with col_b:
                soul_viewpoint = st.text_input("2. 什么观点", placeholder="例如：选校不重要，选对方向才重要")
                soul_opposition = st.text_input("4. 对立面", placeholder="例如：普通家长只盯着学校排名")

            st.markdown("**进阶输入（可选，显著提升文案质量）**")
            reference_script = st.text_area("范文（决定内容结构和语言风格）", placeholder="粘贴一篇你认为写得好的视频号文案...", height=120)
            recording_transcript = st.text_area("录音逐字稿（提炼案例和方法论）", placeholder="粘贴你的录音逐字稿，AI会从中提炼信息点放入对应位置...", height=120)
            opening_line = st.text_area("开头（一字不改保留）", placeholder="粘贴你想要的开头，AI会原样保留...", height=60)

            soul_questions = {
                'audience': soul_audience,
                'viewpoint': soul_viewpoint,
                'impact': soul_impact,
                'opposition': soul_opposition
            } if any([soul_audience, soul_viewpoint, soul_impact, soul_opposition]) else None

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
                        results = generator.generate_all_formats(
                            topic, user_opinion,
                            selected_formats=selected_formats,
                            soul_questions=soul_questions if 'soul_questions' in locals() else None,
                            reference_script=reference_script if 'reference_script' in locals() else "",
                            recording_transcript=recording_transcript if 'recording_transcript' in locals() else "",
                            opening_line=opening_line if 'opening_line' in locals() else ""
                        )
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

            # 添加反馈和重新生成功能
            with st.expander("💬 对生成效果不满意？提供反馈并重新生成"):
                feedback_text = st.text_area(
                    "请描述你希望如何改进",
                    placeholder="例如：\n- 语气太正式，希望更口语化\n- 缺少具体案例，希望增加真实故事\n- 标题不够吸引人\n- 内容太长，希望精简到1500字以内",
                    height=120,
                    key="regenerate_feedback"
                )

                col_regen1, col_regen2 = st.columns([1, 3])
                with col_regen1:
                    if st.button("🔄 重新生成", type="primary", disabled=not feedback_text, use_container_width=True):
                        with st.spinner("正在根据你的反馈重新生成..."):
                            try:
                                # 将反馈添加到用户观点中
                                original_opinion = draft.get('user_opinion', '')
                                enhanced_opinion = f"{original_opinion}\n\n【修改要求】\n{feedback_text}"

                                # 重新生成
                                topic = st.session_state['selected_topic']
                                selected_formats = list(draft['contents'].keys())
                                results = generator.generate_all_formats(topic, enhanced_opinion, selected_formats=selected_formats)

                                st.session_state['current_draft'] = results
                                st.success("✅ 重新生成完成！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 重新生成失败: {str(e)}")

                with col_regen2:
                    st.info("💡 提示：描述越具体，生成效果越好")

            st.markdown("---")

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

                            # 快速复制按钮
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                if st.button(f"📋 复制", key=f"copy_{format_key}", use_container_width=True):
                                    st.session_state[f'show_copy_{format_key}'] = True
                                    st.rerun()

                            if st.session_state.get(f'show_copy_{format_key}', False):
                                st.text_area(
                                    "复制以下内容",
                                    value=content_data['content'],
                                    height=200,
                                    key=f"copy_area_{format_key}"
                                )
                                st.info("💡 请选中并复制上方内容（Ctrl+A, Ctrl+C）")
                                if st.button("✅ 关闭", key=f"close_copy_{format_key}"):
                                    st.session_state[f'show_copy_{format_key}'] = False
                                    st.rerun()

                            st.markdown("---")

                            # 编辑功能
                            with st.expander("✏️ 编辑内容"):
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
                                        st.success("✅ 已保存修改")
                                        st.rerun()

            # 发布选项
            st.markdown("---")
            st.markdown("### 📤 发布选项")

            # 格式选择
            format_options_map = {
                'video': '🎬 视频号',
                'article': '📰 公众号',
                'moments': '💬 朋友圈',
                'xiaohongshu': '📱 小红书',
                'book': '📚 书稿'
            }

            available_formats = list(draft['contents'].keys())
            publish_formats = st.multiselect(
                "选择要发布的格式",
                options=available_formats,
                default=available_formats,
                format_func=lambda x: format_options_map.get(x, x)
            )

            # 发布目标选择
            publish_target = st.radio(
                "发布到",
                options=["Notion 数据库", "导出文件", "复制到剪贴板"],
                horizontal=True
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📤 开始发布", type="primary", use_container_width=True, disabled=not publish_formats):
                    with st.spinner("正在发布..."):
                        try:
                            if publish_target == "Notion 数据库":
                                # 只发布选中的格式
                                filtered_draft = draft.copy()
                                filtered_draft['contents'] = {
                                    k: v for k, v in draft['contents'].items()
                                    if k in publish_formats
                                }
                                results = publisher.publish_draft(filtered_draft)
                                st.success("✅ 发布到 Notion 成功！")
                                st.json(results)

                            elif publish_target == "导出文件":
                                # 检查 export_files 是否支持 formats 参数
                                try:
                                    exported = publisher.export_files(draft, formats=publish_formats)
                                except TypeError:
                                    # 如果不支持，使用原方法
                                    exported = publisher.export_files(draft)
                                st.success(f"✅ 已导出 {len(exported)} 个文件")
                                for file_path in exported:
                                    st.markdown(f"- `{file_path}`")

                            elif publish_target == "复制到剪贴板":
                                # 合并选中格式的内容
                                combined_content = ""
                                for fmt in publish_formats:
                                    if fmt in draft['contents']:
                                        combined_content += f"\n\n{'='*50}\n"
                                        combined_content += f"{format_options_map.get(fmt, fmt)}\n"
                                        combined_content += f"{'='*50}\n\n"
                                        combined_content += draft['contents'][fmt]['content']

                                st.text_area("📋 复制以下内容", combined_content, height=300, key="copy_content")
                                st.info("💡 请手动选中并复制上方内容（Ctrl+A, Ctrl+C 或 Cmd+A, Cmd+C）")

                        except Exception as e:
                            st.error(f"❌ 发布失败: {str(e)}")

            with col2:
                if st.button("👁️ 预览效果", use_container_width=True):
                    st.session_state['show_preview'] = not st.session_state.get('show_preview', False)
                    st.rerun()

            with col3:
                if st.button("🗑️ 清空当前草稿", use_container_width=True):
                    if 'current_draft' in st.session_state:
                        del st.session_state['current_draft']
                    if 'selected_topic' in st.session_state:
                        del st.session_state['selected_topic']
                    if 'show_preview' in st.session_state:
                        del st.session_state['show_preview']
                    st.rerun()

            # ── 生图 + 公众号草稿箱 ──
            st.markdown("---")
            st.markdown("### 🎨 生图 & 一键推草稿")

            img_col, mp_col = st.columns(2)

            with img_col:
                st.markdown("**封面图生成**")
                img_platform = st.selectbox(
                    "平台",
                    ["wechat", "xiaohongshu", "video"],
                    format_func=lambda x: {"wechat": "公众号", "xiaohongshu": "小红书", "video": "视频号"}[x],
                    key="img_platform"
                )
                img_style = st.selectbox(
                    "风格",
                    ["educational", "modern", "minimalist", "colorful"],
                    format_func=lambda x: {"educational": "教育简洁", "modern": "现代渐变", "minimalist": "极简", "colorful": "小红书活泼"}[x],
                    key="img_style"
                )
                if st.button("🎨 生成封面图", use_container_width=True):
                    with st.spinner("生成中，约 10-20 秒…"):
                        try:
                            from modules.visual.image_generator import ImageGenerator
                            ig = ImageGenerator()
                            if not ig.available:
                                st.error("❌ 未配置图片 API key")
                            else:
                                img_path = ig.generate_cover_image(
                                    title=topic['title'],
                                    style=img_style,
                                    platform=img_platform
                                )
                                if img_path:
                                    st.session_state['generated_image'] = img_path
                                    st.success("✅ 封面图生成成功")
                                    st.rerun()
                                else:
                                    st.error("❌ 生成失败，请检查 API 是否支持 images 接口")
                        except Exception as e:
                            st.error(f"❌ 生图出错: {e}")

                if st.session_state.get('generated_image'):
                    img_path = st.session_state['generated_image']
                    if Path(img_path).exists():
                        st.image(img_path, caption="封面图预览", use_container_width=True)
                        with open(img_path, 'rb') as f:
                            st.download_button("⬇️ 下载封面图", f, file_name=Path(img_path).name, mime="image/png")

            with mp_col:
                st.markdown("**推送公众号草稿箱**")
                import os as _os
                has_mp = bool(_os.getenv('WECHAT_APPID') and _os.getenv('WECHAT_SECRET'))
                if not has_mp:
                    st.warning("⚠️ 未配置公众号 AppID/Secret，请到「用户配置」页面填写")
                else:
                    use_cover = st.checkbox("附带封面图", value=bool(st.session_state.get('generated_image')))
                    if st.button("📨 推送到草稿箱", type="primary", use_container_width=True):
                        article_content = draft['contents'].get('article', {}).get('content', '')
                        if not article_content:
                            st.error("❌ 请先生成「公众号」格式内容")
                        else:
                            with st.spinner("推送中…"):
                                try:
                                    from modules.publisher.wechat_mp_client import WechatMPClient
                                    mp = WechatMPClient()
                                    cover = st.session_state.get('generated_image') if use_cover else None
                                    result = mp.push_article_draft(
                                        title=topic['title'],
                                        markdown_content=article_content,
                                        image_path=cover
                                    )
                                    if result['success']:
                                        st.success(f"✅ 草稿已推送！media_id: {result['media_id']}")
                                    else:
                                        st.error(f"❌ 推送失败: {result.get('error')}")
                                except Exception as e:
                                    st.error(f"❌ 推送出错: {e}")

            # 预览功能
            if st.session_state.get('show_preview', False):
                st.markdown("---")
                st.markdown("### 👁️ 内容预览")

                preview_format = st.selectbox(
                    "选择预览格式",
                    options=publish_formats if publish_formats else available_formats,
                    format_func=lambda x: format_options_map.get(x, x)
                )

                if preview_format in draft['contents']:
                    content = draft['contents'][preview_format]['content']

                    # 根据格式渲染预览
                    if preview_format == 'article':
                        # 公众号样式预览
                        st.markdown(f"""
                        <div style="
                            background: white;
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
                            max-width: 800px;
                            margin: 20px auto;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            line-height: 1.8;
                            color: #333;
                        ">
                            {content.replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

                    elif preview_format == 'xiaohongshu':
                        # 小红书样式预览
                        st.markdown(f"""
                        <div style="
                            background: #fff;
                            padding: 20px;
                            border-radius: 12px;
                            max-width: 600px;
                            margin: 20px auto;
                            font-size: 15px;
                            line-height: 1.6;
                            color: #333;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        ">
                            {content.replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

                    elif preview_format == 'moments':
                        # 朋友圈样式预览
                        st.markdown(f"""
                        <div style="
                            background: #f7f7f7;
                            padding: 15px;
                            border-radius: 8px;
                            max-width: 500px;
                            margin: 20px auto;
                            font-size: 14px;
                            line-height: 1.5;
                            color: #333;
                        ">
                            {content.replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        # 默认预览
                        st.markdown(content)



# ==================== 页面2b：大纲审核 ====================
elif page == "大纲审核":
    spec = importlib.util.spec_from_file_location(
        "outline_page",
        Path(__file__).parent / "pages" / "1_大纲审核.py"
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    except Exception as e:
        st.error(f"加载大纲审核页失败: {e}")


# ==================== 页面3：发布管理 ====================
elif page == "发布管理":
    st.title("📤 发布管理")

    # 显示发布记录（使用当前用户的数据）
    user_data_dir = UserContext.get_current_data_dir()
    record_file = user_data_dir / 'published' / 'publish_records.json'

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
elif page == "系统设置":
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
    st.markdown(f'<div style="background:#fff;border:1px solid #e0d5be;border-radius:2px;padding:10px 14px;font-family:monospace;font-size:13px;color:#3a3028">{DATA_DIR}</div>', unsafe_allow_html=True)

    st.markdown("### 📊 统计信息")
    col1, col2, col3 = st.columns(3)

    # 使用当前用户的数据目录
    user_data_dir = UserContext.get_current_data_dir()

    with col1:
        topics_count = len(list((user_data_dir / 'topics').glob('*.json')))
        st.metric("选题文件", topics_count)

    with col2:
        drafts_count = len(list((user_data_dir / 'drafts').glob('*.json')))
        st.metric("草稿文件", drafts_count)

    with col3:
        published_count = len(list((user_data_dir / 'published').glob('*.txt')))
        st.metric("已发布文件", published_count)


# ==================== 页面5：用户配置 ====================
elif page == "用户配置":
    import importlib, sys
    # 动态加载 pages/8_用户配置管理.py 的内容
    spec = importlib.util.spec_from_file_location(
        "user_config_page",
        Path(__file__).parent / "pages" / "8_用户配置管理.py"
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    except Exception as e:
        st.error(f"加载用户配置页失败: {e}")


# ==================== 页面6：知识库 ====================
elif page == "知识库":
    spec = importlib.util.spec_from_file_location(
        "kb_page",
        Path(__file__).parent / "pages" / "6_知识库管理.py"
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    except Exception as e:
        st.error(f"加载知识库页失败: {e}")


# ==================== 页面7：效果反馈 ====================
elif page == "效果反馈":
    spec = importlib.util.spec_from_file_location(
        "feedback_page",
        Path(__file__).parent / "pages" / "7_效果反馈.py"
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    except Exception as e:
        st.error(f"加载效果反馈页失败: {e}")
