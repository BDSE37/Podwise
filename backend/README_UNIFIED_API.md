# Podwise 統一 API Gateway

整合所有 Podwise 功能的統一 FastAPI 反向代理服務。

## 🚀 功能特色

### 1. 頁面服務
- **首頁**: `http://localhost:8008/` - Podwise 首頁
- **Podri 聊天**: `http://localhost:8008/podri.html` - Podri 聊天介面

### 2. 用戶管理 API
- **生成 Podwise ID**: `POST /api/generate-podwise-id`
- **檢查用戶存在性**: `GET /api/user/check/{user_id}`
- **保存用戶偏好**: `POST /api/user/preferences`

### 3. 音檔管理 API
- **獲取隨機音檔**: `POST /api/random-audio`
- **獲取預簽名 URL**: `POST /api/audio/presigned-url`

### 4. 推薦系統 API
- **獲取類別標籤**: `GET /api/category-tags/{category}`
- **獲取節目推薦**: `GET /api/one-minutes-episodes`

### 5. 反饋系統 API
- **記錄用戶反饋**: `POST /api/feedback`

### 6. RAG Pipeline API
- **查詢**: `POST /api/v1/query`

### 7. TTS/STT API
- **語音合成**: `POST /api/v1/tts/synthesize`
- **語音轉文字**: `POST /api/v1/stt/transcribe`

### 8. 服務狀態 API
- **健康檢查**: `GET /health`
- **服務狀態**: `GET /api/v1/services`

## 📦 安裝與設定

### 1. 安裝依賴
```bash
cd backend
pip install -r requirements_unified_api.txt
```

### 2. 環境變數設定
可以通過環境變數設定各服務的 URL：

```bash
export TTS_SERVICE_URL="http://localhost:8001"
export STT_SERVICE_URL="http://localhost:8002"
export RAG_PIPELINE_URL="http://localhost:8003"
export ML_PIPELINE_URL="http://localhost:8004"
export LLM_SERVICE_URL="http://localhost:8005"
```

### 3. 啟動服務
```bash
# 方法 1: 使用啟動腳本
./start_unified_api.sh

# 方法 2: 直接執行
python unified_api_gateway.py
```

## 🧪 測試

### 1. 運行完整測試
```bash
python simple_test_api.py
```

### 2. 查看測試報告
測試完成後會生成 `test_report.json` 檔案，包含詳細的測試結果。

### 3. 手動測試 API
```bash
# 健康檢查
curl http://localhost:8008/health

# 生成 Podwise ID
curl -X POST http://localhost:8008/api/generate-podwise-id

# 獲取類別標籤
curl http://localhost:8008/api/category-tags/business
```

## 📚 API 文檔

啟動服務後，可以訪問以下文檔：

- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc

## 🔧 配置說明

### 服務配置
在 `unified_api_gateway.py` 中的 `SERVICE_CONFIGS` 可以配置各微服務的 URL：

```python
SERVICE_CONFIGS = {
    "tts": {
        "url": os.getenv("TTS_SERVICE_URL", "http://localhost:8001"),
        "health_endpoint": "/health"
    },
    "stt": {
        "url": os.getenv("STT_SERVICE_URL", "http://localhost:8002"),
        "health_endpoint": "/health"
    },
    # ... 其他服務
}
```

### 靜態檔案配置
```python
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend" / "home"
IMAGES_PATH = FRONTEND_PATH / "images"
ASSETS_PATH = FRONTEND_PATH / "assets"
```

## 🐛 故障排除

### 1. 服務無法啟動
- 檢查 Python 版本是否 >= 3.8
- 檢查依賴是否正確安裝
- 檢查前端目錄是否存在

### 2. 頁面無法載入
- 檢查 `frontend/home` 目錄是否存在
- 檢查 `images` 和 `assets` 目錄是否存在

### 3. API 調用失敗
- 檢查對應的微服務是否正在運行
- 檢查環境變數設定是否正確
- 查看服務日誌

### 4. 資料庫連接失敗
- 檢查 PostgreSQL 配置
- 檢查 MinIO 配置
- 確保資料庫服務正在運行

## 📝 開發指南

### 1. 添加新的 API 端點
```python
@app.post("/api/new-endpoint")
async def new_endpoint(request: NewRequestModel):
    # 實現邏輯
    return {"success": True, "data": result}
```

### 2. 添加新的 Pydantic 模型
```python
class NewRequestModel(BaseModel):
    field1: str = Field(..., description="描述")
    field2: int = Field(0, description="描述")
```

### 3. 添加新的服務配置
```python
SERVICE_CONFIGS["new_service"] = {
    "url": os.getenv("NEW_SERVICE_URL", "http://localhost:8006"),
    "health_endpoint": "/health"
}
```

## 🔒 安全注意事項

1. **CORS 設定**: 目前允許所有來源，生產環境應限制特定域名
2. **環境變數**: 敏感資訊應通過環境變數設定，不要硬編碼
3. **輸入驗證**: 所有 API 輸入都應通過 Pydantic 模型驗證
4. **錯誤處理**: 避免在錯誤回應中洩露敏感資訊

## 📄 授權

本專案遵循 Podwise 專案的授權條款。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案。 