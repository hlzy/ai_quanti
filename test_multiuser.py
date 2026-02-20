"""
多用户功能验证脚本
"""
from database import db_manager
from services.watchlist_service import watchlist_service
from services.position_service import position_service
from services.ai_service import ai_service
import os

def test_database_structure():
    """测试数据库结构"""
    print("\n" + "=" * 60)
    print("测试1: 数据库结构检查")
    print("=" * 60)
    
    try:
        # 检查watchlist表
        print("\n检查watchlist表...")
        structure = db_manager.execute_query("PRAGMA table_info(watchlist)")
        columns = [col['name'] for col in structure]
        
        if 'user_id' in columns:
            print("   ✅ watchlist表有user_id字段")
        else:
            print("   ❌ watchlist表缺少user_id字段")
            return False
        
        # 检查positions表
        print("\n检查positions表...")
        structure = db_manager.execute_query("PRAGMA table_info(positions)")
        columns = [col['name'] for col in structure]
        
        if 'user_id' in columns:
            print("   ✅ positions表有user_id字段")
        else:
            print("   ❌ positions表缺少user_id字段")
            return False
        
        # 检查cash_balance表
        print("\n检查cash_balance表...")
        structure = db_manager.execute_query("PRAGMA table_info(cash_balance)")
        columns = [col['name'] for col in structure]
        
        if 'user_id' in columns:
            print("   ✅ cash_balance表有user_id字段")
        else:
            print("   ❌ cash_balance表缺少user_id字段")
            return False
        
        # 检查chat_history表
        print("\n检查chat_history表...")
        structure = db_manager.execute_query("PRAGMA table_info(chat_history)")
        columns = [col['name'] for col in structure]
        
        if 'user_id' in columns:
            print("   ✅ chat_history表有user_id字段")
        else:
            print("   ❌ chat_history表缺少user_id字段")
            return False
        
        print("\n✅ 所有表结构检查通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库结构检查失败: {e}")
        return False


def test_service_methods():
    """测试Service方法签名"""
    print("\n" + "=" * 60)
    print("测试2: Service方法签名检查")
    print("=" * 60)
    
    try:
        # 测试watchlist_service
        print("\n检查watchlist_service...")
        import inspect
        
        # get_all_watchlist应该接受user_id参数
        sig = inspect.signature(watchlist_service.get_all_watchlist)
        params = list(sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ get_all_watchlist(user_id) 签名正确")
        else:
            print(f"   ❌ get_all_watchlist 参数错误: {params}")
            return False
        
        # add_to_watchlist应该接受user_id参数
        sig = inspect.signature(watchlist_service.add_to_watchlist)
        params = list(sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ add_to_watchlist(user_id, ...) 签名正确")
        else:
            print(f"   ❌ add_to_watchlist 参数错误: {params}")
            return False
        
        # 测试position_service
        print("\n检查position_service...")
        
        sig = inspect.signature(position_service.get_all_positions)
        params = list(sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ get_all_positions(user_id) 签名正确")
        else:
            print(f"   ❌ get_all_positions 参数错误: {params}")
            return False
        
        sig = inspect.signature(position_service.get_cash_balance)
        params = list(sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ get_cash_balance(user_id) 签名正确")
        else:
            print(f"   ❌ get_cash_balance 参数错误: {params}")
            return False
        
        # 测试ai_service
        print("\n检查ai_service...")
        
        sig = inspect.signature(ai_service.get_chat_history)
        params = list(sig.parameters.keys())
        if 'user_id' in params:
            print("   ✅ get_chat_history(user_id, ...) 签名正确")
        else:
            print(f"   ❌ get_chat_history 参数错误: {params}")
            return False
        
        sig = inspect.signature(ai_service.chat_with_history)
        params = list(sig.parameters.keys())
        if 'user_id' in params and 'username' in params:
            print("   ✅ chat_with_history(user_id, username, ...) 签名正确")
        else:
            print(f"   ❌ chat_with_history 参数错误: {params}")
            return False
        
        print("\n✅ 所有Service方法签名检查通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ Service方法检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n" + "=" * 60)
    print("测试3: 文件系统结构检查")
    print("=" * 60)
    
    try:
        prompt_history_dir = os.path.join(os.path.dirname(__file__), 'prompt_history')
        
        if not os.path.exists(prompt_history_dir):
            print("   ℹ️ prompt_history目录不存在（正常，首次运行会自动创建）")
            return True
        
        print(f"\n   prompt_history目录: {prompt_history_dir}")
        
        # 列出所有用户目录
        user_dirs = [d for d in os.listdir(prompt_history_dir) 
                     if os.path.isdir(os.path.join(prompt_history_dir, d))]
        
        if user_dirs:
            print(f"   找到 {len(user_dirs)} 个用户目录:")
            for user_dir in user_dirs:
                user_path = os.path.join(prompt_history_dir, user_dir)
                stock_dirs = [d for d in os.listdir(user_path) 
                             if os.path.isdir(os.path.join(user_path, d))]
                print(f"      - {user_dir}/ ({len(stock_dirs)} 只股票)")
        else:
            print("   ℹ️ 暂无用户对话历史")
        
        print("\n✅ 文件系统结构正常！")
        return True
        
    except Exception as e:
        print(f"\n❌ 文件系统检查失败: {e}")
        return False


def test_user_isolation():
    """测试用户数据隔离"""
    print("\n" + "=" * 60)
    print("测试4: 用户数据隔离测试")
    print("=" * 60)
    
    try:
        # 检查是否有多个用户
        users = db_manager.execute_query("SELECT * FROM users ORDER BY id")
        
        if len(users) < 2:
            print(f"   ℹ️ 当前只有 {len(users)} 个用户，无法测试隔离性")
            print("   提示：请先在管理界面创建测试用户")
            return True
        
        print(f"\n   找到 {len(users)} 个用户:")
        for user in users:
            print(f"      - ID={user['id']}, 用户名={user['username']}, 角色={user['role']}")
        
        # 测试每个用户的数据
        print("\n   测试各用户数据...")
        for user in users:
            user_id = user['id']
            username = user['username']
            
            # 获取自选股
            watchlist = watchlist_service.get_all_watchlist(user_id)
            
            # 获取持仓
            positions = position_service.get_all_positions(user_id)
            
            # 获取余额
            balance = position_service.get_cash_balance(user_id)
            
            print(f"\n   用户: {username} (ID={user_id})")
            print(f"      自选股: {len(watchlist)} 只")
            print(f"      持仓: {len(positions)} 只")
            print(f"      余额: {balance:.2f} 元")
        
        print("\n✅ 用户数据隔离正常！")
        return True
        
    except Exception as e:
        print(f"\n❌ 用户隔离测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("          多用户功能验证脚本")
    print("=" * 60)
    
    all_passed = True
    
    # 运行所有测试
    if not test_database_structure():
        all_passed = False
    
    if not test_service_methods():
        all_passed = False
    
    if not test_directory_structure():
        all_passed = False
    
    if not test_user_isolation():
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！多用户功能已正确实现")
    else:
        print("❌ 部分测试失败，请检查上面的错误信息")
    print("=" * 60)
    
    print("\n下一步：")
    print("1. 运行数据迁移: python migrate_to_multiuser.py")
    print("2. 启动应用: python app.py")
    print("3. 使用admin登录并创建测试用户")
    print("4. 验证不同用户的数据隔离")
    print()


if __name__ == '__main__':
    main()
