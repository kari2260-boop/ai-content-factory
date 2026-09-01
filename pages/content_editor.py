"""
内容编辑器 - 查看和编辑已生成的内容
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="内容编辑器 - K博士 AI 内容工厂",
    page_icon="✏️",
    layout="wide"
)

# 样式
st.markdown("""
<style>
    .content-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .format-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 5px;
        font-weight: bold;
    }
    .badge-video { background: #FF6B6B; color: white; }
    .badge-article { background: #4ECDC4; color: white; }
    .badge-moments { background: #95E1D3; color: white; }
    .badge-xiaohongshu { background: #FF6B9D; color: white; }
    .badge-book { background: #C7CEEA; color: white; }
    .stat-box {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("✏️ 内容编辑器")
st.markdown("查看、编辑和管理已生成的内容")

# 加载草稿列表
drafts_dir = Path("/Users/k/ai-content-factory/data/drafts")
draft_files = sorted(drafts_dir.glob("draft_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

if not draft_files:
    st.warning("📭 暂无草稿内容")
    st.info("请先在「内容生成」页面生成内容")
    st.stop()

# 视图模式选择
view_mode = st.radio("查看模式", ["📋 列表视图", "✏️ 编辑视图"], horizontal=True)

if view_mode == "📋 列表视图":
    # 列表视图 - 显示所有草稿
    st.markdown("---")

    # 搜索和筛选
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 搜索标题", "")
    with col2:
        format_filter = st.multiselect(
            "📋 筛选格式",
            ["视频号", "公众号", "朋友圈", "小红书", "书稿"],
            default=[]
        )

    st.markdown(f"### 📚 草稿列表 (共 {len(draft_files)} 个)")

    format_map = {
        'video': '视频号',
        'article': '公众号',
        'moments': '朋友圈',
        'xiaohongshu': '小红书',
        'book': '书稿'
    }

    # 显示所有草稿
    for idx, draft_file in enumerate(draft_files, 1):
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                draft = json.load(f)

            title = draft.get('topic', {}).get('title', '未知标题')
            timestamp = draft.get('timestamp', '')
            contents = draft.get('contents', {})

            # 搜索过滤
            if search_query and search_query.lower() not in title.lower():
                continue

            # 格式过滤
            if format_filter:
                has_format = any(format_map.get(k) in format_filter for k in contents.keys())
                if not has_format:
                    continue

            # 显示草稿卡片
            with st.container():
                st.markdown(f"""
                <div class="content-card">
                    <h4>{idx}. {title}</h4>
                    <p style="color: #666; font-size: 0.9em;">📅 {timestamp}</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    # 显示格式标签
                    formats = []
                    for key, name in format_map.items():
                        if key in contents:
                            formats.append(name)
                    st.markdown(f"**格式:** {', '.join(formats)}")

                with col2:
                    # 显示字数统计
                    total_words = 0
                    for content_data in contents.values():
                        if isinstance(content_data, dict):
                            content = content_data.get('content', '')
                        else:
                            content = content_data
                        total_words += len(content)
                    st.markdown(f"**总字数:** {total_words}")

                with col3:
                    # 编辑按钮
                    if st.button("✏️ 编辑", key=f"edit_{idx}"):
                        st.session_state['selected_draft'] = draft_file
                        st.session_state['view_mode'] = "✏️ 编辑视图"
                        st.rerun()

                st.markdown("---")

        except Exception as e:
            st.error(f"加载草稿失败: {draft_file.name}")
            continue

    st.stop()

# 编辑视图
st.markdown("---")

# 侧边栏 - 草稿选择
st.sidebar.title("📚 选择草稿")
st.sidebar.markdown(f"共 {len(draft_files)} 个草稿")

# 搜索和筛选
search_query = st.sidebar.text_input("🔍 搜索标题", "")
format_filter = st.sidebar.multiselect(
    "📋 筛选格式",
    ["视频号", "公众号", "朋友圈", "小红书", "书稿"],
    default=[]
)

# 草稿选择
draft_options = {}
for draft_file in draft_files:
    try:
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft = json.load(f)

        title = draft.get('topic', {}).get('title', '未知标题')
        timestamp = draft.get('timestamp', '')

        # 搜索过滤
        if search_query and search_query.lower() not in title.lower():
            continue

        # 格式过滤
        if format_filter:
            contents = draft.get('contents', {})
            format_map = {
                'video': '视频号',
                'article': '公众号',
                'moments': '朋友圈',
                'xiaohongshu': '小红书',
                'book': '书稿'
            }
            has_format = any(format_map.get(k) in format_filter for k in contents.keys())
            if not has_format:
                continue

        display_name = f"{title} ({timestamp[:10]})"
        draft_options[display_name] = draft_file
    except:
        continue

if not draft_options:
    st.sidebar.warning("没有匹配的草稿")
    st.stop()

# 使用 session_state 保持选择
if 'selected_draft' in st.session_state and st.session_state['selected_draft'] in draft_options.values():
    # 找到对应的 display_name
    selected_draft_file = st.session_state['selected_draft']
    for name, file in draft_options.items():
        if file == selected_draft_file:
            default_index = list(draft_options.keys()).index(name)
            break
    else:
        default_index = 0
else:
    default_index = 0

selected_draft_name = st.sidebar.selectbox("选择草稿", list(draft_options.keys()), index=default_index)
selected_draft_file = draft_options[selected_draft_name]
st.session_state['selected_draft'] = selected_draft_file

# 加载选中的草稿
with open(selected_draft_file, 'r', encoding='utf-8') as f:
    draft = json.load(f)

topic = draft.get('topic', {})
contents = draft.get('contents', {})
timestamp = draft.get('timestamp', '')

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### 📝 {topic.get('title', '未知标题')}")

with col2:
    st.markdown(f"**创建时间:** {timestamp}")

# 选题信息
with st.expander("📊 选题信息", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("热度分数", topic.get('total_score', 'N/A'))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("来源", topic.get('source', '未知'))
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.metric("格式数", len(contents))
        st.markdown('</div>', unsafe_allow_html=True)

    if topic.get('summary'):
        st.markdown("**摘要:**")
        st.info(topic['summary'])

# 格式标签
format_map = {
    'video': ('视频号', 'badge-video'),
    'article': ('公众号', 'badge-article'),
    'moments': ('朋友圈', 'badge-moments'),
    'xiaohongshu': ('小红书', 'badge-xiaohongshu'),
    'book': ('书稿', 'badge-book')
}

st.markdown("---")
st.markdown("### 📑 内容格式")

# 显示可用格式
available_formats = []
for key, (name, badge_class) in format_map.items():
    if key in contents:
        available_formats.append(name)
        st.markdown(f'<span class="format-badge {badge_class}">{name}</span>', unsafe_allow_html=True)

if not available_formats:
    st.warning("该草稿暂无内容")
    st.stop()

st.markdown("---")

# 选择要编辑的格式
selected_format_name = st.selectbox("选择要查看/编辑的格式", available_formats)

# 找到对应的 key
selected_format_key = None
for key, (name, _) in format_map.items():
    if name == selected_format_name:
        selected_format_key = key
        break

if not selected_format_key or selected_format_key not in contents:
    st.error("内容不存在")
    st.stop()

# 获取内容
content_data = contents[selected_format_key]
if isinstance(content_data, dict):
    content = content_data.get('content', '')
else:
    content = content_data

# 内容统计
word_count = len(content)
line_count = content.count('\n') + 1

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("字数", word_count)
with col2:
    st.metric("段落数", line_count)
with col3:
    st.metric("预计阅读", f"{word_count // 400 + 1} 分钟")

st.markdown("---")

# 编辑模式切换
edit_mode = st.toggle("✏️ 编辑模式", value=False)

if edit_mode:
    st.markdown("### ✏️ 编辑内容")

    # 编辑器
    edited_content = st.text_area(
        "内容",
        value=content,
        height=500,
        key="content_editor"
    )

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("💾 保存", type="primary", use_container_width=True):
            # 更新内容
            if isinstance(contents[selected_format_key], dict):
                contents[selected_format_key]['content'] = edited_content
            else:
                contents[selected_format_key] = edited_content

            # 保存到文件
            draft['contents'] = contents
            with open(selected_draft_file, 'w', encoding='utf-8') as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)

            st.success("✅ 保存成功！")
            st.rerun()

    with col2:
        if st.button("🔄 重置", use_container_width=True):
            st.rerun()

else:
    st.markdown("### 👁️ 预览内容")

    # 预览模式
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# 操作按钮
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📤 发布到 Notion", use_container_width=True):
        try:
            from modules.publisher.notion_client import NotionClient

            notion = NotionClient()
            page_title = f"{topic.get('title', '未知标题')} - {selected_format_name}"

            with st.spinner("正在发布..."):
                page_id = notion.create_page(
                    title=page_title,
                    format_type=selected_format_name,
                    content=content
                )

            st.success(f"✅ 发布成功！")
            st.info(f"页面 ID: {page_id}")
        except Exception as e:
            st.error(f"❌ 发布失败: {str(e)}")

with col2:
    if st.button("📋 复制内容", use_container_width=True):
        st.code(content, language=None)
        st.info("💡 点击代码框右上角复制按钮")

with col3:
    if st.button("🔍 SEO 分析", use_container_width=True):
        st.info("SEO 分析功能")

        # 简单的 SEO 分析
        title_len = len(topic.get('title', ''))
        content_len = len(content)

        st.markdown("**SEO 检查:**")

        if 20 <= title_len <= 60:
            st.success(f"✅ 标题长度合适 ({title_len} 字)")
        else:
            st.warning(f"⚠️ 标题长度: {title_len} 字 (建议 20-60 字)")

        if content_len >= 300:
            st.success(f"✅ 内容长度充足 ({content_len} 字)")
        else:
            st.warning(f"⚠️ 内容较短: {content_len} 字 (建议 300+ 字)")

        # 关键词检查
        edu_keywords = ['留学', '教育', 'AI', '申请', '规划', '孩子', '家长']
        found_keywords = [kw for kw in edu_keywords if kw in content]

        if found_keywords:
            st.success(f"✅ 包含关键词: {', '.join(found_keywords)}")
        else:
            st.warning("⚠️ 建议添加教育领域关键词")

with col4:
    if st.button("🗑️ 删除草稿", use_container_width=True):
        if st.session_state.get('confirm_delete'):
            selected_draft_file.unlink()
            st.success("✅ 已删除")
            st.session_state.confirm_delete = False
            st.rerun()
        else:
            st.session_state.confirm_delete = True
            st.warning("⚠️ 再次点击确认删除")

# 底部信息
st.markdown("---")
st.caption(f"草稿文件: {selected_draft_file.name}")
