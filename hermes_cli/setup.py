"""
Interactive setup wizard for Hermes Agent.

Modular wizard with independently-runnable sections:
  1. Model & Provider — choose your AI provider and model
  2. Terminal Backend — where your agent runs commands
  3. Agent Settings — iterations, compression, session reset
  4. Messaging Platforms — connect Telegram, Discord, etc.
  5. Tools — configure TTS, web search, image generation, etc.

Config files are stored in ~/.hermes/ for easy access.
"""

import importlib.util
import logging
import os
import shutil
import sys
import copy
from pathlib import Path
from typing import Optional, Dict, Any

from hermes_cli.nous_subscription import (
    apply_nous_provider_defaults,
    get_nous_subscription_features,
)
from tools.tool_backend_helpers import managed_nous_tools_enabled
from hermes_constants import get_optional_skills_dir

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

_DOCS_BASE = "https://hermes-agent.nousresearch.com/docs"


def _model_config_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    current_model = config.get("model")
    if isinstance(current_model, dict):
        return dict(current_model)
    if isinstance(current_model, str) and current_model.strip():
        return {"default": current_model.strip()}
    return {}


def _get_credential_pool_strategies(config: Dict[str, Any]) -> Dict[str, str]:
    strategies = config.get("credential_pool_strategies")
    return dict(strategies) if isinstance(strategies, dict) else {}


def _set_credential_pool_strategy(config: Dict[str, Any], provider: str, strategy: str) -> None:
    if not provider:
        return
    strategies = _get_credential_pool_strategies(config)
    strategies[provider] = strategy
    config["credential_pool_strategies"] = strategies


def _supports_same_provider_pool_setup(provider: str) -> bool:
    if not provider or provider == "custom":
        return False
    if provider == "openrouter":
        return True
    from hermes_cli.auth import PROVIDER_REGISTRY

    pconfig = PROVIDER_REGISTRY.get(provider)
    if not pconfig:
        return False
    return pconfig.auth_type in {"api_key", "oauth_device_code"}


# Default model lists per provider — used as fallback when the live
# /models endpoint can't be reached.
_DEFAULT_PROVIDER_MODELS = {
    "copilot-acp": [
        "copilot-acp",
    ],
    "copilot": [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5-mini",
        "gpt-5.3-codex",
        "gpt-5.2-codex",
        "gpt-4.1",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-opus-4.6",
        "claude-sonnet-4.6",
        "claude-sonnet-4.5",
        "claude-haiku-4.5",
        "gemini-2.5-pro",
        "grok-code-fast-1",
    ],
    "gemini": [
        "gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview",
        "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
        "gemma-4-31b-it", "gemma-4-26b-it",
    ],
    "zai": ["glm-5.1", "glm-5", "glm-4.7", "glm-4.5", "glm-4.5-flash"],
    "kimi-coding": ["kimi-k2.5", "kimi-k2-thinking", "kimi-k2-turbo-preview"],
    "kimi-coding-cn": ["kimi-k2.5", "kimi-k2-thinking", "kimi-k2-turbo-preview"],
    "arcee": ["trinity-large-thinking", "trinity-large-preview", "trinity-mini"],
    "minimax": ["MiniMax-M2.7", "MiniMax-M2.5", "MiniMax-M2.1", "MiniMax-M2"],
    "minimax-cn": ["MiniMax-M2.7", "MiniMax-M2.5", "MiniMax-M2.1", "MiniMax-M2"],
    "ai-gateway": ["anthropic/claude-opus-4.6", "anthropic/claude-sonnet-4.6", "openai/gpt-5", "google/gemini-3-flash"],
    "kilocode": ["anthropic/claude-opus-4.6", "anthropic/claude-sonnet-4.6", "openai/gpt-5.4", "google/gemini-3-pro-preview", "google/gemini-3-flash-preview"],
    "opencode-zen": ["gpt-5.4", "gpt-5.3-codex", "claude-sonnet-4-6", "gemini-3-flash", "glm-5", "kimi-k2.5", "minimax-m2.7"],
    "opencode-go": ["glm-5", "kimi-k2.5", "mimo-v2-pro", "mimo-v2-omni", "minimax-m2.5", "minimax-m2.7"],
    "huggingface": [
        "Qwen/Qwen3.5-397B-A17B", "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "Qwen/Qwen3-Coder-480B-A35B-Instruct", "deepseek-ai/DeepSeek-R1-0528",
        "deepseek-ai/DeepSeek-V3.2", "moonshotai/Kimi-K2.5",
    ],
    "xidao": ["claude-opus-4-6", "claude-sonnet-4-6", "gpt-5.4", "glm-5.1", "glm-5", "qwen3.6-plus"],
}


def _current_reasoning_effort(config: Dict[str, Any]) -> str:
    agent_cfg = config.get("agent")
    if isinstance(agent_cfg, dict):
        return str(agent_cfg.get("reasoning_effort") or "").strip().lower()
    return ""


def _set_reasoning_effort(config: Dict[str, Any], effort: str) -> None:
    agent_cfg = config.get("agent")
    if not isinstance(agent_cfg, dict):
        agent_cfg = {}
        config["agent"] = agent_cfg
    agent_cfg["reasoning_effort"] = effort




# Import config helpers
from hermes_cli.config import (
    DEFAULT_CONFIG,
    get_hermes_home,
    get_config_path,
    get_env_path,
    load_config,
    save_config,
    save_env_value,
    get_env_value,
    ensure_hermes_home,
)
# display_hermes_home imported lazily at call sites (stale-module safety during hermes update)

from hermes_cli.colors import Colors, color


def print_header(title: str):
    """打印章节标题。"""
    print()
    print(color(f"◆ {title}", Colors.CYAN, Colors.BOLD))


from hermes_cli.cli_output import (  # noqa: E402
    print_error,
    print_info,
    print_success,
    print_warning,
)


def is_interactive_stdin() -> bool:
    """Return True when stdin looks like a usable interactive TTY."""
    stdin = getattr(sys, "stdin", None)
    if stdin is None:
        return False
    try:
        return bool(stdin.isatty())
    except Exception:
        return False


def print_noninteractive_setup_guidance(reason: str | None = None) -> None:
    """打印无头/非交互式设置流程的指导信息。"""
    print()
    print(color("⚕ Hermes 设置 — 非交互模式", Colors.CYAN, Colors.BOLD))
    print()
    if reason:
        print_info(reason)
    print_info("此处无法使用交互式向导。")
    print()
    print_info("使用环境变量或配置命令来配置 Hermes：")
    print_info("  hermes config set model.provider custom")
    print_info("  hermes config set model.base_url http://localhost:8080/v1")
    print_info("  hermes config set model.default your-model-name")
    print()
    print_info("或在您的环境中设置 OPENROUTER_API_KEY / OPENAI_API_KEY。")
    print_info("在交互式终端中运行 'hermes setup' 以使用完整向导。")
    print()


def prompt(question: str, default: str = None, password: bool = False) -> str:
    """Prompt for input with optional default."""
    if default:
        display = f"{question} [{default}]: "
    else:
        display = f"{question}: "

    try:
        if password:
            import getpass

            value = getpass.getpass(color(display, Colors.YELLOW))
        else:
            value = input(color(display, Colors.YELLOW))

        return value.strip() or default or ""
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


def _curses_prompt_choice(question: str, choices: list, default: int = 0) -> int:
    """Single-select menu using curses. Delegates to curses_radiolist."""
    from hermes_cli.curses_ui import curses_radiolist
    return curses_radiolist(question, choices, selected=default, cancel_returns=-1)



def prompt_choice(question: str, choices: list, default: int = 0) -> int:
    """使用箭头键导航从列表中提示选择。

    Escape 保持当前默认值（跳过问题）。
    Ctrl+C 退出向导。
    """
    idx = _curses_prompt_choice(question, choices, default)
    if idx >= 0:
        if idx == default:
            print_info("  已跳过（保持当前值）")
            print()
            return default
        print()
        return idx

    print(color(question, Colors.YELLOW))
    for i, choice in enumerate(choices):
        marker = "●" if i == default else "○"
        if i == default:
            print(color(f"  {marker} {choice}", Colors.GREEN))
        else:
            print(f"  {marker} {choice}")

    print_info(f"  回车确认默认值 ({default + 1})  Ctrl+C 退出")

    while True:
        try:
            value = input(
                color(f"  Select [1-{len(choices)}] ({default + 1}): ", Colors.DIM)
            )
            if not value:
                return default
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return idx
            print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a number")
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt for yes/no. Ctrl+C exits, empty input returns default."""
    default_str = "Y/n" if default else "y/N"

    while True:
        try:
            value = (
                input(color(f"{question} [{default_str}]: ", Colors.YELLOW))
                .strip()
                .lower()
            )
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)

        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print_error("Please enter 'y' or 'n'")


def prompt_checklist(title: str, items: list, pre_selected: list = None) -> list:
    """
    Display a multi-select checklist and return the indices of selected items.

    Each item in `items` is a display string. `pre_selected` is a list of
    indices that should be checked by default. A "Continue →" option is
    appended at the end — the user toggles items with Space and confirms
    with Enter on "Continue →".

    Falls back to a numbered toggle interface when simple_term_menu is
    unavailable.

    Returns:
        List of selected indices (not including the Continue option).
    """
    if pre_selected is None:
        pre_selected = []

    from hermes_cli.curses_ui import curses_checklist

    chosen = curses_checklist(
        title,
        items,
        set(pre_selected),
        cancel_returns=set(pre_selected),
    )
    return sorted(chosen)


def _prompt_api_key(var: dict):
    """Display a nicely formatted API key input screen for a single env var."""
    tools = var.get("tools", [])
    tools_str = ", ".join(tools[:3])
    if len(tools) > 3:
        tools_str += f", +{len(tools) - 3} more"

    print()
    print(color(f"  ─── {var.get('description', var['name'])} ───", Colors.CYAN))
    print()
    if tools_str:
        print_info(f"  Enables: {tools_str}")
    if var.get("url"):
        print_info(f"  Get your key at: {var['url']}")
    print()

    if var.get("password"):
        value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
    else:
        value = prompt(f"  {var.get('prompt', var['name'])}")

    if value:
        save_env_value(var["name"], value)
        print_success("  ✓ Saved")
    else:
        print_warning("  Skipped (configure later with 'hermes setup')")


def _print_setup_summary(config: dict, hermes_home):
    """Print the setup completion summary."""
    # Tool availability summary
    print()
    print_header("工具可用性摘要")

    tool_status = []
    subscription_features = get_nous_subscription_features(config)

    # Vision — use the same runtime resolver as the actual vision tools
    try:
        from agent.auxiliary_client import get_available_vision_backends

        _vision_backends = get_available_vision_backends()
    except Exception:
        _vision_backends = []

    if _vision_backends:
        tool_status.append(("视觉（图像分析）", True, None))
    else:
        tool_status.append(("视觉（图像分析）", False, "运行 'hermes setup' 配置"))

    # Mixture of Agents — requires OpenRouter specifically (calls multiple models)
    if get_env_value("OPENROUTER_API_KEY"):
        tool_status.append(("混合代理", True, None))
    else:
        tool_status.append(("混合代理", False, "OPENROUTER_API_KEY"))

    # Web tools (Exa, Parallel, Firecrawl, or Tavily)
    if subscription_features.web.managed_by_nous:
        tool_status.append(("网页搜索和提取（Nous 订阅）", True, None))
    elif subscription_features.web.available:
        label = "网页搜索和提取"
        if subscription_features.web.current_provider:
            label = f"网页搜索和提取（{subscription_features.web.current_provider}）"
        tool_status.append((label, True, None))
    else:
        tool_status.append(("网页搜索和提取", False, "EXA_API_KEY、PARALLEL_API_KEY、FIRECRAWL_API_KEY/FIRECRAWL_API_URL 或 TAVILY_API_KEY"))

    # Browser tools (local Chromium, Camofox, Browserbase, Browser Use, or Firecrawl)
    browser_provider = subscription_features.browser.current_provider
    if subscription_features.browser.managed_by_nous:
        tool_status.append(("浏览器自动化（Nous Browser Use）", True, None))
    elif subscription_features.browser.available:
        label = "浏览器自动化"
        if browser_provider:
            label = f"浏览器自动化（{browser_provider}）"
        tool_status.append((label, True, None))
    else:
        missing_browser_hint = "npm install -g agent-browser，设置 CAMOFOX_URL，或配置 Browser Use 或 Browserbase"
        if browser_provider == "Browserbase":
            missing_browser_hint = (
                "npm install -g agent-browser 并设置 "
                "BROWSERBASE_API_KEY/BROWSERBASE_PROJECT_ID"
            )
        elif browser_provider == "Browser Use":
            missing_browser_hint = (
                "npm install -g agent-browser 并设置 BROWSER_USE_API_KEY"
            )
        elif browser_provider == "Camofox":
            missing_browser_hint = "CAMOFOX_URL"
        elif browser_provider == "Local browser":
            missing_browser_hint = "npm install -g agent-browser"
        tool_status.append(
            ("浏览器自动化", False, missing_browser_hint)
        )

    # FAL (image generation)
    if subscription_features.image_gen.managed_by_nous:
        tool_status.append(("图像生成（Nous 订阅）", True, None))
    elif subscription_features.image_gen.available:
        tool_status.append(("图像生成", True, None))
    else:
        tool_status.append(("图像生成", False, "FAL_KEY"))

    # TTS — show configured provider
    tts_provider = config.get("tts", {}).get("provider", "edge")
    if subscription_features.tts.managed_by_nous:
        tool_status.append(("文本转语音（通过 Nous 订阅的 OpenAI）", True, None))
    elif tts_provider == "elevenlabs" and get_env_value("ELEVENLABS_API_KEY"):
        tool_status.append(("文本转语音（ElevenLabs）", True, None))
    elif tts_provider == "openai" and (
        get_env_value("VOICE_TOOLS_OPENAI_KEY") or get_env_value("OPENAI_API_KEY")
    ):
        tool_status.append(("文本转语音（OpenAI）", True, None))
    elif tts_provider == "minimax" and get_env_value("MINIMAX_API_KEY"):
        tool_status.append(("文本转语音（MiniMax）", True, None))
    elif tts_provider == "mistral" and get_env_value("MISTRAL_API_KEY"):
        tool_status.append(("文本转语音（Mistral Voxtral）", True, None))
    elif tts_provider == "neutts":
        try:
            import importlib.util
            neutts_ok = importlib.util.find_spec("neutts") is not None
        except Exception:
            neutts_ok = False
        if neutts_ok:
            tool_status.append(("文本转语音（NeuTTS 本地）", True, None))
        else:
            tool_status.append(("文本转语音（NeuTTS — 未安装）", False, "运行 'hermes setup tts'"))
    else:
        tool_status.append(("文本转语音（Edge TTS）", True, None))

    if subscription_features.modal.managed_by_nous:
        tool_status.append(("Modal 执行（Nous 订阅）", True, None))
    elif config.get("terminal", {}).get("backend") == "modal":
        if subscription_features.modal.direct_override:
            tool_status.append(("Modal 执行（直接 Modal）", True, None))
        else:
            tool_status.append(("Modal 执行", False, "运行 'hermes setup terminal'"))
    elif managed_nous_tools_enabled() and subscription_features.nous_auth_present:
        tool_status.append(("Modal 执行（通过 Nous 订阅可选）", True, None))

    # Tinker + WandB (RL training)
    if get_env_value("TINKER_API_KEY") and get_env_value("WANDB_API_KEY"):
        tool_status.append(("RL 训练（Tinker）", True, None))
    elif get_env_value("TINKER_API_KEY"):
        tool_status.append(("RL 训练（Tinker）", False, "WANDB_API_KEY"))
    else:
        tool_status.append(("RL 训练（Tinker）", False, "TINKER_API_KEY"))

    # Home Assistant
    if get_env_value("HASS_TOKEN"):
        tool_status.append(("智能家居（Home Assistant）", True, None))

    # Skills Hub
    if get_env_value("GITHUB_TOKEN"):
        tool_status.append(("技能中心（GitHub）", True, None))
    else:
        tool_status.append(("技能中心（GitHub）", False, "GITHUB_TOKEN"))

    # Terminal (always available if system deps met)
    tool_status.append(("终端/命令", True, None))

    # Task planning (always available, in-memory)
    tool_status.append(("任务规划（todo）", True, None))

    # Skills (always available -- bundled skills + user-created skills)
    tool_status.append(("技能（查看、创建、编辑）", True, None))

    # Print status
    available_count = sum(1 for _, avail, _ in tool_status if avail)
    total_count = len(tool_status)

    print_info(f"{available_count}/{total_count} 个工具类别可用：")
    print()

    for name, available, missing_var in tool_status:
        if available:
            print(f"   {color('✓', Colors.GREEN)} {name}")
        else:
            print(
                f"   {color('✗', Colors.RED)} {name} {color(f'（缺少 {missing_var}）', Colors.DIM)}"
            )

    print()

    disabled_tools = [(name, var) for name, avail, var in tool_status if not avail]
    if disabled_tools:
        print_warning(
            "部分工具已禁用。运行 'hermes setup tools' 配置它们，"
        )
        from hermes_constants import display_hermes_home as _dhh
        print_warning(f"或直接编辑 {_dhh()}/.env 添加缺失的 API 密钥。")
        print()

    # Done banner
    print()
    print(
        color(
            "┌─────────────────────────────────────────────────────────┐", Colors.GREEN
        )
    )
    print(
        color(
            "│              ✓ 设置完成！                              │", Colors.GREEN
        )
    )
    print(
        color(
            "└─────────────────────────────────────────────────────────┘", Colors.GREEN
        )
    )
    print()

    # Show file locations prominently
    from hermes_constants import display_hermes_home as _dhh
    print(color(f"📁 您的所有文件都在 {_dhh()}/：", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('设置文件：', Colors.YELLOW)}  {get_config_path()}")
    print(f"   {color('API 密钥：', Colors.YELLOW)}  {get_env_path()}")
    print(
        f"   {color('数据目录：', Colors.YELLOW)}      {hermes_home}/cron/, sessions/, logs/"
    )
    print()

    print(color("─" * 60, Colors.DIM))
    print()
    print(color("📝 要编辑您的配置：", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('hermes setup', Colors.GREEN)}          重新运行完整向导")
    print(f"   {color('hermes setup model', Colors.GREEN)}    更改模型/提供商")
    print(f"   {color('hermes setup terminal', Colors.GREEN)} 更改终端后端")
    print(f"   {color('hermes setup gateway', Colors.GREEN)}  配置消息平台")
    print(f"   {color('hermes setup tools', Colors.GREEN)}    配置工具提供商")
    print()
    print(f"   {color('hermes config', Colors.GREEN)}         查看当前设置")
    print(
        f"   {color('hermes config edit', Colors.GREEN)}    在编辑器中打开配置"
    )
    print(f"   {color('hermes config set <key> <value>', Colors.GREEN)}")
    print("                          设置特定值")
    print()
    print("   或直接编辑文件：")
    print(f"   {color(f'nano {get_config_path()}', Colors.DIM)}")
    print(f"   {color(f'nano {get_env_path()}', Colors.DIM)}")
    print()

    print(color("─" * 60, Colors.DIM))
    print()
    print(color("🚀 准备就绪！", Colors.CYAN, Colors.BOLD))
    print()
    print(f"   {color('hermes', Colors.GREEN)}              开始聊天")
    print(f"   {color('hermes gateway', Colors.GREEN)}      启动消息网关")
    print(f"   {color('hermes doctor', Colors.GREEN)}       检查问题")
    print()


def _prompt_container_resources(config: dict):
    """Prompt for container resource settings (Docker, Singularity, Modal, Daytona)."""
    terminal = config.setdefault("terminal", {})

    print()
    print_info("容器资源设置：")

    # Persistence
    current_persist = terminal.get("container_persistent", True)
    persist_label = "是" if current_persist else "否"
    print_info("  持久化文件系统在会话间保留文件。")
    print_info("  设置为'否'用于每次重置的临时沙箱。")
    persist_str = prompt(
        "  跨会话持久化文件系统？（是/否）", persist_label
    )
    terminal["container_persistent"] = persist_str.lower() in ("yes", "true", "y", "1", "是")

    # CPU
    current_cpu = terminal.get("container_cpu", 1)
    cpu_str = prompt("  CPU 核心数", str(current_cpu))
    try:
        terminal["container_cpu"] = float(cpu_str)
    except ValueError:
        pass

    # Memory
    current_mem = terminal.get("container_memory", 5120)
    mem_str = prompt("  内存大小 MB（5120 = 5GB）", str(current_mem))
    try:
        terminal["container_memory"] = int(mem_str)
    except ValueError:
        pass

    # Disk
    current_disk = terminal.get("container_disk", 51200)
    disk_str = prompt("  磁盘大小 MB（51200 = 50GB）", str(current_disk))
    try:
        terminal["container_disk"] = int(disk_str)
    except ValueError:
        pass


# Tool categories and provider config are now in tools_config.py (shared
# between `hermes tools` and `hermes setup tools`).


# =============================================================================
# Section 1: Model & Provider Configuration
# =============================================================================



def setup_model_provider(config: dict, *, quick: bool = False):
    """Configure the inference provider and default model.

    Delegates to ``cmd_model()`` (the same flow used by ``hermes model``)
    for provider selection, credential prompting, and model picking.
    This ensures a single code path for all provider setup — any new
    provider added to ``hermes model`` is automatically available here.

    When *quick* is True, skips credential rotation, vision, and TTS
    configuration — used by the streamlined first-time quick setup.
    """
    from hermes_cli.config import load_config, save_config

    print_header("推理提供商")
    print_info("选择如何连接到您的主要聊天模型。")
    print_info(f"   指南：{_DOCS_BASE}/integrations/providers")
    print()

    # Delegate to the shared hermes model flow — handles provider picker,
    # credential prompting, model selection, and config persistence.
    from hermes_cli.main import select_provider_and_model
    try:
        select_provider_and_model()
    except (SystemExit, KeyboardInterrupt):
        print()
        print_info("提供商设置已跳过。")
    except Exception as exc:
        logger.debug("select_provider_and_model error during setup: %s", exc)
        print_warning(f"提供商设置遇到错误：{exc}")
        print_info("您可以稍后重试：hermes model")

    # Re-sync the wizard's config dict from what cmd_model saved to disk.
    # This is critical: cmd_model writes to disk via its own load/save cycle,
    # and the wizard's final save_config(config) must not overwrite those
    # changes with stale values (#4172).
    _refreshed = load_config()
    config["model"] = _refreshed.get("model", config.get("model"))
    if "custom_providers" in _refreshed:
        config["custom_providers"] = _refreshed["custom_providers"]
    else:
        config.pop("custom_providers", None)

    # Derive the selected provider for downstream steps (vision setup).
    selected_provider = None
    _m = config.get("model")
    if isinstance(_m, dict):
        selected_provider = _m.get("provider")

    nous_subscription_selected = selected_provider == "nous"

    # ── Same-provider fallback & rotation setup (full setup only) ──
    if not quick and _supports_same_provider_pool_setup(selected_provider):
        try:
            from types import SimpleNamespace
            from agent.credential_pool import load_pool
            from hermes_cli.auth_commands import auth_add_command

            pool = load_pool(selected_provider)
            entries = pool.entries()
            entry_count = len(entries)
            manual_count = sum(1 for entry in entries if str(getattr(entry, "source", "")).startswith("manual"))
            auto_count = entry_count - manual_count
            print()
            print_header("同提供商回退和轮换")
            print_info(
                "Hermes 可以为一个提供商保留多个凭证并在它们之间"
            )
            print_info(
                "轮换，当凭证耗尽或受到速率限制时。这可以保护"
            )
            print_info(
                "您的主要提供商，同时减少配额问题导致的中断。"
            )
            print()
            if auto_count > 0:
                print_info(
                    f"Current pooled credentials for {selected_provider}: {entry_count} "
                    f"({manual_count} manual, {auto_count} auto-detected from env/shared auth)"
                )
            else:
                print_info(f"Current pooled credentials for {selected_provider}: {entry_count}")

            while prompt_yes_no("为同提供商回退添加另一个凭证？", False):
                auth_add_command(
                    SimpleNamespace(
                        provider=selected_provider,
                        auth_type="",
                        label=None,
                        api_key=None,
                        portal_url=None,
                        inference_url=None,
                        client_id=None,
                        scope=None,
                        no_browser=False,
                        timeout=15.0,
                        insecure=False,
                        ca_bundle=None,
                        min_key_ttl_seconds=5 * 60,
                    )
                )
                pool = load_pool(selected_provider)
                entry_count = len(pool.entries())
                print_info(f"Provider pool now has {entry_count} credential(s).")

            if entry_count > 1:
                strategy_labels = [
                    "填充优先/粘性 — 持续使用第一个健康的凭证直到耗尽",
                    "轮询 — 每次选择后轮换到下一个健康的凭证",
                    "随机 — 每次随机选择一个健康的凭证",
                ]
                current_strategy = _get_credential_pool_strategies(config).get(selected_provider, "fill_first")
                default_strategy_idx = {
                    "fill_first": 0,
                    "round_robin": 1,
                    "random": 2,
                }.get(current_strategy, 0)
                strategy_idx = prompt_choice(
                    "选择同提供商轮换策略：",
                    strategy_labels,
                    default_strategy_idx,
                )
                strategy_value = ["fill_first", "round_robin", "random"][strategy_idx]
                _set_credential_pool_strategy(config, selected_provider, strategy_value)
                print_success(f"Saved {selected_provider} rotation strategy: {strategy_value}")
        except Exception as exc:
            logger.debug("Could not configure same-provider fallback in setup: %s", exc)

    # ── Vision & Image Analysis Setup (full setup only) ──
    if quick:
        _vision_needs_setup = False
    else:
        try:
            from agent.auxiliary_client import get_available_vision_backends
            _vision_backends = set(get_available_vision_backends())
        except Exception:
            _vision_backends = set()

        _vision_needs_setup = not bool(_vision_backends)

        if selected_provider in _vision_backends:
            _vision_needs_setup = False

    if _vision_needs_setup:
        _prov_names = {
            "nous-api": "Nous Portal API key",
            "copilot": "GitHub Copilot",
            "copilot-acp": "GitHub Copilot ACP",
            "zai": "Z.AI / GLM",
            "kimi-coding": "Kimi / Moonshot",
            "kimi-coding-cn": "Kimi / Moonshot (China)",
            "minimax": "MiniMax",
            "minimax-cn": "MiniMax CN",
            "anthropic": "Anthropic",
            "ai-gateway": "Vercel AI Gateway",
            "custom": "your custom endpoint",
        }
        _prov_display = _prov_names.get(selected_provider, selected_provider or "your provider")

        print()
        print_header("视觉和图像分析（可选）")
        print_info(f"视觉使用单独的多模态后端。{_prov_display}")
        print_info("目前不提供 Hermes 可以自动使用的视觉功能，")
        print_info("所以现在选择一个后端或跳过稍后配置。")
        print()

        _vision_choices = [
            "OpenRouter — 使用 Gemini（在 openrouter.ai/keys 免费层）",
            "OpenAI 兼容端点 — 基础 URL、API 密钥和视觉模型",
            "暂时跳过",
        ]
        _vision_idx = prompt_choice("配置视觉：", _vision_choices, 2)

        if _vision_idx == 0:  # OpenRouter
            _or_key = prompt("  OpenRouter API 密钥", password=True).strip()
            if _or_key:
                save_env_value("OPENROUTER_API_KEY", _or_key)
                print_success("OpenRouter 密钥已保存 — 视觉将使用 Gemini")
            else:
                print_info("已跳过 — 视觉将不可用")
        elif _vision_idx == 1:  # OpenAI-compatible endpoint
            _base_url = prompt("  基础 URL（留空使用 OpenAI）").strip() or "https://api.openai.com/v1"
            _api_key_label = "  API 密钥"
            if "api.openai.com" in _base_url.lower():
                _api_key_label = "  OpenAI API 密钥"
            _oai_key = prompt(_api_key_label, password=True).strip()
            if _oai_key:
                save_env_value("OPENAI_API_KEY", _oai_key)
                # Save vision base URL to config (not .env — only secrets go there)
                _vaux = config.setdefault("auxiliary", {}).setdefault("vision", {})
                _vaux["base_url"] = _base_url
                if "api.openai.com" in _base_url.lower():
                    _oai_vision_models = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]
                    _vm_choices = _oai_vision_models + ["使用默认值（gpt-4o-mini）"]
                    _vm_idx = prompt_choice("选择视觉模型：", _vm_choices, 0)
                    _selected_vision_model = (
                        _oai_vision_models[_vm_idx]
                        if _vm_idx < len(_oai_vision_models)
                        else "gpt-4o-mini"
                    )
                else:
                    _selected_vision_model = prompt("  视觉模型（留空 = 使用主/自定义默认值）").strip()
                save_env_value("AUXILIARY_VISION_MODEL", _selected_vision_model)
                print_success(
                    f"视觉已配置，使用 {_base_url}"
                    + (f" ({_selected_vision_model})" if _selected_vision_model else "")
                )
            else:
                print_info("已跳过 — 视觉将不可用")
        else:
            print_info("已跳过 — 稍后可通过 'hermes setup' 添加或配置 AUXILIARY_VISION_* 设置")


    if selected_provider == "nous" and nous_subscription_selected:
        changed_defaults = apply_nous_provider_defaults(config)
        current_tts = str(config.get("tts", {}).get("provider") or "edge")
        if "tts" in changed_defaults:
            print_success("TTS provider set to: OpenAI TTS via your Nous subscription")
        else:
            print_info(f"Keeping your existing TTS provider: {current_tts}")

    save_config(config)

    if not quick and selected_provider != "nous":
        _setup_tts_provider(config)


# =============================================================================
# Section 1b: TTS Provider Configuration
# =============================================================================


def _check_espeak_ng() -> bool:
    """Check if espeak-ng is installed."""
    import shutil
    return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None


def _install_neutts_deps() -> bool:
    """Install NeuTTS dependencies with user approval. Returns True on success."""
    import subprocess
    import sys

    # Check espeak-ng
    if not _check_espeak_ng():
        print()
        print_warning("NeuTTS requires espeak-ng for phonemization.")
        if sys.platform == "darwin":
            print_info("Install with: brew install espeak-ng")
        elif sys.platform == "win32":
            print_info("Install with: choco install espeak-ng")
        else:
            print_info("Install with: sudo apt install espeak-ng")
        print()
        if prompt_yes_no("Install espeak-ng now?", True):
            try:
                if sys.platform == "darwin":
                    subprocess.run(["brew", "install", "espeak-ng"], check=True)
                elif sys.platform == "win32":
                    subprocess.run(["choco", "install", "espeak-ng", "-y"], check=True)
                else:
                    subprocess.run(["sudo", "apt", "install", "-y", "espeak-ng"], check=True)
                print_success("espeak-ng installed")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print_warning(f"Could not install espeak-ng automatically: {e}")
                print_info("Please install it manually and re-run setup.")
                return False
        else:
            print_warning("espeak-ng is required for NeuTTS. Install it manually before using NeuTTS.")

    # Install neutts Python package
    print()
    print_info("Installing neutts Python package...")
    print_info("This will also download the TTS model (~300MB) on first use.")
    print()
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "neutts[all]", "--quiet"],
            check=True, timeout=300,
        )
        print_success("neutts installed successfully")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print_error(f"Failed to install neutts: {e}")
        print_info("Try manually: python -m pip install -U neutts[all]")
        return False


def _setup_tts_provider(config: dict):
    """Interactive TTS provider selection with install flow for NeuTTS."""
    tts_config = config.get("tts", {})
    current_provider = tts_config.get("provider", "edge")
    subscription_features = get_nous_subscription_features(config)

    provider_labels = {
        "edge": "Edge TTS",
        "elevenlabs": "ElevenLabs",
        "openai": "OpenAI TTS",
        "minimax": "MiniMax TTS",
        "mistral": "Mistral Voxtral TTS",
        "neutts": "NeuTTS",
    }
    current_label = provider_labels.get(current_provider, current_provider)

    print()
    print_header("文本转语音提供商（可选）")
    print_info(f"当前：{current_label}")
    print()

    choices = []
    providers = []
    if managed_nous_tools_enabled() and subscription_features.nous_auth_present:
        choices.append("Nous 订阅（托管 OpenAI TTS，计入您的订阅）")
        providers.append("nous-openai")
    choices.extend(
        [
            "Edge TTS（免费、基于云端、无需设置）",
            "ElevenLabs（优质音质、需要 API 密钥）",
            "OpenAI TTS（良好音质、需要 API 密钥）",
            "MiniMax TTS（高质量带声音克隆、需要 API 密钥）",
            "Mistral Voxtral TTS（多语言、原生 Opus、需要 API 密钥）",
            "NeuTTS（本地设备端、免费、约 300MB 模型下载）",
        ]
    )
    providers.extend(["edge", "elevenlabs", "openai", "minimax", "mistral", "neutts"])
    choices.append(f"保持当前（{current_label}）")
    keep_current_idx = len(choices) - 1
    idx = prompt_choice("选择 TTS 提供商：", choices, keep_current_idx)

    if idx == keep_current_idx:
        return

    selected = providers[idx]
    selected_via_nous = selected == "nous-openai"
    if selected == "nous-openai":
        selected = "openai"
        print_info("OpenAI TTS 将使用托管的 Nous 网关并计入您的订阅。")
        if get_env_value("VOICE_TOOLS_OPENAI_KEY") or get_env_value("OPENAI_API_KEY"):
            print_warning(
                "直接 OpenAI 凭证仍然配置，可能在从 ~/.hermes/.env 移除前优先使用。"
            )

    if selected == "neutts":
        # Check if already installed
        try:
            import importlib.util
            already_installed = importlib.util.find_spec("neutts") is not None
        except Exception:
            already_installed = False

        if already_installed:
            print_success("NeuTTS 已安装")
        else:
            print()
            print_info("NeuTTS 需要：")
            print_info("  • Python 包：neutts（约 50MB 安装 + 首次使用时约 300MB 模型）")
            print_info("  • 系统包：espeak-ng（音素转换器）")
            print()
            if prompt_yes_no("现在安装 NeuTTS 依赖？", True):
                if not _install_neutts_deps():
                    print_warning("NeuTTS 安装不完整。回退到 Edge TTS。")
                    selected = "edge"
            else:
                print_info("跳过安装。手动安装后将 tts.provider 设置为 'neutts'。")
                selected = "edge"

    elif selected == "elevenlabs":
        existing = get_env_value("ELEVENLABS_API_KEY")
        if not existing:
            print()
            api_key = prompt("ElevenLabs API 密钥", password=True)
            if api_key:
                save_env_value("ELEVENLABS_API_KEY", api_key)
                print_success("ElevenLabs API 密钥已保存")
            else:
                print_warning("未提供 API 密钥。回退到 Edge TTS。")
                selected = "edge"

    elif selected == "openai" and not selected_via_nous:
        existing = get_env_value("VOICE_TOOLS_OPENAI_KEY") or get_env_value("OPENAI_API_KEY")
        if not existing:
            print()
            api_key = prompt("用于 TTS 的 OpenAI API 密钥", password=True)
            if api_key:
                save_env_value("VOICE_TOOLS_OPENAI_KEY", api_key)
                print_success("OpenAI TTS API 密钥已保存")
            else:
                print_warning("未提供 API 密钥。回退到 Edge TTS。")
                selected = "edge"

    elif selected == "minimax":
        existing = get_env_value("MINIMAX_API_KEY")
        if not existing:
            print()
            api_key = prompt("用于 TTS 的 MiniMax API 密钥", password=True)
            if api_key:
                save_env_value("MINIMAX_API_KEY", api_key)
                print_success("MiniMax TTS API 密钥已保存")
            else:
                print_warning("未提供 API 密钥。回退到 Edge TTS。")
                selected = "edge"

    elif selected == "mistral":
        existing = get_env_value("MISTRAL_API_KEY")
        if not existing:
            print()
            api_key = prompt("用于 TTS 的 Mistral API 密钥", password=True)
            if api_key:
                save_env_value("MISTRAL_API_KEY", api_key)
                print_success("Mistral TTS API 密钥已保存")
            else:
                print_warning("未提供 API 密钥。回退到 Edge TTS。")
                selected = "edge"

    # Save the selection
    if "tts" not in config:
        config["tts"] = {}
    config["tts"]["provider"] = selected
    save_config(config)
    print_success(f"TTS 提供商已设置为：{provider_labels.get(selected, selected)}")


def setup_tts(config: dict):
    """Standalone TTS setup (for 'hermes setup tts')."""
    _setup_tts_provider(config)


# =============================================================================
# Section 2: Terminal Backend Configuration
# =============================================================================


def setup_terminal_backend(config: dict):
    """Configure the terminal execution backend."""
    import platform as _platform
    import shutil

    print_header("终端后端")
    print_info("选择 Hermes 运行 shell 命令和代码的位置。")
    print_info("这会影响工具执行、文件访问和隔离性。")
    print_info(f"   指南：{_DOCS_BASE}/developer-guide/environments")
    print()

    current_backend = config.get("terminal", {}).get("backend", "local")
    is_linux = _platform.system() == "Linux"

    # Build backend choices with descriptions
    terminal_choices = [
        "本地 - 直接在本机运行（默认）",
        "Docker - 具有可配置资源的隔离容器",
        "Modal - 无服务器云沙箱",
        "SSH - 在远程机器上运行",
        "Daytona - 持久化云开发环境",
    ]
    idx_to_backend = {0: "local", 1: "docker", 2: "modal", 3: "ssh", 4: "daytona"}
    backend_to_idx = {"local": 0, "docker": 1, "modal": 2, "ssh": 3, "daytona": 4}

    next_idx = 5
    if is_linux:
        terminal_choices.append("Singularity/Apptainer - 适合 HPC 的容器")
        idx_to_backend[next_idx] = "singularity"
        backend_to_idx["singularity"] = next_idx
        next_idx += 1

    # Add keep current option
    keep_current_idx = next_idx
    terminal_choices.append(f"保持当前（{current_backend}）")
    idx_to_backend[keep_current_idx] = current_backend

    terminal_idx = prompt_choice(
        "选择终端后端：", terminal_choices, keep_current_idx
    )

    selected_backend = idx_to_backend.get(terminal_idx)

    if terminal_idx == keep_current_idx:
        print_info(f"保持当前后端：{current_backend}")
        return

    config.setdefault("terminal", {})["backend"] = selected_backend

    if selected_backend == "local":
        print_success("终端后端：本地")
        print_info("命令直接在本机运行。")

        # CWD for messaging
        print()
        print_info("消息会话的工作目录：")
        print_info("  当通过 Telegram/Discord 使用 Hermes 时，这是")
        print_info(
            "  代理启动的位置。CLI 模式始终在当前目录启动。"
        )
        current_cwd = config.get("terminal", {}).get("cwd", "")
        cwd = prompt("  消息工作目录", current_cwd or str(Path.home()))
        if cwd:
            config["terminal"]["cwd"] = cwd

        # Sudo support
        print()
        existing_sudo = get_env_value("SUDO_PASSWORD")
        if existing_sudo:
            print_info("Sudo 密码：已配置")
        else:
            if prompt_yes_no(
                "启用 sudo 支持？（存储密码用于 apt install 等）", False
            ):
                sudo_pass = prompt("  Sudo 密码", password=True)
                if sudo_pass:
                    save_env_value("SUDO_PASSWORD", sudo_pass)
                    print_success("Sudo 密码已保存")

    elif selected_backend == "docker":
        print_success("终端后端：Docker")

        # Check if Docker is available
        docker_bin = shutil.which("docker")
        if not docker_bin:
            print_warning("在 PATH 中未找到 Docker！")
            print_info("安装 Docker：https://docs.docker.com/get-docker/")
        else:
            print_info(f"找到 Docker：{docker_bin}")

        # Docker image
        current_image = config.get("terminal", {}).get(
            "docker_image", "nikolaik/python-nodejs:python3.11-nodejs20"
        )
        image = prompt("  Docker 镜像", current_image)
        config["terminal"]["docker_image"] = image
        save_env_value("TERMINAL_DOCKER_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "singularity":
        print_success("终端后端：Singularity/Apptainer")

        # Check if singularity/apptainer is available
        sing_bin = shutil.which("apptainer") or shutil.which("singularity")
        if not sing_bin:
            print_warning("在 PATH 中未找到 Singularity/Apptainer！")
            print_info(
                "安装：https://apptainer.org/docs/admin/main/installation.html"
            )
        else:
            print_info(f"找到：{sing_bin}")

        current_image = config.get("terminal", {}).get(
            "singularity_image", "docker://nikolaik/python-nodejs:python3.11-nodejs20"
        )
        image = prompt("  容器镜像", current_image)
        config["terminal"]["singularity_image"] = image
        save_env_value("TERMINAL_SINGULARITY_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "modal":
        print_success("终端后端：Modal")
        print_info("无服务器云沙箱。每个会话获得自己的容器。")
        from tools.managed_tool_gateway import is_managed_tool_gateway_ready
        from tools.tool_backend_helpers import normalize_modal_mode

        managed_modal_available = bool(
            managed_nous_tools_enabled()
            and
            get_nous_subscription_features(config).nous_auth_present
            and is_managed_tool_gateway_ready("modal")
        )
        modal_mode = normalize_modal_mode(config.get("terminal", {}).get("modal_mode"))
        use_managed_modal = False
        if managed_modal_available:
            modal_choices = [
                "使用我的 Nous 订阅",
                "使用我自己的 Modal 账户",
            ]
            if modal_mode == "managed":
                default_modal_idx = 0
            elif modal_mode == "direct":
                default_modal_idx = 1
            else:
                default_modal_idx = 1 if get_env_value("MODAL_TOKEN_ID") else 0
            modal_mode_idx = prompt_choice(
                "选择 Modal 执行的计费方式：",
                modal_choices,
                default_modal_idx,
            )
            use_managed_modal = modal_mode_idx == 0

        if use_managed_modal:
            config["terminal"]["modal_mode"] = "managed"
            print_info("Modal 执行将使用托管的 Nous 网关并计入您的订阅。")
            if get_env_value("MODAL_TOKEN_ID") or get_env_value("MODAL_TOKEN_SECRET"):
                print_info(
                    "直接 Modal 凭证仍然配置，但此后端固定为托管模式。"
                )
        else:
            config["terminal"]["modal_mode"] = "direct"
            print_info("需要 Modal 账户：https://modal.com")

            # Check if modal SDK is installed
            try:
                __import__("modal")
            except ImportError:
                print_info("正在安装 modal SDK...")
                import subprocess

                uv_bin = shutil.which("uv")
                if uv_bin:
                    result = subprocess.run(
                        [
                            uv_bin,
                            "pip",
                            "install",
                            "--python",
                            sys.executable,
                            "modal",
                        ],
                        capture_output=True,
                        text=True,
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "modal"],
                        capture_output=True,
                        text=True,
                    )
                if result.returncode == 0:
                    print_success("modal SDK 已安装")
                else:
                    print_warning("安装失败 — 手动运行：pip install modal")

            # Modal token
            print()
            print_info("Modal 认证：")
            print_info("  获取您的令牌：https://modal.com/settings")
            existing_token = get_env_value("MODAL_TOKEN_ID")
            if existing_token:
                print_info("  Modal 令牌：已配置")
                if prompt_yes_no("  更新 Modal 凭证？", False):
                    token_id = prompt("    Modal 令牌 ID", password=True)
                    token_secret = prompt("    Modal 令牌密钥", password=True)
                    if token_id:
                        save_env_value("MODAL_TOKEN_ID", token_id)
                    if token_secret:
                        save_env_value("MODAL_TOKEN_SECRET", token_secret)
            else:
                token_id = prompt("    Modal 令牌 ID", password=True)
                token_secret = prompt("    Modal 令牌密钥", password=True)
                if token_id:
                    save_env_value("MODAL_TOKEN_ID", token_id)
                if token_secret:
                    save_env_value("MODAL_TOKEN_SECRET", token_secret)

        _prompt_container_resources(config)

    elif selected_backend == "daytona":
        print_success("终端后端：Daytona")
        print_info("持久化云开发环境。")
        print_info("每个会话获得具有文件系统持久化的专用沙箱。")
        print_info("注册地址：https://daytona.io")

        # Check if daytona SDK is installed
        try:
            __import__("daytona")
        except ImportError:
            print_info("正在安装 daytona SDK...")
            import subprocess

            uv_bin = shutil.which("uv")
            if uv_bin:
                result = subprocess.run(
                    [uv_bin, "pip", "install", "--python", sys.executable, "daytona"],
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "daytona"],
                    capture_output=True,
                    text=True,
                )
            if result.returncode == 0:
                print_success("daytona SDK 已安装")
            else:
                print_warning("安装失败 — 手动运行：pip install daytona")
                if result.stderr:
                    print_info(f"  错误：{result.stderr.strip().splitlines()[-1]}")

        # Daytona API key
        print()
        existing_key = get_env_value("DAYTONA_API_KEY")
        if existing_key:
            print_info("  Daytona API 密钥：已配置")
            if prompt_yes_no("  更新 API 密钥？", False):
                api_key = prompt("    Daytona API 密钥", password=True)
                if api_key:
                    save_env_value("DAYTONA_API_KEY", api_key)
                    print_success("    已更新")
        else:
            api_key = prompt("    Daytona API 密钥", password=True)
            if api_key:
                save_env_value("DAYTONA_API_KEY", api_key)
                print_success("    已配置")

        # Daytona image
        current_image = config.get("terminal", {}).get(
            "daytona_image", "nikolaik/python-nodejs:python3.11-nodejs20"
        )
        image = prompt("  沙箱镜像", current_image)
        config["terminal"]["daytona_image"] = image
        save_env_value("TERMINAL_DAYTONA_IMAGE", image)

        _prompt_container_resources(config)

    elif selected_backend == "ssh":
        print_success("终端后端：SSH")
        print_info("通过 SSH 在远程机器上运行命令。")

        # SSH host
        current_host = get_env_value("TERMINAL_SSH_HOST") or ""
        host = prompt("  SSH 主机（主机名或 IP）", current_host)
        if host:
            save_env_value("TERMINAL_SSH_HOST", host)

        # SSH user
        current_user = get_env_value("TERMINAL_SSH_USER") or ""
        user = prompt("  SSH 用户", current_user or os.getenv("USER", ""))
        if user:
            save_env_value("TERMINAL_SSH_USER", user)

        # SSH port
        current_port = get_env_value("TERMINAL_SSH_PORT") or "22"
        port = prompt("  SSH 端口", current_port)
        if port and port != "22":
            save_env_value("TERMINAL_SSH_PORT", port)

        # SSH key
        current_key = get_env_value("TERMINAL_SSH_KEY") or ""
        default_key = str(Path.home() / ".ssh" / "id_rsa")
        ssh_key = prompt("  SSH 私钥路径", current_key or default_key)
        if ssh_key:
            save_env_value("TERMINAL_SSH_KEY", ssh_key)

        # Test connection
        if host and prompt_yes_no("  测试 SSH 连接？", True):
            print_info("  正在测试连接...")
            import subprocess

            ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
            if ssh_key:
                ssh_cmd.extend(["-i", ssh_key])
            if port and port != "22":
                ssh_cmd.extend(["-p", port])
            ssh_cmd.append(f"{user}@{host}" if user else host)
            ssh_cmd.append("echo ok")
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_success("  SSH 连接成功！")
            else:
                print_warning(f"  SSH 连接失败：{result.stderr.strip()}")
                print_info("  检查您的 SSH 密钥和主机设置。")

    # Sync terminal backend to .env so terminal_tool picks it up directly.
    # config.yaml is the source of truth, but terminal_tool reads TERMINAL_ENV.
    save_env_value("TERMINAL_ENV", selected_backend)
    if selected_backend == "modal":
        save_env_value("TERMINAL_MODAL_MODE", config["terminal"].get("modal_mode", "auto"))
    save_config(config)
    print()
    print_success(f"终端后端已设置为：{selected_backend}")


# =============================================================================
# Section 3: Agent Settings
# =============================================================================


def _apply_default_agent_settings(config: dict):
    """Apply recommended defaults for all agent settings without prompting."""
    config.setdefault("agent", {})["max_turns"] = 90
    save_env_value("HERMES_MAX_ITERATIONS", "90")

    config.setdefault("display", {})["tool_progress"] = "all"

    config.setdefault("compression", {})["enabled"] = True
    config["compression"]["threshold"] = 0.50

    config.setdefault("session_reset", {}).update({
        "mode": "both",
        "idle_minutes": 1440,
        "at_hour": 4,
    })

    save_config(config)
    print_success("已应用推荐默认值：")
    print_info("  最大迭代次数：90")
    print_info("  工具进度：all")
    print_info("  压缩阈值：0.50")
    print_info("  会话重置：不活动（1440 分钟）+ 每日（4:00）")
    print_info("  稍后运行 `hermes setup agent` 自定义。")


def setup_agent_settings(config: dict):
    """Configure agent behavior: iterations, progress display, compression, session reset."""

    print_header("代理设置")
    print_info(f"   指南：{_DOCS_BASE}/user-guide/configuration")
    print()

    # ── Max Iterations ──
    current_max = get_env_value("HERMES_MAX_ITERATIONS") or str(
        config.get("agent", {}).get("max_turns", 90)
    )
    print_info("每次对话的最大工具调用迭代次数。")
    print_info("数值越高 = 可处理更复杂的任务，但消耗更多 token。")
    print_info("默认值为 90，适用于大多数任务。探索性任务可使用 150+。")

    max_iter_str = prompt("最大迭代次数", current_max)
    try:
        max_iter = int(max_iter_str)
        if max_iter > 0:
            save_env_value("HERMES_MAX_ITERATIONS", str(max_iter))
            config.setdefault("agent", {})["max_turns"] = max_iter
            config.pop("max_turns", None)
            print_success(f"最大迭代次数已设置为 {max_iter}")
    except ValueError:
        print_warning("无效数字，保持当前值")

    # ── Tool Progress Display ──
    print_info("")
    print_info("工具进度显示")
    print_info("控制显示多少工具活动（CLI 和消息模式）。")
    print_info("  off     — 静默，仅显示最终响应")
    print_info("  new     — 仅在工具更改时显示工具名称（减少干扰）")
    print_info("  all     — 显示每次工具调用及简短预览")
    print_info("  verbose — 完整参数、结果和调试日志")

    current_mode = config.get("display", {}).get("tool_progress", "all")
    mode = prompt("工具进度模式", current_mode)
    if mode.lower() in ("off", "new", "all", "verbose"):
        if "display" not in config:
            config["display"] = {}
        config["display"]["tool_progress"] = mode.lower()
        save_config(config)
        print_success(f"工具进度已设置为：{mode.lower()}")
    else:
        print_warning(f"未知模式 '{mode}'，保持 '{current_mode}'")

    # ── Context Compression ──
    print_header("上下文压缩")
    print_info("当上下文过长时自动总结旧消息。")
    print_info(
        "阈值越高 = 压缩越晚（使用更多上下文）。阈值越低 = 压缩越早。"
    )

    config.setdefault("compression", {})["enabled"] = True

    current_threshold = config.get("compression", {}).get("threshold", 0.50)
    threshold_str = prompt("Compression threshold (0.5-0.95)", str(current_threshold))
    try:
        threshold = float(threshold_str)
        if 0.5 <= threshold <= 0.95:
            config["compression"]["threshold"] = threshold
    except ValueError:
        pass

    print_success(
        f"上下文压缩阈值已设置为 {config['compression'].get('threshold', 0.50)}"
    )

    # ── Session Reset Policy ──
    print_header("会话重置策略")
    print_info(
        "消息会话（Telegram、Discord 等）会随时间累积上下文。"
    )
    print_info(
        "每条消息都会添加到对话历史中，这意味着 API 成本会增加。"
    )
    print_info("")
    print_info(
        "为了管理这个问题，会话可以在一段时间不活动后自动重置"
    )
    print_info(
        "或在每天固定时间重置。当重置发生时，代理会先将重要内容"
    )
    print_info(
        "保存到持久化内存中 — 但对话上下文会被清除。"
    )
    print_info("")
    print_info("您也可以随时在聊天中输入 /reset 手动重置。")
    print_info("")

    reset_choices = [
        "不活动 + 每日重置（推荐 - 哪个先发生就重置哪个）",
        "仅不活动（在 N 分钟无消息后重置）",
        "仅每日（每天固定时间重置）",
        "永不自动重置（上下文持续直到 /reset 或上下文压缩）",
        "保持当前设置",
    ]

    current_policy = config.get("session_reset", {})
    current_mode = current_policy.get("mode", "both")
    current_idle = current_policy.get("idle_minutes", 1440)
    current_hour = current_policy.get("at_hour", 4)

    default_reset = {"both": 0, "idle": 1, "daily": 2, "none": 3}.get(current_mode, 0)

    reset_idx = prompt_choice("会话重置模式：", reset_choices, default_reset)

    config.setdefault("session_reset", {})

    if reset_idx == 0:  # Both
        config["session_reset"]["mode"] = "both"
        idle_str = prompt("  不活动超时（分钟）", str(current_idle))
        try:
            idle_val = int(idle_str)
            if idle_val > 0:
                config["session_reset"]["idle_minutes"] = idle_val
        except ValueError:
            pass
        hour_str = prompt("  每日重置时间（0-23，本地时间）", str(current_hour))
        try:
            hour_val = int(hour_str)
            if 0 <= hour_val <= 23:
                config["session_reset"]["at_hour"] = hour_val
        except ValueError:
            pass
        print_success(
            f"会话在 {config['session_reset'].get('idle_minutes', 1440)} 分钟不活动后或每天 {config['session_reset'].get('at_hour', 4)}:00 重置"
        )
    elif reset_idx == 1:  # Idle only
        config["session_reset"]["mode"] = "idle"
        idle_str = prompt("  不活动超时（分钟）", str(current_idle))
        try:
            idle_val = int(idle_str)
            if idle_val > 0:
                config["session_reset"]["idle_minutes"] = idle_val
        except ValueError:
            pass
        print_success(
            f"会话在 {config['session_reset'].get('idle_minutes', 1440)} 分钟不活动后重置"
        )
    elif reset_idx == 2:  # Daily only
        config["session_reset"]["mode"] = "daily"
        hour_str = prompt("  每日重置时间（0-23，本地时间）", str(current_hour))
        try:
            hour_val = int(hour_str)
            if 0 <= hour_val <= 23:
                config["session_reset"]["at_hour"] = hour_val
        except ValueError:
            pass
        print_success(
            f"会话每天在 {config['session_reset'].get('at_hour', 4)}:00 重置"
        )
    elif reset_idx == 3:  # None
        config["session_reset"]["mode"] = "none"
        print_info(
            "会话将永不自动重置。上下文仅通过压缩管理。"
        )
        print_warning(
            "长对话会增加成本。需要时使用 /reset 手动重置。"
        )
    # else: keep current (idx == 4)

    save_config(config)


# =============================================================================
# Section 4: Messaging Platforms (Gateway)
# =============================================================================


def _setup_telegram():
    """Configure Telegram bot credentials and allowlist."""
    print_header("Telegram")
    existing = get_env_value("TELEGRAM_BOT_TOKEN")
    if existing:
        print_info("Telegram: already configured")
        if not prompt_yes_no("Reconfigure Telegram?", False):
            # Check missing allowlist on existing config
            if not get_env_value("TELEGRAM_ALLOWED_USERS"):
                print_info("⚠️  Telegram has no user allowlist - anyone can use your bot!")
                if prompt_yes_no("Add allowed users now?", True):
                    print_info("   To find your Telegram user ID: message @userinfobot")
                    allowed_users = prompt("Allowed user IDs (comma-separated)")
                    if allowed_users:
                        save_env_value("TELEGRAM_ALLOWED_USERS", allowed_users.replace(" ", ""))
                        print_success("Telegram allowlist configured")
            return

    print_info("Create a bot via @BotFather on Telegram")
    import re

    while True:
        token = prompt("Telegram bot token", password=True)
        if not token:
            return
        if not re.match(r"^\d+:[A-Za-z0-9_-]{30,}$", token):
            print_error(
                "Invalid token format. Expected: <numeric_id>:<alphanumeric_hash> "
                "(e.g., 123456789:ABCdefGHI-jklMNOpqrSTUvwxYZ)"
            )
            continue
        break
    save_env_value("TELEGRAM_BOT_TOKEN", token)
    print_success("Telegram token saved")

    print()
    print_info("🔒 Security: Restrict who can use your bot")
    print_info("   To find your Telegram user ID:")
    print_info("   1. Message @userinfobot on Telegram")
    print_info("   2. It will reply with your numeric ID (e.g., 123456789)")
    print()
    allowed_users = prompt(
        "Allowed user IDs (comma-separated, leave empty for open access)"
    )
    if allowed_users:
        save_env_value("TELEGRAM_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("Telegram allowlist configured - only listed users can use the bot")
    else:
        print_info("⚠️  No allowlist set - anyone who finds your bot can use it!")

    print()
    print_info("📬 Home Channel: where Hermes delivers cron job results,")
    print_info("   cross-platform messages, and notifications.")
    print_info("   For Telegram DMs, this is your user ID (same as above).")

    first_user_id = allowed_users.split(",")[0].strip() if allowed_users else ""
    if first_user_id:
        if prompt_yes_no(f"Use your user ID ({first_user_id}) as the home channel?", True):
            save_env_value("TELEGRAM_HOME_CHANNEL", first_user_id)
            print_success(f"Telegram home channel set to {first_user_id}")
        else:
            home_channel = prompt("Home channel ID (or leave empty to set later with /set-home in Telegram)")
            if home_channel:
                save_env_value("TELEGRAM_HOME_CHANNEL", home_channel)
    else:
        print_info("   You can also set this later by typing /set-home in your Telegram chat.")
        home_channel = prompt("Home channel ID (leave empty to set later)")
        if home_channel:
            save_env_value("TELEGRAM_HOME_CHANNEL", home_channel)


def _setup_discord():
    """Configure Discord bot credentials and allowlist."""
    print_header("Discord")
    existing = get_env_value("DISCORD_BOT_TOKEN")
    if existing:
        print_info("Discord: already configured")
        if not prompt_yes_no("Reconfigure Discord?", False):
            if not get_env_value("DISCORD_ALLOWED_USERS"):
                print_info("⚠️  Discord has no user allowlist - anyone can use your bot!")
                if prompt_yes_no("Add allowed users now?", True):
                    print_info("   To find Discord ID: Enable Developer Mode, right-click name → Copy ID")
                    allowed_users = prompt("Allowed user IDs (comma-separated)")
                    if allowed_users:
                        cleaned_ids = _clean_discord_user_ids(allowed_users)
                        save_env_value("DISCORD_ALLOWED_USERS", ",".join(cleaned_ids))
                        print_success("Discord allowlist configured")
            return

    print_info("Create a bot at https://discord.com/developers/applications")
    token = prompt("Discord bot token", password=True)
    if not token:
        return
    save_env_value("DISCORD_BOT_TOKEN", token)
    print_success("Discord token saved")

    print()
    print_info("🔒 Security: Restrict who can use your bot")
    print_info("   To find your Discord user ID:")
    print_info("   1. Enable Developer Mode in Discord settings")
    print_info("   2. Right-click your name → Copy ID")
    print()
    print_info("   You can also use Discord usernames (resolved on gateway start).")
    print()
    allowed_users = prompt(
        "Allowed user IDs or usernames (comma-separated, leave empty for open access)"
    )
    if allowed_users:
        cleaned_ids = _clean_discord_user_ids(allowed_users)
        save_env_value("DISCORD_ALLOWED_USERS", ",".join(cleaned_ids))
        print_success("Discord allowlist configured")
    else:
        print_info("⚠️  No allowlist set - anyone in servers with your bot can use it!")

    print()
    print_info("📬 Home Channel: where Hermes delivers cron job results,")
    print_info("   cross-platform messages, and notifications.")
    print_info("   To get a channel ID: right-click a channel → Copy Channel ID")
    print_info("   (requires Developer Mode in Discord settings)")
    print_info("   You can also set this later by typing /set-home in a Discord channel.")
    home_channel = prompt("Home channel ID (leave empty to set later with /set-home)")
    if home_channel:
        save_env_value("DISCORD_HOME_CHANNEL", home_channel)


def _clean_discord_user_ids(raw: str) -> list:
    """Strip common Discord mention prefixes from a comma-separated ID string."""
    cleaned = []
    for uid in raw.replace(" ", "").split(","):
        uid = uid.strip()
        if uid.startswith("<@") and uid.endswith(">"):
            uid = uid.lstrip("<@!").rstrip(">")
        if uid.lower().startswith("user:"):
            uid = uid[5:]
        if uid:
            cleaned.append(uid)
    return cleaned


def _setup_slack():
    """Configure Slack bot credentials."""
    print_header("Slack")
    existing = get_env_value("SLACK_BOT_TOKEN")
    if existing:
        print_info("Slack: already configured")
        if not prompt_yes_no("Reconfigure Slack?", False):
            return

    print_info("Steps to create a Slack app:")
    print_info("   1. Go to https://api.slack.com/apps → Create New App (from scratch)")
    print_info("   2. Enable Socket Mode: Settings → Socket Mode → Enable")
    print_info("      • Create an App-Level Token with 'connections:write' scope")
    print_info("   3. Add Bot Token Scopes: Features → OAuth & Permissions")
    print_info("      Required scopes: chat:write, app_mentions:read,")
    print_info("      channels:history, channels:read, im:history,")
    print_info("      im:read, im:write, users:read, files:read, files:write")
    print_info("      Optional for private channels: groups:history")
    print_info("   4. Subscribe to Events: Features → Event Subscriptions → Enable")
    print_info("      Required events: message.im, message.channels, app_mention")
    print_info("      Optional for private channels: message.groups")
    print_warning("   ⚠ Without message.channels the bot will ONLY work in DMs,")
    print_warning("     not public channels.")
    print_info("   5. Install to Workspace: Settings → Install App")
    print_info("   6. Reinstall the app after any scope or event changes")
    print_info("   7. After installing, invite the bot to channels: /invite @YourBot")
    print()
    print_info("   Full guide: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/slack/")
    print()
    bot_token = prompt("Slack Bot Token (xoxb-...)", password=True)
    if not bot_token:
        return
    save_env_value("SLACK_BOT_TOKEN", bot_token)
    app_token = prompt("Slack App Token (xapp-...)", password=True)
    if app_token:
        save_env_value("SLACK_APP_TOKEN", app_token)
    print_success("Slack tokens saved")

    print()
    print_info("🔒 Security: Restrict who can use your bot")
    print_info("   To find a Member ID: click a user's name → View full profile → ⋮ → Copy member ID")
    print()
    allowed_users = prompt(
        "Allowed user IDs (comma-separated, leave empty to deny everyone except paired users)"
    )
    if allowed_users:
        save_env_value("SLACK_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("Slack allowlist configured")
    else:
        print_warning("⚠️  No Slack allowlist set - unpaired users will be denied by default.")
        print_info("   Set SLACK_ALLOW_ALL_USERS=true or GATEWAY_ALLOW_ALL_USERS=true only if you intentionally want open workspace access.")


def _setup_matrix():
    """Configure Matrix credentials."""
    print_header("Matrix")
    existing = get_env_value("MATRIX_ACCESS_TOKEN") or get_env_value("MATRIX_PASSWORD")
    if existing:
        print_info("Matrix: already configured")
        if not prompt_yes_no("Reconfigure Matrix?", False):
            return

    print_info("Works with any Matrix homeserver (Synapse, Conduit, Dendrite, or matrix.org).")
    print_info("   1. Create a bot user on your homeserver, or use your own account")
    print_info("   2. Get an access token from Element, or provide user ID + password")
    print()
    homeserver = prompt("Homeserver URL (e.g. https://matrix.example.org)")
    if homeserver:
        save_env_value("MATRIX_HOMESERVER", homeserver.rstrip("/"))

    print()
    print_info("Auth: provide an access token (recommended), or user ID + password.")
    token = prompt("Access token (leave empty for password login)", password=True)
    if token:
        save_env_value("MATRIX_ACCESS_TOKEN", token)
        user_id = prompt("User ID (@bot:server — optional, will be auto-detected)")
        if user_id:
            save_env_value("MATRIX_USER_ID", user_id)
        print_success("Matrix access token saved")
    else:
        user_id = prompt("User ID (@bot:server)")
        if user_id:
            save_env_value("MATRIX_USER_ID", user_id)
        password = prompt("Password", password=True)
        if password:
            save_env_value("MATRIX_PASSWORD", password)
            print_success("Matrix credentials saved")

    if token or get_env_value("MATRIX_PASSWORD"):
        print()
        want_e2ee = prompt_yes_no("Enable end-to-end encryption (E2EE)?", False)
        if want_e2ee:
            save_env_value("MATRIX_ENCRYPTION", "true")
            print_success("E2EE enabled")

        matrix_pkg = "mautrix[encryption]" if want_e2ee else "mautrix"
        try:
            __import__("mautrix")
        except ImportError:
            print_info(f"Installing {matrix_pkg}...")
            import subprocess
            uv_bin = shutil.which("uv")
            if uv_bin:
                result = subprocess.run(
                    [uv_bin, "pip", "install", "--python", sys.executable, matrix_pkg],
                    capture_output=True, text=True,
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", matrix_pkg],
                    capture_output=True, text=True,
                )
            if result.returncode == 0:
                print_success(f"{matrix_pkg} installed")
            else:
                print_warning(f"Install failed — run manually: pip install '{matrix_pkg}'")
                if result.stderr:
                    print_info(f"  Error: {result.stderr.strip().splitlines()[-1]}")

        print()
        print_info("🔒 Security: Restrict who can use your bot")
        print_info("   Matrix user IDs look like @username:server")
        print()
        allowed_users = prompt("Allowed user IDs (comma-separated, leave empty for open access)")
        if allowed_users:
            save_env_value("MATRIX_ALLOWED_USERS", allowed_users.replace(" ", ""))
            print_success("Matrix allowlist configured")
        else:
            print_info("⚠️  No allowlist set - anyone who can message the bot can use it!")

        print()
        print_info("📬 Home Room: where Hermes delivers cron job results and notifications.")
        print_info("   Room IDs look like !abc123:server (shown in Element room settings)")
        print_info("   You can also set this later by typing /set-home in a Matrix room.")
        home_room = prompt("Home room ID (leave empty to set later with /set-home)")
        if home_room:
            save_env_value("MATRIX_HOME_ROOM", home_room)


def _setup_mattermost():
    """Configure Mattermost bot credentials."""
    print_header("Mattermost")
    existing = get_env_value("MATTERMOST_TOKEN")
    if existing:
        print_info("Mattermost: already configured")
        if not prompt_yes_no("Reconfigure Mattermost?", False):
            return

    print_info("Works with any self-hosted Mattermost instance.")
    print_info("   1. In Mattermost: Integrations → Bot Accounts → Add Bot Account")
    print_info("   2. Copy the bot token")
    print()
    mm_url = prompt("Mattermost server URL (e.g. https://mm.example.com)")
    if mm_url:
        save_env_value("MATTERMOST_URL", mm_url.rstrip("/"))
    token = prompt("Bot token", password=True)
    if not token:
        return
    save_env_value("MATTERMOST_TOKEN", token)
    print_success("Mattermost token saved")

    print()
    print_info("🔒 Security: Restrict who can use your bot")
    print_info("   To find your user ID: click your avatar → Profile")
    print_info("   or use the API: GET /api/v4/users/me")
    print()
    allowed_users = prompt("Allowed user IDs (comma-separated, leave empty for open access)")
    if allowed_users:
        save_env_value("MATTERMOST_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("Mattermost allowlist configured")
    else:
        print_info("⚠️  No allowlist set - anyone who can message the bot can use it!")

    print()
    print_info("📬 Home Channel: where Hermes delivers cron job results and notifications.")
    print_info("   To get a channel ID: click channel name → View Info → copy the ID")
    print_info("   You can also set this later by typing /set-home in a Mattermost channel.")
    home_channel = prompt("Home channel ID (leave empty to set later with /set-home)")
    if home_channel:
        save_env_value("MATTERMOST_HOME_CHANNEL", home_channel)


def _setup_whatsapp():
    """Configure WhatsApp bridge."""
    print_header("WhatsApp")
    existing = get_env_value("WHATSAPP_ENABLED")
    if existing:
        print_info("WhatsApp: already enabled")
        return

    print_info("WhatsApp connects via a built-in bridge (Baileys).")
    print_info("Requires Node.js. Run 'hermes whatsapp' for guided setup.")
    print()
    if prompt_yes_no("Enable WhatsApp now?", True):
        save_env_value("WHATSAPP_ENABLED", "true")
        print_success("WhatsApp enabled")
        print_info("Run 'hermes whatsapp' to choose your mode (separate bot number")
        print_info("or personal self-chat) and pair via QR code.")


def _setup_weixin():
    """Configure Weixin (personal WeChat) via iLink Bot API QR login."""
    from hermes_cli.gateway import _setup_weixin as _gateway_setup_weixin
    _gateway_setup_weixin()


def _setup_signal():
    """Configure Signal via gateway setup."""
    from hermes_cli.gateway import _setup_signal as _gateway_setup_signal
    _gateway_setup_signal()


def _setup_email():
    """Configure Email via gateway setup."""
    from hermes_cli.gateway import _setup_email as _gateway_setup_email
    _gateway_setup_email()


def _setup_sms():
    """Configure SMS (Twilio) via gateway setup."""
    from hermes_cli.gateway import _setup_sms as _gateway_setup_sms
    _gateway_setup_sms()


def _setup_dingtalk():
    """Configure DingTalk via gateway setup."""
    from hermes_cli.gateway import _setup_dingtalk as _gateway_setup_dingtalk
    _gateway_setup_dingtalk()


def _setup_feishu():
    """Configure Feishu / Lark via gateway setup."""
    from hermes_cli.gateway import _setup_feishu as _gateway_setup_feishu
    _gateway_setup_feishu()


def _setup_wecom():
    """Configure WeCom (Enterprise WeChat) via gateway setup."""
    from hermes_cli.gateway import _setup_wecom as _gateway_setup_wecom
    _gateway_setup_wecom()


def _setup_wecom_callback():
    """Configure WeCom Callback (self-built app) via gateway setup."""
    from hermes_cli.gateway import _setup_wecom_callback as _gw_setup
    _gw_setup()


def _setup_qqbot():
    """Configure QQ Bot gateway."""
    print_header("QQ Bot")
    existing = get_env_value("QQ_APP_ID")
    if existing:
        print_info("QQ Bot: already configured")
        if not prompt_yes_no("Reconfigure QQ Bot?", False):
            return

    print_info("Connects Hermes to QQ via the Official QQ Bot API (v2).")
    print_info("   Requires a QQ Bot application at q.qq.com")
    print_info("   Reference: https://bot.q.qq.com/wiki/develop/api-v2/")
    print()

    app_id = prompt("QQ Bot App ID")
    if not app_id:
        print_warning("App ID is required — skipping QQ Bot setup")
        return
    save_env_value("QQ_APP_ID", app_id.strip())

    client_secret = prompt("QQ Bot App Secret", password=True)
    if not client_secret:
        print_warning("App Secret is required — skipping QQ Bot setup")
        return
    save_env_value("QQ_CLIENT_SECRET", client_secret)
    print_success("QQ Bot credentials saved")

    print()
    print_info("🔒 Security: Restrict who can DM your bot")
    print_info("   Use QQ user OpenIDs (found in event payloads)")
    print()
    allowed_users = prompt("Allowed user OpenIDs (comma-separated, leave empty for open access)")
    if allowed_users:
        save_env_value("QQ_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("QQ Bot allowlist configured")
    else:
        print_info("⚠️  No allowlist set — anyone can DM the bot!")

    print()
    print_info("📬 Home Channel: OpenID for cron job delivery and notifications.")
    home_channel = prompt("Home channel OpenID (leave empty to set later)")
    if home_channel:
        save_env_value("QQ_HOME_CHANNEL", home_channel)

    print()
    print_success("QQ Bot configured!")


def _setup_bluebubbles():
    """Configure BlueBubbles iMessage gateway."""
    print_header("BlueBubbles (iMessage)")
    existing = get_env_value("BLUEBUBBLES_SERVER_URL")
    if existing:
        print_info("BlueBubbles: already configured")
        if not prompt_yes_no("Reconfigure BlueBubbles?", False):
            return

    print_info("Connects Hermes to iMessage via BlueBubbles — a free, open-source")
    print_info("macOS server that bridges iMessage to any device.")
    print_info("   Requires a Mac running BlueBubbles Server v1.0.0+")
    print_info("   Download: https://bluebubbles.app/")
    print()
    print_info("In BlueBubbles Server → Settings → API, note your Server URL and Password.")
    print()

    server_url = prompt("BlueBubbles server URL (e.g. http://192.168.1.10:1234)")
    if not server_url:
        print_warning("Server URL is required — skipping BlueBubbles setup")
        return
    save_env_value("BLUEBUBBLES_SERVER_URL", server_url.rstrip("/"))

    password = prompt("BlueBubbles server password", password=True)
    if not password:
        print_warning("Password is required — skipping BlueBubbles setup")
        return
    save_env_value("BLUEBUBBLES_PASSWORD", password)
    print_success("BlueBubbles credentials saved")

    print()
    print_info("🔒 Security: Restrict who can message your bot")
    print_info("   Use iMessage addresses: email (user@icloud.com) or phone (+15551234567)")
    print()
    allowed_users = prompt("Allowed iMessage addresses (comma-separated, leave empty for open access)")
    if allowed_users:
        save_env_value("BLUEBUBBLES_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("BlueBubbles allowlist configured")
    else:
        print_info("⚠️  No allowlist set — anyone who can iMessage you can use the bot!")

    print()
    print_info("📬 Home Channel: phone or email for cron job delivery and notifications.")
    print_info("   You can also set this later with /set-home in your iMessage chat.")
    home_channel = prompt("Home channel address (leave empty to set later)")
    if home_channel:
        save_env_value("BLUEBUBBLES_HOME_CHANNEL", home_channel)

    print()
    print_info("Advanced settings (defaults are fine for most setups):")
    if prompt_yes_no("Configure webhook listener settings?", False):
        webhook_port = prompt("Webhook listener port (default: 8645)")
        if webhook_port:
            try:
                save_env_value("BLUEBUBBLES_WEBHOOK_PORT", str(int(webhook_port)))
                print_success(f"Webhook port set to {webhook_port}")
            except ValueError:
                print_warning("Invalid port number, using default 8645")

    print()
    print_info("Requires the BlueBubbles Private API helper for typing indicators,")
    print_info("read receipts, and tapback reactions. Basic messaging works without it.")
    print_info("   Install: https://docs.bluebubbles.app/helper-bundle/installation")


def _setup_qqbot():
    """Configure QQ Bot (Official API v2) via standard platform setup."""
    from hermes_cli.gateway import _PLATFORMS
    qq_platform = next((p for p in _PLATFORMS if p["key"] == "qqbot"), None)
    if qq_platform:
        from hermes_cli.gateway import _setup_standard_platform
        _setup_standard_platform(qq_platform)


def _setup_webhooks():
    """Configure webhook integration."""
    print_header("Webhooks")
    existing = get_env_value("WEBHOOK_ENABLED")
    if existing:
        print_info("Webhooks: already configured")
        if not prompt_yes_no("Reconfigure webhooks?", False):
            return

    print()
    print_warning("⚠  Webhook and SMS platforms require exposing gateway ports to the")
    print_warning("   internet. For security, run the gateway in a sandboxed environment")
    print_warning("   (Docker, VM, etc.) to limit blast radius from prompt injection.")
    print()
    print_info("   Full guide: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks/")
    print()

    port = prompt("Webhook port (default 8644)")
    if port:
        try:
            save_env_value("WEBHOOK_PORT", str(int(port)))
            print_success(f"Webhook port set to {port}")
        except ValueError:
            print_warning("Invalid port number, using default 8644")

    secret = prompt("Global HMAC secret (shared across all routes)", password=True)
    if secret:
        save_env_value("WEBHOOK_SECRET", secret)
        print_success("Webhook secret saved")
    else:
        print_warning("No secret set — you must configure per-route secrets in config.yaml")

    save_env_value("WEBHOOK_ENABLED", "true")
    print()
    print_success("Webhooks enabled! Next steps:")
    from hermes_constants import display_hermes_home as _dhh
    print_info(f"   1. Define webhook routes in {_dhh()}/config.yaml")
    print_info("   2. Point your service (GitHub, GitLab, etc.) at:")
    print_info("      http://your-server:8644/webhooks/<route-name>")
    print()
    print_info("   Route configuration guide:")
    print_info("   https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks/#configuring-routes")
    print()
    print_info("   Open config in your editor:  hermes config edit")


# Platform registry for the gateway checklist
_GATEWAY_PLATFORMS = [
    ("Telegram", "TELEGRAM_BOT_TOKEN", _setup_telegram),
    ("Discord", "DISCORD_BOT_TOKEN", _setup_discord),
    ("Slack", "SLACK_BOT_TOKEN", _setup_slack),
    ("Signal", "SIGNAL_HTTP_URL", _setup_signal),
    ("Email", "EMAIL_ADDRESS", _setup_email),
    ("SMS (Twilio)", "TWILIO_ACCOUNT_SID", _setup_sms),
    ("Matrix", "MATRIX_ACCESS_TOKEN", _setup_matrix),
    ("Mattermost", "MATTERMOST_TOKEN", _setup_mattermost),
    ("WhatsApp", "WHATSAPP_ENABLED", _setup_whatsapp),
    ("DingTalk", "DINGTALK_CLIENT_ID", _setup_dingtalk),
    ("Feishu / Lark", "FEISHU_APP_ID", _setup_feishu),
    ("WeCom (Enterprise WeChat)", "WECOM_BOT_ID", _setup_wecom),
    ("WeCom Callback (Self-Built App)", "WECOM_CALLBACK_CORP_ID", _setup_wecom_callback),
    ("Weixin (WeChat)", "WEIXIN_ACCOUNT_ID", _setup_weixin),
    ("BlueBubbles (iMessage)", "BLUEBUBBLES_SERVER_URL", _setup_bluebubbles),
    ("QQ Bot", "QQ_APP_ID", _setup_qqbot),
    ("Webhooks (GitHub, GitLab, etc.)", "WEBHOOK_ENABLED", _setup_webhooks),
]


def setup_gateway(config: dict):
    """Configure messaging platform integrations."""
    print_header("Messaging Platforms")
    print_info("Connect to messaging platforms to chat with Hermes from anywhere.")
    print_info("Toggle with Space, confirm with Enter.")
    print()

    # Build checklist items, pre-selecting already-configured platforms
    items = []
    pre_selected = []
    for i, (name, env_var, _func) in enumerate(_GATEWAY_PLATFORMS):
        # Matrix has two possible env vars
        is_configured = bool(get_env_value(env_var))
        if name == "Matrix" and not is_configured:
            is_configured = bool(get_env_value("MATRIX_PASSWORD"))
        label = f"{name}  (configured)" if is_configured else name
        items.append(label)
        if is_configured:
            pre_selected.append(i)

    selected = prompt_checklist("Select platforms to configure:", items, pre_selected)

    if not selected:
        print_info("No platforms selected. Run 'hermes setup gateway' later to configure.")
        return

    for idx in selected:
        name, _env_var, setup_func = _GATEWAY_PLATFORMS[idx]
        setup_func()

    # ── Gateway Service Setup ──
    any_messaging = (
        get_env_value("TELEGRAM_BOT_TOKEN")
        or get_env_value("DISCORD_BOT_TOKEN")
        or get_env_value("SLACK_BOT_TOKEN")
        or get_env_value("SIGNAL_HTTP_URL")
        or get_env_value("EMAIL_ADDRESS")
        or get_env_value("TWILIO_ACCOUNT_SID")
        or get_env_value("MATTERMOST_TOKEN")
        or get_env_value("MATRIX_ACCESS_TOKEN")
        or get_env_value("MATRIX_PASSWORD")
        or get_env_value("WHATSAPP_ENABLED")
        or get_env_value("DINGTALK_CLIENT_ID")
        or get_env_value("FEISHU_APP_ID")
        or get_env_value("WECOM_BOT_ID")
        or get_env_value("WEIXIN_ACCOUNT_ID")
        or get_env_value("BLUEBUBBLES_SERVER_URL")
        or get_env_value("QQ_APP_ID")
        or get_env_value("WEBHOOK_ENABLED")
    )
    if any_messaging:
        print()
        print_info("━" * 50)
        print_success("Messaging platforms configured!")

        # Check if any home channels are missing
        missing_home = []
        if get_env_value("TELEGRAM_BOT_TOKEN") and not get_env_value(
            "TELEGRAM_HOME_CHANNEL"
        ):
            missing_home.append("Telegram")
        if get_env_value("DISCORD_BOT_TOKEN") and not get_env_value(
            "DISCORD_HOME_CHANNEL"
        ):
            missing_home.append("Discord")
        if get_env_value("SLACK_BOT_TOKEN") and not get_env_value("SLACK_HOME_CHANNEL"):
            missing_home.append("Slack")
        if get_env_value("BLUEBUBBLES_SERVER_URL") and not get_env_value("BLUEBUBBLES_HOME_CHANNEL"):
            missing_home.append("BlueBubbles")
        if get_env_value("QQ_APP_ID") and not get_env_value("QQ_HOME_CHANNEL"):
            missing_home.append("QQBot")

        if missing_home:
            print()
            print_warning(f"No home channel set for: {', '.join(missing_home)}")
            print_info("   Without a home channel, cron jobs and cross-platform")
            print_info("   messages can't be delivered to those platforms.")
            print_info("   Set one later with /set-home in your chat, or:")
            for plat in missing_home:
                print_info(
                    f"     hermes config set {plat.upper()}_HOME_CHANNEL <channel_id>"
                )

        # Offer to install the gateway as a system service
        import platform as _platform

        _is_linux = _platform.system() == "Linux"
        _is_macos = _platform.system() == "Darwin"

        from hermes_cli.gateway import (
            _is_service_installed,
            _is_service_running,
            supports_systemd_services,
            has_conflicting_systemd_units,
            install_linux_gateway_from_setup,
            print_systemd_scope_conflict_warning,
            systemd_start,
            systemd_restart,
            launchd_install,
            launchd_start,
            launchd_restart,
        )

        service_installed = _is_service_installed()
        service_running = _is_service_running()
        supports_systemd = supports_systemd_services()
        supports_service_manager = supports_systemd or _is_macos

        print()
        if supports_systemd and has_conflicting_systemd_units():
            print_systemd_scope_conflict_warning()
            print()

        if service_running:
            if prompt_yes_no("  Restart the gateway to pick up changes?", True):
                try:
                    if supports_systemd:
                        systemd_restart()
                    elif _is_macos:
                        launchd_restart()
                except Exception as e:
                    print_error(f"  Restart failed: {e}")
        elif service_installed:
            if prompt_yes_no("  Start the gateway service?", True):
                try:
                    if supports_systemd:
                        systemd_start()
                    elif _is_macos:
                        launchd_start()
                except Exception as e:
                    print_error(f"  Start failed: {e}")
        elif supports_service_manager:
            svc_name = "systemd" if supports_systemd else "launchd"
            if prompt_yes_no(
                f"  Install the gateway as a {svc_name} service? (runs in background, starts on boot)",
                True,
            ):
                try:
                    installed_scope = None
                    did_install = False
                    if supports_systemd:
                        installed_scope, did_install = install_linux_gateway_from_setup(force=False)
                    else:
                        launchd_install(force=False)
                        did_install = True
                    print()
                    if did_install and prompt_yes_no("  Start the service now?", True):
                        try:
                            if supports_systemd:
                                systemd_start(system=installed_scope == "system")
                            elif _is_macos:
                                launchd_start()
                        except Exception as e:
                            print_error(f"  Start failed: {e}")
                except Exception as e:
                    print_error(f"  Install failed: {e}")
                    print_info("  You can try manually: hermes gateway install")
            else:
                print_info("  You can install later: hermes gateway install")
                if supports_systemd:
                    print_info("  Or as a boot-time service: sudo hermes gateway install --system")
                print_info("  Or run in foreground:  hermes gateway")
        else:
            from hermes_constants import is_container
            if is_container():
                print_info("Start the gateway to bring your bots online:")
                print_info("   hermes gateway run          # Run as container main process")
                print_info("")
                print_info("For automatic restarts, use a Docker restart policy:")
                print_info("   docker run --restart unless-stopped ...")
                print_info("   docker restart <container>  # Manual restart")
            else:
                print_info("Start the gateway to bring your bots online:")
                print_info("   hermes gateway              # Run in foreground")

        print_info("━" * 50)


# =============================================================================
# Section 5: Tool Configuration (delegates to unified tools_config.py)
# =============================================================================


def setup_tools(config: dict, first_install: bool = False):
    """Configure tools — delegates to the unified tools_command() in tools_config.py.

    Both `hermes setup tools` and `hermes tools` use the same flow:
    platform selection → toolset toggles → provider/API key configuration.

    Args:
        first_install: When True, uses the simplified first-install flow
            (no platform menu, prompts for all unconfigured API keys).
    """
    from hermes_cli.tools_config import tools_command

    tools_command(first_install=first_install, config=config)


# =============================================================================
# Post-Migration Section Skip Logic
# =============================================================================


def _get_section_config_summary(config: dict, section_key: str) -> Optional[str]:
    """Return a short summary if a setup section is already configured, else None.

    Used after OpenClaw migration to detect which sections can be skipped.
    ``get_env_value`` is the module-level import from hermes_cli.config
    so that test patches on ``setup_mod.get_env_value`` take effect.
    """
    if section_key == "model":
        has_key = bool(
            get_env_value("OPENROUTER_API_KEY")
            or get_env_value("OPENAI_API_KEY")
            or get_env_value("ANTHROPIC_API_KEY")
        )
        if not has_key:
            # Check for OAuth providers
            try:
                from hermes_cli.auth import get_active_provider
                if get_active_provider():
                    has_key = True
            except Exception:
                pass
        if not has_key:
            return None
        model = config.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip()
        if isinstance(model, dict):
            return str(model.get("default") or model.get("model") or "configured")
        return "configured"

    elif section_key == "terminal":
        backend = config.get("terminal", {}).get("backend", "local")
        return f"backend: {backend}"

    elif section_key == "agent":
        max_turns = config.get("agent", {}).get("max_turns", 90)
        return f"max turns: {max_turns}"

    elif section_key == "gateway":
        platforms = []
        if get_env_value("TELEGRAM_BOT_TOKEN"):
            platforms.append("Telegram")
        if get_env_value("DISCORD_BOT_TOKEN"):
            platforms.append("Discord")
        if get_env_value("SLACK_BOT_TOKEN"):
            platforms.append("Slack")
        if get_env_value("SIGNAL_ACCOUNT"):
            platforms.append("Signal")
        if get_env_value("EMAIL_ADDRESS"):
            platforms.append("Email")
        if get_env_value("TWILIO_ACCOUNT_SID"):
            platforms.append("SMS")
        if get_env_value("MATRIX_ACCESS_TOKEN") or get_env_value("MATRIX_PASSWORD"):
            platforms.append("Matrix")
        if get_env_value("MATTERMOST_TOKEN"):
            platforms.append("Mattermost")
        if get_env_value("WHATSAPP_PHONE_NUMBER_ID"):
            platforms.append("WhatsApp")
        if get_env_value("DINGTALK_CLIENT_ID"):
            platforms.append("DingTalk")
        if get_env_value("FEISHU_APP_ID"):
            platforms.append("Feishu")
        if get_env_value("WECOM_BOT_ID"):
            platforms.append("WeCom")
        if get_env_value("WEIXIN_ACCOUNT_ID"):
            platforms.append("Weixin")
        if get_env_value("BLUEBUBBLES_SERVER_URL"):
            platforms.append("BlueBubbles")
        if get_env_value("WEBHOOK_ENABLED"):
            platforms.append("Webhooks")
        if platforms:
            return ", ".join(platforms)
        return None  # No platforms configured — section must run

    elif section_key == "tools":
        tools = []
        if get_env_value("ELEVENLABS_API_KEY"):
            tools.append("TTS/ElevenLabs")
        if get_env_value("BROWSERBASE_API_KEY"):
            tools.append("Browser")
        if get_env_value("FIRECRAWL_API_KEY"):
            tools.append("Firecrawl")
        if tools:
            return ", ".join(tools)
        return None

    return None


def _skip_configured_section(
    config: dict, section_key: str, label: str
) -> bool:
    """Show an already-configured section summary and offer to skip.

    Returns True if the user chose to skip, False if the section should run.
    """
    summary = _get_section_config_summary(config, section_key)
    if not summary:
        return False
    print()
    print_success(f"  {label}: {summary}")
    return not prompt_yes_no(f"  Reconfigure {label.lower()}?", default=False)


# =============================================================================
# OpenClaw Migration
# =============================================================================


_OPENCLAW_SCRIPT = (
    get_optional_skills_dir(PROJECT_ROOT / "optional-skills")
    / "migration"
    / "openclaw-migration"
    / "scripts"
    / "openclaw_to_hermes.py"
)


def _load_openclaw_migration_module():
    """Load the openclaw_to_hermes migration script as a module.

    Returns the loaded module, or None if the script can't be loaded.
    """
    if not _OPENCLAW_SCRIPT.exists():
        return None

    spec = importlib.util.spec_from_file_location(
        "openclaw_to_hermes", _OPENCLAW_SCRIPT
    )
    if spec is None or spec.loader is None:
        return None

    mod = importlib.util.module_from_spec(spec)
    # Register in sys.modules so @dataclass can resolve the module
    # (Python 3.11+ requires this for dynamically loaded modules)
    import sys as _sys
    _sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        _sys.modules.pop(spec.name, None)
        raise
    return mod


# Item kinds that represent high-impact changes warranting explicit warnings.
# Gateway tokens/channels can hijack messaging platforms from the old agent.
# Config values may have different semantics between OpenClaw and Hermes.
# Instruction/context files (.md) can contain incompatible setup procedures.
_HIGH_IMPACT_KIND_KEYWORDS = {
    "gateway": "⚠ Gateway/messaging — this will configure Hermes to use your OpenClaw messaging channels",
    "telegram": "⚠ Telegram — this will point Hermes at your OpenClaw Telegram bot",
    "slack": "⚠ Slack — this will point Hermes at your OpenClaw Slack workspace",
    "discord": "⚠ Discord — this will point Hermes at your OpenClaw Discord bot",
    "whatsapp": "⚠ WhatsApp — this will point Hermes at your OpenClaw WhatsApp connection",
    "config": "⚠ Config values — OpenClaw settings may not map 1:1 to Hermes equivalents",
    "soul": "⚠ Instruction file — may contain OpenClaw-specific setup/restart procedures",
    "memory": "⚠ Memory/context file — may reference OpenClaw-specific infrastructure",
    "context": "⚠ Context file — may contain OpenClaw-specific instructions",
}


def _print_migration_preview(report: dict):
    """Print a detailed dry-run preview of what migration would do.

    Groups items by category and adds explicit warnings for high-impact
    changes like gateway token takeover and config value differences.
    """
    items = report.get("items", [])
    if not items:
        print_info("Nothing to migrate.")
        return

    migrated_items = [i for i in items if i.get("status") == "migrated"]
    conflict_items = [i for i in items if i.get("status") == "conflict"]
    skipped_items = [i for i in items if i.get("status") == "skipped"]

    warnings_shown = set()

    if migrated_items:
        print(color("  Would import:", Colors.GREEN))
        for item in migrated_items:
            kind = item.get("kind", "unknown")
            dest = item.get("destination", "")
            if dest:
                dest_short = str(dest).replace(str(Path.home()), "~")
                print(f"      {kind:<22s} → {dest_short}")
            else:
                print(f"      {kind}")

            # Check for high-impact items and collect warnings
            kind_lower = kind.lower()
            dest_lower = str(dest).lower()
            for keyword, warning in _HIGH_IMPACT_KIND_KEYWORDS.items():
                if keyword in kind_lower or keyword in dest_lower:
                    warnings_shown.add(warning)
        print()

    if conflict_items:
        print(color("  Would overwrite (conflicts with existing Hermes config):", Colors.YELLOW))
        for item in conflict_items:
            kind = item.get("kind", "unknown")
            reason = item.get("reason", "already exists")
            print(f"      {kind:<22s}  {reason}")
        print()

    if skipped_items:
        print(color("  Would skip:", Colors.DIM))
        for item in skipped_items:
            kind = item.get("kind", "unknown")
            reason = item.get("reason", "")
            print(f"      {kind:<22s}  {reason}")
        print()

    # Print collected warnings
    if warnings_shown:
        print(color("  ── Warnings ──", Colors.YELLOW))
        for warning in sorted(warnings_shown):
            print(color(f"    {warning}", Colors.YELLOW))
        print()
        print(color("  Note: OpenClaw config values may have different semantics in Hermes.", Colors.YELLOW))
        print(color("  For example, OpenClaw's tool_call_execution: \"auto\" ≠ Hermes's yolo mode.", Colors.YELLOW))
        print(color("  Instruction files (.md) from OpenClaw may contain incompatible procedures.", Colors.YELLOW))
        print()


def _offer_openclaw_migration(hermes_home: Path) -> bool:
    """Detect ~/.openclaw and offer to migrate during first-time setup.

    Runs a dry-run first to show the user exactly what would be imported,
    overwritten, or taken over. Only executes after explicit confirmation.

    Returns True if migration ran successfully, False otherwise.
    """
    openclaw_dir = Path.home() / ".openclaw"
    if not openclaw_dir.is_dir():
        return False

    if not _OPENCLAW_SCRIPT.exists():
        return False

    print()
    print_header("OpenClaw Installation Detected")
    print_info(f"Found OpenClaw data at {openclaw_dir}")
    print_info("Hermes can preview what would be imported before making any changes.")
    print()

    if not prompt_yes_no("Would you like to see what can be imported?", default=True):
        print_info(
            "Skipping migration. You can run it later with: hermes claw migrate --dry-run"
        )
        return False

    # Ensure config.yaml exists before migration tries to read it
    config_path = get_config_path()
    if not config_path.exists():
        save_config(load_config())

    # Load the migration module
    try:
        mod = _load_openclaw_migration_module()
        if mod is None:
            print_warning("Could not load migration script.")
            return False
    except Exception as e:
        print_warning(f"Could not load migration script: {e}")
        logger.debug("OpenClaw migration module load error", exc_info=True)
        return False

    # ── Phase 1: Dry-run preview ──
    try:
        selected = mod.resolve_selected_options(None, None, preset="full")
        dry_migrator = mod.Migrator(
            source_root=openclaw_dir.resolve(),
            target_root=hermes_home.resolve(),
            execute=False,  # dry-run — no files modified
            workspace_target=None,
            overwrite=True,  # show everything including conflicts
            migrate_secrets=True,
            output_dir=None,
            selected_options=selected,
            preset_name="full",
        )
        preview_report = dry_migrator.migrate()
    except Exception as e:
        print_warning(f"Migration preview failed: {e}")
        logger.debug("OpenClaw migration preview error", exc_info=True)
        return False

    # Display the full preview
    preview_summary = preview_report.get("summary", {})
    preview_count = preview_summary.get("migrated", 0)

    if preview_count == 0:
        print()
        print_info("Nothing to import from OpenClaw.")
        return False

    print()
    print_header(f"Migration Preview — {preview_count} item(s) would be imported")
    print_info("No changes have been made yet. Review the list below:")
    print()
    _print_migration_preview(preview_report)

    # ── Phase 2: Confirm and execute ──
    if not prompt_yes_no("Proceed with migration?", default=False):
        print_info(
            "Migration cancelled. You can run it later with: hermes claw migrate"
        )
        print_info(
            "Use --dry-run to preview again, or --preset minimal for a lighter import."
        )
        return False

    # Execute the migration — overwrite=False so existing Hermes configs are
    # preserved. The user saw the preview; conflicts are skipped by default.
    try:
        migrator = mod.Migrator(
            source_root=openclaw_dir.resolve(),
            target_root=hermes_home.resolve(),
            execute=True,
            workspace_target=None,
            overwrite=False,  # preserve existing Hermes config
            migrate_secrets=True,
            output_dir=None,
            selected_options=selected,
            preset_name="full",
        )
        report = migrator.migrate()
    except Exception as e:
        print_warning(f"Migration failed: {e}")
        logger.debug("OpenClaw migration error", exc_info=True)
        return False

    # Print final summary
    summary = report.get("summary", {})
    migrated = summary.get("migrated", 0)
    skipped = summary.get("skipped", 0)
    conflicts = summary.get("conflict", 0)
    errors = summary.get("error", 0)

    print()
    if migrated:
        print_success(f"Imported {migrated} item(s) from OpenClaw.")
    if conflicts:
        print_info(f"Skipped {conflicts} item(s) that already exist in Hermes (use hermes claw migrate --overwrite to force).")
    if skipped:
        print_info(f"Skipped {skipped} item(s) (not found or unchanged).")
    if errors:
        print_warning(f"{errors} item(s) had errors — check the migration report.")

    output_dir = report.get("output_dir")
    if output_dir:
        print_info(f"Full report saved to: {output_dir}")

    print_success("Migration complete! Continuing with setup...")
    return True


# =============================================================================
# Main Wizard Orchestrator
# =============================================================================

SETUP_SECTIONS = [
    ("model", "Model & Provider", setup_model_provider),
    ("tts", "Text-to-Speech", setup_tts),
    ("terminal", "Terminal Backend", setup_terminal_backend),
    ("gateway", "Messaging Platforms (Gateway)", setup_gateway),
    ("tools", "Tools", setup_tools),
    ("agent", "Agent Settings", setup_agent_settings),
]

# The returning-user menu intentionally omits standalone TTS because model setup
# already includes TTS selection and tools setup covers the rest of the provider
# configuration. Keep this list in the same order as the visible menu entries.
RETURNING_USER_MENU_SECTION_KEYS = [
    "model",
    "terminal",
    "gateway",
    "tools",
    "agent",
]


def run_setup_wizard(args):
    """Run the interactive setup wizard.

    Supports full, quick, and section-specific setup:
      hermes setup           — full or quick (auto-detected)
      hermes setup model     — just model/provider
      hermes setup tts       — just text-to-speech
      hermes setup terminal  — just terminal backend
      hermes setup gateway   — just messaging platforms
      hermes setup tools     — just tool configuration
      hermes setup agent     — just agent settings
    """
    from hermes_cli.config import is_managed, managed_error
    if is_managed():
        managed_error("run setup wizard")
        return
    ensure_hermes_home()

    reset_requested = bool(getattr(args, "reset", False))
    if reset_requested:
        save_config(copy.deepcopy(DEFAULT_CONFIG))
        print_success("Configuration reset to defaults.")

    config = load_config()
    hermes_home = get_hermes_home()

    # Detect non-interactive environments (headless SSH, Docker, CI/CD)
    non_interactive = getattr(args, 'non_interactive', False)
    if not non_interactive and not is_interactive_stdin():
        non_interactive = True

    if non_interactive:
        print_noninteractive_setup_guidance(
            "Running in a non-interactive environment (no TTY detected)."
        )
        return

    # Check if a specific section was requested
    section = getattr(args, "section", None)
    if section:
        for key, label, func in SETUP_SECTIONS:
            if key == section:
                print()
                print(
                    color(
                        "┌─────────────────────────────────────────────────────────┐",
                        Colors.MAGENTA,
                    )
                )
                print(color(f"│     ⚕ Hermes Setup — {label:<34s} │", Colors.MAGENTA))
                print(
                    color(
                        "└─────────────────────────────────────────────────────────┘",
                        Colors.MAGENTA,
                    )
                )
                func(config)
                save_config(config)
                print()
                print_success(f"{label} configuration complete!")
                return

        print_error(f"Unknown setup section: {section}")
        print_info(f"Available sections: {', '.join(k for k, _, _ in SETUP_SECTIONS)}")
        return

    # Check if this is an existing installation with a provider configured
    from hermes_cli.auth import get_active_provider

    active_provider = get_active_provider()
    is_existing = (
        bool(get_env_value("OPENROUTER_API_KEY"))
        or bool(get_env_value("OPENAI_BASE_URL"))
        or active_provider is not None
    )

    print()
    print(
        color(
            "┌─────────────────────────────────────────────────────────┐",
            Colors.MAGENTA,
        )
    )
    print(
        color(
            "│             ⚕ Hermes Agent 设置向导                   │", Colors.MAGENTA
        )
    )
    print(
        color(
            "├─────────────────────────────────────────────────────────┤",
            Colors.MAGENTA,
        )
    )
    print(
        color(
            "│  让我们配置您的 Hermes Agent 安装。                    │", Colors.MAGENTA
        )
    )
    print(
        color(
            "│  随时按 Ctrl+C 退出。                                   │", Colors.MAGENTA
        )
    )
    print(
        color(
            "└─────────────────────────────────────────────────────────┘",
            Colors.MAGENTA,
        )
    )

    migration_ran = False

    if is_existing:
        # ── Returning User Menu ──
        print()
        print_header("欢迎回来！")
        print_success("您已经配置过 Hermes。")
        print()

        menu_choices = [
            "快速设置 - 仅配置缺失项目",
            "完整设置 - 重新配置所有内容",
            "模型和提供商",
            "终端后端",
            "消息平台（网关）",
            "工具",
            "代理设置",
            "退出",
        ]
        choice = prompt_choice("您想要做什么？", menu_choices, 0)

        if choice == 0:
            # Quick setup
            _run_quick_setup(config, hermes_home)
            return
        elif choice == 1:
            # Full setup — fall through to run all sections
            pass
        elif choice == 7:
            print_info("退出。准备好后再次运行 'hermes setup'。")
            return
        elif 2 <= choice <= 6:
            # Individual section — map by key, not by position.
            # SETUP_SECTIONS includes TTS but the returning-user menu skips it,
            # so positional indexing (choice - 2) would dispatch the wrong section.
            section_key = RETURNING_USER_MENU_SECTION_KEYS[choice - 2]
            section = next((s for s in SETUP_SECTIONS if s[0] == section_key), None)
            if section:
                _, label, func = section
                func(config)
                save_config(config)
                _print_setup_summary(config, hermes_home)
            return
    else:
        # ── First-Time Setup ──
        print()

        # Offer OpenClaw migration before configuration begins
        migration_ran = _offer_openclaw_migration(hermes_home)
        if migration_ran:
            config = load_config()

        setup_mode = prompt_choice("您想要如何设置 Hermes？", [
            "快速设置 — 提供商、模型和消息（推荐）",
            "完整设置 — 配置所有内容",
        ], 0)

        if setup_mode == 0:
            _run_first_time_quick_setup(config, hermes_home, is_existing)
            return

    # ── Full Setup — run all sections ──
    print_header("配置文件位置")
    print_info(f"配置文件：  {get_config_path()}")
    print_info(f"密钥文件：   {get_env_path()}")
    print_info(f"数据文件夹： {hermes_home}")
    print_info(f"安装目录：   {PROJECT_ROOT}")
    print()
    print_info("您可以直接编辑这些文件，或使用 'hermes config edit'")

    if migration_ran:
        print()
        print_info("Settings were imported from OpenClaw.")
        print_info("Each section below will show what was imported — press Enter to keep,")
        print_info("or choose to reconfigure if needed.")

    # Section 1: Model & Provider
    if not (migration_ran and _skip_configured_section(config, "model", "Model & Provider")):
        setup_model_provider(config)

    # Section 2: Terminal Backend
    if not (migration_ran and _skip_configured_section(config, "terminal", "Terminal Backend")):
        setup_terminal_backend(config)

    # Section 3: Agent Settings
    if not (migration_ran and _skip_configured_section(config, "agent", "Agent Settings")):
        setup_agent_settings(config)

    # Section 4: Messaging Platforms
    if not (migration_ran and _skip_configured_section(config, "gateway", "Messaging Platforms")):
        setup_gateway(config)

    # Section 5: Tools
    if not (migration_ran and _skip_configured_section(config, "tools", "Tools")):
        setup_tools(config, first_install=not is_existing)

    # Save and show summary
    save_config(config)
    _print_setup_summary(config, hermes_home)

    _offer_launch_chat()


def _resolve_hermes_chat_argv() -> Optional[list[str]]:
    """Resolve argv for launching ``hermes chat`` in a fresh process."""
    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        return [hermes_bin, "chat"]

    try:
        if importlib.util.find_spec("hermes_cli") is not None:
            return [sys.executable, "-m", "hermes_cli.main", "chat"]
    except Exception:
        pass

    return None


def _offer_launch_chat():
    """Prompt the user to jump straight into chat after setup."""
    print()
    if not prompt_yes_no("现在启动 hermes chat？", True):
        return

    chat_argv = _resolve_hermes_chat_argv()
    if not chat_argv:
        print_info("无法自动重新启动 Hermes。手动运行 'hermes chat'。")
        return

    os.execvp(chat_argv[0], chat_argv)


def _run_first_time_quick_setup(config: dict, hermes_home, is_existing: bool):
    """Streamlined first-time setup: provider + model only.

    Applies sensible defaults for TTS (Edge), terminal (local), agent
    settings, and tools — the user can customize later via
    ``hermes setup <section>``.
    """
    # Step 1: Model & Provider (essential — skips rotation/vision/TTS)
    setup_model_provider(config, quick=True)

    # Step 2: Apply defaults for everything else
    _apply_default_agent_settings(config)
    config.setdefault("terminal", {}).setdefault("backend", "local")

    save_config(config)

    # Step 3: Offer messaging gateway setup
    print()
    gateway_choice = prompt_choice(
        "连接消息平台？（Telegram、Discord 等）",
        [
            "现在设置消息（推荐）",
            "跳过 — 稍后通过 'hermes setup gateway' 设置",
        ],
        0,
    )

    if gateway_choice == 0:
        setup_gateway(config)
        save_config(config)

    print()
    print_success("设置完成！您已准备就绪。")
    print()
    print_info("  配置所有设置：    hermes setup")
    if gateway_choice != 0:
        print_info("  连接 Telegram/Discord：  hermes setup gateway")
    print()

    _print_setup_summary(config, hermes_home)

    _offer_launch_chat()


def _run_quick_setup(config: dict, hermes_home):
    """Quick setup — only configure items that are missing."""
    from hermes_cli.config import (
        get_missing_env_vars,
        get_missing_config_fields,
        check_config_version,
    )

    print()
    print_header("快速设置 — 仅配置缺失项目")

    # Check what's missing
    missing_required = [
        v for v in get_missing_env_vars(required_only=False) if v.get("is_required")
    ]
    missing_optional = [
        v for v in get_missing_env_vars(required_only=False) if not v.get("is_required")
    ]
    missing_config = get_missing_config_fields()
    current_ver, latest_ver = check_config_version()

    has_anything_missing = (
        missing_required
        or missing_optional
        or missing_config
        or current_ver < latest_ver
    )

    if not has_anything_missing:
        print_success("一切已配置！无需操作。")
        print()
        print_info("运行 'hermes setup' 并选择'完整设置'重新配置，")
        print_info("或从菜单中选择特定部分。")
        return

    # Handle missing required env vars
    if missing_required:
        print()
        print_info(f"{len(missing_required)} 个必需设置缺失：")
        for var in missing_required:
            print(f"     • {var['name']}")
        print()

        for var in missing_required:
            print()
            print(color(f"  {var['name']}", Colors.CYAN))
            print_info(f"  {var.get('description', '')}")
            if var.get("url"):
                print_info(f"  获取密钥：{var['url']}")

            if var.get("password"):
                value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
            else:
                value = prompt(f"  {var.get('prompt', var['name'])}")

            if value:
                save_env_value(var["name"], value)
                print_success(f"  已保存 {var['name']}")
            else:
                print_warning(f"  跳过 {var['name']}")

    # Split missing optional vars by category
    missing_tools = [v for v in missing_optional if v.get("category") == "tool"]
    missing_messaging = [
        v
        for v in missing_optional
        if v.get("category") == "messaging" and not v.get("advanced")
    ]

    # ── Tool API keys (checklist) ──
    if missing_tools:
        print()
        print_header("工具 API 密钥")

        checklist_labels = []
        for var in missing_tools:
            tools = var.get("tools", [])
            tools_str = f" → {', '.join(tools[:2])}" if tools else ""
            checklist_labels.append(f"{var.get('description', var['name'])}{tools_str}")

        selected_indices = prompt_checklist(
            "您想要配置哪些工具？",
            checklist_labels,
        )

        for idx in selected_indices:
            var = missing_tools[idx]
            _prompt_api_key(var)

    # ── Messaging platforms (checklist then prompt for selected) ──
    if missing_messaging:
        print()
        print_header("消息平台")
        print_info("将 Hermes 连接到消息应用，随时随地聊天。")
        print_info("您可以稍后通过 'hermes setup gateway' 配置这些。")

        # Group by platform (preserving order)
        platform_order = []
        platforms = {}
        for var in missing_messaging:
            name = var["name"]
            if "TELEGRAM" in name:
                plat = "Telegram"
            elif "DISCORD" in name:
                plat = "Discord"
            elif "SLACK" in name:
                plat = "Slack"
            else:
                continue
            if plat not in platforms:
                platform_order.append(plat)
            platforms.setdefault(plat, []).append(var)

        platform_labels = [
            {
                "Telegram": "📱 Telegram",
                "Discord": "💬 Discord",
                "Slack": "💼 Slack",
            }.get(p, p)
            for p in platform_order
        ]

        selected_indices = prompt_checklist(
            "您想要设置哪些平台？",
            platform_labels,
        )

        for idx in selected_indices:
            plat = platform_order[idx]
            vars_list = platforms[plat]
            emoji = {"Telegram": "📱", "Discord": "💬", "Slack": "💼"}.get(plat, "")
            print()
            print(color(f"  ─── {emoji} {plat} ───", Colors.CYAN))
            print()
            for var in vars_list:
                print_info(f"  {var.get('description', '')}")
                if var.get("url"):
                    print_info(f"  {var['url']}")
                if var.get("password"):
                    value = prompt(f"  {var.get('prompt', var['name'])}", password=True)
                else:
                    value = prompt(f"  {var.get('prompt', var['name'])}")
                if value:
                    save_env_value(var["name"], value)
                    print_success("  ✓ Saved")
                else:
                    print_warning("  Skipped")
                print()

    # Handle missing config fields
    if missing_config:
        print()
        print_info(
            f"正在添加 {len(missing_config)} 个新配置选项（使用默认值）..."
        )
        for field in missing_config:
            print_success(f"  已添加 {field['key']} = {field['default']}")

        # Update config version
        config["_config_version"] = latest_ver
        save_config(config)

    # Jump to summary
    _print_setup_summary(config, hermes_home)
