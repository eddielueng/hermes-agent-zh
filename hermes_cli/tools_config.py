"""
Unified tool configuration for Hermes Agent.

`hermes tools` and `hermes setup tools` both enter this module.
Select a platform → toggle toolsets on/off → for newly enabled tools
that need API keys, run through provider-aware configuration.

Saves per-platform tool configuration to ~/.hermes/config.yaml under
the `platform_toolsets` key.
"""

import json as _json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


from hermes_cli.config import (
    load_config, save_config, get_env_value, save_env_value,
)
from hermes_cli.colors import Colors, color
from hermes_cli.nous_subscription import (
    apply_nous_managed_defaults,
    get_nous_subscription_features,
)
from tools.tool_backend_helpers import managed_nous_tools_enabled

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ─── UI Helpers (shared with setup.py) ────────────────────────────────────────

from hermes_cli.cli_output import (  # noqa: E402 — late import block
    print_error as _print_error,
    print_info as _print_info,
    print_success as _print_success,
    print_warning as _print_warning,
    prompt as _prompt,
)

# ─── Toolset Registry ─────────────────────────────────────────────────────────

# Toolsets shown in the configurator, grouped for display.
# Each entry: (toolset_name, label, description)
# These map to keys in toolsets.py TOOLSETS dict.
CONFIGURABLE_TOOLSETS = [
<<<<<<< HEAD
    ("web",             "🔍 网络搜索与抓取",    "web_search, web_extract"),
    ("browser",         "🌐 浏览器自动化",       "navigate, click, type, scroll"),
    ("terminal",        "💻 终端与进程",          "terminal, process"),
    ("file",            "📁 文件操作",           "read, write, patch, search"),
    ("code_execution",  "⚡ 代码执行",            "execute_code"),
    ("vision",          "👁️  视觉/图像分析",      "vision_analyze"),
    ("image_gen",       "🎨 图像生成",            "image_generate"),
    ("moa",             "🧠 混合代理",           "mixture_of_agents"),
    ("tts",             "🔊 文本转语音",          "text_to_speech"),
    ("skills",          "📚 技能",               "list, view, manage"),
    ("todo",            "📋 任务规划",            "todo"),
    ("memory",          "💾 记忆",               "跨会话持久化记忆"),
    ("session_search",  "🔎 会话搜索",            "搜索历史对话"),
    ("clarify",         "❓ 澄清问题",            "clarify"),
    ("delegation",      "👥 任务委派",            "delegate_task"),
    ("cronjob",         "⏰ 定时任务",            "创建/列表/更新/暂停/恢复/运行，可附加技能"),
    ("rl",              "🧪 强化学习训练",        "Tinker-Atropos 训练工具"),
    ("homeassistant",    "🏠 智能家居",           "智能家居设备控制"),
=======
    ("web",             "🔍 Web Search & Scraping",    "web_search, web_extract"),
    ("browser",         "🌐 Browser Automation",       "navigate, click, type, scroll"),
    ("terminal",        "💻 Terminal & Processes",      "terminal, process"),
    ("file",            "📁 File Operations",           "read, write, patch, search"),
    ("code_execution",  "⚡ Code Execution",            "execute_code"),
    ("vision",          "👁️  Vision / Image Analysis",  "vision_analyze"),
    ("image_gen",       "🎨 Image Generation",          "image_generate"),
    ("moa",             "🧠 Mixture of Agents",         "mixture_of_agents"),
    ("tts",             "🔊 Text-to-Speech",            "text_to_speech"),
    ("skills",          "📚 Skills",                    "list, view, manage"),
    ("todo",            "📋 Task Planning",             "todo"),
    ("memory",          "💾 Memory",                    "persistent memory across sessions"),
    ("session_search",  "🔎 Session Search",            "search past conversations"),
    ("clarify",         "❓ Clarifying Questions",      "clarify"),
    ("delegation",      "👥 Task Delegation",           "delegate_task"),
    ("cronjob",         "⏰ Cron Jobs",                 "create/list/update/pause/resume/run, with optional attached skills"),
    ("messaging",       "📨 Cross-Platform Messaging",  "send_message"),
    ("rl",              "🧪 RL Training",               "Tinker-Atropos training tools"),
    ("homeassistant",    "🏠 Home Assistant",           "smart home device control"),
>>>>>>> upstream/main
]

# Toolsets that are OFF by default for new installs.
# They're still in _HERMES_CORE_TOOLS (available at runtime if enabled),
# but the setup checklist won't pre-select them for first-time users.
_DEFAULT_OFF_TOOLSETS = {"moa", "homeassistant", "rl"}


def _get_effective_configurable_toolsets():
    """Return CONFIGURABLE_TOOLSETS + any plugin-provided toolsets.

    Plugin toolsets are appended at the end so they appear after the
    built-in toolsets in the TUI checklist.
    """
    result = list(CONFIGURABLE_TOOLSETS)
    try:
        from hermes_cli.plugins import discover_plugins, get_plugin_toolsets
        discover_plugins()  # idempotent — ensures plugins are loaded
        result.extend(get_plugin_toolsets())
    except Exception:
        pass
    return result


def _get_plugin_toolset_keys() -> set:
    """Return the set of toolset keys provided by plugins."""
    try:
        from hermes_cli.plugins import discover_plugins, get_plugin_toolsets
        discover_plugins()  # idempotent — ensures plugins are loaded
        return {ts_key for ts_key, _, _ in get_plugin_toolsets()}
    except Exception:
        return set()

# Platform display config — derived from the canonical registry so every
# module shares the same data.  Kept as dict-of-dicts for backward
# compatibility with existing ``PLATFORMS[key]["label"]`` access patterns.
from hermes_cli.platforms import PLATFORMS as _PLATFORMS_REGISTRY

PLATFORMS = {
    k: {"label": info.label, "default_toolset": info.default_toolset}
    for k, info in _PLATFORMS_REGISTRY.items()
}


# ─── Tool Categories (provider-aware configuration) ──────────────────────────
# Maps toolset keys to their provider options. When a toolset is newly enabled,
# we use this to show provider selection and prompt for the right API keys.
# Toolsets not in this map either need no config or use the simple fallback.

TOOL_CATEGORIES = {
    "tts": {
        "name": "文本转语音",
        "icon": "🔊",
        "providers": [
            {
<<<<<<< HEAD
                "name": "Nous 订阅",
                "tag": "托管的 OpenAI TTS，费用计入您的订阅",
=======
                "name": "Nous Subscription",
                "badge": "subscription",
                "tag": "Managed OpenAI TTS billed to your subscription",
>>>>>>> upstream/main
                "env_vars": [],
                "tts_provider": "openai",
                "requires_nous_auth": True,
                "managed_nous_feature": "tts",
                "override_env_vars": ["VOICE_TOOLS_OPENAI_KEY", "OPENAI_API_KEY"],
            },
            {
<<<<<<< HEAD
                "name": "微软 Edge TTS",
                "tag": "免费 - 无需 API 密钥",
=======
                "name": "Microsoft Edge TTS",
                "badge": "★ recommended · free",
                "tag": "Good quality, no API key needed",
>>>>>>> upstream/main
                "env_vars": [],
                "tts_provider": "edge",
            },
            {
                "name": "OpenAI TTS",
<<<<<<< HEAD
                "tag": "高级 - 高质量语音",
=======
                "badge": "paid",
                "tag": "High quality voices",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "VOICE_TOOLS_OPENAI_KEY", "prompt": "OpenAI API 密钥", "url": "https://platform.openai.com/api-keys"},
                ],
                "tts_provider": "openai",
            },
            {
                "name": "ElevenLabs",
<<<<<<< HEAD
                "tag": "高级 - 最自然的声音",
=======
                "badge": "paid",
                "tag": "Most natural voices",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "ELEVENLABS_API_KEY", "prompt": "ElevenLabs API 密钥", "url": "https://elevenlabs.io/app/settings/api-keys"},
                ],
                "tts_provider": "elevenlabs",
            },
            {
                "name": "Mistral (Voxtral TTS)",
<<<<<<< HEAD
                "tag": "多语言，原生 Opus，需要 MISTRAL_API_KEY",
=======
                "badge": "paid",
                "tag": "Multilingual, native Opus",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "MISTRAL_API_KEY", "prompt": "Mistral API 密钥", "url": "https://console.mistral.ai/"},
                ],
                "tts_provider": "mistral",
            },
        ],
    },
    "web": {
        "name": "网络搜索与提取",
        "setup_title": "选择搜索引擎",
        "setup_note": "还包含免费的 DuckDuckGo 搜索技能 — 如果不需要高级搜索引擎可以跳过此步骤。",
        "icon": "🔍",
        "providers": [
            {
<<<<<<< HEAD
                "name": "Nous 订阅",
                "tag": "托管的 Firecrawl，费用计入您的订阅",
=======
                "name": "Nous Subscription",
                "badge": "subscription",
                "tag": "Managed Firecrawl billed to your subscription",
>>>>>>> upstream/main
                "web_backend": "firecrawl",
                "env_vars": [],
                "requires_nous_auth": True,
                "managed_nous_feature": "web",
                "override_env_vars": ["FIRECRAWL_API_KEY", "FIRECRAWL_API_URL"],
            },
            {
<<<<<<< HEAD
                "name": "Firecrawl 云服务",
                "tag": "托管服务 - 搜索、提取和爬取",
=======
                "name": "Firecrawl Cloud",
                "badge": "★ recommended",
                "tag": "Full-featured search, extract, and crawl",
>>>>>>> upstream/main
                "web_backend": "firecrawl",
                "env_vars": [
                    {"key": "FIRECRAWL_API_KEY", "prompt": "Firecrawl API 密钥", "url": "https://firecrawl.dev"},
                ],
            },
            {
                "name": "Exa",
<<<<<<< HEAD
                "tag": "AI 原生搜索和内容获取",
=======
                "badge": "paid",
                "tag": "Neural search with semantic understanding",
>>>>>>> upstream/main
                "web_backend": "exa",
                "env_vars": [
                    {"key": "EXA_API_KEY", "prompt": "Exa API 密钥", "url": "https://exa.ai"},
                ],
            },
            {
                "name": "Parallel",
<<<<<<< HEAD
                "tag": "AI 原生搜索和提取",
=======
                "badge": "paid",
                "tag": "AI-powered search and extract",
>>>>>>> upstream/main
                "web_backend": "parallel",
                "env_vars": [
                    {"key": "PARALLEL_API_KEY", "prompt": "Parallel API 密钥", "url": "https://parallel.ai"},
                ],
            },
            {
                "name": "Tavily",
<<<<<<< HEAD
                "tag": "AI 搜索、提取和爬取",
=======
                "badge": "free tier",
                "tag": "Search, extract, and crawl — 1000 free searches/mo",
>>>>>>> upstream/main
                "web_backend": "tavily",
                "env_vars": [
                    {"key": "TAVILY_API_KEY", "prompt": "Tavily API 密钥", "url": "https://app.tavily.com/home"},
                ],
            },
            {
<<<<<<< HEAD
                "name": "Firecrawl 自托管",
                "tag": "免费 - 运行您自己的实例",
=======
                "name": "Firecrawl Self-Hosted",
                "badge": "free · self-hosted",
                "tag": "Run your own Firecrawl instance (Docker)",
>>>>>>> upstream/main
                "web_backend": "firecrawl",
                "env_vars": [
                    {"key": "FIRECRAWL_API_URL", "prompt": "您的 Firecrawl 实例地址（例如 http://localhost:3002）"},
                ],
            },
        ],
    },
    "image_gen": {
        "name": "图像生成",
        "icon": "🎨",
        "providers": [
            {
<<<<<<< HEAD
                "name": "Nous 订阅",
                "tag": "托管的 FAL 图像生成，费用计入您的订阅",
=======
                "name": "Nous Subscription",
                "badge": "subscription",
                "tag": "Managed FAL image generation billed to your subscription",
>>>>>>> upstream/main
                "env_vars": [],
                "requires_nous_auth": True,
                "managed_nous_feature": "image_gen",
                "override_env_vars": ["FAL_KEY"],
            },
            {
                "name": "FAL.ai",
<<<<<<< HEAD
                "tag": "FLUX 2 Pro，支持自动放大",
=======
                "badge": "paid",
                "tag": "FLUX 2 Pro with auto-upscaling",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "FAL_KEY", "prompt": "FAL API 密钥", "url": "https://fal.ai/dashboard/keys"},
                ],
            },
        ],
    },
    "browser": {
        "name": "浏览器自动化",
        "icon": "🌐",
        "providers": [
            {
<<<<<<< HEAD
                "name": "Nous 订阅 (Browser Use 云服务)",
                "tag": "托管的 Browser Use，费用计入您的订阅",
=======
                "name": "Nous Subscription (Browser Use cloud)",
                "badge": "subscription",
                "tag": "Managed Browser Use billed to your subscription",
>>>>>>> upstream/main
                "env_vars": [],
                "browser_provider": "browser-use",
                "requires_nous_auth": True,
                "managed_nous_feature": "browser",
                "override_env_vars": ["BROWSER_USE_API_KEY"],
                "post_setup": "agent_browser",
            },
            {
<<<<<<< HEAD
                "name": "本地浏览器",
                "tag": "免费的无头 Chromium（无需 API 密钥）",
=======
                "name": "Local Browser",
                "badge": "★ recommended · free",
                "tag": "Headless Chromium, no API key needed",
>>>>>>> upstream/main
                "env_vars": [],
                "browser_provider": "local",
                "post_setup": "agent_browser",
            },
            {
                "name": "Browserbase",
<<<<<<< HEAD
                "tag": "云浏览器，支持隐身和代理",
=======
                "badge": "paid",
                "tag": "Cloud browser with stealth and proxies",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "BROWSERBASE_API_KEY", "prompt": "Browserbase API 密钥", "url": "https://browserbase.com"},
                    {"key": "BROWSERBASE_PROJECT_ID", "prompt": "Browserbase 项目 ID"},
                ],
                "browser_provider": "browserbase",
                "post_setup": "agent_browser",
            },
            {
                "name": "Browser Use",
<<<<<<< HEAD
                "tag": "云浏览器，支持远程执行",
=======
                "badge": "paid",
                "tag": "Cloud browser with remote execution",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "BROWSER_USE_API_KEY", "prompt": "Browser Use API 密钥", "url": "https://browser-use.com"},
                ],
                "browser_provider": "browser-use",
                "post_setup": "agent_browser",
            },
            {
                "name": "Firecrawl",
<<<<<<< HEAD
                "tag": "云浏览器，支持远程执行",
=======
                "badge": "paid",
                "tag": "Cloud browser with remote execution",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "FIRECRAWL_API_KEY", "prompt": "Firecrawl API 密钥", "url": "https://firecrawl.dev"},
                ],
                "browser_provider": "firecrawl",
                "post_setup": "agent_browser",
            },
            {
                "name": "Camofox",
<<<<<<< HEAD
                "tag": "本地反检测浏览器（Firefox/Camoufox）",
=======
                "badge": "free · local",
                "tag": "Anti-detection browser (Firefox/Camoufox)",
>>>>>>> upstream/main
                "env_vars": [
                    {"key": "CAMOFOX_URL", "prompt": "Camofox 服务器地址", "default": "http://localhost:9377",
                     "url": "https://github.com/jo-inc/camofox-browser"},
                ],
                "browser_provider": "camofox",
                "post_setup": "camofox",
            },
        ],
    },
    "homeassistant": {
        "name": "智能家居",
        "icon": "🏠",
        "providers": [
            {
                "name": "Home Assistant",
                "tag": "REST API 集成",
                "env_vars": [
                    {"key": "HASS_TOKEN", "prompt": "Home Assistant 长期访问令牌"},
                    {"key": "HASS_URL", "prompt": "Home Assistant 地址", "default": "http://homeassistant.local:8123"},
                ],
            },
        ],
    },
    "rl": {
        "name": "强化学习训练",
        "icon": "🧪",
        "requires_python": (3, 11),
        "providers": [
            {
                "name": "Tinker / Atropos",
                "tag": "RL 训练平台",
                "env_vars": [
                    {"key": "TINKER_API_KEY", "prompt": "Tinker API 密钥", "url": "https://tinker-console.thinkingmachines.ai/keys"},
                    {"key": "WANDB_API_KEY", "prompt": "WandB API 密钥", "url": "https://wandb.ai/authorize"},
                ],
                "post_setup": "rl_training",
            },
        ],
    },
}

# Simple env-var requirements for toolsets NOT in TOOL_CATEGORIES.
# Used as a fallback for tools like vision/moa that just need an API key.
TOOLSET_ENV_REQUIREMENTS = {
    "vision":     [("OPENROUTER_API_KEY",   "https://openrouter.ai/keys")],
    "moa":        [("OPENROUTER_API_KEY",   "https://openrouter.ai/keys")],
}


# ─── Post-Setup Hooks ─────────────────────────────────────────────────────────

def _run_post_setup(post_setup_key: str):
    """Run post-setup hooks for tools that need extra installation steps."""
    import shutil
    if post_setup_key in ("agent_browser", "browserbase"):
        node_modules = PROJECT_ROOT / "node_modules" / "agent-browser"
        if not node_modules.exists() and shutil.which("npm"):
            _print_info("    正在安装浏览器工具的 Node.js 依赖...")
            import subprocess
            result = subprocess.run(
                ["npm", "install", "--silent"],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                _print_success("    Node.js 依赖安装完成")
            else:
                from hermes_constants import display_hermes_home
                _print_warning(f"    npm 安装失败 - 请手动运行: cd {display_hermes_home()}/hermes-agent && npm install")
        elif not node_modules.exists():
            _print_warning("    未找到 Node.js - 浏览器工具需要: npm install (在 hermes-agent 目录下)")

    elif post_setup_key == "camofox":
        camofox_dir = PROJECT_ROOT / "node_modules" / "@askjo" / "camofox-browser"
        if not camofox_dir.exists() and shutil.which("npm"):
            _print_info("    正在安装 Camofox 浏览器服务器...")
            import subprocess
            result = subprocess.run(
                ["npm", "install", "--silent"],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                _print_success("    Camofox 安装完成")
            else:
                _print_warning("    npm 安装失败 - 请手动运行: npm install")
        if camofox_dir.exists():
<<<<<<< HEAD
            _print_info("    启动 Camofox 服务器:")
            _print_info("      npx @askjo/camoufox-browser")
            _print_info("    首次运行会下载 Camoufox 引擎（约300MB）")
            _print_info("    或使用 Docker: docker run -p 9377:9377 -e CAMOFOX_PORT=9377 jo-inc/camofox-browser")
=======
            _print_info("    Start the Camofox server:")
            _print_info("      npx @askjo/camofox-browser")
            _print_info("    First run downloads the Camoufox engine (~300MB)")
            _print_info("    Or use Docker: docker run -p 9377:9377 -e CAMOFOX_PORT=9377 jo-inc/camofox-browser")
>>>>>>> upstream/main
        elif not shutil.which("npm"):
            _print_warning("    未找到 Node.js。请通过 Docker 安装 Camofox:")
            _print_info("      docker run -p 9377:9377 -e CAMOFOX_PORT=9377 jo-inc/camofox-browser")

    elif post_setup_key == "rl_training":
        try:
            __import__("tinker_atropos")
        except ImportError:
            tinker_dir = PROJECT_ROOT / "tinker-atropos"
            if tinker_dir.exists() and (tinker_dir / "pyproject.toml").exists():
                _print_info("    正在安装 tinker-atropos 子模块...")
                import subprocess
                uv_bin = shutil.which("uv")
                if uv_bin:
                    result = subprocess.run(
                        [uv_bin, "pip", "install", "--python", sys.executable, "-e", str(tinker_dir)],
                        capture_output=True, text=True
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-e", str(tinker_dir)],
                        capture_output=True, text=True
                    )
                if result.returncode == 0:
                    _print_success("    tinker-atropos 安装完成")
                else:
                    _print_warning("    tinker-atropos 安装失败 - 请手动运行:")
                    _print_info('      uv pip install -e "./tinker-atropos"')
            else:
                _print_warning("    未找到 tinker-atropos 子模块 - 请运行:")
                _print_info("      git submodule update --init --recursive")
                _print_info('      uv pip install -e "./tinker-atropos"')


# ─── Platform / Toolset Helpers ───────────────────────────────────────────────

def _get_enabled_platforms() -> List[str]:
    """Return platform keys that are configured (have tokens or are CLI)."""
    enabled = ["cli"]
    if get_env_value("TELEGRAM_BOT_TOKEN"):
        enabled.append("telegram")
    if get_env_value("DISCORD_BOT_TOKEN"):
        enabled.append("discord")
    if get_env_value("SLACK_BOT_TOKEN"):
        enabled.append("slack")
    if get_env_value("WHATSAPP_ENABLED"):
        enabled.append("whatsapp")
    if get_env_value("QQ_APP_ID"):
        enabled.append("qqbot")
    return enabled


def _platform_toolset_summary(config: dict, platforms: Optional[List[str]] = None) -> Dict[str, Set[str]]:
    """Return a summary of enabled toolsets per platform.

    When ``platforms`` is None, this uses ``_get_enabled_platforms`` to
    auto-detect platforms. Tests can pass an explicit list to avoid relying
    on environment variables.
    """
    if platforms is None:
        platforms = _get_enabled_platforms()

    summary: Dict[str, Set[str]] = {}
    for pkey in platforms:
        summary[pkey] = _get_platform_tools(config, pkey)
    return summary


def _parse_enabled_flag(value, default: bool = True) -> bool:
    """Parse bool-like config values used by tool/platform settings."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return default


def _get_platform_tools(
    config: dict,
    platform: str,
    *,
    include_default_mcp_servers: bool = True,
) -> Set[str]:
    """Resolve which individual toolset names are enabled for a platform."""
    from toolsets import resolve_toolset

    platform_toolsets = config.get("platform_toolsets", {})
    toolset_names = platform_toolsets.get(platform)

    if toolset_names is None or not isinstance(toolset_names, list):
        default_ts = PLATFORMS[platform]["default_toolset"]
        toolset_names = [default_ts]

    # YAML may parse bare numeric names (e.g. ``12306:``) as int.
    # Normalise to str so downstream sorted() never mixes types.
    toolset_names = [str(ts) for ts in toolset_names]

    configurable_keys = {ts_key for ts_key, _, _ in CONFIGURABLE_TOOLSETS}

    # If the saved list contains any configurable keys directly, the user
    # has explicitly configured this platform — use direct membership.
    # This avoids the subset-inference bug where composite toolsets like
    # "hermes-cli" (which include all _HERMES_CORE_TOOLS) cause disabled
    # toolsets to re-appear as enabled.
    has_explicit_config = any(ts in configurable_keys for ts in toolset_names)

    if has_explicit_config:
        enabled_toolsets = {ts for ts in toolset_names if ts in configurable_keys}
    else:
        # No explicit config — fall back to resolving composite toolset names
        # (e.g. "hermes-cli") to individual tool names and reverse-mapping.
        all_tool_names = set()
        for ts_name in toolset_names:
            all_tool_names.update(resolve_toolset(ts_name))

        enabled_toolsets = set()
        for ts_key, _, _ in CONFIGURABLE_TOOLSETS:
            ts_tools = set(resolve_toolset(ts_key))
            if ts_tools and ts_tools.issubset(all_tool_names):
                enabled_toolsets.add(ts_key)

    # Plugin toolsets: enabled by default unless explicitly disabled.
    # A plugin toolset is "known" for a platform once `hermes tools`
    # has been saved for that platform (tracked via known_plugin_toolsets).
    # Unknown plugins default to enabled; known-but-absent = disabled.
    plugin_ts_keys = _get_plugin_toolset_keys()
    if plugin_ts_keys:
        known_map = config.get("known_plugin_toolsets", {})
        known_for_platform = set(known_map.get(platform, []))
        for pts in plugin_ts_keys:
            if pts in toolset_names:
                # Explicitly listed in config — enabled
                enabled_toolsets.add(pts)
            elif pts not in known_for_platform:
                # New plugin not yet seen by hermes tools — default enabled
                enabled_toolsets.add(pts)
            # else: known but not in config = user disabled it

    # Preserve any explicit non-configurable toolset entries (for example,
    # custom toolsets or MCP server names saved in platform_toolsets).
    platform_default_keys = {p["default_toolset"] for p in PLATFORMS.values()}
    explicit_passthrough = {
        ts
        for ts in toolset_names
        if ts not in configurable_keys
        and ts not in plugin_ts_keys
        and ts not in platform_default_keys
    }

    # MCP servers are expected to be available on all platforms by default.
    # If the platform explicitly lists one or more MCP server names, treat that
    # as an allowlist. Otherwise include every globally enabled MCP server.
    # Special sentinel: "no_mcp" in the toolset list disables all MCP servers.
    mcp_servers = config.get("mcp_servers") or {}
    enabled_mcp_servers = {
        str(name)
        for name, server_cfg in mcp_servers.items()
        if isinstance(server_cfg, dict)
        and _parse_enabled_flag(server_cfg.get("enabled", True), default=True)
    }
    # Allow "no_mcp" sentinel to opt out of all MCP servers for this platform
    if "no_mcp" in toolset_names:
        explicit_mcp_servers = set()
        enabled_toolsets.update(explicit_passthrough - enabled_mcp_servers - {"no_mcp"})
    else:
        explicit_mcp_servers = explicit_passthrough & enabled_mcp_servers
        enabled_toolsets.update(explicit_passthrough - enabled_mcp_servers)
    if include_default_mcp_servers:
        if explicit_mcp_servers or "no_mcp" in toolset_names:
            enabled_toolsets.update(explicit_mcp_servers)
        else:
            enabled_toolsets.update(enabled_mcp_servers)
    else:
        enabled_toolsets.update(explicit_mcp_servers)

    return enabled_toolsets


def _save_platform_tools(config: dict, platform: str, enabled_toolset_keys: Set[str]):
    """Save the selected toolset keys for a platform to config.

    Preserves any non-configurable toolset entries (like MCP server names)
    that were already in the config for this platform.
    """
    config.setdefault("platform_toolsets", {})

    # Get the set of all configurable toolset keys (built-in + plugin)
    configurable_keys = {ts_key for ts_key, _, _ in CONFIGURABLE_TOOLSETS}
    plugin_keys = _get_plugin_toolset_keys()
    configurable_keys |= plugin_keys

    # Also exclude platform default toolsets (hermes-cli, hermes-telegram, etc.)
    # These are "super" toolsets that resolve to ALL tools, so preserving them
    # would silently override the user's unchecked selections on the next read.
    platform_default_keys = {p["default_toolset"] for p in PLATFORMS.values()}

    # Get existing toolsets for this platform
    existing_toolsets = config.get("platform_toolsets", {}).get(platform, [])
    if not isinstance(existing_toolsets, list):
        existing_toolsets = []

    # Preserve any entries that are NOT configurable toolsets and NOT platform
    # defaults (i.e. only MCP server names should be preserved)
    preserved_entries = {
        entry for entry in existing_toolsets
        if entry not in configurable_keys and entry not in platform_default_keys
    }

    # Merge preserved entries with new enabled toolsets
    config["platform_toolsets"][platform] = sorted(enabled_toolset_keys | preserved_entries)

    # Track which plugin toolsets are "known" for this platform so we can
    # distinguish "new plugin, default enabled" from "user disabled it".
    if plugin_keys:
        config.setdefault("known_plugin_toolsets", {})
        config["known_plugin_toolsets"][platform] = sorted(plugin_keys)

    save_config(config)


def _toolset_has_keys(ts_key: str, config: dict = None) -> bool:
    """Check if a toolset's required API keys are configured."""
    if config is None:
        config = load_config()

    if ts_key == "vision":
        try:
            from agent.auxiliary_client import resolve_vision_provider_client

            _provider, client, _model = resolve_vision_provider_client()
            return client is not None
        except Exception:
            return False

    if ts_key in {"web", "image_gen", "tts", "browser"}:
        features = get_nous_subscription_features(config)
        feature = features.features.get(ts_key)
        if feature and (feature.available or feature.managed_by_nous):
            return True

    # Check TOOL_CATEGORIES first (provider-aware)
    cat = TOOL_CATEGORIES.get(ts_key)
    if cat:
        for provider in _visible_providers(cat, config):
            env_vars = provider.get("env_vars", [])
            if not env_vars:
                return True  # No-key provider (e.g. Local Browser, Edge TTS)
            if all(get_env_value(e["key"]) for e in env_vars):
                return True
        return False

    # Fallback to simple requirements
    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return True
    return all(get_env_value(var) for var, _ in requirements)


# ─── Menu Helpers ─────────────────────────────────────────────────────────────

def _prompt_choice(question: str, choices: list, default: int = 0) -> int:
    """Single-select menu (arrow keys). Delegates to curses_radiolist."""
    from hermes_cli.curses_ui import curses_radiolist
    return curses_radiolist(question, choices, selected=default, cancel_returns=default)


# ─── Token Estimation ────────────────────────────────────────────────────────

# Module-level cache so discovery + tokenization runs at most once per process.
_tool_token_cache: Optional[Dict[str, int]] = None


def _estimate_tool_tokens() -> Dict[str, int]:
    """Return estimated token counts per individual tool name.

    Uses tiktoken (cl100k_base) to count tokens in the JSON-serialised
    OpenAI-format tool schema.  Triggers tool discovery on first call,
    then caches the result for the rest of the process.

    Returns an empty dict when tiktoken or the registry is unavailable.
    """
    global _tool_token_cache
    if _tool_token_cache is not None:
        return _tool_token_cache

    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        logger.debug("tiktoken unavailable; skipping tool token estimation")
        _tool_token_cache = {}
        return _tool_token_cache

    try:
        # Trigger full tool discovery (imports all tool modules).
        import model_tools  # noqa: F401
        from tools.registry import registry
    except Exception:
        logger.debug("Tool registry unavailable; skipping token estimation")
        _tool_token_cache = {}
        return _tool_token_cache

    counts: Dict[str, int] = {}
    for name in registry.get_all_tool_names():
        schema = registry.get_schema(name)
        if schema:
            # Mirror what gets sent to the API:
            # {"type": "function", "function": <schema>}
            text = _json.dumps({"type": "function", "function": schema})
            counts[name] = len(enc.encode(text))
    _tool_token_cache = counts
    return _tool_token_cache


def _prompt_toolset_checklist(platform_label: str, enabled: Set[str]) -> Set[str]:
    """Multi-select checklist of toolsets. Returns set of selected toolset keys."""
    from hermes_cli.curses_ui import curses_checklist
    from toolsets import resolve_toolset

    # Pre-compute per-tool token counts (cached after first call).
    tool_tokens = _estimate_tool_tokens()

    effective = _get_effective_configurable_toolsets()

    labels = []
    for ts_key, ts_label, ts_desc in effective:
        suffix = ""
        if not _toolset_has_keys(ts_key) and (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
            suffix = "  [未配置 API 密钥]"
        labels.append(f"{ts_label}  ({ts_desc}){suffix}")

    pre_selected = {
        i for i, (ts_key, _, _) in enumerate(effective)
        if ts_key in enabled
    }

    # Build a live status function that shows deduplicated total token cost.
    status_fn = None
    if tool_tokens:
        ts_keys = [ts_key for ts_key, _, _ in effective]

        def status_fn(chosen: set) -> str:
            # Collect unique tool names across all selected toolsets
            all_tools: set = set()
            for idx in chosen:
                all_tools.update(resolve_toolset(ts_keys[idx]))
            total = sum(tool_tokens.get(name, 0) for name in all_tools)
            if total >= 1000:
                return f"预估工具上下文: ~{total / 1000:.1f}k tokens"
        return f"预估工具上下文: ~{total} tokens"

    chosen = curses_checklist(
        f"{platform_label} 的工具",
        labels,
        pre_selected,
        cancel_returns=pre_selected,
        status_fn=status_fn,
    )
    return {effective[i][0] for i in chosen}


# ─── Provider-Aware Configuration ────────────────────────────────────────────

def _configure_toolset(ts_key: str, config: dict):
    """Configure a toolset - provider selection + API keys.
    
    Uses TOOL_CATEGORIES for provider-aware config, falls back to simple
    env var prompts for toolsets not in TOOL_CATEGORIES.
    """
    cat = TOOL_CATEGORIES.get(ts_key)

    if cat:
        _configure_tool_category(ts_key, cat, config)
    else:
        # Simple fallback for vision, moa, etc.
        _configure_simple_requirements(ts_key)


def _visible_providers(cat: dict, config: dict) -> list[dict]:
    """Return provider entries visible for the current auth/config state."""
    features = get_nous_subscription_features(config)
    visible = []
    for provider in cat.get("providers", []):
        if provider.get("managed_nous_feature") and not managed_nous_tools_enabled():
            continue
        if provider.get("requires_nous_auth") and not features.nous_auth_present:
            continue
        visible.append(provider)
    return visible


def _toolset_needs_configuration_prompt(ts_key: str, config: dict) -> bool:
    """Return True when enabling this toolset should open provider setup."""
    cat = TOOL_CATEGORIES.get(ts_key)
    if not cat:
        return not _toolset_has_keys(ts_key, config)

    if ts_key == "tts":
        tts_cfg = config.get("tts", {})
        return not isinstance(tts_cfg, dict) or "provider" not in tts_cfg
    if ts_key == "web":
        web_cfg = config.get("web", {})
        return not isinstance(web_cfg, dict) or "backend" not in web_cfg
    if ts_key == "browser":
        browser_cfg = config.get("browser", {})
        return not isinstance(browser_cfg, dict) or "cloud_provider" not in browser_cfg
    if ts_key == "image_gen":
        return not get_env_value("FAL_KEY")

    return not _toolset_has_keys(ts_key, config)


def _configure_tool_category(ts_key: str, cat: dict, config: dict):
    """Configure a tool category with provider selection."""
    icon = cat.get("icon", "")
    name = cat["name"]
    providers = _visible_providers(cat, config)

    # Check Python version requirement
    if cat.get("requires_python"):
        req = cat["requires_python"]
        if sys.version_info < req:
            print()
            _print_error(f"  {name} 需要 Python {req[0]}.{req[1]}+（当前版本: {sys.version_info.major}.{sys.version_info.minor})")
            _print_info("  请升级 Python 并重新安装以启用此工具。")
            return

    if len(providers) == 1:
        # Single provider - configure directly
        provider = providers[0]
        print()
        print(color(f"  --- {icon} {name} ({provider['name']}) ---", Colors.CYAN))
        if provider.get("tag"):
            _print_info(f"  {provider['tag']}")
        # For single-provider tools, show a note if available
        if cat.get("setup_note"):
            _print_info(f"  {cat['setup_note']}")
        _configure_provider(provider, config)
    else:
        # Multiple providers - let user choose
        print()
        # Use custom title if provided (e.g. "选择搜索引擎")
        title = cat.get("setup_title", "选择提供商")
        print(color(f"  --- {icon} {name} - {title} ---", Colors.CYAN))
        if cat.get("setup_note"):
            _print_info(f"  {cat['setup_note']}")
        print()

        # Plain text labels only (no ANSI codes in menu items)
        provider_choices = []
        for p in providers:
            badge = f" [{p['badge']}]" if p.get("badge") else ""
            tag = f" — {p['tag']}" if p.get("tag") else ""
            configured = ""
            env_vars = p.get("env_vars", [])
            if not env_vars or all(get_env_value(v["key"]) for v in env_vars):
                if _is_provider_active(p, config):
                    configured = " [已激活]"
                elif not env_vars:
                    configured = ""
                else:
<<<<<<< HEAD
                    configured = " [已配置]"
            provider_choices.append(f"{p['name']}{tag}{configured}")
=======
                    configured = " [configured]"
            provider_choices.append(f"{p['name']}{badge}{tag}{configured}")
>>>>>>> upstream/main

        # Add skip option
        provider_choices.append("跳过 — 保持默认 / 稍后配置")

        # Detect current provider as default
        default_idx = _detect_active_provider_index(providers, config)

        provider_idx = _prompt_choice(f"  {title}:", provider_choices, default_idx)

        # Skip selected
        if provider_idx >= len(providers):
            _print_info(f"  已跳过 {name}")
            return

        _configure_provider(providers[provider_idx], config)


def _is_provider_active(provider: dict, config: dict) -> bool:
    """Check if a provider entry matches the currently active config."""
    managed_feature = provider.get("managed_nous_feature")
    if managed_feature:
        features = get_nous_subscription_features(config)
        feature = features.features.get(managed_feature)
        if feature is None:
            return False
        if managed_feature == "image_gen":
            return feature.managed_by_nous
        if provider.get("tts_provider"):
            return (
                feature.managed_by_nous
                and config.get("tts", {}).get("provider") == provider["tts_provider"]
            )
        if "browser_provider" in provider:
            current = config.get("browser", {}).get("cloud_provider")
            return feature.managed_by_nous and provider["browser_provider"] == current
        if provider.get("web_backend"):
            current = config.get("web", {}).get("backend")
            return feature.managed_by_nous and current == provider["web_backend"]
        return feature.managed_by_nous

    if provider.get("tts_provider"):
        return config.get("tts", {}).get("provider") == provider["tts_provider"]
    if "browser_provider" in provider:
        current = config.get("browser", {}).get("cloud_provider")
        return provider["browser_provider"] == current
    if provider.get("web_backend"):
        current = config.get("web", {}).get("backend")
        return current == provider["web_backend"]
    return False


def _detect_active_provider_index(providers: list, config: dict) -> int:
    """Return the index of the currently active provider, or 0."""
    for i, p in enumerate(providers):
        if _is_provider_active(p, config):
            return i
        # Fallback: env vars present → likely configured
        env_vars = p.get("env_vars", [])
        if env_vars and all(get_env_value(v["key"]) for v in env_vars):
            return i
    return 0


def _configure_provider(provider: dict, config: dict):
    """Configure a single provider - prompt for API keys and set config."""
    env_vars = provider.get("env_vars", [])
    managed_feature = provider.get("managed_nous_feature")

    if provider.get("requires_nous_auth"):
        features = get_nous_subscription_features(config)
        if not features.nous_auth_present:
            _print_warning("  Nous 订阅仅在登录 Nous Portal 后可用。")
            return

    # Set TTS provider in config if applicable
    if provider.get("tts_provider"):
        config.setdefault("tts", {})["provider"] = provider["tts_provider"]

    # Set browser cloud provider in config if applicable
    if "browser_provider" in provider:
        bp = provider["browser_provider"]
        if bp == "local":
            config.setdefault("browser", {})["cloud_provider"] = "local"
            _print_success("  浏览器已设置为本地模式")
        elif bp:
            config.setdefault("browser", {})["cloud_provider"] = bp
            _print_success(f"  浏览器云提供商设置为: {bp}")

    # Set web search backend in config if applicable
    if provider.get("web_backend"):
        config.setdefault("web", {})["backend"] = provider["web_backend"]
        _print_success(f"  网络后端设置为: {provider['web_backend']}")

    if not env_vars:
        if provider.get("post_setup"):
            _run_post_setup(provider["post_setup"])
        _print_success(f"  {provider['name']} - 无需配置！")
        if managed_feature:
            _print_info("  此工具的请求将计入您的 Nous 订阅。")
            override_envs = provider.get("override_env_vars", [])
            if any(get_env_value(env_var) for env_var in override_envs):
                _print_warning(
                    "  直接配置的凭据仍然存在，可能会优先生效，直到您从 ~/.hermes/.env 中移除它们。"
                )
        return

    # Prompt for each required env var
    all_configured = True
    for var in env_vars:
        existing = get_env_value(var["key"])
        if existing:
            _print_success(f"  {var['key']}: 已配置")
            # Don't ask to update - this is a new enable flow.
            # Reconfigure is handled separately.
        else:
            url = var.get("url", "")
            if url:
                _print_info(f"  获取地址: {url}")

            default_val = var.get("default", "")
            if default_val:
                value = _prompt(f"    {var.get('prompt', var['key'])}", default_val)
            else:
                value = _prompt(f"    {var.get('prompt', var['key'])}", password=True)

            if value:
                save_env_value(var["key"], value)
                _print_success("    已保存")
            else:
                _print_warning("    已跳过")
                all_configured = False

    # Run post-setup hooks if needed
    if provider.get("post_setup") and all_configured:
        _run_post_setup(provider["post_setup"])

    if all_configured:
        _print_success(f"  {provider['name']} 配置完成！")


def _configure_simple_requirements(ts_key: str):
    """Simple fallback for toolsets that just need env vars (no provider selection)."""
    if ts_key == "vision":
        if _toolset_has_keys("vision"):
            return
        print()
        print(color("  视觉/图像分析需要多模态后端:", Colors.YELLOW))
        choices = [
            "OpenAI — 使用 Gemini",
            "OpenAI 兼容端点 — 基础 URL、API 密钥和视觉模型",
            "跳过",
        ]
        idx = _prompt_choice("  配置视觉后端", choices, 2)
        if idx == 0:
            _print_info("  获取密钥地址: https://openrouter.ai/keys")
            value = _prompt("    OPENROUTER_API_KEY", password=True)
            if value and value.strip():
                save_env_value("OPENROUTER_API_KEY", value.strip())
                _print_success("    已保存")
            else:
                _print_warning("    已跳过")
        elif idx == 1:
            base_url = _prompt("    OPENAI_BASE_URL（留空使用 OpenAI）").strip() or "https://api.openai.com/v1"
            key_label = "    OPENAI_API_KEY" if "api.openai.com" in base_url.lower() else "    API 密钥"
            api_key = _prompt(key_label, password=True)
            if api_key and api_key.strip():
                save_env_value("OPENAI_API_KEY", api_key.strip())
                # Save vision base URL to config (not .env — only secrets go there)
                from hermes_cli.config import load_config, save_config
                _cfg = load_config()
                _aux = _cfg.setdefault("auxiliary", {}).setdefault("vision", {})
                _aux["base_url"] = base_url
                save_config(_cfg)
                if "api.openai.com" in base_url.lower():
                    save_env_value("AUXILIARY_VISION_MODEL", "gpt-4o-mini")
                _print_success("    已保存")
            else:
                _print_warning("    已跳过")
        return

    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return

    missing = [(var, url) for var, url in requirements if not get_env_value(var)]
    if not missing:
        return

    ts_label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts_key), ts_key)
    print()
    print(color(f"  {ts_label} 需要配置:", Colors.YELLOW))

    for var, url in missing:
        if url:
            _print_info(f"  获取密钥地址: {url}")
        value = _prompt(f"    {var}", password=True)
        if value and value.strip():
            save_env_value(var, value.strip())
            _print_success("    已保存")
        else:
            _print_warning("    已跳过")


def _reconfigure_tool(config: dict):
    """Let user reconfigure an existing tool's provider or API key."""
    # Build list of configurable tools that are currently set up
    configurable = []
    for ts_key, ts_label, _ in _get_effective_configurable_toolsets():
        cat = TOOL_CATEGORIES.get(ts_key)
        reqs = TOOLSET_ENV_REQUIREMENTS.get(ts_key)
        if cat or reqs:
            if _toolset_has_keys(ts_key, config):
                configurable.append((ts_key, ts_label))

    if not configurable:
        _print_info("没有可重新配置的工具。")
        return

    choices = [label for _, label in configurable]
    choices.append("取消")

    idx = _prompt_choice("  您想重新配置哪个工具？", choices, len(choices) - 1)

    if idx >= len(configurable):
        return  # Cancel

    ts_key, ts_label = configurable[idx]
    cat = TOOL_CATEGORIES.get(ts_key)

    if cat:
        _configure_tool_category_for_reconfig(ts_key, cat, config)
    else:
        _reconfigure_simple_requirements(ts_key)

    save_config(config)


def _configure_tool_category_for_reconfig(ts_key: str, cat: dict, config: dict):
    """Reconfigure a tool category - provider selection + API key update."""
    icon = cat.get("icon", "")
    name = cat["name"]
    providers = _visible_providers(cat, config)

    if len(providers) == 1:
        provider = providers[0]
        print()
        print(color(f"  --- {icon} {name} ({provider['name']}) ---", Colors.CYAN))
        _reconfigure_provider(provider, config)
    else:
        print()
        print(color(f"  --- {icon} {name} - 选择提供商 ---", Colors.CYAN))
        print()

        provider_choices = []
        for p in providers:
            badge = f" [{p['badge']}]" if p.get("badge") else ""
            tag = f" — {p['tag']}" if p.get("tag") else ""
            configured = ""
            env_vars = p.get("env_vars", [])
            if not env_vars or all(get_env_value(v["key"]) for v in env_vars):
                if _is_provider_active(p, config):
                    configured = " [active]"
                elif not env_vars:
                    configured = ""
                else:
                    configured = " [configured]"
            provider_choices.append(f"{p['name']}{badge}{tag}{configured}")

        default_idx = _detect_active_provider_index(providers, config)

        provider_idx = _prompt_choice("  Select provider:", provider_choices, default_idx)
        _reconfigure_provider(providers[provider_idx], config)


def _reconfigure_provider(provider: dict, config: dict):
    """Reconfigure a provider - update API keys."""
    env_vars = provider.get("env_vars", [])
    managed_feature = provider.get("managed_nous_feature")

    if provider.get("requires_nous_auth"):
        features = get_nous_subscription_features(config)
        if not features.nous_auth_present:
            _print_warning("  Nous 订阅仅在登录 Nous Portal 后可用。")
            return

    if provider.get("tts_provider"):
        config.setdefault("tts", {})["provider"] = provider["tts_provider"]
        _print_success(f"  TTS 提供商设置为: {provider['tts_provider']}")

    if "browser_provider" in provider:
        bp = provider["browser_provider"]
        if bp == "local":
            config.setdefault("browser", {})["cloud_provider"] = "local"
            _print_success("  浏览器已设置为本地模式")
        elif bp:
            config.setdefault("browser", {})["cloud_provider"] = bp
            _print_success(f"  浏览器云提供商设置为: {bp}")

    # Set web search backend in config if applicable
    if provider.get("web_backend"):
        config.setdefault("web", {})["backend"] = provider["web_backend"]
        _print_success(f"  网络后端设置为: {provider['web_backend']}")

    if not env_vars:
        if provider.get("post_setup"):
            _run_post_setup(provider["post_setup"])
        _print_success(f"  {provider['name']} - 无需配置！")
        if managed_feature:
            _print_info("  此工具的请求将计入您的 Nous 订阅。")
            override_envs = provider.get("override_env_vars", [])
            if any(get_env_value(env_var) for env_var in override_envs):
                _print_warning(
                    "  直接配置的凭据仍然存在，可能会优先生效，直到您从 ~/.hermes/.env 中移除它们。"
                )
        return

    for var in env_vars:
        existing = get_env_value(var["key"])
        if existing:
            _print_info(f"  {var['key']}: 已配置（{existing[:8]}...）")
        url = var.get("url", "")
        if url:
            _print_info(f"  获取地址: {url}")
        default_val = var.get("default", "")
        value = _prompt(f"    {var.get('prompt', var['key'])} (回车保持当前值)", password=not default_val)
        if value and value.strip():
            save_env_value(var["key"], value.strip())
            _print_success("    已更新")
        else:
            _print_info("    保持当前值")


def _reconfigure_simple_requirements(ts_key: str):
    """Reconfigure simple env var requirements."""
    requirements = TOOLSET_ENV_REQUIREMENTS.get(ts_key, [])
    if not requirements:
        return

    ts_label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts_key), ts_key)
    print()
    print(color(f"  {ts_label}:", Colors.CYAN))

    for var, url in requirements:
        existing = get_env_value(var)
        if existing:
            _print_info(f"  {var}: 已配置（{existing[:8]}...）")
        if url:
            _print_info(f"  获取密钥地址: {url}")
        value = _prompt(f"    {var} (回车保持当前值)", password=True)
        if value and value.strip():
            save_env_value(var, value.strip())
            _print_success("    已更新")
        else:
            _print_info("    保持当前值")


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def tools_command(args=None, first_install: bool = False, config: dict = None):
    """Entry point for `hermes tools` and `hermes setup tools`.

    Args:
        first_install: When True (set by the setup wizard on fresh installs),
            skip the platform menu, go straight to the CLI checklist, and
            prompt for API keys on all enabled tools that need them.
        config: Optional config dict to use.  When called from the setup
            wizard, the wizard passes its own dict so that platform_toolsets
            are written into it and survive the wizard's final save_config().
    """
    if config is None:
        config = load_config()
    enabled_platforms = _get_enabled_platforms()

    print()

    # Non-interactive summary mode for CLI usage
    if getattr(args, "summary", False):
        total = len(_get_effective_configurable_toolsets())
        print(color("⚕ 工具概览", Colors.CYAN, Colors.BOLD))
        print()
        summary = _platform_toolset_summary(config, enabled_platforms)
        for pkey in enabled_platforms:
            pinfo = PLATFORMS[pkey]
            enabled = summary.get(pkey, set())
            count = len(enabled)
            print(color(f"  {pinfo['label']}", Colors.BOLD) + color(f"  ({count}/{total})", Colors.DIM))
            if enabled:
                for ts_key in sorted(enabled):
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts_key), ts_key)
                    print(color(f"    ✓ {label}", Colors.GREEN))
            else:
                print(color("    (none enabled)", Colors.DIM))
        print()
        return
    print(color("⚕ Hermes 工具配置", Colors.CYAN, Colors.BOLD))
    print(color("  按平台启用或禁用工具。", Colors.DIM))
    print(color("  需要 API 密钥的工具将在启用时进行配置。", Colors.DIM))
    print(color("  使用指南: https://hermes-agent.nousresearch.com/docs/user-guide/features/tools", Colors.DIM))
    print()

    # ── First-time install: linear flow, no platform menu ──
    if first_install:
        for pkey in enabled_platforms:
            pinfo = PLATFORMS[pkey]
            current_enabled = _get_platform_tools(config, pkey, include_default_mcp_servers=False)

            # Uncheck toolsets that should be off by default
            checklist_preselected = current_enabled - _DEFAULT_OFF_TOOLSETS

            # Show checklist
            new_enabled = _prompt_toolset_checklist(pinfo["label"], checklist_preselected)

            added = new_enabled - current_enabled
            removed = current_enabled - new_enabled
            if added:
                for ts in sorted(added):
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                    print(color(f"  + {label}", Colors.GREEN))
            if removed:
                for ts in sorted(removed):
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                    print(color(f"  - {label}", Colors.RED))

            auto_configured = apply_nous_managed_defaults(
                config,
                enabled_toolsets=new_enabled,
            )
            if managed_nous_tools_enabled():
                for ts_key in sorted(auto_configured):
                    label = next((l for k, l, _ in CONFIGURABLE_TOOLSETS if k == ts_key), ts_key)
                    print(color(f"  ✓ {label}: 使用您的 Nous 订阅默认设置", Colors.GREEN))

            # Walk through ALL selected tools that have provider options or
            # need API keys.  This ensures browser (Local vs Browserbase),
            # TTS (Edge vs OpenAI vs ElevenLabs), etc. are shown even when
            # a free provider exists.
            to_configure = [
                ts_key for ts_key in sorted(new_enabled)
                if (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key))
                and ts_key not in auto_configured
            ]

            if to_configure:
                print()
                print(color(f"  正在配置 {len(to_configure)} 个工具:", Colors.YELLOW))
                for ts_key in to_configure:
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts_key), ts_key)
                    print(color(f"    • {label}", Colors.DIM))
                print(color("  您可以跳过暂时不需要的工具。", Colors.DIM))
                print()
                for ts_key in to_configure:
                    _configure_toolset(ts_key, config)

            _save_platform_tools(config, pkey, new_enabled)
            save_config(config)
            print(color(f"  ✓ Saved {pinfo['label']} tool configuration", Colors.GREEN))
            print()

        return

    # ── Returning user: platform menu loop ──
    # Build platform choices
    platform_choices = []
    platform_keys = []
    for pkey in enabled_platforms:
        pinfo = PLATFORMS[pkey]
        current = _get_platform_tools(config, pkey, include_default_mcp_servers=False)
        count = len(current)
        total = len(_get_effective_configurable_toolsets())
        platform_choices.append(f"配置 {pinfo['label']}  ({count}/{total} 已启用)")
        platform_keys.append(pkey)

    if len(platform_keys) > 1:
        platform_choices.append("配置所有平台（全局）")
    platform_choices.append("重新配置现有工具的提供商或 API 密钥")

    # Show MCP option if any MCP servers are configured
    _has_mcp = bool(config.get("mcp_servers"))
    if _has_mcp:
        platform_choices.append("Configure MCP server tools")

    platform_choices.append("Done")

    # Index offsets for the extra options after per-platform entries
    _global_idx = len(platform_keys) if len(platform_keys) > 1 else -1
    _reconfig_idx = len(platform_keys) + (1 if len(platform_keys) > 1 else 0)
    _mcp_idx = (_reconfig_idx + 1) if _has_mcp else -1
    _done_idx = _reconfig_idx + (2 if _has_mcp else 1)

    while True:
        idx = _prompt_choice("选择一个选项:", platform_choices, default=0)

        # "Done" selected
        if idx == _done_idx:
            break

        # "Reconfigure" selected
        if idx == _reconfig_idx:
            _reconfigure_tool(config)
            print()
            continue

        # "Configure MCP tools" selected
        if idx == _mcp_idx:
            _configure_mcp_tools_interactive(config)
            print()
            continue

        # "Configure all platforms (global)" selected
        if idx == _global_idx:
            # Use the union of all platforms' current tools as the starting state
            all_current = set()
            for pk in platform_keys:
                all_current |= _get_platform_tools(config, pk, include_default_mcp_servers=False)
            new_enabled = _prompt_toolset_checklist("All platforms", all_current)
            if new_enabled != all_current:
                for pk in platform_keys:
                    prev = _get_platform_tools(config, pk, include_default_mcp_servers=False)
                    added = new_enabled - prev
                    removed = prev - new_enabled
                    pinfo_inner = PLATFORMS[pk]
                    if added or removed:
                        print(color(f"  {pinfo_inner['label']}:", Colors.DIM))
                        for ts in sorted(added):
                            label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                            print(color(f"    + {label}", Colors.GREEN))
                        for ts in sorted(removed):
                            label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                            print(color(f"    - {label}", Colors.RED))
                    # Configure API keys for newly enabled tools
                    for ts_key in sorted(added):
                        if (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
                            if _toolset_needs_configuration_prompt(ts_key, config):
                                _configure_toolset(ts_key, config)
                    _save_platform_tools(config, pk, new_enabled)
                save_config(config)
                print(color("  ✓ Saved configuration for all platforms", Colors.GREEN))
                # Update choice labels
                for ci, pk in enumerate(platform_keys):
                    new_count = len(_get_platform_tools(config, pk, include_default_mcp_servers=False))
                    total = len(_get_effective_configurable_toolsets())
                    platform_choices[ci] = f"Configure {PLATFORMS[pk]['label']}  ({new_count}/{total} enabled)"
            else:
                print(color("  No changes", Colors.DIM))
            print()
            continue

        pkey = platform_keys[idx]
        pinfo = PLATFORMS[pkey]

        # Get current enabled toolsets for this platform
        current_enabled = _get_platform_tools(config, pkey, include_default_mcp_servers=False)

        # Show checklist
        new_enabled = _prompt_toolset_checklist(pinfo["label"], current_enabled)

        if new_enabled != current_enabled:
            added = new_enabled - current_enabled
            removed = current_enabled - new_enabled

            if added:
                for ts in sorted(added):
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                    print(color(f"  + {label}", Colors.GREEN))
            if removed:
                for ts in sorted(removed):
                    label = next((l for k, l, _ in _get_effective_configurable_toolsets() if k == ts), ts)
                    print(color(f"  - {label}", Colors.RED))

            # Configure newly enabled toolsets that need API keys
            for ts_key in sorted(added):
                if (TOOL_CATEGORIES.get(ts_key) or TOOLSET_ENV_REQUIREMENTS.get(ts_key)):
                    if _toolset_needs_configuration_prompt(ts_key, config):
                        _configure_toolset(ts_key, config)

            _save_platform_tools(config, pkey, new_enabled)
            save_config(config)
            print(color(f"  ✓ 已保存 {pinfo['label']} 配置", Colors.GREEN))
        else:
            print(color(f"  {pinfo['label']} 无更改", Colors.DIM))

        print()

        # Update the choice label with new count
        new_count = len(_get_platform_tools(config, pkey, include_default_mcp_servers=False))
        total = len(_get_effective_configurable_toolsets())
        platform_choices[idx] = f"配置 {pinfo['label']}  ({new_count}/{total} 已启用)"

    print()
    from hermes_constants import display_hermes_home
    print(color(f"  工具配置已保存到 {display_hermes_home()}/config.yaml", Colors.DIM))
    print(color("  更改将在下次启动 'hermes' 或网关重启后生效。", Colors.DIM))
    print()


# ─── MCP Tools Interactive Configuration ─────────────────────────────────────


def _configure_mcp_tools_interactive(config: dict):
    """Probe MCP servers for available tools and let user toggle them on/off.

    Connects to each configured MCP server, discovers tools, then shows
    a per-server curses checklist.  Writes changes back as ``tools.exclude``
    entries in config.yaml.
    """
    from hermes_cli.curses_ui import curses_checklist

    mcp_servers = config.get("mcp_servers") or {}
    if not mcp_servers:
        _print_info("No MCP servers configured.")
        return

    # Count enabled servers
    enabled_names = [
        k for k, v in mcp_servers.items()
        if v.get("enabled", True) not in (False, "false", "0", "no", "off")
    ]
    if not enabled_names:
        _print_info("All MCP servers are disabled.")
        return

    print()
    print(color("  正在从 MCP 服务器发现工具...", Colors.YELLOW))
    print(color(f"  正在连接到 {len(enabled_names)} 个服务器: {', '.join(enabled_names)}", Colors.DIM))

    try:
        from tools.mcp_tool import probe_mcp_server_tools
        server_tools = probe_mcp_server_tools()
    except Exception as exc:
        _print_error(f"探测 MCP 服务器失败: {exc}")
        return

    if not server_tools:
        _print_warning("未能从任何 MCP 服务器发现工具。")
        _print_info("请检查服务器命令/地址是否正确以及依赖是否已安装。")
        return

    # Report discovery results
    failed = [n for n in enabled_names if n not in server_tools]
    if failed:
        for name in failed:
            _print_warning(f"  无法连接到 '{name}'")

    total_tools = sum(len(tools) for tools in server_tools.values())
    print(color(f"  在 {len(server_tools)} 个服务器上发现 {total_tools} 个工具", Colors.GREEN))
    print()

    any_changes = False

    for server_name, tools in server_tools.items():
        if not tools:
            _print_info(f"  {server_name}: 未发现任何工具")
            continue

        srv_cfg = mcp_servers.get(server_name, {})
        tools_cfg = srv_cfg.get("tools") or {}
        include_list = tools_cfg.get("include") or []
        exclude_list = tools_cfg.get("exclude") or []

        # Build checklist labels
        labels = []
        for tool_name, description in tools:
            desc_short = description[:70] + "..." if len(description) > 70 else description
            if desc_short:
                labels.append(f"{tool_name}  ({desc_short})")
            else:
                labels.append(tool_name)

        # Determine which tools are currently enabled
        pre_selected: Set[int] = set()
        tool_names = [t[0] for t in tools]
        for i, tool_name in enumerate(tool_names):
            if include_list:
                # Include mode: only included tools are selected
                if tool_name in include_list:
                    pre_selected.add(i)
            elif exclude_list:
                # Exclude mode: everything except excluded
                if tool_name not in exclude_list:
                    pre_selected.add(i)
            else:
                # No filter: all enabled
                pre_selected.add(i)

        chosen = curses_checklist(
            f"MCP Server: {server_name}  ({len(tools)} tools)",
            labels,
            pre_selected,
            cancel_returns=pre_selected,
        )

        if chosen == pre_selected:
            _print_info(f"  {server_name}: no changes")
            continue

        # Compute new exclude list based on unchecked tools
        new_exclude = [tool_names[i] for i in range(len(tool_names)) if i not in chosen]

        # Update config
        srv_cfg = mcp_servers.setdefault(server_name, {})
        tools_cfg = srv_cfg.setdefault("tools", {})

        if new_exclude:
            tools_cfg["exclude"] = new_exclude
            # Remove include if present — we're switching to exclude mode
            tools_cfg.pop("include", None)
        else:
            # All tools enabled — clear filters
            tools_cfg.pop("exclude", None)
            tools_cfg.pop("include", None)

        enabled_count = len(chosen)
        disabled_count = len(tools) - enabled_count
        _print_success(
            f"  {server_name}: {enabled_count} enabled, {disabled_count} disabled"
        )
        any_changes = True

    if any_changes:
        save_config(config)
        print()
        print(color("  ✓ MCP 工具配置已保存", Colors.GREEN))
    else:
        print(color("  MCP 工具无更改", Colors.DIM))


# ─── Non-interactive disable/enable ──────────────────────────────────────────


def _apply_toolset_change(config: dict, platform: str, toolset_names: List[str], action: str):
    """Add or remove built-in toolsets for a platform."""
    enabled = _get_platform_tools(config, platform, include_default_mcp_servers=False)
    if action == "disable":
        updated = enabled - set(toolset_names)
    else:
        updated = enabled | set(toolset_names)
    _save_platform_tools(config, platform, updated)


def _apply_mcp_change(config: dict, targets: List[str], action: str) -> Set[str]:
    """Add or remove specific MCP tools from a server's exclude list.

    Returns the set of server names that were not found in config.
    """
    failed_servers: Set[str] = set()
    mcp_servers = config.get("mcp_servers") or {}

    for target in targets:
        server_name, tool_name = target.split(":", 1)
        if server_name not in mcp_servers:
            failed_servers.add(server_name)
            continue
        tools_cfg = mcp_servers[server_name].setdefault("tools", {})
        exclude = list(tools_cfg.get("exclude") or [])
        if action == "disable":
            if tool_name not in exclude:
                exclude.append(tool_name)
        else:
            exclude = [t for t in exclude if t != tool_name]
        tools_cfg["exclude"] = exclude

    return failed_servers


def _print_tools_list(enabled_toolsets: set, mcp_servers: dict, platform: str = "cli"):
    """Print a summary of enabled/disabled toolsets and MCP tool filters."""
    effective = _get_effective_configurable_toolsets()
    builtin_keys = {ts_key for ts_key, _, _ in CONFIGURABLE_TOOLSETS}

    print(f"内置工具集 ({platform}):")
    for ts_key, label, _ in effective:
        if ts_key not in builtin_keys:
            continue
        status = (color("✓ 已启用", Colors.GREEN) if ts_key in enabled_toolsets
                  else color("✗ 已禁用", Colors.RED))
        print(f"  {status}  {ts_key}  {color(label, Colors.DIM)}")

    # Plugin toolsets
    plugin_entries = [(k, l) for k, l, _ in effective if k not in builtin_keys]
    if plugin_entries:
        print()
        print(f"插件工具集 ({platform}):")
        for ts_key, label in plugin_entries:
            status = (color("✓ 已启用", Colors.GREEN) if ts_key in enabled_toolsets
                      else color("✗ 已禁用", Colors.RED))
            print(f"  {status}  {ts_key}  {color(label, Colors.DIM)}")

    if mcp_servers:
        print()
        print("MCP 服务器:")
        for srv_name, srv_cfg in mcp_servers.items():
            tools_cfg = srv_cfg.get("tools") or {}
            exclude = tools_cfg.get("exclude") or []
            include = tools_cfg.get("include") or []
            if include:
                _print_info(f"{srv_name}  [仅包含: {', '.join(include)}]")
            elif exclude:
                _print_info(f"{srv_name}  [已排除: {color(', '.join(exclude), Colors.YELLOW)}]")
            else:
                _print_info(f"{srv_name}  {color('所有工具已启用', Colors.DIM)}")


def tools_disable_enable_command(args):
    """Enable, disable, or list tools for a platform.

    Built-in toolsets use plain names (e.g. ``web``, ``memory``).
    MCP tools use ``server:tool`` notation (e.g. ``github:create_issue``).
    """
    action = args.tools_action
    platform = getattr(args, "platform", "cli")
    config = load_config()

    if platform not in PLATFORMS:
        _print_error(f"未知平台 '{platform}'。有效值: {', '.join(PLATFORMS)}")
        return

    if action == "list":
        _print_tools_list(_get_platform_tools(config, platform, include_default_mcp_servers=False),
                          config.get("mcp_servers") or {}, platform)
        return

    targets: List[str] = args.names
    toolset_targets = [t for t in targets if ":" not in t]
    mcp_targets = [t for t in targets if ":" in t]

    valid_toolsets = {ts_key for ts_key, _, _ in CONFIGURABLE_TOOLSETS} | _get_plugin_toolset_keys()
    unknown_toolsets = [t for t in toolset_targets if t not in valid_toolsets]
    if unknown_toolsets:
        for name in unknown_toolsets:
            _print_error(f"Unknown toolset '{name}'")
        toolset_targets = [t for t in toolset_targets if t in valid_toolsets]

    if toolset_targets:
        _apply_toolset_change(config, platform, toolset_targets, action)

    failed_servers: Set[str] = set()
    if mcp_targets:
        failed_servers = _apply_mcp_change(config, mcp_targets, action)
        for srv in failed_servers:
            _print_error(f"MCP server '{srv}' not found in config")

    save_config(config)

    successful = [
        t for t in targets
        if t not in unknown_toolsets and (":" not in t or t.split(":")[0] not in failed_servers)
    ]
    if successful:
        verb = "已禁用" if action == "disable" else "已启用"
        _print_success(f"{verb}: {', '.join(successful)}")
