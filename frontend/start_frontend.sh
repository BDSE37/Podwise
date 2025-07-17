#!/bin/bash

# PodWise 前端啟動腳本
# 基於原有的 nginx-proxy.conf 配置
# 啟動 FastAPI 前端和 nginx 代理

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
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

# 檢查服務是否運行
check_service() {
    local port=$1
    local service_name=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        log_success "$service_name 已在端口 $port 運行"
        return 0
    else
        log_warning "$service_name 未在端口 $port 運行"
        return 1
    fi
}

# 啟動 FastAPI 前端應用
start_fastapi_frontend() {
    log_info "啟動 FastAPI 前端應用..."
    cd "$(dirname "$0")/home"
    
    if ! check_service 8081 "FastAPI 前端"; then
        python3 fastapi_app.py &
        sleep 3
        if check_service 8081 "FastAPI 前端"; then
            log_success "FastAPI 前端啟動成功"
        else
            log_error "FastAPI 前端啟動失敗"
            return 1
        fi
    fi
}

# 啟動 nginx 代理
start_nginx_proxy() {
    log_info "啟動 Nginx 代理..."
    
    # 檢查 nginx 是否已安裝
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx 未安裝，請先安裝 nginx"
        return 1
    fi
    
    # 停止現有的 nginx
    sudo systemctl stop nginx 2>/dev/null || true
    
    # 複製配置文件
    sudo cp "$(dirname "$0")/nginx-unified.conf" /etc/nginx/sites-available/podwise-unified
    sudo ln -sf /etc/nginx/sites-available/podwise-unified /etc/nginx/sites-enabled/
    
    # 測試配置
    if sudo nginx -t; then
        sudo systemctl start nginx
        sleep 2
        if check_service 80 "Nginx 代理"; then
            log_success "Nginx 代理啟動成功"
        else
            log_error "Nginx 代理啟動失敗"
            return 1
        fi
    else
        log_error "Nginx 配置測試失敗"
        return 1
    fi
}

# 顯示服務狀態
show_status() {
    log_info "服務狀態檢查："
    echo "----------------------------------------"
    
    local services=(
        "80:Nginx 代理"
        "8081:FastAPI 前端"
        "8000:後端 API"
        "8001:RAG Pipeline"
        "8002:TTS 服務"
        "8003:STT 服務"
        "8004:LLM 服務"
        "8005:ML Pipeline"
        "8006:推薦服務"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        if check_service "$port" "$name"; then
            echo -e "${GREEN}✓${NC} $name (端口 $port)"
        else
            echo -e "${RED}✗${NC} $name (端口 $port)"
        fi
    done
    
    echo "----------------------------------------"
    log_info "統一訪問地址："
    echo "  主頁面: http://localhost/"
    echo "  Podri 聊天: http://localhost/podri"
    echo "  健康檢查: http://localhost/health"
    echo "  系統狀態: http://localhost/status"
}

# 停止所有服務
stop_services() {
    log_info "停止所有服務..."
    
    # 停止 nginx
    sudo systemctl stop nginx 2>/dev/null || true
    
    # 停止 Python 進程
    pkill -f "fastapi_app.py" 2>/dev/null || true
    
    log_success "所有服務已停止"
}

# 主函數
main() {
    case "${1:-start}" in
        "start")
            log_info "啟動 PodWise 前端服務..."
            start_fastapi_frontend
            start_nginx_proxy
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            main start
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [start|stop|restart|status|help]"
            echo ""
            echo "命令："
            echo "  start   - 啟動 FastAPI 前端和 nginx 代理"
            echo "  stop    - 停止所有服務"
            echo "  restart - 重新啟動所有服務"
            echo "  status  - 顯示服務狀態"
            echo "  help    - 顯示此幫助信息"
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@" 