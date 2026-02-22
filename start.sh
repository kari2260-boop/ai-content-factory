#!/bin/bash

# K博士 AI 内容工厂 - 快速启动脚本

echo "🏭 K博士 AI 内容工厂"
echo "===================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
python3 scripts/setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 初始化检查失败，请根据提示修复"
    exit 1
fi

echo ""
echo "===================="
echo "请选择启动模式:"
echo "  1. Streamlit 管理后台 (推荐)"
echo "  2. 定时调度器"
echo "  3. 手动采集选题"
echo "  4. 退出"
echo "===================="
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动 Streamlit 管理后台..."
        streamlit run app.py
        ;;
    2)
        echo ""
        echo "⏰ 启动定时调度器..."
        python3 scheduler.py
        ;;
    3)
        echo ""
        echo "📊 开始采集选题..."
        python3 -m modules.collector.main
        ;;
    4)
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
