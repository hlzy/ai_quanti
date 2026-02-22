import tushare as ts

# 1. 设置你的 Token (请替换为你的实际 Token)
ts.set_token('844bdca7ee4db4f13984c99de7a6593bf7f8fab27f89941ead4ab9fb')
pro = ts.pro_api()

# 定义股票代码 (赛力斯 601127.SH)
ts_code = '601127.SH'

# --- 第一部分：获取实时行情 ---
try:
    # 使用免费的旧接口 (注意：股票代码要去掉后缀)
    stock_code_simple = ts_code.split('.')[0]
    df_real = ts.get_realtime_quotes(stock_code_simple)
    
    if not df_real.empty:
        print("=== 实时行情数据 ===")
        # 打印所有列名看看实际有什么字段
        # print("可用列名:", df_real.columns.tolist())
        
        # 根据实际的列名获取数据
        print(f"股票名称: {df_real['name'].iloc[0]}")
        print(f"当前价: {df_real['price'].iloc[0]}")
        print(f"涨跌幅: {df_real['changepercent'].iloc[0]}")  # 应该是changepercent，不是p_change
        print(f"涨跌额: {df_real['change'].iloc[0]}")
        print(f"最高价: {df_real['high'].iloc[0]}")
        print(f"最低价: {df_real['low'].iloc[0]}")
        print(f"成交量: {df_real['volume'].iloc[0]}")
        print(f"成交额: {df_real['amount'].iloc[0]}")
        print(f"换手率: {df_real['turnoverratio'].iloc[0]}")  # 注意字段名可能是turnoverratio
        print(f"开盘价: {df_real['open'].iloc[0]}")
        print(f"昨收价: {df_real['pre_close'].iloc[0]}")
        
        # 计算振幅 (需要验证高低价是否不为0)
        if float(df_real['high'].iloc[0]) > 0:
            amplitude = (float(df_real['high'].iloc[0]) - float(df_real['low'].iloc[0])) / float(df_real['pre_close'].iloc[0]) * 100
            print(f"振幅: {amplitude:.2f}%")
        
        # 涨停价和跌停价通常需要计算（前收盘的±10%）
        pre_close = float(df_real['pre_close'].iloc[0])
        limit_up = round(pre_close * 1.1, 2)
        limit_down = round(pre_close * 0.9, 2)
        print(f"涨停价: {limit_up}")
        print(f"跌停价: {limit_down}")
        
except Exception as e:
    print(f"获取实时行情失败: {e}")

# --- 第二部分：获取基本面数据 ---
try:
    # 尝试获取日线基本面数据
    df_basic = pro.daily_basic(ts_code=ts_code, limit=1)
    
    if not df_basic.empty:
        basic = df_basic.iloc[0]
        print("\n=== 基本面数据 ===")
        print(f"总市值: {basic.get('total_mv', 0) / 10000:.2f} 亿")
        print(f"流通市值: {basic.get('circ_mv', 0) / 10000:.2f} 亿")
        
        # 市盈率、市净率等
        print(f"市盈率(动): {basic.get('pe', 'N/A')}")
        print(f"市盈率(TTM): {basic.get('pe_ttm', 'N/A')}")
        print(f"市净率: {basic.get('pb', 'N/A')}")
        print(f"股息率: {basic.get('dv_ratio', 'N/A')}%")
        
        # 换手率（与实时数据的换手率可能不同，这个是日换手率）
        print(f"日换手率: {basic.get('turnover_rate', 'N/A')}%")
        
except Exception as e:
    print(f"获取基本面数据失败: {e}")
    print("注意：需要Tushare Pro权限才能调用此接口")

# --- 第三部分：尝试获取日线数据 ---
try:
    df_daily = pro.daily(ts_code=ts_code, limit=1)
    if not df_daily.empty:
        daily = df_daily.iloc[0]
        print("\n=== 日线数据 ===")
        print(f"交易日期: {daily['trade_date']}")
        print(f"开盘价: {daily['open']}")
        print(f"最高价: {daily['high']}")
        print(f"最低价: {daily['low']}")
        print(f"收盘价: {daily['close']}")
        print(f"昨收价: {daily['pre_close']}")
        print(f"涨跌额: {daily['change']}")
        print(f"涨跌幅: {daily['pct_chg']}%")
        print(f"成交量: {daily['vol']}")
        print(f"成交额: {daily['amount']}")
        
except Exception as e:
    print(f"获取日线数据失败: {e}")
    print("注意：需要Tushare Pro权限才能调用此接口")
