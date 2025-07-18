#!/bin/bash

# Kubernetes 版本 Ollama 模型修復腳本
# 解決向量維度不匹配和 LLM 模型不存在問題

set -e

echo "🔧 開始修復 Kubernetes Ollama 模型..."

# 檢查 kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安裝"
    exit 1
fi

# 獲取 Ollama Pod
echo "🔍 獲取 Ollama Pod..."
OLLAMA_POD=$(kubectl get pods -n podwise -l app=ollama-service -o jsonpath='{.items[0].metadata.name}')
if [ -z "$OLLAMA_POD" ]; then
    echo "❌ 無法獲取 Ollama Pod"
    exit 1
fi

echo "📋 Ollama Pod: $OLLAMA_POD"

# 檢查 Ollama 服務
echo "🔍 檢查 Ollama 服務狀態..."
sleep 10
if ! kubectl exec -n podwise $OLLAMA_POD -- curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama 服務未正常運行"
    exit 1
fi

echo "✅ Ollama 服務正常"

# 下載必要的嵌入模型
echo "📥 下載嵌入模型..."

echo "📥 下載 BGE-M3 嵌入模型 (1024維)..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull BAAI/bge-m3

echo "📥 下載 Nomic 嵌入模型 (備用)..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull nomic-embed-text

echo "📥 下載 All-MiniLM 嵌入模型 (備用)..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull all-minilm

# 下載必要的 LLM 模型
echo "📥 下載 LLM 模型..."

echo "📥 下載台灣版本模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull weiren119/Qwen2.5-Taiwan-8B-Instruct

echo "📥 下載 Qwen2.5 模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull Qwen/Qwen2.5-8B-Instruct

echo "📥 下載 Qwen3 模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull qwen2.5:8b

echo "📥 下載 GPT-3.5 模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama pull gpt-3.5-turbo

# 驗證模型
echo "✅ 驗證模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama list

echo "🧪 測試台灣版本模型..."
kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen2.5-taiwan-7b-instruct "你好，請用繁體中文回答：你是誰？" --timeout 30

echo "🧪 測試 BGE-M3 嵌入模型..."
kubectl exec -n podwise $OLLAMA_POD -- bash -c '
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '"'"'{"model": "bge-m3", "prompt": "測試文本"}'"'"' | jq ".embedding | length"
'

echo "🎉 Kubernetes Ollama 模型修復完成！"
echo ""
echo "📋 可用模型:"
kubectl exec -n podwise $OLLAMA_POD -- ollama list
echo ""
echo "🌐 Ollama 服務: http://worker1:31134"
echo "📚 主要模型:"
echo "   - qwen2.5-taiwan-7b-instruct (台灣版本)"
echo "   - bge-m3 (1024維嵌入)"
echo ""
echo "🧪 測試命令:"
echo "   kubectl exec -n podwise $OLLAMA_POD -- ollama run qwen2.5-taiwan-7b-instruct '你好'"
echo "   kubectl exec -n podwise $OLLAMA_POD -- curl -X POST http://localhost:11434/api/embeddings -H 'Content-Type: application/json' -d '{\"model\": \"bge-m3\", \"prompt\": \"測試\"}'" 