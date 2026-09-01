# 实时选题采集系统使用指南

## 系统概述

AI 内容工厂现在支持多种选题采集方式，可以实时获取教育领域的热点话题。

## 采集方式（按优先级）

### 1. Claude API 采集器（推荐）✅
**文件**: `modules/collector/claude_collector.py`

**特点**:
- 使用 Claude API 直接生成高质量选题
- 最稳定可靠，无需外部数据源
- 生成 15-20 个精选教育热点
- 已验证可用

**使用**:
```bash
python3 -m modules.collector.claude_collector
```

**覆盖领域**:
- 留学规划（申请策略、选校、签证政策）
- AI教育（AI工具应用、ChatGPT影响）
- 家庭教育（亲子关系、教育焦虑）
- 教育政策（双减政策、教育改革）
- 国际教育（IB/AP课程、国际学校）

### 2. 混合实时采集器
**文件**: `modules/collector/hybrid_realtime_collector.py`

**特点**:
- 结合 Claude API + 关键词搜索
- 生成 20-25 个选题
- 包含重试机制

**注意**: 可能遇到 API 超时问题，建议使用 Claude 采集器

### 3. OpenClaw 实时采集器
**文件**: `modules/collector/realtime_collector.py`

**特点**:
- 使用 OpenClaw Agent 抓取真实网站
- 支持 8 个高质量教育网站
- 可能遇到 session 锁定问题

**数据源**:
- 澎湃新闻教育频道
- 新浪教育
- 搜狐教育
- 腾讯教育
- 芥末堆
- 多知网
- 知乎教育话题
- 中国教育在线

## 在 Streamlit 界面使用

1. 访问 http://localhost:8501
2. 点击「🔄 开始采集选题」按钮
3. 系统会自动选择最佳采集方式
4. 采集完成后可以查看选题列表

## 采集策略

系统采用多层降级策略：

```
混合实时采集 → OpenClaw采集 → 传统数据源 → Claude备用
```

如果前面的方式失败，会自动切换到下一个方式。

## 生成的数据格式

```json
{
  "date": "2026-03-05",
  "total_count": 15,
  "topics": [
    {
      "title": "选题标题",
      "excerpt": "内容摘要",
      "source": "来源",
      "heat_score": "高/中/低",
      "keywords": ["关键词1", "关键词2"],
      "collected_at": "2026-03-05T19:07:53.013391"
    }
  ]
}
```

## 数据存储位置

- 最新选题: `data/topics/latest.json`
- 历史选题: `data/topics/topics_YYYY-MM-DD.json`

## 常见问题

### Q: API 超时怎么办？
A: 使用 Claude 采集器（claude_collector.py），它最稳定。

### Q: OpenClaw session 锁定？
A: 清理锁定文件或使用 Claude 采集器。

### Q: 如何获取更多选题？
A: 修改 `claude_collector.py` 中的 `count` 参数。

### Q: 选题质量如何保证？
A: 系统会自动去重、清洗，并可以通过 AI 打分筛选高质量选题。

## 最佳实践

1. **日常使用**: 直接在 Streamlit 界面点击采集按钮
2. **批量采集**: 使用命令行运行 `python3 -m modules.collector.main`
3. **定时采集**: 配置 `scheduler.py` 定时任务
4. **自定义**: 修改提示词以适应特定需求

## 下一步优化建议

1. 添加更多垂直教育媒体数据源
2. 实现真实的 web scraping（需要解决 OpenClaw 稳定性）
3. 集成百度热搜、微博热搜等实时热点
4. 添加选题趋势分析和预测功能
