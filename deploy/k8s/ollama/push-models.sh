#!/bin/bash

# 推送多個模型到 Kubernetes Ollama
# 推送台灣版本和 Qwen3:8b 模型 (GGUF 格式)

set -e

echo "🚀 開始推送模型到 Kubernetes Ollama..."

# 檢查 kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安裝"
    exit 1
fi

# 檢查本地模型
TAIWAN_MODEL_PATH="backend/llm/models/Qwen2.5-Taiwan-7B-Instruct/qwen2.5-tw-7b-instruct.gguf"
QWEN3_MODEL_PATH="backend/llm/models/Qwen3-8B"

if [ ! -f "$TAIWAN_MODEL_PATH" ]; then
    echo "❌ 台灣版本 GGUF 模型檔案不存在: $TAIWAN_MODEL_PATH"
    exit 1
fi

if [ ! -d "$QWEN3_MODEL_PATH" ]; then
    echo "❌ Qwen3-8B 模型目錄不存在: $QWEN3_MODEL_PATH"
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

# 直接檢查 Ollama 是否運行
if kubectl exec -n podwise $OLLAMA_POD -- ollama list &> /dev/null; then
    echo "✅ Ollama 服務正常"
else
    echo "❌ Ollama 服務未正常運行"
    exit 1
fi

# 創建台灣版本 Modelfile
echo "📝 創建台灣版本 Modelfile..."
cat > Modelfile.taiwan << 'EOF'
FROM ./qwen2.5-tw-7b-instruct.gguf

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

# 創建 Qwen3 Modelfile
echo "📝 創建 Qwen3 Modelfile..."
cat > Modelfile.qwen3 << 'EOF'
FROM ./Qwen3-8B

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """你是 Qwen3-8B, 一個強大的語言模型助手。"""
EOF

# 推送台灣版本模型
echo "📤 推送台灣版本 GGUF 模型..."
kubectl cp "$TAIWAN_MODEL_PATH" podwise/$OLLAMA_POD:/tmp/qwen2.5-tw-7b-instruct.gguf
kubectl cp Modelfile.taiwan podwise/$OLLAMA_POD:/tmp/Modelfile.taiwan

echo "🔨 創建台灣版本模型..."
kubectl exec -n podwise $OLLAMA_POD -- bash -c "
    cd /tmp && \
    ollama create qwen2.5-taiwan-7b-instruct -f Modelfile.taiwan
"

# 推送 Qwen3 模型
echo "📤 推送 Qwen3 模型..."
kubectl cp backend/llm/models/Qwen3-8B podwise/$OLLAMA_POD:/tmp/Qwen3-8B
kubectl cp Modelfile.qwen3 podwise/$OLLAMA_POD:/tmp/Modelfile.qwen3

echo "🔨 創建 Qwen3 模型..."
kubectl exec -n podwise $OLLAMA_POD -- bash -c "
    cd /tmp && \
    ollama create qwen3:8b -f Modelfile.qwen3
"

# 驗證模型
echo "✅ 驗證模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama list

# 測試模型
echo "🧪 測試台灣版本模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen2.5-taiwan-7b-instruct "你好，請用繁體中文回答：你是誰？" --timeout 30

echo "🧪 測試 Qwen3 模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen3:8b "Hello, who are you?" --timeout 30

echo "🎉 所有模型推送完成！"
echo ""
echo "🌐 Ollama 服務: http://worker1:31134"
echo "📚 可用模型:"
echo "   - qwen2.5-taiwan-7b-instruct (台灣版本 GGUF)"
echo "   - qwen3:8b (Qwen3 8B)"
echo ""
echo "🧪 測試命令:"
echo "   kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen2.5-taiwan-7b-instruct '你好'"
echo "   kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen3:8b 'Hello'" 