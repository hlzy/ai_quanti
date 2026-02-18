"""
数据库管理模块
"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import config


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.config = {
            'host': config.MYSQL_HOST,
            'port': config.MYSQL_PORT,
            'user': config.MYSQL_USER,
            'password': config.MYSQL_PASSWORD,
            'database': config.MYSQL_DATABASE,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor
        }
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = pymysql.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False):
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount
    
    def execute_many(self, query, params_list):
        """批量执行操作"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                return cursor.rowcount
    
    def init_database(self):
        """初始化数据库表结构"""
        # 创建数据库（如果不存在）
        temp_config = self.config.copy()
        temp_config.pop('database')
        
        with pymysql.connect(**temp_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # 创建表结构
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 自选股表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(20) NOT NULL UNIQUE,
                    stock_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stock_code (stock_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 股票日K线数据表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_daily (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    ts_code VARCHAR(20) NOT NULL,
                    trade_date DATE NOT NULL,
                    open DECIMAL(10, 2),
                    high DECIMAL(10, 2),
                    low DECIMAL(10, 2),
                    close DECIMAL(10, 2),
                    volume BIGINT,
                    amount DECIMAL(20, 2),
                    UNIQUE KEY uk_stock_date (ts_code, trade_date),
                    INDEX idx_ts_code (ts_code),
                    INDEX idx_trade_date (trade_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 股票周K线数据表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_weekly (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    ts_code VARCHAR(20) NOT NULL,
                    trade_date DATE NOT NULL,
                    open DECIMAL(10, 2),
                    high DECIMAL(10, 2),
                    low DECIMAL(10, 2),
                    close DECIMAL(10, 2),
                    volume BIGINT,
                    amount DECIMAL(20, 2),
                    UNIQUE KEY uk_stock_date (ts_code, trade_date),
                    INDEX idx_ts_code (ts_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 技术指标表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_indicators (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    ts_code VARCHAR(20) NOT NULL,
                    trade_date DATE NOT NULL,
                    macd DECIMAL(10, 4),
                    macd_signal DECIMAL(10, 4),
                    macd_hist DECIMAL(10, 4),
                    ema_12 DECIMAL(10, 2),
                    ema_26 DECIMAL(10, 2),
                    rsi_6 DECIMAL(10, 2),
                    rsi_12 DECIMAL(10, 2),
                    rsi_24 DECIMAL(10, 2),
                    UNIQUE KEY uk_stock_date (ts_code, trade_date),
                    INDEX idx_ts_code (ts_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 持仓数据表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(20) NOT NULL,
                    stock_name VARCHAR(100),
                    quantity INT NOT NULL DEFAULT 0,
                    cost_price DECIMAL(10, 2) NOT NULL,
                    current_price DECIMAL(10, 2),
                    profit_loss DECIMAL(15, 2),
                    profit_loss_pct DECIMAL(10, 2),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_stock_code (stock_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 现金余额表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_balance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    balance DECIMAL(15, 2) NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 初始化现金余额
                cursor.execute("INSERT IGNORE INTO cash_balance (id, balance) VALUES (1, 0)")
                
                # AI对话记录表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(20) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stock_code (stock_code),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 初始对话模版表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)


# 创建全局数据库管理器实例
db_manager = DatabaseManager()
