# 视觉处理配置说明

## 🎨 图片生成配置

### 方案 1: DALL-E 3 (推荐)
```bash
# .env 文件添加
OPENAI_API_KEY=your_openai_api_key
```

**优势:**
- 质量稳定，理解中文好
- 成本: $0.04/张 (标准质量)
- 速度: 10-30秒/张

### 方案 2: Flux via Replicate (备选)
```bash
# .env 文件添加
REPLICATE_API_TOKEN=your_replicate_token
```

**优势:**
- 生成速度快 (5-10秒)
- 成本更低 (~$0.003/张)
- 质量也很好

## 📱 飞书文档发布配置

```bash
# .env 文件添加
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_DOC_TOKEN=FQKKdaTb6oxOBIxceIOciEK3nFe
```

**获取方式:**
1. 访问 https://open.feishu.cn/
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 开通"云文档"权限
5. 文档 Token 从 URL 中提取

## 🚀 使用方式

### 在 Streamlit 界面中使用

1. 生成内容后，勾选"生成封面图"
2. 选择图片风格 (教育/现代/简约/多彩)
3. 点击"生成并排版"
4. 自动生成图片 + 格式化内容
5. 可选发布到飞书文档

### 命令行使用

```python
from modules.visual.main import VisualProcessor

processor = VisualProcessor()

# 处理草稿
result = processor.process_draft(draft, generate_images=True)

# 结果包含:
# - result['images']: 各平台封面图
# - result['formatted']: 格式化后的文件
```

## 📊 成本估算

### 图片生成成本 (每天 3 篇内容)
- DALL-E 3: 3篇 × 3平台 × $0.04 = $0.36/天 ≈ ¥2.6/天
- Flux: 3篇 × 3平台 × $0.003 = $0.027/天 ≈ ¥0.2/天

### 推荐配置
- **日常使用**: Flux (便宜快速)
- **重要内容**: DALL-E 3 (质量更稳定)

## 🎯 效果预期

### 图片生成
- 教育风格: 专业、清爽、配色柔和
- 小红书风格: 活泼、色彩丰富、吸引眼球
- 视频号风格: 现代、简约、焦点清晰

### 排版输出
- 公众号: HTML 格式，可直接复制到编辑器
- 小红书: 纯文本 + emoji，适合移动端
- 视频号: 结构化脚本，包含拍摄提示
- 书稿: Markdown 格式，便于编辑

## 🔧 故障排除

### 图片生成失败
1. 检查 API Key 是否正确
2. 检查账户余额
3. 查看日志: `logs/visual.log`

### 飞书发布失败
1. 检查应用权限
2. 确认文档 Token 正确
3. 测试 API 连接

## 📝 下一步优化

- [ ] 支持批量生成图片
- [ ] 图片风格自定义
- [ ] 自动添加水印/Logo
- [ ] 支持更多排版模板
- [ ] 集成更多平台 (知乎、B站等)
