"""
股票数据服务
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from database import db_manager
from config import config
from utils.logger import stock_logger
import time


class StockService:
    """股票数据服务类"""
    
    def __init__(self):
        """初始化Tushare API"""
        if config.TUSHARE_TOKEN:
            ts.set_token(config.TUSHARE_TOKEN)
            self.pro = ts.pro_api()
            stock_logger.info("Stock service initialized successfully")
        else:
            stock_logger.error("Tushare Token未配置")
            raise ValueError("Tushare Token未配置，请在.env文件中设置TUSHARE_TOKEN")
        
        # API调用限流
        self._last_api_call = {}  # 记录每个接口的最后调用时间
    
    def detect_code_type(self, stock_code):
        """检测代码类型
        
        Returns:
            'stock': A股
            'index': 指数
            'fund': ETF/基金
        """
        # 如果已带后缀
        if '.' in stock_code:
            code_only = stock_code.split('.')[0]
        else:
            code_only = stock_code
        
        # 指数判断
        # 上证指数：000001等
        # 深证指数：399001等
        if code_only.startswith('000') or code_only.startswith('399'):
            return 'index'
        
        # ETF判断
        # 上交所ETF: 51、52开头
        # 深交所ETF: 15、16开头
        if code_only.startswith(('51', '52', '15', '16')):
            return 'fund'
        
        # 默认为A股
        return 'stock'
    
    def _rate_limit_check(self, api_name, min_interval=30):
        """API限流检查
        
        Args:
            api_name: API名称
            min_interval: 最小调用间隔（秒），默认30秒
        """
        current_time = time.time()
        last_call = self._last_api_call.get(api_name, 0)
        
        if current_time - last_call < min_interval:
            wait_time = min_interval - (current_time - last_call)
            stock_logger.info(f"API限流: {api_name} 等待 {wait_time:.1f} 秒")
            time.sleep(wait_time)
        
        self._last_api_call[api_name] = time.time()
    
    def normalize_stock_code(self, stock_code):
        """标准化股票代码
        支持A股、指数、ETF等
        
        规则：
        - A股上海：6开头的6位数字 -> .SH
        - A股深圳：0或3开头的6位数字 -> .SZ
        - 上证指数：000001等 -> .SH
        - 深证指数：399001等 -> .SZ
        - 上交所ETF：51、52开头 -> .SH
        - 深交所ETF：15、16开头 -> .SZ
        - 已带后缀的直接返回
        """
        if '.' in stock_code:
            return stock_code
        
        # 必须是纯数字
        if not stock_code.isdigit():
            return f"{stock_code}.SZ"  # 默认深圳
        
        # 6位数字
        if len(stock_code) == 6:
            # 上证指数（000开头）
            if stock_code.startswith('000'):
                return f"{stock_code}.SH"
            # 深证指数（399开头）
            elif stock_code.startswith('399'):
                return f"{stock_code}.SZ"
            # 上交所ETF（51、52开头）
            elif stock_code.startswith(('51', '52')):
                return f"{stock_code}.SH"
            # 深交所ETF（15、16开头）
            elif stock_code.startswith(('15', '16')):
                return f"{stock_code}.SZ"
            # A股上海（6开头）
            elif stock_code.startswith('6'):
                return f"{stock_code}.SH"
            # A股深圳（0、3开头）
            else:
                return f"{stock_code}.SZ"
        
        # 其他情况默认深圳
        else:
            return f"{stock_code}.SZ"
    
    def get_stock_info(self, stock_code):
        """获取股票/指数/ETF基本信息"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            code_type = self.detect_code_type(stock_code)
            
            stock_logger.debug(f"查询股票信息: {ts_code}, 类型: {code_type}")
            
            if code_type == 'index':
                # 指数查询
                df = self.pro.index_basic(ts_code=ts_code, fields='ts_code,name,market,publisher,category')
                if not df.empty:
                    info = df.iloc[0].to_dict()
                    info['type'] = 'index'
                    stock_logger.info(f"查询到指数: {info.get('name')} ({ts_code})")
                    return info
            elif code_type == 'fund':
                # ETF查询
                df = self.pro.fund_basic(ts_code=ts_code, market='E', fields='ts_code,name,management,fund_type,issue_date,list_date')
                if not df.empty:
                    info = df.iloc[0].to_dict()
                    info['type'] = 'fund'
                    stock_logger.info(f"查询到ETF: {info.get('name')} ({ts_code})")
                    return info
            else:
                # A股查询
                df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,list_date')
                if not df.empty:
                    info = df.iloc[0].to_dict()
                    info['type'] = 'stock'
                    stock_logger.info(f"查询到股票: {info.get('name')} ({ts_code})")
                    return info
            
            stock_logger.warning(f"未查询到股票信息: {ts_code}")
            return None
        except Exception as e:
            stock_logger.error(f"获取股票信息失败: {stock_code}", exc_info=True)
            print(f"获取信息失败: {e}")
            return None
    
    def fetch_daily_data(self, stock_code, start_date=None, end_date=None):
        """获取日K线数据（支持A股、指数、ETF）"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            code_type = self.detect_code_type(stock_code)
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            stock_logger.debug(f"获取日K线: {ts_code}, 日期范围: {start_date} - {end_date}")
            
            # 根据类型选择不同的API
            if code_type == 'index':
                # 指数日线数据
                df = self.pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            elif code_type == 'fund':
                # ETF日线数据
                df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                # A股日线数据
                df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                stock_logger.warning(f"日K线数据为空: {ts_code}")
                return []
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date')
            stock_logger.info(f"获取日K线成功: {ts_code}, 数据条数: {len(df)}")
            return df.to_dict('records')
        except Exception as e:
            stock_logger.error(f"获取日K线失败: {stock_code}, {start_date} - {end_date}", exc_info=True)
            print(f"获取日K线数据失败: {e}")
            return []
    
    def fetch_weekly_data(self, stock_code, start_date=None, end_date=None):
        """获取周K线数据（支持A股、指数、ETF）"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            code_type = self.detect_code_type(stock_code)
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=720)).strftime('%Y%m%d')
            
            # 根据类型选择不同的API
            if code_type == 'index':
                # 指数周线数据
                df = self.pro.index_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            elif code_type == 'fund':
                # ETF周线数据 - Tushare可能不支持，使用日线数据聚合
                daily_df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if daily_df.empty:
                    return []
                # 转换为周线
                daily_df['trade_date'] = pd.to_datetime(daily_df['trade_date'])
                daily_df = daily_df.set_index('trade_date')
                weekly_df = daily_df.resample('W').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'vol': 'sum',
                    'amount': 'sum'
                }).dropna()
                weekly_df['ts_code'] = ts_code
                weekly_df = weekly_df.reset_index()
                weekly_df = weekly_df.rename(columns={'trade_date': 'trade_date'})
                df = weekly_df
            else:
                # A股周线数据
                df = self.pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date')
            stock_logger.info(f"获取周K线成功: {ts_code}, 数据条数: {len(df)}")
            return df.to_dict('records')
        except Exception as e:
            stock_logger.error(f"获取周K线失败: {stock_code}, {start_date} - {end_date}", exc_info=True)
            print(f"获取周K线数据失败: {e}")
            return []
    
    def fetch_minute_data(self, stock_code, freq='1min'):
        """获取分钟K线数据
        
        Args:
            stock_code: 股票/ETF代码
            freq: 频率，默认1min（1分钟），可选：1min, 5min, 15min, 30min, 60min
        
        Returns:
            最近2天的分钟K线数据
            
        Note:
            - 指数不支持分钟数据
            - 需要Tushare高级权限
            - 每分钟最多调用2次
        """
        try:
            ts_code = self.normalize_stock_code(stock_code)
            code_type = self.detect_code_type(stock_code)
            
            stock_logger.debug(f"获取分钟K线: {ts_code}, 频率: {freq}")
            
            # 指数不支持分钟数据
            if code_type == 'index':
                stock_logger.warning(f"指数不支持分钟K线: {ts_code}")
                print(f"指数不支持分钟K线数据")
                return []
            
            # API限流 - 分钟K线需要特别注意，每分钟最多2次
            self._rate_limit_check(f'pro_bar_{freq}', min_interval=30)
            
            # 获取最近2天的数据（考虑周末，取4天）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=4)
            
            # Tushare分钟数据接口
            # ETF使用asset='FD'，股票使用asset='E'
            asset_type = 'FD' if code_type == 'fund' else 'E'
            
            df = ts.pro_bar(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adj='qfq',  # 前复权
                asset=asset_type
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
            error_msg = str(e)
            
            # 识别权限错误
            if 'ERROR.' in error_msg or '权限' in error_msg:
                stock_logger.warning(
                    f"分钟K线权限不足 - 股票: {ts_code}, 频率: {freq}\n"
                    f"错误信息: {error_msg}\n"
                    f"提示: 该接口需要Tushare高级权限，详情: https://tushare.pro/document/1?doc_id=108"
                )
                print(f"  ⚠️ {ts_code} 无{freq}分钟K线数据（可能需要权限）")
            else:
                # 其他错误记录完整堆栈
                stock_logger.error(
                    f"获取分钟K线数据失败 - 股票: {ts_code}, 频率: {freq}",
                    exc_info=True
                )
                print(f"  ❌ {ts_code} 获取分钟K线失败: {error_msg}")
            
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
    
    def fetch_realtime_price(self, stock_code):
        """获取股票完整实时行情数据（使用旧版免费接口）
        
        Returns:
            dict: 完整的实时行情数据
        """
        try:
            ts_code = self.normalize_stock_code(stock_code)
            code_type = self.detect_code_type(stock_code)
            
            stock_logger.debug(f"获取实时行情: {ts_code}, 类型: {code_type}")
            
            # 准备结果字典
            result = {
                'ts_code': ts_code,
                'stock_name': None,
                'price': None,
                'open': None,
                'pre_close': None,
                'high': None,
                'low': None,
                'volume': None,
                'amount': None,
                'change': None,
                'change_percent': None,
                'turnover_ratio': None,
                'amplitude': None,
                'total_mv': None,
                'circ_mv': None,
                'pe': None,
                'pe_ttm': None,
                'pb': None,
                'dv_ratio': None,
                'trade_date': None,
                'trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 1. 获取实时行情数据（旧版免费接口）
            try:
                stock_code_simple = ts_code.split('.')[0]
                df_real = ts.get_realtime_quotes(stock_code_simple)
                
                if not df_real.empty:
                    real = df_real.iloc[0]
                    result['stock_name'] = real.get('name', '')
                    result['price'] = float(real.get('price', 0)) if real.get('price') else None
                    result['open'] = float(real.get('open', 0)) if real.get('open') else None
                    result['pre_close'] = float(real.get('pre_close', 0)) if real.get('pre_close') else None
                    result['high'] = float(real.get('high', 0)) if real.get('high') else None
                    result['low'] = float(real.get('low', 0)) if real.get('low') else None
                    result['volume'] = float(real.get('volume', 0)) if real.get('volume') else None
                    result['amount'] = float(real.get('amount', 0)) if real.get('amount') else None
                    result['change'] = float(real.get('change', 0)) if real.get('change') else None
                    result['turnover_ratio'] = float(real.get('turnoverratio', 0)) if real.get('turnoverratio') else None
                    
                    # 涨跌幅（注意字段名可能是changepercent）
                    change_pct = real.get('changepercent') or real.get('p_change')
                    if change_pct:
                        result['change_percent'] = float(change_pct)
                    
                    # 计算振幅
                    if result['high'] and result['low'] and result['pre_close'] and result['pre_close'] > 0:
                        result['amplitude'] = (result['high'] - result['low']) / result['pre_close'] * 100
                    
                    # 交易日期（实时接口可能没有，用今天日期）
                    result['trade_date'] = datetime.now().strftime('%Y%m%d')
                    
                    stock_logger.info(f"实时行情获取成功: {ts_code}, 价格: {result['price']}")
            except Exception as e:
                stock_logger.warning(f"旧版实时行情接口失败: {ts_code}, {e}")
            
            # 2. 获取基本面数据（市值、PE、PB等）
            try:
                df_basic = self.pro.daily_basic(ts_code=ts_code, limit=1)
                if not df_basic.empty:
                    basic = df_basic.iloc[0]
                    result['total_mv'] = float(basic.get('total_mv', 0)) if basic.get('total_mv') else None
                    result['circ_mv'] = float(basic.get('circ_mv', 0)) if basic.get('circ_mv') else None
                    result['pe'] = float(basic.get('pe', 0)) if basic.get('pe') else None
                    result['pe_ttm'] = float(basic.get('pe_ttm', 0)) if basic.get('pe_ttm') else None
                    result['pb'] = float(basic.get('pb', 0)) if basic.get('pb') else None
                    result['dv_ratio'] = float(basic.get('dv_ratio', 0)) if basic.get('dv_ratio') else None
                    
                    # 如果实时接口没获取到交易日期，用基本面的
                    if not result['trade_date'] and basic.get('trade_date'):
                        result['trade_date'] = basic['trade_date']
                    
                    stock_logger.info(f"基本面数据获取成功: {ts_code}")
            except Exception as e:
                stock_logger.warning(f"基本面数据获取失败: {ts_code}, {e}")
            
            # 3. 如果实时接口失败，降级使用日K线数据
            if not result['price']:
                try:
                    if code_type == 'index':
                        df = self.pro.index_daily(ts_code=ts_code)
                    elif code_type == 'fund':
                        df = self.pro.fund_daily(ts_code=ts_code)
                    else:
                        df = self.pro.daily(ts_code=ts_code)
                    
                    if df is not None and not df.empty:
                        df = df.sort_values('trade_date', ascending=False)
                        latest = df.iloc[0]
                        
                        result['price'] = float(latest['close'])
                        result['open'] = float(latest.get('open', 0)) if latest.get('open') else None
                        result['pre_close'] = float(latest.get('pre_close', 0)) if latest.get('pre_close') else None
                        result['high'] = float(latest.get('high', 0)) if latest.get('high') else None
                        result['low'] = float(latest.get('low', 0)) if latest.get('low') else None
                        result['volume'] = float(latest.get('vol', 0)) if latest.get('vol') else None
                        result['amount'] = float(latest.get('amount', 0)) if latest.get('amount') else None
                        result['change'] = float(latest.get('change', 0)) if latest.get('change') else None
                        result['change_percent'] = float(latest.get('pct_chg', 0)) if latest.get('pct_chg') else None
                        result['trade_date'] = latest['trade_date']
                        
                        stock_logger.info(f"降级使用日K线数据: {ts_code}, 价格: {result['price']}")
                except Exception as e:
                    stock_logger.error(f"日K线数据获取失败: {ts_code}, {e}")
            
            # 检查是否至少获取到了价格
            if result['price']:
                return result
            else:
                stock_logger.warning(f"未能获取到有效价格数据: {ts_code}")
                return None
                
        except Exception as e:
            stock_logger.error(f"获取实时行情失败: {stock_code}", exc_info=True)
            return None
    
    def save_realtime_price(self, price_data):
        """保存完整实时行情到数据库"""
        if not price_data:
            return False
        
        from config import config
        try:
            if config.DATABASE_TYPE == 'sqlite':
                query = """
                INSERT OR REPLACE INTO stock_realtime (
                    ts_code, stock_name, price, open, pre_close, high, low, 
                    volume, amount, change, change_percent, turnover_ratio, amplitude,
                    total_mv, circ_mv, pe, pe_ttm, pb, dv_ratio, trade_date, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    price_data['ts_code'],
                    price_data.get('stock_name'),
                    price_data.get('price'),
                    price_data.get('open'),
                    price_data.get('pre_close'),
                    price_data.get('high'),
                    price_data.get('low'),
                    price_data.get('volume'),
                    price_data.get('amount'),
                    price_data.get('change'),
                    price_data.get('change_percent'),
                    price_data.get('turnover_ratio'),
                    price_data.get('amplitude'),
                    price_data.get('total_mv'),
                    price_data.get('circ_mv'),
                    price_data.get('pe'),
                    price_data.get('pe_ttm'),
                    price_data.get('pb'),
                    price_data.get('dv_ratio'),
                    price_data.get('trade_date'),
                    price_data.get('trade_time')
                )
            else:
                query = """
                INSERT INTO stock_realtime (
                    ts_code, stock_name, price, open, pre_close, high, low, 
                    volume, amount, change, change_percent, turnover_ratio, amplitude,
                    total_mv, circ_mv, pe, pe_ttm, pb, dv_ratio, trade_date, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                stock_name=VALUES(stock_name), price=VALUES(price), open=VALUES(open), 
                pre_close=VALUES(pre_close), high=VALUES(high), low=VALUES(low), 
                volume=VALUES(volume), amount=VALUES(amount), change=VALUES(change), 
                change_percent=VALUES(change_percent), turnover_ratio=VALUES(turnover_ratio), 
                amplitude=VALUES(amplitude), total_mv=VALUES(total_mv), circ_mv=VALUES(circ_mv), 
                pe=VALUES(pe), pe_ttm=VALUES(pe_ttm), pb=VALUES(pb), dv_ratio=VALUES(dv_ratio), 
                trade_date=VALUES(trade_date), updated_at=VALUES(updated_at)
                """
                params = (
                    price_data['ts_code'],
                    price_data.get('stock_name'),
                    price_data.get('price'),
                    price_data.get('open'),
                    price_data.get('pre_close'),
                    price_data.get('high'),
                    price_data.get('low'),
                    price_data.get('volume'),
                    price_data.get('amount'),
                    price_data.get('change'),
                    price_data.get('change_percent'),
                    price_data.get('turnover_ratio'),
                    price_data.get('amplitude'),
                    price_data.get('total_mv'),
                    price_data.get('circ_mv'),
                    price_data.get('pe'),
                    price_data.get('pe_ttm'),
                    price_data.get('pb'),
                    price_data.get('dv_ratio'),
                    price_data.get('trade_date'),
                    price_data.get('trade_time')
                )
            
            db_manager.execute_update(query, params)
            stock_logger.info(f"保存实时行情成功: {price_data['ts_code']}")
            return True
        except Exception as e:
            stock_logger.error(f"保存实时行情失败: {price_data['ts_code']}", exc_info=True)
            return False
    
    def get_realtime_price(self, stock_code):
        """从数据库获取完整实时行情"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            query = """
            SELECT ts_code, stock_name, price, open, pre_close, high, low, 
                   volume, amount, change, change_percent, turnover_ratio, amplitude,
                   total_mv, circ_mv, pe, pe_ttm, pb, dv_ratio, trade_date, updated_at
            FROM stock_realtime
            WHERE ts_code = %s
            """
            result = db_manager.execute_query(query, (ts_code,))
            if result:
                return result[0]
            return None
        except Exception as e:
            stock_logger.error(f"获取实时行情失败: {stock_code}", exc_info=True)
            return None
            stock_logger.error(f"获取实时价格失败: {stock_code}", exc_info=True)
            return None
    
    def update_kline_data_only(self, stock_code):
        """仅更新日K线和周K线数据（不包含分钟K）"""
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
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
            stock_logger.error(f"更新K线数据失败: {stock_code}", exc_info=True)
            return False
    
    def update_stock_data(self, stock_code):
        """更新股票数据（日K线、周K线、指标、实时价格）
        
        注意：不再获取1分钟K线数据，改为实时价格
        """
        try:
            ts_code = self.normalize_stock_code(stock_code)
            
            # 获取实时价格
            price_data = self.fetch_realtime_price(stock_code)
            if price_data:
                self.save_realtime_price(price_data)
            
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
            stock_logger.error(f"更新股票数据失败: {stock_code}", exc_info=True)
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
