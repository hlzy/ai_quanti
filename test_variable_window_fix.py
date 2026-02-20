#!/usr/bin/env python3
"""最终完整测试"""
import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService

ai = AIService()

# 测试用例 - 使用实际存在的数据
test_cases = [
    # (输入消息, 股票代码, 期望匹配的变量, 期望数据行数, 描述)
    ("日K_10天", "688313.SH", "日K_10天", 10, "无股票名，有窗口"),
    ("日K_30天", "688313.SH", "日K_30天", 30, "无股票名，有窗口"),
    ("日K_688385_10天", "688313.SH", "日K_688385_10天", 10, "有股票代码，有窗口"),
    ("周K_60天", "688313.SH", "周K_60天", 60, "周K数据"),
    ("日K_10天_MACD", "688313.SH", "日K_10天_MACD", 20, "有窗口和指标(K线+指标各10行)"),
    ("日K_688313_20天_EMA", "688313.SH", "日K_688313_20天_EMA", 40, "完整格式(K线+指标各20行)"),
]

print("=" * 80)
print("最终完整测试 - 窗口截取功能")
print("=" * 80)

passed = 0
failed = 0

for message, stock_code, expected_var, expected_lines, description in test_cases:
    print(f"\n【{description}】")
    print(f"  输入: {message}")
    
    replaced_message, variables = ai._replace_variables(stock_code, message)
    
    if not variables:
        print(f"  ❌ 失败: 没有识别到变量")
        failed += 1
        continue
    
    found_var = list(variables.keys())[0]
    
    # 检查变量名
    if found_var != expected_var:
        print(f"  ❌ 失败: 变量名不匹配")
        print(f"     期望: {expected_var}")
        print(f"     实际: {found_var}")
        failed += 1
        continue
    
    # 检查数据行数
    var_value = variables[found_var]
    date_lines = re.findall(r'^202[0-9]-\d{2}-\d{2}', var_value, re.MULTILINE)
    actual_lines = len(date_lines)
    
    if actual_lines == expected_lines:
        print(f"  ✅ 通过: 数据行数={actual_lines}")
        passed += 1
    else:
        print(f"  ❌ 失败: 数据行数不匹配")
        print(f"     期望: {expected_lines} 行")
        print(f"     实际: {actual_lines} 行")
        if date_lines:
            print(f"     首行: {date_lines[0]}")
            print(f"     末行: {date_lines[-1]}")
        failed += 1

print("\n" + "=" * 80)
print(f"测试结果: ✅ 通过 {passed}/{len(test_cases)} 个")
if failed == 0:
    print("🎉 所有测试通过！")
else:
    print(f"❌ {failed} 个测试失败")
