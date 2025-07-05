#!/bin/bash

# Podwise RAG Pipeline K8s 最小化部署腳本
# 部署最小化映像，讓用戶進入容器手動安裝套件

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置變數
REGISTRY="192.168.32.38:5000"
IMAGE_NAME="podwise-rag-pipeline"
IMAGE_TAG="k8s-minimal"
NAMESPACE="podwise"
DEPLOYMENT_NAME="rag-pipeline-service"

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

# 顯示幫助信息
show_help() {
    echo "Podwise RAG Pipeline K8s 最小化部署腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help              顯示此幫助信息"
    echo "  -k, --openai-key KEY   設置 OpenAI API Key"
    echo "  -n, --namespace NS     設置 K8s 命名空間 (預設: podwise)"
    echo "  -y, --yes              自動確認所有提示"
    echo ""
    echo "範例:"
    echo "  $0 -k 'your_openai_key'"
    echo "  $0 -k 'your_openai_key' -y"
    echo ""
}

# 解析命令行參數
parse_args() {
    OPENAI_KEY=""
    NAMESPACE="podwise"
    AUTO_CONFIRM=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -k|--openai-key)
                OPENAI_KEY="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            *)
                log_error "未知選項: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 確認部署
confirm_deployment() {
    if [ "$AUTO_CONFIRM" = true ]; then
        return 0
    fi
    
    echo ""
    log_info "=== K8s 最小化部署配置 ==="
    echo "命名空間: $NAMESPACE"
    echo "映像標籤: $IMAGE_TAG"
    echo "OpenAI Key: ${OPENAI_KEY:+已設置}"
    echo "部署策略: 最小化映像 + 容器內手動安裝套件"
    echo ""
    
    read -p "確認開始部署? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "部署已取消"
        exit 0
    fi
}

# 設置環境變數
setup_environment() {
    log_info "設置環境變數..."
    
    if [ -n "$OPENAI_KEY" ]; then
        export OPENAI_API_KEY="$OPENAI_KEY"
        log_success "OpenAI API Key 已設置"
    fi
    
    export NAMESPACE="$NAMESPACE"
}

# 檢查前置需求
check_prerequisites() {
    log_info "檢查前置需求..."
    
    # 檢查 kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝"
        exit 1
    fi
    
    # 檢查 podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman 未安裝"
        exit 1
    fi
    
    # 檢查 K8s 連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 K8s 集群"
        exit 1
    fi
    
    log_success "前置需求檢查完成"
}

# 構建最小化映像
build_minimal_image() {
    log_info "構建 K8s 最小化映像..."
    
    # 獲取腳本所在目錄
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
    
    log_info "腳本目錄: $SCRIPT_DIR"
    log_info "專案根目錄: $PROJECT_ROOT"
    
    # 檢查 Dockerfile 是否存在
    if [ ! -f "$SCRIPT_DIR/Dockerfile.k8s-minimal" ]; then
        log_error "Dockerfile.k8s-minimal 不存在: $SCRIPT_DIR/Dockerfile.k8s-minimal"
        exit 1
    fi
    
    # 檢查專案根目錄是否存在
    if [ ! -f "$PROJECT_ROOT/backend/rag_pipeline/requirements.txt" ]; then
        log_error "無法找到專案根目錄: $PROJECT_ROOT/backend/rag_pipeline/requirements.txt"
        exit 1
    fi
    
    # 從專案根目錄構建映像
    log_info "從專案根目錄構建 K8s 最小化映像..."
    cd "$PROJECT_ROOT"
    podman build -f deploy/k8s/rag-pipeline/Dockerfile.k8s-minimal -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
    BUILD_RESULT=$?
    cd "$SCRIPT_DIR"
    
    if [ $BUILD_RESULT -eq 0 ]; then
        log_success "K8s 最小化映像構建成功"
    else
        log_error "K8s 最小化映像構建失敗"
        exit 1
    fi
}

# 推送映像
push_image() {
    log_info "推送映像到註冊表..."
    
    if ! podman push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG; then
        log_error "推送映像失敗"
        exit 1
    fi
    
    log_success "映像推送成功"
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
}

# 創建 K8s 部署配置
create_k8s_deployment() {
    log_info "創建 K8s 部署配置..."
    
    cat > /tmp/rag-pipeline-k8s-minimal.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $DEPLOYMENT_NAME
  namespace: $NAMESPACE
  labels:
    app: $DEPLOYMENT_NAME
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $DEPLOYMENT_NAME
  template:
    metadata:
      labels:
        app: $DEPLOYMENT_NAME
    spec:
      nodeSelector:
        kubernetes.io/hostname: worker2
      containers:
      - name: rag-pipeline-service
        image: $REGISTRY/$IMAGE_NAME:$IMAGE_TAG
        ports:
        - containerPort: 8004
        env:
        - name: PYTHONPATH
          value: "/app"
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: APP_ENV
          value: "production"
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL
          value: "INFO"
        - name: OLLAMA_HOST
          value: "http://worker1:11434"
        - name: OLLAMA_MODEL
          value: "qwen2.5:8b"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secrets
              key: OPENAI_API_KEY
              optional: true
        - name: LANGFUSE_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: LANGFUSE_PUBLIC_KEY
              optional: true
        - name: LANGFUSE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: LANGFUSE_SECRET_KEY
              optional: true
        resources:
          requests:
            memory: "1Gi"
            cpu: "0.5"
          limits:
            memory: "2Gi"
            cpu: "1"
        stdin: true
        tty: true
---
apiVersion: v1
kind: Service
metadata:
  name: $DEPLOYMENT_NAME
  namespace: $NAMESPACE
  labels:
    app: $DEPLOYMENT_NAME
spec:
  type: NodePort
  ports:
  - port: 8004
    targetPort: 8004
    nodePort: 30806
    protocol: TCP
  selector:
    app: $DEPLOYMENT_NAME
EOF

    # 應用部署
    kubectl apply -f /tmp/rag-pipeline-k8s-minimal.yaml
    
    if [ $? -eq 0 ]; then
        log_success "K8s 部署配置應用成功"
    else
        log_error "K8s 部署配置應用失敗"
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

# 顯示部署資訊
show_deployment_info() {
    log_success "=== K8s 最小化部署完成 ==="
    
    echo "映像: $REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    echo "命名空間: $NAMESPACE"
    echo "部署名稱: $DEPLOYMENT_NAME"
    echo "部署策略: 最小化映像 + 容器內手動安裝套件"
    echo ""
    
    # 顯示服務端點
    NODE_PORT=$(kubectl get svc $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
    if [ -n "$NODE_PORT" ]; then
        NODE_IP=$(kubectl get nodes -o wide | grep worker2 | awk '{print $6}' 2>/dev/null)
        if [ -n "$NODE_IP" ]; then
            echo "服務端點: http://$NODE_IP:$NODE_PORT"
        fi
    fi
    
    echo ""
    echo "進入容器安裝套件:"
    echo "kubectl exec -it deployment/$DEPLOYMENT_NAME -n $NAMESPACE -- bash"
    echo ""
    echo "容器內操作步驟:"
    echo "1. 檢查 requirements.txt: cat requirements.txt"
    echo "2. 安裝套件: pip install -r requirements.txt"
    echo "3. 啟動服務: python -m uvicorn backend.rag_pipeline.app.main_crewai:app --host 0.0.0.0 --port 8004"
    echo "4. 測試健康檢查: curl http://localhost:8004/health"
    echo ""
    echo "查看日誌:"
    echo "kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
}

# 主函數
main() {
    log_info "Podwise RAG Pipeline K8s 最小化部署腳本"
    
    parse_args "$@"
    confirm_deployment
    setup_environment
    check_prerequisites
    build_minimal_image
    push_image
    create_secrets
    create_k8s_deployment
    wait_for_deployment
    check_service_status
    show_deployment_info
    
    log_success "K8s 最小化部署完成！"
    log_info "請進入容器手動安裝套件"
}

# 執行主函數
main "$@" 