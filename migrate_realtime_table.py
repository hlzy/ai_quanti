"""
数据库迁移脚本：升级 stock_realtime 表结构
添加完整的实时行情字段
"""
import sqlite3
import os

DB_PATH = 'data/quanti_stock.db'

def migrate():
    """执行数据库迁移"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("开始迁移 stock_realtime 表...")
        
        # 1. 检查旧表是否存在
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='stock_realtime'
        """)
        
        if cursor.fetchone():
            print("  - 发现旧表，开始备份...")
            
            # 2. 重命名旧表为备份表
            cursor.execute("ALTER TABLE stock_realtime RENAME TO stock_realtime_old")
            print("  - 旧表已重命名为 stock_realtime_old")
        
        # 3. 创建新表结构
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_realtime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL UNIQUE,
            stock_name TEXT,
            price REAL,
            open REAL,
            pre_close REAL,
            high REAL,
            low REAL,
            volume REAL,
            amount REAL,
            change REAL,
            change_percent REAL,
            turnover_ratio REAL,
            amplitude REAL,
            total_mv REAL,
            circ_mv REAL,
            pe REAL,
            pe_ttm REAL,
            pb REAL,
            dv_ratio REAL,
            trade_date TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("  - 新表结构创建成功")
        
        # 4. 如果有旧数据，迁移到新表
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='stock_realtime_old'
        """)
        
        if cursor.fetchone():
            print("  - 开始迁移旧数据...")
            cursor.execute("""
            INSERT INTO stock_realtime (ts_code, price, trade_date, updated_at)
            SELECT ts_code, price, trade_date, updated_at
            FROM stock_realtime_old
            """)
            
            migrated_count = cursor.rowcount
            print(f"  - 已迁移 {migrated_count} 条记录")
            
            # 删除备份表
            cursor.execute("DROP TABLE stock_realtime_old")
            print("  - 备份表已删除")
        
        # 5. 创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_realtime_ts_code 
        ON stock_realtime(ts_code)
        """)
        print("  - 索引创建成功")
        
        conn.commit()
        print("✅ 迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("stock_realtime 表结构升级脚本")
    print("=" * 50)
    migrate()
