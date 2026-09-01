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
from modules.user.manager import UserManager
from modules.user.context import UserContext

# 页面配置
st.set_page_config(
    page_title="K博士 AI 内容工厂",
    page_icon="🏭",
    layout="wide"
)

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
collector, generator, publisher = init_modules(selected_user_id)

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
        if generator.openclaw.available:
            st.success("✅ 运行中")
        else:
            st.warning("⚠️ 未运行")

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
