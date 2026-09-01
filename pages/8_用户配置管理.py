"""
用户配置管理页面
管理每个用户的知识库文件（USER.md, MEMORY.md, CONTENT_GUIDE.md）
"""
import streamlit as st
from pathlib import Path

from modules.user.manager import UserManager
from modules.user.context import UserContext

st.set_page_config(page_title="用户配置管理", page_icon="👥", layout="wide")

st.title("👥 用户配置管理")

# 初始化用户管理器
user_manager = UserManager()
users = user_manager.get_active_users()

# 用户选择
st.markdown("### 选择要管理的用户")
user_options = {u['id']: f"{u['name']} ({u['description']})" for u in users}
selected_user_id = st.selectbox(
    "用户",
    options=list(user_options.keys()),
    format_func=lambda x: user_options[x],
    key='manage_user_selector'
)

selected_user = user_manager.get_user(selected_user_id)
openclaw_path = user_manager.get_user_openclaw_path(selected_user_id)

st.info(f"📁 当前用户的 OpenClaw 路径: `{openclaw_path}`")

st.markdown("---")

# 三个知识库文件的编辑器
tabs = st.tabs(["👤 USER.md", "🧠 MEMORY.md", "📝 CONTENT_GUIDE.md"])

# 文件名列表
files = ['USER.md', 'MEMORY.md', 'CONTENT_GUIDE.md']
file_descriptions = {
    'USER.md': '用户画像：基本信息、写作风格、核心理念、目标受众等',
    'MEMORY.md': '记忆库：重要案例、金句库、历史内容等',
    'CONTENT_GUIDE.md': '内容创作指南：内容风格、创作原则、避免事项等'
}

for tab, filename in zip(tabs, files):
    with tab:
        st.markdown(f"### {filename}")
        st.caption(file_descriptions[filename])

        file_path = openclaw_path / filename

        # 读取现有内容
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        else:
            current_content = f"# {selected_user['name']}的{filename.replace('.md', '')}\n\n待补充..."

        # 显示文件状态
        col1, col2 = st.columns([3, 1])
        with col1:
            if file_path.exists():
                file_size = file_path.stat().st_size
                st.success(f"✅ 文件已存在 ({file_size} 字节)")
            else:
                st.warning("⚠️ 文件不存在，将创建新文件")

        with col2:
            word_count = len(current_content)
            st.metric("字数", word_count)

        st.markdown("---")

        # 两种输入方式
        input_method = st.radio(
            "输入方式",
            ["📝 直接编辑", "📤 上传文件"],
            key=f"input_method_{filename}",
            horizontal=True
        )

        if input_method == "📝 直接编辑":
            # 文本编辑器
            edited_content = st.text_area(
                "内容",
                value=current_content,
                height=400,
                key=f"editor_{filename}"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button(f"💾 保存 {filename}", key=f"save_{filename}", type="primary"):
                    try:
                        # 确保目录存在
                        openclaw_path.mkdir(parents=True, exist_ok=True)

                        # 保存文件
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(edited_content)

                        st.success(f"✅ {filename} 保存成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 保存失败: {str(e)}")

            with col2:
                if st.button(f"🔄 重置", key=f"reset_{filename}"):
                    st.rerun()

            with col3:
                if edited_content != current_content:
                    st.warning("⚠️ 内容已修改，记得保存")

        else:
            # 文件上传
            st.markdown("#### 上传 Markdown 文件")
            uploaded_file = st.file_uploader(
                f"选择 {filename} 文件",
                type=['md', 'txt'],
                key=f"upload_{filename}"
            )

            if uploaded_file:
                # 预览上传的内容
                uploaded_content = uploaded_file.read().decode('utf-8')

                st.markdown("##### 预览上传内容")
                st.text_area(
                    "内容预览",
                    value=uploaded_content,
                    height=300,
                    key=f"preview_{filename}",
                    disabled=True
                )

                col1, col2 = st.columns([1, 3])

                with col1:
                    if st.button(f"✅ 确认上传", key=f"confirm_upload_{filename}", type="primary"):
                        try:
                            # 确保目录存在
                            openclaw_path.mkdir(parents=True, exist_ok=True)

                            # 保存文件
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(uploaded_content)

                            st.success(f"✅ {filename} 上传成功！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 上传失败: {str(e)}")

                with col2:
                    st.info(f"📊 上传文件大小: {len(uploaded_content)} 字符")

st.markdown("---")

# 底部：快速操作
st.markdown("### 🚀 快速操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 复制 K博士 的配置", key="copy_from_drk"):
        if selected_user_id == 'dr_k':
            st.warning("⚠️ 当前已经是 K博士")
        else:
            try:
                source_path = user_manager.get_user_openclaw_path('dr_k')
                target_path = openclaw_path

                # 确保目标目录存在
                target_path.mkdir(parents=True, exist_ok=True)

                # 复制三个文件
                import shutil
                copied_files = []
                for filename in files:
                    source_file = source_path / filename
                    target_file = target_path / filename
                    if source_file.exists():
                        shutil.copy2(source_file, target_file)
                        copied_files.append(filename)

                st.success(f"✅ 已复制 {len(copied_files)} 个文件: {', '.join(copied_files)}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 复制失败: {str(e)}")

with col2:
    if st.button("🗑️ 清空当前用户配置", key="clear_config"):
        if st.session_state.get('confirm_clear', False):
            try:
                for filename in files:
                    file_path = openclaw_path / filename
                    if file_path.exists():
                        file_path.unlink()

                st.success("✅ 配置已清空")
                st.session_state['confirm_clear'] = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ 清空失败: {str(e)}")
        else:
            st.session_state['confirm_clear'] = True
            st.warning("⚠️ 再次点击确认清空")

with col3:
    if st.button("📥 下载当前配置", key="download_config"):
        st.info("💡 提示：可以在每个文件的编辑区域复制内容")

st.markdown("---")

# 显示所有用户的配置状态
st.markdown("### 📊 所有用户配置状态")

status_data = []
for user in users:
    user_openclaw_path = user_manager.get_user_openclaw_path(user['id'])

    status = {
        '用户': user['name'],
        'USER.md': '✅' if (user_openclaw_path / 'USER.md').exists() else '❌',
        'MEMORY.md': '✅' if (user_openclaw_path / 'MEMORY.md').exists() else '❌',
        'CONTENT_GUIDE.md': '✅' if (user_openclaw_path / 'CONTENT_GUIDE.md').exists() else '❌',
    }

    # 计算总字数
    total_chars = 0
    for filename in files:
        file_path = user_openclaw_path / filename
        if file_path.exists():
            total_chars += file_path.stat().st_size

    status['总大小'] = f"{total_chars} 字节"
    status_data.append(status)

import pandas as pd
df = pd.DataFrame(status_data)
st.dataframe(df, use_container_width=True)
