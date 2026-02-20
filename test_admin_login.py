#!/usr/bin/env python3
"""
测试管理员登录和管理界面
"""
import requests
import json

BASE_URL = 'http://localhost:5000'

def test_admin_login():
    """测试管理员登录"""
    print("=" * 60)
    print("测试管理员登录")
    print("=" * 60)
    
    session = requests.Session()
    
    # 1. 测试登录
    print("\n1. 测试管理员登录...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f'{BASE_URL}/api/auth/login', json=login_data)
    result = response.json()
    
    if result['success']:
        print(f"✅ 登录成功")
        print(f"   用户信息: {result['user']}")
    else:
        print(f"❌ 登录失败: {result['message']}")
        return
    
    # 2. 测试获取用户列表
    print("\n2. 测试获取用户列表...")
    response = session.get(f'{BASE_URL}/api/admin/users')
    users = response.json()
    
    print(f"✅ 成功获取 {len(users)} 个用户:")
    for user in users:
        print(f"   - ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
    
    # 3. 测试创建用户
    print("\n3. 测试创建普通用户...")
    new_user_data = {
        'username': 'testuser',
        'password': 'test123456',
        'role': 'user'
    }
    
    response = session.post(f'{BASE_URL}/api/admin/users', json=new_user_data)
    result = response.json()
    
    if result['success']:
        print(f"✅ 创建用户成功: {result['message']}")
        test_user_id = result.get('user_id')
    else:
        print(f"⚠️  {result['message']}")
        # 可能用户已存在，尝试获取
        response = session.get(f'{BASE_URL}/api/admin/users')
        users = response.json()
        test_user = next((u for u in users if u['username'] == 'testuser'), None)
        if test_user:
            test_user_id = test_user['id']
            print(f"   用户已存在，ID: {test_user_id}")
        else:
            test_user_id = None
    
    # 4. 再次获取用户列表
    print("\n4. 再次获取用户列表...")
    response = session.get(f'{BASE_URL}/api/admin/users')
    users = response.json()
    
    print(f"✅ 当前共有 {len(users)} 个用户:")
    for user in users:
        print(f"   - ID: {user['id']}, 用户名: {user['username']}, 角色: {user['role']}")
    
    # 5. 测试删除用户（可选，如果创建成功）
    if test_user_id and input("\n是否删除测试用户? (y/n): ").lower() == 'y':
        print(f"\n5. 测试删除用户 (ID: {test_user_id})...")
        response = session.delete(f'{BASE_URL}/api/admin/users/{test_user_id}')
        result = response.json()
        
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_admin_login()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Flask应用正在运行：")
        print("   python app.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
