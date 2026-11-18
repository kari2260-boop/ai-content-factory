# App.py 修复方案

## 问题 1：草稿列表无法打开编辑

### 当前代码（第 252-260 行）
```python
st.markdown("### 📝 最近的草稿")
drafts = generator.get_latest_drafts(5)

if drafts:
    for draft in drafts:
        with st.expander(f"{draft['topic']['title'][:50]}... ({draft['generated_at'][:10]})"):
            st.json(draft)  # ❌ 只显示 JSON，无法编辑
else:
    st.info("暂无草稿")
```

### 修复方案
```python
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
                st.markdown(f"**格式：** {', '.join(formats)}")

            with col2:
                # ✅ 添加"打开编辑"按钮
                if st.button("📝 打开编辑", key=f"open_draft_{i}"):
                    st.session_state['selected_topic'] = draft['topic']
                    st.session_state['current_draft'] = draft
                    st.success("已加载草稿，请查看下方内容")
                    st.rerun()
else:
    st.info("暂无草稿")
```

---

## 问题 2：发布功能缺少选择

### 当前代码（第 345-369 行）
```python
# 发布按钮
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📤 发布到 Notion", type="primary", use_container_width=True):
        # ❌ 直接发布所有格式，无法选择
        with st.spinner("正在发布..."):
            try:
                results = publisher.publish_draft(draft)
                st.success("✅ 发布成功！")
                st.json(results)
            except Exception as e:
                st.error(f"❌ 发布失败: {str(e)}")
```

### 修复方案
```python
# 发布选项
st.markdown("---")
st.markdown("### 📤 发布选项")

# ✅ 添加格式选择
publish_formats = st.multiselect(
    "选择要发布的格式",
    options=list(draft['contents'].keys()),
    default=list(draft['contents'].keys()),
    format_func=lambda x: {
        'video': '🎬 视频号',
        'article': '📰 公众号',
        'moments': '💬 朋友圈',
        'xiaohongshu': '📱 小红书',
        'book': '📚 书稿'
    }.get(x, x)
)

# ✅ 添加发布目标选择
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
                    exported = publisher.export_files(draft, formats=publish_formats)
                    st.success(f"✅ 已导出 {len(exported)} 个文件")
                    for file_path in exported:
                        st.markdown(f"- `{file_path}`")

                elif publish_target == "复制到剪贴板":
                    # 合并选中格式的内容
                    combined_content = ""
                    for fmt in publish_formats:
                        if fmt in draft['contents']:
                            combined_content += f"\n\n{'='*50}\n"
                            combined_content += f"{fmt.upper()}\n"
                            combined_content += f"{'='*50}\n\n"
                            combined_content += draft['contents'][fmt]['content']

                    st.text_area("复制以下内容", combined_content, height=300)
                    st.info("💡 请手动复制上方内容")

            except Exception as e:
                st.error(f"❌ 发布失败: {str(e)}")

with col2:
    if st.button("👁️ 预览效果", use_container_width=True):
        st.session_state['show_preview'] = True

with col3:
    if st.button("🗑️ 清空当前草稿", use_container_width=True):
        del st.session_state['current_draft']
        if 'selected_topic' in st.session_state:
            del st.session_state['selected_topic']
        st.rerun()

# ✅ 添加预览功能
if st.session_state.get('show_preview', False):
    st.markdown("---")
    st.markdown("### 👁️ 内容预览")

    preview_format = st.selectbox(
        "选择预览格式",
        options=publish_formats,
        format_func=lambda x: {
            'video': '🎬 视频号',
            'article': '📰 公众号',
            'moments': '💬 朋友圈',
            'xiaohongshu': '📱 小红书',
            'book': '📚 书稿'
        }.get(x, x)
    )

    if preview_format in draft['contents']:
        content = draft['contents'][preview_format]['content']

        # 根据格式渲染预览
        if preview_format == 'article':
            # 公众号样式预览
            st.markdown(f"""
            <div style="
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 800px;
                margin: 0 auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                {content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

        elif preview_format == 'xiaohongshu':
            # 小红书样式预览
            st.markdown(f"""
            <div style="
                background: #fff;
                padding: 15px;
                border-radius: 12px;
                max-width: 600px;
                margin: 0 auto;
                font-size: 14px;
                line-height: 1.6;
            ">
                {content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

        else:
            # 默认预览
            st.markdown(content)
```

---

## 额外优化建议

### 1. 添加草稿管理功能
```python
# 在"内容生成"页面添加
with st.sidebar:
    st.markdown("### 📁 草稿管理")

    drafts = generator.get_latest_drafts(10)
    if drafts:
        draft_options = {
            f"{d['topic']['title'][:30]}... ({d['generated_at'][:10]})": d
            for d in drafts
        }

        selected_draft_name = st.selectbox(
            "选择草稿",
            options=["当前草稿"] + list(draft_options.keys())
        )

        if selected_draft_name != "当前草稿":
            if st.button("📂 加载选中草稿"):
                draft = draft_options[selected_draft_name]
                st.session_state['selected_topic'] = draft['topic']
                st.session_state['current_draft'] = draft
                st.rerun()
```

### 2. 添加内容对比功能
```python
# 在编辑区域添加
if st.checkbox("📊 显示修改对比"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**原始内容**")
        st.markdown(content_data['content'])

    with col2:
        st.markdown("**修改后内容**")
        st.markdown(edited_content)
```

### 3. 添加快速复制按钮
```python
# 在每个格式的内容下方添加
if st.button(f"📋 复制{format_options[format_key]}", key=f"copy_{format_key}"):
    st.code(content_data['content'], language=None)
    st.info("💡 请使用 Ctrl+C (或 Cmd+C) 复制上方内容")
```

---

## 实施步骤

1. **立即修复**（5分钟）
   - 修复草稿列表的"打开编辑"按钮
   - 添加发布格式选择

2. **短期优化**（30分钟）
   - 添加发布目标选择（Notion/导出/复制）
   - 添加内容预览功能

3. **中期优化**（1-2小时）
   - 完善草稿管理
   - 添加内容对比
   - 优化预览样式

---

需要我现在就帮你实施这些修复吗？
