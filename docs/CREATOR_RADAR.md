# 神经多样性创作者雷达

这个模块是每天早上 8:00 运行的“内容研究员工”。它长期收集神经科学、特殊教育、ADHD、neurodiversity、个人成长、自我差异叙事相关的视频创作者和爆款视频，并输出日报。

## 它会做什么

- 收集 YouTube、Bilibili、人工导入的小红书/视频号样本。
- 记录博主粉丝量，并自动归入 `0-5,000`、`5,000-1万`、`1万-5万`、`5万-10万`、`10万-20万` 等区间。
- 记录视频播放、点赞、评论、分享。
- 计算爆火分、播放粉丝比、互动率。
- 分析视频核心主旨、为什么好、为什么能吸引流量、你可以借鉴什么。
- 每次运行保存 SQLite 数据库和 Markdown 日报。

## 初始化

```bash
cd /Users/k/ai-content-factory
python3 scripts/creator_radar.py init
```

初始化后会生成：

- 配置：`config/creator_radar.json`
- 数据库：`data/creator_radar/creator_radar.sqlite3`
- 人工导入模板：`data/creator_radar/imports/_manual_import_template.csv`

## 每日运行

```bash
cd /Users/k/ai-content-factory
python3 scripts/creator_radar.py run
```

只跑人工导入：

```bash
python3 scripts/creator_radar.py run --source manual_csv
```

只根据已有数据库重新生成报告：

```bash
python3 scripts/creator_radar.py report
```

## 平台配置

### YouTube

使用官方 YouTube Data API。把 API key 放到 `.env`：

```bash
YOUTUBE_API_KEY=你的_key
```

YouTube 官方 API 默认不能直接抓取任意视频完整字幕，所以报告里的“视频文本”会优先使用人工导入的 transcript；否则使用标题和简介。

### Bilibili

B 站使用公开网页接口。为提高稳定性，可以在 `.env` 放入登录 Cookie：

```bash
BILIBILI_COOKIE=你的_cookie
```

### 小红书和视频号

这两个平台没有稳定公开搜索 API。长期系统默认使用合规导出/人工导入：

1. 从平台、第三方数据工具或人工整理得到样本。
2. 复制 `data/creator_radar/imports/_manual_import_template.csv` 为普通 CSV 文件。
3. 填入 `platform`、`creator_name`、`follower_count`、`title`、`view_count`、`like_count`、`transcript` 等字段。
4. 运行 `python3 scripts/creator_radar.py run --source manual_csv`。

## 8:00 定时

项目的 `scheduler.py` 已接入：

- 每天 `07:00`：原有选题采集。
- 每天 `08:00`：创作者雷达日报。
- 每周日 `08:00`：原有书稿整合占位任务。

启动调度器：

```bash
cd /Users/k/ai-content-factory
python3 scheduler.py
```

日报输出目录：

```text
data/creator_radar/reports/
```

日志：

```text
logs/creator_radar.log
logs/scheduler.log
```
