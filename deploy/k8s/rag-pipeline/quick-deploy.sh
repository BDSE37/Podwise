#!/bin/bash

# Podwise RAG Pipeline 快速部署腳本
# 整合 K8s 部署和 Worker2 部署

set -e

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

# 顯示幫助信息
show_help() {
    echo "Podwise RAG Pipeline 快速部署腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help              顯示此幫助信息"
    echo "  -m, --mode MODE         部署模式 (k8s|worker2|both)"
    echo "  -b, --builder BUILDER   構建工具 (docker|podman) (預設: podman)"
    echo "  -k, --openai-key KEY   設置 OpenAI API Key"
    echo "  -l, --langfuse-key KEY 設置 Langfuse Public Key"
    echo "  -s, --langfuse-secret SECRET 設置 Langfuse Secret Key"
    echo "  -n, --namespace NS     設置 K8s 命名空間 (預設: podwise)"
    echo "  -t, --tag TAG          設置映像標籤 (預設: latest)"
    echo "  -y, --yes              自動確認所有提示"
    echo ""
    echo "範例:"
    echo "  $0 -m k8s -b podman -k 'your_openai_key'"
    echo "  $0 -m worker2 -k 'your_openai_key'"
    echo "  $0 -m both -b docker -k 'your_openai_key' -y"
    echo ""
}

# 解析命令行參數
parse_args() {
    MODE="k8s"
    BUILDER="podman"
    OPENAI_KEY=""
    LANGFUSE_PUBLIC_KEY=""
    LANGFUSE_SECRET_KEY=""
    NAMESPACE="podwise"
    IMAGE_TAG="latest"
    AUTO_CONFIRM=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -m|--mode)
                MODE="$2"
                shift 2
                ;;
            -b|--builder)
                BUILDER="$2"
                shift 2
                ;;
            -k|--openai-key)
                OPENAI_KEY="$2"
                shift 2
                ;;
            -l|--langfuse-key)
                LANGFUSE_PUBLIC_KEY="$2"
                shift 2
                ;;
            -s|--langfuse-secret)
                LANGFUSE_SECRET_KEY="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
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
    log_info "=== 部署配置 ==="
    echo "部署模式: $MODE"
    echo "構建工具: $BUILDER"
    echo "命名空間: $NAMESPACE"
    echo "映像標籤: $IMAGE_TAG"
    echo "OpenAI Key: ${OPENAI_KEY:+已設置}"
    echo "Langfuse Key: ${LANGFUSE_PUBLIC_KEY:+已設置}"
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
    
    if [ -n "$LANGFUSE_PUBLIC_KEY" ]; then
        export LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY"
        log_success "Langfuse Public Key 已設置"
    fi
    
    if [ -n "$LANGFUSE_SECRET_KEY" ]; then
        export LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY"
        log_success "Langfuse Secret Key 已設置"
    fi
    
    export IMAGE_TAG="$IMAGE_TAG"
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
    
    # 檢查構建工具
    if [ "$BUILDER" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker 未安裝"
            exit 1
        fi
    elif [ "$BUILDER" = "podman" ]; then
        if ! command -v podman &> /dev/null; then
            log_error "Podman 未安裝"
            exit 1
        fi
    else
        log_error "不支援的構建工具: $BUILDER"
        exit 1
    fi
    
    # 檢查 K8s 連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 K8s 集群"
        exit 1
    fi
    
    log_success "前置需求檢查完成"
}

# 執行 K8s 部署
deploy_k8s() {
    log_info "開始 K8s 部署 (使用 $BUILDER)..."
    
    if [ "$BUILDER" = "podman" ] && [ -f "build-and-deploy-podman.sh" ]; then
        chmod +x build-and-deploy-podman.sh
        ./build-and-deploy-podman.sh
    elif [ "$BUILDER" = "docker" ] && [ -f "build-and-deploy-k8s.sh" ]; then
        chmod +x build-and-deploy-k8s.sh
        ./build-and-deploy-k8s.sh
    else
        log_error "$BUILDER 部署腳本不存在"
        exit 1
    fi
}

# 執行 Worker2 部署
deploy_worker2() {
    log_info "開始 Worker2 部署..."
    
    if [ -f "deploy-rag-on-worker2.sh" ]; then
        chmod +x deploy-rag-on-worker2.sh
        ./deploy-rag-on-worker2.sh
    else
        log_error "Worker2 部署腳本不存在"
        exit 1
    fi
}

# 驗證部署
verify_deployment() {
    log_info "驗證部署..."
    
    # 等待服務啟動
    sleep 10
    
    # 檢查 K8s 部署
    if kubectl get deployment rag-pipeline-service -n $NAMESPACE &> /dev/null; then
        log_success "K8s 部署驗證成功"
        
        # 檢查 Pod 狀態
        kubectl get pods -n $NAMESPACE -l app=rag-pipeline-service
        
        # 測試健康檢查
        NODE_PORT=$(kubectl get svc rag-pipeline-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
        if [ -n "$NODE_PORT" ]; then
            NODE_IP=$(kubectl get nodes -o wide | grep worker2 | awk '{print $6}' 2>/dev/null)
            if [ -n "$NODE_IP" ]; then
                if curl -s "http://$NODE_IP:$NODE_PORT/health" > /dev/null; then
                    log_success "健康檢查通過"
                else
                    log_warning "健康檢查失敗"
                fi
            fi
        fi
    else
        log_warning "K8s 部署驗證失敗"
    fi
}

# 顯示部署結果
show_results() {
    log_success "=== 部署完成 ==="
    echo ""
    echo "部署模式: $MODE"
    echo "構建工具: $BUILDER"
    echo "命名空間: $NAMESPACE"
    echo "映像標籤: $IMAGE_TAG"
    echo ""
    
    if [ "$MODE" = "k8s" ] || [ "$MODE" = "both" ]; then
        echo "K8s 服務端點:"
        NODE_PORT=$(kubectl get svc rag-pipeline-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
        if [ -n "$NODE_PORT" ]; then
            NODE_IP=$(kubectl get nodes -o wide | grep worker2 | awk '{print $6}' 2>/dev/null)
            if [ -n "$NODE_IP" ]; then
                echo "  健康檢查: http://$NODE_IP:$NODE_PORT/health"
                echo "  API 文檔: http://$NODE_IP:$NODE_PORT/docs"
                echo "  LLM 狀態: http://$NODE_IP:$NODE_PORT/api/v1/llm-status"
            fi
        fi
        echo ""
        echo "查看日誌: kubectl logs -f deployment/rag-pipeline-service -n $NAMESPACE"
        echo ""
        echo "$BUILDER 相關命令:"
        if [ "$BUILDER" = "podman" ]; then
            echo "podman images | grep podwise-rag-pipeline"
            echo "podman ps -a | grep podwise-rag-pipeline"
        else
            echo "docker images | grep podwise-rag-pipeline"
            echo "docker ps -a | grep podwise-rag-pipeline"
        fi
    fi
    
    if [ "$MODE" = "worker2" ] || [ "$MODE" = "both" ]; then
        echo "Worker2 服務端點:"
        echo "  健康檢查: http://worker2:8002/health"
        echo "  API 文檔: http://worker2:8002/docs"
        echo ""
        echo "查看日誌: ssh worker2 'tail -f /home/bdse37/rag_pipeline/rag_service.log'"
    fi
    
    echo ""
    echo "LLM 備援機制已啟用:"
    echo "  1. Qwen2.5-Taiwan (第一優先)"
    echo "  2. Qwen3:8b (第二優先)"
    if [ -n "$OPENAI_KEY" ]; then
        echo "  3. OpenAI GPT-3.5 (備援)"
        echo "  4. OpenAI GPT-4 (最後備援)"
    else
        echo "  3. OpenAI 備援 (未配置)"
    fi
}

# 主函數
main() {
    log_info "Podwise RAG Pipeline 快速部署腳本"
    
    parse_args "$@"
    confirm_deployment
    setup_environment
    check_prerequisites
    
    case $MODE in
        "k8s")
            deploy_k8s
            ;;
        "worker2")
            deploy_worker2
            ;;
        "both")
            deploy_k8s
            deploy_worker2
            ;;
        *)
            log_error "無效的部署模式: $MODE"
            show_help
            exit 1
            ;;
    esac
    
    verify_deployment
    show_results
    
    log_success "部署流程完成！"
}

# 執行主函數
main "$@" 