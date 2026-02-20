#!/bin/bash
# 日志系统快速验证脚本

echo "================================================"
echo "日志系统验证"
echo "================================================"
echo ""

# 检查日志目录
if [ -d "log" ]; then
    echo "✓ 日志目录存在: log/"
    echo "  文件数: $(ls -1 log/*.log 2>/dev/null | wc -l)"
else
    echo "✗ 日志目录不存在"
    exit 1
fi

echo ""
echo "日志文件列表:"
ls -lh log/*.log 2>/dev/null

echo ""
echo "================================================"
echo "最近的日志记录（stock_service）:"
echo "================================================"
if [ -f "log/stock_service_$(date +%Y-%m-%d).log" ]; then
    tail -10 "log/stock_service_$(date +%Y-%m-%d).log"
else
    echo "今天还没有stock_service日志"
fi

echo ""
echo "================================================"
echo "搜索警告和错误:"
echo "================================================"
grep -h "WARNING\|ERROR" log/*.log 2>/dev/null | tail -5 || echo "暂无警告或错误"

echo ""
echo "================================================"
echo "验证完成！"
echo "================================================"
