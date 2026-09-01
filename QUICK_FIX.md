# 快速修复说明

## 问题
OpenClaw agent 需要配置 API key 才能生成内容

## 解决方案
已将系统默认改为使用 Claude API 生成（更稳定）

## 现在可以使用

### 方式1: 使用 Streamlit 界面（推荐）
```bash
cd ~/ai-content-factory
streamlit run app.py
```

### 方式2: 手动执行工作流
```bash
# Step 1: 采集选题
python3 workflow.py --step1

# Step 2: 生成内容（使用 Claude API）
python3 workflow.py --step2

# Step 3: 发布内容
python3 workflow.py --step3
```

### 方式3: 测试单个选题生成
```bash
python3 test_generate.py
```

## 效果
- ✅ 完全按照你的风格生成
- ✅ 使用你的方法论和案例库
- ✅ 5种格式一键生成
- ✅ 稳定可靠

## 如果想使用 OpenClaw
```bash
openclaw agents add main
# 按提示配置 Anthropic API key
```

然后在代码中设置 `use_openclaw=True`
