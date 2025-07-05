#!/bin/bash

# Podwise RAG Pipeline K8s 部署腳本
# 用於構建 Docker 映像並部署到 K8s 集群

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
REGISTRY="192.168.32.38:5000"
IMAGE_NAME="podwise-rag-pipeline"
IMAGE_TAG="latest"
NAMESPACE="podwise"
DEPLOYMENT_NAME="rag-pipeline-service"
NODE_SELECTOR="worker2"

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
check_prerequisites() {
    log_info "檢查必要工具..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 K8s 集群"
        exit 1
    fi
    
    log_success "必要工具檢查完成"
}

# 檢查命名空間
check_namespace() {
    log_info "檢查命名空間..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_success "命名空間 $NAMESPACE 存在"
    else
        log_warning "命名空間 $NAMESPACE 不存在，正在創建..."
        kubectl create namespace $NAMESPACE
        log_success "命名空間 $NAMESPACE 創建完成"
    fi
}

# 構建 Docker 映像
build_docker_image() {
    log_info "構建 Docker 映像..."
    
    # 檢查 Dockerfile 是否存在
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile 不存在"
        exit 1
    fi
    
    # 構建映像
    docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
    
    if [ $? -eq 0 ]; then
        log_success "Docker 映像構建成功"
    else
        log_error "Docker 映像構建失敗"
        exit 1
    fi
}

# 推送 Docker 映像
push_docker_image() {
    log_info "推送 Docker 映像到註冊表..."
    
    # 檢查註冊表連接
    if ! docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG; then
        log_error "推送 Docker 映像失敗"
        exit 1
    fi
    
    log_success "Docker 映像推送成功"
}

# 創建 Secrets
create_secrets() {
    log_info "創建 Secrets..."
    
    # 檢查 OpenAI API Key
    if [ -n "$OPENAI_API_KEY" ]; then
        log_info "創建 OpenAI Secrets..."
        kubectl create secret generic openai-secrets \
            --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
            --namespace=$NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "OpenAI Secrets 創建完成"
    else
        log_warning "未設置 OPENAI_API_KEY，跳過 OpenAI Secrets 創建"
    fi
    
    # 檢查 Langfuse Secrets
    if [ -n "$LANGFUSE_PUBLIC_KEY" ] && [ -n "$LANGFUSE_SECRET_KEY" ]; then
        log_info "創建 Langfuse Secrets..."
        kubectl create secret generic langfuse-secrets \
            --from-literal=LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
            --from-literal=LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
            --from-literal=LANGFUSE_HOST="${LANGFUSE_HOST:-https://cloud.langfuse.com}" \
            --namespace=$NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "Langfuse Secrets 創建完成"
    else
        log_warning "未設置 Langfuse 配置，跳過 Langfuse Secrets 創建"
    fi
}

# 部署到 K8s
deploy_to_k8s() {
    log_info "部署到 K8s..."
    
    # 檢查部署檔案是否存在
    if [ ! -f "rag-pipeline-deployment.yaml" ]; then
        log_error "部署檔案 rag-pipeline-deployment.yaml 不存在"
        exit 1
    fi
    
    # 應用部署
    kubectl apply -f rag-pipeline-deployment.yaml
    
    if [ $? -eq 0 ]; then
        log_success "K8s 部署成功"
    else
        log_error "K8s 部署失敗"
        exit 1
    fi
}

# 等待部署完成
wait_for_deployment() {
    log_info "等待部署完成..."
    
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s
    
    if [ $? -eq 0 ]; then
        log_success "部署完成"
    else
        log_error "部署超時或失敗"
        kubectl describe deployment $DEPLOYMENT_NAME -n $NAMESPACE
        exit 1
    fi
}

# 檢查服務狀態
check_service_status() {
    log_info "檢查服務狀態..."
    
    # 檢查 Pod 狀態
    kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME
    
    # 檢查服務狀態
    kubectl get svc -n $NAMESPACE -l app=$DEPLOYMENT_NAME
    
    # 檢查節點分配
    kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o wide
}

# 測試服務連線
test_service_connection() {
    log_info "測試服務連線..."
    
    # 獲取服務 IP 和端口
    SERVICE_IP=$(kubectl get svc $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    NODE_PORT=$(kubectl get svc $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
    
    if [ -n "$SERVICE_IP" ]; then
        # 使用 LoadBalancer IP
        HEALTH_URL="http://$SERVICE_IP:8004/health"
    else
        # 使用 NodePort
        NODE_IP=$(kubectl get nodes -o wide | grep $NODE_SELECTOR | awk '{print $6}')
        HEALTH_URL="http://$NODE_IP:$NODE_PORT/health"
    fi
    
    log_info "測試健康檢查端點: $HEALTH_URL"
    
    # 等待服務啟動
    sleep 30
    
    # 測試連線
    if curl -s "$HEALTH_URL" > /dev/null; then
        log_success "服務連線測試成功"
        curl -s "$HEALTH_URL" | jq . 2>/dev/null || curl -s "$HEALTH_URL"
    else
        log_warning "服務連線測試失敗，但部署可能仍在啟動中"
    fi
}

# 顯示部署資訊
show_deployment_info() {
    log_info "=== 部署資訊 ==="
    
    echo "映像: $REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    echo "命名空間: $NAMESPACE"
    echo "部署名稱: $DEPLOYMENT_NAME"
    echo "節點選擇器: $NODE_SELECTOR"
    echo ""
    
    # 顯示服務端點
    NODE_PORT=$(kubectl get svc $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    if [ -n "$NODE_PORT" ]; then
        NODE_IP=$(kubectl get nodes -o wide | grep $NODE_SELECTOR | awk '{print $6}' 2>/dev/null)
        if [ -n "$NODE_IP" ]; then
            echo "服務端點: http://$NODE_IP:$NODE_PORT"
            echo "健康檢查: http://$NODE_IP:$NODE_PORT/health"
            echo "API 文檔: http://$NODE_IP:$NODE_PORT/docs"
        fi
    fi
    
    echo ""
    echo "查看日誌:"
    echo "kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
    echo ""
    echo "進入 Pod:"
    echo "kubectl exec -it deployment/$DEPLOYMENT_NAME -n $NAMESPACE -- bash"
}

# 主函數
main() {
    log_info "開始 K8s 部署流程..."
    
    check_prerequisites
    check_namespace
    build_docker_image
    push_docker_image
    create_secrets
    deploy_to_k8s
    wait_for_deployment
    check_service_status
    test_service_connection
    show_deployment_info
    
    log_success "K8s 部署完成！"
}

# 執行主函數
main "$@" 