#!/bin/bash

# Ollama 部署腳本
# 部署 Ollama 服務並下載所需的 LLM 模型

set -e

echo "🚀 開始部署 Ollama 服務..."

# 部署 Ollama 到 Kubernetes
echo "📦 部署 Ollama 到 Kubernetes..."
kubectl apply -f deploy/k8s/ollama/ollama-deployment.yaml

# 等待 Pod 啟動
echo "⏳ 等待 Ollama Pod 啟動..."
kubectl wait --for=condition=ready pod -l app=ollama-service -n podwise --timeout=300s

# 獲取 Pod 名稱
OLLAMA_POD=$(kubectl get pods -n podwise -l app=ollama-service -o jsonpath='{.items[0].metadata.name}')
echo "📋 Ollama Pod: $OLLAMA_POD"

# 等待服務完全啟動
echo "⏳ 等待 Ollama 服務完全啟動..."
sleep 60

# 檢查服務狀態
echo "🔍 檢查 Ollama 服務狀態..."
kubectl exec -n podwise $OLLAMA_POD -- curl -s http://localhost:11434/api/tags

echo "✅ Ollama 服務部署完成！"

# 下載模型
echo "📥 開始下載 LLM 模型..."
kubectl cp deploy/k8s/ollama/download-models.sh podwise/$OLLAMA_POD:/tmp/download-models.sh
kubectl exec -n podwise $OLLAMA_POD -- chmod +x /tmp/download-models.sh
kubectl exec -n podwise $OLLAMA_POD -- /tmp/download-models.sh

echo "🎉 Ollama 部署和模型下載完成！"
echo "📊 服務端點: http://worker1:31134"
echo "📋 可用模型:"
kubectl exec -n podwise $OLLAMA_POD -- ollama list 