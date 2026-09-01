# 🦞 OpenClaw 启动和使用指南

## ✅ OpenClaw 已启动成功！

### 当前状态
- ✅ **网关运行中**：ws://127.0.0.1:18789
- ✅ **控制面板**：http://127.0.0.1:18789/
- ✅ **代理数量**：1 个（main）
- ✅ **会话**：1 个活跃会话
- ✅ **模型**：claude-opus-4-5-20251101

---

## 🚀 OpenClaw 基本命令

### 查看状态
```bash
openclaw status
```

### 启动网关
```bash
openclaw gateway start
```

### 停止网关
```bash
openclaw gateway stop
```

### 重启网关
```bash
openclaw gateway restart
```

### 查看日志
```bash
openclaw logs --follow
```

### 打开控制面板
```bash
openclaw dashboard
```
或直接访问：http://127.0.0.1:18789/

---

## 🔧 在 AI 内容工厂中使用 OpenClaw

### 自动集成
OpenClaw 已经集成到内容生成流程中：

```
内容生成优先级：
OpenClaw（优先）→ Claude API → Gemini API
```

### 使用方法

**方法 1：自动模式**
1. 确保 OpenClaw 网关正在运行
2. 在"内容生成"页面正常生成内容
3. 系统会自动优先使用 OpenClaw

**方法 2：检查状态**
在应用侧边栏查看：
- ✅ OpenClaw - 运行中
- ⚠️ OpenClaw (未运行) - 需要启动

---

## 📊 OpenClaw 优势

### 为什么使用 OpenClaw？

1. **本地运行**
   - 数据隐私更好
   - 响应速度更快
   - 不受网络限制

2. **功能强大**
   - 支持多种 AI 模型
   - 内置工作区管理
   - 支持技能扩展

3. **成本优化**
   - 可以使用本地模型
   - 减少 API 调用成本

---

## 🎯 OpenClaw 工作区

### 查看工作区
```bash
openclaw agents list
```

### 当前工作区
- **主工作区**：`main`
- **位置**：`~/.openclaw/agents/main/`
- **会话**：`~/.openclaw/agents/main/sessions/`

### 工作区用途
在 AI 内容工厂中，OpenClaw 工作区用于：
- 存储用户风格指南
- 保存内容生成历史
- 管理个性化设置

---

## 🔍 常用操作

### 1. 启动 OpenClaw
```bash
openclaw gateway start
```

### 2. 检查是否运行
```bash
openclaw health
```

### 3. 查看详细状态
```bash
openclaw status --all
```

### 4. 查看实时日志
```bash
openclaw logs --follow
```

### 5. 打开控制面板
```bash
openclaw dashboard
```

### 6. 更新 OpenClaw
```bash
openclaw update
```

---

## 🐛 常见问题

### Q1: OpenClaw 没有运行？
**解决方案**：
```bash
openclaw gateway start
```

### Q2: 端口被占用？
**解决方案**：
```bash
openclaw gateway --force
```
这会强制关闭占用端口的进程并重启。

### Q3: 如何查看错误日志？
**解决方案**：
```bash
openclaw logs --follow
```

### Q4: 如何重置 OpenClaw？
**解决方案**：
```bash
openclaw reset
```
⚠️ 注意：这会清除所有配置和数据！

### Q5: 如何配置 OpenClaw？
**解决方案**：
```bash
openclaw configure
```
或编辑配置文件：`~/.openclaw/openclaw.json`

---

## 📁 OpenClaw 目录结构

```
~/.openclaw/
├── openclaw.json          # 主配置文件
├── agents/                # 代理工作区
│   └── main/             # 主工作区
│       ├── sessions/     # 会话历史
│       └── workspace/    # 工作文件
├── extensions/           # 扩展插件
│   └── feishu/          # 飞书插件
└── logs/                # 日志文件
```

---

## 🎨 在 AI 内容工厂中的作用

### 内容生成流程

**使用 OpenClaw**：
```
选题 → OpenClaw 生成内容 → 保存草稿
```

**OpenClaw 不可用时**：
```
选题 → Claude/Gemini 生成内容 → 保存草稿
```

### 优势
1. **个性化**：使用你的风格指南
2. **上下文**：记住之前的对话
3. **本地化**：数据不离开你的电脑

---

## 🔄 启动和停止

### 开机自动启动
OpenClaw 已配置为 LaunchAgent，会在登录时自动启动。

### 手动控制

**启动**：
```bash
openclaw gateway start
```

**停止**：
```bash
openclaw gateway stop
```

**重启**：
```bash
openclaw gateway restart
```

**查看状态**：
```bash
openclaw gateway status
```

---

## 📊 监控 OpenClaw

### 实时监控
```bash
# 查看状态
openclaw status

# 查看日志
openclaw logs --follow

# 查看健康状态
openclaw health
```

### 控制面板
访问：http://127.0.0.1:18789/

可以看到：
- 网关状态
- 活跃会话
- 内存使用
- 代理列表

---

## 🎯 最佳实践

### 日常使用
1. **保持运行**：让 OpenClaw 一直运行
2. **定期更新**：`openclaw update`
3. **查看日志**：遇到问题时查看日志

### 性能优化
1. **清理会话**：定期清理旧会话
2. **管理内存**：监控内存使用
3. **更新模型**：使用最新的模型

### 安全建议
1. **本地访问**：只在本地访问控制面板
2. **定期备份**：备份工作区数据
3. **更新及时**：保持 OpenClaw 最新版本

---

## 📞 获取帮助

### 官方文档
- 主页：https://docs.openclaw.ai/
- FAQ：https://docs.openclaw.ai/faq
- 故障排除：https://docs.openclaw.ai/troubleshooting

### 命令帮助
```bash
openclaw --help
openclaw <command> --help
```

### 社区支持
- GitHub：https://github.com/openclaw/openclaw
- Discord：https://discord.gg/openclaw

---

## ✅ 快速检查清单

- [x] OpenClaw 已安装
- [x] 网关正在运行
- [x] 控制面板可访问
- [x] 已集成到 AI 内容工厂
- [x] 自动启动已配置

---

## 🎉 现在可以使用了！

OpenClaw 已经启动并运行，你可以：

1. ✅ 在 AI 内容工厂中自动使用 OpenClaw
2. ✅ 访问控制面板：http://127.0.0.1:18789/
3. ✅ 查看实时状态：`openclaw status`
4. ✅ 享受更快、更个性化的内容生成

重启 AI 内容工厂应用，侧边栏会显示：
- ✅ OpenClaw（绿色勾）

开始创作吧！🚀
