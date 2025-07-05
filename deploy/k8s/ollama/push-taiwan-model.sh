#!/bin/bash

# 推送台灣版本模型到 Kubernetes Ollama 腳本
# 將本地的 Qwen2.5-Taiwan-7B-Instruct 模型推送到 K8s Ollama 服務

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

# 檢查前置條件
check_prerequisites() {
    log_info "檢查前置條件..."
    
    # 檢查 kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝，請先安裝 kubectl"
        exit 1
    fi
    
    # 檢查 Ollama Pod 是否存在
    if ! kubectl get pods -n podwise -l app=ollama-service &> /dev/null; then
        log_error "Ollama Pod 不存在，請先部署 Ollama 服務"
        exit 1
    fi
    
    # 檢查本地模型目錄
    MODEL_PATH="backend/llm/models/Qwen2.5-Taiwan-7B-Instruct"
    if [ ! -d "$MODEL_PATH" ]; then
        log_error "本地模型目錄不存在: $MODEL_PATH"
        exit 1
    fi
    
    log_success "前置條件檢查通過"
}

# 獲取 Ollama Pod 名稱
get_ollama_pod() {
    log_info "獲取 Ollama Pod 名稱..."
    
    OLLAMA_POD=$(kubectl get pods -n podwise -l app=ollama-service -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$OLLAMA_POD" ]; then
        log_error "無法獲取 Ollama Pod 名稱"
        exit 1
    fi
    
    log_success "Ollama Pod: $OLLAMA_POD"
    echo "$OLLAMA_POD"
}

# 檢查 Ollama 服務狀態
check_ollama_service() {
    log_info "檢查 Ollama 服務狀態..."
    
    local pod_name=$1
    
    # 等待服務啟動
    log_info "等待 Ollama 服務啟動..."
    sleep 30
    
    # 檢查服務狀態
    if kubectl exec -n podwise $pod_name -- curl -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama 服務正常運行"
    else
        log_error "Ollama 服務未正常運行"
        exit 1
    fi
}

# 創建 Modelfile
create_modelfile() {
    log_info "創建 Modelfile..."
    
    cat > Modelfile << 'EOF'
FROM ./Qwen2.5-Taiwan-7B-Instruct

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """你是 Qwen-Taiwan-7B, 來自台灣。你是一位樂於回答問題的助手。"""
EOF
    
    log_success "Modelfile 創建完成"
}

# 推送模型到 Ollama
push_model_to_ollama() {
    log_info "推送模型到 Ollama..."
    
    local pod_name=$1
    
    # 複製模型檔案到 Pod
    log_info "複製模型檔案到 Ollama Pod..."
    kubectl cp backend/llm/models/Qwen2.5-Taiwan-7B-Instruct podwise/$pod_name:/tmp/Qwen2.5-Taiwan-7B-Instruct
    
    # 複製 Modelfile 到 Pod
    log_info "複製 Modelfile 到 Ollama Pod..."
    kubectl cp Modelfile podwise/$pod_name:/tmp/Modelfile
    
    # 在 Pod 中創建模型
    log_info "在 Ollama Pod 中創建模型..."
    kubectl exec -n podwise $pod_name -- bash -c "
        cd /tmp && \
        ollama create qwen2.5-taiwan-7b-instruct -f Modelfile && \
        echo '模型創建完成'
    "
    
    log_success "模型推送完成"
}

# 驗證模型
verify_model() {
    log_info "驗證模型..."
    
    local pod_name=$1
    
    # 檢查模型列表
    log_info "檢查可用模型..."
    kubectl exec -n podwise $pod_name -- ollama list
    
    # 測試模型
    log_info "測試模型回應..."
    kubectl exec -n podwise $pod_name -- ollama run qwen2.5-taiwan-7b-instruct "你好，請用繁體中文回答：你是誰？" --timeout 30
    
    log_success "模型驗證完成"
}

# 更新配置
update_config() {
    log_info "更新系統配置..."
    
    # 更新下載腳本，將台灣版本設為第一優先
    log_info "更新模型下載腳本..."
    
    cat > deploy/k8s/ollama/download-models.sh << 'EOF'
#!/bin/bash

# Qwen 模型下載腳本
# 用於在 Ollama 容器中下載所需的 LLM 模型

set -e

echo "🚀 開始下載 Qwen 模型..."

# 等待 Ollama 服務啟動
echo "⏳ 等待 Ollama 服務啟動..."
sleep 30

# 檢查 Ollama 服務狀態
echo "🔍 檢查 Ollama 服務狀態..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama 服務未啟動，請檢查服務狀態"
    exit 1
fi

echo "✅ Ollama 服務正常運行"

# 檢查是否已有本地台灣版本模型
echo "🔍 檢查本地台灣版本模型..."
if ollama list | grep -q "qwen2.5-taiwan-7b-instruct"; then
    echo "✅ 本地台灣版本模型已存在"
else
    echo "📥 下載 Qwen2.5-Taiwan-7B-Instruct..."
    ollama pull weiren119/Qwen2.5-Taiwan-7B-Instruct
fi

# 下載 Qwen2.5-8B-Instruct (第二優先)
echo "📥 下載 Qwen2.5-8B-Instruct..."
ollama pull Qwen/Qwen2.5-8B-Instruct

# 下載 Qwen3:8b (備用)
echo "📥 下載 Qwen3:8b..."
ollama pull qwen2.5:8b

# 列出已下載的模型
echo "📋 已下載的模型列表："
ollama list

echo "✅ 所有模型下載完成！"
EOF
    
    log_success "配置更新完成"
}

# 顯示服務資訊
show_service_info() {
    log_info "Podwise 台灣版本模型部署完成！"
    echo ""
    echo "🌐 Ollama 服務端點: http://worker1:31134"
    echo "📚 台灣版本模型: qwen2.5-taiwan-7b-instruct"
    echo "🔧 模型管理: kubectl exec -n podwise <pod-name> -- ollama list"
    echo "🧪 模型測試: kubectl exec -n podwise <pod-name> -- ollama run qwen2.5-taiwan-7b-instruct '你好'"
    echo ""
    log_success "部署完成！"
}

# 主函數
main() {
    log_info "開始推送台灣版本模型到 Kubernetes Ollama..."
    
    # 檢查前置條件
    check_prerequisites
    
    # 獲取 Ollama Pod 名稱
    OLLAMA_POD=$(get_ollama_pod)
    
    # 檢查 Ollama 服務狀態
    check_ollama_service $OLLAMA_POD
    
    # 創建 Modelfile
    create_modelfile
    
    # 推送模型到 Ollama
    push_model_to_ollama $OLLAMA_POD
    
    # 驗證模型
    verify_model $OLLAMA_POD
    
    # 更新配置
    update_config
    
    # 顯示服務資訊
    show_service_info
}

# 執行主函數
main "$@" 