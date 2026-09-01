#!/bin/bash
# AI 内容工厂 - 本地启动脚本

cd "$(dirname "$0")"

echo "🏭 启动 AI 内容工厂..."
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 未找到 .env 文件"
    echo "请复制 .env.example 并配置："
    echo "  cp .env.example .env"
    exit 1
fi

# 检查必要的配置
if ! grep -q "NOTION_TOKEN=ntn_" .env; then
    echo "⚠️  警告：Notion Token 未配置"
fi

# 设置 PATH（确保能找到 streamlit）
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# 启动应用
echo ""
echo "✅ 启动成功！"
echo "📱 浏览器将自动打开 http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

streamlit run app.py
