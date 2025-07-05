#!/bin/bash

# 推送本地台灣版本模型到 Kubernetes Ollama
# 簡化版本，專門用於推送本地模型

set -e

echo "🚀 開始推送本地台灣版本模型到 Kubernetes Ollama..."

# 檢查 kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安裝"
    exit 1
fi

# 檢查本地模型
MODEL_PATH="backend/llm/models/Qwen2.5-Taiwan-7B-Instruct"
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ 本地模型目錄不存在: $MODEL_PATH"
    exit 1
fi

echo "✅ 本地模型檢查通過"

# 獲取 Ollama Pod
OLLAMA_POD=$(kubectl get pods -n podwise -l app=ollama-service -o jsonpath='{.items[0].metadata.name}')
if [ -z "$OLLAMA_POD" ]; then
    echo "❌ 無法獲取 Ollama Pod"
    exit 1
fi

echo "📋 Ollama Pod: $OLLAMA_POD"

# 檢查 Ollama 服務
echo "⏳ 檢查 Ollama 服務..."
sleep 10
if ! kubectl exec -n podwise $OLLAMA_POD -- curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama 服務未正常運行"
    exit 1
fi

echo "✅ Ollama 服務正常"

# 創建 Modelfile
echo "📝 創建 Modelfile..."
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

# 複製模型到 Pod
echo "📤 複製模型檔案到 Ollama Pod..."
kubectl cp backend/llm/models/Qwen2.5-Taiwan-7B-Instruct podwise/$OLLAMA_POD:/tmp/Qwen2.5-Taiwan-7B-Instruct

# 複製 Modelfile 到 Pod
echo "📤 複製 Modelfile 到 Ollama Pod..."
kubectl cp Modelfile podwise/$OLLAMA_POD:/tmp/Modelfile

# 創建模型
echo "🔨 在 Ollama 中創建模型..."
kubectl exec -n podwise $OLLAMA_POD -- bash -c "
    cd /tmp && \
    ollama create qwen2.5-taiwan-7b-instruct -f Modelfile
"

# 驗證模型
echo "✅ 驗證模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama list

echo "🎉 台灣版本模型推送完成！"
echo ""
echo "🌐 Ollama 服務: http://worker1:31134"
echo "📚 模型名稱: qwen2.5-taiwan-7b-instruct"
echo "🧪 測試命令: kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen2.5-taiwan-7b-instruct '你好'" 