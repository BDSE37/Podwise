# Podwise 四步驟功能實現指南

## 概述

本指南詳細說明了 Podwise 系統中四步驟功能的實現，包括前端頁面、後端 API 和資料庫整合。

## 功能流程

### Step 1: 用戶選擇類別
- 用戶選擇「商業」或「教育」類別
- 前端：`frontend/home/index.html`
- 後端：`/api/category-tags` 端點

### Step 2: 獲取標籤
- 根據選擇的類別，從 MinIO bucket 隨機獲取 4 個不重複標籤
- 商業類別：`business-one-min-audio` bucket
- 教育類別：`education-one-min-audio` bucket
- 後端：`/api/category-tags` 端點

### Step 3: 節目推薦
- 根據用戶選擇的標籤，顯示三個相關節目
- 如果沒有相關標籤的節目，隨機補足三個節目
- 節目資料來源：
  - 音檔：MinIO bucket（格式：`Spotify_RSS_{rss_id}_{episode_title}.mp3`）
  - 圖片：`podcast-images` bucket（格式：`RSS_{podcast_id}_300.jpg`）
  - 節目標題：PostgreSQL 資料庫
- 用戶可點選 heart_like 按鈕表示喜歡
- 後端：`/api/one-minutes-episodes` 端點

### Step 4: 用戶註冊與偏好儲存
- 用戶輸入 Podwise ID 或產生新的 Podwise ID
- 系統將用戶行為記錄到 PostgreSQL 的 `user_feedback` 資料表
- 如果用戶 ID 不存在，以訪客模式登入
- 用戶 ID 用於後續的精準推薦
- 後端端點：
  - `/api/generate-podwise-id`：生成新 ID
  - `/api/user/check/{user_code}`：檢查用戶存在
  - `/api/user/preferences`：儲存用戶偏好
  - `/api/feedback`：記錄反饋

## 技術架構

### 後端架構（OOP 設計）

#### 1. 用戶偏好管理器
- 檔案：`backend/user_management/main.py`
- 類別：`UserPreferenceManager`
- 功能：統一管理所有用戶相關功能

#### 2. 用戶服務
- 檔案：`backend/user_management/user_service.py`
- 類別：`UserPreferenceService`
- 功能：處理資料庫操作和用戶管理

#### 3. API 端點
- 檔案：`backend/api/app.py`
- 整合所有四步驟相關的 API 端點

#### 4. MinIO 工具
- 檔案：`backend/utils/minio_milvus_utils.py`
- 提供 MinIO 客戶端和檔案操作功能

### 前端架構

#### 1. 主要頁面
- 檔案：`frontend/home/index.html`
- 實現四步驟的用戶介面

#### 2. JavaScript 功能
- Step 1：類別選擇
- Step 2：標籤獲取和選擇
- Step 3：節目推薦和播放
- Step 4：用戶註冊和偏好儲存

## API 端點詳解

### 1. 獲取類別標籤
```http
GET /api/category-tags?category={category}
```

**參數：**
- `category`：類別名稱（business 或 education）

**回應：**
```json
{
  "success": true,
  "tags": ["投資理財", "股票分析", "經濟分析", "財務規劃"]
}
```

### 2. 獲取節目推薦
```http
GET /api/one-minutes-episodes?category={category}&tag={tag}
```

**參數：**
- `category`：類別名稱
- `tag`：選擇的標籤

**回應：**
```json
{
  "success": true,
  "episodes": [
    {
      "podcast_id": "123",
      "podcast_name": "股癌 Gooaye",
      "episode_title": "投資理財精選",
      "audio_url": "http://192.168.32.66:30090/business-one-min-audio/Spotify_RSS_123_投資理財精選.mp3",
      "image_url": "http://192.168.32.66:30090/podcast-images/RSS_123_300.jpg",
      "tags": ["投資理財", "股票分析", "經濟分析", "財務規劃"],
      "rss_id": "123"
    }
  ]
}
```

### 3. 生成 Podwise ID
```http
POST /api/generate-podwise-id
```

**回應：**
```json
{
  "success": true,
  "podwise_id": "Podwise0001",
  "user_id": 1,
  "message": "Podwise ID 生成成功"
}
```

### 4. 檢查用戶存在
```http
GET /api/user/check/{user_code}
```

**回應：**
```json
{
  "success": true,
  "exists": true
}
```

### 5. 儲存用戶偏好
```http
POST /api/user/preferences
```

**請求體：**
```json
{
  "user_code": "Podwise0001",
  "main_category": "business",
  "selected_tag": "投資理財",
  "liked_episodes": [
    {
      "episode_id": 4,
      "podcast_name": "財經一路發",
      "episode_title": "財富生活活化大腦與強健身體的體智能鍛練",
      "rss_id": "RSS_1531106786"
    }
  ]
}
```

### 6. 記錄反饋
```http
POST /api/feedback
```

**請求體：**
```json
{
  "user_code": "Podwise0001",
  "episode_id": 4,
  "podcast_name": "財經一路發",
  "episode_title": "財富生活活化大腦與強健身體的體智能鍛練",
  "rss_id": "RSS_1531106786",
  "action": "like",
  "category": "business"
}
```

### 7. 獲取音檔 URL
```http
POST /api/audio/presigned-url
```

**請求體：**
```json
{
  "rss_id": "RSS_1531106786",
  "episode_title": "財富生活活化大腦與強健身體的體智能鍛練",
  "category": "business"
}
```

**回應：**
```json
{
  "success": true,
  "audio_url": "http://192.168.32.66:30090/business-one-min-audio/Spotify_RSS_1531106786_財富生活活化大腦與強健身體的體智能鍛練.mp3",
  "bucket": "business-one-min-audio",
  "object_key": "Spotify_RSS_1531106786_財富生活活化大腦與強健身體的體智能鍛練.mp3"
}
```

## 資料庫結構

### 用戶表 (users)
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_code VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 用戶偏好表 (user_preferences)
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    category VARCHAR(50) NOT NULL,
    preference_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category)
);
```

### 用戶反饋表 (user_feedback)
```sql
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    episode_id INTEGER NOT NULL,
    like_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, episode_id)
);
```

## MinIO 儲存結構

### Bucket 組織
```
business-one-min-audio/
├── Spotify_RSS_123_投資理財精選.mp3
├── Spotify_RSS_456_AI技術趨勢.mp3
└── ...

education-one-min-audio/
├── Spotify_RSS_101_學習方法論.mp3
├── Spotify_RSS_102_未來教育趨勢.mp3
└── ...

podcast-images/
├── RSS_123_300.jpg
├── RSS_456_300.jpg
└── ...
```

### 檔案命名規則
- 音檔：`Spotify_RSS_{rss_id}_{episode_title}.mp3`
- 圖片：`RSS_{podcast_id}_{size}.jpg`

## 部署和測試

### 1. 啟動後端服務
```bash
cd backend/api
python app.py
```

### 2. 測試 API 端點
```bash
cd backend
python test_api_endpoints.py
```

### 3. 訪問前端頁面
```
http://localhost:8080/home/index.html
```

## 錯誤處理

### 常見問題
1. **MinIO 連接失敗**：檢查 MinIO 服務狀態和配置
2. **資料庫連接失敗**：檢查 PostgreSQL 服務狀態和配置
3. **音檔播放失敗**：檢查音檔是否存在於 MinIO bucket
4. **圖片載入失敗**：檢查圖片是否存在於 podcast-images bucket

### 日誌記錄
- 所有 API 操作都有詳細的日誌記錄
- 錯誤信息會記錄到後端日誌中
- 前端控制台會顯示詳細的錯誤信息

## 擴展功能

### 1. 推薦算法優化
- 基於用戶偏好的協同過濾
- 內容基於推薦
- 混合推薦策略

### 2. 用戶體驗改進
- 音檔預載入
- 圖片懶載入
- 響應式設計優化

### 3. 數據分析
- 用戶行為分析
- 節目熱度統計
- 推薦效果評估

## 維護和監控

### 1. 健康檢查
- API 端點健康狀態監控
- 資料庫連接狀態檢查
- MinIO 服務可用性檢查

### 2. 性能優化
- API 回應時間監控
- 資料庫查詢優化
- 快取策略實施

### 3. 安全措施
- API 認證和授權
- 資料加密
- 輸入驗證和清理 