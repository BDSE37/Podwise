#!/bin/bash
# RAG Pipeline 單節點部署腳本
# 適用於任何可用的 K8s 節點

set -e

echo "🚀 開始單節點 RAG Pipeline 部署..."

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

# 7. 切換到部署目錄
cd /home/bai/Desktop/Podwise/deploy/k8s/rag-pipeline

# 8. 刪除舊的 Pod（如果存在）
echo "🗑️ 清理舊的部署..."
kubectl delete pod -n podwise -l app=rag-pipeline-service --force --grace-period=0 2>/dev/null || true

# 9. 應用 PVC 配置
echo "📦 創建 PVC..."
kubectl apply -f rag-pipeline-pvc-single.yaml

# 10. 應用新的部署配置
echo "🚀 部署 RAG Pipeline..."
kubectl apply -f rag-pipeline-single-node.yaml

# 11. 等待 Pod 啟動
echo "⏳ 等待 Pod 啟動..."
sleep 30

# 12. 檢查 Pod 狀態
echo "📊 檢查 Pod 狀態..."
kubectl get pods -n podwise | grep rag

# 13. 檢查 Pod 日誌
echo "📝 檢查 Pod 日誌..."
POD_NAME=$(kubectl get pods -n podwise -l app=rag-pipeline-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$POD_NAME" ]; then
    kubectl logs $POD_NAME -n podwise --tail=20
else
    echo "⚠️ Pod 尚未啟動，請稍後檢查"
fi

# 14. 檢查服務狀態
echo "🔍 檢查服務狀態..."
kubectl get svc -n podwise | grep rag

# 15. 等待服務完全啟動
echo "⏳ 等待服務完全啟動..."
sleep 60

# 16. 測試健康檢查
echo "🏥 測試健康檢查..."
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
if [ -n "$NODE_IP" ]; then
    echo "測試節點 IP: $NODE_IP"
    curl -f http://$NODE_IP:30806/health || echo "❌ 健康檢查失敗，請檢查 Pod 日誌"
else
    echo "⚠️ 無法獲取節點 IP"
fi

echo "✅ RAG Pipeline 單節點部署完成！"
echo "📋 後續步驟："
echo "1. 檢查 Pod 狀態: kubectl get pods -n podwise | grep rag"
echo "2. 查看日誌: kubectl logs -n podwise -l app=rag-pipeline-service -f"
echo "3. 測試 API: curl http://<NODE_IP>:30806/health" 