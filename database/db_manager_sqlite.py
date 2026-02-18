"""
SQLite数据库管理模块 - 轻量级替代方案
适用于开发、测试环境，无需安装MySQL服务
"""
import sqlite3
from contextlib import contextmanager
from config import config
import os


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self):
        # 创建数据目录
        self.db_dir = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = os.path.join(self.db_dir, 'quanti_stock.db')
        
        print(f"SQLite数据库路径: {self.db_path}")
    
    def dict_factory(self, cursor, row):
        """将查询结果转换为字典"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = self.dict_factory
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
        # 转换MySQL占位符 %s 为 SQLite 占位符 ?
        query = query.replace('%s', '?')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        # 转换MySQL占位符
        query = query.replace('%s', '?')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    def execute_many(self, query, params_list):
        """批量执行操作"""
        # 转换MySQL占位符
        query = query.replace('%s', '?')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def init_database(self):
        """初始化数据库表结构"""
        print(f"初始化SQLite数据库: {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 自选股表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL UNIQUE,
                stock_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_stock_code 
            ON watchlist(stock_code)
            """)
            
            # 股票日K线数据表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                UNIQUE(ts_code, trade_date)
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_daily_ts_code 
            ON stock_daily(ts_code)
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_daily_trade_date 
            ON stock_daily(trade_date)
            """)
            
            # 股票周K线数据表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_weekly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                UNIQUE(ts_code, trade_date)
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_weekly_ts_code 
            ON stock_weekly(ts_code)
            """)
            
            # 股票分钟K线数据表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_minute (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_time TIMESTAMP NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                UNIQUE(ts_code, trade_time)
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_minute_ts_code 
            ON stock_minute(ts_code)
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_minute_trade_time 
            ON stock_minute(trade_time)
            """)
            
            # 技术指标表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                ema_12 REAL,
                ema_26 REAL,
                rsi_6 REAL,
                rsi_12 REAL,
                rsi_24 REAL,
                UNIQUE(ts_code, trade_date)
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_indicators_ts_code 
            ON stock_indicators(ts_code)
            """)
            
            # 持仓数据表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL UNIQUE,
                stock_name TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price REAL NOT NULL,
                current_price REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 现金余额表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_balance (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance REAL NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 初始化现金余额
            cursor.execute("""
            INSERT OR IGNORE INTO cash_balance (id, balance) 
            VALUES (1, 0)
            """)
            
            # AI对话记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_stock_code 
            ON chat_history(stock_code)
            """)
            
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_history_created_at 
            ON chat_history(created_at)
            """)
            
            # 初始对话模版表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            print("SQLite数据库初始化完成！")


# 创建全局数据库管理器实例
db_manager = DatabaseManager()
