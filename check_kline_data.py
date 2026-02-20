#!/usr/bin/env python3
"""
检查K线数据
"""
from database import db_manager

print("检查数据库中的K线数据...")
print("=" * 60)

# 检查股票数据表
tables = ['stock_daily', 'stock_weekly', 'stock_minute']
for table in tables:
    query = f'SELECT COUNT(*) as count FROM {table}'
    result = db_manager.execute_query(query, fetch_one=True)
    print(f'{table}: {result["count"]} 条记录')

# 检查自选股
print("\n自选股列表:")
print("-" * 60)
query = 'SELECT * FROM watchlist'
watchlist = db_manager.execute_query(query)
print(f'共 {len(watchlist)} 只自选股')
for stock in watchlist:
    print(f'  - {stock["stock_code"]}: {stock.get("stock_name", "未知")}')
    
    # 检查每只自选股的数据
    for table in ['stock_daily', 'stock_minute']:
        query = f'SELECT COUNT(*) as count FROM {table} WHERE ts_code = ?'
        result = db_manager.execute_query(query, (stock['stock_code'],), fetch_one=True)
        print(f'    {table}: {result["count"]} 条')

print("\n" + "=" * 60)
