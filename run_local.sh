#!/bin/bash

echo "🏭 K博士 AI 内容工厂 - 本地启动"
echo "================================"
echo ""

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v streamlit &> /dev/null; then
    echo "📦 安装 Streamlit..."
    pip3 install streamlit
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件配置你的 API Keys"
    echo ""
    read -p "按回车键继续..."
fi

# 启动应用
echo "🚀 启动应用..."
echo ""
streamlit run app.py
