#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Agent 中文版 - 自动化汉化脚本

功能：
1. 从官方仓库同步最新代码
2. 智能识别新增/修改的用户可见文本
3. 根据预定义规则自动翻译为中文
4. 保持已有翻译不变
5. 生成详细的翻译报告

使用方法：
    # 基本用法（从官方仓库同步）
    python auto_translate.py --upstream nousresearch/hermes-agent
    
    # 指定规则文件
    python auto_translate.py --rules translation_rules.yaml --upstream nousresearch/hermes-agent
    
    # 仅检查（不实际修改）
    python auto_translate.py --dry-run --upstream nousresearch/hermes-agent
    
    # 翻译指定文件
    python auto_translate.py --files hermes_cli/main.py hermes_cli/commands.py
    
    # 生成报告
    python auto_translate.py --report-only

作者：Hermes Agent 中文版社区
版本：1.0.0
"""

import os
import sys
import re
import json
import yaml
import argparse
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """翻译结果数据类"""
    file_path: str
    original_text: str
    translated_text: str
    line_number: int
    rule_matched: str = ""
    confidence: float = 1.0


@dataclass
class FileTranslationStats:
    """文件翻译统计"""
    file_path: str
    total_lines: int = 0
    translated_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    translations: List[TranslationResult] = field(default_factory=list)


class AutoTranslator:
    """自动化翻译器主类"""

    def __init__(self, rules_file: str = "translation_rules.yaml", dry_run: bool = False):
        """
        初始化翻译器
        
        Args:
            rules_file: 翻译规则配置文件路径
            dry_run: 是否仅预览不实际修改
        """
        self.rules_file = Path(rules_file)
        self.dry_run = dry_run
        self.rules: Dict = {}
        self.stats: Dict[str, FileTranslationStats] = {}
        
        # 加载规则
        self._load_rules()
    
    def _load_rules(self):
        """加载翻译规则配置"""
        if not self.rules_file.exists():
            print(f"❌ 规则文件不存在: {self.rules_file}")
            sys.exit(1)
        
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        
        global_settings = self.rules.get('global', {})
        if not global_settings.get('enabled', True):
            print("⚠️ 自动翻译已禁用 (enabled: false)")
            sys.exit(0)
        
        print(f"✅ 已加载规则文件: {self.rules_file}")
        print(f"   模式: {'预览模式' if self.dry_run else '实际翻译'}")
    
    def sync_from_upstream(self, upstream_repo: str, branch: str = "main") -> bool:
        """
        从上游仓库同步代码
        
        Args:
            upstream_repo: 上游仓库地址（如 nousresearch/hermes-agent）
            branch: 要同步的分支
            
        Returns:
            bool: 是否成功同步
        """
        print(f"\n🔄 正在从上游仓库同步...")
        print(f"   上游: {upstream_repo}")
        print(f"   分支: {branch}")
        
        try:
            # 添加上游远程仓库（如果不存在）
            result = subprocess.run(
                ["git", "remote", "get-url", "upstream"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode != 0:
                subprocess.run(
                    ["git", "remote", "add", "upstream", f"https://github.com/{upstream_repo}.git"],
                    check=True,
                    cwd="."
                )
                print("   ✅ 已添加上游远程仓库")
            
            # 获取上游最新代码
            subprocess.run(
                ["git", "fetch", "upstream", branch],
                check=True,
                capture_output=True,
                cwd="."
            )
            
            # 合并上游更改
            result = subprocess.run(
                ["git", "merge", f"upstream/{branch}", "--no-edit"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode == 0:
                print("   ✅ 同步成功！")
                return True
            else:
                print(f"   ⚠️ 合并时出现冲突或错误")
                print(f"   {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ 同步失败: {e}")
            return False
    
    def get_changed_files(self) -> List[str]:
        """
        获取自上次提交以来变更的文件列表
        
        Returns:
            List[str]: 变更的文件路径列表
        """
        try:
            # 获取新增和修改的文件
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
            
        except Exception as e:
            print(f"⚠️ 无法获取变更文件列表: {e}")
            return []
    
    def should_translate_file(self, file_path: str) -> bool:
        """
        判断文件是否需要翻译
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否应该翻译该文件
        """
        path = Path(file_path)
        
        # 检查文件扩展名
        patterns = self.rules.get('global', {}).get('file_patterns', ['*.py'])
        
        for pattern in patterns:
            if path.match(pattern):
                return True
        
        return False
    
    def translate_string(self, text: str, context: str = "") -> Optional[Tuple[str, str]]:
        """
        翻译单个字符串
        
        Args:
            text: 要翻译的英文文本
            context: 上下文信息（如文件路径）
            
        Returns:
            Optional[Tuple[str, str]]: (翻译后的文本, 匹配的规则) 或 None（无需翻译）
        """
        if not text or not text.strip():
            return None
        
        original = text.strip()
        
        # 1. 检查是否已经在排除列表中
        exclusions = self.rules.get('exclusions', [])
        for exclusion in exclusions:
            pattern = exclusion.get('pattern', '')
            reason = exclusion.get('reason', '')
            if re.search(pattern, original, re.IGNORECASE):
                return None
        
        # 2. 检查特定文件的规则
        file_rules = self.rules.get('file_specific_rules', {})
        
        # 先尝试精确匹配文件路径
        if context and context in file_rules:
            specific_rules = file_rules[context]
            for en, zh in specific_rules.items():
                if original == en or original.startswith(en):
                    return (original.replace(en, zh), f"file_rule:{context}")
        
        # 再尝试通配符匹配
        for pattern, rules in file_rules.items():
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(context, pattern):
                    for en, zh in rules.items():
                        if original == en or original.startswith(en):
                            return (original.replace(en, zh), f"file_rule:{pattern}")
        
        # 3. 检查通用映射
        common_mappings = self.rules.get('common_mappings', {})
        for en, zh in common_mappings.items():
            if original == en or original.endswith(en):
                return (original.replace(en, zh, 1), "common_mapping")
            if en in original:
                # 部分匹配，替换第一个出现的
                return (original.replace(en, zh, 1), "common_mapping_partial")
        
        return None
    
    def translate_file(self, file_path: str) -> FileTranslationStats:
        """
        翻译单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            FileTranslationStats: 翻译统计信息
        """
        stats = FileTranslationStats(file_path=file_path)
        path = Path(file_path)
        
        if not path.exists():
            stats.error_count += 1
            return stats
        
        # 备份原始文件
        backup_enabled = self.rules.get('global', {}).get('backup_original', True)
        if backup_enabled and not self.dry_run:
            backup_path = path.with_suffix(path.suffix + '.backup')
            import shutil
            shutil.copy2(path, backup_path)
        
        # 读取文件内容
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"   ❌ 无法读取文件 {file_path}: {e}")
            stats.error_count += 1
            return stats
        
        stats.total_lines = len(lines)
        new_lines = []
        
        for i, line in enumerate(lines, 1):
            line_num = i
            translated_line = line
            
            # 匹配需要翻译的模式
            patterns_to_check = [
                # Python 字符串字面量
                (r'(["\'])([^"\']+?)\1', lambda m: (m.group(2), m.group(1))),
                # f-string
                (rf'f(["\'])([^"\']*?[A-Z][^"\']*?)\1', lambda m: (m.group(2), m.group(1))),
                # print() 语句
                (r'print\(f?["\']([^"\']+)["\']', lambda m: (m.group(1), None)),
                # raise 语句
                (r'raise\s+\w+Error\(["\']([^"\']+)["\']', lambda m: (m.group(1), None)),
            ]
            
            should_translate = False
            original_text = ""
            quote_char = None
            
            for pattern, extractor in patterns_to_check:
                match = re.search(pattern, line)
                if match:
                    original_text, quote_char = extractor(match)
                    if original_text and len(original_text) > 3:  # 至少4个字符才考虑翻译
                        result = self.translate_string(original_text, context=file_path)
                        if result:
                            translated_text, rule_matched = result
                            
                            # 替换原文
                            if quote_char:
                                new_content = line.replace(
                                    f"{quote_char}{original_text}{quote_char}",
                                    f"{quote_char}{translated_text}{quote_char}",
                                    1
                                )
                            else:
                                new_content = line.replace(original_text, translated_text, 1)
                            
                            if new_content != line:
                                translated_line = new_content
                                should_translate = True
                                
                                # 记录翻译结果
                                tr = TranslationResult(
                                    file_path=file_path,
                                    original_text=original_text,
                                    translated_text=translated_text,
                                    line_number=line_num,
                                    rule_matched=rule_matched
                                )
                                stats.translations.append(tr)
                                stats.translated_count += 1
                            break
            
            new_lines.append(translated_line)
            
            if not should_translate:
                stats.skipped_count += 1
        
        # 写入翻译后的文件
        if stats.translated_count > 0 and not self.dry_run:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                # 删除备份
                if backup_enabled and backup_path.exists():
                    backup_path.unlink()
                    
            except Exception as e:
                print(f"   ❌ 写入失败 {file_path}: {e}")
                stats.error_count += 1
        
        return stats
    
    def translate_files(self, file_paths: List[str]) -> Dict[str, FileTranslationStats]:
        """
        批量翻译多个文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            Dict: 各文件的翻译统计
        """
        results = {}
        total_translations = 0
        
        print(f"\n📝 开始翻译 {len(file_paths)} 个文件...\n")
        
        for i, file_path in enumerate(file_paths, 1):
            if not self.should_translate_file(file_path):
                continue
            
            print(f"[{i}/{len(file_paths)}] 正在处理: {file_path}")
            
            stats = self.translate_file(file_path)
            results[file_path] = stats
            total_translations += stats.translated_count
            
            if stats.translated_count > 0:
                print(f"   ✅ 翻译了 {stats.translated_count} 条文本")
            else:
                print(f"   ℹ️ 无需翻译")
        
        print(f"\n{'='*60}")
        print(f"✅ 翻译完成！共翻译 {total_translations} 条文本")
        print(f"{'='*60}\n")
        
        self.stats = results
        return results
    
    def generate_report(self, output_file: str = "translation_report.md") -> str:
        """
        生成翻译报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            str: 报告内容
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 🔄 Hermes Agent 自动汉化报告

**生成时间**: {now}  
**运行模式**: {"预览（未实际修改）" if self.dry_run else "正式翻译"}  
**规则文件**: {self.rules_file}

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 处理文件数 | {len(self.stats)} |
| 总翻译条目数 | {sum(s.translated_count for s in self.stats.values())} |
| 总跳过行数 | {sum(s.skipped_count for s in self.stats.values())} |
| 错误数量 | {sum(s.error_count for s in self.stats.values())} |

---

## 📝 详细翻译记录

"""
        
        for file_path, stats in sorted(self.stats.items()):
            if stats.translated_count == 0:
                continue
                
            report += f"### 📄 {file_path}\n\n"
            report += f"| 原文 | 译文 | 行号 | 匹配规则 |\n"
            report += f"|------|------|------|----------|\n"
            
            for tr in stats.translations:
                # 截断过长的文本
                orig = tr.original_text[:50] + "..." if len(tr.original_text) > 50 else tr.original_text
                trans = tr.translated_text[:50] + "..." if len(tr.translated_text) > 50 else tr.translated_text
                
                report += f"| `{orig}` | `{trans}` | L{tr.line_number} | {tr.rule_matched} |\n"
            
            report += "\n"
        
        report += """---

## ⚙️ 配置信息

- **规则文件**: `translation_rules.yaml`
- **全局设置**:
"""
        for key, value in self.rules.get('global', {}).items():
            report += f"  - {key}: {value}\n"
        
        report += """
- **排除规则**: 
"""
        for excl in self.rules.get('exclusions', []):
            report += f"  - `{excl.get('pattern', '')}` ({excl.get('reason', '')})\n"
        
        report += """

---

*此报告由 `auto_translate.py` 自动生成*
"""
        
        # 写入文件
        if not self.dry_run:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存到: {output_file}")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Hermes Agent 自动化汉化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --upstream nousresearch/hermes-agent     # 从官方同步并翻译
  %(prog)s --files hermes_cli/main.py               # 翻译指定文件
  %(prog)s --dry-run --upstream nousresearch/hermes  # 预览模式
  %(prog)s --report-only                             # 仅生成报告
        """
    )
    
    parser.add_argument(
        '--upstream', '-u',
        type=str,
        help='上游仓库地址（如 nousresearch/hermes-agent）'
    )
    
    parser.add_argument(
        '--rules', '-r',
        type=str,
        default='translation_rules.yaml',
        help='翻译规则配置文件（默认: translation_rules.yaml）'
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        type=str,
        help='要翻译的文件列表'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='预览模式：只显示将要翻译的内容，不实际修改'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='仅生成报告，不做任何翻译'
    )
    
    parser.add_argument(
        '--branch', '-b',
        type=str,
        default='main',
        help='要同步的上游分支（默认: main）'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='translation_report.md',
        help='报告输出文件（默认: translation_report.md）'
    )
    
    args = parser.parse_args()
    
    # 初始化翻译器
    translator = AutoTranslator(rules_file=args.rules, dry_run=args.dry_run)
    
    # 仅生成报告
    if args.report_only:
        # 先扫描所有文件
        all_py_files = []
        for root, dirs, files in os.walk('.'):
            # 排除隐藏目录和虚拟环境
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
            for file in files:
                if translator.should_translate_file(os.path.join(root, file)):
                    all_py_files.append(os.path.join(root, file))
        
        translator.translate_files(all_py_files)
        report = translator.generate_report(args.output)
        print(report)
        return
    
    # 从上游同步
    if args.upstream:
        success = translator.sync_from_upstream(args.upstream, args.branch)
        if not success:
            print("\n❌ 同步失败，退出")
            sys.exit(1)
        
        # 获取变更的文件
        changed_files = translator.get_changed_files()
        
        if not changed_files:
            print("\nℹ️ 没有检测到新的变更")
            return
        
        print(f"\n📋 检测到 {len(changed_files)} 个变更文件:")
        for f in changed_files[:10]:  # 只显示前10个
            print(f"   • {f}")
        if len(changed_files) > 10:
            print(f"   ... 还有 {len(changed_files) - 10} 个文件")
        
        # 过滤需要翻译的文件
        files_to_translate = [f for f in changed_files if translator.should_translate_file(f)]
        
        if not files_to_translate:
            print("\nℹ️ 变更的文件中无需翻译的内容")
            return
        
        print(f"\n其中 {len(files_to_translate)} 个文件可能需要翻译")
        
        # 执行翻译
        translator.translate_files(files_to_translate)
    
    # 翻译指定文件
    elif args.files:
        translator.translate_files(args.files)
    
    else:
        # 默认：翻译当前目录所有相关文件
        all_py_files = []
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
            for file in files:
                if translator.should_translate_file(os.path.join(root, file)):
                    all_py_files.append(os.path.join(root, file))
        
        if not all_py_files:
            print("❌ 未找到可翻译的文件")
            sys.exit(1)
        
        translator.translate_files(all_py_files)
    
    # 生成报告
    if translator.stats:
        report = translator.generate_report(args.output)
        
        if args.dry_run:
            print("\n" + "="*60)
            print("🔍 预览模式 - 以上是将会被翻译的内容")
            print("="*60)


if __name__ == "__main__":
    main()
