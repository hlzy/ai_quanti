# SQL兼容性修复说明 - 快速参考

## 🎯 问题

添加股票到自选股时出现错误：`near "DUPLICATE": syntax error`

## ✅ 解决方案

已修复MySQL和SQLite的SQL语法兼容性问题。

## 📝 修改的文件

1. **services/watchlist_service.py**
   - 修复自选股插入语法

2. **services/stock_service.py**
   - 修复日K线数据插入
   - 修复周K线数据插入
   - 修复技术指标插入
   - 修复pandas Timestamp类型转换

## 🧪 测试结果

```bash
✅ 自选股插入成功
✅ 日K线数据插入成功: 1 条
✅ 周K线数据插入成功
✅ 技术指标插入成功: 1 条
```

## 🚀 现在可以正常使用

1. **添加自选股**: 输入 `300058` → 点击"添加" → ✅ 成功
2. **查看列表**: 自选股列表显示"蓝色光标"
3. **获取数据**: K线数据自动缓存到本地数据库

## 📊 支持的功能

- ✅ A股（上海/深圳）
- ✅ 港股
- ✅ 日K线数据
- ✅ 周K线数据
- ✅ 技术指标（MACD、RSI、EMA）
- ✅ 本地数据缓存

## 💡 技术细节

### MySQL vs SQLite 语法差异

| 功能 | MySQL | SQLite |
|------|-------|--------|
| 插入或更新 | `ON DUPLICATE KEY UPDATE` | `INSERT OR REPLACE` |
| 占位符 | `%(name)s` | `?` |
| 日期类型 | datetime | 字符串 |

### 修复内容

1. **自动检测数据库类型**
   ```python
   if config.DATABASE_TYPE == 'sqlite':
       # 使用SQLite语法
   else:
       # 使用MySQL语法
   ```

2. **Timestamp转换**
   ```python
   if hasattr(trade_date, 'strftime'):
       trade_date = trade_date.strftime('%Y-%m-%d')
   ```

## 🔍 详细文档

完整调试过程请参考：[调试报告3-SQL语法兼容性修复.md](./调试报告3-SQL语法兼容性修复.md)

---

**修复日期**: 2026-02-18  
**状态**: ✅ 已完成  
**影响**: 所有数据插入功能恢复正常
