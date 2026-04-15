#!/bin/bash
# ============================================================================
# Hermes Agent 中文版 - 一键安装脚本
# ============================================================================
# 专用安装脚本，确保安装的是完整中文化的版本
# 不会覆盖为官方英文版
#
# 用法：
#   bash install-zh.sh
#   或
#   curl -fsSL https://raw.githubusercontent.com/eddielueng/hermes-agent-zh/main/scripts/install-zh.sh | bash
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
NC='\033[0m' # 无颜色
BOLD='\033[1m'

# 配置
HERMES_HOME="$HOME/.hermes"
INSTALL_DIR="${HERMES_INSTALL_DIR:-$HERMES_HOME/hermes-agent}"
PYTHON_MIN_VERSION="3.10"
PYTHON_RECOMMENDED="3.11"
REPO_URL="https://github.com/eddielueng/hermes-agent-zh.git"

# 选项
USE_VENV=true
RUN_SETUP=true

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
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Hermes Agent 中文版 - 一键安装脚本"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --no-venv      不创建虚拟环境"
            echo "  --skip-setup   跳过交互式设置向导"
            echo "  --dir PATH     安装目录 (默认: ~/.hermes/hermes-agent)"
            echo "  -h, --help     显示帮助信息"
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
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                      ║"
    echo "║          🎌 Hermes Agent 中文版 安装器               ║"
    echo "║                                                      ║"
    echo "║      完整中文化的 AI 代理系统 - 基于 NousResearch    ║"
    echo "║                                                      ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$NAME
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ "$OSTYPE" == "linux-android"* ]]; then
        OS="Termux"
    else
        OS="Unknown"
    fi
}

# 检查 Python 版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "未找到 Python！请先安装 Python $PYTHON_MIN_VERSION 或更高版本"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "检测到 Python 版本: $PYTHON_VERSION"
    
    # 提取主版本号和次版本号
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
        print_error "Python 版本过低 ($PYTHON_VERSION)，需要 $PYTHON_MIN_VERSION 或更高版本"
        
        if [[ "$OS" == "Linux" ]] && [[ "$DISTRO" == *"Ubuntu"* || "$DISTRO" == *"Debian"* ]]; then
            print_info "建议运行以下命令升级 Python:"
            echo "  sudo apt update"
            echo "  sudo apt install -y python3.11 python3.11-venv python3-pip"
        fi
        
        exit 1
    fi
    
    if [ "$PYTHON_MINOR" -lt 11 ]; then
        print_warning "建议使用 Python 3.11+ 以获得最佳体验 (当前: $PYTHON_VERSION)"
    fi
    
    print_success "Python 版本检查通过: $PYTHON_VERSION"
}

# 检查 git
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "未找到 Git！请先安装 Git"
        if [[ "$OS" == "Linux" ]]; then
            print_info "Ubuntu/Debian: sudo apt install git"
            print_info "CentOS/RHEL: sudo yum install git"
        elif [[ "$OS" == "macOS" ]]; then
            print_info "运行: xcode-select --install"
        fi
        exit 1
    fi
    print_success "Git 已安装: $(git --version)"
}

# 创建目录结构
create_directories() {
    print_step "创建安装目录..."
    
    if [ ! -d "$HERMES_HOME" ]; then
        mkdir -p "$HERMES_HOME"
        print_success "配置目录已创建: $HERMES_HOME"
    else
        print_info "配置目录已存在: $HERMES_HOME"
    fi
}

# 克隆中文版仓库（支持 curl | bash 模式）
clone_repository() {
    print_step "获取 Hermes Agent 中文版代码..."

    # 如果已经在正确的目录中（本地运行模式）
    if [ -f "pyproject.toml" ] && (grep -q "Hermes Agent 中文版" README.md 2>/dev/null || grep -q "XiDao Api" hermes_cli/models.py 2>/dev/null); then
        print_success "✨ 已在中文版仓库中，跳过克隆"
        return 0
    fi

    # curl | bash 模式：当前目录不是项目目录，需要克隆
    if [ ! -f "$INSTALL_DIR/pyproject.toml" ] || [ ! -d "$INSTALL_DIR/hermes_cli" ]; then
        print_info "正在从 GitHub 克隆中文版仓库..."

        # 删除旧的不完整安装
        rm -rf "$INSTALL_DIR" 2>/dev/null || true

        # 克隆中文版仓库
        git clone "$REPO_URL" "$INSTALL_DIR"

        if [ $? -eq 0 ]; then
            cd "$INSTALL_DIR"
            print_success "✨ 中文版代码下载完成！"

            # 验证是否为中文版
            if grep -q "XiDao Api" hermes_cli/models.py 2>/dev/null; then
                print_success "✅ 确认为中文版！"
            else
                print_warning "⚠️  未检测到中文版标记，但继续安装..."
            fi
        else
            print_error "克隆失败！请检查网络连接或手动下载："
            echo "  git clone https://github.com/eddielueng/hermes-agent-zh.git ~/.hermes/hermes-agent"
            exit 1
        fi
    else
        # 目录存在且有效
        cd "$INSTALL_DIR"

        if grep -q "Hermes Agent 中文版" README.md 2>/dev/null || grep -q "XiDao Api" hermes_cli/models.py 2>/dev/null; then
            print_success "✨ 检测到已有的中文版安装！"
        else
            print_warning "⚠️  检测到现有安装，但可能不是中文版"
        fi
    fi
}

# 创建虚拟环境
create_venv() {
    if [ "$USE_VENV" = false ]; then
        print_info "跳过虚拟环境创建 (--no-venv)"
        return
    fi
    
    print_step "创建 Python 虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "发现已有的虚拟环境，是否删除并重新创建？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_info "旧虚拟环境已删除"
        else
            print_info "保留现有虚拟环境"
            return
        fi
    fi
    
    $PYTHON_CMD -m venv venv
    
    if [ $? -eq 0 ]; then
        print_success "虚拟环境创建成功"
    else
        print_error "虚拟环境创建失败"
        exit 1
    fi
}

# 激活虚拟环境并安装依赖
install_dependencies() {
    print_step "激活虚拟环境..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_success "虚拟环境已激活"
    else
        print_warning "未找到虚拟环境，使用系统 Python"
    fi
    
    print_step "升级 pip..."
    pip install --upgrade pip -q
    print_success "pip 已升级到最新版本"
    
    print_step "安装依赖包（这可能需要几分钟）..."
    print_info "正在安装 Hermes Agent 及其所有依赖..."
    
    # 使用可编辑模式安装，这样修改源码后无需重新安装
    pip install -e ".[dev]"
    
    if [ $? -eq 0 ]; then
        print_success "✨ 所有依赖包安装完成！"
    else
        print_error "依赖包安装失败！"
        print_info "可能的原因:"
        echo "  1. 网络连接问题"
        echo "  2. Python 版本不兼容"
        echo "  3. 系统缺少必要的编译工具"
        echo ""
        print_info "尝试手动安装以查看详细错误:"
        echo "  pip install -e \".[dev]\""
        exit 1
    fi
}

# 显示安装完成信息
show_completion() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                                                          ║${NC}"
    echo -e "${GREEN}${BOLD}║          � Hermes Agent 中文版 安装完成！              ║${NC}"
    echo -e "${GREEN}${BOLD}║                                                          ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}🚀 启动方式:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ "$USE_VENV" = true ] && [ -d "venv" ]; then
        echo -e "  ${GREEN}方式一（推荐）:${NC}"
        echo "    cd $(pwd)"
        echo "    source venv/bin/activate"
        echo "    hermes"
        echo ""
        echo -e "  ${GREEN}方式二（一行命令）:${NC}"
        echo "    cd $(pwd) && source venv/bin/activate && hermes"
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
    echo "  2. 输入 ${YELLOW}/model${NC} 选择 XiDao Api 作为服务商"
    echo "  3. 输入 ${YELLOW}/tools${NC} 配置可用工具"
    echo "  4. 输入 ${YELLOW}/skills${NC} 管理技能插件"
    echo "  5. 输入 ${YELLOW}/skin${NC} 更换界面主题"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}⭐ 特色功能:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  ✅ 完全中文化界面"
    echo "  ✅ 内置 XiDao Api 服务商（首选推荐）"
    echo "  ✅ 支持 23+ 主流 API 服务商"
    echo "  ✅ 完整保留原版所有功能"
    echo "  ✅ 支持网关服务（Telegram/Discord等）"
    echo ""
    
    # 如果用户选择运行设置向导
    if [ "$RUN_SETUP" = true ]; then
        echo -e "${YELLOW}是否现在启动设置向导？(Y/n)${NC}"
        read -r start_setup
        if [[ ! "$start_setup" =~ ^[Nn]$ ]]; then
            echo ""
            echo -e "${BOLD}正在启动 Hermes Agent...${NC}"
            echo ""
            
            if [ "$USE_VENV" = true ] && [ -d "venv" ]; then
                source venv/bin/activate
            fi
            
            hermes setup
        fi
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    print_banner
    
    echo -e "${BOLD}正在准备安装环境...${NC}"
    echo ""
    
    # 检测操作系统
    detect_os
    print_info "操作系统: $OS ${DISTRO:+($DISTRO)}"
    
    # 检查依赖
    check_python
    check_git
    
    # 创建目录
    create_directories

    # 克隆或验证中文版仓库（支持 curl | bash 模式）
    clone_repository
    
    # 创建虚拟环境
    create_venv
    
    # 安装依赖
    install_dependencies
    
    # 显示完成信息
    show_completion
}

# 运行主函数
main "$@"
