#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Agent 涓枃鐗?- 鑷姩鍖栨眽鍖栬剼鏈?

鍔熻兘锛?
1. 浠庡畼鏂逛粨搴撳悓姝ユ渶鏂颁唬鐮?
2. 鏅鸿兘璇嗗埆鏂板/淇敼鐨勭敤鎴峰彲瑙佹枃鏈?
3. 鏍规嵁棰勫畾涔夎鍒欒嚜鍔ㄧ炕璇戜负涓枃
4. 淇濇寔宸叉湁缈昏瘧涓嶅彉
5. 鐢熸垚璇︾粏鐨勭炕璇戞姤鍛?

浣跨敤鏂规硶锛?
    # 鍩烘湰鐢ㄦ硶锛堜粠瀹樻柟浠撳簱鍚屾锛?
    python auto_translate.py --upstream nousresearch/hermes-agent
    
    # 鎸囧畾瑙勫垯鏂囦欢
    python auto_translate.py --rules translation_rules.yaml --upstream nousresearch/hermes-agent
    
    # 浠呮鏌ワ紙涓嶅疄闄呬慨鏀癸級
    python auto_translate.py --dry-run --upstream nousresearch/hermes-agent
    
    # 缈昏瘧鎸囧畾鏂囦欢
    python auto_translate.py --files hermes_cli/main.py hermes_cli/commands.py
    
    # 鐢熸垚鎶ュ憡
    python auto_translate.py --report-only

浣滆€咃細Hermes Agent 涓枃鐗堢ぞ鍖?
鐗堟湰锛?.0.0
"""

import os
import sys
import re
import json
import yaml
import argparse
import subprocess
import datetime
import ast
import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


def contains_chinese(text: str) -> bool:
    """妫€娴嬫枃鏈槸鍚﹀寘鍚腑鏂囧瓧绗?""
    if not text:
        return False
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def is_likely_user_facing(line: str) -> bool:
    """鍒ゆ柇涓€琛屼唬鐮佹槸鍚﹀寘鍚敤鎴峰彲瑙佺殑瀛楃涓诧紙鑰岄潪鎶€鏈爣璇嗙锛?""
    user_facing_patterns = [
        r'print\s*\(', r'input\s*\(', r'raise\s+\w+Error',
        r'logger\.(warning|error|info|critical)\s*\(',
        r'click\.echo|rich\.print|console\.print|typer\.echo',
        r'Panel\(|Markdown\(|Text\(',
        r'prompt_toolkit|questionary|inquirer',
        r'\b(message|msg|text|label|title|description|hint|prompt|error|warning|success|info|help)\s*=',
    ]
    stripped = line.strip()
    if stripped.startswith('#'):
        return False
    for pattern in user_facing_patterns:
        if re.search(pattern, stripped):
            return True
    return False


def validate_python_syntax(file_path: str) -> bool:
    """楠岃瘉 Python 鏂囦欢璇硶鏄惁鏈夋晥"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=file_path)
        return True
    except SyntaxError as e:
        print(f"   鉂?璇硶楠岃瘉澶辫触 {file_path}: {e}")
        return False


@dataclass
class TranslationResult:
    """缈昏瘧缁撴灉鏁版嵁绫?""
    file_path: str
    original_text: str
    translated_text: str
    line_number: int
    rule_matched: str = ""
    confidence: float = 1.0


@dataclass
class FileTranslationStats:
    """鏂囦欢缈昏瘧缁熻"""
    file_path: str
    total_lines: int = 0
    translated_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    translations: List[TranslationResult] = field(default_factory=list)


class AutoTranslator:
    """鑷姩鍖栫炕璇戝櫒涓荤被"""

    def __init__(self, rules_file: str = "translation_rules.yaml", dry_run: bool = False):
        """
        鍒濆鍖栫炕璇戝櫒
        
        Args:
            rules_file: 缈昏瘧瑙勫垯閰嶇疆鏂囦欢璺緞
            dry_run: 鏄惁浠呴瑙堜笉瀹為檯淇敼
        """
        self.rules_file = Path(rules_file)
        self.dry_run = dry_run
        self.rules: Dict = {}
        self.stats: Dict[str, FileTranslationStats] = {}
        
        # 鍔犺浇瑙勫垯
        self._load_rules()
    
    def _load_rules(self):
        """鍔犺浇缈昏瘧瑙勫垯閰嶇疆"""
        if not self.rules_file.exists():
            print(f"鉂?瑙勫垯鏂囦欢涓嶅瓨鍦? {self.rules_file}")
            print("鈿狅笍 灏嗕娇鐢ㄩ粯璁よ鍒欙紙绌鸿鍒欓泦锛?)
            self.rules = {'global': {'enabled': True, 'file_patterns': ['*.py', '*.md', '*.yaml', '*.yml']}, 'common_mappings': {}, 'exclusions': [], 'file_specific_rules': {}}
            return

        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                self.rules = yaml.safe_load(f)
        except Exception as e:
            print(f"鉂?瑙勫垯鏂囦欢璇诲彇澶辫触: {e}")
            print("鈿狅笍 灏嗕娇鐢ㄩ粯璁よ鍒?)
            self.rules = {'global': {'enabled': True, 'file_patterns': ['*.py', '*.md', '*.yaml', '*.yml']}, 'common_mappings': {}, 'exclusions': [], 'file_specific_rules': {}}
            return

        global_settings = self.rules.get('global', {})
        if not global_settings.get('enabled', True):
            print("鈿狅笍 鑷姩缈昏瘧宸茬鐢?(enabled: false)")
            return

        print(f"鉁?宸插姞杞借鍒欐枃浠? {self.rules_file}")
        print(f"   妯″紡: {'棰勮妯″紡' if self.dry_run else '瀹為檯缈昏瘧'}")
    
    def sync_from_upstream(self, upstream_repo: str, branch: str = "main") -> bool:
        """
        浠庝笂娓镐粨搴撳悓姝ヤ唬鐮?
        
        Args:
            upstream_repo: 涓婃父浠撳簱鍦板潃锛堝 nousresearch/hermes-agent锛?
            branch: 瑕佸悓姝ョ殑鍒嗘敮
            
        Returns:
            bool: 鏄惁鎴愬姛鍚屾
        """
        print(f"\n馃攧 姝ｅ湪浠庝笂娓镐粨搴撳悓姝?..")
        print(f"   涓婃父: {upstream_repo}")
        print(f"   鍒嗘敮: {branch}")
        
        try:
            # 娣诲姞涓婃父杩滅▼浠撳簱锛堝鏋滀笉瀛樺湪锛?
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
                print("   鉁?宸叉坊鍔犱笂娓歌繙绋嬩粨搴?)
            
            # 鑾峰彇涓婃父鏈€鏂颁唬鐮?
            subprocess.run(
                ["git", "fetch", "upstream", branch],
                check=True,
                capture_output=True,
                cwd="."
            )
            
            # 鍚堝苟涓婃父鏇存敼
            result = subprocess.run(
                ["git", "merge", f"upstream/{branch}", "--no-edit"],
                capture_output=True,
                text=True,
                cwd="."
            )
            
            if result.returncode == 0:
                print("   鉁?鍚屾鎴愬姛锛?)
                return True
            else:
                print(f"   鈿狅笍 鍚堝苟鏃跺嚭鐜板啿绐佹垨閿欒")
                print(f"   {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   鉂?鍚屾澶辫触: {e}")
            return False
    
    def get_changed_files(self) -> List[str]:
        """
        鑾峰彇鑷笂娆℃彁浜や互鏉ュ彉鏇寸殑鏂囦欢鍒楄〃
        浣跨敤 merge-base 纭繚鍦?squash merge 鍚庝篃鑳芥纭伐浣?
        
        Returns:
            List[str]: 鍙樻洿鐨勬枃浠惰矾寰勫垪琛?
        """
        try:
            # 浼樺厛浣跨敤 merge-base锛堟洿鍙潬锛岄€傜敤浜?squash merge 鍚庯級
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD", "upstream/main"],
                capture_output=True,
                text=True,
                cwd="."
            )
            files = [f for f in result.stdout.strip().split('\n') if f]
            
            if not files:
                # 鍥為€€鍒?HEAD~1
                result = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd="."
                )
                files = [f for f in result.stdout.strip().split('\n') if f]
            
            return files
            
        except Exception as e:
            print(f"鈿狅笍 鏃犳硶鑾峰彇鍙樻洿鏂囦欢鍒楄〃: {e}")
            return []
    
    def should_translate_file(self, file_path: str) -> bool:
        """
        鍒ゆ柇鏂囦欢鏄惁闇€瑕佺炕璇?
        
        Args:
            file_path: 鏂囦欢璺緞
            
        Returns:
            bool: 鏄惁搴旇缈昏瘧璇ユ枃浠?
        """
        path = Path(file_path)
        
        # 妫€鏌ユ枃浠舵墿灞曞悕
        patterns = self.rules.get('global', {}).get('file_patterns', ['*.py'])
        
        for pattern in patterns:
            if path.match(pattern):
                return True
        
        return False
    
    def translate_string(self, text: str, context: str = "") -> Optional[Tuple[str, str]]:
        """
        缈昏瘧鍗曚釜瀛楃涓?
        
        Args:
            text: 瑕佺炕璇戠殑鑻辨枃鏂囨湰
            context: 涓婁笅鏂囦俊鎭紙濡傛枃浠惰矾寰勶級
            
        Returns:
            Optional[Tuple[str, str]]: (缈昏瘧鍚庣殑鏂囨湰, 鍖归厤鐨勮鍒? 鎴?None锛堟棤闇€缈昏瘧锛?
        """
        if not text or not text.strip():
            return None
        
        original = text.strip()
        
        # 闃查噸澶嶇炕璇戯細濡傛灉鏂囨湰宸茬粡鍖呭惈涓枃锛岃烦杩?
        if contains_chinese(original):
            return None
        
        # 1. 妫€鏌ユ槸鍚﹀凡缁忓湪鎺掗櫎鍒楄〃涓?
        exclusions = self.rules.get('exclusions', [])
        for exclusion in exclusions:
            pattern = exclusion.get('pattern', '')
            reason = exclusion.get('reason', '')
            if re.search(pattern, original, re.IGNORECASE):
                return None
        
        # 2. 妫€鏌ョ壒瀹氭枃浠剁殑瑙勫垯锛堝彧鍋氱簿纭尮閰嶏紝涓嶇敤 startswith 閬垮厤鐮村潖鏍囪瘑绗︼級
        file_rules = self.rules.get('file_specific_rules', {})
        
        if context and context in file_rules:
            specific_rules = file_rules[context]
            for en, zh in specific_rules.items():
                if original == en:
                    return (zh, f"file_rule:{context}:exact")
                # 鍏ㄨ瘝鍖归厤锛氱‘淇濅笉浼氭妸 ExitCode 鍙樻垚 閫€鍑篊ode
                if re.search(r'\b' + re.escape(en) + r'\b', original) and len(en) > 3:
                    return (re.sub(r'\b' + re.escape(en) + r'\b', zh, original, count=1), f"file_rule:{context}:word")
        
        # 閫氶厤绗︽枃浠惰鍒?
        for pattern, rules in file_rules.items():
            if '*' in pattern:
                if fnmatch.fnmatch(context, pattern):
                    for en, zh in rules.items():
                        if original == en:
                            return (zh, f"file_rule:{pattern}:exact")
                        if re.search(r'\b' + re.escape(en) + r'\b', original) and len(en) > 3:
                            return (re.sub(r'\b' + re.escape(en) + r'\b', zh, original, count=1), f"file_rule:{pattern}:word")
        
        # 3. 妫€鏌ラ€氱敤鏄犲皠锛堝彧鍦ㄥ畬鏁存秷鎭笂涓嬫枃涓娇鐢紝閬垮厤璇浛鎹唬鐮佷腑鐨勫崟璇嶏級
        common_mappings = self.rules.get('common_mappings', {})
        for en, zh in common_mappings.items():
            if original == en:
                return (zh, "common_mapping:exact")
            # 鍏ㄨ瘝杈圭晫鍖归厤锛堥伩鍏嶉儴鍒嗘浛鎹㈠ ErrorMessages锛?
            if len(en) > 4 and re.search(r'\b' + re.escape(en) + r'\b', original):
                new_text = re.sub(r'\b' + re.escape(en) + r'\b', zh, original, count=1)
                if new_text != original:
                    return (new_text, "common_mapping:word")
        
        return None
    
    def translate_file(self, file_path: str) -> FileTranslationStats:
        """
        缈昏瘧鍗曚釜鏂囦欢
        
        Args:
            file_path: 鏂囦欢璺緞
            
        Returns:
            FileTranslationStats: 缈昏瘧缁熻淇℃伅
        """
        stats = FileTranslationStats(file_path=file_path)
        path = Path(file_path)
        
        if not path.exists():
            stats.error_count += 1
            return stats
        
        # === 鐗规畩澶勭悊锛歋KILL.md 鏂囦欢鐨?description 瀛楁缈昏瘧 ===
        if path.name == 'SKILL.md' or (path.suffix == '.md' and 'optional-skills' in str(path)):
            return self._translate_skill_md(path, stats)
        
        # 瀹夊叏妫€娴嬶細妫€鏌ユ枃浠舵槸鍚﹀寘鍚湭瑙ｅ喅鐨勫悎骞跺啿绐佹爣璁?
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            if '<<<<<<< HEAD' in raw_content or '<<<<<<<<<' in raw_content:
                print(f"   鈿狅笍 璺宠繃: {file_path} (鍖呭惈鏈В鍐崇殑鍚堝苟鍐茬獊鏍囪)")
                print(f"      鎻愮ず: 宸ヤ綔娴佸簲鍏堣В鍐冲啿绐佸啀杩愯缈昏瘧")
                stats.skipped_count += 1
                return stats
        except Exception:
            pass
        
        # 澶囦唤鍘熷鏂囦欢
        backup_enabled = self.rules.get('global', {}).get('backup_original', True)
        if backup_enabled and not self.dry_run:
            backup_path = path.with_suffix(path.suffix + '.backup')
            import shutil
            shutil.copy2(path, backup_path)
        
        # 璇诲彇鏂囦欢鍐呭
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"   鉂?鏃犳硶璇诲彇鏂囦欢 {file_path}: {e}")
            stats.error_count += 1
            return stats
        
        stats.total_lines = len(lines)
        new_lines = []
        
        for i, line in enumerate(lines, 1):
            line_num = i
            translated_line = line
            stripped_line = line.strip()
            
            # 璺宠繃娉ㄩ噴琛屽拰绌鸿
            if not stripped_line or stripped_line.startswith('#'):
                new_lines.append(line)
                stats.skipped_count += 1
                continue
            
            # 闃查噸澶嶇炕璇戯細鏁磋宸插寘鍚腑鏂囧垯璺宠繃锛堥櫎闈炴槸娣峰悎涓嫳鏂囩殑鏂板鏂囨湰锛?
            chinese_ratio = sum(1 for c in stripped_line if '\u4e00' <= c <= '\u9fff') / max(len(stripped_line), 1)
            if chinese_ratio > 0.3:
                new_lines.append(line)
                stats.skipped_count += 1
                continue
            
            # 鍙鐞嗙敤鎴峰彲瑙佺殑浠ｇ爜琛岋紙print/input/raise/logger/echo 绛夛級
            if not is_likely_user_facing(line):
                new_lines.append(line)
                stats.skipped_count += 1
                continue
            
            # 绮剧‘鍖归厤闇€瑕佺炕璇戠殑妯″紡锛堝彧鍖归厤鐢ㄦ埛浜や簰鐩稿叧鐨勫瓧绗︿覆锛?
            patterns_to_check = [
                # print / echo 璇彞涓殑瀛楃涓?
                (r'(?:print|click\.echo|rich\.print|console\.print|typer\.echo|logger\.(?:warning|error|info|critical))\s*\(\s*f?["\']([^"\']{4,}?)["\']', lambda m: (m.group(1), None)),
                # raise Error("...") 
                (r'raise\s+\w+Error\s*\(\s*f?["\']([^"\']{4,}?)["\']', lambda m: (m.group(1), None)),
                # input("...") / Prompt.ask("...")
                (r'(?:input|Prompt\.ask|questionary\.prompt)\s*\(\s*f?["\']([^"\']{4,}?)["\']', lambda m: (m.group(1), None)),
                # 鍙橀噺璧嬪€间腑鐨勭敤鎴锋秷鎭瓧绗︿覆 (message="...", label="...", title="...", etc.)
                (r'\b(?:message|msg|text|label|title|description|hint|prompt|error_msg|warning_msg|success_msg|help_text)\s*=\s*f?["\']([^"\']{4,}?)["\']', lambda m: (m.group(1), None)),
                # Panel/Markdown/Text(...) 涓殑瀛楃涓?
                (r'(?:Panel|Markdown|Text|Alert|Rule|Group)\s*\(\s*f?["\']([^"\']{4,}?)["\']', lambda m: (m.group(1), None)),
            ]
            
            should_translate = False
            original_text = ""
            
            for pattern, extractor in patterns_to_check:
                match = re.search(pattern, line)
                if match:
                    original_text = extractor(match)
                    if original_text:
                        result = self.translate_string(original_text, context=file_path)
                        if result:
                            translated_text, rule_matched = result
                            
                            new_content = line.replace(original_text, translated_text, 1)
                            
                            if new_content != line:
                                translated_line = new_content
                                should_translate = True
                                
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
        
        # 鍐欏叆缈昏瘧鍚庣殑鏂囦欢
        if stats.translated_count > 0 and not self.dry_run:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                # 璇硶楠岃瘉锛氱‘淇濈炕璇戝悗鏂囦欢浠嶇劧鏄悎娉?Python
                if path.suffix == '.py':
                    if not validate_python_syntax(path):
                        print(f"   鈿狅笍 缈昏瘧鍚庤娉曟棤鏁堬紝鍥炴粴澶囦唤")
                        if backup_path.exists():
                            import shutil
                            shutil.copy2(backup_path, path)
                        backup_path.unlink() if backup_path.exists() else None
                        stats.error_count += 1
                        return stats
                
                # 鍒犻櫎澶囦唤
                if backup_enabled and backup_path.exists():
                    backup_path.unlink()
                    
            except Exception as e:
                print(f"   鉂?鍐欏叆澶辫触 {file_path}: {e}")
                stats.error_count += 1
                # 灏濊瘯鎭㈠澶囦唤
                if backup_path.exists():
                    import shutil
                    shutil.copy2(backup_path, path)
        
        return stats
    
    def _translate_skill_md(self, path: Path, stats: FileTranslationStats) -> FileTranslationStats:
        """
        缈昏瘧 SKILL.md 鏂囦欢鐨?YAML frontmatter description 瀛楁
        
        Args:
            path: SKILL.md 鏂囦欢璺緞
            stats: 缁熻瀵硅薄
            
        Returns:
            FileTranslationStats: 缈昏瘧缁熻淇℃伅
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            stats.total_lines = len(lines)
            
            # 妫€娴?YAML frontmatter (浠?--- 寮€澶?
            if not lines or not lines[0].strip().startswith('---'):
                stats.skipped_count = len(lines)
                return stats
            
            # 鎵惧埌 frontmatter 鐨勭粨鏉熶綅缃?
            frontmatter_end = -1
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    frontmatter_end = i
                    break
            
            if frontmatter_end == -1:
                # 娌℃湁鎵惧埌闂悎鐨?frontmatter锛岃烦杩?
                stats.skipped_count = len(lines)
                return stats
            
            # 鍦?frontmatter 涓煡鎵惧苟缈昏瘧 description 瀛楁
            new_lines = list(lines)
            translated_any = False
            
            for i in range(1, frontmatter_end):
                line = new_lines[i]
                
                # 鍖归厤 description: "..." 鎴?description: '...'
                desc_match = re.match(r'^(\s*description\s*:\s*)["\'](.+?)["\']\s*$', line)
                if desc_match:
                    prefix = desc_match.group(1)
                    original_desc = desc_match.group(2)
                    
                    # 璺宠繃宸茬粡鏄腑鏂囩殑鎻忚堪
                    chinese_ratio = sum(1 for c in original_desc if '\u4e00' <= c <= '\u9fff') / max(len(original_desc), 1)
                    if chinese_ratio > 0.3:
                        stats.skipped_count += 1
                        continue
                    
                    # 缈昏瘧鎻忚堪
                    result = self.translate_string(original_desc, context=str(path))
                    if result and result[0] != original_desc:
                        translated_desc = result[0]
                        new_lines[i] = f'{prefix}"{translated_desc}"'
                        translated_any = True
                        stats.translated_count += 1
                        print(f"   鉁?SKILL鎻忚堪: {original_desc[:50]}... 鈫?{translated_desc[:50]}...")
                    else:
                        stats.skipped_count += 1
                else:
                    stats.skipped_count += 1
            
            # 澶勭悊 frontmatter 涔嬪悗鐨勫唴瀹癸紙璺宠繃锛?
            for i in range(frontmatter_end + 1, len(new_lines)):
                stats.skipped_count += 1
            
            if translated_any:
                # 鍐欏洖鏂囦欢
                backup_path = path.with_suffix(path.suffix + '.backup')
                import shutil
                shutil.copy2(path, backup_path)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                print(f"   鉁?宸叉洿鏂?{path.name} 鐨?description")
            
            return stats
            
        except Exception as e:
            print(f"   鉂?缈昏瘧SKILL.md澶辫触 {path}: {e}")
            stats.error_count += 1
            return stats
    
    def translate_files(self, file_paths: List[str]) -> Dict[str, FileTranslationStats]:
        """
        鎵归噺缈昏瘧澶氫釜鏂囦欢
        
        Args:
            file_paths: 鏂囦欢璺緞鍒楄〃
            
        Returns:
            Dict: 鍚勬枃浠剁殑缈昏瘧缁熻
        """
        results = {}
        total_translations = 0
        
        print(f"\n馃摑 寮€濮嬬炕璇?{len(file_paths)} 涓枃浠?..\n")
        
        for i, file_path in enumerate(file_paths, 1):
            if not self.should_translate_file(file_path):
                continue
            
            print(f"[{i}/{len(file_paths)}] 姝ｅ湪澶勭悊: {file_path}")
            
            stats = self.translate_file(file_path)
            results[file_path] = stats
            total_translations += stats.translated_count
            
            if stats.translated_count > 0:
                print(f"   鉁?缈昏瘧浜?{stats.translated_count} 鏉℃枃鏈?)
            else:
                print(f"   鈩癸笍 鏃犻渶缈昏瘧")
        
        print(f"\n{'='*60}")
        print(f"鉁?缈昏瘧瀹屾垚锛佸叡缈昏瘧 {total_translations} 鏉℃枃鏈?)
        print(f"{'='*60}\n")
        
        self.stats = results
        return results
    
    def generate_report(self, output_file: str = "translation_report.md") -> str:
        """
        鐢熸垚缈昏瘧鎶ュ憡
        
        Args:
            output_file: 杈撳嚭鏂囦欢璺緞
            
        Returns:
            str: 鎶ュ憡鍐呭
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# 馃攧 Hermes Agent 鑷姩姹夊寲鎶ュ憡

**鐢熸垚鏃堕棿**: {now}  
**杩愯妯″紡**: {"棰勮锛堟湭瀹為檯淇敼锛? if self.dry_run else "姝ｅ紡缈昏瘧"}  
**瑙勫垯鏂囦欢**: {self.rules_file}

---

## 馃搳 鎬讳綋缁熻

| 鎸囨爣 | 鏁板€?|
|------|------|
| 澶勭悊鏂囦欢鏁?| {len(self.stats)} |
| 鎬荤炕璇戞潯鐩暟 | {sum(s.translated_count for s in self.stats.values())} |
| 鎬昏烦杩囪鏁?| {sum(s.skipped_count for s in self.stats.values())} |
| 閿欒鏁伴噺 | {sum(s.error_count for s in self.stats.values())} |

---

## 馃摑 璇︾粏缈昏瘧璁板綍

"""
        
        for file_path, stats in sorted(self.stats.items()):
            if stats.translated_count == 0:
                continue
                
            report += f"### 馃搫 {file_path}\n\n"
            report += f"| 鍘熸枃 | 璇戞枃 | 琛屽彿 | 鍖归厤瑙勫垯 |\n"
            report += f"|------|------|------|----------|\n"
            
            for tr in stats.translations:
                # 鎴柇杩囬暱鐨勬枃鏈?
                orig = tr.original_text[:50] + "..." if len(tr.original_text) > 50 else tr.original_text
                trans = tr.translated_text[:50] + "..." if len(tr.translated_text) > 50 else tr.translated_text
                
                report += f"| `{orig}` | `{trans}` | L{tr.line_number} | {tr.rule_matched} |\n"
            
            report += "\n"
        
        report += """---

## 鈿欙笍 閰嶇疆淇℃伅

- **瑙勫垯鏂囦欢**: `translation_rules.yaml`
- **鍏ㄥ眬璁剧疆**:
"""
        for key, value in self.rules.get('global', {}).items():
            report += f"  - {key}: {value}\n"
        
        report += """
- **鎺掗櫎瑙勫垯**: 
"""
        for excl in self.rules.get('exclusions', []):
            report += f"  - `{excl.get('pattern', '')}` ({excl.get('reason', '')})\n"
        
        report += """

---

*姝ゆ姤鍛婄敱 `auto_translate.py` 鑷姩鐢熸垚*
"""
        
        # 鍐欏叆鏂囦欢
        if not self.dry_run:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"馃搫 鎶ュ憡宸蹭繚瀛樺埌: {output_file}")
        
        return report


def main():
    """涓诲嚱鏁?""
    parser = argparse.ArgumentParser(
        description="Hermes Agent 鑷姩鍖栨眽鍖栧伐鍏?,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
绀轰緥鐢ㄦ硶:
  %(prog)s --upstream nousresearch/hermes-agent     # 浠庡畼鏂瑰悓姝ュ苟缈昏瘧
  %(prog)s --files hermes_cli/main.py               # 缈昏瘧鎸囧畾鏂囦欢
  %(prog)s --dry-run --upstream nousresearch/hermes  # 棰勮妯″紡
  %(prog)s --report-only                             # 浠呯敓鎴愭姤鍛?
        """
    )
    
    parser.add_argument(
        '--upstream', '-u',
        type=str,
        help='涓婃父浠撳簱鍦板潃锛堝 nousresearch/hermes-agent锛?
    )
    
    parser.add_argument(
        '--rules', '-r',
        type=str,
        default='translation_rules.yaml',
        help='缈昏瘧瑙勫垯閰嶇疆鏂囦欢锛堥粯璁? translation_rules.yaml锛?
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        type=str,
        help='瑕佺炕璇戠殑鏂囦欢鍒楄〃'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='棰勮妯″紡锛氬彧鏄剧ず灏嗚缈昏瘧鐨勫唴瀹癸紝涓嶅疄闄呬慨鏀?
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='浠呯敓鎴愭姤鍛婏紝涓嶅仛浠讳綍缈昏瘧'
    )
    
    parser.add_argument(
        '--branch', '-b',
        type=str,
        default='main',
        help='瑕佸悓姝ョ殑涓婃父鍒嗘敮锛堥粯璁? main锛?
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='translation_report.md',
        help='鎶ュ憡杈撳嚭鏂囦欢锛堥粯璁? translation_report.md锛?
    )
    
    args = parser.parse_args()
    
    # 鍒濆鍖栫炕璇戝櫒
    translator = AutoTranslator(rules_file=args.rules, dry_run=args.dry_run)
    
    # 鍏ㄥ眬瀹夊叏妫€娴嬶細妫€鏌ヤ粨搴撲腑鏄惁鏈夋湭瑙ｅ喅鐨勫悎骞跺啿绐?
    skipped_conflicts = []
    if not args.report_only:
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=U'],
                capture_output=True, text=True, cwd='.'
            )
            conflict_files = [f for f in result.stdout.strip().split('\n') if f]
            if conflict_files:
                print(f"\n鈿狅笍 璀﹀憡: 鍙戠幇 {len(conflict_files)} 涓枃浠跺寘鍚湭瑙ｅ喅鐨勫悎骞跺啿绐?)
                print("   鍐茬獊鏂囦欢鍒楄〃:")
                for f in conflict_files[:10]:
                    print(f"     鈥?{f}")
                if len(conflict_files) > 10:
                    print(f"   ... 杩樻湁 {len(conflict_files) - 10} 涓枃浠?)
                
                # 鑷姩瑙ｅ喅鍐茬獊锛氭帴鍙梪pstream鐗堟湰
                print("\n   馃敡 鑷姩瑙ｅ喅鍐茬獊锛堟帴鍙椾笂娓哥増鏈級...")
                for f in conflict_files:
                    try:
                        subprocess.run(
                            ['git', 'checkout', '--theirs', f],
                            capture_output=True, cwd='.'
                        )
                        subprocess.run(
                            ['git', 'add', f],
                            capture_output=True, cwd='.'
                        )
                        skipped_conflicts.append(f)
                    except Exception as e:
                        print(f"     鉂?鏃犳硶瑙ｅ喅: {f} ({e})")
                
                if skipped_conflicts:
                    print(f"   鉁?宸茶嚜鍔ㄨВ鍐?{len(skipped_conflicts)} 涓啿绐佹枃浠讹紝璺宠繃缈昏瘧")
        except Exception as e:
            print(f"   鈿狅笍 鍐茬獊妫€娴嬪け璐? {e}锛岀户缁墽琛?..")
    
    # 浠呯敓鎴愭姤鍛?
    if args.report_only:
        # 鍏堟壂鎻忔墍鏈夋枃浠?
        all_py_files = []
        for root, dirs, files in os.walk('.'):
            # 鎺掗櫎闅愯棌鐩綍鍜岃櫄鎷熺幆澧?
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
            for file in files:
                if translator.should_translate_file(os.path.join(root, file)):
                    all_py_files.append(os.path.join(root, file))
        
        translator.translate_files(all_py_files)
        report = translator.generate_report(args.output)
        print(report)
        return
    
    # 浠庝笂娓稿悓姝?
    if args.upstream:
        success = translator.sync_from_upstream(args.upstream, args.branch)
        if not success:
            print("\n鈿狅笍 鍚屾澶辫触锛屼絾灏嗙户缁炕璇戝綋鍓嶆枃浠?..")

        # 鑾峰彇鍙樻洿鐨勬枃浠?
        changed_files = translator.get_changed_files()

        if not changed_files:
            print("\n鈩癸笍 娌℃湁妫€娴嬪埌鏂扮殑鍙樻洿锛屽皢鎵弿鎵€鏈夋枃浠惰繘琛岀炕璇?)
            # 鍗充娇娌℃湁鍙樻洿涔熸壂鎻忔墍鏈夋枃浠?
            all_py_files = []
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']]
                for file in files:
                    if translator.should_translate_file(os.path.join(root, file)):
                        all_py_files.append(os.path.join(root, file))

            if all_py_files:
                print(f"\n馃搵 鎵惧埌 {len(all_py_files)} 涓彲缈昏瘧鏂囦欢")
                translator.translate_files(all_py_files)
            return
        
        print(f"\n馃搵 妫€娴嬪埌 {len(changed_files)} 涓彉鏇存枃浠?")
        for f in changed_files[:10]:  # 鍙樉绀哄墠10涓?
            print(f"   鈥?{f}")
        if len(changed_files) > 10:
            print(f"   ... 杩樻湁 {len(changed_files) - 10} 涓枃浠?)
        
        # 杩囨护闇€瑕佺炕璇戠殑鏂囦欢
        files_to_translate = [f for f in changed_files if translator.should_translate_file(f)]
        
        if not files_to_translate:
            print("\n鈩癸笍 鍙樻洿鐨勬枃浠朵腑鏃犻渶缈昏瘧鐨勫唴瀹?)
            return
        
        print(f"\n鍏朵腑 {len(files_to_translate)} 涓枃浠跺彲鑳介渶瑕佺炕璇?)
        
        # 鎵ц缈昏瘧
        translator.translate_files(files_to_translate)
    
    # 缈昏瘧鎸囧畾鏂囦欢
    elif args.files:
        translator.translate_files(args.files)
    
    else:
        # 榛樿锛氱炕璇戝綋鍓嶇洰褰曟墍鏈夌浉鍏虫枃浠?
        all_py_files = []
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']]
            for file in files:
                if translator.should_translate_file(os.path.join(root, file)):
                    all_py_files.append(os.path.join(root, file))

        if not all_py_files:
            print("鈩癸笍 鏈壘鍒板彲缈昏瘧鐨勬枃浠?)
            return

        translator.translate_files(all_py_files)
    
    # 鐢熸垚鎶ュ憡
    if translator.stats:
        report = translator.generate_report(args.output)
        
        if args.dry_run:
            print("\n" + "="*60)
            print("馃攳 棰勮妯″紡 - 浠ヤ笂鏄皢浼氳缈昏瘧鐨勫唴瀹?)
            print("="*60)


if __name__ == "__main__":
    main()
