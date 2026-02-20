"""
多用户数据迁移脚本
将现有的单用户数据迁移到多用户结构
"""
import os
import shutil
from database import db_manager

def migrate_database():
    """迁移数据库结构"""
    print("=" * 60)
    print("开始数据库迁移...")
    print("=" * 60)
    
    try:
        # 1. 检查watchlist表是否有user_id字段
        print("\n1. 检查watchlist表结构...")
        structure = db_manager.execute_query("PRAGMA table_info(watchlist)")
        has_user_id = any(col['name'] == 'user_id' for col in structure)
        
        if not has_user_id:
            print("   需要为watchlist表添加user_id字段")
            
            # 创建新表
            db_manager.execute_update("""
            CREATE TABLE watchlist_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, stock_code)
            )
            """)
            
            # 复制数据（默认user_id=1，即admin用户）
            db_manager.execute_update("""
            INSERT INTO watchlist_new (id, user_id, stock_code, stock_name, created_at)
            SELECT id, 1, stock_code, stock_name, created_at FROM watchlist
            """)
            
            # 删除旧表
            db_manager.execute_update("DROP TABLE watchlist")
            
            # 重命名新表
            db_manager.execute_update("ALTER TABLE watchlist_new RENAME TO watchlist")
            
            # 创建索引
            db_manager.execute_update("CREATE INDEX idx_watchlist_user_id ON watchlist(user_id)")
            db_manager.execute_update("CREATE INDEX idx_watchlist_stock_code ON watchlist(stock_code)")
            
            print("   ✅ watchlist表迁移完成")
        else:
            print("   ✅ watchlist表已有user_id字段")
        
        # 2. 检查positions表的user_id字段
        print("\n2. 检查positions表结构...")
        structure = db_manager.execute_query("PRAGMA table_info(positions)")
        has_user_id = any(col['name'] == 'user_id' for col in structure)
        
        if has_user_id:
            print("   ✅ positions表已有user_id字段")
            # 确保所有旧数据的user_id都是1
            db_manager.execute_update("UPDATE positions SET user_id = 1 WHERE user_id = 0 OR user_id IS NULL")
        else:
            print("   ⚠️ positions表没有user_id字段，请检查数据库初始化")
        
        # 3. 检查cash_balance表
        print("\n3. 检查cash_balance表结构...")
        structure = db_manager.execute_query("PRAGMA table_info(cash_balance)")
        has_user_id = any(col['name'] == 'user_id' for col in structure)
        
        if has_user_id:
            print("   ✅ cash_balance表已有user_id字段")
            # 确保admin用户有余额记录
            admin_balance = db_manager.execute_query("SELECT * FROM cash_balance WHERE user_id = 1", fetch_one=True)
            if not admin_balance:
                # 迁移旧的余额记录（id=1）到user_id=1
                old_balance = db_manager.execute_query("SELECT * FROM cash_balance WHERE id = 1", fetch_one=True)
                if old_balance:
                    db_manager.execute_update("UPDATE cash_balance SET user_id = 1 WHERE id = 1")
                else:
                    db_manager.execute_update("INSERT INTO cash_balance (user_id, balance) VALUES (1, 0)")
                print("   ✅ 已初始化admin用户余额")
        else:
            print("   ⚠️ cash_balance表没有user_id字段，请检查数据库初始化")
        
        # 4. 检查chat_history表
        print("\n4. 检查chat_history表结构...")
        structure = db_manager.execute_query("PRAGMA table_info(chat_history)")
        has_user_id = any(col['name'] == 'user_id' for col in structure)
        
        if has_user_id:
            print("   ✅ chat_history表已有user_id字段")
            # 确保所有旧数据的user_id都是1
            db_manager.execute_update("UPDATE chat_history SET user_id = 1 WHERE user_id = 0 OR user_id IS NULL")
        else:
            print("   ⚠️ chat_history表没有user_id字段，请检查数据库初始化")
        
        print("\n" + "=" * 60)
        print("✅ 数据库迁移完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def migrate_file_system():
    """迁移文件系统（对话历史）"""
    print("\n" + "=" * 60)
    print("开始文件系统迁移...")
    print("=" * 60)
    
    try:
        prompt_history_dir = os.path.join(os.path.dirname(__file__), 'prompt_history')
        
        if not os.path.exists(prompt_history_dir):
            print("   ℹ️ prompt_history目录不存在，无需迁移")
            return True
        
        # 获取admin用户名
        admin = db_manager.execute_query("SELECT username FROM users WHERE id = 1", fetch_one=True)
        if not admin:
            print("   ⚠️ 找不到admin用户，使用默认用户名'admin'")
            admin_username = 'admin'
        else:
            admin_username = admin['username']
        
        print(f"\n   将对话历史迁移到 {admin_username}/ 目录下...")
        
        # 创建admin用户目录
        admin_dir = os.path.join(prompt_history_dir, admin_username)
        os.makedirs(admin_dir, exist_ok=True)
        
        # 遍历所有股票目录
        moved_count = 0
        for item in os.listdir(prompt_history_dir):
            item_path = os.path.join(prompt_history_dir, item)
            
            # 跳过admin目录本身
            if item == admin_username:
                continue
            
            # 只处理目录
            if os.path.isdir(item_path):
                # 检查是否是股票代码目录（包含history_*.md文件）
                has_history = any(f.startswith('history_') and f.endswith('.md') for f in os.listdir(item_path))
                
                if has_history:
                    target_path = os.path.join(admin_dir, item)
                    
                    # 如果目标已存在，需要合并
                    if os.path.exists(target_path):
                        print(f"   ⚠️ {item} 目录已存在于 {admin_username}/ 下，跳过")
                    else:
                        shutil.move(item_path, target_path)
                        print(f"   ✅ 移动 {item}/ -> {admin_username}/{item}/")
                        moved_count += 1
        
        if moved_count > 0:
            print(f"\n   ✅ 成功移动 {moved_count} 个股票对话历史目录")
        else:
            print(f"\n   ℹ️ 没有需要迁移的对话历史")
        
        print("\n" + "=" * 60)
        print("✅ 文件系统迁移完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 文件系统迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("          多用户数据迁移脚本")
    print("=" * 60)
    print("\n此脚本将执行以下操作：")
    print("1. 为watchlist表添加user_id字段")
    print("2. 将现有数据关联到admin用户（user_id=1）")
    print("3. 将prompt_history/{stock_code}/ 迁移到 prompt_history/admin/{stock_code}/")
    print("\n⚠️  建议先备份数据库和prompt_history目录")
    print("=" * 60)
    
    response = input("\n是否继续？(yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ 取消迁移")
        return
    
    # 执行迁移
    db_success = migrate_database()
    fs_success = migrate_file_system()
    
    if db_success and fs_success:
        print("\n" + "=" * 60)
        print("🎉 所有迁移完成！")
        print("=" * 60)
        print("\n现在你可以：")
        print("1. 启动应用：python app.py")
        print("2. 使用admin账户登录查看数据")
        print("3. 创建新用户，每个用户将有独立的持仓和对话历史")
        print("\n对话历史路径格式：prompt_history/{username}/{stock_code}/history_{index}.md")
        print("=" * 60)
    else:
        print("\n❌ 迁移过程中出现错误，请检查上面的错误信息")


if __name__ == '__main__':
    main()
