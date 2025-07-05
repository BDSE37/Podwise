#!/bin/bash

# Podwise RAG Pipeline Worker2 部署腳本
# 用於在 worker2 節點上部署 RAG pipeline，並引用 K8s 中的 LLM 服務

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
WORKER2_HOST="bdse37@worker2"
RAG_PIPELINE_DIR="/home/bdse37/rag_pipeline"
REGISTRY="192.168.32.38:5000"
IMAGE_NAME="podwise-rag-pipeline"
IMAGE_TAG="latest"
CONTAINER_NAME="rag-pipeline-worker2"

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

# 檢查 SSH 連接
check_ssh_connection() {
    log_info "檢查 SSH 連接到 worker2..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes $WORKER2_HOST "echo 'SSH 連接成功'" 2>/dev/null; then
        log_success "SSH 連接正常"
    else
        log_error "無法連接到 worker2，請檢查 SSH 配置"
        exit 1
    fi
}

# 檢查 RAG pipeline 目錄
check_rag_pipeline_dir() {
    log_info "檢查 RAG pipeline 目錄..."
    if ssh $WORKER2_HOST "[ -d $RAG_PIPELINE_DIR ]"; then
        log_success "RAG pipeline 目錄存在"
        ssh $WORKER2_HOST "ls -la $RAG_PIPELINE_DIR"
    else
        log_error "RAG pipeline 目錄不存在: $RAG_PIPELINE_DIR"
        exit 1
    fi
}

# 檢查 K8s 服務狀態
check_k8s_services() {
    log_info "檢查 K8s 服務狀態..."
    
    # 檢查 LLM 服務
    if kubectl get svc -n podwise llm-service >/dev/null 2>&1; then
        log_success "LLM 服務存在"
        kubectl get svc -n podwise llm-service
    else
        log_error "LLM 服務不存在"
        exit 1
    fi
    
    # 檢查 TTS 服務
    if kubectl get svc -n podwise tts-service >/dev/null 2>&1; then
        log_success "TTS 服務存在"
        kubectl get svc -n podwise tts-service
    else
        log_warning "TTS 服務不存在"
    fi
    
    # 檢查 STT 服務
    if kubectl get svc -n podwise stt-service >/dev/null 2>&1; then
        log_success "STT 服務存在"
        kubectl get svc -n podwise stt-service
    else
        log_warning "STT 服務不存在"
    fi
}

# 安裝依賴
install_dependencies() {
    log_info "在 worker2 上安裝 Python 依賴..."
    
    # 檢查並安裝 pip
    ssh $WORKER2_HOST "if ! command -v pip3 &> /dev/null; then sudo apt update && sudo apt install -y python3-pip; fi"
    
    # 安裝依賴
    ssh $WORKER2_HOST "cd $RAG_PIPELINE_DIR && pip3 install --upgrade pip"
    ssh $WORKER2_HOST "cd $RAG_PIPELINE_DIR && pip3 install -r requirements.txt"
    
    # 安裝額外的依賴
    ssh $WORKER2_HOST "cd $RAG_PIPELINE_DIR && pip3 install pydantic-settings"
    
    log_success "依賴安裝完成"
}

# 測試 K8s 服務連線
test_k8s_connections() {
    log_info "測試 K8s 服務連線..."
    
    # 獲取 worker1 IP
    WORKER1_IP=$(kubectl get nodes -o wide | grep worker1 | awk '{print $6}')
    if [ -z "$WORKER1_IP" ]; then
        WORKER1_IP="192.168.32.38"  # 預設 IP
    fi
    
    # 測試 LLM 服務
    log_info "測試 LLM 服務連線..."
    if ssh $WORKER2_HOST "curl -s http://$WORKER1_IP:30800/health" >/dev/null 2>&1; then
        log_success "LLM 服務連線正常"
    else
        log_warning "LLM 服務連線失敗，但繼續部署"
    fi
    
    # 測試 TTS 服務
    log_info "測試 TTS 服務連線..."
    if ssh $WORKER2_HOST "curl -s http://$WORKER1_IP:30801/health" >/dev/null 2>&1; then
        log_success "TTS 服務連線正常"
    else
        log_warning "TTS 服務連線失敗"
    fi
    
    # 測試 STT 服務
    log_info "測試 STT 服務連線..."
    if ssh $WORKER2_HOST "curl -s http://$WORKER1_IP:30802/health" >/dev/null 2>&1; then
        log_success "STT 服務連線正常"
    else
        log_warning "STT 服務連線失敗"
    fi
}

# 設置環境變數
setup_environment() {
    log_info "設置環境變數..."
    
    # 檢查 OpenAI API Key
    if [ -n "$OPENAI_API_KEY" ]; then
        log_info "✅ 檢測到 OpenAI API Key，將啟用備援機制"
        OPENAI_CONFIG="export OPENAI_API_KEY=\"$OPENAI_API_KEY\""
    else
        log_warning "⚠️  未設置 OpenAI API Key，將僅使用 Qwen 模型"
        OPENAI_CONFIG="# export OPENAI_API_KEY=\"\""
    fi
    
    # 創建環境變數檔案
    cat > /tmp/rag_env.sh << EOF
#!/bin/bash
# K8s 服務配置
export LLM_HOST="192.168.32.38"
export LLM_PORT="30800"
export TTS_HOST="192.168.32.38"
export TTS_PORT="30801"
export STT_HOST="192.168.32.38"
export STT_PORT="30802"

# Python 配置
export PYTHONPATH="$RAG_PIPELINE_DIR"
export PYTHONUNBUFFERED="1"
export CUDA_VISIBLE_DEVICES="0"

# 應用配置
export APP_ENV="production"
export DEBUG="false"
export LOG_LEVEL="INFO"

# LLM 配置
export OLLAMA_HOST="http://worker1:11434"
export OLLAMA_MODEL="qwen2.5:8b"

# OpenAI 備援配置
$OPENAI_CONFIG

# 資料庫配置
export MONGODB_URI="mongodb://worker3:27017/podwise"
export POSTGRES_HOST="worker3"
export POSTGRES_PORT="5432"

# 向量搜尋配置
export MILVUS_HOST="worker3"
export MILVUS_PORT="19530"
EOF
    
    # 複製到 worker2
    scp /tmp/rag_env.sh $WORKER2_HOST:$RAG_PIPELINE_DIR/
    ssh $WORKER2_HOST "chmod +x $RAG_PIPELINE_DIR/rag_env.sh"
    
    log_success "環境變數設置完成"
}

# 測試 RAG pipeline
test_rag_pipeline() {
    log_info "測試 RAG pipeline..."
    
    # 創建測試腳本
    cat > /tmp/test_rag.py << 'EOF'
#!/usr/bin/env python3
"""
RAG Pipeline 測試腳本 - 包含 LLM 備援機制測試
"""

import sys
import os
sys.path.append('/home/bdse37/rag_pipeline')

try:
    from config.integrated_config import get_config
    from core.qwen3_llm_manager import get_qwen3_llm_manager
    
    print("=== RAG Pipeline 測試 ===")
    
    # 測試配置
    config = get_config()
    print("✅ 配置載入成功")
    
    # 檢查優先級順序
    priority_models = config.models.llm_priority or []
    print(f"📋 模型優先級順序: {priority_models}")
    
    # 檢查台灣模型是否為第一優先
    taiwan_first = priority_models and priority_models[0] == "qwen2.5:taiwan"
    print(f"🇹🇼 台灣模型第一優先: {'✅' if taiwan_first else '❌'}")
    
    # 測試 LLM 管理器
    manager = get_qwen3_llm_manager()
    available_models = manager.get_available_models()
    print(f"🤖 可用模型: {available_models}")
    
    # 檢查 OpenAI 配置
    openai_configured = bool(config.api.openai_api_key)
    print(f"🔑 OpenAI 備援配置: {'✅ 已配置' if openai_configured else '❌ 未配置'}")
    
    # 測試健康檢查
    current_model = manager.current_model
    is_healthy = manager.test_model_health(current_model)
    print(f"🏥 當前模型 {current_model} 健康狀態: {'✅' if is_healthy else '❌'}")
    
    # 測試備援機制
    best_model = manager.get_best_model()
    print(f"🎯 最佳模型: {best_model}")
    
    # 測試簡單查詢
    if is_healthy:
        response = manager.call_with_fallback("請用繁體中文簡單介紹一下你自己。")
        success = "錯誤" not in response and len(response) > 10
        print(f"💬 測試回應: {'✅ 成功' if success else '❌ 失敗'}")
        print(f"   回應內容: {response[:100]}...")
    else
        print("⚠️  模型不健康，跳過查詢測試")
    
    print("=== 測試完成 ===")
    
except Exception as e:
    print(f"❌ 測試失敗: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
    
    # 複製到 worker2 並執行
    scp /tmp/test_rag.py $WORKER2_HOST:$RAG_PIPELINE_DIR/
    ssh $WORKER2_HOST "cd $RAG_PIPELINE_DIR && source rag_env.sh && python3 test_rag.py"
    
    if [ $? -eq 0 ]; then
        log_success "RAG pipeline 測試通過"
    else
        log_error "RAG pipeline 測試失敗"
        exit 1
    fi
}

# 啟動 RAG pipeline 服務
start_rag_service() {
    log_info "啟動 RAG pipeline 服務..."
    
    # 創建啟動腳本
    cat > /tmp/start_rag_service.py << 'EOF'
#!/usr/bin/env python3
"""
RAG Pipeline 服務啟動腳本 - CrewAI 架構
"""

import sys
import os
sys.path.append('/home/bdse37/rag_pipeline')

from app.main_crewai import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        workers=1
    )
EOF
    
    # 複製到 worker2
    scp /tmp/start_rag_service.py $WORKER2_HOST:$RAG_PIPELINE_DIR/
    
    # 啟動服務（在背景運行）
    ssh $WORKER2_HOST "cd $RAG_PIPELINE_DIR && source rag_env.sh && nohup python3 start_rag_service.py > rag_service.log 2>&1 &"
    
    # 等待服務啟動
    sleep 10
    
    # 檢查服務狀態
    if ssh $WORKER2_HOST "curl -s http://localhost:8002/health" >/dev/null 2>&1; then
        log_success "RAG pipeline 服務啟動成功"
        ssh $WORKER2_HOST "curl -s http://localhost:8002/health"
    else
        log_error "RAG pipeline 服務啟動失敗"
        ssh $WORKER2_HOST "tail -20 $RAG_PIPELINE_DIR/rag_service.log"
        exit 1
    fi
}

# 顯示服務資訊
show_service_info() {
    log_info "=== RAG Pipeline 服務資訊 ==="
    echo "服務端點: http://worker2:8002"
    echo "健康檢查: http://worker2:8002/health"
    echo "API 文檔: http://worker2:8002/docs"
    echo ""
    echo "K8s 服務連線:"
    echo "- LLM 服務: http://192.168.32.38:30800"
    echo "- TTS 服務: http://192.168.32.38:30801"
    echo "- STT 服務: http://192.168.32.38:30802"
    echo ""
    echo "日誌檔案: $RAG_PIPELINE_DIR/rag_service.log"
    echo "環境變數: $RAG_PIPELINE_DIR/rag_env.sh"
}

# 主函數
main() {
    log_info "開始部署 RAG pipeline 到 worker2..."
    
    check_ssh_connection
    check_rag_pipeline_dir
    check_k8s_services
    install_dependencies
    test_k8s_connections
    setup_environment
    test_rag_pipeline
    start_rag_service
    show_service_info
    
    log_success "RAG pipeline 部署完成！"
}

# 執行主函數
main "$@" 