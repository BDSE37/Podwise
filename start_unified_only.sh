#!/bin/bash

# Podwise 統一 API Gateway 快速啟動腳本
# 僅啟動統一 API Gateway，不包含基礎設施服務

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

# 啟動統一 API Gateway
start_unified_api() {
    log_info "啟動 Podwise 統一 API Gateway..."
    
    # 檢查 Python 版本
    python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    log_info "Python 版本: $python_version"
    
    # 檢查必要目錄
    FRONTEND_PATH="frontend"
    IMAGES_PATH="$FRONTEND_PATH/images"
    ASSETS_PATH="$FRONTEND_PATH/assets"
    
    if [ ! -d "$FRONTEND_PATH" ]; then
        log_error "前端目錄不存在: $FRONTEND_PATH"
        exit 1
    fi
    
    if [ ! -d "$IMAGES_PATH" ]; then
        log_error "圖片目錄不存在: $IMAGES_PATH"
        exit 1
    fi
    
    if [ ! -d "$ASSETS_PATH" ]; then
        log_error "資源目錄不存在: $ASSETS_PATH"
        exit 1
    fi
    
    log_success "目錄檢查通過"
    
    # 檢查端口
    if check_port 8008; then
        log_warning "端口 8008 已被佔用，請先停止現有服務"
        return 1
    fi
    
    # 進入後端目錄
    cd backend
    
    # 檢查依賴
    log_info "檢查依賴..."
    if ! python3 -c "import fastapi" 2>/dev/null; then
        log_info "安裝依賴..."
        pip3 install -r requirements_unified_api.txt
    fi
    
    # 創建日誌目錄
    mkdir -p logs
    
    # 設定環境變數
    export TTS_SERVICE_URL=${TTS_SERVICE_URL:-"http://localhost:8002"}
    export STT_SERVICE_URL=${STT_SERVICE_URL:-"http://localhost:8003"}
    export RAG_PIPELINE_URL=${RAG_PIPELINE_URL:-"http://localhost:8005"}
    export ML_PIPELINE_URL=${ML_PIPELINE_URL:-"http://localhost:8004"}
    export LLM_SERVICE_URL=${LLM_SERVICE_URL:-"http://localhost:8006"}
    
    log_info "服務配置:"
    log_info "  TTS: $TTS_SERVICE_URL"
    log_info "  STT: $STT_SERVICE_URL"
    log_info "  RAG Pipeline: $RAG_PIPELINE_URL"
    log_info "  ML Pipeline: $ML_PIPELINE_URL"
    log_info "  LLM: $LLM_SERVICE_URL"
    
    # 啟動統一 API Gateway
    log_info "啟動服務在 http://localhost:8008"
    log_info "API 文檔: http://localhost:8008/docs"
    log_info "ReDoc: http://localhost:8008/redoc"
    
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

# 停止服務
stop_service() {
    log_info "停止統一 API Gateway..."
    
    cd backend
    
    if [ -f "logs/unified_api.pid" ]; then
        kill $(cat logs/unified_api.pid) 2>/dev/null
        rm -f logs/unified_api.pid
        log_success "統一 API Gateway 已停止"
    else
        log_warning "找不到 PID 文件，嘗試強制停止..."
        pkill -f "unified_api_gateway.py" 2>/dev/null
        log_success "統一 API Gateway 已停止"
    fi
    
    cd "$PROJECT_ROOT"
}

# 檢查服務狀態
check_status() {
    log_info "檢查統一 API Gateway 狀態..."
    
    if check_port 8008; then
        log_success "統一 API Gateway: 運行中 (端口: 8008)"
        log_info "  API 服務: http://localhost:8008"
        log_info "  API 文檔: http://localhost:8008/docs"
        log_info "  ReDoc: http://localhost:8008/redoc"
    else
        log_error "統一 API Gateway: 未運行 (端口: 8008)"
    fi
}

# 主函數
case "${1:-start}" in
    "start")
        start_unified_api
        if [ $? -eq 0 ]; then
            echo ""
            log_success "統一 API Gateway 啟動完成！"
            echo ""
            echo "🌐 服務信息:"
            echo "  主頁面: http://localhost:8008"
            echo "  API 文檔: http://localhost:8008/docs"
            echo "  ReDoc: http://localhost:8008/redoc"
            echo ""
            echo "按 Ctrl+C 停止服務"
            echo ""
            
            # 等待用戶中斷
            trap stop_service INT
            wait
        fi
        ;;
    "stop")
        stop_service
        ;;
    "status")
        check_status
        ;;
    "restart")
        stop_service
        sleep 2
        start_unified_api
        ;;
    *)
        echo "用法: $0 [start|stop|status|restart]"
        echo ""
        echo "命令說明:"
        echo "  start   - 啟動統一 API Gateway (預設)"
        echo "  stop    - 停止統一 API Gateway"
        echo "  status  - 檢查服務狀態"
        echo "  restart - 重新啟動統一 API Gateway"
        ;;
esac 