"""
项目配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Tushare配置
    TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
    
    # OpenRouter配置
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    SITE_URL = os.getenv('SITE_URL', 'https://ai-quant.example.com')
    SITE_NAME = os.getenv('SITE_NAME', 'AI量化股票分析工具')
    
    # 数据库配置
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'mysql')  # mysql 或 sqlite
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'quanti_stock')
    
    # 数据库连接字符串
    @property
    def DATABASE_URI(self):
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
    
    # 项目路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STRATEGY_DIR = os.path.join(BASE_DIR, 'strategy')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    
    # 确保必要的目录存在
    @classmethod
    def init_directories(cls):
        """初始化必要的目录"""
        os.makedirs(cls.STRATEGY_DIR, exist_ok=True)
        os.makedirs(os.path.join(cls.STATIC_DIR, 'charts'), exist_ok=True)
        os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)


# 创建全局配置实例
config = Config()
config.init_directories()
