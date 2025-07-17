#!/bin/bash

# Podwise 分階段服務啟動腳本
# 作者: Podwise Team
# 版本: 1.0.0

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

# 檢查服務健康狀態
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "檢查 $service_name 服務健康狀態..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "$service_name 服務已就緒 (端口: $port)"
            return 0
        fi
        
        log_info "等待 $service_name 服務啟動... (嘗試 $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    log_error "$service_name 服務啟動失敗"
    return 1
}

# 顯示選單
show_menu() {
    echo -e "\n${BLUE}=== Podwise 服務管理 ===${NC}"
    echo "1. 啟動基礎服務 (Redis)"
    echo "2. 啟動 Ollama 服務"
    echo "3. 啟動 LLM 服務"
    echo "4. 啟動 TTS 服務"
    echo "5. 啟動 STT 服務"
    echo "6. 啟動 RAG Pipeline 服務"
    echo "7. 啟動前端服務"
    echo "8. 啟動所有服務"
    echo "9. 停止所有服務"
    echo "10. 查看服務狀態"
    echo "11. 查看服務日誌"
    echo "0. 退出"
    echo -e "${BLUE}=======================${NC}\n"
}

# 啟動基礎服務
start_base_services() {
    log_info "啟動基礎服務..."
    podman-compose up -d redis
    log_success "基礎服務已啟動"
    
    # 等待 Redis 啟動
    log_info "等待 Redis 啟動..."
    sleep 5
    log_info "Redis 服務已就緒"
}

# 啟動 Ollama 服務
start_ollama() {
    log_info "啟動 Ollama 服務..."
    podman-compose up -d ollama
    log_success "Ollama 服務已啟動"
    
    # 等待 Ollama 啟動
    log_info "等待 Ollama 啟動..."
    sleep 15
}

# 啟動 LLM 服務
start_llm() {
    log_info "啟動 LLM 服務..."
    podman-compose up -d llm-service
    log_success "LLM 服務已啟動"
    
    check_service_health "LLM" "8004"
}

# 啟動 TTS 服務
start_tts() {
    log_info "啟動 TTS 服務..."
    podman-compose up -d tts-service
    log_success "TTS 服務已啟動"
    
    check_service_health "TTS" "8002"
}

# 啟動 STT 服務
start_stt() {
    log_info "啟動 STT 服務..."
    podman-compose up -d stt-service
    log_success "STT 服務已啟動"
    
    check_service_health "STT" "8001"
}

# 啟動 RAG Pipeline 服務
start_rag() {
    log_info "啟動 RAG Pipeline 服務..."
    podman-compose up -d rag-pipeline
    log_success "RAG Pipeline 服務已啟動"
    
    check_service_health "RAG Pipeline" "8005"
}

# 啟動前端服務
start_frontend() {
    log_info "啟動前端服務..."
    podman-compose up -d frontend
    log_success "前端服務已啟動"
    
    log_info "前端服務地址: http://localhost"
}

# 啟動所有服務
start_all_services() {
    log_info "啟動所有服務..."
    start_base_services
    start_ollama
    start_llm
    start_tts
    start_stt
    start_rag
    start_frontend
    log_success "所有服務已啟動"
}

# 停止所有服務
stop_all_services() {
    log_info "停止所有服務..."
    podman-compose down
    log_success "所有服務已停止"
}

# 查看服務狀態
show_status() {
    log_info "服務狀態:"
    podman-compose ps
    echo ""
    log_info "容器狀態:"
    podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 查看服務日誌
show_logs() {
    echo -e "\n${BLUE}選擇要查看日誌的服務:${NC}"
    echo "1. LLM 服務"
    echo "2. TTS 服務"
    echo "3. STT 服務"
    echo "4. RAG Pipeline 服務"
    echo "5. 所有服務"
    echo "0. 返回主選單"
    
    read -p "請選擇: " log_choice
    
    case $log_choice in
        1) podman-compose logs -f llm-service ;;
        2) podman-compose logs -f tts-service ;;
        3) podman-compose logs -f stt-service ;;
        4) podman-compose logs -f rag-pipeline ;;
        5) podman-compose logs -f ;;
        0) return ;;
        *) log_error "無效選擇" ;;
    esac
}

# 主程式
main() {
    log_info "Podwise 服務管理工具"
    
    while true; do
        show_menu
        read -p "請選擇操作 (0-11): " choice
        
        case $choice in
            1) start_base_services ;;
            2) start_ollama ;;
            3) start_llm ;;
            4) start_tts ;;
            5) start_stt ;;
            6) start_rag ;;
            7) start_frontend ;;
            8) start_all_services ;;
            9) stop_all_services ;;
            10) show_status ;;
            11) show_logs ;;
            0) 
                log_info "退出服務管理工具"
                exit 0
                ;;
            *) log_error "無效選擇，請重新輸入" ;;
        esac
        
        echo ""
        read -p "按 Enter 鍵繼續..."
    done
}

# 執行主程式
main "$@" 