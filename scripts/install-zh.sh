#!/bin/bash
# ============================================================================
# Hermes Agent 中文版安装脚本
# ============================================================================
# 基于 NousResearch/hermes-agent 官方安装脚本修改
# 从 eddielueng/hermes-agent-zh 仓库安装完整中文化版本
#
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/eddielueng/hermes-agent-zh/main/scripts/install.sh | bash
#
# ============================================================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # 无颜色
BOLD='\033[1m'

# 配置
REPO_URL_HTTPS="https://github.com/eddielueng/hermes-agent-zh.git"
REPO_URL_ZIP="https://github.com/eddielueng/hermes-agent-zh/archive/refs/heads/main.zip"
HERMES_HOME="$HOME/.hermes"
INSTALL_DIR="${HERMES_INSTALL_DIR:-$HERMES_HOME/hermes-agent}"
PYTHON_VERSION="3.11"
NODE_VERSION="22"

# 选项
USE_VENV=true
RUN_SETUP=true
BRANCH="main"

# 检测非交互模式（如 curl | bash）
if [ -t 0 ]; then
    IS_INTERACTIVE=true
else
    IS_INTERACTIVE=false
fi

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --skip-setup)
            RUN_SETUP=false
            shift
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Hermes Agent 中文版安装程序"
            echo ""
            echo "用法: install.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --no-venv      不创建虚拟环境"
            echo "  --skip-setup   跳过交互式设置向导"
            echo "  --branch NAME  Git 分支 (默认: main)"
            echo "  --dir PATH     安装目录 (默认: ~/.hermes/hermes-agent)"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# 辅助函数
# ============================================================================

print_banner() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│             ⚕ Hermes Agent 安装程序                   │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│  🎌 Hermes Agent 中文版 — 基于NousResearch项目          │"
    echo "│     完整中文化界面 · 内置XiDao Api支持               │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# 主安装流程
# ============================================================================

main() {
    print_banner

    # 检测操作系统
    OS="$(uname -s)"
    case "$OS" in
        Linux*)  PLATFORM="linux";;
        Darwin*) PLATFORM="macos";;
        *)       PLATFORM="unknown";;
    esac

    print_success "检测到: $(uname -m) ($PLATFORM)"

    # 检查 Python
    if check_command python3; then
        PYTHON_VERSION_FULL=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python 已找到: $PYTHON_VERSION_FULL"
    elif check_command python; then
        PYTHON_VERSION_FULL=$(python --version 2>&1 | awk '{print $2}')
        print_success "Python 已找到: $PYTHON_VERSION_FULL"
    else
        print_error "未找到 Python！请先安装 Python 3.10+"
        print_info "Ubuntu/Debian: sudo apt install python3 python3-venv"
        print_info "CentOS/RHEL:   sudo yum install python3"
        exit 1
    fi

    # 自动安装 python3-venv（创建虚拟环境必需）
    echo ""
    print_info "检查 Python 虚拟环境支持..."
    if ! python3 -m venv --help &>/dev/null 2>&1; then
        print_warning "需要安装 python3-venv 包..."
        if [ "$PLATFORM" = "linux" ]; then
            if check_command apt-get; then
                apt-get update -qq && apt-get install -y -qq python3-venv && \
                print_success "python3-venv 已安装" || \
                { print_error "自动安装失败，请手动运行: sudo apt install python3-venv"; exit 1; }
            elif check_command yum; then
                yum install -y python3-virtualenv && \
                print_success "python3-virtualenv 已安装" || \
                { print_error "自动安装失败，请手动运行: sudo yum install python3-virtualenv"; exit 1; }
            fi
        elif [ "$PLATFORM" = "macos" ]; then
            print_info "macOS 通常已内置 venv 支持。如果出错请: brew install python@3.11"
        fi
    else
        print_success "虚拟环境支持就绪"
    fi

    # 检查 curl 或 wget
    if check_command curl; then
        DOWNLOAD_CMD="curl -sL"
    elif check_command wget; then
        DOWNLOAD_CMD="wget -qO-"
    else
        print_error "未找到 curl 或 wget！请先安装其中一个。"
        exit 1
    fi

    # 检查 unzip（用于 zip 下载）
    NEED_UNZIP=false
    if ! check_command git; then
        NEED_UNZIP=true
        if ! check_command unzip; then
            print_warning "未找到 git 和 unzip，正在尝试安装 unzip..."
            if [ "$PLATFORM" = "linux" ]; then
                (apt-get update -qq && apt-get install -y -qq unzip) &>/dev/null || \
                (yum install -y unzip) &>/dev/null || \
                print_error "无法自动安装 unzip。请手动运行: apt install unzip 或 yum install unzip"
            fi
        fi
    fi

    # 创建安装目录
    print_info "安装到: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    # 下载并解压中文版
    echo ""
    print_info "正在下载 Hermes Agent 中文版..."

    if check_command git && [ "$IS_INTERACTIVE" = true ]; then
        # 使用 git 克隆（交互模式）
        if [ -d ".git" ]; then
            print_info "发现已有安装，正在更新..."
            git fetch origin "$BRANCH" || true
            git stash || true 2>/dev/null
            git checkout "$BRANCH" || git checkout -b "$BRANCH" "origin/$BRANCH" || true
            git pull origin "$BRANCH" || true
            git stash pop || true 2>/dev/null
        else
            git clone "$REPO_URL_HTTPS" temp_install && \
            shopt -s dotglob nullglob && \
            mv temp_install/* . && \
            mv temp_install/.* . 2>/dev/null && \
            rmdir temp_install 2>/dev/null || rm -rf temp_install
        fi
    else
        # 使用 zip 下载（非交互模式或无 git）
        TEMP_ZIP="/tmp/hermes-zh-install.zip"
        $DOWNLOAD_CMD "$REPO_URL_ZIP" -o "$TEMP_ZIP"
        
        if [ -f "$TEMP_ZIP" ]; then
            print_success "下载完成，正在解压..."
            
            # 创建临时目录
            TEMP_DIR="/tmp/hermes-zh-temp"
            rm -rf "$TEMP_DIR"
            mkdir -p "$TEMP_DIR"
            unzip -o "$TEMP_ZIP" -d "$TEMP_DIR"
            rm -f "$TEMP_ZIP"
            
            # 移动文件（排除临时目录）
            EXTRACTED_DIR=$(ls -d "$TEMP_DIR"/hermes-agent-zh-main 2>/dev/null || echo "$TEMP_DIR")
            
            # 复制所有文件到当前目录
            cp -rf "$EXTRACTED_DIR"/* . 2>/dev/null || true
            cp -rf "$EXTRACTED_DIR"/.* . 2>/dev/null || true
            
            # 清理
            rm -rf "$TEMP_DIR"
            
            print_success "解压完成"
        else
            print_error "下载失败！请检查网络连接。"
            print_info "手动下载地址: $REPO_URL_ZIP"
            exit 1
        fi
    fi

    # 验证文件存在
    if [ ! -f "pyproject.toml" ] && [ ! -f "setup.py" ]; then
        print_error "安装失败！未找到 pyproject.toml 或 setup.py"
        print_info "当前目录内容:"
        ls -la | head -20
        exit 1
    fi

    print_success "文件就绪"

    # 创建虚拟环境
    if [ "$USE_VENV" = true ]; then
        echo ""
        print_info "创建 Python 虚拟环境..."
        
        if [ ! -d "venv" ]; then
            # 尝试创建虚拟环境，如果失败则尝试安装依赖后重试
            if ! python3 -m venv venv 2>/dev/null; then
                print_warning "虚拟环境创建失败，正在尝试安装依赖..."
                
                # 尝试安装 python3-venv
                if check_command apt-get; then
                    apt-get update -qq && apt-get install -y -qq python3-venv python3-pip 2>/dev/null || true
                elif check_command yum; then
                    yum install -y python3-virtualenv python3-pip 2>/dev/null || true
                fi
                
                # 重试创建虚拟环境
                if ! python3 -m venv venv; then
                    print_error "无法创建虚拟环境！"
                    print_info "请手动运行以下命令安装依赖："
                    print_info "  Ubuntu/Debian: sudo apt install python3-venv python3-pip"
                    print_info "  CentOS/RHEL:   sudo yum install python3-virtualenv python3-pip"
                    exit 1
                fi
            fi
        fi
        
        source venv/bin/activate
        print_success "虚拟环境已激活: $(which python)"
        
        # 使用 python -m pip（更可靠）
        PIP_CMD="python -m pip"
        
        # 升级 pip
        $PIP_CMD install --upgrade pip --quiet 2>/dev/null || true
        
        # 安装 Hermes
        echo ""
        print_info "正在安装 Hermes Agent 及依赖..."
        
        if [ -f "pyproject.toml" ]; then
            $PIP_CMD install -e . --quiet 2>/dev/null || $PIP_CMD install .
        elif [ -f "setup.py" ]; then
            $PIP_CMD install -e . --quiet 2>/dev/null || $PIP_CMD install .
        else
            print_error "未找到安装配置文件"
            exit 1
        fi
        
        print_success "安装完成！"
    fi

    # 添加到 PATH（如果使用默认路径）
    if [ "$INSTALL_DIR" = "$HERMES_HOME/hermes-agent" ] && [ ! -f "$HOME/.bashrc" ] || ! grep -q "hermes-agent" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo '# Hermes Agent 中文版' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.hermes/hermes-agent:$PATH"' >> "$HOME/.bashrc"
        print_info "已添加到 ~/.bashrc"
    fi

    # 运行设置向导
    if [ "$RUN_SETUP" = true ] && [ "$IS_INTERACTIVE" = true ]; then
        echo ""
        echo -e "${GREEN}${BOLD}"
        echo "╔══════════════════════════════════════════════════════════╗"
        echo "║                                                          ║"
        echo "║         🎌 Hermes Agent 中文版 安装成功！                  ║"
        echo "║                                                          ║"
        echo "║   所有用户界面均已翻译为简体中文                          ║"
        echo "║   内置 XiDao Api 支持（Claude、GPT、GLM、Qwen）        ║"
        echo "║                                                          ║"
        echo "╚══════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
        echo ""
        
        if [ "$USE_VENV" = true ]; then
            source venv/bin/activate 2>/dev/null || true
        fi
        
        print_info "启动中文设置向导..."
        echo ""
        
        # 尝试运行 hermes setup
        if command -v hermes &> /dev/null; then
            hermes setup
        elif [ -f "hermes" ]; then
            ./hermes setup
        else
            python -m hermes_cli.main setup 2>/dev/null || \
            python -c "from hermes_cli.setup import run_setup_wizard; import sys; run_setup_wizard(sys.argv[1:])" 
        fi
    else
        echo ""
        echo -e "${GREEN}${BOLD}"
        echo "╔══════════════════════════════════════════════════════════╗"
        echo "║         🎌 Hermes Agent 中文版 安装成功！                  ║"
        echo "╚══════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
        echo ""
        print_info "下一步操作："
        echo ""
        echo "  1. 激活虚拟环境:"
        if [ "$INSTALL_DIR" = "$HERMES_HOME/hermes-agent" ]; then
            echo "     source \$HOME/.hermes/hermes-agent/venv/bin/activate"
        else
            echo "     source $INSTALL_DIR/venv/bin/activate"
        fi
        echo ""
        echo "  2. 启动中文设置向导:"
        echo "     hermes setup"
        echo ""
        echo "  3. 或直接开始聊天:"
        echo "     hermes"
        echo ""
        echo -e "${CYAN}📖 完整文档: https://github.com/eddielueng/hermes-agent-zh${NC}"
        echo ""
    fi
}

# 运行主函数
main "$@"
