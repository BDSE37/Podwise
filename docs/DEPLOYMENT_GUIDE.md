# Podwise 後端服務部署指南

## 📋 目錄
1. [環境配置](#環境配置)
2. [資料庫服務部署](#資料庫服務部署)
3. [應用服務部署](#應用服務部署)
4. [服務健康檢查](#服務健康檢查)
5. [故障排除](#故障排除)

## 🔧 環境配置

### 1. 建立環境變數檔案
```bash
# 複製環境配置範例
cp env.example .env

# 編輯 .env 檔案，填入實際值
nano .env
```

### 2. 重要環境變數說明
- **資料庫服務**: 指向 K8s 服務名
- **應用服務**: 指向本地 pod 或 K8s 服務
- **API Keys**: 從環境變數或 K8s Secret 讀取

## 🗄️ 資料庫服務部署

### PostgreSQL 部署
```bash
# 建立 namespace（如果不存在）
kubectl apply -f ../deploy/k8s/podwise-namespace.yaml

# 部署 PostgreSQL
kubectl apply -f ../deploy/k8s/postgresql/postgres-pv.yaml
kubectl apply -f ../deploy/k8s/postgresql/postgres-pvc.yaml
kubectl apply -f ../deploy/k8s/postgresql/postgres-deployment.yaml
kubectl apply -f ../deploy/k8s/postgresql/postgres-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep postgres
kubectl get svc -n podwise | grep postgres
```

### MongoDB 部署
```bash
# 部署 MongoDB
kubectl apply -f ../deploy/k8s/mongodb/mongo-deployment.yaml
kubectl apply -f ../deploy/k8s/mongodb/mongo-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep mongo
kubectl get svc -n podwise | grep mongo
```

### MinIO 部署
```bash
# 部署 MinIO
kubectl apply -f ../deploy/k8s/minio/minio-deployment.yaml
kubectl apply -f ../deploy/k8s/minio/minio-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep minio
kubectl get svc -n podwise | grep minio
```

### Milvus 部署（worker3 docker）
```bash
# 在 worker3 節點上執行
ssh worker3

# 啟動 Milvus docker container
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest standalone

# 檢查容器狀態
docker ps | grep milvus
```

## 🚀 應用服務部署

### RAG Pipeline 部署
```bash
# 建立 RAG Pipeline pod
kubectl apply -f ../deploy/k8s/rag-pipeline/rag-pipeline-deployment.yaml
kubectl apply -f ../deploy/k8s/rag-pipeline/rag-pipeline-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep rag
kubectl get svc -n podwise | grep rag
```

### ML Pipeline 部署
```bash
# 建立 ML Pipeline pod
kubectl apply -f ../deploy/k8s/ml-pipeline/ml-pipeline-deployment.yaml
kubectl apply -f ../deploy/k8s/ml-pipeline/ml-pipeline-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep ml
kubectl get svc -n podwise | grep ml
```

### TTS 服務部署
```bash
# 建立 TTS pod
kubectl apply -f ../deploy/k8s/tts/tts-deployment.yaml
kubectl apply -f ../deploy/k8s/tts/tts-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep tts
kubectl get svc -n podwise | grep tts
```

### STT 服務部署
```bash
# 建立 STT pod
kubectl apply -f ../deploy/k8s/stt/stt-deployment.yaml
kubectl apply -f ../deploy/k8s/stt/stt-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep stt
kubectl get svc -n podwise | grep stt
```

### Ollama 服務部署
```bash
# 建立 Ollama pod
kubectl apply -f ../deploy/k8s/ollama/ollama-deployment.yaml
kubectl apply -f ../deploy/k8s/ollama/ollama-service.yaml

# 檢查部署狀態
kubectl get pods -n podwise | grep ollama
kubectl get svc -n podwise | grep ollama
```

## 🔍 服務健康檢查

### 檢查所有服務狀態
```bash
# 檢查所有 pod 狀態
kubectl get pods -n podwise

# 檢查所有服務狀態
kubectl get svc -n podwise

# 檢查 pod 日誌
kubectl logs -n podwise <pod-name>

# 檢查服務端點
kubectl get endpoints -n podwise
```

### 測試服務連線
```bash
# 測試 PostgreSQL
kubectl exec -n podwise <postgres-pod> -- psql -U bdse37 -d podcast -c "SELECT 1;"

# 測試 MongoDB
kubectl exec -n podwise <mongo-pod> -- mongosh --eval "db.runCommand('ping')"

# 測試 MinIO
kubectl exec -n podwise <minio-pod> -- mc admin info local

# 測試 Milvus
curl http://worker3:19530/health
```

### 服務連線測試腳本
```bash
#!/bin/bash
# test-services.sh

echo "🔍 測試 Podwise 服務連線..."

# PostgreSQL
echo "🐘 測試 PostgreSQL..."
kubectl exec -n podwise $(kubectl get pods -n podwise -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U bdse37 -d podcast -c "SELECT 1;" 2>/dev/null && echo "✅ PostgreSQL 正常" || echo "❌ PostgreSQL 異常"

# MongoDB
echo "📊 測試 MongoDB..."
kubectl exec -n podwise $(kubectl get pods -n podwise -l app=mongodb -o jsonpath='{.items[0].metadata.name}') -- mongosh --eval "db.runCommand('ping')" 2>/dev/null && echo "✅ MongoDB 正常" || echo "❌ MongoDB 異常"

# MinIO
echo "📦 測試 MinIO..."
kubectl exec -n podwise $(kubectl get pods -n podwise -l app=minio -o jsonpath='{.items[0].metadata.name}') -- mc admin info local 2>/dev/null && echo "✅ MinIO 正常" || echo "❌ MinIO 異常"

# Milvus
echo "🔍 測試 Milvus..."
curl -s http://worker3:19530/health >/dev/null && echo "✅ Milvus 正常" || echo "❌ Milvus 異常"

echo "🎉 服務測試完成！"
```

## 🛠️ 故障排除

### 常見問題

#### 1. Pod 無法啟動
```bash
# 檢查 pod 狀態
kubectl describe pod <pod-name> -n podwise

# 檢查 pod 日誌
kubectl logs <pod-name> -n podwise

# 檢查事件
kubectl get events -n podwise --sort-by='.lastTimestamp'
```

#### 2. 服務無法連線
```bash
# 檢查服務配置
kubectl describe svc <service-name> -n podwise

# 檢查端點
kubectl get endpoints <service-name> -n podwise

# 測試服務連線
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup <service-name>.podwise.svc.cluster.local
```

#### 3. 資料庫連線失敗
```bash
# 檢查資料庫 pod 狀態
kubectl get pods -n podwise | grep -E "(postgres|mongo|minio)"

# 檢查資料庫日誌
kubectl logs <db-pod-name> -n podwise

# 測試資料庫連線
kubectl exec -n podwise <db-pod-name> -- <db-command>
```

### 重新部署服務
```bash
# 重新部署特定服務
kubectl rollout restart deployment <deployment-name> -n podwise

# 檢查部署狀態
kubectl rollout status deployment <deployment-name> -n podwise

# 回滾部署
kubectl rollout undo deployment <deployment-name> -n podwise
```

### 清理資源
```bash
# 刪除特定服務
kubectl delete deployment <deployment-name> -n podwise
kubectl delete service <service-name> -n podwise

# 清理 PVC（小心使用）
kubectl delete pvc <pvc-name> -n podwise

# 清理整個 namespace
kubectl delete namespace podwise
```

## 📝 注意事項

1. **環境變數**: 確保 `.env` 檔案中的服務地址正確
2. **網路連線**: 確保 pod 間可以正常通訊
3. **資源限制**: 注意 CPU 和記憶體使用量
4. **持久化儲存**: 重要資料使用 PVC 持久化
5. **安全配置**: 敏感資訊使用 K8s Secret 管理
6. **監控日誌**: 定期檢查服務日誌和監控指標

## 🔗 相關連結

- [Kubernetes 官方文檔](https://kubernetes.io/docs/)
- [Podwise 專案文檔](../README.md)
- [服務配置詳情](../deploy/k8s/) 