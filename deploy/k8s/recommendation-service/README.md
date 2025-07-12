# Podwise 推薦服務部署指南

## 概述

推薦服務是 Podwise 系統的核心組件，負責：
- 根據用戶選擇的類別從 MinIO 搜尋音檔
- 從 PostgreSQL 獲取節目和集數資訊
- 記錄用戶反饋到 user_feedback 表
- 提供個人化推薦

## 功能特點

### 1. 類別選擇與搜尋
- 支援 business（商業）和 education（教育）類別
- 自動映射中文類別到英文 bucket 名稱
- 從 MinIO one_minutes_mp3 bucket 搜尋音檔

### 2. 節目資訊整合
- 解析 RSS 檔案名稱獲取節目資訊
- 從 PostgreSQL 查詢 podcast 和 episode 詳細資訊
- 提供節目圖片、標題、描述、集數等完整資訊

### 3. 用戶反饋系統
- 記錄用戶 like/unlike 操作
- 追蹤播放行為
- 暫存到 user_feedback 表
- 支援用戶偏好分析

### 4. 音檔播放
- 生成 MinIO 預簽名 URL
- 支援直接播放音檔
- 處理不同格式的檔案名稱

## 部署步驟

### 1. 準備環境
```bash
# 確保 K8s 集群運行
kubectl cluster-info

# 確保 podwise namespace 存在
kubectl get namespace podwise
```

### 2. 部署推薦服務
```bash
# 部署推薦服務
kubectl apply -f deploy/k8s/recommendation-service/

# 檢查部署狀態
kubectl get pods -n podwise -l app=recommendation-service
kubectl get svc -n podwise -l app=recommendation-service
```

### 3. 驗證服務
```bash
# 檢查服務健康狀態
kubectl port-forward svc/recommendation-service 8005:8005 -n podwise

# 測試 API
curl http://localhost:8005/health
```

## API 端點

### 1. 健康檢查
```
GET /health
```

### 2. 獲取推薦
```
POST /recommendations
Content-Type: application/json

{
  "category": "business",
  "user_id": "user123",
  "limit": 3
}
```

### 3. 記錄反饋
```
POST /feedback
Content-Type: application/json

{
  "user_id": "user123",
  "episode_id": 123,
  "action": "like",
  "category": "business",
  "file_name": "RSS_123_podcast_456_title.mp3",
  "bucket_category": "business"
}
```

### 4. 獲取用戶偏好
```
GET /user/preferences/{user_id}
```

### 5. 獲取 MinIO 音檔 URL
```
GET /minio/audio/{bucket_name}/{file_name}
```

## 配置說明

### 環境變數
- `POSTGRES_HOST`: PostgreSQL 服務地址
- `POSTGRES_PORT`: PostgreSQL 端口
- `POSTGRES_DB`: 資料庫名稱
- `POSTGRES_USER`: 資料庫用戶
- `POSTGRES_PASSWORD`: 資料庫密碼
- `MINIO_ENDPOINT`: MinIO 服務地址
- `MINIO_ACCESS_KEY`: MinIO 訪問密鑰
- `MINIO_SECRET_KEY`: MinIO 秘密密鑰

### 資料庫表結構
服務依賴以下 PostgreSQL 表：
- `podcasts`: 節目資訊
- `episodes`: 集數資訊
- `user_feedback`: 用戶反饋

### MinIO Bucket 結構
預期的 bucket 結構：
```
business_one_minutes/
├── RSS_123_podcast_456_title1.mp3
├── RSS_123_podcast_456_title2.mp3
└── ...

education_one_minutes/
├── RSS_789_podcast_101_title1.mp3
├── RSS_789_podcast_101_title2.mp3
└── ...
```

## 故障排除

### 1. 服務無法啟動
```bash
# 檢查 Pod 日誌
kubectl logs -f deployment/recommendation-service -n podwise

# 檢查 Pod 狀態
kubectl describe pod -l app=recommendation-service -n podwise
```

### 2. 資料庫連接失敗
```bash
# 檢查 PostgreSQL 服務
kubectl get svc postgres -n podwise

# 測試資料庫連接
kubectl exec -it deployment/recommendation-service -n podwise -- python -c "
import psycopg2
conn = psycopg2.connect(host='postgres.podwise.svc.cluster.local', port=5432, database='podcast', user='bdse37', password='111111')
print('資料庫連接成功')
"
```

### 3. MinIO 連接失敗
```bash
# 檢查 MinIO 服務
kubectl get svc minio -n podwise

# 測試 MinIO 連接
kubectl exec -it deployment/recommendation-service -n podwise -- python -c "
from minio import Minio
client = Minio('minio.podwise.svc.cluster.local:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
buckets = client.list_buckets()
print('MinIO 連接成功，buckets:', [b.name for b in buckets])
"
```

## 監控與日誌

### 日誌查看
```bash
# 實時查看日誌
kubectl logs -f deployment/recommendation-service -n podwise

# 查看特定時間的日誌
kubectl logs deployment/recommendation-service -n podwise --since=1h
```

### 性能監控
```bash
# 檢查資源使用情況
kubectl top pods -n podwise -l app=recommendation-service

# 檢查服務端點
kubectl get endpoints recommendation-service -n podwise
```

## 擴展與優化

### 1. 水平擴展
```bash
# 擴展到多個副本
kubectl scale deployment recommendation-service --replicas=3 -n podwise
```

### 2. 資源限制調整
編輯 deployment 配置中的 resources 部分：
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### 3. 快取優化
考慮添加 Redis 快取來提升性能：
- 快取推薦結果
- 快取用戶偏好
- 快取 MinIO 預簽名 URL

## 安全考慮

1. **資料庫安全**：使用 Secret 管理資料庫憑證
2. **MinIO 安全**：使用 Secret 管理 MinIO 憑證
3. **API 安全**：考慮添加認證和授權機制
4. **網路安全**：使用 NetworkPolicy 限制網路訪問

## 更新與維護

### 更新服務
```bash
# 更新鏡像
kubectl set image deployment/recommendation-service recommendation-service=python:3.9-slim -n podwise

# 滾動更新
kubectl rollout restart deployment/recommendation-service -n podwise
```

### 備份與恢復
```bash
# 備份配置
kubectl get configmap recommendation-service-code -n podwise -o yaml > backup-config.yaml

# 恢復配置
kubectl apply -f backup-config.yaml
``` 