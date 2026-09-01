# 🎨 YouMind API 集成指南

## 什么是 YouMind？

YouMind 是一个 AI 图片生成和文字排版平台，提供：
- 🖼️ **AI 图片生成**：多种风格的高质量图片
- 📝 **文字排版**：智能排版，生成精美的文章布局
- 🎨 **海报制作**：快速创建营销海报

官网：https://youmind.com/

---

## 📦 已集成的功能

### 1. 图片生成
- 自动为内容生成封面图
- 支持多平台尺寸（微信、小红书、视频号）
- 多种风格（教育、现代、极简、多彩）

### 2. 文字排版
- 智能排版文章内容
- 生成 HTML/Markdown 格式
- 提供在线预览链接

### 3. 海报制作
- 快速创建营销海报
- 自定义标题和背景
- 多种海报风格

---

## 🚀 如何启用 YouMind

### 步骤 1：获取 API Key

1. 访问 https://youmind.com/
2. 注册/登录账号
3. 进入 API 设置页面
4. 复制你的 API Key

### 步骤 2：配置环境变量

编辑 `.env` 文件，添加：

```bash
# YouMind API 配置
YOUMIND_API_KEY=your_api_key_here
YOUMIND_BASE_URL=https://api.youmind.ai/v1
```

### 步骤 3：重启应用

```bash
./start_local.sh
```

---

## 💡 使用方法

### 方法 1：在内容生成中自动使用

YouMind 已集成到内容生成流程中，会自动：
1. 为每个内容生成封面图
2. 优先使用 YouMind（如果配置了）
3. 降级到 DALL-E 或 Replicate（如果 YouMind 不可用）

**无需额外操作**，生成内容时会自动调用！

### 方法 2：单独使用 YouMind 功能

在 Python 代码中：

```python
from modules.visual.youmind_client import YouMindClient

# 初始化客户端
client = YouMindClient()

# 1. 生成图片
image_path = client.generate_image(
    prompt="一个温馨的家庭教育场景",
    style="realistic",
    size="1024x1024"
)

# 2. 生成封面图（针对内容优化）
cover_path = client.generate_cover_image(
    title="AI时代，如何培养孩子的核心竞争力",
    style="educational",
    platform="xiaohongshu"
)

# 3. 文字排版
layout = client.format_text_layout(
    title="AI时代的教育",
    content="这是一篇关于AI教育的文章...",
    layout_type="article"
)

# 4. 创建海报
poster_path = client.create_poster(
    title="AI 教育讲座",
    subtitle="2024年3月15日",
    style="modern"
)
```

---

## 🎯 支持的功能参数

### 图片生成风格
- `realistic` - 写实风格
- `anime` - 动漫风格
- `cartoon` - 卡通风格
- `abstract` - 抽象风格
- `minimalist` - 极简风格
- `vibrant` - 鲜艳风格

### 图片尺寸
- `1024x1024` - 正方形（推荐）
- `1024x768` - 横向
- `768x1024` - 纵向

### 排版类型
- `article` - 文章排版
- `poster` - 海报排版
- `card` - 卡片排版
- `story` - 故事排版

---

## 📊 API 优先级

系统会按以下优先级选择图片生成服务：

1. **YouMind**（如果配置）- 推荐
2. **DALL-E 3**（OpenAI）- 备选
3. **Flux**（Replicate）- 备选

配置多个 API 可以提高可用性！

---

## 🔍 检查 YouMind 状态

在应用侧边栏查看服务状态：
- ✅ YouMind API - 已配置且可用
- ⚠️ YouMind API (未配置) - 需要配置 API Key
- ❌ YouMind API - 配置错误或服务不可用

---

## 💰 费用说明

YouMind 是付费服务，请查看官网了解定价：
https://youmind.com/pricing

建议：
- 开发测试阶段：使用免费额度
- 生产环境：购买合适的套餐

---

## 🐛 常见问题

### Q1: API Key 配置后不生效？
**A:** 重启应用：`./start_local.sh`

### Q2: 图片生成失败？
**A:** 检查：
1. API Key 是否正确
2. 账户余额是否充足
3. 网络连接是否正常
4. 查看日志：`logs/visual.log`

### Q3: 如何查看生成的图片？
**A:** 图片保存在 `data/images/youmind/` 目录

### Q4: 可以同时配置多个图片生成服务吗？
**A:** 可以！系统会自动选择可用的服务，提高稳定性

---

## 📝 测试 YouMind

运行测试脚本：

```bash
cd /Users/kari77/Desktop/ai-content-factory
python3 modules/visual/youmind_client.py
```

如果配置正确，会生成测试图片并显示路径。

---

## 📞 需要帮助？

- YouMind 官方文档：https://docs.youmind.com/
- YouMind 支持：support@youmind.com
- 项目问题：查看 `logs/visual.log`
