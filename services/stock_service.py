"""
股票数据服务
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from database import db_manager
from config import config


class StockService:
    """股票数据服务类"""
    
    def __init__(self):
        """初始化Tushare API"""
        if config.TUSHARE_TOKEN:
            ts.set_token(config.TUSHARE_TOKEN)
            self.pro = ts.pro_api()
        else:
            raise ValueError("Tushare Token未配置，请在.env文件中设置TUSHARE_TOKEN")
    
    def normalize_stock_code(self, stock_code):
        """标准化股票代码
        支持A股、港股、美股等多市场
        
        规则：
        - A股上海：6开头的6位数字
        - A股深圳：0或3开头的6位数字
        - 港股：5位或以下纯数字（如 00700, 02050）
        - 已带后缀的直接返回
        """
        if '.' in stock_code:
            return stock_code
        
        # 必须是纯数字
        if not stock_code.isdigit():
            return f"{stock_code}.SZ"  # 默认深圳
        
        # 6位数字
        if len(stock_code) == 6:
            if stock_code.startswith('6'):
                return f"{stock_code}.SH"  # 上海
            else:
                return f"{stock_code}.SZ"  # 深圳
        
        # 5位及以下数字，判断为港股
        elif len(stock_code) <= 5:
            # 补齐到5位
            padded_code = stock_code.zfill(5)
            return f"{padded_code}.HK"
        
        # 其他情况默认深圳
        else:
            return f"{stock_code}.SZ"
    
    def get_stock_info(self, stock_code):
        """获取股票基本信息"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            # 判断市场类型
            if ts_code.endswith('.HK'):
                # 港股查询
                df = self.pro.hk_basic(ts_code=ts_code, fields='ts_code,name,list_date,list_status')
                if not df.empty:
                    return df.iloc[0].to_dict()
            else:
                # A股查询
                df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,list_date')
                if not df.empty:
                    return df.iloc[0].to_dict()
            
            return None
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_daily_data(self, stock_code, start_date=None, end_date=None):
        """获取日K线数据"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 根据市场选择不同的API
            if ts_code.endswith('.HK'):
                # 港股日线数据
                df = self.pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                # A股日线数据
                df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date')
            return df.to_dict('records')
        except Exception as e:
            print(f"获取日K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_weekly_data(self, stock_code, start_date=None, end_date=None):
        """获取周K线数据"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=720)).strftime('%Y%m%d')
            
            # 根据市场选择不同的API
            if ts_code.endswith('.HK'):
                # 港股周线数据
                df = self.pro.hk_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                # A股周线数据
                df = self.pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date')
            return df.to_dict('records')
        except Exception as e:
            print(f"获取周K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_minute_data(self, stock_code, freq='1min'):
        """获取分钟K线数据
        
        Args:
            stock_code: 股票代码
            freq: 频率，默认1min（1分钟），可选：1min, 5min, 15min, 30min, 60min
        
        Returns:
            最近2天的分钟K线数据
        """
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            # 港股暂不支持分钟数据
            if ts_code.endswith('.HK'):
                print(f"港股暂不支持分钟K线数据")
                return []
            
            # 获取最近2天的数据（考虑周末，取4天）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=4)
            
            # Tushare分钟数据接口
            df = ts.pro_bar(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adj='qfq',  # 前复权
                asset='E'   # 股票
            )
            
            if df is None or df.empty:
                return []
            
            # 转换时间格式
            df['trade_time'] = pd.to_datetime(df['trade_date'] + ' ' + df['trade_time'])
            df = df.sort_values('trade_time')
            
            # 只保留最近2天的交易时间数据（1440分钟）
            df = df.tail(1440)
            
            return df.to_dict('records')
        except Exception as e:
            print(f"获取分钟K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        if df.empty:
            return df
        
        # 确保数据按日期排序
        df = df.sort_values('trade_date')
        
        # 计算EMA
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # 计算MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
        rs = gain / loss
        df['rsi_6'] = 100 - (100 / (1 + rs))
        
        gain = (delta.where(delta > 0, 0)).rolling(window=12).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
        rs = gain / loss
        df['rsi_12'] = 100 - (100 / (1 + rs))
        
        gain = (delta.where(delta > 0, 0)).rolling(window=24).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=24).mean()
        rs = gain / loss
        df['rsi_24'] = 100 - (100 / (1 + rs))
        
        return df
    
    def save_daily_data(self, data_list):
        """保存日K线数据到数据库"""
        if not data_list:
            return 0
        
        from config import config
        if config.DATABASE_TYPE == 'sqlite':
            # SQLite使用INSERT OR REPLACE
            query = """
            INSERT OR REPLACE INTO stock_daily (ts_code, trade_date, open, high, low, close, volume, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            # 转换为元组列表，并处理Timestamp类型
            params_list = []
            for d in data_list:
                trade_date = d['trade_date']
                # 转换pandas Timestamp为字符串
                if hasattr(trade_date, 'strftime'):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                params_list.append((
                    d['ts_code'], trade_date, d['open'], d['high'], d['low'], 
                    d['close'], d.get('vol', 0), d.get('amount', 0)
                ))
        else:
            # MySQL使用命名占位符和ON DUPLICATE KEY UPDATE
            query = """
            INSERT INTO stock_daily (ts_code, trade_date, open, high, low, close, volume, amount)
            VALUES (%(ts_code)s, %(trade_date)s, %(open)s, %(high)s, %(low)s, %(close)s, %(vol)s, %(amount)s)
            ON DUPLICATE KEY UPDATE
            open=VALUES(open), high=VALUES(high), low=VALUES(low), 
            close=VALUES(close), volume=VALUES(volume), amount=VALUES(amount)
            """
            params_list = data_list
        
        return db_manager.execute_many(query, params_list)
    
    def save_weekly_data(self, data_list):
        """保存周K线数据到数据库"""
        if not data_list:
            return 0
        
        from config import config
        if config.DATABASE_TYPE == 'sqlite':
            # SQLite使用INSERT OR REPLACE
            query = """
            INSERT OR REPLACE INTO stock_weekly (ts_code, trade_date, open, high, low, close, volume, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            # 转换为元组列表，并处理Timestamp类型
            params_list = []
            for d in data_list:
                trade_date = d['trade_date']
                # 转换pandas Timestamp为字符串
                if hasattr(trade_date, 'strftime'):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                params_list.append((
                    d['ts_code'], trade_date, d['open'], d['high'], d['low'], 
                    d['close'], d.get('vol', 0), d.get('amount', 0)
                ))
        else:
            # MySQL使用命名占位符和ON DUPLICATE KEY UPDATE
            query = """
            INSERT INTO stock_weekly (ts_code, trade_date, open, high, low, close, volume, amount)
            VALUES (%(ts_code)s, %(trade_date)s, %(open)s, %(high)s, %(low)s, %(close)s, %(vol)s, %(amount)s)
            ON DUPLICATE KEY UPDATE
            open=VALUES(open), high=VALUES(high), low=VALUES(low), 
            close=VALUES(close), volume=VALUES(volume), amount=VALUES(amount)
            """
            params_list = data_list
        
        return db_manager.execute_many(query, params_list)
    
    def save_minute_data(self, data_list):
        """保存分钟K线数据到数据库"""
        if not data_list:
            return 0
        
        from config import config
        if config.DATABASE_TYPE == 'sqlite':
            query = """
            INSERT OR REPLACE INTO stock_minute (ts_code, trade_time, open, high, low, close, volume, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params_list = []
            for d in data_list:
                trade_time = d['trade_time']
                if hasattr(trade_time, 'strftime'):
                    trade_time = trade_time.strftime('%Y-%m-%d %H:%M:%S')
                params_list.append((
                    d['ts_code'], trade_time, d['open'], d['high'], d['low'],
                    d['close'], d.get('vol', 0), d.get('amount', 0)
                ))
        else:
            query = """
            INSERT INTO stock_minute (ts_code, trade_time, open, high, low, close, volume, amount)
            VALUES (%(ts_code)s, %(trade_time)s, %(open)s, %(high)s, %(low)s, %(close)s, %(vol)s, %(amount)s)
            ON DUPLICATE KEY UPDATE
            open=VALUES(open), high=VALUES(high), low=VALUES(low),
            close=VALUES(close), volume=VALUES(volume), amount=VALUES(amount)
            """
            params_list = data_list
        
        return db_manager.execute_many(query, params_list)
    
    def save_indicators(self, stock_code, df):
        """保存技术指标到数据库"""
        if df.empty:
            return 0
        
        # 只保存有效的指标数据
        df = df.dropna(subset=['macd', 'macd_signal', 'rsi_6'])
        
        data_list = []
        for _, row in df.iterrows():
            data_list.append({
                'ts_code': stock_code,
                'trade_date': row['trade_date'],
                'macd': row['macd'],
                'macd_signal': row['macd_signal'],
                'macd_hist': row['macd_hist'],
                'ema_12': row['ema_12'],
                'ema_26': row['ema_26'],
                'rsi_6': row['rsi_6'],
                'rsi_12': row['rsi_12'],
                'rsi_24': row['rsi_24']
            })
        
        if not data_list:
            return 0
        
        from config import config
        if config.DATABASE_TYPE == 'sqlite':
            # SQLite使用INSERT OR REPLACE
            query = """
            INSERT OR REPLACE INTO stock_indicators (ts_code, trade_date, macd, macd_signal, macd_hist, 
                                         ema_12, ema_26, rsi_6, rsi_12, rsi_24)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # 转换为元组列表，并处理Timestamp类型
            params_list = []
            for d in data_list:
                trade_date = d['trade_date']
                # 转换pandas Timestamp为字符串
                if hasattr(trade_date, 'strftime'):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                params_list.append((
                    d['ts_code'], trade_date, d['macd'], d['macd_signal'], d['macd_hist'],
                    d['ema_12'], d['ema_26'], d['rsi_6'], d['rsi_12'], d['rsi_24']
                ))
        else:
            # MySQL使用命名占位符和ON DUPLICATE KEY UPDATE
            query = """
            INSERT INTO stock_indicators (ts_code, trade_date, macd, macd_signal, macd_hist, 
                                         ema_12, ema_26, rsi_6, rsi_12, rsi_24)
            VALUES (%(ts_code)s, %(trade_date)s, %(macd)s, %(macd_signal)s, %(macd_hist)s,
                    %(ema_12)s, %(ema_26)s, %(rsi_6)s, %(rsi_12)s, %(rsi_24)s)
            ON DUPLICATE KEY UPDATE
            macd=VALUES(macd), macd_signal=VALUES(macd_signal), macd_hist=VALUES(macd_hist),
            ema_12=VALUES(ema_12), ema_26=VALUES(ema_26),
            rsi_6=VALUES(rsi_6), rsi_12=VALUES(rsi_12), rsi_24=VALUES(rsi_24)
            """
            params_list = data_list
        
        return db_manager.execute_many(query, params_list)
    
    def update_stock_data(self, stock_code):
        """更新股票数据（分钟K、日K线、周K线、指标）"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            # 获取1分钟K线数据
            minute_data = self.fetch_minute_data(stock_code)
            if minute_data:
                self.save_minute_data(minute_data)
            
            # 获取日K线数据
            daily_data = self.fetch_daily_data(stock_code)
            if daily_data:
                self.save_daily_data(daily_data)
                
                # 计算并保存指标
                df = pd.DataFrame(daily_data)
                df = self.calculate_indicators(df)
                self.save_indicators(ts_code, df)
            
            # 获取周K线数据
            weekly_data = self.fetch_weekly_data(stock_code)
            if weekly_data:
                self.save_weekly_data(weekly_data)
            
            return True
        except Exception as e:
            print(f"更新股票数据失败: {e}")
            return False
    
    def get_stock_data_from_db(self, stock_code, period='daily', days=60):
        """从数据库获取股票数据
        
        Args:
            stock_code: 股票代码
            period: 'minute', 'daily', 'weekly'
            days: 天数（对于minute，表示分钟数）
        """
        if period == 'minute':
            # 分钟数据，days参数表示分钟数
            query = """
            SELECT * FROM stock_minute
            WHERE ts_code = %s
            ORDER BY trade_time DESC
            LIMIT %s
            """
            data = db_manager.execute_query(query, (stock_code, days))
            return list(reversed(data))
        else:
            table = 'stock_daily' if period == 'daily' else 'stock_weekly'
            query = f"""
            SELECT * FROM {table}
            WHERE ts_code = %s
            ORDER BY trade_date DESC
            LIMIT %s
            """
            data = db_manager.execute_query(query, (stock_code, days))
            return list(reversed(data))
    
    
    def get_indicators_from_db(self, stock_code, days=60):
        """从数据库获取技术指标"""
        query = """
        SELECT * FROM stock_indicators
        WHERE ts_code = %s
        ORDER BY trade_date DESC
        LIMIT %s
        """
        
        data = db_manager.execute_query(query, (stock_code, days))
        return list(reversed(data))


# 创建全局股票服务实例
stock_service = StockService()
