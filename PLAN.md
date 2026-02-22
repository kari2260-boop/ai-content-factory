# AI 内容工厂 - 完整技术方案

## 项目概述

**目标：** 将内容生产从"每天写4小时"优化为"每天审核30分钟"

**核心功能：**
- 自动采集每日10-20个热门选题（教育/留学/AI育儿领域）
- 基于用户风格自动生成四种格式内容（视频文案、公众号文章、朋友圈、书稿素材）
- 智能归档到书稿章节，支持每周整合、每月梳理
- 本地运行，可通过外接硬盘迁移

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI内容工厂系统                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  输入层       │      │  处理层       │      │  输出层       │
│ Topic Miner  │─────▶│ Content AI   │─────▶│ Publisher    │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
  热点采集器           数字分身引擎            多格式生成器
  智能打分器           风格迁移器              书稿归档器
  用户审核台           质量检查器              分发管理器
                       记忆融合器 【新增】
                       反馈学习器 【新增】

【处理层核心升级】
1. 记忆与知识碰撞：
   - 不仅做简单的风格化提取
   - 利用提取的热点痛点检索历史知识库
   - 融合底层逻辑，避免产出套话

2. 反馈学习闭环：
   - 对比用户修改后的定稿与 AI 原稿
   - 自动提取修改规律
   - 吸收到 style_guide 的错题本中
   - 持续优化生成质量
```

---

## 技术栈

### 核心技术
- **语言：** TypeScript + Node.js 24.13.1
- **数据库：** Supabase (云端) + JSON (本地备份)
- **AI API：** Claude (Anthropic), DeepSeek, Gemini, 自定义中转
- **定时任务：** node-cron
- **Web框架：** Next.js 14 (管理后台)

### 已有资源
- OpenClaw CLI (53个技能模块)
- PathForge Web (Next.js + Supabase)
- PathForge AI Backend (Express)
- 5,285行高质量文档（风格参考）

---

## 项目结构

```
ai-content-factory/
├── package.json                 # 项目配置
├── tsconfig.json               # TypeScript 配置
├── .env                        # 环境变量（API keys）
├── PLAN.md                     # 本文档
├── README.md                   # 使用说明
│
├── src/
│   ├── collector/              # 输入层：选题采集
│   │   ├── sources/            # 数据源爬虫
│   │   │   ├── tophub.ts       # 今日热榜（聚合多平台）【推荐】
│   │   │   ├── weibo.ts
│   │   │   ├── zhihu.ts
│   │   │   ├── wechat.ts
│   │   │   ├── xiaohongshu.ts
│   │   │   └── rss.ts
│   │   ├── scorer.ts           # 智能打分器
│   │   ├── deduplicator.ts     # 去重器
│   │   └── index.ts            # 采集器主入口
│   │
│   ├── processor/              # 处理层：风格化处理
│   │   ├── style-analyzer.ts   # 风格分析器
│   │   ├── knowledge-base.ts   # 知识库管理
│   │   ├── prompt-builder.ts   # Prompt 构建器
│   │   ├── feedback-loop.ts    # 反馈学习闭环 【新增】
│   │   └── index.ts
│   │
│   ├── generator/              # 输出层：内容生成
│   │   ├── templates/          # 格式模板
│   │   │   ├── video-script.ts
│   │   │   ├── wechat-article.ts
│   │   │   ├── moments.ts
│   │   │   └── book-material.ts
│   │   ├── ai-client.ts        # AI API 客户端
│   │   ├── multi-format.ts     # 多格式生成器
│   │   └── index.ts
│   │
│   ├── publisher/              # 分发层：归档和发布
│   │   ├── book-manager.ts     # 书稿管理器
│   │   ├── archiver.ts         # 归档器
│   │   ├── exporter.ts         # 导出器
│   │   └── index.ts
│   │
│   ├── scheduler/              # 调度层：定时任务
│   │   ├── daily-tasks.ts      # 每日任务
│   │   ├── weekly-tasks.ts     # 每周任务
│   │   ├── monthly-tasks.ts    # 每月任务
│   │   └── index.ts
│   │
│   ├── web/                    # Web 管理后台
│   │   ├── app/                # Next.js 应用
│   │   ├── components/         # React 组件
│   │   └── lib/                # 工具库
│   │
│   ├── database/               # 数据库层
│   │   ├── schema.sql          # 数据库 Schema
│   │   ├── supabase.ts         # Supabase 客户端
│   │   └── local-storage.ts    # 本地存储
│   │
│   ├── utils/                  # 工具函数
│   │   ├── logger.ts           # 日志工具
│   │   ├── config.ts           # 配置管理
│   │   └── helpers.ts          # 辅助函数
│   │
│   └── types/                  # TypeScript 类型定义
│       ├── topic.ts
│       ├── content.ts
│       └── book.ts
│
├── data/                       # 数据目录
│   ├── topics/                 # 选题数据
│   │   ├── raw/                # 原始采集数据
│   │   ├── scored/             # 打分后数据
│   │   └── selected/           # 用户选中数据
│   ├── drafts/                 # 草稿数据
│   │   ├── video/
│   │   ├── article/
│   │   ├── moments/
│   │   └── book/
│   ├── published/              # 已发布内容
│   └── book/                   # 书稿归档
│       ├── chapters/           # 按章节
│       ├── weekly/             # 每周整合
│       └── monthly/            # 每月梳理
│
├── config/                     # 配置文件
│   ├── sources.json            # 数据源配置
│   ├── prompts.json            # Prompt 模板
│   ├── book-structure.json     # 书稿结构
│   └── style-guide.json        # 风格指南
│
├── logs/                       # 日志文件
│   ├── collector.log
│   ├── generator.log
│   └── scheduler.log
│
└── scripts/                    # 脚本工具
    ├── setup.ts                # 初始化脚本
    ├── migrate.ts              # 数据迁移
    └── backup.ts               # 备份脚本
```

---

## 数据源配置

### 推荐数据源：今日热榜 (tophub.today)

**优势：**
- 一站式聚合20+主流平台热榜
- 实时更新，数据新鲜度高
- 覆盖面广：社交媒体、内容平台、垂直领域
- 减少单独爬取多个平台的开发成本

**聚合平台列表：**

**社交媒体/新闻类：**
- 微博热搜榜
- 微信24h热文榜
- 百度实时热点
- 澎湃热榜

**内容平台：**
- 知乎热榜
- 哔哩哔哩全站日榜
- 抖音总榜
- 快手实时热榜
- 小红书热门

**科技/商业类（AI/教育相关）：**
- 36氪24小时热榜（创业教育）
- 虎嗅网热文（商业观察）
- 机器之心（AI专业）
- 量子位（AI新闻）
- 掘金人工智能

**采集策略：**
1. 优先从今日热榜采集，覆盖多平台
2. 针对教育/留学/AI育儿领域做关键词过滤
3. 补充采集：小红书教育博主、知乎教育话题
4. 每日采集时间：早上7:00-8:00（热榜更新高峰）

**技术实现：**
```typescript
// collector/sources/tophub.ts
interface TopHubSource {
  platform: string;        // 平台名称
  category: string;        // 分类（科技/教育/社交）
  url: string;            // 热榜URL
  relevance: number;      // 与目标领域的相关度 (0-1)
}

// 高相关度平台（优先采集）
const HIGH_PRIORITY = [
  '知乎热榜',
  '微博热搜',
  '36氪',
  '机器之心',
  '量子位'
];
```

### 备用数据源

**直接平台采集（当今日热榜不可用时）：**
- 微博热搜 API
- 知乎热榜 API
- 小红书搜索 API
- RSS 订阅（教育类博客）

---

## 数据库 Schema

### 1. topics (选题表)

```sql
CREATE TABLE topics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  source TEXT NOT NULL,              -- 来源平台
  source_url TEXT,                   -- 原文链接
  raw_content TEXT,                  -- 原始内容
  summary TEXT,                      -- 摘要

  -- 打分数据
  relevance_score INTEGER,           -- 相关度 (0-10)
  timeliness_score INTEGER,          -- 时效性 (0-10)
  engagement_score INTEGER,          -- 热度 (0-10)
  uniqueness_score INTEGER,          -- 独特性 (0-10)
  emotion_score INTEGER,             -- 情绪共鸣度 (0-10) 【新增】
  total_score INTEGER,               -- 总分 (0-50) 【更新：从0-40改为0-50】
  ai_reason TEXT,                    -- AI 评分理由
  suggested_angles TEXT[],           -- 建议切入角度
  audience_pain_point TEXT,          -- 核心用户痛点 【新增】

  -- 状态
  status TEXT DEFAULT 'pending',     -- pending/selected/rejected/generated
  selected_at TIMESTAMP,
  user_note TEXT,                    -- 用户备注

  -- 元数据
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- 索引
  INDEX idx_status (status),
  INDEX idx_total_score (total_score DESC),
  INDEX idx_created_at (created_at DESC)
);
```

### 2. contents (内容表)

```sql
CREATE TABLE contents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic_id UUID REFERENCES topics(id),

  -- 内容数据
  format TEXT NOT NULL,              -- video/article/moments/book
  title TEXT,
  content TEXT NOT NULL,
  metadata JSONB,                    -- 格式特定元数据

  -- 书稿归档
  book_chapter TEXT,                 -- 书稿章节
  book_section TEXT,                 -- 书稿小节

  -- 状态
  status TEXT DEFAULT 'draft',       -- draft/reviewed/published
  reviewed_at TIMESTAMP,
  published_at TIMESTAMP,

  -- AI 生成信息
  ai_provider TEXT,                  -- 使用的 AI 提供商
  ai_model TEXT,                     -- 使用的模型
  generation_time INTEGER,           -- 生成耗时(ms)
  token_usage INTEGER,               -- Token 使用量

  -- 元数据
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- 索引
  INDEX idx_topic_id (topic_id),
  INDEX idx_format (format),
  INDEX idx_status (status),
  INDEX idx_book_chapter (book_chapter)
);
```

### 3. style_guide (风格指南表)

```sql
CREATE TABLE style_guide (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category TEXT NOT NULL,            -- tone/structure/vocabulary/examples
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  examples TEXT[],
  correction_history TEXT[],         -- 错题本：记录用户修改前后的对比逻辑 【新增】

  -- 学习数据
  confidence_score FLOAT,            -- 置信度 (0-1)
  sample_count INTEGER,              -- 样本数量
  last_updated TIMESTAMP DEFAULT NOW(),

  UNIQUE(category, key)
);
```

### 4. book_structure (书稿结构表)

```sql
CREATE TABLE book_structure (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chapter_number INTEGER NOT NULL,
  chapter_title TEXT NOT NULL,
  section_number INTEGER,
  section_title TEXT,
  description TEXT,
  target_word_count INTEGER,
  current_word_count INTEGER DEFAULT 0,

  -- 进度
  status TEXT DEFAULT 'planning',    -- planning/writing/reviewing/completed
  progress FLOAT DEFAULT 0,          -- 进度百分比

  -- 元数据
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(chapter_number, section_number)
);
```

---

## Prompt 模板

### 1. 选题打分 Prompt

```typescript
const TOPIC_SCORING_PROMPT = `你是一位教育领域的内容策划专家，专注于留学、AI时代育儿和家庭教育。

请对以下选题进行评分（0-10分）：

**选题信息：**
标题：{title}
来源：{source}
内容摘要：{summary}

**评分维度：**
1. 相关度 (Relevance)：与留学/AI育儿/家庭教育的相关程度
2. 时效性 (Timeliness)：话题的新鲜度和时效性
3. 热度 (Engagement)：话题的讨论热度和关注度
4. 独特性 (Uniqueness)：观点的独特性和差异化
5. 情绪共鸣 (Emotion)：能否触动家长的焦虑、期待、共鸣等核心情绪 【新增】

**用户背景：**
- 教育类博士，专注留学和AI时代家庭教育
- 目标读者：关注孩子成长的家长
- 内容风格：专业但易懂，有温度有深度

**输出格式（JSON）：**
{
  "relevance": 8,
  "timeliness": 7,
  "engagement": 9,
  "uniqueness": 6,
  "emotion": 8,
  "total": 38,
  "reason": "这个话题...",
  "audience_pain_point": "家长担心孩子在AI时代失去竞争力，不知道该培养什么技能",
  "suggested_angles": [
    "从AI时代技能培养角度切入",
    "结合留学申请趋势分析"
  ]
}`;
```

### 2. 视频文案生成 Prompt

```typescript
const VIDEO_SCRIPT_PROMPT = `你是一位专业的短视频文案创作者，擅长教育类内容。

**任务：** 将以下选题改写为3-5分钟的视频文案

**选题信息：**
{topic_info}

**用户风格指南：**
{style_guide}

**文案要求：**
1. 开头3秒抓住注意力（Hook）
2. 口语化表达，避免书面语
3. 每30秒一个小高潮
4. 包含2-3个金句（可单独截图传播）
5. 结尾有明确的行动号召（CTA）
6. 总时长控制在3-5分钟（约900-1500字）
7. 【重要】每段落必须包含 [画面/动作建议] 和 [BGM情绪] 标签，不只是纯口播稿 【新增】

**输出格式：**
【开场Hook】(0-10秒)
[画面建议：特写镜头/手势动作等]
[BGM情绪：紧张/悬疑/轻快等]
...

【核心观点1】(10-90秒)
[画面建议：...]
[BGM情绪：...]
...

【案例/故事】(90-180秒)
[画面建议：...]
[BGM情绪：...]
...

【核心观点2】(180-240秒)
[画面建议：...]
[BGM情绪：...]
...

【金句总结】(240-270秒)
[画面建议：...]
[BGM情绪：...]
...

【行动号召】(270-300秒)
[画面建议：...]
[BGM情绪：...]
...

---
**金句提取：**
1. "..."
2. "..."
3. "..."`;
```

### 3. 公众号文章生成 Prompt

```typescript
const WECHAT_ARTICLE_PROMPT = `你是一位资深的教育类公众号作者，擅长深度内容创作。

**任务：** 将以下选题扩展为2000字左右的公众号文章

**选题信息：**
{topic_info}

**用户风格指南：**
{style_guide}

**文章要求：**
1. 标题吸引人但不标题党（提供3个备选标题）
2. 开头引入场景或故事，引发共鸣
3. 结构清晰：问题-分析-解决方案-总结
4. 包含具体案例或数据支撑
5. 每300-400字一个小标题
6. 结尾留下思考问题，引导互动
7. 总字数2000字左右

**输出格式：**
【备选标题】
1. ...
2. ...
3. ...

【正文】
（开头场景/故事）
...

## 一、问题的本质
...

## 二、深层原因分析
...

## 三、实践解决方案
...

## 四、写在最后
...

【思考问题】
...`;
```

### 4. 朋友圈文案生成 Prompt

```typescript
const MOMENTS_PROMPT = `你是一位社交媒体运营专家，擅长朋友圈内容创作。

**任务：** 将以下选题浓缩为朋友圈文案

**选题信息：**
{topic_info}

**用户风格指南：**
{style_guide}

**文案要求：**
1. 字数控制在150-200字
2. 第一句话抓眼球
3. 有态度、有观点
4. 引发思考或讨论
5. 可以使用emoji但不过度
6. 结尾留钩子，引导评论

**输出格式：**
【文案】
...

【配图建议】
...

【话题标签】
#... #... #...`;
```

### 5. 小红书爆款图文 Prompt 【新增】

```typescript
const XIAOHONGSHU_PROMPT = `你是一位小红书爆款内容创作者，深谙平台流量密码。

**任务：** 将以下选题改写为小红书爆款图文

**选题信息：**
{topic_info}

**用户风格指南：**
{style_guide}

**文案要求：**
1. 字数控制在400-800字
2. 首图大标题：12字以内，极具痛点，直击焦虑
3. 正文重度使用 Emoji（每段至少2-3个）
4. 采用高干货 List 体（1234、✅❌对比、步骤拆解）
5. 每段话不超过2行，保持视觉呼吸感
6. 结尾带流量标签（8-12个）
7. 语气亲切接地气，像闺蜜聊天

**输出格式：**
【首图大标题】
（12字以内，例如："别再坑娃了！AI时代必备3大能力"）

【正文】
💡 姐妹们！最近发现好多家长都在焦虑...

✅ 第一点：...
（具体展开，带emoji）

✅ 第二点：...
（具体展开，带emoji）

✅ 第三点：...
（具体展开，带emoji）

⚠️ 避坑提醒：
❌ 千万别...
✅ 正确做法是...

📌 总结一下：
...

---
【流量标签】
#教育焦虑 #AI时代育儿 #留学规划 #家庭教育 #妈妈必看 #教育干货 #育儿经验 #学习方法

【配图建议】
封面：大字标题+痛点场景
图2-4：干货要点拆解（文字卡片）
图5-6：对比图/案例图`;
```

### 6. 书稿素材生成 Prompt

```typescript
const BOOK_MATERIAL_PROMPT = `你是一位教育类图书作者，正在撰写关于AI时代家庭教育的专著。

**任务：** 将以下选题整理为书稿素材

**选题信息：**
{topic_info}

**书稿结构：**
{book_structure}

**素材要求：**
1. 学术化表达，有理论支撑
2. 包含数据、研究、案例
3. 逻辑严密，论证充分
4. 适合归档到对应章节
5. 字数800-1200字

**输出格式：**
【建议归档章节】
第X章 第Y节

【核心论点】
...

【理论支撑】
...

【案例/数据】
...

【实践建议】
...

【参考文献】
...`;
```

---

## 开发阶段划分

### Phase 1: 项目基础搭建（1天）

**目标：** 搭建项目骨架，配置开发环境

**任务清单：**
1. ✅ 创建项目目录结构
2. ⬜ 初始化 package.json 和 tsconfig.json
3. ⬜ 配置环境变量 (.env)
4. ⬜ 设置数据库 Schema (Supabase)
5. ⬜ 创建基础类型定义 (types/)
6. ⬜ 实现日志工具 (utils/logger.ts)
7. ⬜ 实现配置管理 (utils/config.ts)

**验证标准：**
- 项目可以成功编译
- 可以连接 Supabase 数据库
- 日志系统正常工作

---

### Phase 2: 输入层开发（3天）

**目标：** 实现选题采集和智能打分

**任务清单：**
1. ⬜ 实现 AI 客户端 (generator/ai-client.ts)
2. ⬜ 实现智能打分器 (collector/scorer.ts)
3. ⬜ 实现去重器 (collector/deduplicator.ts)
4. ⬜ 实现数据源爬虫（优先级排序）
   - 【推荐】今日热榜 (tophub.today) - 一站式聚合多平台热点
   - 微博热搜
   - 知乎热榜
   - 小红书热门
5. ⬜ 实现采集器主流程 (collector/index.ts)
6. ⬜ 编写测试脚本

**验证标准：**
- 每天能采集到10-20个选题
- 打分准确率 > 70%
- 去重率 > 90%

---

### Phase 3: 处理层开发（2天）

**目标：** 建立用户风格指南和知识库，实现记忆与反馈学习

**任务清单：**
1. ⬜ 实现风格分析器 (processor/style-analyzer.ts)
   - 分析用户历史文档
   - 提取风格特征
   - 生成风格指南
2. ⬜ 实现知识库管理 (processor/knowledge-base.ts)
   - 对接 OpenClaw 记忆系统
   - 实现向量搜索
   - 【新增】旧知+新知融合逻辑：利用热点痛点检索历史知识库底层逻辑，避免套话
3. ⬜ 实现 Prompt 构建器 (processor/prompt-builder.ts)
   - 动态组装 Prompt
   - 注入风格指南和知识
4. ⬜ 【新增】实现反馈学习闭环 (processor/feedback-loop.ts)
   - 对比用户手动修改后的定稿与 AI 原稿
   - 自动提取修改规律
   - 将规律吸收到 style_guide 的 correction_history 中

**验证标准：**
- 风格指南准确反映用户特点
- 知识库可以检索相关内容并融合历史逻辑
- Prompt 构建正确
- 反馈学习能自动捕获用户修改习惯

---

### Phase 4: 输出层开发（3天）

**目标：** 实现多格式内容生成

**任务清单：**
1. ⬜ 实现视频文案生成器 (generator/templates/video-script.ts)
2. ⬜ 实现公众号文章生成器 (generator/templates/wechat-article.ts)
3. ⬜ 实现朋友圈文案生成器 (generator/templates/moments.ts)
4. ⬜ 实现书稿素材生成器 (generator/templates/book-material.ts)
5. ⬜ 实现多格式生成器 (generator/multi-format.ts)
   - 并行生成四种格式
   - 错误重试机制
   - 成本优化

**验证标准：**
- 四种格式都能正常生成
- 生成质量符合要求
- 生成时间 < 2分钟

---

### Phase 5: 分发层开发（2天）

**目标：** 实现书稿管理和内容归档

**任务清单：**
1. ⬜ 实现书稿管理器 (publisher/book-manager.ts)
   - 章节结构管理
   - 素材自动归档
   - 进度追踪
2. ⬜ 实现归档器 (publisher/archiver.ts)
   - 本地文件归档
   - Supabase 数据同步
3. ⬜ 实现导出器 (publisher/exporter.ts)
   - 导出 Markdown
   - 导出 Word
   - 导出 PDF

**验证标准：**
- 内容能正确归档到章节
- 导出格式正确
- 数据同步无误

---

### Phase 6: 调度层开发（1天）

**目标：** 实现定时任务自动化和两段式审核流

**任务清单：**
1. ⬜ 实现每日任务 (scheduler/daily-tasks.ts)
   - 每天早上8点采集选题
   - 自动打分排序
   - 推送通知
   - 【新增】两段式审核流：
     * 第一阶段：AI 生成"核心切入点和大纲"
     * 用户确认 OK 后触发第二阶段
     * 第二阶段：并行生成全格式长文（节省成本，避免垃圾产出）
2. ⬜ 实现每周任务 (scheduler/weekly-tasks.ts)
   - 每周日整合书稿
   - 生成周报
3. ⬜ 实现每月任务 (scheduler/monthly-tasks.ts)
   - 每月1号梳理书稿结构
   - 生成月报

**验证标准：**
- 定时任务准时执行
- 两段式审核流正常工作，用户可在大纲阶段拦截
- 任务执行成功率 > 95%
- 错误能正确记录和通知

---

### Phase 7: Web 管理后台（3天）

**目标：** 实现可视化管理界面和两段式审核

**任务清单：**
1. ⬜ 选题审核页面
   - 查看每日选题列表
   - 勾选感兴趣的选题
   - 添加备注和切入角度
2. ⬜ 【优化】大纲审核页面（两段式审核第一阶段）
   - 查看 AI 生成的核心切入点和大纲
   - 用户确认或修改大纲
   - 确认后触发完整内容生成
3. ⬜ 内容预览页面（两段式审核第二阶段）
   - 查看生成的四种格式（含新增的小红书格式）
   - 在线编辑修改
   - 一键复制/导出
   - 【新增】修改对比功能：记录用户修改前后差异，自动学习
4. ⬜ 书稿管理页面
   - 章节大纲可视化
   - 素材拖拽归档
   - 进度追踪仪表盘
5. ⬜ 设置页面
   - API 配置
   - 数据源配置
   - 风格指南编辑
   - 【新增】错题本查看：展示 correction_history

**验证标准：**
- 界面友好易用
- 两段式审核流畅，大纲阶段可有效拦截
- 30分钟内完成每日审核
- 所有功能正常工作
- 修改对比和学习功能正常

---

### Phase 8: 测试和优化（2天）

**目标：** 全流程测试和性能优化

**任务清单：**
1. ⬜ 端到端测试
2. ⬜ 性能优化
   - API 调用成本优化
   - 并发处理优化
   - 缓存策略
3. ⬜ 错误处理完善
4. ⬜ 文档完善
5. ⬜ 备份和迁移脚本

**验证标准：**
- 全流程无阻塞错误
- API 成本降低30%
- 文档完整可用

---

## API 成本估算

### 每日使用量估算

**输入层（选题打分）：**
- 每天采集20个选题
- 每个选题打分消耗约500 tokens
- 使用 DeepSeek（免费额度充足）
- 成本：¥0

**输出层（内容生成）：**
- 每天生成2-3个选题的内容
- 每个选题生成4种格式
- 每种格式消耗约2000 tokens 输出
- 总计：3 × 4 × 2000 = 24,000 tokens/天

**AI 提供商选择策略：**
1. 优先使用自定义中转（免费）
2. 备用 DeepSeek（免费额度）
3. 最后使用 Claude API（付费）

**预估月成本：**
- 如果全部使用免费额度：¥0
- 如果使用 Claude API：约 ¥50-100/月

---

## 数据迁移方案

### 迁移到新电脑的步骤

1. **备份数据：**
```bash
npm run backup
# 生成 backup-YYYY-MM-DD.tar.gz
```

2. **复制到外接硬盘：**
```bash
cp -r ai-content-factory /Volumes/ExternalDrive/
cp backup-YYYY-MM-DD.tar.gz /Volumes/ExternalDrive/
```

3. **在新电脑上恢复：**
```bash
# 复制项目
cp -r /Volumes/ExternalDrive/ai-content-factory ~/

# 安装依赖
cd ~/ai-content-factory
npm install

# 恢复数据
npm run restore backup-YYYY-MM-DD.tar.gz

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API keys

# 启动服务
npm run dev
```

---

## 使用流程

### 每日工作流

**早上 8:00（自动）：**
- 系统自动采集选题
- 智能打分排序
- 推送通知到微信/邮箱

**早上 8:30（5分钟）：**
- 打开管理后台
- 浏览选题列表
- 勾选 2-3 个感兴趣的选题
- 添加备注和切入角度

**早上 8:35（自动 - 第一阶段）：**
- 系统自动生成"核心切入点和大纲"
- 1分钟内生成完成

**早上 8:36（5分钟 - 大纲审核）：**
- 查看 AI 生成的大纲
- 确认切入角度是否准确
- 如不满意可修改或放弃
- 确认后触发完整内容生成

**早上 8:41（自动 - 第二阶段）：**
- 系统并行生成五种格式内容（视频、文章、朋友圈、小红书、书稿）
- 2-3 分钟后生成完成

**早上 8:45（20分钟）：**
- 查看生成的内容
- 在线编辑修改（系统自动记录修改规律）
- 一键复制到对应平台
- 书稿素材自动归档

**总耗时：约 30 分钟**

### 每周工作流

**周日晚上（自动）：**
- 系统自动整合本周书稿素材
- 按章节归档
- 生成周报（本周生成内容统计）

### 每月工作流

**每月1号（自动）：**
- 系统梳理书稿整体结构
- 生成月报（本月进度、字数统计）
- 提醒需要补充的章节

---

## 风险和应对

### 风险1：API 限流或失效

**应对：**
- 多 AI 提供商备份
- 本地缓存机制
- 失败自动重试

### 风险2：内容质量不稳定

**应对：**
- 持续优化 Prompt
- 学习用户修改习惯
- 人工审核机制

### 风险3：数据丢失

**应对：**
- Supabase 云端备份
- 本地 JSON 文件备份
- 每日自动备份脚本

### 风险4：爬虫被封

**应对：**
- 使用代理池
- 降低爬取频率
- 多数据源备份

---

## 下一步行动

1. ✅ 完成 PLAN.md 文档
2. ⬜ 开始 Phase 1：项目基础搭建
3. ⬜ 初始化 package.json
4. ⬜ 配置 TypeScript
5. ⬜ 设置 Supabase 数据库

---

## 更新日志

- 2026-02-19：创建完整技术方案文档
- 2026-02-20：【爆款与网感升级】
  * 数据库升级：topics 表新增 emotion_score 和 audience_pain_point；style_guide 表新增 correction_history
  * Prompt 优化：选题打分增加"情绪共鸣"维度；视频文案增加画面/BGM标签；新增小红书爆款图文 Prompt
  * 架构升级：处理层增加"记忆与知识碰撞"和"反馈学习闭环"模块
  * 工作流优化：实现两段式审核流（大纲确认→完整生成），节省成本避免垃圾产出
  * 数据源升级：新增"今日热榜"(tophub.today) 作为推荐数据源，一站式聚合20+平台热点
