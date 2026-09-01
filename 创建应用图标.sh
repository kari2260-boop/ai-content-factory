#!/bin/bash

# 创建 macOS 应用包
APP_NAME="AI内容工厂"
APP_DIR="/Users/kari77/Desktop/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# 创建目录结构
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# 创建启动脚本
cat > "${MACOS_DIR}/launcher" << 'LAUNCHER_EOF'
#!/bin/bash

# 获取应用所在目录
PROJECT_DIR="/Users/kari77/Desktop/ai-content-factory"

# 设置 PATH
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# 打开终端并启动应用
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$PROJECT_DIR' && export PATH='$HOME/Library/Python/3.9/bin:\$PATH' && echo '🏭 AI 内容工厂启动中...' && echo '' && streamlit run app.py"
end tell
EOF

# 等待 5 秒后自动打开浏览器
sleep 5
open http://localhost:8501

LAUNCHER_EOF

# 添加执行权限
chmod +x "${MACOS_DIR}/launcher"

# 创建 Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.ai-content-factory</string>
    <key>CFBundleName</key>
    <string>AI内容工厂</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST_EOF

echo "✅ 应用创建成功！"
echo "📍 位置: ${APP_DIR}"
echo ""
echo "🎯 使用方法："
echo "1. 在桌面找到「AI内容工厂.app」"
echo "2. 双击打开"
echo "3. 浏览器会自动打开 http://localhost:8501"
echo ""
echo "💡 提示: 首次打开可能需要在「系统偏好设置 > 安全性与隐私」中允许运行"
