#!/bin/bash

# Podwise 完整前後端架構啟動腳本
# 整合統一 API Gateway 和基礎設施服務

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安裝，請先安裝"
        return 1
    fi
    return 0
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

# 等待服務啟動
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "等待 $service_name 服務啟動..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$service_name 服務已就緒"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name 服務啟動超時"
    return 1
}

# 啟動基礎設施服務 (Docker/Podman)
start_infrastructure() {
    log_step "啟動基礎設施服務..."
    
    # 檢查 Docker/Podman
    if check_command "podman"; then
        DOCKER_CMD="podman-compose"
        log_info "使用 Podman Compose"
    elif check_command "docker"; then
        DOCKER_CMD="docker-compose"
        log_info "使用 Docker Compose"
    else
        log_error "未找到 Docker 或 Podman，跳過基礎設施服務"
        return 1
    fi
    
    # 檢查 docker-compose 文件
    COMPOSE_FILE="deploy/docker/docker-compose-full.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "找不到 Docker Compose 文件: $COMPOSE_FILE"
        return 1
    fi
    
    # 啟動基礎設施服務
    log_info "啟動基礎設施服務..."
    cd deploy/docker
    
    # 檢查並創建必要的目錄
    mkdir -p /tmp/podwise-data/{milvus,minio,postgresql,pgadmin,mongodb,portainer}
    
    # 修改 docker-compose 文件中的路徑
    sed -i 's|/Volumes/Transcend/docker-data|/tmp/podwise-data|g' docker-compose-full.yml
    
    $DOCKER_CMD -f docker-compose-full.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "基礎設施服務啟動成功"
        cd "$PROJECT_ROOT"
        
        # 等待關鍵服務啟動
        sleep 10
        wait_for_service "http://localhost:5432" "PostgreSQL"
        wait_for_service "http://localhost:9000" "MinIO"
        wait_for_service "http://localhost:19530" "Milvus"
        
        return 0
    else
        log_error "基礎設施服務啟動失敗"
        cd "$PROJECT_ROOT"
        return 1
    fi
}

# 啟動統一 API Gateway
start_unified_api() {
    log_step "啟動統一 API Gateway..."
    
    # 檢查 Python 環境
    if ! check_command "python3"; then
        log_error "Python3 未安裝"
        return 1
    fi
    
    # 檢查端口
    if check_port 8008; then
        log_warning "端口 8008 已被佔用，跳過統一 API Gateway"
        return 0
    fi
    
    # 進入後端目錄
    cd backend
    
    # 檢查依賴
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安裝統一 API Gateway 依賴..."
        pip3 install -r requirements_unified_api.txt
    fi
    
    # 設定環境變數
    export TTS_SERVICE_URL=${TTS_SERVICE_URL:-"http://localhost:8002"}
    export STT_SERVICE_URL=${STT_SERVICE_URL:-"http://localhost:8003"}
    export RAG_PIPELINE_URL=${RAG_PIPELINE_URL:-"http://localhost:8005"}
    export ML_PIPELINE_URL=${ML_PIPELINE_URL:-"http://localhost:8004"}
    export LLM_SERVICE_URL=${LLM_SERVICE_URL:-"http://localhost:8006"}
    
    # 啟動統一 API Gateway
    log_info "啟動統一 API Gateway (端口: 8008)"
    nohup python3 unified_api_gateway.py > logs/unified_api.log 2>&1 &
    echo $! > logs/unified_api.pid
    
    cd "$PROJECT_ROOT"
    
    # 等待服務啟動
    sleep 5
    if wait_for_service "http://localhost:8008/health" "統一 API Gateway"; then
        log_success "統一 API Gateway 啟動成功"
        return 0
    else
        log_error "統一 API Gateway 啟動失敗"
        return 1
    fi
}

# 啟動其他後端服務
start_backend_services() {
    log_step "啟動其他後端服務..."
    
    cd backend
    
    # 創建日誌目錄
    mkdir -p logs
    
    # 啟動 TTS 服務
    if ! check_port 8002; then
        log_info "啟動 TTS 服務 (端口: 8002)"
        cd tts
        nohup python3 main.py > ../logs/tts.log 2>&1 &
        echo $! > ../logs/tts.pid
        cd ..
        sleep 3
    fi
    
    # 啟動 LLM 服務
    if ! check_port 8006; then
        log_info "啟動 LLM 服務 (端口: 8006)"
        cd llm
        nohup python3 main.py > ../logs/llm.log 2>&1 &
        echo $! > ../logs/llm.pid
        cd ..
        sleep 3
    fi
    
    # 啟動 RAG Pipeline 服務
    if ! check_port 8005; then
        log_info "啟動 RAG Pipeline 服務 (端口: 8005)"
        cd rag_pipeline
        nohup python3 main.py > ../logs/rag_pipeline.log 2>&1 &
        echo $! > ../logs/rag_pipeline.pid
        cd ..
        sleep 3
    fi
    
    # 啟動 STT 服務
    if ! check_port 8003; then
        log_info "啟動 STT 服務 (端口: 8003)"
        cd stt
        nohup python3 main.py > ../logs/stt.log 2>&1 &
        echo $! > ../logs/stt.pid
        cd ..
        sleep 3
    fi
    
    cd "$PROJECT_ROOT"
    
    # 等待服務啟動
    sleep 10
    
    # 檢查服務狀態
    local services=(
        "http://localhost:8002/health:TTS"
        "http://localhost:8003/health:STT"
        "http://localhost:8005/health:RAG Pipeline"
        "http://localhost:8006/health:LLM"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        wait_for_service "$url" "$name"
    done
}

# 啟動前端服務
start_frontend() {
    log_step "啟動前端服務..."
    
    if check_port 8081; then
        log_warning "端口 8081 已被佔用，跳過前端"
        return 0
    fi
    
    cd frontend
    
    # 檢查 Python 依賴
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安裝前端依賴..."
        pip3 install fastapi uvicorn jinja2
    fi
    
    log_info "啟動前端服務 (端口: 8081)"
    nohup python3 fastapi_app.py > ../logs/frontend.log 2>&1 &
    echo $! > ../logs/frontend.pid
    
    cd "$PROJECT_ROOT"
    
    sleep 5
    if wait_for_service "http://localhost:8081" "前端服務"; then
        log_success "前端服務啟動成功"
        return 0
    else
        log_error "前端服務啟動失敗"
        return 1
    fi
}

# 顯示服務信息
show_service_info() {
    echo ""
    echo "🌐 Podwise 完整架構已啟動"
    echo "================================"
    echo ""
    echo "📱 前端服務:"
    echo "  主頁面: http://localhost:8081"
    echo "  Podri 頁面: http://localhost:8081/podri.html"
    echo ""
    echo "🔧 統一 API Gateway:"
    echo "  API 服務: http://localhost:8008"
    echo "  API 文檔: http://localhost:8008/docs"
    echo "  ReDoc: http://localhost:8008/redoc"
    echo ""
    echo "⚙️ 後端服務:"
    echo "  TTS 服務: http://localhost:8002"
    echo "  STT 服務: http://localhost:8003"
    echo "  RAG Pipeline: http://localhost:8005"
    echo "  LLM 服務: http://localhost:8006"
    echo ""
    echo "🗄️ 基礎設施服務:"
    echo "  PostgreSQL: localhost:5432"
    echo "  MinIO Console: http://localhost:9001"
    echo "  Milvus: localhost:19530"
    echo "  Attu (Milvus UI): http://localhost:3000"
    echo "  pgAdmin: http://localhost:5050"
    echo "  MongoDB Express: http://localhost:8081"
    echo "  Portainer: http://localhost:9000"
    echo ""
    echo "📊 監控與管理:"
    echo "  服務狀態檢查: $0 status"
    echo "  停止所有服務: $0 stop"
    echo "  重啟所有服務: $0 restart"
    echo ""
    echo "按 Ctrl+C 停止所有服務"
}

# 啟動所有服務
start_all() {
    echo "🚀 啟動 Podwise 完整前後端架構..."
    echo "=================================="
    
    # 創建日誌目錄
    mkdir -p logs backend/logs
    
    # 1. 啟動基礎設施服務
    start_infrastructure
    
    # 2. 啟動統一 API Gateway
    start_unified_api
    
    # 3. 啟動其他後端服務
    start_backend_services
    
    # 4. 啟動前端服務
    start_frontend
    
    # 5. 顯示服務信息
    show_service_info
    
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
    
    local services=("unified_api" "tts" "stt" "rag_pipeline" "llm")
    for service in "${services[@]}"; do
        if [ -f "logs/${service}.pid" ]; then
            kill $(cat logs/${service}.pid) 2>/dev/null
            rm -f logs/${service}.pid
            log_success "${service} 服務已停止"
        fi
    done
    
    cd "$PROJECT_ROOT"
    
    # 停止 Docker 服務
    if command -v podman-compose &> /dev/null; then
        cd deploy/docker
        podman-compose -f docker-compose-full.yml down
        cd "$PROJECT_ROOT"
        log_success "Docker 服務已停止"
    elif command -v docker-compose &> /dev/null; then
        cd deploy/docker
        docker-compose -f docker-compose-full.yml down
        cd "$PROJECT_ROOT"
        log_success "Docker 服務已停止"
    fi
    
    log_success "所有服務已停止"
}

# 檢查服務狀態
check_status() {
    echo "📊 Podwise 服務狀態檢查..."
    echo "=========================="
    
    # 檢查前端服務
    if check_port 8081; then
        log_success "前端服務: 運行中 (端口: 8081)"
    else
        log_error "前端服務: 未運行 (端口: 8081)"
    fi
    
    # 檢查統一 API Gateway
    if check_port 8008; then
        log_success "統一 API Gateway: 運行中 (端口: 8008)"
    else
        log_error "統一 API Gateway: 未運行 (端口: 8008)"
    fi
    
    # 檢查後端服務
    local backend_services=(
        "8002:TTS 服務"
        "8003:STT 服務"
        "8005:RAG Pipeline"
        "8006:LLM 服務"
    )
    
    for service in "${backend_services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        if check_port $port; then
            log_success "$name: 運行中 (端口: $port)"
        else
            log_error "$name: 未運行 (端口: $port)"
        fi
    done
    
    # 檢查基礎設施服務
    local infra_services=(
        "5432:PostgreSQL"
        "9000:MinIO"
        "19530:Milvus"
        "3000:Attu"
        "5050:pgAdmin"
        "8081:MongoDB Express"
    )
    
    echo ""
    echo "🗄️ 基礎設施服務狀態:"
    for service in "${infra_services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        if check_port $port; then
            log_success "$name: 運行中 (端口: $port)"
        else
            log_error "$name: 未運行 (端口: $port)"
        fi
    done
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
    "infrastructure")
        start_infrastructure
        ;;
    "api")
        start_unified_api
        ;;
    "backend")
        start_backend_services
        ;;
    "frontend")
        start_frontend
        ;;
    *)
        echo "用法: $0 [start|stop|status|restart|infrastructure|api|backend|frontend]"
        echo ""
        echo "命令說明:"
        echo "  start         - 啟動完整架構 (預設)"
        echo "  stop          - 停止所有服務"
        echo "  status        - 檢查服務狀態"
        echo "  restart       - 重新啟動所有服務"
        echo "  infrastructure - 僅啟動基礎設施服務"
        echo "  api           - 僅啟動統一 API Gateway"
        echo "  backend       - 僅啟動後端服務"
        echo "  frontend      - 僅啟動前端服務"
        ;;
esac 