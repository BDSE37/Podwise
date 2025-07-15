#!/bin/bash

# =============================================================================
# Podwise 專案停止腳本 (Podman 版本)
# 停止所有微服務並清理資源
# =============================================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝"
        exit 1
    fi
    
    if ! command -v podman-compose &> /dev/null; then
        log_error "Podman Compose 未安裝"
        exit 1
    fi
}

# 停止服務
stop_services() {
    log_info "停止 Podwise 服務..."
    
    if [ -f "docker-compose.yaml" ]; then
        podman-compose down --remove-orphans
        log_success "所有服務已停止"
    else
        log_error "未找到 docker-compose.yaml 文件"
        exit 1
    fi
}

# 清理容器
cleanup_containers() {
    log_info "清理 Podwise 容器..."
    
    # 停止並移除所有 Podwise 容器
    podman ps -a --filter "name=podwise_" --format "{{.ID}}" | xargs -r podman rm -f 2>/dev/null || true
    
    log_success "容器清理完成"
}

# 清理網路
cleanup_networks() {
    log_info "清理未使用的網路..."
    
    podman network prune -f 2>/dev/null || true
    
    log_success "網路清理完成"
}

# 清理映像（可選）
cleanup_images() {
    read -p "是否要清理未使用的映像？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理未使用的映像..."
        podman image prune -f 2>/dev/null || true
        log_success "映像清理完成"
    fi
}

# 清理 Pod 和卷
cleanup_pods_and_volumes() {
    log_info "清理 Pod 和卷..."
    
    # 清理未使用的 Pod
    podman pod prune -f 2>/dev/null || true
    
    # 清理未使用的卷
    podman volume prune -f 2>/dev/null || true
    
    log_success "Pod 和卷清理完成"
}

# 顯示狀態
show_status() {
    log_info "顯示剩餘容器狀態..."
    
    local remaining_containers=$(podman ps -a --filter "name=podwise_" --format "{{.Names}}" 2>/dev/null | wc -l)
    
    if [ "$remaining_containers" -eq 0 ]; then
        log_success "所有 Podwise 容器已清理完成"
    else
        log_warning "仍有 $remaining_containers 個 Podwise 容器存在"
        podman ps -a --filter "name=podwise_"
    fi
}

# 顯示 Podman 系統信息
show_podman_system_info() {
    log_info "顯示 Podman 系統信息..."
    
    echo ""
    echo "=========================================="
    echo "           Podman 系統信息"
    echo "=========================================="
    
    echo "容器數量: $(podman ps -a --format "{{.Names}}" | wc -l)"
    echo "映像數量: $(podman images --format "{{.Repository}}" | wc -l)"
    echo "網路數量: $(podman network ls --format "{{.Name}}" | wc -l)"
    echo "Pod 數量: $(podman pod ls --format "{{.Name}}" | wc -l)"
    echo "卷數量: $(podman volume ls --format "{{.Name}}" | wc -l)"
    
    echo ""
    echo "系統使用情況:"
    podman system df 2>/dev/null || echo "無法獲取系統使用情況"
    
    echo ""
}

# 主函數
main() {
    echo ""
    echo "=========================================="
    echo "    Podwise 專案停止腳本 (Podman 版本)"
    echo "=========================================="
    echo ""
    
    check_podman
    stop_services
    cleanup_containers
    cleanup_networks
    cleanup_pods_and_volumes
    cleanup_images
    show_status
    show_podman_system_info
    
    echo ""
    log_success "Podwise 專案已完全停止！(使用 Podman)"
    echo ""
    echo "💡 Podman 特定提示："
    echo "   - 使用 'podman system prune -a' 清理所有未使用的資源"
    echo "   - 使用 'podman system df' 查看系統使用情況"
    echo "   - 使用 'podman ps -a' 查看所有容器"
    echo ""
}

main "$@" 