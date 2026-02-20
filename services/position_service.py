"""
持仓管理服务
"""
from database import db_manager
from services.stock_service import stock_service
from utils.logger import position_logger


class PositionService:
    """持仓管理服务类"""
    
    def get_all_positions(self, user_id):
        """获取指定用户的所有持仓"""
        query = "SELECT * FROM positions WHERE user_id = %s ORDER BY id"
        return db_manager.execute_query(query, (user_id,))
    
    def get_position(self, user_id, stock_code):
        """获取指定用户的单个持仓"""
        query = "SELECT * FROM positions WHERE user_id = %s AND stock_code = %s"
        return db_manager.execute_query(query, (user_id, stock_code), fetch_one=True)
    
    def add_or_update_position(self, user_id, stock_code, stock_name, quantity, cost_price):
        """添加或更新持仓（SQLite兼容版本）"""
        # 如果没有提供股票名称，尝试获取
        if not stock_name:
            stock_info = stock_service.get_stock_info(stock_code)
            if stock_info:
                stock_name = stock_info['name']
        
        # 先检查是否存在
        existing = self.get_position(user_id, stock_code)
        
        if existing:
            # 更新现有持仓
            query = """
            UPDATE positions 
            SET stock_name = ?, quantity = ?, cost_price = ?
            WHERE user_id = ? AND stock_code = ?
            """
            result = db_manager.execute_update(query, (stock_name, quantity, cost_price, user_id, stock_code))
        else:
            # 插入新持仓
            query = """
            INSERT INTO positions (user_id, stock_code, stock_name, quantity, cost_price)
            VALUES (?, ?, ?, ?, ?)
            """
            result = db_manager.execute_update(query, (user_id, stock_code, stock_name, quantity, cost_price))
        
        # 添加到自选股（如果不存在）
        if result:
            from services.watchlist_service import watchlist_service
            try:
                watchlist_service.add_to_watchlist(user_id, stock_code, stock_name)
            except Exception as e:
                print(f"添加到自选股失败: {e}")
        
        return result
    
    def delete_position(self, user_id, stock_code):
        """删除持仓"""
        query = "DELETE FROM positions WHERE user_id = %s AND stock_code = %s"
        return db_manager.execute_update(query, (user_id, stock_code))
    
    def update_position_price(self, user_id, stock_code, current_price):
        """更新持仓当前价格和盈亏"""
        position = self.get_position(user_id, stock_code)
        if not position:
            return False
        
        profit_loss = (current_price - position['cost_price']) * position['quantity']
        profit_loss_pct = ((current_price - position['cost_price']) / position['cost_price']) * 100
        
        query = """
        UPDATE positions 
        SET current_price = %s, profit_loss = %s, profit_loss_pct = %s
        WHERE user_id = %s AND stock_code = %s
        """
        return db_manager.execute_update(query, (current_price, profit_loss, profit_loss_pct, user_id, stock_code))
    
    def update_all_positions_price(self, user_id):
        """更新指定用户所有持仓的当前价格"""
        positions = self.get_all_positions(user_id)
        for pos in positions:
            try:
                # 获取最新价格
                daily_data = stock_service.get_stock_data_from_db(pos['stock_code'], 'daily', 1)
                if daily_data:
                    current_price = daily_data[0]['close']
                    self.update_position_price(user_id, pos['stock_code'], current_price)
            except Exception as e:
                print(f"更新持仓价格失败 {pos['stock_code']}: {e}")
        return True
    
    def get_cash_balance(self, user_id):
        """获取指定用户的现金余额"""
        query = "SELECT balance FROM cash_balance WHERE user_id = %s"
        result = db_manager.execute_query(query, (user_id,), fetch_one=True)
        if result:
            return result['balance']
        else:
            # 首次查询时初始化用户余额
            self.init_cash_balance(user_id)
            return 0
    
    def init_cash_balance(self, user_id):
        """初始化用户的现金余额"""
        query = "INSERT OR IGNORE INTO cash_balance (user_id, balance) VALUES (?, 0)"
        return db_manager.execute_update(query, (user_id,))
    
    def update_cash_balance(self, user_id, balance):
        """更新现金余额"""
        # 先确保用户有余额记录
        self.init_cash_balance(user_id)
        query = "UPDATE cash_balance SET balance = %s WHERE user_id = %s"
        return db_manager.execute_update(query, (balance, user_id))
    
    def get_portfolio_summary(self, user_id):
        """获取指定用户的投资组合汇总"""
        positions = self.get_all_positions(user_id)
        cash = self.get_cash_balance(user_id)
        
        total_market_value = sum(
            (pos['current_price'] or pos['cost_price']) * pos['quantity'] 
            for pos in positions
        )
        total_cost = sum(pos['cost_price'] * pos['quantity'] for pos in positions)
        total_profit_loss = sum(pos['profit_loss'] or 0 for pos in positions)
        
        return {
            'cash': float(cash),
            'positions_count': len(positions),
            'total_market_value': float(total_market_value),
            'total_cost': float(total_cost),
            'total_profit_loss': float(total_profit_loss),
            'total_assets': float(cash + total_market_value),
            'positions': positions
        }


# 创建全局持仓服务实例
position_service = PositionService()
