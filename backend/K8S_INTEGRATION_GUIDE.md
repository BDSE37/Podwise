# Podwise 後端 K8s 整合指南

## 📋 概述

本指南說明如何將 Podwise 後端的所有服務整合到 Kubernetes (K8s) 環境中，確保每個服務都能連接到 K8s 節點中的資料庫服務。

## 🏗️ 架構設計

### 服務架構
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   K8s Services  │
│   (Local)       │◄──►│   (Port 8000)   │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Backend Pods  │
                    │                 │
                    │ • RAG Pipeline  │
                    │ • ML Pipeline   │
                    │ • TTS Service   │
                    │ • STT Service   │
                    │ • LLM Service   │
                    └─────────────────┘
```

### 資料庫連接
- **PostgreSQL**: `postgres.podwise.svc.cluster.local:5432`
- **MongoDB**: `mongodb.podwise.svc.cluster.local:27017`
- **Milvus**: `worker3:19530` (Docker container)
- **MinIO**: `minio.podwise.svc.cluster.local:9000`

## 🔧 配置更新

### 1. 環境變數配置

所有服務統一使用 `.env` 檔案管理環境變數：

```bash
# 資料庫配置 (K8s 服務)
POSTGRES_HOST=postgres.podwise.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DB=podcast
POSTGRES_USER=bdse37
POSTGRES_PASSWORD=111111
DATABASE_URL=postgresql://bdse37:111111@postgres.podwise.svc.cluster.local:5432/podcast

MONGO_HOST=mongodb.podwise.svc.cluster.local
MONGO_PORT=27017
MONGO_DB=podwise
MONGO_USER=bdse37
MONGO_PASSWORD=111111
MONGO_URI=mongodb://bdse37:111111@mongodb.podwise.svc.cluster.local:27017/podwise

# 服務端口配置
API_PORT=8000
RAG_PORT=8001
ML_PORT=8002
TTS_PORT=8003
STT_PORT=8004
LLM_PORT=8005
```

### 2. 服務配置更新

#### RAG Pipeline (`rag_pipeline/config/integrated_config.py`)
- 更新資料庫連接字串指向 K8s 服務
- 支援環境變數覆蓋

#### ML Pipeline (`ml_pipeline/config/recommender_config.py`)
- 添加資料庫配置區塊
- 支援環境變數讀取

#### Vector Pipeline (`vector_pipeline/core/mongo_processor.py`)
- 支援環境變數配置 MongoDB 連接
- 整合 data_cleaning 模組

#### Data Cleaning (`data_cleaning/config/config.py`)
- 更新 PostgreSQL 連接指向 K8s 服務
- 支援環境變數配置

#### API Gateway (`api/app.py`)
- 更新服務 URL 配置
- 統一使用環境變數管理端口

## 🚀 部署流程

### 1. 環境設置

```bash
# 進入 backend 目錄
cd backend

# 設置 K8s 環境
./setup-k8s-env.sh
```

### 2. 連接測試

```bash
# 測試 K8s 服務連接
./test-k8s-connection.sh
```

### 3. 本地服務啟動

```bash
# 啟動所有後端服務
./start-all-services.sh
```

### 4. K8s 部署 (可選)

```bash
# 部署到 K8s 環境
./deploy-backend-to-k8s.sh
```

## 📊 服務端口分配

| 服務 | 端口 | 說明 |
|------|------|------|
| API Gateway | 8000 | 統一 API 入口 |
| RAG Pipeline | 8001 | 檢索增強生成 |
| ML Pipeline | 8002 | 機器學習推薦 |
| TTS Service | 8003 | 文字轉語音 |
| STT Service | 8004 | 語音轉文字 |
| LLM Service | 8005 | 大語言模型 |

## 🔍 健康檢查

### 服務健康檢查端點

```bash
# API Gateway
curl http://localhost:8000/health

# RAG Pipeline
curl http://localhost:8001/health

# ML Pipeline
curl http://localhost:8002/health

# TTS Service
curl http://localhost:8003/health

# STT Service
curl http://localhost:8004/health

# LLM Service
curl http://localhost:8005/health
```

### 資料庫連接檢查

```bash
# PostgreSQL
nc -z postgres.podwise.svc.cluster.local 5432

# MongoDB
nc -z mongodb.podwise.svc.cluster.local 27017

# Milvus
nc -z worker3 19530

# MinIO
nc -z minio.podwise.svc.cluster.local 9000
```

## 🛠️ 故障排除

### 常見問題

#### 1. 資料庫連接失敗
```bash
# 檢查 K8s 服務狀態
kubectl get services -n podwise

# 檢查服務端點
kubectl get endpoints -n podwise

# 檢查網路連接
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup postgres.podwise.svc.cluster.local
```

#### 2. 服務啟動失敗
```bash
# 檢查環境變數
cat .env

# 檢查端口佔用
netstat -tlnp | grep :800

# 檢查服務日誌
tail -f logs/service.log
```

#### 3. 配置載入失敗
```bash
# 檢查配置文件
ls -la config/

# 檢查權限
chmod 644 .env

# 重新載入配置
source .env
```

## 📝 配置範例

### 完整的 .env 配置

```bash
# =============================================================================
# Podwise 後端環境配置
# 所有服務統一使用 K8s 資料庫服務
# =============================================================================

# 資料庫配置 (K8s 服務)
POSTGRES_HOST=postgres.podwise.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DB=podcast
POSTGRES_USER=bdse37
POSTGRES_PASSWORD=111111
DATABASE_URL=postgresql://bdse37:111111@postgres.podwise.svc.cluster.local:5432/podcast

MONGO_HOST=mongodb.podwise.svc.cluster.local
MONGO_PORT=27017
MONGO_DB=podwise
MONGO_USER=bdse37
MONGO_PASSWORD=111111
MONGO_URI=mongodb://bdse37:111111@mongodb.podwise.svc.cluster.local:27017/podwise

MILVUS_HOST=worker3
MILVUS_PORT=19530
MILVUS_COLLECTION=podwise_vectors

MINIO_HOST=minio.podwise.svc.cluster.local
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# 服務配置 (本地 pod)
API_HOST=0.0.0.0
API_PORT=8000
RAG_URL=http://localhost:8001
RAG_HOST=localhost
RAG_PORT=8001
ML_URL=http://localhost:8002
ML_HOST=localhost
ML_PORT=8002
TTS_URL=http://localhost:8003
TTS_HOST=localhost
TTS_PORT=8003
STT_URL=http://localhost:8004
STT_HOST=localhost
STT_PORT=8004
LLM_URL=http://localhost:8005
LLM_HOST=localhost
LLM_PORT=8005

# AI/ML 模型配置
OPENAI_API_KEY=your_openai_api_key_here
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=float32

# 系統配置
LOG_LEVEL=INFO
DEBUG_MODE=false
APP_NAME=podwise-backend
APP_VERSION=1.0.0
ENVIRONMENT=production
```

## 🔐 安全注意事項

### 1. 密碼管理
- 使用 K8s Secret 管理敏感資訊
- 避免在程式碼中硬編碼密碼
- 定期更換資料庫密碼

### 2. 網路安全
- 限制服務間通信
- 使用 Service Mesh 進行流量管理
- 實施網路策略 (NetworkPolicy)

### 3. 存取控制
- 使用 RBAC 控制 K8s 資源存取
- 實施 API 認證機制
- 監控異常存取行為

## 📈 監控與日誌

### 1. 服務監控
```bash
# 檢查服務狀態
kubectl get pods -n podwise

# 查看服務日誌
kubectl logs -f deployment/podwise-api-gateway -n podwise

# 監控資源使用
kubectl top pods -n podwise
```

### 2. 日誌收集
- 使用 Fluentd 收集容器日誌
- 整合 ELK Stack 進行日誌分析
- 設置日誌輪轉和清理策略

### 3. 效能監控
- 使用 Prometheus 收集指標
- 設置 Grafana 儀表板
- 監控服務響應時間和錯誤率

## 🚀 後續優化

### 1. 自動化部署
- 設置 CI/CD 管道
- 自動化測試和部署
- 藍綠部署策略

### 2. 擴展性優化
- 水平自動擴展 (HPA)
- 資源限制和請求優化
- 負載均衡配置

### 3. 高可用性
- 多副本部署
- 故障轉移機制
- 備份和恢復策略

## 📞 支援

如有問題，請參考：
1. 服務日誌檔案
2. K8s 事件日誌
3. 網路連接測試結果
4. 配置檔案驗證

---

**版本**: 1.0.0  
**更新日期**: 2024-12-19  
**維護者**: Podwise Team 