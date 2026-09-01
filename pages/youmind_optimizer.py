"""
YouMind 内容优化页面 - 专门用于优化文案和图片
"""
import streamlit as st
from pathlib import Path
from modules.visual.youmind_client import YouMindClient
from modules.user.context import UserContext

st.set_page_config(page_title="YouMind 内容优化", page_icon="🎨", layout="wide")

# 初始化 YouMind 客户端
youmind = YouMindClient()

st.title("🎨 YouMind 内容优化工坊")

if not youmind.available:
    st.error("❌ YouMind API 未配置")
    st.info("""
    请在 `.env` 文件中配置：
    ```
    YOUMIND_API_KEY=your_api_key_here
    ```
    然后重启应用。

    查看详细说明：`YouMind集成指南.md`
    """)
    st.stop()

st.success("✅ YouMind API 已就绪")

# 选择优化类型
tab1, tab2, tab3, tab4 = st.tabs(["📝 文案优化", "🖼️ 图片生成", "🎨 海报制作", "📋 批量处理"])

# ==================== Tab 1: 文案优化 ====================
with tab1:
    st.markdown("### 📝 AI 文案优化")
    st.info("使用 YouMind 的文字排版能力，让你的内容更专业、更吸引人")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 输入原始内容")

        input_title = st.text_input("标题", placeholder="输入文章标题")
        input_content = st.text_area(
            "正文内容",
            placeholder="粘贴你的文章内容...",
            height=300
        )

        layout_type = st.selectbox(
            "排版类型",
            options=["article", "poster", "card", "story"],
            format_func=lambda x: {
                "article": "📰 文章排版",
                "poster": "🎨 海报排版",
                "card": "💳 卡片排版",
                "story": "📖 故事排版"
            }[x]
        )

        template = st.selectbox(
            "模板风格（可选）",
            options=[None, "modern", "classic", "minimal", "colorful"],
            format_func=lambda x: "默认" if x is None else x.title()
        )

        if st.button("🚀 开始优化", type="primary", use_container_width=True):
            if not input_title or not input_content:
                st.warning("请输入标题和内容")
            else:
                with st.spinner("YouMind 正在优化中..."):
                    result = youmind.format_text_layout(
                        title=input_title,
                        content=input_content,
                        layout_type=layout_type,
                        template=template
                    )

                    if result:
                        st.session_state['optimized_result'] = result
                        st.success("✅ 优化完成！")
                        st.rerun()
                    else:
                        st.error("❌ 优化失败，请查看日志")

    with col2:
        st.markdown("#### 优化结果")

        if 'optimized_result' in st.session_state:
            result = st.session_state['optimized_result']

            # 显示预览链接
            if 'preview_url' in result:
                st.markdown(f"[🔗 在线预览]({result['preview_url']})")

            # 显示格式化结果
            format_tab1, format_tab2 = st.tabs(["HTML", "Markdown"])

            with format_tab1:
                if 'formatted_html' in result:
                    st.code(result['formatted_html'], language='html')

                    # 预览 HTML
                    with st.expander("👁️ HTML 预览"):
                        st.markdown(result['formatted_html'], unsafe_allow_html=True)

            with format_tab2:
                if 'formatted_md' in result:
                    st.code(result['formatted_md'], language='markdown')

                    # 预览 Markdown
                    with st.expander("👁️ Markdown 预览"):
                        st.markdown(result['formatted_md'])

            # 复制按钮
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📋 复制 HTML", use_container_width=True):
                    st.session_state['show_copy_html'] = True
                    st.rerun()
            with col_b:
                if st.button("📋 复制 Markdown", use_container_width=True):
                    st.session_state['show_copy_md'] = True
                    st.rerun()

            if st.session_state.get('show_copy_html'):
                st.text_area("复制 HTML", result.get('formatted_html', ''), height=200)
            if st.session_state.get('show_copy_md'):
                st.text_area("复制 Markdown", result.get('formatted_md', ''), height=200)
        else:
            st.info("优化后的内容将显示在这里")


# ==================== Tab 2: 图片生成 ====================
with tab2:
    st.markdown("### 🖼️ AI 图片生成")
    st.info("使用 YouMind 生成高质量的封面图和配图")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 图片设置")

        image_prompt = st.text_area(
            "图片描述",
            placeholder="描述你想要的图片，例如：一个温馨的家庭教育场景，父母和孩子一起阅读...",
            height=150
        )

        image_style = st.selectbox(
            "图片风格",
            options=["realistic", "anime", "cartoon", "abstract", "minimalist", "vibrant"],
            format_func=lambda x: {
                "realistic": "🎨 写实风格",
                "anime": "🎌 动漫风格",
                "cartoon": "🎪 卡通风格",
                "abstract": "🌈 抽象风格",
                "minimalist": "⚪ 极简风格",
                "vibrant": "🌟 鲜艳风格"
            }[x]
        )

        image_size = st.selectbox(
            "图片尺寸",
            options=["1024x1024", "1024x768", "768x1024"],
            format_func=lambda x: {
                "1024x1024": "正方形 (1:1)",
                "1024x768": "横向 (4:3)",
                "768x1024": "纵向 (3:4)"
            }[x]
        )

        image_quality = st.radio(
            "图片质量",
            options=["standard", "hd"],
            format_func=lambda x: "标准" if x == "standard" else "高清",
            horizontal=True
        )

        if st.button("🎨 生成图片", type="primary", use_container_width=True):
            if not image_prompt:
                st.warning("请输入图片描述")
            else:
                with st.spinner("YouMind 正在生成图片..."):
                    image_path = youmind.generate_image(
                        prompt=image_prompt,
                        style=image_style,
                        size=image_size,
                        quality=image_quality
                    )

                    if image_path:
                        st.session_state['generated_image'] = image_path
                        st.success("✅ 图片生成完成！")
                        st.rerun()
                    else:
                        st.error("❌ 图片生成失败，请查看日志")

    with col2:
        st.markdown("#### 生成结果")

        if 'generated_image' in st.session_state:
            image_path = st.session_state['generated_image']

            # 显示图片
            st.image(image_path, use_column_width=True)

            # 图片信息
            st.info(f"📁 保存路径：`{image_path}`")

            # 操作按钮
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 下载图片", use_container_width=True):
                    with open(image_path, 'rb') as f:
                        st.download_button(
                            "点击下载",
                            f,
                            file_name=Path(image_path).name,
                            mime="image/png",
                            use_container_width=True
                        )
            with col_b:
                if st.button("🗑️ 清除", use_container_width=True):
                    del st.session_state['generated_image']
                    st.rerun()
        else:
            st.info("生成的图片将显示在这里")


# ==================== Tab 3: 海报制作 ====================
with tab3:
    st.markdown("### 🎨 AI 海报制作")
    st.info("快速创建营销海报、活动宣传图")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 海报设置")

        poster_title = st.text_input("主标题", placeholder="例如：AI 教育讲座")
        poster_subtitle = st.text_input("副标题（可选）", placeholder="例如：2024年3月15日")

        poster_bg = st.text_input(
            "背景图片 URL（可选）",
            placeholder="留空使用默认背景"
        )

        poster_style = st.selectbox(
            "海报风格",
            options=["modern", "classic", "minimal", "colorful", "professional"],
            format_func=lambda x: x.title()
        )

        if st.button("🎨 生成海报", type="primary", use_container_width=True):
            if not poster_title:
                st.warning("请输入主标题")
            else:
                with st.spinner("YouMind 正在制作海报..."):
                    poster_path = youmind.create_poster(
                        title=poster_title,
                        subtitle=poster_subtitle if poster_subtitle else None,
                        background_image=poster_bg if poster_bg else None,
                        style=poster_style
                    )

                    if poster_path:
                        st.session_state['generated_poster'] = poster_path
                        st.success("✅ 海报制作完成！")
                        st.rerun()
                    else:
                        st.error("❌ 海报制作失败，请查看日志")

    with col2:
        st.markdown("#### 海报预览")

        if 'generated_poster' in st.session_state:
            poster_path = st.session_state['generated_poster']

            # 显示海报
            st.image(poster_path, use_column_width=True)

            # 海报信息
            st.info(f"📁 保存路径：`{poster_path}`")

            # 操作按钮
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 下载海报", use_container_width=True):
                    with open(poster_path, 'rb') as f:
                        st.download_button(
                            "点击下载",
                            f,
                            file_name=Path(poster_path).name,
                            mime="image/png",
                            use_container_width=True
                        )
            with col_b:
                if st.button("🗑️ 清除", use_container_width=True):
                    del st.session_state['generated_poster']
                    st.rerun()
        else:
            st.info("生成的海报将显示在这里")


# ==================== Tab 4: 批量处理 ====================
with tab4:
    st.markdown("### 📋 批量优化处理")
    st.info("一次性优化多个内容的文案和图片")

    st.markdown("#### 从草稿中选择")

    # 获取最近的草稿
    from modules.generator.main import ContentGenerator
    user_id = UserContext.get_current_user()
    generator = ContentGenerator(user_id=user_id)
    drafts = generator.get_latest_drafts(10)

    if drafts:
        selected_drafts = st.multiselect(
            "选择要优化的草稿",
            options=range(len(drafts)),
            format_func=lambda i: f"{drafts[i]['topic']['title'][:50]}... ({drafts[i]['generated_at'][:10]})"
        )

        if selected_drafts:
            st.markdown(f"已选择 {len(selected_drafts)} 个草稿")

            optimize_options = st.multiselect(
                "优化选项",
                options=["文案排版", "生成封面图", "生成海报"],
                default=["文案排版", "生成封面图"]
            )

            if st.button("🚀 开始批量优化", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = []

                for idx, draft_idx in enumerate(selected_drafts):
                    draft = drafts[draft_idx]
                    title = draft['topic']['title']

                    status_text.text(f"正在处理: {title[:30]}...")

                    draft_result = {'title': title, 'success': [], 'failed': []}

                    # 文案排版
                    if "文案排版" in optimize_options:
                        try:
                            content = draft['contents'].get('article', {}).get('content', '')
                            if content:
                                layout = youmind.format_text_layout(title, content)
                                if layout:
                                    draft_result['success'].append('文案排版')
                                else:
                                    draft_result['failed'].append('文案排版')
                        except:
                            draft_result['failed'].append('文案排版')

                    # 生成封面图
                    if "生成封面图" in optimize_options:
                        try:
                            image = youmind.generate_cover_image(title, platform='wechat')
                            if image:
                                draft_result['success'].append('封面图')
                            else:
                                draft_result['failed'].append('封面图')
                        except:
                            draft_result['failed'].append('封面图')

                    # 生成海报
                    if "生成海报" in optimize_options:
                        try:
                            poster = youmind.create_poster(title)
                            if poster:
                                draft_result['success'].append('海报')
                            else:
                                draft_result['failed'].append('海报')
                        except:
                            draft_result['failed'].append('海报')

                    results.append(draft_result)
                    progress_bar.progress((idx + 1) / len(selected_drafts))

                status_text.text("✅ 批量处理完成！")

                # 显示结果
                st.markdown("---")
                st.markdown("### 处理结果")

                for result in results:
                    with st.expander(f"{result['title'][:50]}..."):
                        if result['success']:
                            st.success(f"✅ 成功: {', '.join(result['success'])}")
                        if result['failed']:
                            st.error(f"❌ 失败: {', '.join(result['failed'])}")
    else:
        st.info("暂无草稿，请先在「内容生成」页面生成内容")

st.markdown("---")
st.markdown("💡 **提示**: 查看 `YouMind集成指南.md` 了解更多功能")
