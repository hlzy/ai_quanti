import tushare as ts
import pandas as pd

# 设置Tushare token（需要先注册获取）
# ts.set_token('844bdca7ee4db4f13984c99de7a6593bf7f8fab27f89941ead4ab9fb')  # 替换为你的实际token

# 初始化pro接口
pro = ts.pro_api()

def get_daily_data(symbol, start_date=None, end_date=None):
    """
    获取单只股票的历史日线数据
    """
    try:
        df = pro.daily(ts_code=symbol, 
                      start_date=start_date, 
                      end_date=end_date)
        return df
    except Exception as e:
        print(f"获取日线数据失败: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    print("\n=== 最新日线数据 ===")
    # 获取平安银行最近1个交易日数据
    daily_data = get_daily_data('688385.SH', start_date='20260101')
    if daily_data is not None:
        latest_data = daily_data.iloc[0]  # 最新数据
        print(f"股票代码: {latest_data['ts_code']}")
        print(f"交易日期: {latest_data['trade_date']}")
        print(f"收盘价: {latest_data['close']}")
        print(f"涨跌幅: {latest_data['pct_chg']}%")
