"""
用户上下文管理
基于 Streamlit session_state 管理当前用户
"""
from pathlib import Path
from typing import Dict, Optional
import streamlit as st

from modules.user.manager import UserManager


class UserContext:
    """用户上下文管理器"""

    _manager = None

    @classmethod
    def _get_manager(cls) -> UserManager:
        """获取用户管理器实例（单例）"""
        if cls._manager is None:
            cls._manager = UserManager()
        return cls._manager

    @staticmethod
    def get_current_user() -> str:
        """获取当前用户ID"""
        if 'current_user_id' not in st.session_state:
            manager = UserContext._get_manager()
            st.session_state['current_user_id'] = manager.get_default_user()
        return st.session_state['current_user_id']

    @staticmethod
    def set_current_user(user_id: str):
        """设置当前用户"""
        st.session_state['current_user_id'] = user_id

    @staticmethod
    def get_current_user_info() -> Optional[Dict]:
        """获取当前用户信息"""
        user_id = UserContext.get_current_user()
        manager = UserContext._get_manager()
        return manager.get_user(user_id)

    @staticmethod
    def get_current_data_dir() -> Path:
        """获取当前用户的数据目录"""
        user_id = UserContext.get_current_user()
        manager = UserContext._get_manager()
        return manager.get_user_data_dir(user_id)

    @staticmethod
    def get_current_openclaw_path() -> Path:
        """获取当前用户的 OpenClaw profile 路径"""
        user_id = UserContext.get_current_user()
        manager = UserContext._get_manager()
        return manager.get_user_openclaw_path(user_id)
