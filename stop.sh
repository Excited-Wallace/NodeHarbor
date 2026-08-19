#!/usr/bin/env bash
# ==============================================================================
# 文件名称: stop.sh
# 文件说明: NodeHarbor 代理节点管理平台一键停止脚本
# 功能概述:
#   1. 读取后端 (backend.pid) 和前端 (frontend.pid) 进程 PID
#   2. 发送 SIGTERM (kill -15) 进行平滑停止，并等待进程退出
#   3. 若超时仍未停止，则发送 SIGKILL (kill -9) 进行强制终止
#   4. 检查并清理端口占用与残留的相关进程 (uvicorn / vite)
#   5. 清理 PID 文件并输出停止状态总结
#
# 使用方式:
#   chmod +x stop.sh
#   ./stop.sh
# ==============================================================================

# 设置字符集与基础配置
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 脚本所在根目录绝对路径
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"

# 进程 PID 文件路径
BACKEND_PID_FILE="${LOG_DIR}/backend.pid"
FRONTEND_PID_FILE="${LOG_DIR}/frontend.pid"

# 默认端口定义（用于辅助检查残留进程，与 start.sh 保持一致）
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
# 函数: stop_process_by_pid
# 作用: 安全终止指定 PID 的进程，支持超时强制终止
# 参数: $1 - 进程名称, $2 - PID, $3 - PID 文件路径
# ------------------------------------------------------------------------------
stop_process_by_pid() {
    local service_name="$1"
    local pid="$2"
    local pid_file="$3"

    if [ -z "${pid}" ]; then
        return 0
    fi

    if kill -0 "${pid}" 2>/dev/null; then
        log_info "正在停止 ${service_name} (PID: ${pid})..."
        kill -15 "${pid}" 2>/dev/null

        # 等待最多 5 秒让进程优雅退出
        local count=0
        while kill -0 "${pid}" 2>/dev/null && [ ${count} -lt 5 ]; do
            sleep 1
            count=$((count + 1))
        done

        # 如果进程仍未退出，执行强制 kill -9
        if kill -0 "${pid}" 2>/dev/null; then
            log_warning "${service_name} 未在 5 秒内退出，正在强制终止 (kill -9)..."
            kill -9 "${pid}" 2>/dev/null
            sleep 1
        fi

        if ! kill -0 "${pid}" 2>/dev/null; then
            log_success "${service_name} 已成功停止"
        else
            log_error "无法停止 ${service_name} (PID: ${pid})，请手动排查"
        fi
    else
        log_warning "${service_name} (PID: ${pid}) 未在运行"
    fi

    # 清理 PID 文件
    if [ -f "${pid_file}" ]; then
        rm -f "${pid_file}"
    fi
}

# ------------------------------------------------------------------------------
# 函数: cleanup_port_processes
# 作用: 辅助清理指定端口上残留的进程
# 参数: $1 - 端口号, $2 - 服务名称
# ------------------------------------------------------------------------------
cleanup_port_processes() {
    local port="$1"
    local service_name="$2"

    if command -v lsof >/dev/null 2>&1; then
        local pids
        pids=$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null)
        if [ -n "${pids}" ]; then
            log_warning "发现端口 ${port} 上仍有残留进程 (PID: ${pids})，正在清理..."
            # shellcheck disable=SC2086
            kill -9 ${pids} 2>/dev/null
            log_success "端口 ${port} 残留进程已清理"
        fi
    elif command -v fuser >/dev/null 2>&1; then
        if fuser "${port}/tcp" >/dev/null 2>&1; then
            log_warning "发现端口 ${port} 上仍有残留进程，正在使用 fuser 清理..."
            fuser -k -9 "${port}/tcp" >/dev/null 2>&1
            log_success "端口 ${port} 残留进程已清理"
        fi
    fi
}

echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}          NodeHarbor 一键停止程序                  ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_CYAN}====================================================${COLOR_RESET}"

# ------------------------------------------------------------------------------
# 步骤 1: 停止后端服务
# ------------------------------------------------------------------------------
if [ -f "${BACKEND_PID_FILE}" ]; then
    BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
    stop_process_by_pid "FastAPI 后端服务" "${BACKEND_PID}" "${BACKEND_PID_FILE}"
else
    log_warning "未找到后端 PID 文件 (${BACKEND_PID_FILE})"
fi

# 检查并清理可能残留的后端端口
cleanup_port_processes "${BACKEND_PORT}" "FastAPI 后端服务"

# ------------------------------------------------------------------------------
# 步骤 2: 停止前端服务
# ------------------------------------------------------------------------------
if [ -f "${FRONTEND_PID_FILE}" ]; then
    FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
    stop_process_by_pid "Vite 前端服务" "${FRONTEND_PID}" "${FRONTEND_PID_FILE}"
else
    log_warning "未找到前端 PID 文件 (${FRONTEND_PID_FILE})"
fi

# 检查并清理可能残留的前端端口
cleanup_port_processes "${FRONTEND_PORT}" "Vite 前端服务"

# ------------------------------------------------------------------------------
# 步骤 3: 辅助清理可能孤立的 uvicorn/vite 进程
# ------------------------------------------------------------------------------
if command -v pgrep >/dev/null 2>&1; then
    stray_uvicorn=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)
    if [ -n "${stray_uvicorn}" ]; then
        log_warning "清理残留的 uvicorn 进程 (PID: ${stray_uvicorn})..."
        # shellcheck disable=SC2086
        kill -9 ${stray_uvicorn} 2>/dev/null
    fi
fi

# ------------------------------------------------------------------------------
# 步骤 4: 输出停止结果
# ------------------------------------------------------------------------------
echo ""
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_GREEN}          NodeHarbor 所有服务已停止！              ${COLOR_RESET}"
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo -e "  🚀 重新启动服务命令: ./start.sh"
echo -e "${COLOR_BOLD}${COLOR_GREEN}====================================================${COLOR_RESET}"
echo ""
