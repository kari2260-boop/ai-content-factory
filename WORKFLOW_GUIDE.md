# AI Content Factory - 每日自动化工作流使用指南

## 🎯 工作流概述

每天只需30分钟，自动生产5种格式内容：

```
08:00 自动采集选题 (自动)
  ↓
08:30 审核选题 (5分钟)
  ↓
08:35 生成内容 (自动，2-3分钟)
  ↓
08:40 审核发布 (20分钟)
  ↓
完成！
```

---

## 🚀 快速开始

### 1. 确保 OpenClaw 运行

```bash
# 检查 OpenClaw 状态
openclaw gateway health

# 如果未运行，启动它
openclaw gateway
```

### 2. 启动定时调度器

```bash
cd ~/ai-content-factory
python workflow.py --schedule
```

### 3. 或者手动执行各步骤

```bash
# Step 1: 采集选题
python workflow.py --step1

# Step 2: 生成内容
python workflow.py --step2

# Step 3: 发布内容
python workflow.py --step3
```

---

## 📋 详细工作流

### Step 1: 采集选题 (08:00 自动)

**自动执行:**
- 从多个数据源采集热门选题
- AI自动打分（相关度、时效性、互动潜力、独特性）
- 保存到 `data/topics/` 目录

**你需要做:**
- 无需操作，系统自动完成

---

### Step 2: 审核选题 (08:30 手动，5分钟)

**打开 Streamlit 界面:**
```bash
streamlit run app.py
```

**操作步骤:**
1. 查看今日选题列表
2. 勾选 2-3 个感兴趣的选题
3. 为每个选题写一句话核心观点
4. 点击"生成所有格式内容"

**示例观点:**
```
"我认为AI时代最重要的是培养孩子从弱变强的能力和做决策的能力"
```

---

### Step 3: 生成内容 (08:35 自动，2-3分钟)

**自动执行:**
- OpenClaw 读取你的风格、方法论、案例库
- 为每个选题生成5种格式:
  - 🎬 视频号文案 (900-1500字)
  - 📰 公众号文章 (2000字)
  - 💬 朋友圈文案 (150-200字)
  - 📱 小红书文案 (800-1000字)
  - 📚 书稿素材 (800-1200字)
- 保存草稿到 `data/drafts/` 目录

**你需要做:**
- 无需操作，系统自动完成

---

### Step 4: 审核发布 (08:40 手动，20分钟)

**在 Streamlit 界面:**
1. 查看生成的5种格式内容
2. 在线编辑修改（如需要）
3. 点击"发布到 Notion"
4. 点击"导出文件"

**自动完成:**
- 发布到 Notion 数据库
- 导出为本地文件
- 书稿素材自动归档到对应章节

---

## 🔧 配置说明

### 环境变量 (.env)

```bash
# Claude API (用于打分)
ANTHROPIC_API_KEY=your_key_here

# Gemini API (备用)
GEMINI_API_KEY=your_key_here

# Notion (发布)
NOTION_TOKEN=your_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### OpenClaw 配置

确保以下文件已更新:
- `~/.openclaw/workspace/USER.md` - 你的完整画像
- `~/.openclaw/workspace/MEMORY.md` - 人生杠杆方法论
- `~/.openclaw/workspace/CONTENT_GUIDE.md` - 内容创作指南

---

## 📊 数据目录结构

```
ai-content-factory/
├── data/
│   ├── topics/              # 采集的选题
│   │   └── topics_20260220.json
│   ├── drafts/              # 生成的草稿
│   │   └── draft_20260220_083500_AI时代.json
│   └── published/           # 已发布内容
│       ├── 20260220_083500_AI时代_video.txt
│       ├── 20260220_083500_AI时代_article.txt
│       ├── 20260220_083500_AI时代_moments.txt
│       ├── 20260220_083500_AI时代_xiaohongshu.txt
│       └── 20260220_083500_AI时代_book.txt
└── logs/                    # 日志文件
    ├── collector.log
    ├── generator.log
    └── workflow.log
```

---

## 🧪 测试工作流

### 测试完整流程

```bash
python workflow.py --test
```

这会:
1. 采集选题
2. 等待30秒（模拟审核）
3. 自动生成内容
4. 等待30秒（模拟审核）
5. 发布内容

### 测试 OpenClaw 生成

```bash
cd modules/generator
python openclaw_bridge.py
```

---

## 🐛 故障排除

### OpenClaw 不可用

```bash
# 检查状态
openclaw gateway health

# 重启
openclaw gateway restart

# 查看日志
openclaw logs
```

### 生成内容为空

1. 检查 OpenClaw workspace 文件是否存在
2. 检查 OpenClaw 是否能读取 workspace
3. 查看日志: `logs/generator.log`

### Notion 发布失败

1. 检查 NOTION_TOKEN 是否正确
2. 检查 NOTION_DATABASE_ID 是否正确
3. 确保 Integration 有权限访问数据库

---

## 📈 效率对比

### 传统方式
- 找选题: 30分钟
- 写视频号: 1小时
- 写公众号: 2小时
- 写朋友圈: 15分钟
- 写小红书: 30分钟
- 写书稿: 1小时
- **总计: 5小时15分钟**

### 自动化方式
- 审核选题: 5分钟
- 审核内容: 20分钟
- **总计: 25分钟**

**效率提升: 12倍！**

---

## 🎯 下一步优化

- [ ] 添加微信推送通知
- [ ] 自动发布到各平台
- [ ] 智能选题推荐
- [ ] 内容质量评分
- [ ] A/B测试不同风格

---

## 📞 需要帮助？

查看日志:
```bash
tail -f logs/workflow.log
tail -f logs/generator.log
```

联系支持: 查看项目 README.md

---

**最后更新:** 2026-02-20
