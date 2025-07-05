#!/bin/bash

# K8s 部署測試腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 配置
NAMESPACE="podwise"
DEPLOYMENT_NAME="rag-pipeline-service"

log_info "開始測試 K8s 部署..."

# 檢查 Pod 狀態
log_info "檢查 Pod 狀態..."
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME

# 檢查服務狀態
log_info "檢查服務狀態..."
kubectl get svc -n $NAMESPACE -l app=$DEPLOYMENT_NAME

# 檢查節點分配
log_info "檢查節點分配..."
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o wide

# 獲取 Pod 名稱
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o jsonpath='{.items[0].metadata.name}')

if [ -n "$POD_NAME" ]; then
    log_info "Pod 名稱: $POD_NAME"
    
    # 檢查 Pod 日誌
    log_info "檢查 Pod 日誌..."
    kubectl logs $POD_NAME -n $NAMESPACE --tail=20
    
    # 檢查 Pod 詳細信息
    log_info "檢查 Pod 詳細信息..."
    kubectl describe pod $POD_NAME -n $NAMESPACE
    
    log_success "測試完成！"
    echo ""
    echo "進入容器安裝套件:"
    echo "kubectl exec -it $POD_NAME -n $NAMESPACE -- bash"
    echo ""
    echo "容器內操作步驟:"
    echo "1. 檢查 requirements.txt: cat requirements.txt"
    echo "2. 安裝套件: pip install -r requirements.txt"
    echo "3. 啟動服務: python -m uvicorn backend.rag_pipeline.app.main_crewai:app --host 0.0.0.0 --port 8004"
    echo "4. 測試健康檢查: curl http://localhost:8004/health"
else
    log_error "無法獲取 Pod 名稱"
    exit 1
fi 