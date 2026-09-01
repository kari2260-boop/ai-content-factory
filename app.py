"""
K博士 AI 内容工厂 - Streamlit 管理后台
"""
import streamlit as st
import json
import re
from datetime import datetime
from pathlib import Path
from PIL import Image

from modules.collector.main import TopicCollector
from modules.generator.main import ContentGenerator
from modules.publisher.main import ContentPublisher
from modules.utils import DATA_DIR, setup_logger
from modules.user.manager import UserManager
from modules.user.context import UserContext

logger = setup_logger('app', 'app.log')


def parse_xiaohongshu_cards(content: str, topic_title: str = ""):
    """把小红书文案拆成卡片，便于做图文卡预览和单卡配图。"""
    if not content:
        return []

    raw_lines = [line.strip() for line in content.splitlines()]
    sections = []
    current_title = ""
    current_body = []

    def flush():
        nonlocal current_title, current_body
        body = "\n".join([line for line in current_body if line]).strip()
        if current_title or body:
            sections.append({
                "title": current_title.strip(),
                "body": body
            })
        current_title = ""
        current_body = []

    heading_patterns = [
        r"^#{1,3}\s*(.+)$",
        r"^###\s*(.+)$",
        r"^0?1[\.、]?\s*(.+)$",
        r"^0?2[\.、]?\s*(.+)$",
        r"^0?3[\.、]?\s*(.+)$",
        r"^0?4[\.、]?\s*(.+)$",
        r"^0?5[\.、]?\s*(.+)$",
        r"^封面标题[:：]?\s*(.+)$",
        r"^结尾[:：]?\s*(.+)$",
    ]

    for line in raw_lines:
        if not line:
            continue
        matched = None
        for pattern in heading_patterns:
            m = re.match(pattern, line)
            if m:
                matched = m.group(1).strip("：: ")
                break
        if matched:
            flush()
            current_title = matched
            continue
        if line.startswith("#"):
            flush()
            current_title = line.lstrip("# ").strip()
            continue
        current_body.append(line)

    flush()

    cleaned = []
    for item in sections:
        title = item["title"].strip()
        body = item["body"].strip()
        if not title and not body:
            continue
        cleaned.append({
            "title": title or topic_title,
            "body": body
        })

    if not cleaned:
        paras = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
        for idx, para in enumerate(paras[:6], 1):
            cleaned.append({
                "title": f"{idx:02d}",
                "body": para
            })

    slots = ["封面", "误区", "核心判断", "方法", "案例/清单", "总结"]
    cards = []
    for idx, item in enumerate(cleaned[:6]):
        cards.append({
            "slot": slots[idx] if idx < len(slots) else f"第{idx + 1}张",
            "title": item["title"][:24] if item["title"] else slots[idx],
            "body": item["body"]
        })
    return cards

# 页面配置
app_icon_path = Path(__file__).resolve().parent / "assets" / "openclaw-icon.png"
page_icon = Image.open(app_icon_path) if app_icon_path.exists() else "🏭"
st.set_page_config(
    page_title="K博士 AI 内容工厂",
    page_icon=page_icon,
    layout="wide"
)

# 初始化
@st.cache_resource
def init_modules(_user_id, cache_version: str = "collect_fast_v2"):
    """初始化各模块（传入用户ID）"""
    collector = TopicCollector(user_id=_user_id)
    generator = ContentGenerator(user_id=_user_id)
    publisher = ContentPublisher(user_id=_user_id)
    return collector, generator, publisher

# 初始化用户管理器
user_manager = UserManager()
users = user_manager.get_active_users()

# 侧边栏
st.sidebar.title("🏭 AI 内容工厂")

# 用户选择器
if users:
    user_options = {u['id']: u['name'] for u in users}
    selected_user_id = st.sidebar.selectbox(
        "👤 选择用户",
        options=list(user_options.keys()),
        format_func=lambda x: user_options[x],
        key='user_selector',
        index=list(user_options.keys()).index(user_manager.get_default_user()) if user_manager.get_default_user() in user_options else 0
    )

    # 设置当前用户
    UserContext.set_current_user(selected_user_id)
    current_user = user_manager.get_user(selected_user_id)

    st.sidebar.info(f"当前用户：{current_user['name']}")
else:
    st.sidebar.error("❌ 未找到用户配置")
    selected_user_id = 'dr_k'

st.sidebar.markdown("---")

# 初始化模块（使用选中的用户ID）
collector, generator, publisher = init_modules(selected_user_id, cache_version="collect_fast_v2")

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
        st.sidebar.info("  └─ 文本生成可用")
    else:
        st.sidebar.warning("⚠️ Gemini API (未配置)")
except:
    st.sidebar.warning("⚠️ Gemini API (未配置)")

# OpenClaw 状态
try:
    from modules.generator.openclaw_bridge import OpenClawBridge
    openclaw = OpenClawBridge()
    openclaw_status = openclaw.get_status()
    if openclaw_status.get("gateway_reachable"):
        st.sidebar.success("✅ OpenClaw")
        st.sidebar.info("  └─ 网关可用")
    elif openclaw_status.get("service_running"):
        st.sidebar.warning("⚠️ OpenClaw (已启动但不可达)")
        st.sidebar.info(f"  └─ {openclaw_status.get('detail', '')}")
    else:
        st.sidebar.warning("⚠️ OpenClaw (未运行)")
        st.sidebar.info(f"  └─ {openclaw_status.get('detail', '')}")
except:
    st.sidebar.warning("⚠️ OpenClaw (未运行)")

# Notion 状态
try:
    from modules.publisher.notion_client import NotionClient
    notion = NotionClient()
    st.sidebar.success("✅ Notion API")
except:
    st.sidebar.error("❌ Notion API (未配置)")

# YouMind 状态
try:
    from modules.visual.youmind_client import YouMindClient
    youmind = YouMindClient()
    if youmind.available:
        st.sidebar.success("✅ YouMind API")
    else:
        st.sidebar.warning("⚠️ YouMind API (未配置)")
except:
    st.sidebar.warning("⚠️ YouMind API (未配置)")

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

    with st.expander("⚙️ 采集设置", expanded=False):
        col_mode1, col_mode2 = st.columns(2)
        with col_mode1:
            use_realtime_collect = st.checkbox(
                "优先使用 OpenClaw 实时采集",
                value=False,
                help="只在 OpenClaw 网关和模型都稳定时启用；否则直接走传统热点源。"
            )
        with col_mode2:
            use_ai_scoring = st.checkbox(
                "启用 AI 精细评分",
                value=False,
                help="会逐条调用 AI 打分，速度较慢；默认使用本地快速评分。"
            )

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🔄 开始采集选题", type="primary", use_container_width=True):
            status_box = st.empty()
            progress_bar = st.progress(0)
            try:
                if use_realtime_collect:
                    status_box.info("正在尝试 OpenClaw 实时采集，若超时会自动回退...")
                else:
                    status_box.info("正在快速采集热点源...")
                progress_bar.progress(20)

                if use_ai_scoring:
                    status_box.info("正在采集并进行 AI 精细评分，预计需要 1-3 分钟...")
                else:
                    status_box.info("正在采集并进行本地快速评分，通常几十秒内完成...")
                progress_bar.progress(45)

                try:
                    topics = collector.run(
                        use_openclaw=use_realtime_collect,
                        ai_scoring=use_ai_scoring
                    )
                except TypeError as e:
                    if "ai_scoring" not in str(e):
                        raise
                    logger.warning("采集器缓存为旧版本，降级使用兼容参数运行")
                    topics = collector.run(use_openclaw=use_realtime_collect)
                progress_bar.progress(100)
                status_box.success(f"✅ 采集完成！共获得 {len(topics)} 个选题")
                st.rerun()
            except Exception as e:
                progress_bar.empty()
                status_box.error(f"❌ 采集失败: {str(e)}")

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
                min_score = st.slider("最低分数", 0, 40, 0, help="设置为0可显示所有选题（包括手动添加的）")
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

        # AI 服务选择
        with st.expander("⚙️ 高级设置"):
            col_ai1, col_ai2 = st.columns(2)

            with col_ai1:
                # 内容生成服务选择
                ai_service = st.radio(
                    "内容生成服务",
                    options=["auto", "claude", "gemini"],
                    format_func=lambda x: {
                        "auto": "🤖 自动选择（推荐）",
                        "claude": "🔵 Claude",
                        "gemini": "🟢 Gemini"
                    }[x],
                    index=0,
                    help="自动选择优先级：OpenClaw > Claude > Gemini"
                )

            with col_ai2:
                # 图片生成服务选择
                image_service = st.radio(
                    "图片生成服务",
                    options=["auto", "skill", "openai", "youmind", "gemini", "flux"],
                    format_func=lambda x: {
                        "auto": "🤖 自动选择（本地生图Skill优先）",
                        "skill": "🖼️ 本地 gpt-image Skill",
                        "openai": "🔵 OpenAI 图片",
                        "youmind": "🎨 YouMind",
                        "gemini": "🟢 Gemini/Imagen",
                        "flux": "⚡ Flux"
                    }[x],
                    index=0,
                    help="自动选择优先级：本地 gpt-image Skill > OpenAI > YouMind > Gemini > Flux"
                )

                generate_images = st.checkbox(
                    "生成内容后自动补配图",
                    value=False,
                    help="建议先生成文字，再到各平台内容下方单独生成配图。自动补图会明显增加等待时间。"
                )
                image_format_options = {
                    'video': '🎬 视频号',
                    'article': '📰 公众号',
                    'moments': '💬 朋友圈',
                    'xiaohongshu': '📱 小红书'
                }
                auto_image_formats = []
                if generate_images:
                    available_image_formats = [fmt for fmt in selected_formats if fmt in image_format_options]
                    auto_image_formats = st.multiselect(
                        "自动补图范围",
                        options=available_image_formats,
                        default=['article'] if 'article' in available_image_formats else available_image_formats[:1],
                        format_func=lambda x: image_format_options[x],
                        help="每张图通常需要 40-90 秒，建议一次只选 1 个平台。"
                    )
                image_prompt_note = st.text_input(
                    "图片风格补充",
                    placeholder="可选：例如更高级、更教育行业、不要人物、留出标题空间",
                    help="会叠加到每个平台的图片提示词里"
                )
                overlay_text_on_image = st.checkbox(
                    "封面自动叠加标题文字",
                    value=True,
                    help="先生成无字底图，再用程序叠加中文标题和英文副标题，避免 AI 画错中文。"
                )
                image_subtitle = st.text_input(
                    "英文副标题",
                    value="AI × Education",
                    help="可留空；用于封面小字。"
                )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🚀 生成内容", type="primary", use_container_width=True, disabled=not user_opinion or not selected_formats):
                wait_hint = "正在生成内容，预计需要 2-3 分钟..."
                if generate_images and auto_image_formats:
                    wait_hint = f"正在生成内容，并自动补 {len(auto_image_formats)} 张配图；每张图通常需要 40-90 秒..."
                with st.spinner(wait_hint):
                    try:
                        # 根据用户选择设置 AI 服务
                        if ai_service == "claude" and not generator.claude.available:
                            st.warning("⚠️ Claude 不可用，自动切换到 Gemini")
                        elif ai_service == "gemini" and not generator.gemini.available:
                            st.warning("⚠️ Gemini 不可用，自动切换到 Claude")

                        results = generator.generate_all_formats(topic, user_opinion, selected_formats=selected_formats)

                        # 生成图片（如果勾选）
                        if generate_images:
                            from modules.visual.image_generator import ImageGenerator
                            img_gen = ImageGenerator()
                            platform_map = {
                                'video': 'video',
                                'article': 'wechat',
                                'xiaohongshu': 'xiaohongshu',
                                'moments': 'moments'
                            }

                            for format_key in auto_image_formats:
                                platform = platform_map.get(format_key)
                                if not platform:
                                    continue
                                try:
                                    content_for_image = results['contents'].get(format_key, {}).get('content', '')
                                    image_path = img_gen.generate_platform_cover(
                                        title=topic['title'],
                                        content=content_for_image,
                                        platform=platform,
                                        subtitle=image_subtitle,
                                        custom_prompt=image_prompt_note,
                                        preferred_provider=image_service,
                                        overlay_text=overlay_text_on_image
                                    )
                                    if image_path:
                                        if 'images' not in results:
                                            results['images'] = {}
                                        results['images'][format_key] = image_path
                                except Exception as e:
                                    logger.warning(f"图片生成失败 ({format_key}): {e}")

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

                                if generate_images:
                                    from modules.visual.image_generator import ImageGenerator
                                    img_gen = ImageGenerator()
                                    platform_map = {
                                        'video': 'video',
                                        'article': 'wechat',
                                        'xiaohongshu': 'xiaohongshu',
                                        'moments': 'moments'
                                    }
                                    for format_key in auto_image_formats:
                                        platform = platform_map.get(format_key)
                                        if not platform:
                                            continue
                                        content_for_image = results['contents'].get(format_key, {}).get('content', '')
                                        image_path = img_gen.generate_platform_cover(
                                            title=topic['title'],
                                            content=content_for_image,
                                            platform=platform,
                                            subtitle=image_subtitle,
                                            custom_prompt=image_prompt_note,
                                            preferred_provider=image_service,
                                            overlay_text=overlay_text_on_image
                                        )
                                        if image_path:
                                            results.setdefault('images', {})[format_key] = image_path

                                st.session_state['current_draft'] = results
                                st.success("✅ 重新生成完成！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 重新生成失败: {str(e)}")

                with col_regen2:
                    st.info("💡 提示：描述越具体，生成效果越好")

            st.markdown("---")

            format_options_map = {
                'video': '🎬 视频号',
                'article': '📰 公众号',
                'moments': '💬 朋友圈',
                'xiaohongshu': '📱 小红书',
                'book': '📚 书稿'
            }

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

                            platform_image = draft.get('images', {}).get(format_key)
                            if platform_image:
                                st.image(platform_image, caption=f"{format_options_map.get(format_key, format_key)} 配图", use_column_width=True)
                                st.caption(f"图片路径：`{platform_image}`")

                            if format_key == 'xiaohongshu':
                                xhs_cards = parse_xiaohongshu_cards(content_data['content'], topic['title'])
                                draft.setdefault('xhs_cards', xhs_cards)
                                st.markdown("### 📌 图文卡片拆解")

                                card_provider = st.selectbox(
                                    "卡片图片服务",
                                    options=["auto", "skill", "openai", "youmind", "gemini", "flux"],
                                    format_func=lambda x: {
                                        "auto": "自动选择（本地生图Skill优先）",
                                        "skill": "本地 gpt-image Skill",
                                        "openai": "OpenAI 图片",
                                        "youmind": "YouMind",
                                        "gemini": "Gemini/Imagen",
                                        "flux": "Flux"
                                    }[x],
                                    index=0,
                                    key=f"xhs_card_provider_{format_key}"
                                )

                                card_style = st.selectbox(
                                    "卡片风格",
                                    options=["knowledge_card", "editorial", "minimal"],
                                    format_func=lambda x: {
                                        "knowledge_card": "知识卡片",
                                        "editorial": "杂志封面",
                                        "minimal": "极简留白"
                                    }[x],
                                    index=0,
                                    key=f"xhs_card_style_{format_key}"
                                )

                                card_image_paths = draft.setdefault('xhs_card_images', {})
                                card_cols = st.columns(2)

                                for idx, card in enumerate(xhs_cards):
                                    with card_cols[idx % 2]:
                                        with st.container():
                                            st.markdown("---")
                                            st.markdown(f"**{card['slot']}**")
                                            st.markdown(f"### {card['title']}")
                                            st.markdown(card['body'])

                                            existing_card_image = card_image_paths.get(str(idx))
                                            if existing_card_image:
                                                st.image(existing_card_image, use_column_width=True)

                                            if st.button("生成这张卡配图", key=f"xhs_card_{idx}"):
                                                with st.spinner("正在生成卡片配图..."):
                                                    try:
                                                        from modules.visual.image_generator import ImageGenerator
                                                        img_gen = ImageGenerator()
                                                        prompt_note_map = {
                                                            "knowledge_card": "Use a high-end vertical knowledge-card style, dense but clean information, strong hierarchy, suitable for Xiaohongshu save/share behavior.",
                                                            "editorial": "Use a premium editorial poster style, clean but memorable, like a high-quality note cover.",
                                                            "minimal": "Use a minimalist vertical layout with strong negative space and one central visual metaphor."
                                                        }
                                                        card_custom_prompt = "\n".join([
                                                            prompt_note_map.get(card_style, ""),
                                                            f"Card slot: {card['slot']}",
                                                            f"Card title: {card['title']}",
                                                            f"Card body: {card['body']}",
                                                            "This is one card in a Xiaohongshu carousel. Make it visually consistent with the rest of the set.",
                                                        ]).strip()
                                                        image_path = img_gen.generate_platform_cover(
                                                            title=card['title'],
                                                            content=card['body'],
                                                            platform='xiaohongshu',
                                                            subtitle='',
                                                            custom_prompt=card_custom_prompt,
                                                            preferred_provider=card_provider,
                                                            overlay_text=True
                                                        )
                                                        if image_path:
                                                            card_image_paths[str(idx)] = image_path
                                                            st.session_state['current_draft'] = draft
                                                            try:
                                                                generator._save_draft(draft)
                                                            except Exception as save_err:
                                                                logger.warning(f"保存小红书卡片草稿失败: {save_err}")
                                                            st.success("✅ 已生成")
                                                            st.rerun()
                                                        else:
                                                            st.warning("没有生成成功，请检查图片 API 配置")
                                                    except Exception as e:
                                                        st.error(f"❌ 卡片配图生成失败: {str(e)}")

                                if st.button("生成整组图文卡", key=f"xhs_card_batch_{format_key}"):
                                    with st.spinner("正在生成整组卡片..."):
                                        try:
                                            from modules.visual.image_generator import ImageGenerator
                                            img_gen = ImageGenerator()
                                            prompt_note_map = {
                                                "knowledge_card": "Use a high-end vertical knowledge-card style, dense but clean information, strong hierarchy, suitable for Xiaohongshu save/share behavior.",
                                                "editorial": "Use a premium editorial poster style, clean but memorable, like a high-quality note cover.",
                                                "minimal": "Use a minimalist vertical layout with strong negative space and one central visual metaphor."
                                            }
                                            for idx, card in enumerate(xhs_cards):
                                                card_custom_prompt = "\n".join([
                                                    prompt_note_map.get(card_style, ""),
                                                    f"Card slot: {card['slot']}",
                                                    f"Card title: {card['title']}",
                                                    f"Card body: {card['body']}",
                                                    "This is one card in a Xiaohongshu carousel. Make it visually consistent with the rest of the set.",
                                                ]).strip()
                                                image_path = img_gen.generate_platform_cover(
                                                    title=card['title'],
                                                    content=card['body'],
                                                    platform='xiaohongshu',
                                                    subtitle='',
                                                    custom_prompt=card_custom_prompt,
                                                    preferred_provider=card_provider,
                                                    overlay_text=True
                                                )
                                                if image_path:
                                                    card_image_paths[str(idx)] = image_path
                                            st.session_state['current_draft'] = draft
                                            try:
                                                generator._save_draft(draft)
                                            except Exception as save_err:
                                                logger.warning(f"保存小红书整组卡片草稿失败: {save_err}")
                                            st.success("✅ 整组卡片已生成")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ 整组卡片生成失败: {str(e)}")

                            if format_key != 'book':
                                with st.expander("🖼️ 配图生成/重生成"):
                                    image_note = st.text_input(
                                        "这张图的补充要求",
                                        value="",
                                        key=f"image_note_{format_key}",
                                        placeholder="例如：更像公众号封面、不要人物、背景更干净"
                                    )
                                    visual_preset = st.selectbox(
                                        "视觉风格预设",
                                        options=["editorial", "documentary", "knowledge_card", "dark_tech", "minimal"],
                                        format_func=lambda x: {
                                            "editorial": "高级杂志/深度媒体",
                                            "documentary": "真实纪实/场景化",
                                            "knowledge_card": "知识卡片/信息图",
                                            "dark_tech": "暗黑科技/发布页",
                                            "minimal": "极简留白/克制"
                                        }[x],
                                        index=2 if format_key == 'xiaohongshu' else 0,
                                        key=f"visual_preset_{format_key}"
                                    )
                                    image_feedback = st.text_area(
                                        "对上一张图的反馈",
                                        value="",
                                        key=f"image_feedback_{format_key}",
                                        placeholder="可选：例如画面和文章主题不相关；人物太卡通；希望更像真实家庭学习场景；颜色太暗",
                                        height=90,
                                        help="有上一张图时，会优先按这个反馈修改；没有上一张图时，会把反馈加入新图提示词。"
                                    )
                                    edit_previous_image = st.checkbox(
                                        "优先基于上一张图修改",
                                        value=bool(platform_image),
                                        disabled=not bool(platform_image),
                                        key=f"edit_previous_image_{format_key}",
                                        help="目前本地 gpt-image Skill 支持图生图修改。"
                                    )
                                    overlay_enabled = st.checkbox(
                                        "叠加准确标题文字",
                                        value=True,
                                        key=f"overlay_enabled_{format_key}"
                                    )
                                    overlay_title = st.text_input(
                                        "封面中文标题",
                                        value=draft['topic']['title'],
                                        key=f"overlay_title_{format_key}",
                                        help="建议改短一点，封面更好看。"
                                    )
                                    overlay_subtitle = st.text_input(
                                        "封面英文副标题",
                                        value="AI × Education",
                                        key=f"overlay_subtitle_{format_key}",
                                        help="可留空。"
                                    )
                                    image_provider = st.selectbox(
                                        "图片服务",
                                        options=["auto", "skill", "openai", "youmind", "gemini", "flux"],
                                        format_func=lambda x: {
                                            "auto": "自动选择（本地生图Skill优先）",
                                            "skill": "本地 gpt-image Skill",
                                            "openai": "OpenAI 图片",
                                            "youmind": "YouMind",
                                            "gemini": "Gemini/Imagen",
                                            "flux": "Flux"
                                        }[x],
                                        key=f"image_provider_{format_key}"
                                    )

                                    if st.button("重新生成这张配图", key=f"regen_image_{format_key}"):
                                        with st.spinner("正在生成配图..."):
                                            try:
                                                from modules.visual.image_generator import ImageGenerator
                                                img_gen = ImageGenerator()
                                                platform_map = {
                                                    'video': 'video',
                                                    'article': 'wechat',
                                                    'xiaohongshu': 'xiaohongshu',
                                                    'moments': 'moments'
                                                }
                                                platform = platform_map.get(format_key)
                                                preset_prompt_map = {
                                                    "editorial": "Use a premium editorial magazine-cover style, sophisticated typography space, strong concrete metaphor, refined lighting and composition.",
                                                    "documentary": "Use realistic documentary photography style, believable environment, human-scale scene details, natural light, no staged stock-photo look.",
                                                    "knowledge_card": "Use a high-end knowledge-card / infographic cover style, one central symbolic object, clean geometric structure, restrained data-card details, no generated readable text.",
                                                    "dark_tech": "Use a restrained dark technology release-note style, black textured background, terminal/dashboard-like abstract structures, controlled neon green accents, no cheap cyberpunk.",
                                                    "minimal": "Use minimalist editorial style, large negative space, one precise symbolic object, quiet premium palette, no clutter."
                                                }
                                                combined_image_note = "\n".join(
                                                    part for part in [
                                                        preset_prompt_map.get(visual_preset, ""),
                                                        image_note
                                                    ] if part
                                                )
                                                image_path = img_gen.generate_platform_cover(
                                                    title=overlay_title,
                                                    content=content_data['content'],
                                                    platform=platform,
                                                    subtitle=overlay_subtitle,
                                                    custom_prompt=combined_image_note,
                                                    preferred_provider=image_provider,
                                                    overlay_text=overlay_enabled,
                                                    feedback=image_feedback,
                                                    source_image=platform_image if edit_previous_image else None
                                                )
                                                if image_path:
                                                    draft.setdefault('images', {})[format_key] = image_path
                                                    st.session_state['current_draft'] = draft
                                                    st.success("✅ 配图已更新")
                                                    st.rerun()
                                                else:
                                                    st.warning("没有生成成功，请检查图片 API 配置")
                                            except Exception as e:
                                                st.error(f"❌ 配图生成失败: {str(e)}")

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
                        xhs_cards = parse_xiaohongshu_cards(content, draft['topic']['title'])
                        st.markdown("### 📌 图文卡片预览")
                        for idx, card in enumerate(xhs_cards):
                            with st.container():
                                st.markdown("---")
                                st.markdown(f"**{card['slot']}**")
                                st.markdown(f"### {card['title']}")
                                st.markdown(card['body'])

                        st.markdown("### 📄 原始文案")
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



# ==================== 页面3：发布管理 ====================
elif page == "📤 发布管理":
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
        openclaw_status = generator.openclaw.get_status()
        if openclaw_status.get("gateway_reachable"):
            st.success("✅ 运行中")
            st.caption("Gateway 可达")
        elif openclaw_status.get("service_running"):
            st.warning("⚠️ 已启动但不可达")
            st.caption(openclaw_status.get("detail", ""))
        else:
            st.warning("⚠️ 未运行")
            st.caption(openclaw_status.get("detail", ""))

    st.markdown("---")
    st.markdown("### 📁 数据目录")
    st.code(str(DATA_DIR))

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
