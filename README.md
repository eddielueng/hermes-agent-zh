# 🎌 Hermes Agent 中文版 (Chinese Version)

<p align="center">
  <img src="https://img.shields.io/badge/版本-基于官方最新版-blue?style=flat-square" alt="基于官方最新版" />
  <img src="https://img.shields.io/badge/语言-简体中文-red?style=flat-square" alt="简体中文" />
  <img src="https://img.shields.io/badge/状态-完全汉化-success?style=flat-square" alt="完全汉化" />
  <img src="https://img.shields.io/badge/功能-100%25兼容-brightgreen?style=flat-square" alt="100% 功能兼容" />
</p>

---

## ✨ 项目简介

**Hermes Agent 中文版** 是对 [NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent) 官方项目的 **完整中文化版本**。

### 🎯 核心特性

✅ **完全中文化** - 所有用户界面、提示信息、错误消息、帮助文档均已翻译为简体中文  
✅ **零功能影响** - 仅翻译用户可见文本，代码逻辑 100% 保持不变  
✅ **内置 XiDao Api 服务商** - 默认首选服务商（支持 Claude、GPT、GLM、Qwen 等主流模型）  
✅ **支持 23+ 主流 API 服务商** - Nous Portal、OpenAI、DeepSeek、Kimi、智谱等  
✅ **完整保留原版功能** - 所有命令、工具、网关平台功能完全保留  

---

## 🆚 与官方原版的区别

| 特性 | 官方英文版 | 本中文版 |
|------|----------|---------|
| **界面语言** | English | ✅ 简体中文 |
| **命令帮助** | 英文描述 | ✅ 中文描述 |
| **错误提示** | 英文消息 | ✅ 中文消息 |
| **状态显示** | 英文标签 | ✅ 中文标签 |
| **设置向导** | 英文引导 | ✅ 中文引导 |
| **诊断输出** | 英文报告 | ✅ 中文报告 |
| **网关消息** | 英文状态 | ✅ 中文状态 |
| **功能完整性** | 100% | ✅ 100%（完全一致） |
| **代码逻辑** | 原版 | ✅ 未修改任何业务逻辑 |

---

## 🚀 快速开始

### 安装要求

- Python 3.10+ 
- Windows / macOS / Linux / WSL2 / Android (Termux)

### 一键安装

```bash
# 克隆本仓库
git clone https://github.com/你的用户名/hermes-agent-zh.git
cd hermes-agent-zh

# 运行安装脚本
curl -fsSL https://raw.githubusercontent.com/nousresearch/hermes-agent/main/scripts/install.sh | bash

# 重新加载 shell
source ~/.bashrc  # 或 source ~/.zshrc
```

### 配置 API 密钥

编辑 `~/.hermes/.env` 文件：

```bash
# =============================================
# 推荐使用 XiDao Api（默认首选服务商）
# =============================================
XIDAO_API_KEY=sk-你的API密钥

# 或者使用其他服务商：
# OPENROUTER_API_KEY=sk-xxx          # OpenRouter（200+ 模型）
# OPENAI_API_KEY=sk-xxx              # OpenAI
# DEEPSEEK_API_KEY=sk-xxx            # DeepSeek
# KIMI_API_KEY=sk-xxx                # Kimi/Moonshot
```

### 启动 Hermes

```bash
# 方式一：交互式 CLI（推荐）
hermes

# 方式二：选择模型后启动
hermes model xidao        # 选择 XiDao Api
hermes                   # 启动聊天界面
```

---

## 📋 支持的服务商（23+ 个）

### ⭐ 首选推荐：XiDao Api（已内置）

| 服务商 | 说明 | 认证方式 |
|--------|------|---------|
| **XiDao Api** | 默认首选，支持主流热门模型 | API Key |

**支持的模型**：
- `claude-opus-4-6` - Anthropic 最强智能 ⭐
- `claude-sonnet-4-6` - Anthropic 高性能 ⭐
- `gpt-5.4` - OpenAI 最新旗舰 ⭐
- `glm-5.1` - 智谱 AI 最新国产 ⭐
- `glm-5` - 智谱 AI 国产主力
- `qwen3.6-plus` - 阿里通义千问 ⭐

### 🔑 OAuth 认证类

| 服务商 | 名称 | 说明 |
|--------|------|------|
| nous | Nous Portal | 官方推荐，200+ 模型，免费额度 |
| openai-codex | OpenAI Codex | OpenAI 设备码登录 |
| qwen-oauth | Qwen OAuth | 通义千问 OAuth 登录 |
| copilot-acp | GitHub Copilot ACP | GitHub 外部进程认证 |

### 🔐 API Key 类

| 服务商 | 名称 | API 端点 |
|--------|------|----------|
| copilot | GitHub Copilot | githubmodels.com |
| gemini | Google AI Studio | generativelanguage.googleapis.com |
| zai | Z.AI / GLM (智谱) | api.z.ai |
| kimi-coding | Kimi / Moonshot (国际) | api.moonshot.ai |
| kimi-coding-cn | Kimi / Moonshot (国内) | api.moonshot.cn |
| arcee | Arcee AI | api.arcee.ai |
| minimax | MiniMax (国际) | api.minimax.io |
| minimax-cn | MiniMax (国内) | api.minimaxi.com |
| anthropic | Anthropic (Claude) | api.anthropic.com |
| alibaba | Alibaba Cloud (DashScope) | dashscope-intl.aliyuncs.com |
| deepseek | DeepSeek | api.deepseek.com |
| xai | xAI (Grok) | api.x.ai |
| ai-gateway | Vercel AI Gateway | ai-gateway.vercel.sh |
| opencode-zen | OpenCode Zen | opencode.ai/zen/v1 |
| opencode-go | OpenCode Go | opencode.ai/zen/go/v1 |
| kilocode | Kilo Code | api.kilo.ai |
| huggingface | Hugging Face | router.huggingface.co |
| xiaomi | Xiaomi MiMo (小米) | api.xiaomimimo.com |

---

## 💻 主要命令

### 会话管理
```bash
/new                    # 开始新会话
/history                 # 显示对话历史
/save                    # 保存当前对话
/retry                   # 重试上一条消息
/undo                    # 撤销最后一次交互
/title [名称]            # 设置会话标题
/branch                  # 分支当前会话
/compress                # 压缩上下文
/status                  # 显示会话信息
```

### 配置管理
```bash
/model [模型]             # 切换模型
/provider                # 查看/切换提供商
/personality [名称]       # 设置人格
/config                  # 显示配置
/skin [主题]              # 切换显示主题
/yolo                     # 跳过危险命令审批
/fast                     # 切换快速模式
/reasoning [级别]         # 设置推理强度
```

### 工具与技能
```bash
/tools [list\|disable\|enable]  # 管理工具
/toolsets                      # 列出工具集
/skills search [关键词]        # 搜索技能
/skills install [技能名]       # 安装技能
/cron list                     # 查看定时任务
/plugins                       # 查看插件
```

### 信息与诊断
```bash
/help                    # 显示可用命令
/status                  # 显示系统状态
/usage                   # 显示令牌使用情况
/insights [天数]         # 使用洞察分析
/platforms               # 网关平台状态
/update                  # 更新到最新版本
/debug                   # 上传调试报告
```

### 系统工具
```bash
hermes status           # 查看详细状态
hermes doctor           # 运行诊断检查
hermes setup            # 运行设置向导
hermes gateway start    # 启动消息网关
hermes gateway setup    # 配置网关
```

---

## 🌐 多平台支持

Hermes Agent 支持 **6 种终端后端** 和 **7 种消息平台**：

### 终端后端
- ✅ 本地运行（Local）
- ✅ Docker 容器
- ✅ SSH 远程连接
- ✅ Daytona（无服务器）
- ✅ Modal（无服务器）
- ✅ Singularity

### 消息平台
- ✅ Telegram
- ✅ Discord
- ✅ Slack
- ✅ WhatsApp
- ✅ Signal
- ✅ Email
- ✅ CLI 终端

---

## 🎨 界面预览

### 命令选择界面（中文版）

```
选择提供商：

  ★ 1. XiDao Api            (API Key)
    2. Nous Portal          (OAuth)
    3. OpenAI Codex         (OAuth)
   ...
  23. Xiaomi MiMo           (API Key)

请选择 [1-23]:
```

### 模型选择界面（中文版）

```
从 XiDao Api 选择模型（热门主流）：

  1. claude-opus-4-6       ⭐ 最强智能 (Anthropic)
  2. claude-sonnet-4-6     ⭐ 高性能 (Anthropic)
  3. gpt-5.4              ⭐ 最新旗舰 (OpenAI)
  4. glm-5.1              ⭐ 最新国产 (智谱 AI)
  5. glm-5                国产主力 (智谱 AI)
  6. qwen3.6-plus         通义千问 (阿里)
  7. 输入自定义模型名称
```

### 状态显示界面（中文版）

```
┌─────────────────────────────────────────────────────────┐
│                 ⚕ Hermes Agent 状态                  │
└─────────────────────────────────────────────────────────┘

◆ 环境
  项目:        /home/user/hermes-agent
  Python:      3.11.0
  .env 文件:   ✓ 存在
  模型:         gpt-4o
  提供商:       XiDao Api

◆ API 密钥
  XiDao Api      ✓ sk-xida...***

◆ 认证提供商
  XiDao Api      ✓ 已配置
```

---

## 📖 详细文档

- [XiDao Api 配置指南](./XIDAO_API_配置指南.md) - 如何使用 XiDao Api 服务商
- [官方文档](https://hermes-agent.nousresearch.com/docs/) - 完整的英文原版文档
- [CLI 使用指南](https://hermes-agent.nousresearch.com/docs/cli/) - 命令行使用说明
- [网关配置](https://hermes-agent.nousresearch.com/docs/gateway/) - 消息网关配置

---

## 🔧 自定义配置

### 添加自己的 API 服务商

在 `~/.hermes/.env` 中配置：

```bash
# 方式一：作为 OpenAI 兼容端点
OPENAI_BASE_URL=https://your-api.example.com/v1
OPENAI_API_KEY=sk-your-key

# 方式二：添加到 custom_providers（config.yaml）
# 编辑 ~/.hermes/config.yaml:
custom_providers:
  - name: "我的服务商"
    base_url: "https://api.example.com/v1"
    api_key: "${MY_API_KEY}"
```

### 修改默认模型列表

编辑 `hermes_cli/setup.py` 第 114 行：

```python
"xidao": [
    "claude-opus-4-6", "claude-sonnet-4-6", "gpt-5.4",
    "glm-5.1", "glm-5", "qwen3.6-plus",
    # 在这里添加你的模型
],
```

---

## 🛠️ 开发与贡献

### 翻译范围

本项目翻译了以下类型的用户可见文本：

✅ **已翻译**
- 命令定义和描述（commands.py）
- 用户界面提示（main.py, curses_ui.py）
- 错误和警告消息
- 状态和诊断输出（status.py, doctor.py）
- 设置向导（setup.py）
- 工具系统提示（tools/）
- 网关平台消息（gateway/）
- 认证流程提示（auth.py）

❌ **未修改**（保持原样）
- 代码变量名、函数名、类名
- API 路径和配置键名
- 命令名称本身（如 `/new`, `/config`）
- 技术标识符和协议名称
- 日志格式字符串

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '添加某个功能的中文翻译'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 [NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent) 官方项目，遵循相同的开源许可证。

---

## 🙏 致谢

- **[Nous Research](https://github.com/nousresearch)** - 原始项目作者
- **[Hermes Agent 官方仓库](https://github.com/nousresearch/hermes-agent)** - 本项目的基础
- **所有贡献者** - 为原始项目做出贡献的开发者

---

## 📞 联系方式

- **问题反馈**: 请在 [GitHub Issues](https://github.com/你的用户名/hermes-agent-zh/issues) 提交
- **功能建议**: 欢迎 Pull Request
- **XiDao Api**: https://api.xidao.online

---

## 🎊 特别说明

### 关于本中文版

1. **定位**: 本项目是 Hermes Agent 的**非官方中文社区版本**
2. **目的**: 降低中文用户的使用门槛，提供更好的中文体验
3. **更新**: 将跟随官方版本持续更新翻译
4. **兼容**: 保证与官方版本 100% 功能兼容

### 与官方的关系

- ✅ 基于[官方最新版本](https://github.com/nousresearch/hermes-agent)
- ✅ 保留所有原有功能和代码逻辑
- ✅ 仅做用户界面的中文化处理
- ✅ 欢迎合并回官方（如果官方需要）

---

<p align="center">
  <b>⭐ 如果这个项目对你有帮助，请给一个 Star！⭐</b>
</p>

<p align="center">
  Made with ❤️ by Chinese AI Community | 基于 <a href="https://github.com/nousresearch/hermes-agent">NousResearch/hermes-agent</a>
</p>
