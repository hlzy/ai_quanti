"""
检查和修复管理员账户 (SQLite版本)
"""
import hashlib
import sqlite3
import os
from config import config

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_admin():
    """检查管理员账户"""
    try:
        # SQLite数据库路径
        db_dir = os.path.join(config.BASE_DIR, 'data')
        db_path = os.path.join(db_dir, 'quanti_stock.db')
        
        print("=" * 60)
        print("检查管理员账户状态 (SQLite)")
        print("=" * 60)
        print(f"数据库路径: {db_path}")
        
        if not os.path.exists(db_path):
            print("\n❌ 数据库文件不存在")
            print("\n请先运行数据库初始化:")
            print("python -c \"from database import db_manager; db_manager.init_database()\"")
            return
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. 检查users表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("\n❌ users表不存在")
            print("\n请先运行数据库初始化:")
            print("python -c \"from database import db_manager; db_manager.init_database()\"")
            conn.close()
            return
        else:
            print("✅ users表存在")
        
        # 2. 查询所有用户
        cursor.execute("SELECT id, username, role, created_at FROM users")
        users = cursor.fetchall()
        print(f"\n当前用户数: {len(users)}")
        for user in users:
            print(f"  - ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
        
        # 3. 检查admin用户
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", ('admin',))
        admin = cursor.fetchone()
        
        if not admin:
            print("\n❌ admin账户不存在")
            print("正在创建admin账户...")
            
            password_hash = hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ('admin', password_hash, 'admin')
            )
            conn.commit()
            print("✅ admin账户创建成功")
            print("   用户名: admin")
            print("   密码: admin123")
        else:
            print(f"\n✅ admin账户存在 (ID: {admin['id']})")
            
            # 4. 验证密码
            correct_hash = hash_password('admin123')
            if admin['password_hash'] == correct_hash:
                print("✅ 密码哈希正确")
                print("   用户名: admin")
                print("   密码: admin123")
            else:
                print("❌ 密码哈希不匹配")
                print(f"   数据库中的哈希: {admin['password_hash']}")
                print(f"   期望的哈希: {correct_hash}")
                
                # 修复密码
                print("\n正在重置admin密码为 admin123...")
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (correct_hash, 'admin')
                )
                conn.commit()
                print("✅ 密码重置成功")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("检查完成！")
        print("=" * 60)
        print("\n登录信息:")
        print("  URL: http://localhost:5000/login")
        print("  用户名: admin")
        print("  密码: admin123")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_admin()
