# 🏭 K博士 AI 内容工厂

AI 驱动的教育内容自动化生产平台

## ✨ 功能特性

- 📊 **智能选题采集**: 从多个教育资讯源自动采集热点话题
- ✍️ **AI 内容生成**: 使用 Claude 和 Gemini 生成高质量内容
- 📤 **一键发布**: 自动发布到 Notion 数据库
- 📈 **数据分析**: 百度统计集成，追踪内容表现

## 🚀 快速开始

查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解详细部署指南。

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行应用
streamlit run app.py
```

### 网页部署

推荐使用 Streamlit Cloud 一键部署，详见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 📖 使用文档

- [部署指南](./DEPLOYMENT.md)
- [使用说明](./USAGE.md)
- [工作流程](./WORKFLOW_GUIDE.md)

## 🛠️ 技术栈

- **前端**: Streamlit
- **AI**: Claude API, Gemini API
- **数据库**: Notion
- **分析**: 百度统计

## 📝 License

MIT
