#!/usr/bin/env bash
# ==============================================================================
# 文件名称: start.sh
# 文件说明: NodeHarbor 代理节点管理平台一键启动脚本
# 功能概述:
#   1. 检查并初始化 Python 虚拟环境（符合虚拟环境规范，自动安装后端依赖）
#   2. 检查并安装前端 Node.js 依赖（自动执行 npm install）
#   3. 后台启动 FastAPI 后端服务（默认端口: 8000，输出日志到 logs/backend.log）
#   4. 后台启动 Vite 前端开发服务器（默认端口: 5173，输出日志到 logs/frontend.log）
#   5. 保存 PID 文件并进行健康检查，输出服务访问地址与默认账号信息
#
# 使用方式:
#   chmod +x start.sh
#   ./start.sh
#
# 环境变量可配置项:
#   HOST            服务监听IP（默认 0.0.0.0）
#   BACKEND_PORT    后端端口（默认 8000）
#   FRONTEND_PORT   前端端口（默认 5173）
# ==============================================================================

# 设置字符集与基础配置
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 脚本所在根目录绝对路径
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
LOG_DIR="${ROOT_DIR}/logs"

# 进程 PID 文件路径
BACKEND_PID_FILE="${LOG_DIR}/backend.pid"
FRONTEND_PID_FILE="${LOG_DIR}/frontend.pid"

# 默认配置（后端使用 8001 端口以避免与系统现有 8000 容器冲突）
HOST="${HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"


# 终端输出颜色定义
COLOR_RESET="\033[0m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_RED="\033[31m"
COLOR_CYAN="\033[36m"
COLOR_BOLD="\033[1m"

# ------------------------------------------------------------------------------
# 函数: log_info / log_success / log_warning / log_error
# 作用: 格式化打印各级别日志
# ------------------------------------------------------------------------------
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

# ------------------------------------------------------------------------------
# 函数: check_process_running
# 作用: 检查指定 PID 是否在运行中
# 参数: $1 - PID
# 返回: 0 (运行中), 1 (未运行)
# ------------------------------------------------------------------------------
check_process_running() {
    local pid="$1"
    if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 函数: check_port_in_use
# 作用: 检查指定端口是否已被占用
# 参数: $1 - 端口号
# 返回: 0 (被占用), 1 (空闲)
# ------------------------------------------------------------------------------
check_port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"${port}" -sTCP:LISTEN -P -n >/dev/null 2>&1 && return 0
    elif command -v ss >/dev/null 2>&1; then
        ss -tln | grep -q ":${port} " && return 0
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tln | grep -q ":${port} " && return 0
    fi
    return 1
}

# ------------------------------------------------------------------------------
# 函数: wait_for_port
# 作用: 等待指定端口启动就绪
# 参数: $1 - 端口号, $2 - 最长等待时间(秒), $3 - 服务名称
# ------------------------------------------------------------------------------
wait_for_port() {
    local port="$1"
    local timeout="$2"
    local service_name="$3"
    local elapsed=0

    while [ ${elapsed} -lt "${timeout}" ]; do
        if check_port_in_use "${port}"; then
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    return 1
}

# ------------------------------------------------------------------------------
# 步骤 0: 创建日志与运行目录
# ------------------------------------------------------------------------------
mkdir -p "${LOG_DIR}"

echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}          NodeHarbor 一键启动程序                  ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"

# ------------------------------------------------------------------------------
# 步骤 1: 检查是否已经有实例在运行
# ------------------------------------------------------------------------------
backend_already_running=false
frontend_already_running=false

if [ -f "${BACKEND_PID_FILE}" ]; then
    old_pid=$(cat "${BACKEND_PID_FILE}")
    if check_process_running "${old_pid}"; then
        log_warning "后端服务已在运行 (PID: ${old_pid})"
        backend_already_running=true
    fi
fi

if [ -f "${FRONTEND_PID_FILE}" ]; then
    old_pid=$(cat "${FRONTEND_PID_FILE}")
    if check_process_running "${old_pid}"; then
        log_warning "前端服务已在运行 (PID: ${old_pid})"
        frontend_already_running=true
    fi
fi

if [ "${backend_already_running}" = true ] && [ "${frontend_already_running}" = true ]; then
    log_info "所有服务均已启动，无需重复启动。若需重启请先执行 ./stop.sh"
    exit 0
fi

# ------------------------------------------------------------------------------
# 步骤 2: 准备 Python 虚拟环境与后端依赖
# ------------------------------------------------------------------------------
if [ "${backend_already_running}" = false ]; then
    log_info "正在准备后端 Python 虚拟环境..."

    # 优先检测项目内虚拟环境，其次检查系统默认虚拟环境位置
    VENV_PATH=""
    if [ -d "${BACKEND_DIR}/.venv" ]; then
        VENV_PATH="${BACKEND_DIR}/.venv"
    elif [ -d "${BACKEND_DIR}/venv" ]; then
        VENV_PATH="${BACKEND_DIR}/venv"
    elif [ -d "${ROOT_DIR}/.venv" ]; then
        VENV_PATH="${ROOT_DIR}/.venv"
    elif [ -d "/root/venv" ]; then
        VENV_PATH="/root/venv"
    else
        # 不存在虚拟环境时，使用 python3 自动在 backend/.venv 创建
        log_info "未检测到现有虚拟环境，正在创建后端独立虚拟环境: ${BACKEND_DIR}/.venv ..."
        if ! python3 -m venv "${BACKEND_DIR}/.venv"; then
            log_error "创建 Python 虚拟环境失败，请确认系统已安装 python3-venv 包。"
            exit 1
        fi
        VENV_PATH="${BACKEND_DIR}/.venv"
    fi

    # 激活虚拟环境
    log_info "激活虚拟环境: ${VENV_PATH}"
    # shellcheck disable=SC1090
    source "${VENV_PATH}/bin/activate"

    # 校验 uvicorn / fastapi 是否已安装，未安装则自动执行 pip install
    if ! command -v uvicorn >/dev/null 2>&1; then
        log_info "检测到虚拟环境中缺少依赖，正在安装 backend/requirements.txt ..."
        pip install -r "${BACKEND_DIR}/requirements.txt"
    fi

    # 检查后端端口占用情况
    if check_port_in_use "${BACKEND_PORT}"; then
        log_error "后端端口 ${BACKEND_PORT} 已被占用，请先释放该端口或在启动前设置 BACKEND_PORT 环境变量。"
        exit 1
    fi

    # 启动后端服务
    log_info "正在启动 FastAPI 后端服务 (端口: ${BACKEND_PORT})..."
    cd "${BACKEND_DIR}" || exit 1
    nohup uvicorn app.main:app --host "${HOST}" --port "${BACKEND_PORT}" > "${LOG_DIR}/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "${BACKEND_PID}" > "${BACKEND_PID_FILE}"
    log_info "后端服务已在后台启动 (PID: ${BACKEND_PID})"
fi

# ------------------------------------------------------------------------------
# 步骤 3: 准备 Node.js 环境与前端依赖
# ------------------------------------------------------------------------------
if [ "${frontend_already_running}" = false ]; then
    log_info "正在准备前端 Node.js 环境..."

    # 检查 node 和 npm 是否可用
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        log_error "未找到 node 或 npm 命令，请确保已安装 Node.js (推荐 v18+)。"
        exit 1
    fi

    # 检查 node_modules 是否存在，不存在则自动安装依赖
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        log_info "前端 node_modules 不存在，正在执行 npm install ..."
        (cd "${FRONTEND_DIR}" && npm install)
    fi

    # 检查前端端口占用情况
    if check_port_in_use "${FRONTEND_PORT}"; then
        log_warning "前端端口 ${FRONTEND_PORT} 当前已被占用，Vite 可能会自动递增端口，建议检查。"
    fi

    # 启动前端服务
    log_info "正在启动 Vite 前端服务 (默认端口: ${FRONTEND_PORT})..."
    cd "${FRONTEND_DIR}" || exit 1
    nohup npm run dev -- --host "${HOST}" --port "${FRONTEND_PORT}" > "${LOG_DIR}/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "${FRONTEND_PID}" > "${FRONTEND_PID_FILE}"
    log_info "前端服务已在后台启动 (PID: ${FRONTEND_PID})"
fi

# 返回根目录
cd "${ROOT_DIR}" || exit 1

# ------------------------------------------------------------------------------
# 步骤 4: 等待服务就绪与健康检查
# ------------------------------------------------------------------------------
log_info "正在等待服务就绪..."

if [ "${backend_already_running}" = false ]; then
    if wait_for_port "${BACKEND_PORT}" 15 "后端服务"; then
        log_success "后端服务已成功监听端口 ${BACKEND_PORT}"
    else
        log_warning "后端端口 ${BACKEND_PORT} 响应较慢或启动异常，请查看日志: ${LOG_DIR}/backend.log"
    fi
fi

if [ "${frontend_already_running}" = false ]; then
    if wait_for_port "${FRONTEND_PORT}" 15 "前端服务"; then
        log_success "前端服务已成功监听端口 ${FRONTEND_PORT}"
    else
        log_warning "前端端口 ${FRONTEND_PORT} 响应较慢或启动异常，请查看日志: ${LOG_DIR}/frontend.log"
    fi
fi

# ------------------------------------------------------------------------------
# 步骤 5: 打印运行状态与访问信息
# ------------------------------------------------------------------------------
echo ""
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_GREEN}          NodeHarbor 服务启动成功！                ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo -e "  🌍 域名访问入口   : ${COLOR_CYAN}https://node.undefinedip.com${COLOR_RESET}"
echo -e "  🔐 用户登录页面   : ${COLOR_CYAN}https://node.undefinedip.com/login${COLOR_RESET} (默认密码: admin)"
echo -e "  ⚙️  管理登录页面   : ${COLOR_CYAN}https://node.undefinedip.com/admin/login${COLOR_RESET} (默认密码: admin)"
echo -e "  📖 Swagger 文档   : ${COLOR_CYAN}https://node.undefinedip.com/docs${COLOR_RESET}"
echo -e "----------------------------------------------------"
echo -e "  🌐 本地前端地址   : http://localhost:${FRONTEND_PORT}"
echo -e "  🚀 本地后端地址   : http://localhost:${BACKEND_PORT}"
echo -e "  📄 后端日志文件   : ${LOG_DIR}/backend.log"
echo -e "  📄 前端日志文件   : ${LOG_DIR}/frontend.log"
echo -e "  🛑 停止服务命令   : ./stop.sh"
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo ""
