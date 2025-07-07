#!/bin/bash

# =============================================================================
# Podwise Podman 部署腳本
# =============================================================================
# 此腳本用於使用 Podman 部署完整的 Podwise 環境
# 包含環境檢查、服務構建、啟動和健康檢查
# 支援互動式選單，可選擇特定模組進行建置
# =============================================================================

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# 顯示標題
show_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  Podwise Podman 部署腳本"
    echo "=================================================="
    echo -e "${NC}"
}

# 顯示選單
show_menu() {
    echo -e "\n${BLUE}請選擇要操作的模組:${NC}"
    echo -e "${CYAN}1.${NC} 檢查系統要求"
    echo -e "${CYAN}2.${NC} 檢查環境文件"
    echo -e "${CYAN}3.${NC} 檢查 K8s 服務連接"
    echo -e "${CYAN}4.${NC} 清理現有容器"
    echo -e "${CYAN}5.${NC} 建置 LLM 服務"
    echo -e "${CYAN}6.${NC} 建置 STT 服務"
    echo -e "${CYAN}7.${NC} 建置 TTS 服務"
    echo -e "${CYAN}8.${NC} 建置 ML Pipeline"
    echo -e "${CYAN}9.${NC} 建置 RAG Pipeline"
    echo -e "${CYAN}10.${NC} 建置前端服務"
    echo -e "${CYAN}11.${NC} 建置 Podri Chat"
    echo -e "${CYAN}12.${NC} 建置所有服務"
    echo -e "${CYAN}13.${NC} 啟動 LLM 服務"
    echo -e "${CYAN}14.${NC} 啟動 STT 服務"
    echo -e "${CYAN}15.${NC} 啟動 TTS 服務"
    echo -e "${CYAN}16.${NC} 啟動 ML Pipeline"
    echo -e "${CYAN}17.${NC} 啟動 RAG Pipeline"
    echo -e "${CYAN}18.${NC} 啟動前端服務"
    echo -e "${CYAN}19.${NC} 啟動 Podri Chat"
    echo -e "${CYAN}20.${NC} 啟動所有服務"
    echo -e "${CYAN}21.${NC} 執行健康檢查"
    echo -e "${CYAN}22.${NC} 顯示服務狀態"
    echo -e "${CYAN}23.${NC} 顯示日誌指令"
    echo -e "${CYAN}24.${NC} 完整部署流程"
    echo -e "${CYAN}0.${NC} 退出"
    echo -e "\n${YELLOW}請輸入選項編號:${NC} "
}

# 檢查系統要求
check_system_requirements() {
    log_step "檢查系統要求..."
    
    # 檢查 Podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝或不在 PATH 中"
        log_info "請安裝 Podman: https://podman.io/getting-started/installation"
        return 1
    fi
    
    # 檢查 Podman Compose
    if ! command -v podman-compose &> /dev/null; then
        log_warning "Podman Compose 未安裝，嘗試安裝..."
        if command -v pip3 &> /dev/null; then
            pip3 install podman-compose
        else
            log_error "無法安裝 Podman Compose，請手動安裝"
            return 1
        fi
    fi
    
    # 檢查網路工具
    if ! command -v nc &> /dev/null; then
        log_warning "netcat 未安裝，健康檢查功能可能受限"
    fi
    
    # 檢查 curl
    if ! command -v curl &> /dev/null; then
        log_warning "curl 未安裝，健康檢查功能可能受限"
    fi
    
    log_success "系統要求檢查完成"
    return 0
}

# 檢查環境文件
check_environment_files() {
    log_step "檢查環境配置文件..."
    
    # 檢查主要環境文件
    if [ ! -f "./backend/.env" ]; then
        log_error "環境文件 ./backend/.env 不存在"
        log_info "請複製 env.example 並配置必要的環境變數"
        return 1
    fi
    
    # 檢查其他必要的配置文件
    required_files=(
        "docker-compose.yaml"
        "backend/llm/Dockerfile"
        "backend/stt/Dockerfile"
        "backend/tts/Dockerfile"
        "backend/rag_pipeline/Dockerfile"
        "backend/ml_pipeline/Dockerfile"
        "frontend/Dockerfile"
        "frontend/chat/Dockerfile"
    )
    
    local missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "以下必要文件不存在:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
    
    log_success "環境文件檢查完成"
    return 0
}

# 檢查 K8s 服務連接
check_k8s_connectivity() {
    log_step "檢查 K8s 服務連接..."
    
    local k8s_services=(
        "postgres.podwise.svc.cluster.local:5432"
        "mongodb.podwise.svc.cluster.local:27017"
        "minio.podwise.svc.cluster.local:9000"
        "192.168.32.38:31134"  # Ollama
    )
    
    local connected_count=0
    local total_count=${#k8s_services[@]}
    
    echo -e "${BLUE}開始檢查 $total_count 個 K8s 服務...${NC}\n"
    
    for service in "${k8s_services[@]}"; do
        local host=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)
        
        log_info "檢查 $service 連接..."
        
        # 使用更簡單的連接檢查方法
        if command -v nc >/dev/null 2>&1; then
            # 使用 nc 檢查
            if timeout 3 nc -z "$host" "$port" 2>/dev/null; then
                log_success "✓ $service 連接正常"
                ((connected_count++))
            else
                log_warning "✗ $service 連接失敗"
            fi
        else
            # 如果沒有 nc，使用 bash 內建的 /dev/tcp
            if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
                log_success "✓ $service 連接正常"
                ((connected_count++))
            else
                log_warning "✗ $service 連接失敗"
            fi
        fi
        
        # 添加小延遲避免過於頻繁的連接
        sleep 1
    done
    
    echo -e "\n${BLUE}K8s 服務連接結果:${NC} $connected_count/$total_count 服務可達"
    
    if [ $connected_count -eq 0 ]; then
        log_warning "無法連接到任何 K8s 服務，請檢查網路配置"
    elif [ $connected_count -lt $total_count ]; then
        log_warning "部分 K8s 服務無法連接，但可以繼續執行"
    else
        log_success "所有 K8s 服務連接正常"
    fi
    
    # 顯示 Langfuse 雲端服務資訊
    echo -e "\n${BLUE}Langfuse 雲端服務:${NC}"
    echo -e "${CYAN}雲端地址:${NC} https://cloud.langfuse.com"
    echo -e "${CYAN}狀態:${NC} 雲端服務，無需本地連接檢查"
    
    echo -e "\n${CYAN}K8s 連接檢查完成${NC}"
    return 0
}

# 清理現有容器
cleanup_existing_containers() {
    log_step "清理現有容器..."
    
    # 停止並移除現有容器
    if podman-compose ps | grep -q "Up"; then
        log_info "停止現有服務..."
        podman-compose down
    fi
    
    # 清理孤立的容器
    local orphaned_containers=$(podman ps -a --filter "label=com.docker.compose.project=podwise" --format "{{.ID}}")
    if [ ! -z "$orphaned_containers" ]; then
        log_info "清理孤立容器..."
        echo "$orphaned_containers" | xargs -r podman rm -f
    fi
    
    log_success "容器清理完成"
    return 0
}

# 建置單一服務
build_single_service() {
    local service_name=$1
    log_step "建置 $service_name 服務..."
    
    if podman-compose build $service_name; then
        log_success "$service_name 建置完成"
        return 0
    else
        log_error "$service_name 建置失敗"
        return 1
    fi
}

# 啟動單一服務
start_single_service() {
    local service_name=$1
    log_step "啟動 $service_name 服務..."
    
    if podman-compose up -d $service_name; then
        log_success "$service_name 啟動成功"
        
        # 等待服務啟動
        log_info "等待 $service_name 啟動..."
        sleep 10
        
        return 0
    else
        log_error "$service_name 啟動失敗"
        return 1
    fi
}

# 建置所有服務
build_all_services() {
    log_step "建置所有服務映像..."
    
    local services=("llm" "stt" "tts" "rag_pipeline" "ml_pipeline" "frontend" "podri_chat")
    
    for service in "${services[@]}"; do
        if ! build_single_service $service; then
            return 1
        fi
    done
    
    log_success "所有服務建置完成"
    return 0
}

# 啟動所有服務
start_all_services() {
    log_step "啟動所有服務..."
    
    # 啟動核心 AI 服務
    local core_services=("llm" "stt" "tts" "ml_pipeline")
    
    for service in "${core_services[@]}"; do
        if ! start_single_service $service; then
            return 1
        fi
    done
    
    # 啟動 RAG Pipeline
    if ! start_single_service "rag_pipeline"; then
        return 1
    fi
    
    # 啟動前端服務
    local frontend_services=("frontend" "podri_chat")
    for service in "${frontend_services[@]}"; do
        if ! start_single_service $service; then
            return 1
        fi
    done
    
    log_success "所有服務啟動完成"
    return 0
}

# 健康檢查
perform_health_checks() {
    log_step "執行健康檢查..."
    
    local services=(
        "llm:8000"
        "stt:8001"
        "tts:8003"
        "ml_pipeline:8004"
        "rag_pipeline:8005"
    )
    
    local healthy_count=0
    local total_count=${#services[@]}
    
    for service_info in "${services[@]}"; do
        local service_name=$(echo $service_info | cut -d: -f1)
        local port=$(echo $service_info | cut -d: -f2)
        
        log_info "檢查 $service_name 健康狀態..."
        
        # 等待服務啟動
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -f http://localhost:$port/health >/dev/null 2>&1; then
                log_success "✓ $service_name 健康檢查通過"
                ((healthy_count++))
                break
            else
                if [ $attempt -eq $max_attempts ]; then
                    log_warning "✗ $service_name 健康檢查失敗"
                else
                    log_debug "等待 $service_name 啟動... (嘗試 $attempt/$max_attempts)"
                    sleep 2
                fi
            fi
            ((attempt++))
        done
    done
    
    echo -e "\n${BLUE}健康檢查結果:${NC} $healthy_count/$total_count 服務正常"
    
    if [ $healthy_count -eq 0 ]; then
        log_warning "所有服務健康檢查失敗，請檢查日誌"
    fi
    
    return 0
}

# 顯示服務狀態
show_service_status() {
    log_step "顯示服務狀態..."
    
    echo -e "\n${BLUE}容器狀態:${NC}"
    podman-compose ps
    
    echo -e "\n${BLUE}服務端口映射:${NC}"
    echo -e "${CYAN}LLM 服務:${NC} http://localhost:8000"
    echo -e "${CYAN}STT 服務:${NC} http://localhost:8001"
    echo -e "${CYAN}TTS 服務:${NC} http://localhost:8003"
    echo -e "${CYAN}ML Pipeline:${NC} http://localhost:8004"
    echo -e "${CYAN}RAG Pipeline:${NC} http://localhost:8005"
    echo -e "${CYAN}前端網站:${NC} http://localhost:80"
    echo -e "${CYAN}Streamlit 聊天:${NC} http://localhost:8501"
    
    echo -e "\n${BLUE}K8s 服務:${NC}"
    echo -e "${CYAN}Grafana:${NC} http://192.168.32.38:30004"
    echo -e "${CYAN}Prometheus:${NC} http://192.168.32.38:30090"
    echo -e "${CYAN}Portainer:${NC} http://192.168.32.38:3003"
    echo -e "${CYAN}Attu (Milvus):${NC} http://192.168.32.38:3101"
    
    return 0
}

# 顯示日誌查看指令
show_log_commands() {
    echo -e "\n${BLUE}常用指令:${NC}"
    echo -e "${CYAN}查看所有服務日誌:${NC} podman-compose logs -f"
    echo -e "${CYAN}查看特定服務日誌:${NC} podman-compose logs -f [service_name]"
    echo -e "${CYAN}停止所有服務:${NC} podman-compose down"
    echo -e "${CYAN}重啟服務:${NC} podman-compose restart [service_name]"
    echo -e "${CYAN}進入容器:${NC} podman exec -it [container_name] /bin/bash"
    echo -e "${CYAN}查看容器狀態:${NC} podman-compose ps"
    
    return 0
}

# 完整部署流程
full_deployment() {
    log_step "開始完整部署流程..."
    
    # 檢查系統要求
    if ! check_system_requirements; then
        return 1
    fi
    
    # 檢查環境文件
    if ! check_environment_files; then
        return 1
    fi
    
    # 檢查 K8s 服務連接
    if ! check_k8s_connectivity; then
        log_warning "K8s 服務連接檢查失敗，但繼續執行..."
    fi
    
    # 清理現有容器
    if ! cleanup_existing_containers; then
        return 1
    fi
    
    # 建置所有服務
    if ! build_all_services; then
        return 1
    fi
    
    # 啟動所有服務
    if ! start_all_services; then
        return 1
    fi
    
    # 執行健康檢查
    perform_health_checks
    
    # 顯示服務狀態
    show_service_status
    
    # 顯示日誌查看指令
    show_log_commands
    
    echo -e "\n${GREEN}=================================================="
    echo "  Podwise 完整部署完成！"
    echo "==================================================${NC}"
    
    return 0
}

# 處理用戶選擇
handle_user_choice() {
    local choice=$1
    
    case $choice in
        1)
            check_system_requirements
            ;;
        2)
            check_environment_files
            ;;
        3)
            check_k8s_connectivity
            ;;
        4)
            cleanup_existing_containers
            ;;
        5)
            build_single_service "llm"
            ;;
        6)
            build_single_service "stt"
            ;;
        7)
            build_single_service "tts"
            ;;
        8)
            build_single_service "ml_pipeline"
            ;;
        9)
            build_single_service "rag_pipeline"
            ;;
        10)
            build_single_service "frontend"
            ;;
        11)
            build_single_service "podri_chat"
            ;;
        12)
            build_all_services
            ;;
        13)
            start_single_service "llm"
            ;;
        14)
            start_single_service "stt"
            ;;
        15)
            start_single_service "tts"
            ;;
        16)
            start_single_service "ml_pipeline"
            ;;
        17)
            start_single_service "rag_pipeline"
            ;;
        18)
            start_single_service "frontend"
            ;;
        19)
            start_single_service "podri_chat"
            ;;
        20)
            start_all_services
            ;;
        21)
            perform_health_checks
            ;;
        22)
            show_service_status
            ;;
        23)
            show_log_commands
            ;;
        24)
            full_deployment
            ;;
        0)
            echo -e "\n${GREEN}感謝使用 Podwise 部署腳本！${NC}"
            return 0
            ;;
        *)
            echo -e "\n${RED}無效選項，請重新選擇${NC}"
            ;;
    esac
}

# 互動式主函數
interactive_main() {
    show_header
    
    while true; do
        show_menu
        read -r choice
        
        echo -e "\n"
        
        # 執行用戶選擇的操作，並捕獲任何錯誤
        if handle_user_choice $choice; then
            echo -e "\n${GREEN}操作執行完成${NC}"
        else
            echo -e "\n${YELLOW}操作執行完成（可能有警告）${NC}"
        fi
        
        # 如果選擇了退出，則跳出循環
        if [ "$choice" = "0" ]; then
            break
        fi
        
        echo -e "\n${YELLOW}按 Enter 鍵繼續...${NC}"
        read -r
        
        # 清屏（可選）
        clear
        show_header
    done
}

# 檢查是否為互動模式
if [ "$1" = "--interactive" ] || [ "$1" = "-i" ]; then
    interactive_main
else
    # 非互動模式，執行完整部署
    show_header
    full_deployment
fi 