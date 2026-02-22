# K博士 AI 内容工厂

> 每天 30 分钟，自动生产 5 种格式内容，半年"长"出一本书

## 快速开始

### 1. 安装依赖

```bash
cd ~/ai-content-factory
pip3 install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 Notion Token 和 Database ID
# NOTION_TOKEN=secret_xxx
# NOTION_DATABASE_ID=xxx
```

### 3. 获取 Notion 配置

#### 3.1 创建 Notion Integration
1. 访问 https://www.notion.so/my-integrations
2. 点击 "New integration"
3. 命名为 "AI内容工厂"
4. 复制 "Internal Integration Token" 到 `.env` 的 `NOTION_TOKEN`

#### 3.2 创建 Notion 数据库
1. 在 Notion 中创建一个新页面，命名为 "K博士内容库"
2. 创建一个 Database，包含以下字段：
   - 标题（Title）
   - 格式（Select）：视频号/公众号/朋友圈/小红书/书稿
   - 状态（Select）：草稿/已审核/已发布
   - 选题（Text）
   - 内容（Text）
   - 创建时间（Created time）
3. 点击右上角 "Share"，邀请你的 Integration
4. 复制数据库 URL 中的 ID（32位字符）到 `.env` 的 `NOTION_DATABASE_ID`

### 4. 运行系统

```bash
# 启动 Web 管理后台
streamlit run app.py

# 或手动运行采集器
python3 modules/collector/main.py

# 或手动运行生成器
python3 modules/generator/main.py
```

### 5. 设置定时任务

```bash
# 每天早上 7:00 自动采集选题
python3 scheduler.py
```

## 项目结构

```
ai-content-factory/
├── app.py                      # Streamlit 主界面
├── scheduler.py                # 定时任务调度器
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量配置
├── README.md                   # 本文档
│
├── modules/
│   ├── collector/              # 选题采集模块
│   │   ├── main.py            # 采集器主入口
│   │   ├── sources.py         # 数据源（知乎/Google Trends/RSS）
│   │   └── scorer.py          # Claude 打分器
│   │
│   ├── generator/              # 内容生成模块
│   │   ├── main.py            # 生成器主入口
│   │   ├── claude_client.py   # Claude API 客户端
│   │   ├── gemini_client.py   # Gemini API 客户端
│   │   ├── openclaw_bridge.py # OpenClaw 知识库桥接
│   │   └── templates.py       # 5种格式的 Prompt 模板
│   │
│   └── publisher/              # 发布模块
│       ├── notion_client.py   # Notion API 客户端
│       ├── formatter.py       # Markdown → 微信 HTML
│       └── exporter.py        # 导出工具
│
├── data/
│   ├── topics/                # 选题数据（JSON）
│   ├── drafts/                # 草稿数据
│   └── published/             # 已发布内容
│
├── logs/                      # 日志文件
└── config/                    # 配置文件
    └── book_structure.json    # 书稿章节结构
```

## 每日使用流程

1. **07:00** - 系统自动采集选题并打分
2. **07:05** - 打开 http://localhost:8501
3. **07:08** - 勾选 2-3 个选题，写一句话观点
4. **07:10** - 点击"生成内容"
5. **07:15** - 审核 5 种格式初稿
6. **07:25** - 确认发布，自动归档到 Notion

## 系统要求

- macOS / Linux
- Python 3.9+
- Node.js 24+ (OpenClaw)
- 已安装 OpenClaw CLI
- 已配置环境变量：ANTHROPIC_AUTH_TOKEN, GEMINI_API_KEY

## 故障排除

### OpenClaw 连接失败
```bash
# 检查 OpenClaw 是否运行
openclaw gateway health

# 重启 OpenClaw
openclaw gateway restart
```

### Notion API 报错
- 检查 Integration 是否有权限访问数据库
- 检查 Database ID 是否正确（32位字符）

### Claude API 限流
- 系统会自动降级到 Gemini
- 或等待 1 分钟后重试

## 开发进度

- [x] Phase 0: 项目初始化
- [ ] Phase 1: 选题采集器
- [ ] Phase 2: 内容生成引擎
- [ ] Phase 3: Notion 发布器
- [ ] Phase 4: Streamlit 管理后台

## 许可证

MIT License
