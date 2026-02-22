# API Skills 配置和使用指南

K博士内容工厂已集成 4 个 API skills，帮助自动化内容发布和分析。

## 已安装的 Skills

### 1. `/wechat-publish` - 微信公众号发布
### 2. `/xiaohongshu-publish` - 小红书发布
### 3. `/baidu-analytics` - 百度统计分析
### 4. `/seo-optimize` - SEO 优化助手

---

## 快速开始

### 第一步：配置 API 凭证

编辑 `/Users/k/ai-content-factory/.env` 文件，添加以下配置：

```bash
# 微信公众号
WECHAT_APPID=your_appid_here
WECHAT_SECRET=your_secret_here

# 小红书
XHS_APP_KEY=your_app_key
XHS_APP_SECRET=your_app_secret
XHS_ACCESS_TOKEN=your_access_token

# 百度统计
BAIDU_TONGJI_TOKEN=your_token
BAIDU_TONGJI_SITE_ID=your_site_id

# SEO 工具（可选）
SEO_5118_TOKEN=your_token  # 可选
SEO_CHINAZ_KEY=your_key    # 可选
```

### 第二步：获取 API 凭证

#### 微信公众号
1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 开发 -> 基本配置
3. 获取 AppID 和 AppSecret
4. 将服务器 IP 加入白名单

#### 小红书
1. 访问 [小红书开放平台](https://open.xiaohongshu.com/)
2. 注册开发者账号
3. 创建应用获取 App Key 和 App Secret
4. 完成账号授权获取 Access Token

#### 百度统计
1. 登录 [百度统计](https://tongji.baidu.com/)
2. 管理 -> API 管理
3. 获取 token
4. 记录网站的 site_id

---

## 使用方法

### 微信公众号发布

**发布草稿到草稿箱：**
```bash
/wechat-publish 草稿 data/drafts/draft_20260220_xxx.json
```

**正式发布文章：**
```bash
/wechat-publish 发布 [标题]
```

**查看发布状态：**
```bash
/wechat-publish 状态
```

**工作流程：**
1. 从 Notion 或草稿文件读取内容
2. 转换为微信公众号 HTML 格式
3. 上传图片到素材库
4. 创建草稿或直接发布

---

### 小红书发布

**发布图文笔记：**
```bash
/xiaohongshu-publish 图文 [草稿文件]
```

**发布视频笔记：**
```bash
/xiaohongshu-publish 视频 [标题] [视频路径]
```

**查看笔记状态：**
```bash
/xiaohongshu-publish 状态 [笔记ID]
```

**注意事项：**
- 标题不超过 20 字
- 正文不超过 1000 字
- 图片最多 9 张
- 添加话题标签提高曝光

---

### 百度统计分析

**查看流量概况：**
```bash
/baidu-analytics 概况
```

**查看热门内容：**
```bash
/baidu-analytics 热门
```

**查看来源分析：**
```bash
/baidu-analytics 来源
```

**分析维度：**
- 浏览量（PV）
- 访客数（UV）
- 跳出率
- 平均访问时长
- 热门页面
- 流量来源

---

### SEO 优化

**分析内容 SEO：**
```bash
/seo-optimize 分析 data/drafts/draft_xxx.json
```

**关键词研究：**
```bash
/seo-optimize 关键词 留学申请
```

**获取优化建议：**
```bash
/seo-optimize 优化
```

**优化检查项：**
- 标题长度和关键词
- 内容结构和可读性
- 关键词密度
- 标题层级
- 内部链接

---

## 完整工作流示例

### 场景：发布一篇新文章

```bash
# 1. 生成内容（在 Streamlit 应用中）
# 选择选题 -> 生成内容 -> 保存草稿

# 2. SEO 优化
/seo-optimize 分析 data/drafts/draft_20260220_xxx.json

# 3. 根据建议优化内容（手动或让 Claude 优化）

# 4. 发布到 Notion
/publish-notion data/drafts/draft_20260220_xxx.json

# 5. 发布到微信公众号
/wechat-publish 草稿 data/drafts/draft_20260220_xxx.json

# 6. 发布到小红书
/xiaohongshu-publish 图文 data/drafts/draft_20260220_xxx.json

# 7. 等待一段时间后查看数据
/baidu-analytics 概况
```

---

## 高级用法

### 批量发布

创建一个批量发布脚本：

```bash
# 发布所有未发布的草稿
for draft in data/drafts/draft_*.json; do
    echo "处理: $draft"
    /wechat-publish 草稿 "$draft"
    /xiaohongshu-publish 图文 "$draft"
    sleep 5  # 避免 API 限流
done
```

### 定时分析

使用 cron 定时查看数据：

```bash
# 每天早上 9 点查看昨日数据
0 9 * * * /usr/local/bin/claude /baidu-analytics 概况 >> ~/analytics.log
```

### 自动优化

结合 SEO 分析自动优化内容：

```bash
# 分析 -> 优化 -> 重新发布
/seo-optimize 分析 draft.json
# 根据建议修改内容
/wechat-publish 发布 draft.json
```

---

## 故障排查

### 微信公众号

**问题：获取 token 失败**
- 检查 AppID 和 AppSecret 是否正确
- 确认 IP 地址在白名单中
- 检查公众号类型（需要认证）

**问题：发布失败**
- 检查内容是否符合规范
- 确认图片已上传到素材库
- 查看错误码：https://developers.weixin.qq.com/doc/offiaccount/Return_codes/

### 小红书

**问题：授权失败**
- 确认开发者账号已认证
- 检查 Access Token 是否过期
- 重新授权获取新 token

**问题：发布被拒**
- 检查内容是否违规
- 确认图片尺寸和数量
- 添加相关话题标签

### 百度统计

**问题：无数据返回**
- 确认 site_id 正确
- 检查日期范围
- 确认网站有流量数据

### SEO 优化

**问题：分析不准确**
- 提供完整的标题和内容
- 使用 JSON 格式的草稿文件
- 检查文件编码（UTF-8）

---

## API 限制和配额

### 微信公众号
- 每天发布次数有限制（根据账号类型）
- API 调用频率限制
- 素材库容量限制

### 小红书
- 每天发布笔记数量限制
- 图片和视频大小限制
- API 调用频率限制

### 百度统计
- API 调用次数限制（根据套餐）
- 数据查询时间范围限制

---

## 最佳实践

1. **内容优先**：先优化内容质量，再考虑发布渠道
2. **SEO 优化**：每篇内容发布前都进行 SEO 分析
3. **数据驱动**：定期查看统计数据，优化内容策略
4. **多渠道发布**：同一内容适配不同平台特点
5. **避免限流**：批量操作时添加延迟
6. **备份内容**：发布前保存到 Notion 作为备份

---

## 扩展建议

可以继续集成的 API：
- 抖音开放平台（短视频发布）
- 知乎 API（专栏文章）
- B站 API（视频投稿）
- 微博 API（微博发布）
- Google Analytics（国际流量分析）
- Ahrefs/SEMrush API（专业 SEO 工具）

---

## 技术支持

- 微信公众平台文档：https://developers.weixin.qq.com/doc/offiaccount/
- 小红书开放平台：https://open.xiaohongshu.com/doc
- 百度统计 API：https://tongji.baidu.com/api/manual/
- Claude Code Skills：https://code.claude.com/docs/en/skills

---

**更新日期：** 2026-02-20
**版本：** 1.0
