# AI Content Factory 网页部署指南

## 方案一：Streamlit Cloud 部署（推荐）

### 1. 准备工作

确保你的代码已经推送到 GitHub：
```bash
cd /Users/k/ai-content-factory
git add .
git commit -m "准备部署到 Streamlit Cloud"
git push origin main
```

### 2. 部署到 Streamlit Cloud

1. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库：`kari2260-boop/ai-content-factory`
5. 主文件路径：`app.py`
6. 点击 "Deploy"

### 3. 配置环境变量

在 Streamlit Cloud 的应用设置中：

1. 点击右上角的 "⋮" > "Settings"
2. 选择 "Secrets" 标签
3. 添加以下配置（参考 `.streamlit/secrets.toml.example`）：

```toml
NOTION_TOKEN = "你的_notion_token"
NOTION_DATABASE_ID = "你的_notion_database_id"
ANTHROPIC_AUTH_TOKEN = "你的_anthropic_api_key"
GEMINI_API_KEY = "你的_gemini_api_key"
LOG_LEVEL = "INFO"
```

4. 点击 "Save"

### 4. 访问应用

部署完成后，你会获得一个类似这样的 URL：
```
https://your-app-name.streamlit.app
```

---

## 方案二：Heroku 部署

### 1. 安装 Heroku CLI

```bash
brew tap heroku/brew && brew install heroku
```

### 2. 登录 Heroku

```bash
heroku login
```

### 3. 创建应用

```bash
cd /Users/k/ai-content-factory
heroku create your-app-name
```

### 4. 配置环境变量

```bash
heroku config:set NOTION_TOKEN="你的_notion_token"
heroku config:set NOTION_DATABASE_ID="你的_notion_database_id"
heroku config:set ANTHROPIC_AUTH_TOKEN="你的_anthropic_api_key"
heroku config:set GEMINI_API_KEY="你的_gemini_api_key"
heroku config:set LOG_LEVEL="INFO"
```

### 5. 部署

```bash
git push heroku main
```

### 6. 打开应用

```bash
heroku open
```

---

## 方案三：本地运行（测试用）

### 1. 安装依赖

```bash
cd /Users/k/ai-content-factory
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：
```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 运行应用

```bash
streamlit run app.py
```

应用会在 `http://localhost:8501` 打开。

---

## 常见问题

### Q: 部署后无法访问 Notion？
A: 检查 Notion Token 和 Database ID 是否正确配置。

### Q: API 调用失败？
A: 确认 API Keys 已正确添加到环境变量中。

### Q: 应用启动慢？
A: Streamlit Cloud 免费版可能有冷启动延迟，升级到付费版可以改善。

### Q: 如何更新部署？
A: 推送代码到 GitHub，Streamlit Cloud 会自动重新部署。

---

## 推荐配置

- **部署平台**: Streamlit Cloud（免费且易用）
- **数据存储**: Notion Database
- **API 服务**: Claude + Gemini
- **监控**: Streamlit Cloud 内置监控

---

## 下一步

部署完成后，你可以：
1. 在网页界面采集选题
2. 生成内容草稿
3. 发布到 Notion
4. 查看统计数据

祝使用愉快！🎉
