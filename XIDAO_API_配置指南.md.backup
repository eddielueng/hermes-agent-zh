# XiDao Api 服务商配置指南

## ✅ 已完成的工作

你的 **XiDao Api** 已经成功添加到 Hermes Agent 的内置服务商列表中！

### 📍 修改的文件：

1. **[auth.py](hermes_cli/auth.py)** - 注册服务商
   - 添加了 `xidao` 到 `PROVIDER_REGISTRY`
   - 配置名称：`XiDao Api`
   - API 端点：`https://api.xidao.online/v1`

2. **[setup.py](hermes_cli/setup.py)** - 添加默认模型列表
   - 支持模型：claude-opus-4-6, claude-sonnet-4-6, gpt-5.4, glm-5.1, glm-5, qwen3.6-plus
   - **XiDao Api 排在服务商列表第一位**（优先显示）

---

## 🚀 使用方法（三选一）

### 方式一：通过环境变量配置（推荐 ⭐⭐⭐⭐⭐）

编辑 `~/.hermes/.env` 文件（Windows: `C:\Users\你的用户名\.hermes\.env`）：

```bash
# =============================================
# XiDao Api 配置
# =============================================
XIDAO_API_KEY=sk-你的实际API密钥

# 可选：覆盖 API 地址（如果需要）
# XIDAO_BASE_URL=https://api.xidao.online/v1
```

然后运行：
```bash
hermes model xidao
```

选择你想要的模型即可！

---

### 方式二：通过 config.yaml 配置

编辑 `~/.hermes/config.yaml`：

```yaml
model:
  provider: xidao
  default: gpt-4o  # 修改成你支持的默认模型
  base_url: https://api.xidao.online/v1
  api_key: ${XIDAO_API_KEY}  # 从 .env 文件读取
```

---

### 方式三：命令行交互式选择

```bash
# 运行模型选择命令
hermes model

# 在服务商列表中找到 "XiDao Api" 并选择
# 然后选择你要使用的模型
```

---

## 🔧 验证配置是否成功

### 1. 检查服务商状态
```bash
hermes status
```
你应该能看到：
```
◆ 认证提供商
  XiDao Api      ✓ 已登录 (或显示密钥状态)
```

### 2. 测试连接
```bash
# 启动 Hermes
hermes

# 发送测试消息
你好，请介绍一下你自己
```

如果看到回复，说明配置成功！✅

---

## 📋 支持的模型

当前为 XiDao Api 预设了以下**热门主流模型**（按推荐顺序排列）：

| 模型 ID | 说明 | 厂商 |
|---------|------|------|
| `claude-opus-4-6` | Claude Opus 4.6（最强智能）⭐ | Anthropic |
| `claude-sonnet-4-6` | Claude Sonnet 4.6（高性能）⭐ | Anthropic |
| `gpt-5.4` | GPT-5.4（最新旗舰）⭐ | OpenAI |
| `glm-5.1` | GLM-5.1（最新国产）⭐ | 智谱 AI |
| `glm-5` | GLM-5（国产主力） | 智谱 AI |
| `qwen3.6-plus` | Qwen 3.6 Plus（通义千问）⭐ | 阿里 |

### 选择 XiDao Api 后，可选模型：

```
从 XiDao Api 选择模型（热门主流）：

  1. claude-opus-4-6       ⭐ 最强智能 (Anthropic)
  2. claude-sonnet-4-6     ⭐ 高性能 (Anthropic)
  3. gpt-5.4              ⭐ 最新旗舰 (OpenAI)
  4. glm-5.1              ⭐ 最新国产 (智谱 AI)
  5. glm-5                国产主力 (智谱 AI)
  6. qwen3.6-plus         通义千问 (阿里)
  7. 输入自定义模型名称     (支持任意模型)
```

### ✨ 特色
- **覆盖全球顶级模型**：Claude、GPT、GLM、Qwen 全都有
- **优先展示最新版本**：4-6、5.4、5.1 等最新型号排在前面
- **国产大模型支持**：GLM 和 Qwen 代表中国 AI 最高水平

### 🔄 如何添加更多模型？

如果你的 XiDao Api 支持其他模型，可以：

1. **临时指定**：
   ```bash
   hermes model xidao
   # 选择 "输入自定义模型名称"
   # 输入：你的模型名称（例如：glm-4、qwen-turbo 等）
   ```

2. **永久添加到预设列表**：

   编辑 [setup.py](hermes_cli/setup.py) 第 115 行，在 xidao 的模型列表中添加：
   ```python
   "xidao": [
       "claude-opus-4-6", "claude-sonnet-4-6", "gpt-5.4",
       "glm-5.1", "glm-5", "qwen3.6-plus",
       # ↓↓↓ 在这里添加你的模型 ↓↓↓
       "deepseek-chat",
       "your-custom-model",
   ],
   ```

---

## ⚙️ 高级配置（可选）

### 自定义 API 基础 URL

如果你的 XiDao Api 有特殊的端点路径：

```bash
# 在 .env 中设置
XIDAO_BASE_URL=https://your-custom-url/v1
```

### 多个 API 密钥切换

```bash
# 在 .env 中可以设置多个密钥（系统会自动选择第一个有效的）
XIDAO_API_KEY=sk-key-1
# XIDAO_API_KEY_2=sk-key-2  # 备用
```

---

## ❓ 常见问题

### Q1: 提示 "未找到 API 密钥"？
**A**: 确保 `.env` 文件中正确设置了 `XIDAO_API_KEY=sk-你的密钥`

### Q2: 如何确认我的 API 密钥有效？
**A**: 运行 `hermes status` 查看 XiDao Api 的认证状态

### Q3: 可以同时配置多个服务商吗？
**A**: 可以！Hermes Agent 支持随时切换服务商，使用 `/model` 命令即可

### Q4: 我的 XiDao Api 支持哪些模型？
**A**: 这取决于你的服务商配置。查看你的 XiDao Api 文档或联系客服获取支持的模型列表

### Q5: 如何重置回其他服务商？
**A**: 
```bash
hermes model nous        # 切换到 Nous Portal
hermes model openai      # 切换到 OpenAI
hermes model deepseek    # 切换到 DeepSeek
# 或直接运行 hermes model 查看所有可用选项
```

---

## 🎯 快速开始（3 步搞定）

```bash
# 第 1 步：配置 API 密钥
echo "XIDAO_API_KEY=sk-你的密钥" >> ~/.hermes/.env

# 第 2 步：选择 XiDao Api
hermes model xidao

# 第 3 步：选择模型并开始使用
# （在弹出的列表中选择 gpt-4o 或其他模型）

# 完成！现在启动 hermes 即可使用
hermes
```

---

## 📞 技术支持

如果遇到问题：

1. 运行诊断：`hermes doctor`
2. 查看状态：`hermes status`
3. 查看日志：`~/.hermes/logs/`

---

## ✨ 特性说明

✅ **零代码配置** - 只需环境变量即可  
✅ **自动识别** - 系统会自动加载 XiDao Api  
✅ **灵活切换** - 随时可以切换到其他服务商  
✅ **完全兼容** - 支持 OpenAI 标准格式  
✅ **中文界面** - 所有提示都是中文  

---

🎉 **恭喜！你的 XiDao Api 已经完美集成到 Hermes Agent 中了！**
