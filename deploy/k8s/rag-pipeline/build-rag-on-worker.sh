#!/bin/bash
# RAG Pipeline 在 Worker 節點建置腳本
# 在 worker2 節點上執行

set -e

echo "🚀 開始在 worker2 節點建置 RAG Pipeline..."

# 1. 檢查並切換到正確目錄
cd /home/bai/Desktop/Podwise/backend/rag_pipeline

# 2. 檢查必要檔案
echo "📋 檢查必要檔案..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 不存在"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile 不存在"
    exit 1
fi

# 3. 建置 Docker 映像檔
echo "🔨 建置 RAG Pipeline Docker 映像檔..."
podman build -t localhost/podwise-rag-pipeline:latest .

# 4. 標籤映像檔用於推送到 registry
echo "🏷️ 標籤映像檔..."
podman tag localhost/podwise-rag-pipeline:latest 192.168.32.38:5000/podwise-rag-pipeline:latest

# 5. 推送到 registry
echo "📤 推送映像檔到 registry..."
podman push 192.168.32.38:5000/podwise-rag-pipeline:latest

# 6. 清理本地映像檔
echo "🧹 清理本地映像檔..."
podman rmi localhost/podwise-rag-pipeline:latest

# 7. 重新部署 K8s Pod
echo "🔄 重新部署 K8s Pod..."
kubectl delete pod -n podwise -l app=rag-pipeline-service --force --grace-period=0

# 8. 等待 Pod 重新啟動
echo "⏳ 等待 Pod 重新啟動..."
sleep 10

# 9. 檢查 Pod 狀態
echo "📊 檢查 Pod 狀態..."
kubectl get pods -n podwise | grep rag

# 10. 檢查 Pod 日誌
echo "📝 檢查 Pod 日誌..."
POD_NAME=$(kubectl get pods -n podwise -l app=rag-pipeline-service -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME -n podwise --tail=20

# 11. 測試健康檢查
echo "🏥 測試健康檢查..."
sleep 30
curl -f http://192.168.32.56:30806/health || echo "❌ 健康檢查失敗"

echo "✅ RAG Pipeline 建置完成！" 