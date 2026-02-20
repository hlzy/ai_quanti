#!/bin/bash

# ECharts离线版本下载脚本

echo "======================================"
echo "ECharts离线版本安装脚本"
echo "======================================"

# 创建目录
STATIC_DIR="/Users/sunjie/CodeBuddy/ai_quanti/static/js"
mkdir -p "$STATIC_DIR"

echo ""
echo "📁 目标目录: $STATIC_DIR"
echo ""

# 下载ECharts
echo "⬇️  正在下载ECharts 5.4.3..."

# 尝试从多个源下载
SUCCESS=false

# 源1: npmmirror（国内）
echo "尝试源1: npmmirror..."
if curl -L -o "$STATIC_DIR/echarts.min.js" \
    "https://registry.npmmirror.com/echarts/5.4.3/files/dist/echarts.min.js" 2>/dev/null; then
    if [ -s "$STATIC_DIR/echarts.min.js" ]; then
        echo "✅ 从npmmirror下载成功！"
        SUCCESS=true
    fi
fi

# 源2: unpkg
if [ "$SUCCESS" = false ]; then
    echo "尝试源2: unpkg..."
    if curl -L -o "$STATIC_DIR/echarts.min.js" \
        "https://unpkg.com/echarts@5.4.3/dist/echarts.min.js" 2>/dev/null; then
        if [ -s "$STATIC_DIR/echarts.min.js" ]; then
            echo "✅ 从unpkg下载成功！"
            SUCCESS=true
        fi
    fi
fi

# 源3: jsdelivr
if [ "$SUCCESS" = false ]; then
    echo "尝试源3: jsdelivr..."
    if curl -L -o "$STATIC_DIR/echarts.min.js" \
        "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js" 2>/dev/null; then
        if [ -s "$STATIC_DIR/echarts.min.js" ]; then
            echo "✅ 从jsdelivr下载成功！"
            SUCCESS=true
        fi
    fi
fi

if [ "$SUCCESS" = false ]; then
    echo "❌ 所有下载源均失败"
    echo "请手动下载: https://github.com/apache/echarts/releases/download/5.4.3/dist.tgz"
    exit 1
fi

# 验证文件
FILE_SIZE=$(wc -c < "$STATIC_DIR/echarts.min.js")
echo ""
echo "📊 文件大小: $FILE_SIZE bytes"

if [ "$FILE_SIZE" -lt 100000 ]; then
    echo "⚠️  警告：文件太小，可能下载不完整"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 编辑 templates/base.html"
echo "2. 修改ECharts引入为："
echo "   <script src=\"{{ url_for('static', filename='js/echarts.min.js') }}\"></script>"
echo ""
echo "或者运行自动配置："
echo "   python scripts/use_local_echarts.py"
