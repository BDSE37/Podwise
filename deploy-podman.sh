#!/bin/bash
"""
Podwise Podman 部署腳本
使用 Podman 建置和部署整個 Podwise 系統
"""

set -e  # 遇到錯誤立即退出

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

# 檢查 Podman 是否安裝
check_podman() {
    log_info "檢查 Podman 安裝狀態..."
    
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝，請先安裝 Podman"
        exit 1
    fi
    
    podman_version=$(podman --version)
    log_success "Podman 已安裝: $podman_version"
}

# 檢查 Podman Compose 是否安裝
check_podman_compose() {
    log_info "檢查 Podman Compose 安裝狀態..."
    
    if ! command -v podman-compose &> /dev/null; then
        log_warning "Podman Compose 未安裝，嘗試使用 docker-compose..."
        
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose 也未安裝，請安裝其中之一"
            exit 1
        fi
        
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="podman-compose"
    fi
    
    log_success "使用 $COMPOSE_CMD"
}

# 建置映像
build_images() {
    log_info "開始建置 Podwise 映像..."
    
    # 建置 RAG Pipeline
    log_info "建置 RAG Pipeline 映像..."
    podman build -t localhost/podwise/rag_pipeline:latest ./backend/rag_pipeline
    log_success "RAG Pipeline 映像建置完成"
    
    # 建置 TTS 服務
    log_info "建置 TTS 服務映像..."
    podman build -t localhost/podwise/tts:latest ./backend/tts
    log_success "TTS 服務映像建置完成"
    
    # 建置 STT 服務
    log_info "建置 STT 服務映像..."
    podman build -t localhost/podwise/stt:latest ./backend/stt
    log_success "STT 服務映像建置完成"
    
    # 建置 LLM 服務
    log_info "建置 LLM 服務映像..."
    podman build -t localhost/podwise/llm:latest ./backend/llm
    log_success "LLM 服務映像建置完成"
    
    # 建置前端
    log_info "建置前端映像..."
    podman build -t localhost/podwise/frontend:latest ./frontend
    log_success "前端映像建置完成"
    
    log_success "所有映像建置完成"
}

# 啟動服務
start_services() {
    log_info "啟動 Podwise 服務..."
    
    # 使用 docker-compose 或 podman-compose 啟動服務
    $COMPOSE_CMD up -d
    
    log_success "服務啟動完成"
}

# 檢查服務狀態
check_services() {
    log_info "檢查服務狀態..."
    
    # 等待服務啟動
    sleep 10
    
    # 檢查容器狀態
    $COMPOSE_CMD ps
    
    # 檢查健康狀態
    log_info "檢查服務健康狀態..."
    
    # 檢查 RAG Pipeline
    if curl -f http://localhost:8004/health &> /dev/null; then
        log_success "RAG Pipeline 健康檢查通過"
    else
        log_warning "RAG Pipeline 健康檢查失敗"
    fi
    
    # 檢查 TTS 服務
    if curl -f http://localhost:8002/health &> /dev/null; then
        log_success "TTS 服務健康檢查通過"
    else
        log_warning "TTS 服務健康檢查失敗"
    fi
    
    # 檢查 STT 服務
    if curl -f http://localhost:8001/health &> /dev/null; then
        log_success "STT 服務健康檢查通過"
    else
        log_warning "STT 服務健康檢查失敗"
    fi
}

# 顯示服務資訊
show_service_info() {
    log_info "Podwise 服務資訊:"
    echo ""
    echo "🌐 前端介面: http://localhost:3000"
    echo "📚 API 文件: http://localhost:8004/docs"
    echo "🎵 TTS 服務: http://localhost:8002"
    echo "🎤 STT 服務: http://localhost:8001"
    echo "🧠 LLM 服務: http://localhost:8000"
    echo "🗄️  PostgreSQL: localhost:5432"
    echo "📊 MongoDB: localhost:27017"
    echo "🔍 Milvus: localhost:19530"
    echo "💾 MinIO: http://localhost:9000"
    echo ""
    log_success "部署完成！"
}

# 停止服務
stop_services() {
    log_info "停止 Podwise 服務..."
    $COMPOSE_CMD down
    log_success "服務已停止"
}

# 清理資源
cleanup() {
    log_info "清理 Podman 資源..."
    
    # 停止所有容器
    podman stop $(podman ps -q) 2>/dev/null || true
    
    # 移除所有容器
    podman rm $(podman ps -aq) 2>/dev/null || true
    
    # 移除所有映像
    podman rmi $(podman images -q) 2>/dev/null || true
    
    log_success "清理完成"
}

# 顯示幫助
show_help() {
    echo "Podwise Podman 部署腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  build     建置所有映像"
    echo "  start     啟動所有服務"
    echo "  stop      停止所有服務"
    echo "  restart   重啟所有服務"
    echo "  status    檢查服務狀態"
    echo "  cleanup   清理所有資源"
    echo "  deploy    完整部署（建置 + 啟動）"
    echo "  help      顯示此幫助"
    echo ""
}

# 主函數
main() {
    case "${1:-deploy}" in
        "build")
            check_podman
            build_images
            ;;
        "start")
            check_podman
            check_podman_compose
            start_services
            check_services
            show_service_info
            ;;
        "stop")
            check_podman_compose
            stop_services
            ;;
        "restart")
            check_podman_compose
            stop_services
            sleep 5
            start_services
            check_services
            ;;
        "status")
            check_podman_compose
            $COMPOSE_CMD ps
            ;;
        "cleanup")
            check_podman
            cleanup
            ;;
        "deploy")
            check_podman
            check_podman_compose
            build_images
            start_services
            check_services
            show_service_info
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@" 