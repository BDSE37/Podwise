#!/bin/bash

# PostgreSQL Cleanup 部署腳本
# 用於建立 Docker 映像並部署到 Kubernetes

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置變數
IMAGE_NAME="postgresql-cleanup"
IMAGE_TAG="latest"
NAMESPACE="podwise"
REGISTRY=""  # 如果使用私有 registry，請設定完整路徑

# 函數：印出彩色訊息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函數：檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安裝，請先安裝 $1"
        exit 1
    fi
}

# 函數：檢查 Kubernetes 連線
check_k8s_connection() {
    if ! kubectl cluster-info &> /dev/null; then
        print_error "無法連線到 Kubernetes 叢集"
        exit 1
    fi
    print_info "Kubernetes 連線正常"
}

# 函數：建立 Docker 映像
build_image() {
    print_info "開始建立 Docker 映像..."
    
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    fi
    
    docker build -t $FULL_IMAGE_NAME .
    
    if [ $? -eq 0 ]; then
        print_info "Docker 映像建立成功: $FULL_IMAGE_NAME"
    else
        print_error "Docker 映像建立失敗"
        exit 1
    fi
}

# 函數：推送映像到 Registry (如果指定)
push_image() {
    if [ -n "$REGISTRY" ]; then
        print_info "推送映像到 Registry..."
        docker push $FULL_IMAGE_NAME
        
        if [ $? -eq 0 ]; then
            print_info "映像推送成功"
        else
            print_error "映像推送失敗"
            exit 1
        fi
    else
        print_warning "未指定 Registry，跳過推送步驟"
    fi
}

# 函數：部署到 Kubernetes
deploy_to_k8s() {
    print_info "部署到 Kubernetes..."
    
    # 檢查 namespace 是否存在
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        print_info "建立 namespace: $NAMESPACE"
        kubectl create namespace $NAMESPACE
    fi
    
    # 更新 k8s_deployment.yaml 中的映像名稱
    if [ -n "$REGISTRY" ]; then
        sed -i "s|image: postgresql-cleanup:latest|image: $FULL_IMAGE_NAME|g" k8s_deployment.yaml
    fi
    
    # 部署資源
    kubectl apply -f k8s_deployment.yaml
    
    if [ $? -eq 0 ]; then
        print_info "Kubernetes 部署成功"
    else
        print_error "Kubernetes 部署失敗"
        exit 1
    fi
}

# 函數：驗證部署
verify_deployment() {
    print_info "驗證部署狀態..."
    
    # 等待資源建立
    sleep 5
    
    # 檢查 ConfigMap
    if kubectl get configmap postgresql-cleanup-config -n $NAMESPACE &> /dev/null; then
        print_info "ConfigMap 建立成功"
    else
        print_error "ConfigMap 建立失敗"
    fi
    
    # 檢查 Secret
    if kubectl get secret postgresql-cleanup-secret -n $NAMESPACE &> /dev/null; then
        print_info "Secret 建立成功"
    else
        print_error "Secret 建立失敗"
    fi
    
    # 檢查 CronJob
    if kubectl get cronjob postgresql-cleanup-cronjob -n $NAMESPACE &> /dev/null; then
        print_info "CronJob 建立成功"
    else
        print_error "CronJob 建立失敗"
    fi
    
    # 顯示 CronJob 狀態
    print_info "CronJob 狀態:"
    kubectl get cronjobs -n $NAMESPACE
}

# 函數：顯示使用說明
show_usage() {
    echo "使用方法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help          顯示此說明"
    echo "  -b, --build-only    僅建立 Docker 映像"
    echo "  -d, --deploy-only   僅部署到 Kubernetes (不建立映像)"
    echo "  -r, --registry URL  指定 Docker Registry URL"
    echo "  -t, --tag TAG       指定映像標籤 (預設: latest)"
    echo "  -n, --namespace NS  指定 Kubernetes namespace (預設: podwise)"
    echo ""
    echo "範例:"
    echo "  $0                    # 完整部署流程"
    echo "  $0 -b                 # 僅建立映像"
    echo "  $0 -d                 # 僅部署"
    echo "  $0 -r my-registry.com -t v1.0.0  # 使用自訂 registry 和標籤"
}

# 主程式
main() {
    # 解析命令列參數
    BUILD_ONLY=false
    DEPLOY_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -b|--build-only)
                BUILD_ONLY=true
                shift
                ;;
            -d|--deploy-only)
                DEPLOY_ONLY=true
                shift
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            *)
                print_error "未知選項: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 檢查必要工具
    print_info "檢查必要工具..."
    check_command docker
    check_command kubectl
    
    # 檢查 Kubernetes 連線
    check_k8s_connection
    
    # 執行部署流程
    if [ "$BUILD_ONLY" = true ]; then
        print_info "僅建立 Docker 映像"
        build_image
    elif [ "$DEPLOY_ONLY" = true ]; then
        print_info "僅部署到 Kubernetes"
        deploy_to_k8s
        verify_deployment
    else
        print_info "執行完整部署流程"
        build_image
        push_image
        deploy_to_k8s
        verify_deployment
    fi
    
    print_info "部署完成！"
    print_info "查看 CronJob 狀態: kubectl get cronjobs -n $NAMESPACE"
    print_info "查看日誌: kubectl logs -n $NAMESPACE -l app=postgresql-cleanup"
}

# 執行主程式
main "$@" 