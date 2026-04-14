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

# 检查端口是否可用
check_port_available() {
    local port=$1
    local service_name=$2

    # 尝试多种工具检查端口占用
    if command -v lsof &> /dev/null; then
        if lsof -i :${port} &> /dev/null; then
            log_error "${service_name} 端口 ${port} 已被占用"
            log_info "占用进程："
            lsof -i :${port}
            return 1
        fi
    elif command -v ss &> /dev/null; then
        if ss -tln | grep -q ":${port} "; then
            log_error "${service_name} 端口 ${port} 已被占用"
            log_info "占用详情："
            ss -tln | grep ":${port}"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tln | grep -q ":${port} "; then
            log_error "${service_name} 端口 ${port} 已被占用"
            log_info "占用详情："
            netstat -tln | grep ":${port}"
            return 1
        fi
    fi
    return 0
}

# 检查进程是否已运行
check_process_running() {
    local pattern=$1
    if pgrep -f "$pattern" > /dev/null; then
        log_warning "进程已运行：$pattern"
        pgrep -af "$pattern"
        return 0
    fi
    return 1
}

# 等待端口就绪（重试最多 N 次）
wait_for_port() {
    local port=$1
    local max_attempts=${2:-30}
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if command -v ss &> /dev/null; then
            if ss -tln | grep -q ":${port} "; then
                return 0
            fi
        elif command -v netstat &> /dev/null; then
            if netstat -tln | grep -q ":${port} "; then
                return 0
            fi
        else
            #  fallback: 尝试连接
            if echo > /dev/tcp/localhost/${port} 2>/dev/null; then
                return 0
            fi
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

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

    # 检查端口是否已被占用
    if ! check_port_available 8000 "后端服务"; then
        log_error "请先停止占用端口 8000 的进程，或手动指定其他端口"
        return 1
    fi

    # 检查是否已有 uvicorn 进程在运行
    if check_process_running "uvicorn app.main:app"; then
        log_warning "后端服务似乎已经在运行"
        log_info "如需重启，请先停止现有进程：pkill -f 'uvicorn app.main:app'"
        return 1
    fi

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

    # 检查端口是否已被占用
    if ! check_port_available 5173 "前端服务"; then
        log_error "请先停止占用端口 5173 的进程，或手动指定其他端口"
        return 1
    fi

    # 检查是否已有 vite 进程在运行
    if check_process_running "vite"; then
        log_warning "前端服务似乎已经在运行"
        log_info "如需重启，请先停止现有进程：pkill -f 'vite'"
        return 1
    fi

    cd "${FRONTEND_DIR}"

    log_info "Vite 开发服务器运行在 http://localhost:5173"
    log_info "API 请求将代理到 http://localhost:8000"

    # 启动 vite
    exec npm run dev
}

# 同时启动前后端（使用后台进程）
start_all() {
    log_info "启动所有服务..."

    # 检查端口占用
    if ! check_port_available 8000 "后端服务"; then
        log_error "后端端口 8000 已被占用，请先停止现有服务"
        return 1
    fi
    if ! check_port_available 5173 "前端服务"; then
        log_error "前端端口 5173 已被占用，请先停止现有服务"
        return 1
    fi

    # 检查后端环境
    check_backend_env
    check_frontend_env

    # 启动后端（后台）
    log_info "启动后端服务（后台进程）..."
    source "${BACKEND_DIR}/venv/bin/activate"
    cd "${BACKEND_DIR}"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!

    # 等待后端端口就绪
    log_info "等待后端服务就绪..."
    if wait_for_port 8000 15; then
        log_success "后端服务已启动 (PID: ${BACKEND_PID})"
    else
        log_error "后端服务启动失败，请检查日志"
        kill ${BACKEND_PID} 2>/dev/null || true
        return 1
    fi

    # 启动前端（前台）
    log_info "启动前端服务..."
    cd "${FRONTEND_DIR}"
    npm run dev

    # 等待所有后台进程
    wait
}

# 重启后端服务
restart_backend() {
    log_info "重启后端服务..."

    # 停止现有进程
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_info "停止现有后端进程..."
        pkill -f "uvicorn app.main:app"
        sleep 2
    fi

    # 等待端口释放
    log_info "等待端口 8000 释放..."
    local attempts=0
    while [ $attempts -lt 10 ]; do
        if check_port_available 8000 "后端服务"; then
            break
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    # 启动新进程
    start_backend
}

# 重启前端服务
restart_frontend() {
    log_info "重启前端服务..."

    # 停止现有进程
    if pgrep -f "vite" > /dev/null; then
        log_info "停止现有前端进程..."
        pkill -f "vite"
        sleep 2
    fi

    # 等待端口释放
    log_info "等待端口 5173 释放..."
    local attempts=0
    while [ $attempts -lt 10 ]; do
        if check_port_available 5173 "前端服务"; then
            break
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    # 启动新进程
    start_frontend
}

# 重启所有服务
restart_all() {
    log_info "重启所有服务..."

    # 停止后端
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_info "停止后端进程..."
        pkill -f "uvicorn app.main:app"
    fi

    # 停止前端
    if pgrep -f "vite" > /dev/null; then
        log_info "停止前端进程..."
        pkill -f "vite"
    fi

    # 等待端口释放
    log_info "等待端口释放..."
    sleep 3

    # 启动所有
    start_all
}

# 显示帮助信息
show_help() {
    echo "SECA 项目启动脚本"
    echo ""
    echo "用法：$0 [命令]"
    echo ""
    echo "命令:"
    echo "  backend     - 仅启动后端 FastAPI 服务 (端口 8000)"
    echo "  frontend    - 仅启动前端 Vite 服务 (端口 5173)"
    echo "  all         - 同时启动前后端服务（默认）"
    echo "  restart     - 重启所有服务"
    echo "  restart-be  - 仅重启后端服务"
    echo "  restart-fe  - 仅重启前端服务"
    echo "  stop        - 停止所有服务"
    echo "  status      - 查看服务运行状态"
    echo "  help        - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0            # 启动所有服务"
    echo "  $0 backend    # 仅启动后端"
    echo "  $0 restart    # 重启所有服务"
    echo "  $0 status     # 查看服务状态"
}

# 停止所有服务
stop_all() {
    log_info "停止所有服务..."

    # 停止后端
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_info "停止后端进程..."
        pkill -f "uvicorn app.main:app"
        log_success "后端服务已停止"
    else
        log_info "后端服务未运行"
    fi

    # 停止前端
    if pgrep -f "vite" > /dev/null; then
        log_info "停止前端进程..."
        pkill -f "vite"
        log_success "前端服务已停止"
    else
        log_info "前端服务未运行"
    fi
}

# 查看服务状态
status_all() {
    echo ""
    log_info "=== 服务运行状态 ==="
    echo ""

    # 后端状态
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        log_success "后端服务：运行中"
        pgrep -af "uvicorn app.main:app"
        if command -v ss &> /dev/null; then
            ss -tln | grep ":8000" || true
        fi
    else
        log_warning "后端服务：未运行"
    fi
    echo ""

    # 前端状态
    if pgrep -f "vite" > /dev/null; then
        log_success "前端服务：运行中"
        pgrep -af "vite"
        if command -v ss &> /dev/null; then
            ss -tln | grep ":5173" || true
        fi
    else
        log_warning "前端服务：未运行"
    fi
    echo ""
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
    restart)
        restart_all
        ;;
    restart-be)
        restart_backend
        ;;
    restart-fe)
        restart_frontend
        ;;
    stop)
        stop_all
        ;;
    status)
        status_all
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
