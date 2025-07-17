#!/bin/bash
# RAG Pipeline 本地測試腳本
# 使用 podman 或 docker 進行本地測試

set -e

# 配置變數
PROJECT_ROOT="/home/bai/Desktop/Podwise"
RAG_PIPELINE_DIR="${PROJECT_ROOT}/backend/rag_pipeline"
DEPLOY_DIR="${PROJECT_ROOT}/deploy/k8s/rag-pipeline"
COMPOSE_FILE="${DEPLOY_DIR}/docker-compose-local-test.yml"

# 顏色輸出
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

# 檢查容器引擎
check_container_engine() {
    log_info "檢查容器引擎..."
    
    if command -v podman &> /dev/null; then
        CONTAINER_ENGINE="podman"
        log_success "使用 Podman"
    elif command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
        log_success "使用 Docker"
    else
        log_error "未找到 Podman 或 Docker"
        exit 1
    fi
}

# 檢查必要檔案
check_files() {
    log_info "檢查必要檔案..."
    
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "找不到 docker-compose 檔案: ${COMPOSE_FILE}"
        exit 1
    fi
    
    if [ ! -f "${RAG_PIPELINE_DIR}/requirements-minimal.txt" ]; then
        log_error "找不到最小化 requirements 檔案"
        exit 1
    fi
    
    if [ ! -f "${RAG_PIPELINE_DIR}/start-rag-service.sh" ]; then
        log_error "找不到啟動腳本"
        exit 1
    fi
    
    log_success "必要檔案檢查完成"
}

# 清理舊容器
cleanup_old_containers() {
    log_info "清理舊容器..."
    
    # 停止並移除舊容器
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" down --volumes --remove-orphans 2>/dev/null || true
    
    # 清理未使用的映像
    ${CONTAINER_ENGINE} image prune -f 2>/dev/null || true
    
    log_success "清理完成"
}

# 建構映像
build_image() {
    log_info "建構 RAG Pipeline 映像..."
    
    cd "${DEPLOY_DIR}"
    
    # 使用 compose 建構
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" build --no-cache
    
    log_success "映像建構完成"
}

# 啟動服務
start_services() {
    log_info "啟動本地測試服務..."
    
    cd "${DEPLOY_DIR}"
    
    # 啟動服務
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" up -d
    
    log_success "服務啟動完成"
}

# 等待服務就緒
wait_for_service() {
    log_info "等待 RAG Pipeline 服務就緒..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8004/health &> /dev/null; then
            log_success "RAG Pipeline 服務已就緒！"
            return 0
        fi
        
        log_info "等待服務啟動... (嘗試 $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "服務啟動超時"
    return 1
}

# 檢查服務狀態
check_service_status() {
    log_info "檢查服務狀態..."
    
    # 檢查容器狀態
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" ps
    
    # 檢查網路
    ${CONTAINER_ENGINE} network ls | grep podwise || log_warning "podwise 網路不存在"
    
    # 檢查健康狀態
    if curl -f http://localhost:8004/health &> /dev/null; then
        log_success "健康檢查通過"
        curl -s http://localhost:8004/health | jq . 2>/dev/null || curl -s http://localhost:8004/health
    else
        log_warning "健康檢查失敗"
    fi
}

# 顯示測試資訊
show_test_info() {
    log_info "本地測試資訊："
    echo "服務 URL: http://localhost:8004"
    echo "健康檢查: http://localhost:8004/health"
    echo "API 文檔: http://localhost:8004/docs"
    echo "容器引擎: ${CONTAINER_ENGINE}"
    echo "網路: podwise"
    
    log_info "有用的命令："
    echo "查看日誌: ${CONTAINER_ENGINE} compose -f ${COMPOSE_FILE} logs -f rag-pipeline-local"
    echo "進入容器: ${CONTAINER_ENGINE} exec -it rag-pipeline-local /bin/bash"
    echo "停止服務: ${CONTAINER_ENGINE} compose -f ${COMPOSE_FILE} down"
    echo "重啟服務: ${CONTAINER_ENGINE} compose -f ${COMPOSE_FILE} restart rag-pipeline-local"
}

# 測試 API 端點
test_api_endpoints() {
    log_info "測試 API 端點..."
    
    local base_url="http://localhost:8004"
    
    # 測試健康檢查
    log_info "測試健康檢查端點..."
    curl -s "${base_url}/health" | jq . 2>/dev/null || curl -s "${base_url}/health"
    
    # 測試根端點
    log_info "測試根端點..."
    curl -s "${base_url}/" | jq . 2>/dev/null || curl -s "${base_url}/"
    
    # 測試 API 文檔
    log_info "測試 API 文檔端點..."
    curl -s "${base_url}/docs" | head -20
    
    log_success "API 端點測試完成"
}

# 監控日誌
monitor_logs() {
    log_info "開始監控 RAG Pipeline 日誌..."
    log_info "按 Ctrl+C 停止監控"
    
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" logs -f rag-pipeline-local
}

# 清理函數
cleanup() {
    log_info "清理資源..."
    ${CONTAINER_ENGINE} compose -f "${COMPOSE_FILE}" down --volumes
    log_success "清理完成"
}

# 主函數
main() {
    log_info "開始 RAG Pipeline 本地測試..."
    
    # 設定錯誤處理
    trap cleanup EXIT
    
    check_container_engine
    check_files
    cleanup_old_containers
    build_image
    start_services
    
    if wait_for_service; then
        check_service_status
        test_api_endpoints
        show_test_info
        
        log_success "本地測試設置完成！"
        log_info "服務已啟動，可以開始測試"
        
        # 詢問是否要監控日誌
        read -p "是否要監控日誌？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            monitor_logs
        fi
    else
        log_error "服務啟動失敗"
        exit 1
    fi
}

# 處理命令行參數
case "${1:-}" in
    "build")
        check_container_engine
        check_files
        build_image
        ;;
    "start")
        check_container_engine
        start_services
        wait_for_service
        ;;
    "stop")
        cleanup
        ;;
    "logs")
        check_container_engine
        monitor_logs
        ;;
    "test")
        check_container_engine
        test_api_endpoints
        ;;
    "status")
        check_container_engine
        check_service_status
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        main
        ;;
esac 