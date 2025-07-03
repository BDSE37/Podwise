#!/bin/bash

# GPT-SoVITS Web UI 建置和部署腳本
# 使用 Podman 建置映像並部署到 Kubernetes

set -e

# 設定變數
REGISTRY="192.168.32.38:5000"
IMAGE_NAME="gpt-sovits-webui"
TAG="latest"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"

# 顏色設定
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

# 檢查必要工具
check_requirements() {
    log_info "檢查必要工具..."
    
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝"
        exit 1
    fi
    
    log_success "必要工具檢查完成"
}

# 建置 Podman 映像
build_image() {
    log_info "開始建置 GPT-SoVITS Web UI 映像..."
    
    # 切換到 GPT-SoVITS 目錄
    cd ../../../backend/tts/GPT-SoVITS
    
    # 建置映像
    log_info "執行 Podman 建置命令..."
    podman build -t ${FULL_IMAGE_NAME} .
    
    if [ $? -eq 0 ]; then
        log_success "映像建置成功: ${FULL_IMAGE_NAME}"
    else
        log_error "映像建置失敗"
        exit 1
    fi
    
    # 返回原目錄
    cd ../../../deploy/k8s/gpt-sovits-webui
}

# 推送映像到私有 Registry
push_image() {
    log_info "推送映像到私有 Registry..."
    
    podman push ${FULL_IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        log_success "映像推送成功"
    else
        log_error "映像推送失敗"
        exit 1
    fi
}

# 部署 PVC
deploy_pvcs() {
    log_info "部署 GPT-SoVITS PVC..."
    
    kubectl apply -f gpt-sovits-pvcs.yaml
    
    if [ $? -eq 0 ]; then
        log_success "PVC 部署成功"
    else
        log_error "PVC 部署失敗"
        exit 1
    fi
    
    # 等待 PVC 綁定
    log_info "等待 PVC 綁定..."
    kubectl wait --for=condition=Bound pvc/gpt-sovits-data-pvc -n podwise --timeout=300s
    kubectl wait --for=condition=Bound pvc/gpt-sovits-models-pvc -n podwise --timeout=300s
    kubectl wait --for=condition=Bound pvc/gpt-sovits-weights-pvc -n podwise --timeout=300s
    kubectl wait --for=condition=Bound pvc/gpt-sovits-gpt-weights-pvc -n podwise --timeout=300s
    kubectl wait --for=condition=Bound pvc/gpt-sovits-logs-pvc -n podwise --timeout=300s
    kubectl wait --for=condition=Bound pvc/gpt-sovits-output-pvc -n podwise --timeout=300s
}

# 部署 GPT-SoVITS Web UI
deploy_webui() {
    log_info "部署 GPT-SoVITS Web UI..."
    
    kubectl apply -f gpt-sovits-webui-deployment.yaml
    
    if [ $? -eq 0 ]; then
        log_success "GPT-SoVITS Web UI 部署成功"
    else
        log_error "GPT-SoVITS Web UI 部署失敗"
        exit 1
    fi
}

# 檢查部署狀態
check_deployment() {
    log_info "檢查部署狀態..."
    
    # 等待 Pod 啟動
    log_info "等待 Pod 啟動..."
    kubectl wait --for=condition=Ready pod -l app=gpt-sovits-webui -n podwise --timeout=600s
    
    # 檢查 Pod 狀態
    log_info "檢查 Pod 狀態..."
    kubectl get pods -n podwise -l app=gpt-sovits-webui
    
    # 檢查服務狀態
    log_info "檢查服務狀態..."
    kubectl get svc -n podwise -l app=gpt-sovits-webui
}

# 顯示訪問資訊
show_access_info() {
    log_info "=== GPT-SoVITS Web UI 訪問資訊 ==="
    echo
    log_success "Web UI 主介面:"
    echo "  http://192.168.32.38:30786"
    echo
    log_success "其他服務端口:"
    echo "  主服務: http://192.168.32.38:30974"
    echo "  UVR5: http://192.168.32.38:30973"
    echo "  推理 TTS: http://192.168.32.38:30972"
    echo "  子服務: http://192.168.32.38:30971"
    echo
    log_info "訓練流程:"
    echo "  1. 上傳音頻檔案到 'raw' 目錄"
    echo "  2. 使用 UVR5 進行人聲分離"
    echo "  3. 使用 ASR 進行語音轉文字"
    echo "  4. 開始訓練 SoVITS 模型"
    echo "  5. 開始訓練 GPT 模型"
    echo "  6. 進行推理測試"
    echo
    log_warning "注意事項:"
    echo "  - 確保 GPU 資源充足"
    echo "  - 訓練過程可能需要數小時"
    echo "  - 建議使用高品質的音頻檔案"
}

# 清理函數
cleanup() {
    log_info "清理本地映像..."
    podman rmi ${FULL_IMAGE_NAME} 2>/dev/null || true
}

# 主函數
main() {
    log_info "=== GPT-SoVITS Web UI 建置和部署腳本 ==="
    echo
    
    # 檢查參數
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "用法: $0 [選項]"
        echo "選項:"
        echo "  --build-only    只建置映像，不部署"
        echo "  --deploy-only   只部署，不建置映像"
        echo "  --help, -h      顯示此幫助訊息"
        exit 0
    fi
    
    # 檢查必要工具
    check_requirements
    
    # 根據參數執行不同操作
    if [ "$1" = "--build-only" ]; then
        log_info "只建置映像模式"
        build_image
        push_image
        cleanup
        log_success "映像建置完成"
        exit 0
    elif [ "$1" = "--deploy-only" ]; then
        log_info "只部署模式"
        deploy_pvcs
        deploy_webui
        check_deployment
        show_access_info
        log_success "部署完成"
        exit 0
    fi
    
    # 完整流程
    log_info "開始完整建置和部署流程..."
    
    # 建置映像
    build_image
    
    # 推送映像
    push_image
    
    # 部署 PVC
    deploy_pvcs
    
    # 部署 Web UI
    deploy_webui
    
    # 檢查部署狀態
    check_deployment
    
    # 顯示訪問資訊
    show_access_info
    
    # 清理
    cleanup
    
    log_success "GPT-SoVITS Web UI 建置和部署完成！"
}

# 執行主函數
main "$@" 