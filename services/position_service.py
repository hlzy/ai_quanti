"""
持仓管理服务
"""
from database import db_manager
from services.stock_service import stock_service


class PositionService:
    """持仓管理服务类"""
    
    def get_all_positions(self):
        """获取所有持仓"""
        query = "SELECT * FROM positions ORDER BY id"
        return db_manager.execute_query(query)
    
    def get_position(self, stock_code):
        """获取单个持仓"""
        query = "SELECT * FROM positions WHERE stock_code = %s"
        return db_manager.execute_query(query, (stock_code,), fetch_one=True)
    
    def add_or_update_position(self, stock_code, stock_name, quantity, cost_price):
        """添加或更新持仓（SQLite兼容版本）"""
        # 先检查是否存在
        existing = self.get_position(stock_code)
        
        if existing:
            # 更新现有持仓
            query = """
            UPDATE positions 
            SET stock_name = ?, quantity = ?, cost_price = ?
            WHERE stock_code = ?
            """
            return db_manager.execute_update(query, (stock_name, quantity, cost_price, stock_code))
        else:
            # 插入新持仓
            query = """
            INSERT INTO positions (stock_code, stock_name, quantity, cost_price)
            VALUES (?, ?, ?, ?)
            """
            return db_manager.execute_update(query, (stock_code, stock_name, quantity, cost_price))
    
    def delete_position(self, stock_code):
        """删除持仓"""
        query = "DELETE FROM positions WHERE stock_code = %s"
        return db_manager.execute_update(query, (stock_code,))
    
    def update_position_price(self, stock_code, current_price):
        """更新持仓当前价格和盈亏"""
        position = self.get_position(stock_code)
        if not position:
            return False
        
        profit_loss = (current_price - position['cost_price']) * position['quantity']
        profit_loss_pct = ((current_price - position['cost_price']) / position['cost_price']) * 100
        
        query = """
        UPDATE positions 
        SET current_price = %s, profit_loss = %s, profit_loss_pct = %s
        WHERE stock_code = %s
        """
        return db_manager.execute_update(query, (current_price, profit_loss, profit_loss_pct, stock_code))
    
    def update_all_positions_price(self):
        """更新所有持仓的当前价格"""
        positions = self.get_all_positions()
        for pos in positions:
            try:
                # 获取最新价格
                daily_data = stock_service.get_stock_data_from_db(pos['stock_code'], 'daily', 1)
                if daily_data:
                    current_price = daily_data[0]['close']
                    self.update_position_price(pos['stock_code'], current_price)
            except Exception as e:
                print(f"更新持仓价格失败 {pos['stock_code']}: {e}")
        return True
    
    def get_cash_balance(self):
        """获取现金余额"""
        query = "SELECT balance FROM cash_balance WHERE id = 1"
        result = db_manager.execute_query(query, fetch_one=True)
        return result['balance'] if result else 0
    
    def update_cash_balance(self, balance):
        """更新现金余额"""
        query = "UPDATE cash_balance SET balance = %s WHERE id = 1"
        return db_manager.execute_update(query, (balance,))
    
    def get_portfolio_summary(self):
        """获取投资组合汇总"""
        positions = self.get_all_positions()
        cash = self.get_cash_balance()
        
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
