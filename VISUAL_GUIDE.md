# 🎨 视觉处理模块使用指南

## 快速开始

### 1. 安装依赖

```bash
cd ~/ai-content-factory
python3 -m pip install openai replicate lark-oapi markdown --user
```

### 2. 配置 API Key

编辑 `.env` 文件，添加以下配置：

```bash
# 图片生成 (二选一)
OPENAI_API_KEY=sk-xxx                    # DALL-E 3
# REPLICATE_API_TOKEN=r8_xxx             # Flux (更便宜)

# 飞书文档
FEISHU_DOC_TOKEN=FQKKdaTb6oxOBIxceIOciEK3nFe

# 飞书 API (可选，用于自动发布)
# FEISHU_APP_ID=cli_xxx
# FEISHU_APP_SECRET=xxx
```

### 3. 测试图片生成

```bash
cd ~/ai-content-factory
python3 modules/visual/image_generator.py
```

### 4. 测试排版

```bash
python3 modules/visual/layout_processor.py
```

### 5. 测试完整流程

```bash
python3 modules/visual/main.py
```

## 在 Streamlit 中使用

### 方式 1: 集成到现有流程

在生成内容后，添加视觉处理步骤：

```python
from modules.visual.main import VisualProcessor

# 生成内容后
visual = VisualProcessor()
result = visual.process_draft(draft, generate_images=True)

# 获取结果
images = result['images']        # {'wechat': 'path/to/image.png', ...}
formatted = result['formatted']  # {'wechat': 'path/to/file.html', ...}
```

### 方式 2: 独立使用

```python
from modules.visual.main import VisualProcessor

visual = VisualProcessor()

# 快速处理单个内容
result = visual.quick_process(
    title="AI时代如何培养孩子",
    content="正文内容...",
    platform="xiaohongshu"
)

print(f"图片: {result['image']}")
print(f"格式化文件: {result['formatted']}")
```

## 功能说明

### 图片生成

**支持平台:**
- 公众号: 1024x1024 (教育风格)
- 小红书: 1024x1024 (多彩风格)
- 视频号: 1024x1024 (现代风格)
- 朋友圈: 1024x1024 (简约风格)

**风格选项:**
- `educational`: 专业教育风格
- `modern`: 现代简约风格
- `minimalist`: 极简风格
- `colorful`: 多彩活泼风格

### 排版输出

**公众号 (HTML):**
- 响应式设计
- 适配微信编辑器
- 包含封面图
- 段落自动缩进

**小红书 (纯文本):**
- Emoji 装饰
- 标签格式化
- 移动端优化

**视频号 (脚本):**
- 结构化脚本
- 拍摄提示
- 时长建议

**书稿 (Markdown):**
- 章节归类
- 便于编辑
- 版本追踪

## 成本参考

### DALL-E 3
- 标准质量: $0.04/张
- 高清质量: $0.08/张
- 每天 3 篇 × 3 平台 = $0.36/天 ≈ ¥2.6/天

### Flux (Replicate)
- 约 $0.003/张
- 每天 3 篇 × 3 平台 = $0.027/天 ≈ ¥0.2/天

## 输出目录

```
ai-content-factory/
├── data/
│   ├── images/              # 生成的图片
│   │   └── cover_20260312_160000.png
│   └── formatted/           # 格式化的文件
│       ├── wechat_20260312_160000.html
│       ├── xiaohongshu_20260312_160000.txt
│       ├── video_20260312_160000.txt
│       └── book_20260312_160000.md
```

## 故障排除

### 图片生成失败

**检查 API Key:**
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

**查看日志:**
```bash
tail -f logs/visual.log
```

### 飞书发布失败

1. 确认文档 Token 正确
2. 检查应用权限
3. 测试 API 连接

## 下一步

1. 在 Streamlit 界面添加"生成封面图"按钮
2. 集成到自动化工作流
3. 批量处理历史内容
4. 自定义图片风格模板

## 示例效果

生成的内容会包含:
- ✅ 高质量封面图 (适配各平台尺寸)
- ✅ 专业排版 (HTML/Markdown/纯文本)
- ✅ 自动发布到飞书文档
- ✅ 本地文件备份

**时间节省:**
- 手动制图 + 排版: 30-60 分钟/篇
- 自动化处理: 1-2 分钟/篇
- **效率提升: 30倍+**
