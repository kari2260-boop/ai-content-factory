"""
用户配置管理页面
管理用户（添加/删除）及对应知识库文件
"""
import streamlit as st
from pathlib import Path

from modules.user.manager import UserManager
from modules.user.context import UserContext

st.set_page_config(page_title="用户配置管理", page_icon="👥", layout="wide")

st.title("👥 用户配置管理")

user_manager = UserManager()

# ── 用户管理区 ────────────────────────────────────────────────
st.markdown("### 用户管理")

users = user_manager.list_users()
default_user_id = user_manager.get_default_user()

# 现有用户列表
if users:
    cols = st.columns([2, 2, 2, 1, 1])
    cols[0].markdown("**ID**")
    cols[1].markdown("**名称**")
    cols[2].markdown("**描述**")
    cols[3].markdown("**默认**")
    cols[4].markdown("**操作**")

    for user in users:
        uid = user['id']
        cols = st.columns([2, 2, 2, 1, 1])
        cols[0].text(uid)
        cols[1].text(user['name'])
        cols[2].text(user.get('description', ''))

        is_default = uid == default_user_id
        if is_default:
            cols[3].markdown("⭐")
        else:
            if cols[3].button("设为默认", key=f"default_{uid}"):
                user_manager.set_default_user(uid)
                st.success(f"已将 {user['name']} 设为默认用户")
                st.rerun()

        if is_default:
            cols[4].caption("默认用户")
        else:
            if cols[4].button("🗑️ 删除", key=f"del_{uid}"):
                st.session_state[f'confirm_delete_{uid}'] = True

        # 二次确认删除
        if st.session_state.get(f'confirm_delete_{uid}'):
            with st.container():
                st.warning(f"确认删除用户 **{user['name']}**？")
                delete_files = st.checkbox("同时删除该用户的所有数据文件和知识库", key=f"del_files_{uid}")
                c1, c2 = st.columns([1, 4])
                if c1.button("确认删除", key=f"confirm_del_{uid}", type="primary"):
                    if user_manager.delete_user(uid, delete_files=delete_files):
                        st.success(f"已删除用户 {user['name']}")
                        st.session_state.pop(f'confirm_delete_{uid}', None)
                        st.rerun()
                    else:
                        st.error("删除失败")
                if c2.button("取消", key=f"cancel_del_{uid}"):
                    st.session_state.pop(f'confirm_delete_{uid}', None)
                    st.rerun()

st.markdown("---")

# 添加新用户
with st.expander("➕ 添加新用户", expanded=False):
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        new_id = col1.text_input("用户ID（英文，无空格）", placeholder="例：zhangsan")
        new_name = col2.text_input("显示名称", placeholder="例：张三")
        new_full = st.text_input("全名（可选）", placeholder="例：张三丰")
        new_desc = st.text_input("描述", placeholder="例：教育内容创作者")
        copy_from = st.selectbox(
            "从现有用户复制知识库（可选）",
            options=["不复制"] + [u['id'] for u in users],
            format_func=lambda x: x if x == "不复制" else next((u['name'] for u in users if u['id'] == x), x)
        )
        submitted = st.form_submit_button("创建用户", type="primary")

        if submitted:
            new_id = new_id.strip().lower().replace(' ', '_')
            if not new_id or not new_name:
                st.error("用户ID和名称不能为空")
            elif not new_id.replace('_', '').isalnum():
                st.error("用户ID只能包含英文字母、数字和下划线")
            elif user_manager.get_user(new_id):
                st.error(f"用户ID '{new_id}' 已存在")
            else:
                ok = user_manager.create_user(new_id, new_name, new_full or new_name, new_desc)
                if ok:
                    # 复制知识库
                    if copy_from != "不复制":
                        import shutil
                        src = user_manager.get_user_openclaw_path(copy_from)
                        dst = user_manager.get_user_openclaw_path(new_id)
                        dst.mkdir(parents=True, exist_ok=True)
                        for fname in ['USER.md', 'MEMORY.md', 'CONTENT_GUIDE.md']:
                            if (src / fname).exists():
                                shutil.copy2(src / fname, dst / fname)
                        st.success(f"✅ 用户 {new_name} 创建成功，并复制了 {copy_from} 的知识库")
                    else:
                        st.success(f"✅ 用户 {new_name} 创建成功")
                    st.rerun()
                else:
                    st.error("创建失败，请查看日志")

st.markdown("---")

# ── 知识库编辑区 ──────────────────────────────────────────────
st.markdown("### 知识库配置")

users = user_manager.get_active_users()
user_options = {u['id']: f"{u['name']}（{u.get('description', '')}）" for u in users}
selected_user_id = st.selectbox(
    "选择用户",
    options=list(user_options.keys()),
    format_func=lambda x: user_options[x],
    key='manage_user_selector'
)

selected_user = user_manager.get_user(selected_user_id)
openclaw_path = user_manager.get_user_openclaw_path(selected_user_id)

st.info(f"📁 知识库路径: `{openclaw_path}`")

files = ['USER.md', 'MEMORY.md', 'CONTENT_GUIDE.md']
file_descriptions = {
    'USER.md': '用户画像：基本信息、写作风格、核心理念、目标受众等',
    'MEMORY.md': '记忆库：重要案例、金句库、历史内容等',
    'CONTENT_GUIDE.md': '内容创作指南：内容风格、创作原则、避免事项等'
}

tabs = st.tabs(["👤 USER.md", "🧠 MEMORY.md", "📝 CONTENT_GUIDE.md"])

for tab, filename in zip(tabs, files):
    with tab:
        st.markdown(f"**{file_descriptions[filename]}**")
        file_path = openclaw_path / filename

        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            st.caption(f"✅ 已存在 · {file_path.stat().st_size} 字节")
        else:
            current_content = f"# {selected_user['name']}的{filename.replace('.md', '')}\n\n待补充..."
            st.caption("⚠️ 文件不存在，保存后自动创建")

        input_method = st.radio(
            "输入方式",
            ["直接编辑", "上传文件"],
            key=f"input_method_{filename}",
            horizontal=True
        )

        if input_method == "直接编辑":
            edited_content = st.text_area(
                "内容",
                value=current_content,
                height=400,
                key=f"editor_{filename}"
            )
            c1, c2 = st.columns([1, 5])
            if c1.button(f"💾 保存", key=f"save_{filename}", type="primary"):
                try:
                    openclaw_path.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(edited_content)
                    st.success(f"✅ {filename} 保存成功")
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {e}")
            if edited_content != current_content:
                c2.warning("内容已修改，记得保存")
        else:
            uploaded = st.file_uploader(f"选择 {filename}", type=['md', 'txt'], key=f"upload_{filename}")
            if uploaded:
                content = uploaded.read().decode('utf-8')
                st.text_area("预览", value=content, height=300, disabled=True, key=f"preview_{filename}")
                if st.button("✅ 确认上传", key=f"confirm_upload_{filename}", type="primary"):
                    try:
                        openclaw_path.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        st.success(f"✅ {filename} 上传成功")
                        st.rerun()
                    except Exception as e:
                        st.error(f"上传失败: {e}")

st.markdown("---")

# ── 汇总状态 ─────────────────────────────────────────────────
st.markdown("### 所有用户配置状态")

import pandas as pd
status_data = []
for user in user_manager.get_active_users():
    p = user_manager.get_user_openclaw_path(user['id'])
    total = sum((p / f).stat().st_size for f in files if (p / f).exists())
    status_data.append({
        '用户': user['name'],
        'ID': user['id'],
        '默认': '⭐' if user['id'] == default_user_id else '',
        'USER.md': '✅' if (p / 'USER.md').exists() else '❌',
        'MEMORY.md': '✅' if (p / 'MEMORY.md').exists() else '❌',
        'CONTENT_GUIDE.md': '✅' if (p / 'CONTENT_GUIDE.md').exists() else '❌',
        '总大小': f"{total} 字节",
    })

st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)
