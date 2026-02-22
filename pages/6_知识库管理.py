"""
知识库管理页面
"""
import streamlit as st
from pathlib import Path
import time

from knowledge_feed import KnowledgeFeed

st.set_page_config(page_title="知识库管理", page_icon="📚", layout="wide")

# 初始化
@st.cache_resource
def init_knowledge_feed():
    return KnowledgeFeed()

kf = init_knowledge_feed()

st.title("📚 知识库管理")

# 顶部状态栏
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("收件箱路径", str(kf.inbox_dir))

with col2:
    status = "🟢 运行中" if kf.is_watching else "🔴 未启动"
    st.metric("监听状态", status)

with col3:
    inbox_files = list(kf.inbox_dir.glob('*'))
    inbox_count = len([f for f in inbox_files if f.is_file()])
    st.metric("待处理文件", inbox_count)

# 控制按钮
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 启动收件箱监听", disabled=kf.is_watching):
        kf.start_inbox_watcher()
        st.success("收件箱监听已启动")
        st.rerun()

with col2:
    if st.button("⏹️ 停止收件箱监听", disabled=not kf.is_watching):
        kf.stop_inbox_watcher()
        st.info("收件箱监听已停止")
        st.rerun()

st.markdown("---")

# 三个 Tab
tab1, tab2, tab3 = st.tabs(["📝 粘贴文本注入", "🔗 URL 注入", "📁 上传文件"])

# Tab1: 粘贴文本注入
with tab1:
    st.markdown("### 粘贴文本直接注入知识库")

    title = st.text_input("标题", key="text_title")
    source_type = st.selectbox("来源类型", ["文章", "笔记", "会议记录", "课程讲义", "其他"], key="text_source")
    tags_input = st.text_input("标签（逗号分隔）", key="text_tags")
    text_content = st.text_area("内容", height=300, key="text_content")

    if st.button("💾 注入到知识库", key="text_submit"):
        if not title or not text_content:
            st.error("请填写标题和内容")
        else:
            with st.spinner("正在处理..."):
                tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
                result = kf.process_text(
                    text=text_content,
                    title=title,
                    source_type=source_type,
                    tags=tags
                )

                if result['success']:
                    st.success("✅ 注入成功！")
                    if result.get('prompts'):
                        st.warning("⚠️ 检测到提示词，请确认是否保存")
                        st.json(result['prompts'])
                    st.json(result)
                else:
                    st.error(f"❌ 注入失败: {result.get('error')}")

# Tab2: URL 注入
with tab2:
    st.markdown("### 从 URL 抓取内容并注入")

    url = st.text_input("URL 地址", key="url_input")
    url_title = st.text_input("标题（可选，留空自动提取）", key="url_title")
    url_tags_input = st.text_input("标签（逗号分隔）", key="url_tags")

    if st.button("🌐 抓取并注入", key="url_submit"):
        if not url:
            st.error("请输入 URL")
        else:
            with st.spinner("正在抓取页面..."):
                tags = [t.strip() for t in url_tags_input.split(',')] if url_tags_input else []
                result = kf.process_url(
                    url=url,
                    title=url_title,
                    tags=tags
                )

                if result['success']:
                    st.success("✅ 抓取并注入成功！")
                    st.json(result)
                else:
                    st.error(f"❌ 处理失败: {result.get('error')}")

# Tab3: 上传文件
with tab3:
    st.markdown("### 上传文件到知识库")
    st.info("支持格式：.txt, .md, .docx, .pdf")

    uploaded_files = st.file_uploader(
        "选择文件",
        type=['txt', 'md', 'docx', 'pdf'],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:
        st.write(f"已选择 {len(uploaded_files)} 个文件")

        if st.button("📤 上传并处理", key="file_submit"):
            results = []

            for uploaded_file in uploaded_files:
                with st.spinner(f"处理 {uploaded_file.name}..."):
                    # 保存到收件箱
                    file_path = kf.inbox_dir / uploaded_file.name
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # 等待2秒
                    time.sleep(2)

                    # 处理文件
                    result = kf.process_single_file(file_path)
                    results.append({
                        'filename': uploaded_file.name,
                        'result': result
                    })

            # 显示结果
            st.markdown("### 处理结果")
            for item in results:
                if item['result']['success']:
                    st.success(f"✅ {item['filename']}")
                else:
                    st.error(f"❌ {item['filename']}: {item['result'].get('error')}")

st.markdown("---")

# 底部：最近注入记录
st.markdown("### 📋 最近注入记录")

# 获取最近导入的文件
imported_files = []
for date_dir in sorted(kf.imported_dir.glob('*'), reverse=True)[:7]:  # 最近7天
    if date_dir.is_dir():
        for file in date_dir.glob('*'):
            if file.is_file():
                imported_files.append({
                    'title': file.stem,
                    'source': file.suffix[1:],
                    'time': date_dir.name,
                    'path': str(file)
                })

if imported_files:
    for i, item in enumerate(imported_files[:10], 1):
        with st.expander(f"{i}. {item['title']} ({item['source']})"):
            st.markdown(f"**时间**: {item['time']}")
            st.markdown(f"**路径**: `{item['path']}`")
else:
    st.info("暂无注入记录")
