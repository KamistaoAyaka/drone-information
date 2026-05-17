# AI功能安装指南

## 📋 概述

DroneScout 现在支持使用 AI 来增强数据采集、内容分类和翻译功能。

## 🚀 安装 AI 依赖

如果你想使用 AI 功能，请安装对应的 Python 包：

### 方式1：安装所有支持的 AI 包
```bash
pip install openai anthropic google-generativeai dashscope zhipuai
```

### 方式2：按需安装

**DeepSeek (深度求索)** ⭐推荐
```bash
# DeepSeek 使用 requests 库即可，无需额外安装
# 只需要有 API Key 即可使用
```

**OpenAI (GPT 系列)**
```bash
pip install openai
```

**Claude (Anthropic)**
```bash
pip install anthropic
```

**Gemini (Google)**
```bash
pip install google-generativeai
```

**通义千问 (阿里云)**
```bash
pip install dashscope
```

**智谱 AI (GLM)**
```bash
pip install zhipuai
```

## ⚠️ 注意

- **即使不安装这些包，主程序也可以正常运行**，只是 AI 功能不可用
- AI 功能是可选的，不会影响基本的数据采集和展示功能
- 使用 AI 功能需要你拥有对应服务的 API Key

## 🔑 获取 API Key

### DeepSeek ⭐推荐
1. 访问 https://platform.deepseek.com/
2. 注册并登录账号
3. 点击左侧菜单 "API Keys"
4. 点击 "创建 API Key"
5. 复制生成的 Key（注意：Key 只会显示一次，请妥善保存）
6. 充值：新用户有免费额度，用完后需要充值（价格非常便宜，约 1-2 元/百万 tokens）

### OpenAI
1. 访问 https://platform.openai.com/api-keys
2. 注册并登录账号
3. 创建 API Key

### Claude
1. 访问 https://console.anthropic.com/
2. 注册并登录账号
3. 创建 API Key

### Gemini
1. 访问 https://makersuite.google.com/app/apikey
2. 获取 API Key

### 通义千问
1. 访问 https://dashscope.console.aliyun.com/
2. 注册并登录阿里云
3. 开通服务并获取 API Key

### 智谱 AI
1. 访问 https://open.bigmodel.cn/
2. 注册并登录
3. 获取 API Key

## 🧪 测试 AI 功能

安装完依赖后，重启 Web 服务即可使用 AI 功能：

```bash
python drone_scout.py web
```

然后在前端界面的三个 AI 选择框中选择你想要的 AI 服务商，输入 API Key 即可使用。

## 💡 建议

- ⭐ **强烈推荐 DeepSeek**：国产优秀大模型，价格便宜（约 1-2 元/百万 tokens），国内访问稳定，无需翻墙
- 如果你在中国大陆，建议使用 DeepSeek、通义千问、智谱 AI 或星火认知，因为这些服务在国内访问更稳定
- OpenAI 和 Claude 在中国大陆需要特殊网络环境才能访问
- Gemini 在中国大陆访问可能不稳定

## 🆘 常见问题

### Q: 报错 "No module named 'openai'"
**A:** 运行 `pip install openai`

### Q: 报错 "AI模块未安装"
**A:** 按照上面的安装指南安装对应的 Python 包

### Q: API Key 无效
**A:** 检查你输入的 API Key 是否正确，确保没有多余的空格或特殊字符
