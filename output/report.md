# 🔄 Hermes Agent 自动汉化报告

**生成时间**: 2026-04-16 17:18:30  
**运行模式**: 正式翻译  
**规则文件**: translation_rules.yaml

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 处理文件数 | 1506 |
| 总翻译条目数 | 0 |
| 总跳过行数 | 652460 |
| 错误数量 | 0 |

---

## 📝 详细翻译记录

---

## ⚙️ 配置信息

- **规则文件**: `translation_rules.yaml`
- **全局设置**:
  - enabled: True
  - log_level: INFO
  - backup_original: True
  - mode: strict
  - file_patterns: ['*.py', '*.md', '*.yaml', '*.yml', '*.json']

- **排除规则**: 
  - `^import |^from |^class |^def |^async def ` (Python 代码结构关键字)
  - `\b(True|False|None|self|cls|args|kwargs|config|logger)\b` (Python 内置标识符)
  - `https?://[\w\./-]+` (URL 地址)
  - `\b[A-Z_]{2,}\b` (环境变量名)
  - `^/[a-z-]+` (斜杠命令)
  - `\bv?\d+\.\d+(\.\d+)?(-[a-z]+)?\b` (版本号)
  - `logger\.(debug|info|warning|error)\(` (日志调用)


---

*此报告由 `auto_translate.py` 自动生成*
