# 📝 Notion 配置完整指南

## 步骤 1: 创建 Notion Integration

### 1.1 访问 Notion Integrations 页面
```
https://www.notion.so/my-integrations
```

### 1.2 创建新的 Integration
1. 点击 **"+ New integration"** 按钮
2. 填写信息：
   - **Name**: AI内容工厂
   - **Logo**: 可选
   - **Associated workspace**: 选择你的工作区
3. 点击 **"Submit"**

### 1.3 复制 Token
- 创建成功后，会显示 **"Internal Integration Token"**
- 格式类似：`secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **复制这个 Token**（后面要用）

---

## 步骤 2: 创建 Notion 数据库

### 2.1 在 Notion 中创建新页面
1. 打开 Notion
2. 点击左侧 **"+ New page"**
3. 命名为：**"K博士内容库"**

### 2.2 创建 Database
1. 在页面中输入 `/database`
2. 选择 **"Table - Inline"**
3. 创建以下字段（列）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 标题 | Title | 自动创建，保持默认 |
| 格式 | Select | 添加选项：视频号、公众号、朋友圈、小红书、书稿 |
| 状态 | Select | 添加选项：草稿、已审核、已发布 |
| 选题 | Text | 普通文本 |
| 创建时间 | Created time | 自动创建时间 |
| 阅读量 | Number | 数字类型 |
| 互动数 | Number | 数字类型 |
| 主观评分 | Select | 添加选项：⭐⭐⭐⭐⭐、⭐⭐⭐⭐、⭐⭐⭐、⭐⭐、⭐、未评分 |

### 2.3 分享数据库给 Integration
1. 点击数据库右上角的 **"..."** 按钮
2. 选择 **"Add connections"**
3. 搜索并选择 **"AI内容工厂"**（你刚创建的 Integration）
4. 点击 **"Confirm"**

### 2.4 获取 Database ID
1. 点击数据库右上角的 **"..."** 按钮
2. 选择 **"Copy link"**
3. 链接格式类似：
   ```
   https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyyyy
   ```
4. **Database ID** 就是 `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 这部分（32位字符）

---

## 步骤 3: 配置 AI 内容工厂

### 3.1 编辑 .env 文件
```bash
cd ~/ai-content-factory
nano .env
```

### 3.2 填入配置
```bash
# Notion 配置（必填）
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AI API Keys（已在系统环境变量中配置，无需填写）
# ANTHROPIC_AUTH_TOKEN=（系统环境变量）
# GEMINI_API_KEY=（系统环境变量）

# OpenClaw 配置（可选，默认使用本地 CLI）
OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789

# 日志级别
LOG_LEVEL=INFO
```

### 3.3 保存并退出
- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

---

## 步骤 4: 重启 Streamlit

```bash
# 停止当前的 Streamlit
pkill -f "streamlit run app.py"

# 重新启动
cd ~/ai-content-factory
/Users/k/Library/Python/3.9/bin/streamlit run app.py --server.headless=true --server.port=8501 &
```

---

## 步骤 5: 测试发布

### 5.1 访问 Streamlit
```
http://localhost:8501
```

### 5.2 生成内容
1. 进入「📊 选题采集」
2. 选择一个选题
3. 进入「✍️ 内容生成」
4. 写一句话观点
5. 点击「生成内容」

### 5.3 发布到 Notion
1. 进入「📤 发布管理」
2. 点击「📤 发布到 Notion」
3. 等待几秒钟

### 5.4 检查 Notion
- 打开你的 Notion 数据库
- 应该能看到 5 条新记录（5种格式）
- 每条记录包含完整内容和元数据

---

## 常见问题

### Q1: 提示 "API token is invalid"
**原因**: Token 配置错误

**解决**:
1. 检查 Token 是否完整复制（包括 `secret_` 前缀）
2. 检查 Token 中是否有多余的空格或换行
3. 重新生成 Token 并配置

### Q2: 提示 "Could not find database"
**原因**: Database ID 错误或未分享给 Integration

**解决**:
1. 检查 Database ID 是否正确（32位字符）
2. 确认已将数据库分享给 Integration
3. 尝试重新复制 Database ID

### Q3: 内容被截断
**原因**: 单个 block 超过 2000 字符

**解决**:
- 系统已自动处理分块写入
- 如果仍然截断，检查 `modules/publisher/notion_client.py`

### Q4: 发布很慢
**原因**: Notion API 有速率限制

**解决**:
- 正常现象，每个格式需要 3-5 秒
- 5 种格式总共需要 15-25 秒
- 系统已自动添加延迟避免限流

---

## 验证配置

运行以下命令验证配置：

```bash
cd ~/ai-content-factory
python3 -c "
from modules.publisher.notion_client import NotionClient
try:
    client = NotionClient()
    print('✅ Notion 配置成功')
except Exception as e:
    print(f'❌ Notion 配置失败: {str(e)}')
"
```

---

## 完成！

配置完成后，每次生成内容都会自动：
1. ✅ 创建 5 个 Notion 页面（5种格式）
2. ✅ 分块写入完整内容（避免截断）
3. ✅ 添加元数据（选题、观点、字数、时间）
4. ✅ 书稿素材自动归类到章节
5. ✅ 导出文件到本地备份

**现在你的内容会自动同步到 Notion 了！** 🎉
