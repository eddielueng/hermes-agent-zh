# 🔄 Hermes Agent 自动化汉化系统 - 使用指南

## 📋 目录

- [功能概述](#功能概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
  - [方式一：GitHub Actions 全自动（推荐）](#方式一github-actions-全自动推荐)
  - [方式二：命令行半自动](#方式二命令行半自动)
  - [方式三：手动触发](#方式三手动触发)
- [配置说明](#配置说明)
  - [翻译规则配置](#翻译规则配置)
  - [排除规则](#排除规则)
  - [高级选项](#高级选项)
- [工作流程详解](#工作流程详解)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 功能概述

### 🎯 核心能力

1. **自动同步** - 从官方仓库 (nousresearch/hermes-agent) 自动拉取最新代码
2. **智能识别** - 精准识别新增/修改的用户可见英文文本
3. **规则匹配** - 基于预定义的 500+ 条翻译规则自动翻译
4. **保持兼容** - 不修改任何代码逻辑和功能
5. **自动提交** - 创建 PR 或直接推送到 main 分支
6. **报告生成** - 生成详细的翻译报告

### ✨ 特色优势

| 特性 | 说明 |
|------|------|
| **零人工干预** | 完全自动运行，无需手动操作 |
| **高准确率** | 基于规则的精确匹配，避免误译 |
| **可追溯** | 每次翻译都有完整记录 |
| **灵活可控** | 支持预览、手动审核、自定义规则 |
| **安全可靠** | 自动备份原始文件 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    自动化汉化系统架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│   │  上游仓库    │    │  翻译引擎    │    │  中文版仓库  │ │
│   │              │───▶│              │───▶│              │ │
│   │ nousresearch │    │ auto_        │    │ eddielueng/  │ │
│   │ /hermes-     │    │ translate.py │    │ hermes-agent │ │
│   │ agent       │    │              │    │ -zh          │ │
│   └──────────────┘    └──────┬───────┘    └──────┬───────┘ │
│                              │                    │        │
│                              ▼                    ▼        │
│                       ┌──────────────┐    ┌──────────────┐ │
│                       │ translation │    │ GitHub       │ │
│                       │ _rules.yaml │    │ Actions      │ │
│                       │ (500+ 规则)  │    │ 工作流      │ │
│                       └──────────────┘    └──────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 三层体系

#### 第一层：数据源
- **上游仓库**: https://github.com/nousresearch/hermes-agent
- **监控频率**: 每天自动检查更新
- **同步范围**: 所有 Python 文件、文档等

#### 第二层：翻译引擎
- **核心脚本**: `auto_translate.py`
- **规则文件**: `translation_rules.yaml`
- **处理能力**: 
  - 智能识别用户可见文本
  - 基于规则精确匹配
  - 保持已有翻译不变
  - 生成详细报告

#### 第三层：自动化执行
- **GitHub Actions**: `.github/workflows/auto-translate.yml`
- **触发方式**: 定时 / 手动 / Webhook
- **输出结果**: PR 或直接推送 + 报告

---

## 快速开始

### 前置要求

- ✅ Python 3.10+
- ✅ Git 已安装并配置
- ✅ GitHub 账号及 Token（用于 API 访问）

### 一键启动（3 步搞定）

```bash
# 第 1 步：克隆中文版仓库
git clone https://github.com/eddielueng/hermes-agent-zh.git
cd hermes-agent-zh

# 第 2 步：安装依赖
pip install pyyaml

# 第 3 步：运行自动翻译（从官方同步）
python auto_translate.py --upstream nousresearch/hermes-agent
```

完成！✅ 新的英文文本会自动被翻译成中文。

---

## 使用方法

### 方式一：GitHub Actions 全自动（推荐 ⭐⭐⭐⭐⭐）

适合场景：长期维护，希望完全自动化

#### 配置步骤：

1. **创建 GitHub Token**
   
   访问：https://github.com/settings/tokens
   
   权限需要：
   - `repo` (完整仓库访问权限)
   - `workflow` (GitHub Actions 权限)

2. **添加到 Secrets**
   
   在你的仓库中：
   ```
   Settings → Secrets and variables → Actions → New repository secret
   Name: GH_TOKEN
   Value: 你的 GitHub Token
   ```

3. **启用工作流**
   
   工作流已包含在仓库中，会自动运行。

4. **查看运行状态**
   
   访问：Actions → "Auto Translation Sync"

#### 触发方式：

##### ✅ 手动触发（推荐测试时使用）
```
Actions → "Auto Translation Sync" → Run workflow → 选择参数 → Run
```

##### ⚡ 定时任务（默认每天北京时间 10:00 运行）
已配置在 `auto-translate.yml` 中：
```yaml
schedule:
  - cron: '0 2 * * *'  # UTC 02:00 = 北京时间 10:00
```

##### 🔔 监听上游 Release（可选）
可配置 webhook，当官方发布新版本时自动触发。

---

### 方式二：命令行半自动（⭐⭐⭐⭐）

适合场景：本地开发、调试、快速迭代

#### 常用命令：

```bash
# 1. 从官方同步并翻译
python auto_translate.py --upstream nousresearch/hermes-agent

# 2. 仅翻译指定文件
python auto_translate.py --files hermes_cli/main.py hermes_cli/commands.py

# 3. 预览模式（不实际修改）
python auto_translate.py --dry-run --upstream nousresearch/hermes-agent

# 4. 使用自定义规则文件
python auto_translate.py --rules my_custom_rules.yaml --upstream nousresearch/hermes-agent

# 5. 仅生成报告（不做翻译）
python auto_translate.py --report-only

# 6. 同步特定分支
python auto_translate.py --upstream nousresearch/hermes-agent --branch dev
```

#### 输出示例：

```
🔄 正在从上游仓库同步...
   上游: nousresearch/hermes-agent
   分支: main
   ✅ 已添加上游远程仓库
   ✅ 同步成功！

📋 检测到 15 个变更文件:
   • hermes_cli/main.py
   • hermes_cli/auth.py
   • tools/web_tools.py
   ...

📝 开始翻译 12 个文件...

[1/12] 正在处理: hermes_cli/main.py
   ✅ 翻译了 8 条文本

[2/12] 正在处理: hermes_cli/auth.py
   ✅ 翻译了 5 条文本

...

============================================================
✅ 翻译完成！共翻译 42 条文本
============================================================

📄 报告已保存到: translation_report.md
```

---

### 方式三：手动触发（⭐⭐⭐）

适合场景：偶尔更新，需要完全控制

#### 操作步骤：

```bash
# 1. 添加上游远程仓库
git remote add upstream https://github.com/nousresearch/hermes-agent.git

# 2. 拉取最新代码
git fetch upstream main

# 3. 查看新提交
git log HEAD..upstream/main --oneline

# 4. 合并更改
git merge upstream/main --no-edit

# 5. 运行翻译
python auto_translate.py

# 6. 检查变更
git diff --stat

# 7. 提交并推送
git add -A
git commit -m "🔄 手动汉化同步"
git push origin main
```

---

## 配置说明

### 翻译规则配置 (`translation_rules.yaml`)

#### 全局设置

```yaml
global:
  enabled: true           # 是否启用自动翻译
  log_level: INFO         # 日志级别
  backup_original: true   # 是否备份原始文件
  mode: strict            # strict=严格模式, aggressive=激进模式
  
  file_patterns:           # 要处理的文件类型
    - "*.py"
    - "*.md"
    - "*.yaml"
```

#### 通用映射表

```yaml
common_mappings:
  # 错误消息
  "Error:": "错误："
  "Warning:": "警告："
  
  # 用户交互
  "Enter ": "输入 "
  "Select ": "选择 "
  "Confirm": "确认"
  "Cancel": "取消"
  
  # 时间相关
  "just now": "刚刚"
  " ago": "前"
  "yesterday": "昨天"
```

#### 文件特定规则

```yaml
file_specific_rules:
  "hermes_cli/main.py":
    "requires an interactive terminal": "需要交互式终端"
    "Default model set to": "默认模型已设置为"
    
  "hermes_cli/status.py":
    "Hermes Agent Status": "Hermes Agent 状态"
    "Environment": "环境"
    "API Keys": "API 密钥"
```

#### 排除列表

```yaml
exclusions:
  # 不翻译 Python 关键字
  - pattern: "^import |^from |^class |^def "
    reason: "Python 代码结构关键字"
    
  # 不翻译 URL
  - pattern: "https?://[\\w\\./-]+"
    reason: "URL 地址"
    
  # 不翻译环境变量
  - pattern: "\\b[A-Z_]{2,}\\b"
    when: "in_string_literal"
    reason: "环境变量名"
```

### 如何添加新的翻译规则

#### 方法一：直接编辑 YAML 文件

编辑 `translation_rules.yaml`：

```yaml
# 在 common_mappings 中添加通用规则
common_mappings:
  "New English Text": "新的中文翻译"

# 在 file_specific_rules 中添加文件特定规则
file_specific_rules:
  "path/to/file.py":
    "Specific English text": "特定的中文翻译"
```

然后重新运行翻译：
```bash
python auto_translate.py --files path/to/file.py
```

#### 方法二：通过命令行动态添加

```bash
# 编辑规则后立即应用
vim translation_rules.yaml
python auto_translate.py --files .
```

---

## 工作流程详解

### 完整的自动化流程图

```
┌──────────────────────────────────────────────────────────────┐
│                    自动化汉化工作流                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 触发                                                    │
│     ├─ 定时任务 (每天 10:00)                               │
│     ├─ 手动触发 (Actions 页面)                             │
│     └─ Webhook (可选)                                      │
│                                                              │
│  ② 同步上游                                                │
│     ├─ git fetch upstream main                             │
│     ├─ 检查是否有新提交                                     │
│     └─ git merge upstream/main                             │
│                                                              │
│  ③ 执行翻译                                                │
│     ├─ 扫描变更文件                                        │
│     ├─ 匹配翻译规则                                        │
│     ├─ 应用中文翻译                                        │
│     └─ 生成翻译报告                                        │
│                                                              │
│  ④ 提交与发布                                              │
│     ├─ git add -A                                          │
│     ├─ git commit                                          │
│     ├─ 创建 PR 或 push 到 main                             │
│     └─ 发送通知                                            │
│                                                              │
│  ⑤ 完成                                                    │
│     ├─ 上传报告到 Artifacts                                │
│     ├─ 更新 Actions 日志                                    │
│     └─ 可选：发送 Slack/Email 通知                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 详细步骤说明

#### Step 1: 触发

**定时触发**（默认）：
- 每天 UTC 02:00（北京时间 10:00）自动运行
- 检查上游是否有新提交

**手动触发**：
- 在 Actions 页面点击 "Run workflow"
- 可选择参数：
  - `upstream_branch`: 上游分支（main/dev/next）
  - `dry_run`: 预览模式
  - `create_pr`: 是否创建 PR

#### Step 2: 同步上游

```bash
# 添加远程仓库
git remote add upstream https://github.com/nousresearch/hermes-agent.git

# 获取最新代码
git fetch upstream main

# 比较差异
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse upstream/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    # 有新提交，继续
    COMMITS=$(git rev-list --count HEAD..upstream/main)
else
    # 已经是最新，退出
fi
```

#### Step 3: 执行翻译

核心逻辑在 `auto_translate.py`：

```python
for file_path in changed_files:
    if should_translate_file(file_path):
        stats = translate_file(file_path)
        
        for line in lines:
            # 匹配模式
            if re.search(pattern, line):
                original_text = extract_text(line)
                translated = apply_rules(original_text)
                
                if translated != original_text:
                    replace_in_line(line, original_text, translated)
```

#### Step 4: 提交与发布

**如果启用 PR 模式**：
```bash
BRANCH="auto-sync-$(date +%Y%m%d-%H%M%S)"
git checkout -b $BRANCH
git commit -m "🔄 自动汉化同步"
git push origin $BRANCH
gh pr create --title "..." --body "..."
```

**如果直接推送**：
```bash
git commit -m "🔄 自动汉化同步"
git push origin main
```

#### Step 5: 完成

- 生成翻译报告
- 上传到 GitHub Artifacts
- 更新 Actions 日志
- （可选）发送通知

---

## 常见问题

### Q1: 翻译不准确怎么办？

**A**: 可以通过以下方式优化：

1. **调整规则优先级**：在 `translation_rules.yaml` 中将更具体的规则放在前面
2. **添加排除规则**：对于不需要翻译的内容，添加到 `exclusions` 列表
3. **手动修正**：翻译完成后可以手动微调
4. **反馈改进**：提交 Issue 说明误译情况，我们会优化规则

### Q2: 出现合并冲突怎么办？

**A**: 工作流会尝试自动解决冲突。如果失败：

```bash
# 手动解决
git status                      # 查看冲突文件
vim <conflicted-file>           # 手动编辑
git add <resolved-file>         # 标记为已解决
git commit                     # 完成合并
```

### Q3: 如何暂停自动翻译？

**A**: 方法有三种：

1. **禁用工作流**：Settings → Actions → Disable workflow
2. **修改规则**：在 `translation_rules.yaml` 中设置 `enabled: false`
3. **删除 Token**：移除 `GH_TOKEN` Secret

### Q4: 能否只翻译某些文件？

**A**: 可以！使用 `--files` 参数：

```bash
# 只翻译主界面
python auto_translate.py --files hermes_cli/main.py

# 只翻译工具系统
python auto_translate.py --files tools/*.py
```

### Q5: 如何查看历史翻译记录？

**A**: 

1. **GitHub Actions 日志**：每次运行的详细日志
2. **Git 提交历史**：所有翻译都有 commit 记录
3. **翻译报告**：`translation_report.md` 包含详细信息
4. **Artifacts**：GitHub 保存最近 30 天的报告

### Q6: 性能如何？会影响速度吗？

**A**: 

- **翻译速度快**：通常几秒内完成（取决于变更量）
- **不影响原项目性能**：翻译是离线进行的
- **资源占用低**：主要消耗 CPU 进行字符串匹配

---

## 最佳实践

### ✅ 推荐做法

1. **定期审查 PR**
   - 不要直接合到 main，先创建 PR 审核
   - 检查翻译是否准确
   - 测试功能是否正常

2. **保持规则更新**
   - 当官方新增术语时，及时更新规则
   - 收集用户反馈，持续优化
   - 版本化管理规则文件

3. **备份重要数据**
   - 启用 `backup_original: true`
   - 保留 Git 历史
   - 定期导出翻译报告

4. **监控运行状态**
   - 设置 Actions 失败通知
   - 定期查看翻译统计
   - 关注上游更新频率

### ❌ 避免的做法

1. **不要盲目信任自动翻译**
   - 重要更新要人工审核
   - 敏感内容要仔细检查

2. **不要频繁手动干预**
   - 让自动化流程正常工作
   - 只在必要时手动调整

3. **不要忽略错误日志**
   - Actions 失败要及时处理
   - 翻译异常要调查原因

---

## 进阶功能

### 自定义通知

在 `translation_rules.yaml` 中配置：

```yaml
notifications:
  enabled: true
  type: webhook
  webhook_url: "https://your-webhook-url.com/notify"
```

### 集成 CI/CD

可以在翻译后自动运行测试：

```yaml
# 在 .github/workflows/auto-translate.yml 的最后添加
- name: 🧪 Run tests
  run: |
    pip install pytest
    pytest tests/
```

### 多语言支持（未来）

虽然当前只支持中英翻译，但架构支持扩展：

```yaml
# 未来可能支持
languages:
  zh-CN: translation_rules_zh.yaml
  ja-JP: translation_rules_ja.yaml
  ko-KR: translation_rules_ko.yaml
```

---

## 📊 统计与监控

### 关键指标

| 指标 | 说明 | 查看方式 |
|------|------|---------|
| 翻译总条目数 | 累计翻译的文本数量 | Git log 统计 |
| 准确率 | 翻译正确的比例 | 人工抽样检查 |
| 覆盖率 | 用户可见文本的覆盖比例 | 工具扫描 |
| 同步延迟 | 上游更新到翻译完成的间隔 | Actions 时间戳 |

### 优化目标

- **准确率**: > 95%
- **覆盖率**: > 90%
- **同步延迟**: < 24 小时

---

## 📞 技术支持

### 获取帮助

1. **查看文档**：本指南 + README.md
2. **搜索 Issues**：https://github.com/eddielueng/hermes-agent-zh/issues
3. **提交新 Issue**：描述问题并提供复现步骤
4. **讨论交流**：在 Issue 中提问

### 贡献代码

欢迎提交 Pull Request 改进翻译规则或修复 Bug！

---

## 🎉 总结

这套自动化汉化系统让维护中文版变得简单高效：

✅ **零门槛** - 配置一次，永久自动运行  
✅ **高质量** - 基于规则的精准翻译  
✅ **可追溯** - 完整的历史记录  
✅ **灵活可控** - 支持多种使用模式  
✅ **安全可靠** - 自动备份和回滚  

---

**开始使用**：只需 3 个命令即可体验！

```bash
git clone https://github.com/eddielueng/hermes-agent-zh.git
cd hermes-agent-zh
python auto_translate.py --upstream nousresearch/hermes-agent
```

🚀 **享受自动化的便利吧！**

---

*最后更新：2026-04-14*  
*作者：Hermes Agent 中文版社区*  
*基于：NousResearch/hermes-agent*
