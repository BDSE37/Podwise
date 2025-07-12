# Podwise 用戶偏好收集系統

## 概述

這個系統實現了完整的用戶偏好收集流程，包括：

1. **類別選擇** - 用戶選擇感興趣的內容類別（商業/教育）
2. **節目推薦** - 根據類別從 MinIO 獲取相關音檔並推薦
3. **用戶反饋** - 記錄用戶的播放和喜歡行為
4. **用戶註冊** - 創建新用戶或檢查現有用戶
5. **偏好記錄** - 將用戶選擇的節目保存到 PostgreSQL

## 系統架構

### 後端服務
- `user_preference_service.py` - 主要的 API 服務
- 整合 MinIO 音檔存儲
- 整合 PostgreSQL 資料庫
- 提供 RESTful API 接口

### 前端整合
- 修改 `frontend/home/index.html`
- 實現完整的用戶偏好收集流程
- 保持原有樣式，只修改功能邏輯

## API 端點

### 1. 類別推薦
```
POST /api/category/recommendations
Content-Type: application/json

{
  "category": "business"  // 或 "education"
}
```

**回應：**
```json
{
  "recommendations": [
    {
      "podcast_name": "股癌 Gooaye",
      "episode_title": "投資理財精選",
      "episode_description": "晦澀金融投資知識直白講...",
      "podcast_image": "images/股癌.png",
      "audio_url": "audio/sample1.mp3",
      "episode_id": 1,
      "rss_id": "123"
    }
  ]
}
```

### 2. 用戶反饋
```
POST /api/feedback
Content-Type: application/json

{
  "user_id": "user123",
  "episode_id": 1,
  "podcast_name": "股癌 Gooaye",
  "episode_title": "投資理財精選",
  "rss_id": "123",
  "action": "like",  // "like", "unlike", "play"
  "category": "business"
}
```

### 3. 用戶註冊
```
POST /api/user/register
Content-Type: application/json

{
  "user_id": "user123",
  "category": "business",
  "selected_episodes": [
    {
      "episode_id": 1,
      "podcast_name": "股癌 Gooaye",
      "episode_title": "投資理財精選",
      "rss_id": "123"
    }
  ]
}
```

### 4. 用戶檢查
```
GET /api/user/check/{user_id}
```

**回應：**
```json
{
  "exists": true
}
```

## 資料庫結構

### user_feedback 表
```sql
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    episode_id INTEGER,
    podcast_name VARCHAR(255),
    episode_title VARCHAR(500),
    rss_id VARCHAR(255),
    action VARCHAR(50),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_preferences 表
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 配置

### 環境變數
```bash
# PostgreSQL
POSTGRES_HOST=postgres.podwise.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DB=podcast
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# MinIO
MINIO_ENDPOINT=minio.podwise.svc.cluster.local
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_SECURE=false

# 服務配置
API_HOST=0.0.0.0
API_PORT=8000
```

## 使用流程

### 1. 啟動服務
```bash
cd backend/api
python user_preference_service.py
```

### 2. 測試功能
```bash
python test_user_preference.py
```

### 3. 前端整合
1. 確保前端可以訪問後端 API
2. 修改 API 端點地址（如果需要）
3. 測試完整的用戶偏好收集流程

## 功能特點

### 1. 智能推薦
- 根據用戶選擇的類別從 MinIO 獲取相關音檔
- 隨機選擇 4 個推薦節目
- 支援商業和教育兩個主要類別

### 2. 用戶體驗
- 保持原有前端樣式
- 流暢的步驟切換
- 即時反饋和狀態更新

### 3. 資料完整性
- 完整的用戶行為記錄
- 支援多筆節目選擇
- 自動處理新用戶和現有用戶

### 4. 錯誤處理
- API 失敗時的預設資料
- 優雅的錯誤提示
- 完整的日誌記錄

## 注意事項

1. **MinIO 配置** - 確保 MinIO 中有對應的 bucket 和音檔
2. **資料庫連接** - 確保 PostgreSQL 服務正常運行
3. **CORS 設置** - 如果需要跨域訪問，請配置 CORS
4. **音檔路徑** - 確保音檔 URL 可以正確訪問

## 故障排除

### 常見問題

1. **API 無法連接**
   - 檢查服務是否正常啟動
   - 確認端口是否被佔用

2. **資料庫連接失敗**
   - 檢查 PostgreSQL 服務狀態
   - 確認連接參數是否正確

3. **MinIO 訪問失敗**
   - 檢查 MinIO 服務狀態
   - 確認 bucket 是否存在

4. **前端無法獲取推薦**
   - 檢查 API 端點地址
   - 確認 CORS 設置

## 未來改進

1. **更多類別支援** - 擴展到更多內容類別
2. **個性化推薦** - 基於用戶歷史行為的智能推薦
3. **音檔預處理** - 自動生成音檔元資料
4. **用戶分析** - 提供用戶行為分析報告
5. **A/B 測試** - 支援不同的推薦算法測試 