# PodWise Onboarding 流程實作

## 概述

本實作完成了完整的 PodWise 用戶 onboarding 流程，包含四個步驟：

1. **Step 1**: 類別選擇（商業/教育）
2. **Step 2**: 標籤選擇（2行2列泡泡顯示）
3. **Step 3**: 節目推薦與試聽
4. **Step 4**: 用戶註冊與偏好儲存

## 功能特色

### 🎯 Step 1: 類別選擇
- 用戶點選「商業」或「教育」類別
- 保持原有設計樣式和大小
- 點擊後自動進入 Step 2

### 🏷️ Step 2: 標籤選擇
- 根據選擇的類別從後端動態獲取標籤
- 隨機提取 4 個標籤，以 2行2列 泡泡形式顯示
- 點擊標籤後自動進入 Step 3

### 🎵 Step 3: 節目推薦
- 根據類別和標籤從 MinIO 獲取對應節目
- 顯示三個不同的節目，包含：
  - 節目圖片（從 MinIO podcast-images 獲取）
  - 可播放的音檔（從 MinIO business-one-min-audio/education-one-min-audio）
  - RSS_ID 和 episode_title
  - Like 按鈕
- 用戶必須至少選擇一個節目才能進入下一步

### 👤 Step 4: 用戶註冊
- 支援兩種方式：
  1. **輸入現有 Podwise ID**: 檢查 PostgreSQL 資料庫中是否存在
  2. **創建新 Podwise ID**: 自動生成並在資料庫中創建用戶
- 記錄完整的用戶行為到 PostgreSQL

## 資料庫結構

### user_feedback 表欄位
```sql
CREATE TABLE user_feedback (
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    rating INTEGER,
    bookmark BOOLEAN,
    preview_played BOOLEAN,
    preview_listen_time INTEGER,
    preview_played_at TIMESTAMP,
    like_count INTEGER,
    dislike_count INTEGER,
    preview_play_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (user_id, episode_id)
);
```

### user_preferences 表欄位
```sql
CREATE TABLE user_preferences (
    user_id INTEGER NOT NULL,
    category VARCHAR(64) NOT NULL,
    preference_score DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, category)
);
```

## API 端點

### 1. 類別標籤獲取
```
GET /api/category-tags?category={business|education}
```

### 2. 一分鐘節目獲取
```
GET /api/one-minutes-episodes?category={business|education}&tag={tag}
```

### 3. 用戶檢查
```
GET /api/user/check/{user_code}
```

### 4. 用戶偏好儲存
```
POST /api/user/preferences
```

### 5. 反饋記錄
```
POST /api/feedback
```

### 6. Podwise ID 生成
```
POST /api/generate-podwise-id
```

### 7. 音檔 URL 獲取
```
POST /api/audio/presigned-url
```

## 檔案結構

```
frontend/home/
├── index.html                    # 主要前端檔案（已修改）
├── README_onboarding.md          # 本說明文件
└── images/                       # 圖片資源
    ├── default_podcast.png       # 預設節目圖片
    ├── play_gray.png            # 播放按鈕
    └── stop_gray.png            # 停止按鈕

backend/
├── api/
│   └── app.py                   # API 服務（已新增端點）
├── utils/
│   └── minio_milvus_utils.py    # MinIO 工具函數（新建）
└── test_onboarding.py           # 測試腳本（新建）
```

## 使用流程

### 1. 啟動後端服務
```bash
cd backend/api
python app.py
```

### 2. 啟動前端服務
```bash
cd frontend/home
# 使用任何 HTTP 伺服器，例如 Python 內建伺服器
python -m http.server 8080
```

### 3. 測試 API 端點
```bash
cd backend
python test_onboarding.py
```

### 4. 訪問前端
打開瀏覽器訪問 `http://localhost:8080`

## 技術細節

### 前端實作
- 保持原有 CSS 樣式和設計大小
- 使用 JavaScript 實現步驟切換
- 整合 MinIO 音檔和圖片載入
- 實現音檔播放控制
- 用戶偏好收集和儲存

### 後端實作
- FastAPI 框架提供 RESTful API
- PostgreSQL 資料庫整合
- MinIO 物件存儲整合
- 用戶管理和偏好儲存
- 錯誤處理和日誌記錄

### 資料流程
1. 用戶選擇類別 → 後端獲取標籤
2. 用戶選擇標籤 → 後端獲取節目
3. 用戶試聽和選擇節目 → 前端記錄行為
4. 用戶註冊 → 後端儲存完整偏好

## 注意事項

1. **MinIO 配置**: 確保 MinIO 服務運行且包含必要的 bucket
2. **PostgreSQL 配置**: 確保資料庫連接正常
3. **CORS 設置**: 已配置允許跨域請求
4. **錯誤處理**: 包含完整的錯誤處理和用戶提示
5. **音檔格式**: 支援 MP3 格式的音檔播放

## 測試

運行測試腳本驗證所有功能：
```bash
python test_onboarding.py
```

測試將檢查：
- API 端點可用性
- 資料庫連接
- MinIO 整合
- 用戶註冊流程
- 偏好儲存功能 