# K博士 AI 内容工厂 - 使用指南

## 🎯 快速开始

### 1. 安装依赖

```bash
cd ~/ai-content-factory
pip3 install -r requirements.txt
```

### 2. 配置环境

#### 2.1 系统环境变量（已配置）
- `ANTHROPIC_AUTH_TOKEN` - Claude API Key ✅
- `GEMINI_API_KEY` - Gemini API Key ✅

#### 2.2 配置 Notion

1. 创建 Notion Integration
   - 访问 https://www.notion.so/my-integrations
   - 点击 "New integration"
   - 命名为 "AI内容工厂"
   - 复制 Token

2. 创建 Notion 数据库
   - 在 Notion 中创建新页面
   - 添加 Database，包含字段：
     - 标题 (Title)
     - 格式 (Select): 视频号/公众号/朋友圈/小红书/书稿
     - 状态 (Select): 草稿/已审核/已发布
   - 点击 Share，邀请你的 Integration
   - 复制数据库 URL 中的 ID（32位字符）

3. 编辑 `.env` 文件
   ```bash
   cp .env.example .env
   nano .env
   ```

   填入：
   ```
   NOTION_TOKEN=secret_xxx
   NOTION_DATABASE_ID=xxx
   ```

### 3. 运行初始化检查

```bash
python3 scripts/setup.py
```

### 4. 启动系统

#### 方式1：使用启动脚本（推荐）
```bash
./start.sh
```

#### 方式2：手动启动
```bash
# 启动 Web 管理后台
streamlit run app.py

# 或启动定时调度器
python3 scheduler.py

# 或手动采集选题
python3 -m modules.collector.main
```

## 📖 使用流程

### 每日工作流（30分钟）

1. **07:00** - 系统自动采集选题（或手动触发）
2. **07:05** - 打开 http://localhost:8501
3. **07:08** - 在「选题采集」页面勾选 2-3 个选题
4. **07:10** - 在「内容生成」页面写一句话观点，点击生成
5. **07:15** - 审核 5 种格式的内容，微调
6. **07:25** - 点击「发布到 Notion」，完成

### 定时任务

- **每天 07:00** - 自动采集选题
- **每周日 08:00** - 整合书稿（待实现）

## 🗂️ 项目结构

```
ai-content-factory/
├── app.py                          # Streamlit 管理后台
├── scheduler.py                    # 定时任务调度器
├── start.sh                        # 快速启动脚本
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量配置
├── README.md                       # 本文档
│
├── modules/
│   ├── collector/                  # 选题采集模块
│   │   ├── main.py                # 采集器主入口
│   │   ├── sources.py             # 数据源（知乎/Google/RSS）
│   │   └── scorer.py              # Claude 打分器
│   │
│   ├── generator/                  # 内容生成模块
│   │   ├── main.py                # 生成器主入口
│   │   ├── claude_client.py       # Claude API 客户端
│   │   ├── gemini_client.py       # Gemini API 客户端
│   │   ├── openclaw_bridge.py     # OpenClaw 知识库桥接
│   │   └── templates.py           # 5种格式的 Prompt 模板
│   │
│   ├── publisher/                  # 发布模块
│   │   ├── main.py                # 发布器主入口
│   │   ├── notion_client.py       # Notion API 客户端
│   │   ├── formatter.py           # Markdown → 微信 HTML
│   │   └── exporter.py            # 导出工具
│   │
│   ├── config.py                   # 配置管理
│   └── utils.py                    # 工具函数
│
├── data/
│   ├── topics/                     # 选题数据
│   ├── drafts/                     # 草稿数据
│   └── published/                  # 已发布内容
│
├── logs/                           # 日志文件
├── config/                         # 配置文件
│   └── book_structure.json         # 书稿章节结构
│
└── scripts/
    └── setup.py                    # 初始化脚本
```

## 🔧 故障排除

### OpenClaw 连接失败
```bash
# 检查 OpenClaw 状态
openclaw gateway health

# 重启 OpenClaw
openclaw gateway restart
```

### Notion API 报错
- 检查 Integration 是否有权限访问数据库
- 检查 Database ID 是否正确（32位字符）
- 确认数据库字段名称正确

### Claude API 限流
- 系统会自动降级到 Gemini（如果配置）
- 或等待 1 分钟后重试

### 依赖安装失败
```bash
# 升级 pip
python3 -m pip install --upgrade pip

# 重新安装依赖
pip3 install -r requirements.txt --force-reinstall
```

## 📊 开发进度

- [x] Phase 0: 项目初始化
- [x] Phase 1: 选题采集器
- [x] Phase 2: 内容生成引擎
- [x] Phase 3: Notion 发布器
- [x] Phase 4: Streamlit 管理后台
- [ ] Phase 5: 书稿整合功能
- [ ] Phase 6: 历史数据导入

## 🚀 下一步计划

1. 实现书稿整合功能
2. 添加历史文档导入
3. 优化 Prompt 模板
4. 添加更多数据源
5. 实现自动发布到公众号

## 📝 许可证

MIT License

## 🙏 致谢

- Claude API by Anthropic
- Gemini API by Google
- OpenClaw by OpenClaw Team
- Notion API by Notion
- Streamlit by Streamlit Inc.
