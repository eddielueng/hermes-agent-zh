#!/bin/bash
# ============================================================================
# Hermes Agent 中文版 - 一键安装脚本 (v2)
# ============================================================================
# 参考 NousResearch 官方安装脚本，使用 uv 自动管理 Python 版本
# 支持 Linux, macOS, WSL2, Android/Termux
#
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/eddielueng/hermes-agent-zh/main/scripts/install-zh.sh | bash
#   或
#   bash install-zh.sh [--no-venv] [--skip-setup] [--dir PATH]
#
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# 配置
REPO_URL="https://github.com/eddielueng/hermes-agent-zh.git"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
INSTALL_DIR="${HERMES_INSTALL_DIR:-$HERMES_HOME/hermes-agent}"
PYTHON_VERSION="3.11"
NODE_VERSION="22"

# 选项
USE_VENV=true
RUN_SETUP=true
BRANCH="main"

# 检测非交互模式 (curl | bash)
if [ -t 0 ]; then
    IS_INTERACTIVE=true
else
    IS_INTERACTIVE=false
fi

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv) USE_VENV=false; shift ;;
        --skip-setup) RUN_SETUP=false; shift ;;
        --branch) BRANCH="$2"; shift 2 ;;
        --dir) INSTALL_DIR="$2"; shift 2 ;;
        --hermes-home) HERMES_HOME="$2"; shift 2 ;;
        -h|--help)
            echo "Hermes Agent 中文版 安装器 (v2)"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --no-venv       不创建虚拟环境"
            echo "  --skip-setup    跳过交互式设置向导"
            echo "  --branch NAME   Git分支 (默认: main)"
            echo "  --dir PATH      安装目录 (默认: ~/.hermes/hermes-agent)"
            echo "  --hermes-home   数据目录 (默认: ~/.hermes)"
            echo "  -h, --help      显示帮助信息"
            exit 0
            ;;
        *) echo "未知选项: $1"; exit 1 ;;
    esac
done

# ============================================================================
# 辅助函数
# ============================================================================

print_banner() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                      ║"
    echo "║          🎌 Hermes Agent 中文版 安装器 v2            ║"
    echo "║                                                      ║"
    echo "║      完整中文化的 AI 代理系统 - 基于 NousResearch    ║"
    echo "║          使用 uv 自动管理 Python 版本               ║"
    echo "║                                                      ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() { echo -e "${CYAN}→${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

prompt_yes_no() {
    local question="$1"
    local default="${2:-yes}"
    local prompt_suffix answer=""

    case "$default" in
        [yY]|[yY][eE][sS]|[tT][rR][uU][eE]|1) prompt_suffix="[Y/n]" ;;
        *) prompt_suffix="[y/N]" ;;
    esac

    if [ "$IS_INTERACTIVE" = true ]; then
        read -r -p "$question $prompt_suffix " answer || answer=""
    elif [ -r /dev/tty ] && [ -w /dev/tty ]; then
        printf "%s %s " "$question" "$prompt_suffix" > /dev/tty
        IFS= read -r answer < /dev/tty || answer=""
    else
        answer=""
    fi

    answer="${answer#"${answer%%[![:space:]]*}"}"
    answer="${answer%"${answer##*[![:space:]]}"}"

    if [ -z "$answer" ]; then
        case "$default" in
            [yY]|[yY][eE][sS]|[tT][rR][uU][eE]|1) return 0 ;; *) return 1 ;;
        esac
    fi
    case "$answer" in [yY]|[yY][eE][sS]) return 0 ;; *) return 1 ;; esac
}

is_termux() {
    [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux/files/usr"* ]]
}

get_command_link_dir() {
    if is_termux && [ -n "${PREFIX:-}" ]; then echo "$PREFIX/bin"
    else echo "$HOME/.local/bin"; fi
}

# ============================================================================
# 系统检测
# ============================================================================

detect_os() {
    case "$(uname -s)" in
        Linux*)
            if is_termux; then OS="android"; DISTRO="termux"
            else
                OS="linux"
                if [ -f /etc/os-release ]; then . /etc/os-release; DISTRO="$ID"
                else DISTRO="unknown"; fi
            fi
            ;;
        Darwin*) OS="macos"; DISTRO="macos" ;;
        CYGWIN*|MINGW*|MSYS*) OS="windows"; DISTRO="windows"
            log_error "Windows 不支持原生安装，请使用 WSL2"
            exit 1
            ;;
        *) OS="unknown"; DISTRO="unknown" ;;
    esac
    log_success "系统: $OS ($DISTRO)"
}

# ============================================================================
# 安装 uv (Python包管理器) - 核心改进！
# ============================================================================

install_uv() {
    if [ "$DISTRO" = "termux" ]; then
        log_info "Termux 检测到 — 使用 Python 自带 venv + pip"
        UV_CMD=""
        return 0
    fi

    log_info "检查 uv 包管理器..."

    # 常见位置查找
    for cmd_path in uv "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if command -v "$cmd_path" &> /dev/null || [ -x "$cmd_path" ]; then
            UV_CMD="$(command -v $cmd_path 2>/dev/null || echo $cmd_path)"
            log_success "uv 已找到: $($UV_CMD --version 2>/dev/null)"
            return 0
        fi
    done

    # 自动安装 uv
    log_info "正在安装 uv (快速 Python 包管理器)..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then
        export PATH="$HOME/.local/bin:$PATH"
        if [ -x "$HOME/.local/bin/uv" ]; then
            UV_CMD="$HOME/.local/bin/uv"
            log_success "uv 已安装: $($UV_CMD --version 2>/dev/null)"
            return 0
        fi
    fi

    log_error "uv 安装失败"
    log_info "手动安装: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

# ============================================================================
# Python 版本检查与自动安装 - 核心改进！
# ============================================================================

check_python() {
    if [ "$DISTRO" = "termux" ]; then
        log_info "检查 Termux Python..."
        if command -v python &>/dev/null; then
            PYTHON_PATH="$(command -v python)"
            PYTHON_VER="$($PYTHON_PATH --version 2>/dev/null)"
            log_success "Python: $PYTHON_VER"
            return 0
        fi
        log_info "通过 pkg 安装 Python..."
        pkg install -y python >/dev/null
        PYTHON_PATH="$(command -v python)"
        log_success "Python 已安装: $($PYTHON_PATH --version 2>/dev/null)"
        return 0
    fi

    # === 核心：使用 uv 管理 Python 版本 ===
    log_info "检查 Python ${PYTHON_VERSION}..."

    # 让 uv 查找合适的 Python
    if PYTHON_PATH="$("$UV_CMD" python find "$PYTHON_VERSION" 2>/dev/null)"; then
        PYTHON_FOUND_VER="$("$PYTHON_PATH" --version 2>/dev/null)"
        log_success "Python 已找到: $PYTHON_FOUND_VER"
        return 0
    fi

    # Python 未找到 — 通过 uv 自动安装（无需 sudo！）
    log_warn "Python ${PYTHON_VERSION} 未找到，正在通过 uv 自动安装..."
    if "$UV_CMD" python install "$PYTHON_VERSION"; then
        PYTHON_PATH="$("$UV_CMD" python find "$PYTHON_VERSION")"
        PYTHON_FOUND_VER="$("$PYTHON_PATH" --version 2>/dev/null)"
        log_success "Python 已自动安装: $PYTHON_FOUND_VER"
    else
        log_error "Python ${PYTHON_VERSION} 安装失败"
        log_info "请手动安装 Python ${PYTHON_VERSION} 后重试"
        exit 1
    fi
}

# ============================================================================
# Git 检查
# ============================================================================

check_git() {
    log_info "检查 Git..."
    if command -v git &> /dev/null; then
        log_success "Git $(git --version | awk '{print $3}')"
        return 0
    fi
    log_error "未找到 Git"

    case "$OS" in
        linux)
            case "$DISTRO" in
                ubuntu|debian) log_info "  sudo apt update && sudo apt install git" ;;
                fedora) log_info "  sudo dnf install git" ;;
                arch) log_info "  sudo pacman -S git" ;;
                *) log_info "  请用包管理器安装 git" ;;
            esac
            ;;
        macos) log_info "  xcode-select --install 或 brew install git" ;;
        android) log_info "  pkg install git" ;;
    esac
    exit 1
}

# ============================================================================
# 克隆仓库
# ============================================================================

clone_repository() {
    log_info "获取 Hermes Agent 中文版代码..."

    # 如果已在正确目录
    if [ -f "pyproject.toml" ] && grep -q "XiDao Api\|中文版\|hermes-agent-zh" README.md 2>/dev/null; then
        log_success "已在中文版仓库中，跳过克隆"
        cd "$(pwd)"
        INSTALL_DIR="$(pwd)"
        return 0
    fi

    # 需要克隆
    if [ ! -f "$INSTALL_DIR/pyproject.toml" ] || [ ! -d "$INSTALL_DIR/hermes_cli" ]; then
        log_info "正在从 GitHub 克隆中文版仓库..."
        rm -rf "$INSTALL_DIR" 2>/dev/null || true

        git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
        if [ $? -eq 0 ]; then
            cd "$INSTALL_DIR"
            if grep -q "XiDao Api" hermes_cli/models.py 2>/dev/null; then
                log_success "代码下载完成，确认为中文版！"
            else
                log_warn "未检测到中文版标记，但继续安装..."
            fi
        else
            log_error "克隆失败！请检查网络连接"
            exit 1
        fi
    else
        cd "$INSTALL_DIR"
        log_success "检测到已有中文版安装"
    fi
}

# ============================================================================
# 创建虚拟环境并安装依赖 - 使用 uv！
# ============================================================================

setup_environment() {
    if [ "$USE_VENV" = false ]; then
        log_info "跳过虚拟环境 (--no-venv)"
        return
    fi

    # === 使用 uv 创建虚拟环境 ===
    if [ -n "$UV_CMD" ] && [ -x "$(command -v $UV_CMD 2>/dev/null || echo $UV_CMD)" ]; then
        log_info "使用 uv 创建虚拟环境..."
        "$UV_CMD" venv
        if [ $? -eq 0 ]; then
            log_success "虚拟环境创建成功 (uv)"
            source .venv/bin/activate
        else
            log_warn "uv venv 失败，回退到标准方式..."
            setup_venv_fallback
        fi
    else
        setup_venv_fallback
    fi

    # === 使用 uv/pip 安装依赖 ===
    log_info "升级包管理器..."
    if [ -n "$UV_CMD" ] && command -v uv &>/dev/null; then
        "$UV_CMD" pip install -U pip setuptools wheel -q 2>/dev/null || true
    else
        pip install --upgrade pip -q 2>/dev/null || true
    fi
    log_success "包管理器已就绪"

    # === 安装项目依赖 ===
    log_info "正在安装 Hermes Agent 及所有依赖（可能需要几分钟）..."
    if [ -n "$UV_CMD" ] && command -v uv &>/dev/null; then
        "$UV_CMD" pip install -e ".[dev]" 2>&1 || {
            log_error "依赖安装失败！尝试标准pip..."
            pip install -e ".[dev]" || exit 1
        }
    else
        pip install -e ".[dev]" || exit 1
    fi
    log_success "所有依赖安装完成！"
}

# 回退：标准方式创建虚拟环境
setup_venv_fallback() {
    log_info "使用 Python 标准库创建虚拟环境..."

    if [ -d ".venv" ] || [ -d "venv" ]; then
        VENV_DIR=".venv"
        [ -d "venv" ] && VENV_DIR="venv"
        if [ "$IS_INTERACTIVE" = true ]; then
            if prompt_yes_no "发现已有虚拟环境，是否删除重新创建？"; then
                rm -rf .venv venv
            else
                log_info "保留现有虚拟环境"
                source "$VENV_DIR/bin/activate" 2>/dev/null || true
                return 0
            fi
        else
            rm -rf .venv venv
        fi
    fi

    "$PYTHON_PATH" -m venv .venv
    source .venv/bin/activate
    log_success "虚拟环境已激活"
}

# ============================================================================
# 创建命令链接
# ============================================================================

create_command_link() {
    local link_dir
    link_dir="$(get_command_link_dir)"

    mkdir -p "$link_dir"

    # 确保 hermes 命令可用
    if [ -d ".venv" ]; then
        ln -sf "$(pwd)/.venv/bin/hermes" "$link_dir/hermes" 2>/dev/null || true
    elif [ -d "venv" ]; then
        ln -sf "$(pwd)/venv/bin/hermes" "$link_dir/hermes" 2>/dev/null || true
    fi

    # 确保在PATH中
    if [[ ":$PATH:" != *":$link_dir:"* ]]; then
        echo "export PATH=\"$link_dir:\$PATH\"" >> ~/.bashrc
        echo "export PATH=\"$link_dir:\$PATH\"" >> ~/.zshrc 2>/dev/null || true
    fi

    log_success "hermes 命令已添加到 $(get_command_link_display_dir)"
}

# ============================================================================
# 完成提示
# ============================================================================

show_completion() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                          ║${NC}"
    echo -e "${GREEN}${BOLD}║     ✅ Hermes Agent 中文版 安装完成！                    ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                          ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}🚀 启动方式:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if [ -d ".venv" ] || [ -d "venv" ]; then
        echo -e "  ${GREEN}方式一（推荐）:${NC}"
        echo "    cd $(pwd)"
        echo "    source .venv/bin/activate  # 或 source venv/bin/activate"
        echo "    hermes"
        echo ""
        echo -e "  ${GREEN}方式二（一行命令）:${NC}"
        echo "    cd $(pwd) && source .venv/bin/activate && hermes"
        echo ""
        echo -e "  ${GREEN}方式三（如果配置了PATH）:${NC}"
        echo "    source ~/.bashrc && hermes"
    else
        echo -e "  ${GREEN}直接运行:${NC}"
        echo "    hermes"
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}📋 首次使用建议:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  1. 启动后输入 ${YELLOW}/help${NC} 查看所有命令"
    echo "  2. 输入 ${YELLOW}/model${NC} 选择 API 服务商（推荐 XiDao Api）"
    echo "  3. 输入 ${YELLOW}/tools${NC} 配置可用工具"
    echo "  4. 输入 ${YELLOW}/skills${NC} 管理技能插件"
    echo "  5. 输入 ${YELLOW}/skin${NC} 更换界面主题"
    echo ""

    if [ "$IS_INTERACTIVE" = false ]; then
        echo -e "${YELLOW}ℹ️  检测到非交互模式，请复制上面的启动命令到终端执行${NC}"
        echo ""
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    print_banner
    echo -e "${BOLD}正在准备安装环境...${NC}"
    echo ""

    detect_os
    install_uv
    check_python
    check_git
    clone_repository
    setup_environment
    create_command_link
    show_completion
}

main "$@"
