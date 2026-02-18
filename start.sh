#!/bin/bash
# 快速启动脚本

echo "🚀 AI量化股票分析工具 - 启动中..."
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    echo "请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查环境
echo "📋 检查环境配置..."
python check_env.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 环境检查失败，请根据上述提示修复问题"
    exit 1
fi

echo ""
echo "✅ 环境检查通过"
echo ""
echo "🌐 启动Web服务..."
echo "访问地址: http://localhost:5000"
echo ""

# 启动应用
python app.py
