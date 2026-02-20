"""
测试登录功能
"""
import hashlib
from services.user_service import user_service

def test_login():
    """测试登录"""
    print("=" * 60)
    print("测试登录功能")
    print("=" * 60)
    
    # 测试正确的密码
    print("\n测试1: 使用正确的用户名和密码")
    user = user_service.authenticate('admin', 'admin123')
    if user:
        print("✅ 登录成功!")
        print(f"   用户ID: {user['id']}")
        print(f"   用户名: {user['username']}")
        print(f"   角色: {user['role']}")
    else:
        print("❌ 登录失败")
    
    # 测试错误的密码
    print("\n测试2: 使用错误的密码")
    user = user_service.authenticate('admin', 'wrongpassword')
    if user:
        print("❌ 不应该登录成功")
    else:
        print("✅ 正确拒绝了错误密码")
    
    # 测试不存在的用户
    print("\n测试3: 使用不存在的用户名")
    user = user_service.authenticate('nonexist', 'password')
    if user:
        print("❌ 不应该登录成功")
    else:
        print("✅ 正确拒绝了不存在的用户")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n✅ 现在可以使用以下信息登录:")
    print("   URL: http://localhost:5000/login")
    print("   用户名: admin")
    print("   密码: admin123")

if __name__ == '__main__':
    test_login()
