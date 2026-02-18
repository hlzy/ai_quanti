"""
环境检查脚本
用于检查项目运行所需的环境和依赖
"""
import sys
import os

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print(f"   需要Python 3.8或更高版本")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")
    required_packages = [
        'flask',
        'flask_cors',
        'pymysql',
        'pandas',
        'numpy',
        'tushare',
        'dotenv',
        'matplotlib',
        'mplfinance',
        'requests'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            elif package == 'flask_cors':
                __import__('flask_cors')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  请安装缺失的依赖:")
        print(f"   pip install {' '.join(missing)}")
        return False
    return True

def check_env_file():
    """检查环境变量文件"""
    print("\n🔍 检查环境配置...")
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"   ❌ {env_file} 文件不存在")
        print(f"   请复制 .env.example 为 .env 并填写配置")
        return False
    
    print(f"   ✅ {env_file} 存在")
    
    # 检查必要的环境变量
    required_vars = {
        'TUSHARE_TOKEN': 'Tushare API Token',
        'QWEN_API_KEY': '通义千问 API Key',
        'MYSQL_HOST': 'MySQL主机地址',
        'MYSQL_USER': 'MySQL用户名',
        'MYSQL_PASSWORD': 'MySQL密码',
        'MYSQL_DATABASE': 'MySQL数据库名'
    }
    
    from dotenv import load_dotenv
    load_dotenv()
    
    missing_vars = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            print(f"   ⚠️  {var} 未配置 ({desc})")
            missing_vars.append(var)
        else:
            # 隐藏敏感信息
            masked_value = value[:8] + '...' if len(value) > 8 else '***'
            print(f"   ✅ {var} = {masked_value}")
    
    if missing_vars:
        print(f"\n⚠️  请在 .env 文件中配置以下变量:")
        for var in missing_vars:
            print(f"   - {var}: {required_vars[var]}")
        return False
    
    return True

def check_database():
    """检查数据库连接"""
    print("\n🔍 检查数据库连接...")
    
    try:
        from config import config
        
        # 检查是否使用SQLite
        db_type = os.getenv('DATABASE_TYPE', 'mysql')
        
        if db_type == 'sqlite':
            print(f"   ℹ️  使用SQLite数据库")
            print(f"   数据文件: data/quanti_stock.db")
            return True
        
        # 检查MySQL连接
        import pymysql
        
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"   ✅ MySQL连接成功")
        print(f"   MySQL版本: {version[0]}")
        
        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{config.MYSQL_DATABASE}'")
        if cursor.fetchone():
            print(f"   ✅ 数据库 '{config.MYSQL_DATABASE}' 已存在")
        else:
            print(f"   ⚠️  数据库 '{config.MYSQL_DATABASE}' 不存在，将自动创建")
        
        conn.close()
        return True
        
    except ImportError as e:
        print(f"   ❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        print(f"\n💡 解决方案:")
        print(f"   方案1: 安装并启动MySQL")
        print(f"      brew install mysql")
        print(f"      brew services start mysql")
        print(f"\n   方案2: 使用SQLite（无需安装数据库）")
        print(f"      在 .env 文件中添加: DATABASE_TYPE=sqlite")
        print(f"\n   方案3: 使用Docker")
        print(f"      docker run -d --name mysql-quanti \\")
        print(f"        -e MYSQL_ROOT_PASSWORD=admin123 \\")
        print(f"        -e MYSQL_DATABASE=quanti_stock \\")
        print(f"        -p 3306:3306 mysql:8.0")
        return False

def check_directories():
    """检查必要的目录"""
    print("\n🔍 检查项目目录...")
    
    required_dirs = [
        'database',
        'services',
        'templates',
        'static',
        'strategy'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主检查流程"""
    print("=" * 60)
    print("🚀 AI量化股票分析工具 - 环境检查")
    print("=" * 60)
    
    results = []
    
    # 执行各项检查
    results.append(("Python版本", check_python_version()))
    results.append(("依赖包", check_dependencies()))
    results.append(("环境配置", check_env_file()))
    results.append(("项目目录", check_directories()))
    results.append(("数据库连接", check_database()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 检查结果总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 所有检查通过！可以启动应用:")
        print("   python app.py")
        return 0
    else:
        print("\n⚠️  存在问题，请根据上述提示进行修复")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
