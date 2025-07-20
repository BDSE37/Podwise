#!/bin/bash

# Podwise 完整專案啟動腳本
# 穩定版本 - 啟動核心服務

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

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

# 檢查端口是否被佔用
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # 端口被佔用
        else
            return 1  # 端口可用
        fi
    else
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            return 0  # 端口被佔用
        else
            return 1  # 端口可用
        fi
    fi
}

# 啟動 TTS 服務
start_tts() {
    log_info "啟動 TTS 服務 (端口: 8002)"
    
    if check_port 8002; then
        log_warning "端口 8002 已被佔用，跳過 TTS"
        return 0
    fi
    
    cd backend/tts
    nohup python3 main.py > ../logs/tts.log 2>&1 &
    echo $! > ../logs/tts.pid
    cd "$PROJECT_ROOT"
    
    sleep 10
    if check_port 8002; then
        log_success "TTS 服務啟動成功"
        return 0
    else
        log_error "TTS 服務啟動失敗"
        return 1
    fi
}

# 啟動 LLM 服務
start_llm() {
    log_info "啟動 LLM 服務 (端口: 8006)"
    
    if check_port 8006; then
        log_warning "端口 8006 已被佔用，跳過 LLM"
        return 0
    fi
    
    cd backend/llm
    nohup python3 main.py > ../logs/llm.log 2>&1 &
    echo $! > ../logs/llm.pid
    cd "$PROJECT_ROOT"
    
    sleep 10
    if check_port 8006; then
        log_success "LLM 服務啟動成功"
        return 0
    else
        log_error "LLM 服務啟動失敗"
        return 1
    fi
}

# 啟動 RAG Pipeline 服務
start_rag_pipeline() {
    log_info "啟動 RAG Pipeline 服務 (端口: 8005)"
    
    if check_port 8005; then
        log_warning "端口 8005 已被佔用，跳過 RAG Pipeline"
        return 0
    fi
    
    cd backend/rag_pipeline
    nohup python3 main.py > ../logs/rag_pipeline.log 2>&1 &
    echo $! > ../logs/rag_pipeline.pid
    cd "$PROJECT_ROOT"
    
    sleep 10
    if check_port 8005; then
        log_success "RAG Pipeline 服務啟動成功"
        return 0
    else
        log_error "RAG Pipeline 服務啟動失敗"
        return 1
    fi
}

# 啟動前端服務
start_frontend() {
    log_info "啟動前端服務 (端口: 8081)"
    
    if check_port 8081; then
        log_warning "端口 8081 已被佔用，跳過前端"
        return 0
    fi
    
    cd frontend
    nohup python3 fastapi_app.py > ../logs/frontend.log 2>&1 &
    echo $! > ../logs/frontend.pid
    cd "$PROJECT_ROOT"
    
    sleep 10
    if check_port 8081; then
        log_success "前端服務啟動成功"
        return 0
    else
        log_error "前端服務啟動失敗"
        return 1
    fi
}

# 啟動所有服務
start_all() {
    echo "🚀 啟動 Podwise 專案服務..."
    echo "================================"
    
    # 創建日誌目錄
    mkdir -p logs backend/logs
    
    # 順序啟動服務
    start_tts
    sleep 5
    
    start_llm
    sleep 5
    
    start_rag_pipeline
    sleep 5
    
    start_frontend
    
    echo ""
    echo "🌐 服務信息:"
    echo "  前端服務: http://localhost:8081"
    echo "  TTS 服務: http://localhost:8002"
    echo "  LLM 服務: http://localhost:8006"
    echo "  RAG Pipeline: http://localhost:8005"
    echo ""
    echo "按 Ctrl+C 停止所有服務"
    
    # 等待用戶中斷
    trap stop_all INT
    wait
}

# 停止所有服務
stop_all() {
    echo ""
    log_info "停止所有服務..."
    
    # 停止前端
    if [ -f "logs/frontend.pid" ]; then
        kill $(cat logs/frontend.pid) 2>/dev/null
        rm -f logs/frontend.pid
        log_success "前端服務已停止"
    fi
    
    # 停止後端服務
    cd backend
    
    if [ -f "logs/tts.pid" ]; then
        kill $(cat logs/tts.pid) 2>/dev/null
        rm -f logs/tts.pid
        log_success "TTS 服務已停止"
    fi
    
    if [ -f "logs/llm.pid" ]; then
        kill $(cat logs/llm.pid) 2>/dev/null
        rm -f logs/llm.pid
        log_success "LLM 服務已停止"
    fi
    
    if [ -f "logs/rag_pipeline.pid" ]; then
        kill $(cat logs/rag_pipeline.pid) 2>/dev/null
        rm -f logs/rag_pipeline.pid
        log_success "RAG Pipeline 服務已停止"
    fi
    
    cd "$PROJECT_ROOT"
    log_success "所有服務已停止"
}

# 檢查服務狀態
check_status() {
    echo "📊 服務狀態檢查..."
    echo "=================="
    
    if check_port 8081; then
        log_success "前端服務: 運行中 (端口: 8081)"
    else
        log_error "前端服務: 未運行 (端口: 8081)"
    fi
    
    if check_port 8002; then
        log_success "TTS 服務: 運行中 (端口: 8002)"
    else
        log_error "TTS 服務: 未運行 (端口: 8002)"
    fi
    
    if check_port 8006; then
        log_success "LLM 服務: 運行中 (端口: 8006)"
    else
        log_error "LLM 服務: 未運行 (端口: 8006)"
    fi
    
    if check_port 8005; then
        log_success "RAG Pipeline: 運行中 (端口: 8005)"
    else
        log_error "RAG Pipeline: 未運行 (端口: 8005)"
    fi
}

# 主函數
case "${1:-start}" in
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "status")
        check_status
        ;;
    "restart")
        stop_all
        sleep 2
        start_all
        ;;
    *)
        echo "用法: $0 [start|stop|status|restart]"
        echo ""
        echo "命令說明:"
        echo "  start   - 啟動所有服務 (預設)"
        echo "  stop    - 停止所有服務"
        echo "  status  - 檢查服務狀態"
        echo "  restart - 重新啟動所有服務"
        ;;
esac 