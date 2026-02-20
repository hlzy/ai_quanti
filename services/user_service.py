"""
用户管理服务
"""
import hashlib
from datetime import datetime
from database import db_manager
from utils.logger import app_logger


class UserService:
    """用户管理服务"""
    
    def __init__(self):
        """初始化用户服务"""
        self.init_admin_user()
    
    def _hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def init_admin_user(self):
        """初始化管理员账户"""
        try:
            # 检查管理员是否存在
            query = "SELECT id FROM users WHERE username = %s"
            result = db_manager.execute_query(query, ('admin',), fetch_one=True)
            
            if not result:
                # 创建管理员账户
                password_hash = self._hash_password('admin123')
                query = """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (%s, %s, %s, %s)
                """
                db_manager.execute_update(
                    query, 
                    ('admin', password_hash, 'admin', datetime.now())
                )
                app_logger.info("管理员账户初始化成功")
        except Exception as e:
            app_logger.error(f"初始化管理员账户失败: {e}", exc_info=True)
    
    def authenticate(self, username, password):
        """验证用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            dict: 用户信息 or None
        """
        try:
            password_hash = self._hash_password(password)
            query = """
            SELECT id, username, role, created_at 
            FROM users 
            WHERE username = %s AND password_hash = %s
            """
            user = db_manager.execute_query(
                query, 
                (username, password_hash), 
                fetch_one=True
            )
            
            if user:
                app_logger.info(f"用户登录成功: {username}")
            else:
                app_logger.warning(f"用户登录失败: {username}")
            
            return user
        except Exception as e:
            app_logger.error(f"用户认证失败: {e}", exc_info=True)
            return None
    
    def create_user(self, username, password, role='user'):
        """创建新用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色 ('user' 或 'admin')
            
        Returns:
            dict: {'success': bool, 'message': str, 'user_id': int}
        """
        try:
            # 检查用户名是否已存在
            query = "SELECT id FROM users WHERE username = %s"
            existing = db_manager.execute_query(query, (username,), fetch_one=True)
            
            if existing:
                return {'success': False, 'message': '用户名已存在'}
            
            # 创建用户
            password_hash = self._hash_password(password)
            query = """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            """
            db_manager.execute_update(
                query, 
                (username, password_hash, role, datetime.now())
            )
            
            # 获取新用户ID
            user = db_manager.execute_query(
                "SELECT id FROM users WHERE username = %s", 
                (username,), 
                fetch_one=True
            )
            
            app_logger.info(f"创建用户成功: {username} (role: {role})")
            return {
                'success': True, 
                'message': '用户创建成功', 
                'user_id': user['id']
            }
        except Exception as e:
            app_logger.error(f"创建用户失败: {e}", exc_info=True)
            return {'success': False, 'message': f'创建失败: {str(e)}'}
    
    def delete_user(self, user_id):
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # 检查是否是管理员账户
            query = "SELECT username, role FROM users WHERE id = %s"
            user = db_manager.execute_query(query, (user_id,), fetch_one=True)
            
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            if user['role'] == 'admin' and user['username'] == 'admin':
                return {'success': False, 'message': '不能删除默认管理员账户'}
            
            # 删除用户
            query = "DELETE FROM users WHERE id = %s"
            db_manager.execute_update(query, (user_id,))
            
            app_logger.info(f"删除用户成功: {user['username']}")
            return {'success': True, 'message': '用户删除成功'}
        except Exception as e:
            app_logger.error(f"删除用户失败: {e}", exc_info=True)
            return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    def get_all_users(self):
        """获取所有用户列表
        
        Returns:
            list: 用户列表
        """
        try:
            query = """
            SELECT id, username, role, created_at 
            FROM users 
            ORDER BY id
            """
            users = db_manager.execute_query(query)
            return users or []
        except Exception as e:
            app_logger.error(f"获取用户列表失败: {e}", exc_info=True)
            return []
    
    def change_password(self, user_id, old_password, new_password):
        """修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # 验证旧密码
            old_password_hash = self._hash_password(old_password)
            query = "SELECT id FROM users WHERE id = %s AND password_hash = %s"
            user = db_manager.execute_query(
                query, 
                (user_id, old_password_hash), 
                fetch_one=True
            )
            
            if not user:
                return {'success': False, 'message': '旧密码错误'}
            
            # 更新密码
            new_password_hash = self._hash_password(new_password)
            query = "UPDATE users SET password_hash = %s WHERE id = %s"
            db_manager.execute_update(query, (new_password_hash, user_id))
            
            app_logger.info(f"用户修改密码成功: user_id={user_id}")
            return {'success': True, 'message': '密码修改成功'}
        except Exception as e:
            app_logger.error(f"修改密码失败: {e}", exc_info=True)
            return {'success': False, 'message': f'修改失败: {str(e)}'}
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户信息 or None
        """
        try:
            query = """
            SELECT id, username, role, created_at 
            FROM users 
            WHERE id = %s
            """
            return db_manager.execute_query(query, (user_id,), fetch_one=True)
        except Exception as e:
            app_logger.error(f"获取用户信息失败: {e}", exc_info=True)
            return None


# 创建全局用户服务实例
user_service = UserService()
