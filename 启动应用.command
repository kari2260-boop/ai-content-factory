#!/bin/bash

# AI 内容工厂 - 快速启动脚本
# 双击运行此脚本即可启动应用

# 获取脚本所在目录
cd "$(dirname "$0")"

# 设置 PATH
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# 打开终端并启动应用
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$PWD' && export PATH='$HOME/Library/Python/3.9/bin:\$PATH' && streamlit run app.py"
end tell
EOF

# 等待 3 秒后自动打开浏览器
sleep 3
open http://localhost:8501
