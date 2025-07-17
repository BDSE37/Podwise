# Podwise 後端架構文檔

## 🏗️ 架構概述

Podwise 後端採用模組化設計，遵循 OOP 原則和 Google Clean Code 規範，提供統一的服務管理介面。

## 📁 目錄結構

```
backend/
├── core/                          # 核心服務模組
│   ├── __init__.py
│   └── podwise_service_manager.py # 統一服務管理器
├── config/                        # 配置管理
│   ├── db_config.py              # 資料庫配置
│   └── init-scripts/             # 初始化腳本
├── unified_api_gateway.py        # 統一 API Gateway
├── main.py                       # 服務啟動器
├── requirements_unified_api.txt  # 依賴套件
└── ARCHITECTURE.md               # 架構文檔
```

## 🔧 核心模組

### 1. PodwiseServiceManager (core/podwise_service_manager.py)

**功能**: 統一管理所有 Podwise 核心功能

**主要方法**:
- `get_category_tags(category)`: 獲取類別標籤
- `get_episodes_by_tag(category, tag, limit)`: 根據標籤獲取節目
- `generate_user_id()`: 生成用戶 ID
- `check_user_exists(user_code)`: 檢查用戶存在性
- `save_user_preferences(user_id, main_category, sub_category)`: 保存用戶偏好
- `record_user_feedback(user_id, episode_id, episode_title, like_count, preview_play_count)`: 記錄用戶反饋
- `get_random_audio(category)`: 獲取隨機音檔

**設計原則**:
- 單一職責原則：專注於 Podwise 核心業務邏輯
- 依賴反轉：透過介面與外部服務互動
- 錯誤處理：統一的異常處理機制

### 2. 統一 API Gateway (unified_api_gateway.py)

**功能**: 整合所有前端頁面和後端服務的統一入口

**主要端點**:
- `GET /`: 首頁
- `GET /podri.html`: 聊天頁面
- `GET /api/category-tags/{category}`: 獲取類別標籤
- `GET /api/one-minutes-episodes`: 獲取節目推薦
- `POST /api/generate-podwise-id`: 生成用戶 ID
- `POST /api/feedback`: 記錄反饋
- `POST /api/random-audio`: 獲取隨機音檔

**設計特色**:
- 靜態檔案服務：自動處理前端資源
- 音檔代理：從 MinIO 獲取真實音檔
- 統一錯誤處理：標準化的錯誤回應格式

### 3. 服務啟動器 (main.py)

**功能**: 提供統一的服務管理介面

**主要命令**:
- `python main.py`: 啟動統一 API Gateway
- `python main.py list`: 列出所有服務
- `python main.py start <service>`: 啟動指定服務
- `python main.py status <service>`: 檢查服務狀態

## 🗄️ 資料來源

### MinIO 儲存結構

```
business-one-min-audio/
├── RSS_{podcast_id}_{episode_title}.mp3
└── ...

education-one-min-audio/
├── RSS_{podcast_id}_{episode_title}.mp3
└── ...

podcast-images/
├── RSS_{podcast_id}_300.jpg
├── RSS_{podcast_id}_64.jpg
└── RSS_{podcast_id}_XX.jpg
```

### PostgreSQL 資料庫結構

**users 表**:
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_identifier VARCHAR(64) UNIQUE NOT NULL,
    user_type VARCHAR(32) NOT NULL DEFAULT 'guest',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**user_preferences 表**:
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

**user_feedback 表**:
```sql
CREATE TABLE user_feedback (
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    like_count INTEGER DEFAULT 0,
    preview_play_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, episode_id)
);
```

## 🔄 工作流程

### 1. 用戶註冊流程
1. 用戶選擇類別（商業/教育）
2. 系統隨機顯示 4 個標籤
3. 用戶選擇標籤，系統顯示 3 個相關節目
4. 用戶輸入或生成 Podwise ID
5. 系統記錄用戶偏好和反饋

### 2. 節目推薦流程
1. 根據類別從 MinIO 獲取對應 bucket 的音檔
2. 從 PostgreSQL 查詢節目資訊和標籤
3. 根據標籤匹配節目，不足時補充隨機節目
4. 為每個節目生成 MinIO 預簽名 URL
5. 返回完整的節目資訊

### 3. 音檔播放流程
1. 前端請求音檔 URL
2. API Gateway 檢查本地檔案
3. 如果是文字檔案，從 MinIO 獲取真實音檔
4. 生成預簽名 URL 並重定向
5. 前端播放音檔

## 🛡️ 錯誤處理

### 統一錯誤回應格式
```json
{
    "success": false,
    "error": "錯誤描述",
    "message": "用戶友好訊息"
}
```

### 常見錯誤類型
- 資料庫連接失敗
- MinIO 服務不可用
- 檔案不存在
- 參數驗證失敗

## 📊 監控與日誌

### 日誌配置
- 統一使用 Python logging 模組
- 結構化日誌格式
- 不同級別的日誌記錄

### 健康檢查
- `GET /health`: API Gateway 健康檢查
- `GET /api/v1/services`: 所有微服務狀態

## 🚀 部署指南

### 1. 環境準備
```bash
# 安裝依賴
pip install -r requirements_unified_api.txt

# 設定環境變數
cp env.example .env
# 編輯 .env 檔案
```

### 2. 啟動服務
```bash
# 啟動統一 API Gateway
python main.py

# 或使用啟動腳本
./start_unified_api.sh
```

### 3. 測試服務
```bash
# 快速測試
python quick_test.py

# 詳細測試
python simple_test_api.py
```

## 🔧 擴展指南

### 新增服務模組
1. 在 `core/` 目錄下建立新的服務類別
2. 在 `PodwiseServiceManager` 中整合新服務
3. 在 `unified_api_gateway.py` 中新增 API 端點
4. 更新 `main.py` 中的服務配置

### 新增資料來源
1. 更新 `config/db_config.py` 中的配置
2. 在 `PodwiseServiceManager` 中新增連接方法
3. 更新相關的業務邏輯方法

## 📝 最佳實踐

### 1. 程式碼風格
- 遵循 PEP 8 規範
- 使用類型提示
- 完整的文檔字串
- 清晰的變數命名

### 2. 錯誤處理
- 使用 try-except 包裝所有外部調用
- 記錄詳細的錯誤資訊
- 提供用戶友好的錯誤訊息

### 3. 效能優化
- 使用連接池管理資料庫連接
- 快取常用的查詢結果
- 非同步處理 I/O 操作

### 4. 安全性
- 參數驗證和清理
- 安全的資料庫查詢
- 適當的權限控制

## 🔄 版本控制

### 版本號格式
- 主版本號.次版本號.修訂號
- 例如：1.0.0

### 變更記錄
- 記錄所有重要的功能變更
- 包含破壞性變更的說明
- 提供升級指南

## 📞 支援與維護

### 問題回報
- 使用 GitHub Issues
- 提供詳細的錯誤資訊
- 包含重現步驟

### 維護計劃
- 定期更新依賴套件
- 監控系統效能
- 備份重要資料 