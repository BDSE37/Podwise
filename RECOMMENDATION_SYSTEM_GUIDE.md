# Podwise 推薦系統完整指南

## 🎯 系統概述

Podwise 推薦系統是一個完整的個人化音檔推薦平台，整合了 MinIO 音檔儲存、PostgreSQL 資料庫和用戶反饋機制。

### 核心功能
1. **類別選擇**：用戶選擇 business（商業）或 education（教育）類別
2. **智能推薦**：根據類別從 MinIO one_minutes_mp3 搜尋相關音檔
3. **資訊整合**：結合 PostgreSQL 中的節目和集數資訊
4. **用戶反饋**：記錄 like/unlike 操作到 user_feedback 表
5. **音檔播放**：通過預簽名 URL 直接播放音檔

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (React)   │    │  推薦服務 API   │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ - 類別選擇      │◄──►│ - 推薦邏輯      │◄──►│ - podcasts      │
│ - 推薦顯示      │    │ - 用戶反饋      │    │ - episodes      │
│ - 用戶交互      │    │ - 音檔管理      │    │ - user_feedback │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     MinIO       │
                       │                 │
                       │ - business_     │
                       │   one_minutes   │
                       │ - education_    │
                       │   one_minutes   │
                       └─────────────────┘
```

## 📋 功能流程

### 1. 用戶選擇類別
```
用戶選擇類別 (財經/職業/房地產/行銷 → business)
                    ↓
前端調用 /api/recommendations
                    ↓
推薦服務從 MinIO 搜尋音檔
                    ↓
結合 PostgreSQL 節目資訊
                    ↓
返回完整推薦列表
```

### 2. 推薦顯示
```
推薦服務返回：
- 節目名稱 (podcast_name)
- 集數標題 (episode_title)
- 節目描述 (episode_description)
- 節目圖片 (podcast_image)
- 音檔 URL (audio_url)
- 用戶反饋狀態 (user_feedback)
```

### 3. 用戶反饋
```
用戶點擊 like/unlike
                    ↓
前端調用 /api/feedback
                    ↓
記錄到 user_feedback 表
                    ↓
更新用戶偏好分析
```

## 🚀 部署指南

### 1. 環境準備
```bash
# 確保 K8s 集群運行
kubectl cluster-info

# 確保 podwise namespace 存在
kubectl get namespace podwise
```

### 2. 部署推薦服務
```bash
# 進入推薦服務目錄
cd deploy/k8s/recommendation-service/

# 執行部署腳本
./deploy.sh
```

### 3. 驗證部署
```bash
# 檢查 Pod 狀態
kubectl get pods -n podwise -l app=recommendation-service

# 檢查服務狀態
kubectl get svc -n podwise -l app=recommendation-service

# 測試健康檢查
kubectl port-forward svc/recommendation-service 8005:8005 -n podwise &
curl http://localhost:8005/health
```

## 🔧 API 文檔

### 1. 健康檢查
```http
GET /health
```
**回應：**
```json
{
  "status": "healthy",
  "service": "recommendation"
}
```

### 2. 獲取推薦
```http
POST /recommendations
Content-Type: application/json

{
  "category": "business",
  "user_id": "user123",
  "limit": 3
}
```
**回應：**
```json
{
  "recommendations": [
    {
      "file_name": "RSS_123_podcast_456_title.mp3",
      "audio_url": "https://minio.example.com/presigned-url",
      "podcast_name": "股癌 Gooaye",
      "episode_title": "投資理財精選",
      "episode_description": "晦澀金融投資知識直白講...",
      "podcast_image": "https://example.com/image.png",
      "category": "business",
      "episode_id": 123,
      "user_feedback": {
        "liked": false,
        "played": false,
        "rating": null
      }
    }
  ],
  "category": "business",
  "total_count": 1,
  "user_id": "user123"
}
```

### 3. 記錄反饋
```http
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
**回應：**
```json
{
  "success": true,
  "message": "成功記錄 like 操作",
  "feedback_id": "user123_123"
}
```

### 4. 獲取用戶偏好
```http
GET /user/preferences/{user_id}
```
**回應：**
```json
{
  "user_id": "user123",
  "preferences": {
    "business": 0.8,
    "education": 0.6
  }
}
```

### 5. 獲取音檔 URL
```http
GET /minio/audio/{bucket_name}/{file_name}
```
**回應：**
```json
{
  "audio_url": "https://minio.example.com/presigned-url",
  "bucket_name": "business_one_minutes",
  "file_name": "RSS_123_podcast_456_title.mp3"
}
```

## 📊 資料庫結構

### 1. podcasts 表
```sql
CREATE TABLE podcasts (
    podcast_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    rss_link VARCHAR(512) UNIQUE,
    images_640 VARCHAR(512),
    images_300 VARCHAR(512),
    images_64 VARCHAR(512),
    languages VARCHAR(64),
    category VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. episodes 表
```sql
CREATE TABLE episodes (
    episode_id SERIAL PRIMARY KEY,
    podcast_id INTEGER NOT NULL,
    episode_title VARCHAR(255) NOT NULL,
    published_date DATE,
    audio_url VARCHAR(512),
    duration INTEGER,
    description TEXT,
    languages VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(podcast_id)
);
```

### 3. user_feedback 表
```sql
CREATE TABLE user_feedback (
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    rating INTEGER,
    bookmark BOOLEAN,
    preview_played BOOLEAN,
    preview_listen_time INTEGER,
    preview_played_at TIMESTAMP,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    preview_play_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, episode_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
);
```

## 🗂️ MinIO 結構

### Bucket 組織
```
business_one_minutes/
├── RSS_262026947_podcast_1304_Millennials and business.mp3
├── RSS_1567737523_podcast_1304_一天10分鐘 商務英語通.mp3
└── ...

education_one_minutes/
├── RSS_789_podcast_101_科技趨勢分享.mp3
├── RSS_456_podcast_202_學習方法論.mp3
└── ...
```

### 檔案命名規則
- **RSS 格式**：`RSS_{rss_id}_podcast_{podcast_id}_{episode_title}.mp3`
- **簡單格式**：`{category}_{episode_num}.mp3`

## 🧪 測試指南

### 1. 運行測試腳本
```bash
# 進入測試目錄
cd backend/api/

# 運行測試
python test_recommendation_service.py
```

### 2. 手動測試
```bash
# 啟動端口轉發
kubectl port-forward svc/recommendation-service 8005:8005 -n podwise &

# 測試健康檢查
curl http://localhost:8005/health

# 測試獲取推薦
curl -X POST http://localhost:8005/recommendations \
  -H "Content-Type: application/json" \
  -d '{"category": "business", "user_id": "test_user", "limit": 3}'

# 測試記錄反饋
curl -X POST http://localhost:8005/feedback \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "episode_id": 1, "action": "like", "category": "business", "file_name": "test.mp3", "bucket_category": "business"}'
```

## 🔍 故障排除

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

### 4. 前端無法連接
```bash
# 檢查 Nginx 配置
kubectl get configmap nginx-config -n podwise -o yaml

# 檢查前端服務
kubectl get svc -n podwise | grep frontend

# 測試前端 API
curl http://localhost:8081/api/recommendations
```

## 📈 監控與日誌

### 1. 日誌查看
```bash
# 實時查看日誌
kubectl logs -f deployment/recommendation-service -n podwise

# 查看特定時間的日誌
kubectl logs deployment/recommendation-service -n podwise --since=1h

# 查看錯誤日誌
kubectl logs deployment/recommendation-service -n podwise | grep ERROR
```

### 2. 性能監控
```bash
# 檢查資源使用情況
kubectl top pods -n podwise -l app=recommendation-service

# 檢查服務端點
kubectl get endpoints recommendation-service -n podwise

# 檢查 Pod 詳細信息
kubectl describe pod -l app=recommendation-service -n podwise
```

## 🔄 更新與維護

### 1. 更新服務
```bash
# 更新鏡像
kubectl set image deployment/recommendation-service recommendation-service=python:3.9-slim -n podwise

# 滾動更新
kubectl rollout restart deployment/recommendation-service -n podwise

# 檢查更新狀態
kubectl rollout status deployment/recommendation-service -n podwise
```

### 2. 擴展服務
```bash
# 水平擴展
kubectl scale deployment recommendation-service --replicas=3 -n podwise

# 檢查擴展狀態
kubectl get pods -n podwise -l app=recommendation-service
```

### 3. 備份與恢復
```bash
# 備份配置
kubectl get configmap recommendation-service-code -n podwise -o yaml > backup-config.yaml

# 備份部署配置
kubectl get deployment recommendation-service -n podwise -o yaml > backup-deployment.yaml

# 恢復配置
kubectl apply -f backup-config.yaml
kubectl apply -f backup-deployment.yaml
```

## 🎯 使用案例

### 案例 1：用戶選擇商業類別
1. 用戶在前端選擇「財經」類別
2. 前端調用 `/api/recommendations` 獲取推薦
3. 推薦服務從 `business_one_minutes` bucket 搜尋音檔
4. 結合 PostgreSQL 中的節目資訊
5. 返回包含節目名稱、描述、圖片的推薦列表
6. 用戶可以播放音檔和記錄反饋

### 案例 2：用戶記錄反饋
1. 用戶點擊 like 按鈕
2. 前端調用 `/api/feedback` 記錄反饋
3. 推薦服務更新 `user_feedback` 表
4. 系統記錄用戶偏好用於後續推薦

### 案例 3：音檔播放
1. 用戶點擊播放按鈕
2. 前端獲取 MinIO 預簽名 URL
3. 直接播放音檔
4. 記錄播放行為到資料庫

## 🚀 未來擴展

### 1. 智能推薦算法
- 基於協同過濾的推薦
- 內容基於推薦
- 深度學習推薦模型

### 2. 用戶行為分析
- 播放時長分析
- 跳過行為分析
- 用戶畫像建立

### 3. 個性化功能
- 自定義播放列表
- 推薦理由說明
- 社交分享功能

### 4. 性能優化
- Redis 快取層
- CDN 音檔分發
- 微服務架構

## 📞 支援與聯繫

如有問題或建議，請聯繫：
- 技術支援：tech@podwise.com
- 功能建議：feature@podwise.com
- 故障報告：bug@podwise.com

---

**版本**：1.0.0  
**更新日期**：2025-01-11  
**維護者**：Podwise 開發團隊 