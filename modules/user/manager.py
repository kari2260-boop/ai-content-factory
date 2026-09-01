"""
用户管理器
负责加载和管理用户配置
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from modules.utils import DATA_DIR, setup_logger

logger = setup_logger('user_manager', 'user.log')


class UserManager:
    """用户管理器"""

    def __init__(self):
        self.users_file = DATA_DIR / 'users.json'
        self.users_data = self._load_users()

    def _load_users(self) -> Dict:
        """加载用户配置"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"用户配置文件不存在: {self.users_file}")
                return {'users': [], 'default_user': 'dr_k'}
        except Exception as e:
            logger.error(f"加载用户配置失败: {str(e)}")
            return {'users': [], 'default_user': 'dr_k'}

    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        for user in self.users_data.get('users', []):
            if user['id'] == user_id:
                return user
        return None

    def list_users(self) -> List[Dict]:
        """获取所有用户列表"""
        return self.users_data.get('users', [])

    def get_active_users(self) -> List[Dict]:
        """获取所有活跃用户"""
        return [u for u in self.users_data.get('users', []) if u.get('active', True)]

    def get_default_user(self) -> str:
        """获取默认用户ID"""
        return self.users_data.get('default_user', 'dr_k')

    def get_user_data_dir(self, user_id: str) -> Path:
        """获取用户数据目录"""
        return DATA_DIR / 'users' / user_id

    def get_user_openclaw_path(self, user_id: str) -> Path:
        """获取用户的 OpenClaw profile 路径"""
        return Path.home() / '.openclaw' / 'workspace' / 'profiles' / user_id

    def create_user(self, user_id: str, name: str, full_name: str = None, description: str = "") -> bool:
        """创建新用户"""
        try:
            # 检查用户是否已存在
            if self.get_user(user_id):
                logger.warning(f"用户已存在: {user_id}")
                return False

            # 创建用户数据目录
            user_data_dir = self.get_user_data_dir(user_id)
            user_data_dir.mkdir(parents=True, exist_ok=True)
            (user_data_dir / 'topics').mkdir(exist_ok=True)
            (user_data_dir / 'drafts').mkdir(exist_ok=True)
            (user_data_dir / 'published').mkdir(exist_ok=True)
            (user_data_dir / 'inbox').mkdir(exist_ok=True)

            # 创建 OpenClaw profile 目录
            openclaw_path = self.get_user_openclaw_path(user_id)
            openclaw_path.mkdir(parents=True, exist_ok=True)

            # 添加用户到配置
            from datetime import datetime
            new_user = {
                'id': user_id,
                'name': name,
                'full_name': full_name or name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'active': True
            }

            self.users_data['users'].append(new_user)

            # 保存配置
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 用户创建成功: {user_id}")
            return True

        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return False
