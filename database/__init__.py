"""
数据库模块
根据配置自动选择MySQL或SQLite
"""
import os
from config import config

# 根据配置选择数据库管理器
if config.DATABASE_TYPE == 'sqlite':
    from .db_manager_sqlite import db_manager
    print("使用SQLite数据库")
else:
    from .db_manager import db_manager
    print("使用MySQL数据库")

__all__ = ['db_manager']
