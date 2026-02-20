"""
自选股服务
"""
from database import db_manager
from services.stock_service import stock_service
from utils.logger import watchlist_logger


class WatchlistService:
    """自选股服务类"""
    
    def get_all_watchlist(self, user_id):
        """获取指定用户的所有自选股"""
        query = "SELECT * FROM watchlist WHERE user_id = %s ORDER BY created_at DESC"
        return db_manager.execute_query(query, (user_id,))
    
    def add_to_watchlist(self, user_id, stock_code, stock_name=None):
        """添加到自选股
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            stock_name: 股票名称（可选，如果不提供则自动获取）
        """
        # 如果没有提供股票名称，获取股票信息
        if not stock_name:
            stock_info = stock_service.get_stock_info(stock_code)
            if not stock_info:
                return False
            ts_code = stock_info['ts_code']
            stock_name = stock_info.get('name', '')
        else:
            # 使用提供的名称，但仍需要获取ts_code
            stock_info = stock_service.get_stock_info(stock_code)
            if not stock_info:
                return False
            ts_code = stock_info['ts_code']
        
        # SQLite使用INSERT OR IGNORE（避免重复添加）
        query = """
        INSERT OR IGNORE INTO watchlist (user_id, stock_code, stock_name)
        VALUES (?, ?, ?)
        """
        
        result = db_manager.execute_update(query, (user_id, ts_code, stock_name))
        
        # 如果是新添加的，更新股票数据
        if result:
            stock_service.update_stock_data(ts_code)
        
        return True
    
    def remove_from_watchlist(self, user_id, stock_code):
        """从自选股移除"""
        query = "DELETE FROM watchlist WHERE user_id = %s AND stock_code = %s"
        return db_manager.execute_update(query, (user_id, stock_code))
    
    def is_in_watchlist(self, user_id, stock_code):
        """检查是否在自选股中"""
        query = "SELECT COUNT(*) as count FROM watchlist WHERE user_id = %s AND stock_code = %s"
        result = db_manager.execute_query(query, (user_id, stock_code), fetch_one=True)
        return result['count'] > 0


# 创建全局自选股服务实例
watchlist_service = WatchlistService()
