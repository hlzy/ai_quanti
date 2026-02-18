"""
自选股服务
"""
from database import db_manager
from services.stock_service import stock_service


class WatchlistService:
    """自选股服务类"""
    
    def get_all_watchlist(self):
        """获取所有自选股"""
        query = "SELECT * FROM watchlist ORDER BY created_at DESC"
        return db_manager.execute_query(query)
    
    def add_to_watchlist(self, stock_code):
        """添加到自选股"""
        # 获取股票信息
        stock_info = stock_service.get_stock_info(stock_code)
        
        if not stock_info:
            return False
        
        ts_code = stock_info['ts_code']
        stock_name = stock_info.get('name', '')
        
        # 兼容MySQL和SQLite的语法
        from config import config
        if config.DATABASE_TYPE == 'sqlite':
            # SQLite使用INSERT OR REPLACE
            query = """
            INSERT OR REPLACE INTO watchlist (stock_code, stock_name)
            VALUES (%s, %s)
            """
        else:
            # MySQL使用ON DUPLICATE KEY UPDATE
            query = """
            INSERT INTO watchlist (stock_code, stock_name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE stock_name = VALUES(stock_name)
            """
        
        result = db_manager.execute_update(query, (ts_code, stock_name))
        
        # 更新股票数据
        if result:
            stock_service.update_stock_data(ts_code)
        
        return result > 0
    
    def remove_from_watchlist(self, stock_code):
        """从自选股移除"""
        query = "DELETE FROM watchlist WHERE stock_code = %s"
        return db_manager.execute_update(query, (stock_code,))
    
    def is_in_watchlist(self, stock_code):
        """检查是否在自选股中"""
        query = "SELECT COUNT(*) as count FROM watchlist WHERE stock_code = %s"
        result = db_manager.execute_query(query, (stock_code,), fetch_one=True)
        return result['count'] > 0


# 创建全局自选股服务实例
watchlist_service = WatchlistService()
