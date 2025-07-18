#!/bin/bash

# =============================================================================
# Podwise 專案啟動腳本 (Podman 版本)
# 使用 Podman Compose 啟動所有微服務
# =============================================================================

set -e  # 遇到錯誤時停止執行

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

# 檢查 Podman
check_podman() {
    log_info "檢查 Podman 環境..."
    
    # 檢查 Podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝，請先安裝 Podman"
        echo "安裝指令："
        echo "  Ubuntu/Debian: sudo apt-get install podman"
        echo "  CentOS/RHEL: sudo yum install podman"
        echo "  Fedora: sudo dnf install podman"
        exit 1
    fi
    
    # 檢查 Podman Compose
    if ! command -v podman-compose &> /dev/null; then
        log_warning "Podman Compose 未安裝，正在安裝..."
        if command -v pip3 &> /dev/null; then
            pip3 install podman-compose
        elif command -v pip &> /dev/null; then
            pip install podman-compose
        else
            log_error "無法安裝 Podman Compose，請手動安裝"
            echo "安裝指令：pip install podman-compose"
            exit 1
        fi
    fi
    
    # 檢查 Podman 服務狀態
    if ! podman info > /dev/null 2>&1; then
        log_error "Podman 服務未運行，請啟動 Podman 服務"
        echo "啟動指令："
        echo "  sudo systemctl start podman"
        echo "  sudo systemctl enable podman"
        exit 1
    fi
    
    log_success "Podman 環境檢查完成"
    log_info "Podman 版本: $(podman --version)"
    log_info "Podman Compose 版本: $(podman-compose --version)"
}

# 檢查環境變數文件
check_env_file() {
    log_info "檢查環境變數文件..."
    
    if [ ! -f "./backend/.env" ]; then
        log_warning "未找到 backend/.env 文件，將創建範例文件"
        cp ./backend/env.example ./backend/.env 2>/dev/null || {
            log_error "無法創建 .env 文件，請手動創建 backend/.env"
            exit 1
        }
    fi
    
    log_success "環境變數文件檢查完成"
}

# 檢查網路連接
check_network() {
    log_info "檢查外部服務連接..."
    
    # 檢查 K8s 服務連接
    local k8s_hosts=(
        "192.168.32.38:31134"  # Ollama
        "192.168.32.38:30000"  # Langfuse
        "worker3:19530"        # Milvus
    )
    
    for host in "${k8s_hosts[@]}"; do
        if ping -c 1 "${host%:*}" &> /dev/null; then
            log_success "可連接到 ${host}"
        else
            log_warning "無法連接到 ${host}，某些功能可能受限"
        fi
    done
}

# 停止現有服務
stop_existing_services() {
    log_info "停止現有服務..."
    
    if [ -f "docker-compose.yaml" ]; then
        podman-compose down --remove-orphans 2>/dev/null || true
        log_success "現有服務已停止"
    fi
}

# 清理舊的容器和映像
cleanup_old_containers() {
    log_info "清理舊的容器和映像..."
    
    # 停止並移除舊的 Podwise 容器
    podman ps -a --filter "name=podwise_" --format "{{.ID}}" | xargs -r podman rm -f 2>/dev/null || true
    
    # 清理未使用的映像
    podman image prune -f 2>/dev/null || true
    
    log_success "清理完成"
}

# 啟動服務
start_services() {
    log_info "啟動 Podwise 服務 (使用 Podman)..."
    
    # 使用 podman-compose 啟動服務
    podman-compose up -d --build
    
    if [ $? -eq 0 ]; then
        log_success "服務啟動命令執行成功"
    else
        log_error "服務啟動失敗"
        exit 1
    fi
}

# 等待服務啟動
wait_for_services() {
    log_info "等待服務啟動..."
    
    local services=(
        "postgresql:5432"
        "llm:8000"
        "stt:8001"
        "tts:8003"
        "ml_pipeline:8004"
        "rag_pipeline:8005"
        "web_search:8006"
        "frontend:8080"
        # "podri_chat:8501"  # 已移除，不再使用
    )
    
    for service in "${services[@]}"; do
        local host="${service%:*}"
        local port="${service#*:}"
        
        log_info "等待 ${host} 服務啟動 (端口: ${port})..."
        
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if timeout 5 bash -c "</dev/tcp/${host}/${port}" 2>/dev/null; then
                log_success "${host} 服務已啟動"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "${host} 服務啟動超時，但繼續執行"
            fi
            
            sleep 2
            ((attempt++))
        done
    done
}

# 顯示服務狀態
show_service_status() {
    log_info "顯示服務狀態..."
    
    echo ""
    echo "=========================================="
    echo "           Podwise 服務狀態 (Podman)"
    echo "=========================================="
    
    podman-compose ps
    
    echo ""
    echo "=========================================="
    echo "           服務訪問地址"
    echo "=========================================="
    echo "🌐 前端主頁面: http://localhost:8080"
    # echo "💬 Streamlit 聊天: http://localhost:8501"  # 已移除，不再使用
    echo "🔊 TTS 服務: http://localhost:8003"
    echo "🎤 STT 服務: http://localhost:8001"
    echo "🤖 LLM 服務: http://localhost:8000"
    echo "🔍 RAG Pipeline: http://localhost:8005"
    echo "📊 ML Pipeline: http://localhost:8004"
    echo "🌍 Web Search: http://localhost:8006"
    echo "🗄️  PostgreSQL: localhost:5432"
    echo ""
    echo "=========================================="
    echo "           監控工具"
    echo "=========================================="
    echo "📈 Grafana: http://192.168.32.38:30004"
    echo "📊 Prometheus: http://192.168.32.38:30090"
    echo "🐳 Portainer: http://192.168.32.38:30003"
    echo "🔍 Attu (Milvus): http://192.168.32.38:3101"
    echo ""
}

# 顯示日誌
show_logs() {
    log_info "顯示服務日誌..."
    
    echo ""
    echo "=========================================="
    echo "           服務日誌 (最近 10 行)"
    echo "=========================================="
    
    # 顯示主要服務的日誌
    local main_services=("rag_pipeline" "tts" "frontend")
    
    for service in "${main_services[@]}"; do
        echo ""
        echo "--- ${service} 日誌 ---"
        podman-compose logs --tail=10 $service 2>/dev/null || echo "無法獲取 ${service} 日誌"
    done
}

# 健康檢查
health_check() {
    log_info "執行健康檢查..."
    
    local health_endpoints=(
        "http://localhost:8005/health"  # RAG Pipeline
        "http://localhost:8003/health"  # TTS
        "http://localhost:8001/health"  # STT
        "http://localhost:8000/health"  # LLM
        "http://localhost:8004/health"  # ML Pipeline
        "http://localhost:8006/health"  # Web Search
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null; then
            log_success "健康檢查通過: ${endpoint}"
        else
            log_warning "健康檢查失敗: ${endpoint}"
        fi
    done
}

# 顯示 Podman 特定信息
show_podman_info() {
    log_info "顯示 Podman 系統信息..."
    
    echo ""
    echo "=========================================="
    echo "           Podman 系統信息"
    echo "=========================================="
    echo "Podman 版本: $(podman --version)"
    echo "Podman Compose 版本: $(podman-compose --version)"
    echo "Podman 信息:"
    podman info --format "{{.Host.Arch}} {{.Host.OS}}" 2>/dev/null || echo "無法獲取 Podman 信息"
    echo ""
    echo "容器統計:"
    podman stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "無法獲取容器統計"
    echo ""
}

# 主函數
main() {
    echo ""
    echo "=========================================="
    echo "    Podwise 專案啟動腳本 (Podman 版本)"
    echo "=========================================="
    echo ""
    
    # 檢查是否在正確的目錄
    if [ ! -f "docker-compose.yaml" ]; then
        log_error "請在包含 docker-compose.yaml 的目錄中執行此腳本"
        exit 1
    fi
    
    # 執行各個步驟
    check_podman
    check_env_file
    check_network
    stop_existing_services
    cleanup_old_containers
    start_services
    wait_for_services
    show_service_status
    show_podman_info
    health_check
    show_logs
    
    echo ""
    log_success "Podwise 專案啟動完成！(使用 Podman)"
    echo ""
    echo "💡 Podman 特定提示："
    echo "   - 使用 'podman-compose logs -f [服務名]' 查看實時日誌"
    echo "   - 使用 'podman-compose down' 停止所有服務"
    echo "   - 使用 'podman-compose restart [服務名]' 重啟特定服務"
    echo "   - 使用 'podman ps' 查看所有容器"
    echo "   - 使用 'podman system prune' 清理未使用的資源"
    echo ""
}

# 執行主函數
main "$@" 