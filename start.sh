#!/bin/bash

# SECA 项目启动脚本
# 用法：./start.sh [backend|frontend|all]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/src/backend"
FRONTEND_DIR="${SCRIPT_DIR}/src/frontend"

# 检查 Python 虚拟环境
check_backend_env() {
    if [ ! -d "${BACKEND_DIR}/venv" ]; then
        log_error "后端虚拟环境不存在，请先创建：cd ${BACKEND_DIR} && python -m venv venv"
        return 1
    fi
}

# 检查 Node 依赖
check_frontend_env() {
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        log_warning "前端依赖未安装，正在安装..."
        cd "${FRONTEND_DIR}" && npm install
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    check_backend_env

    source "${BACKEND_DIR}/venv/bin/activate"
    cd "${BACKEND_DIR}"

    # 检查依赖
    pip install -q fastapi uvicorn sqlmodel 2>/dev/null || true

    log_info "FastAPI 服务运行在 http://localhost:8000"
    log_info "API 文档：http://localhost:8000/docs"

    # 启动 uvicorn
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    check_frontend_env

    cd "${FRONTEND_DIR}"

    log_info "Vite 开发服务器运行在 http://localhost:5173"
    log_info "API 请求将代理到 http://localhost:8000"

    # 启动 vite
    exec npm run dev
}

# 同时启动前后端（使用后台进程）
start_all() {
    log_info "启动所有服务..."

    # 检查后端环境
    check_backend_env
    check_frontend_env

    # 启动后端（后台）
    log_info "启动后端服务（后台进程）..."
    source "${BACKEND_DIR}/venv/bin/activate"
    cd "${BACKEND_DIR}"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    log_success "后端服务已启动 (PID: ${BACKEND_PID})"

    # 等待后端启动
    sleep 2

    # 启动前端（前台）
    log_info "启动前端服务..."
    cd "${FRONTEND_DIR}"
    npm run dev

    # 等待所有后台进程
    wait
}

# 显示帮助信息
show_help() {
    echo "SECA 项目启动脚本"
    echo ""
    echo "用法：$0 [命令]"
    echo ""
    echo "命令:"
    echo "  backend   - 仅启动后端 FastAPI 服务 (端口 8000)"
    echo "  frontend  - 仅启动前端 Vite 服务 (端口 5173)"
    echo "  all       - 同时启动前后端服务（默认）"
    echo "  help      - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 启动所有服务"
    echo "  $0 backend  # 仅启动后端"
    echo "  $0 frontend # 仅启动前端"
}

# 主逻辑
case "${1:-all}" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        start_all
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        log_error "未知命令：$1"
        show_help
        exit 1
        ;;
esac
