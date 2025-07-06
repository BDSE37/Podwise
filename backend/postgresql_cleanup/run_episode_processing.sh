#!/bin/bash

# Episodes 處理腳本 - K8s 環境版本
# 在 K8s 叢集內執行 episodes 資料處理

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

# 檢查 kubectl
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝"
        exit 1
    fi
    
    log_info "kubectl 版本: $(kubectl version --client --short)"
}

# 建立臨時 Pod 來處理 episodes
create_episode_processor_pod() {
    log_info "建立臨時 Pod 來處理 episodes..."
    
    # 建立 Pod YAML
    cat > temp_episode_processor.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: episode-processor-temp
  namespace: podwise
spec:
  containers:
  - name: episode-processor
    image: python:3.10-slim
    command: ["/bin/bash"]
    args:
    - -c
    - |
      echo "開始安裝依賴..."
      pip install psycopg2-binary
      
      echo "建立處理腳本..."
      cat > episode_processor.py << 'SCRIPT_EOF'
      # 這裡會插入 episode_processor.py 的內容
      SCRIPT_EOF
      
      cat > config.py << 'CONFIG_EOF'
      # 這裡會插入 config.py 的內容
      CONFIG_EOF
      
      echo "開始處理 episodes..."
      python episode_processor.py --episodes-dir /episodes --insert-db --verbose
      
      echo "處理完成！"
    volumeMounts:
    - name: episodes-data
      mountPath: /episodes
    env:
    - name: POSTGRES_HOST
      value: "postgres"
    - name: POSTGRES_PORT
      value: "5432"
    - name: POSTGRES_DB
      value: "podcast"
    - name: POSTGRES_USER
      value: "bdse37"
    - name: POSTGRES_PASSWORD
      value: "111111"
    - name: K8S_NAMESPACE
      value: "podwise"
  volumes:
  - name: episodes-data
    hostPath:
      path: /home/bai/Desktop/Podwise/backend/postgresql_cleanup/episodes
      type: Directory
  restartPolicy: Never
EOF
    
    # 部署 Pod
    kubectl apply -f temp_episode_processor.yaml
    
    log_info "Pod 已建立，等待啟動..."
    kubectl wait --for=condition=Ready pod/episode-processor-temp -n podwise --timeout=60s
    
    log_success "Pod 已準備就緒！"
}

# 執行處理
run_processing() {
    log_info "開始執行 episodes 處理..."
    
    # 查看 Pod 日誌
    kubectl logs -f episode-processor-temp -n podwise
}

# 清理資源
cleanup() {
    log_info "清理臨時資源..."
    
    # 刪除 Pod
    kubectl delete pod episode-processor-temp -n podwise --ignore-not-found=true
    
    # 刪除臨時檔案
    rm -f temp_episode_processor.yaml
    
    log_success "清理完成！"
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  --create    建立處理 Pod"
    echo "  --run       執行處理"
    echo "  --logs      查看日誌"
    echo "  --cleanup   清理資源"
    echo "  --all       執行完整流程 (建立->執行->清理)"
    echo "  -h, --help  顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0 --all    執行完整處理流程"
    echo "  $0 --logs   查看處理日誌"
}

# 主函數
main() {
    # 解析命令列參數
    case "${1:-}" in
        --create)
            check_kubectl
            create_episode_processor_pod
            ;;
        --run)
            run_processing
            ;;
        --logs)
            kubectl logs -f episode-processor-temp -n podwise
            ;;
        --cleanup)
            cleanup
            ;;
        --all)
            check_kubectl
            create_episode_processor_pod
            run_processing
            cleanup
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "未知參數: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@" 