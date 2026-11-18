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
echo "  1. Streamlit 管理后台 - 本地 (localhost:8501)"
echo "  2. Streamlit 管理后台 - 生产 (带 /studio 前缀)"
echo "  3. 定时调度器"
echo "  4. 手动采集选题"
echo "  5. 退出"
echo "===================="
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动本地 Streamlit 后台..."
        /Users/k/Library/Python/3.9/bin/streamlit run app.py --server.headless true
        ;;
    2)
        echo ""
        echo "🚀 启动生产 Streamlit 后台（/studio 前缀）..."
        streamlit run app.py \
            --server.headless true \
            --server.baseUrlPath /studio \
            --server.port 8501
        ;;
    3)
        echo ""
        echo "⏰ 启动定时调度器..."
        python3 scheduler.py
        ;;
    4)
        echo ""
        echo "📊 开始采集选题..."
        python3 -m modules.collector.main
        ;;
    5)
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
