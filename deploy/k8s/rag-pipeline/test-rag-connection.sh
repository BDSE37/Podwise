#!/bin/bash
# 測試 RAG Pipeline 連接腳本

echo "🔍 測試 RAG Pipeline 連接..."

# 1. 檢查 K8s Pod 狀態
echo "📊 檢查 RAG Pipeline Pod 狀態..."
kubectl get pods -n podwise | grep rag

# 2. 檢查服務狀態
echo "🔧 檢查 RAG Pipeline 服務狀態..."
kubectl get svc -n podwise | grep rag

# 3. 測試 NodePort 連接
echo "🌐 測試 NodePort 連接..."
RAG_URL="http://192.168.32.56:30806"

echo "測試健康檢查端點..."
curl -s $RAG_URL/health | jq . || echo "❌ 健康檢查失敗"

echo "測試 API 端點..."
curl -s $RAG_URL/docs || echo "❌ API 文檔端點失敗"

# 4. 測試簡單查詢
echo "🔍 測試簡單查詢..."
curl -X POST $RAG_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "測試查詢",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | jq . || echo "❌ 查詢測試失敗"

echo "✅ RAG Pipeline 連接測試完成！" 