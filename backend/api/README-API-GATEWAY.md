# Podwise API 閘道服務使用指南

## 🎯 概述

Podwise API 閘道服務是一個統一的 API 介面，整合所有後端微服務，提供標準化的 API 端點和錯誤處理。

## 🚀 快速開始

### 1. 啟動服務

```bash
# 方法一：使用啟動腳本
cd backend/api
./start_api_gateway.sh

# 方法二：手動啟動
cd backend/api
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

### 2. 驗證服務

```bash
# 測試 API 閘道服務
cd backend/api
python test_api_gateway.py
```

### 3. 訪問 API 文檔

- **Swagger UI**: http://localhost:8006/docs
- **ReDoc**: http://localhost:8006/redoc

## 🌐 服務配置

### 環境變數

```bash
# 服務 URL 配置
export STT_SERVICE_URL=http://localhost:8001
export TTS_SERVICE_URL=http://localhost:8003
export LLM_SERVICE_URL=http://localhost:8000
export RAG_SERVICE_URL=http://localhost:8011
export ML_SERVICE_URL=http://localhost:8004
export CONFIG_SERVICE_URL=http://localhost:8008
```

### 預設配置

如果未設定環境變數，服務將使用以下預設配置：

- **STT 服務**: http://localhost:8001
- **TTS 服務**: http://localhost:8003
- **LLM 服務**: http://localhost:8000
- **RAG 服務**: http://localhost:8011
- **ML 服務**: http://localhost:8004
- **Config 服務**: http://localhost:8008

## 📋 API 端點

### 基礎端點

#### GET /
顯示服務資訊和可用端點

```bash
curl http://localhost:8006/
```

回應範例：
```json
{
  "service": "Podwise API Gateway",
  "version": "1.0.0",
  "description": "統一的 API 閘道，整合所有後端服務",
  "endpoints": {
    "health": "/health",
    "services": "/api/v1/services",
    "configs": "/api/v1/configs",
    "stt": "/api/v1/stt/transcribe",
    "tts": "/api/v1/tts/synthesize",
    "llm": "/api/v1/llm/chat",
    "rag": "/api/v1/rag/query",
    "ml": "/api/v1/ml/recommend"
  }
}
```

#### GET /health
健康檢查 - 檢查所有服務狀態

```bash
curl http://localhost:8006/health
```

#### GET /api/v1/services
獲取所有服務狀態

```bash
curl http://localhost:8006/api/v1/services
```

#### GET /api/v1/configs
獲取所有服務配置

```bash
curl http://localhost:8006/api/v1/configs
```

### 服務端點

#### POST /api/v1/stt/transcribe
語音轉文字

```bash
curl -X POST http://localhost:8006/api/v1/stt/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "http://example.com/audio.mp3",
    "language": "zh-TW"
  }'
```

#### POST /api/v1/tts/synthesize
文字轉語音

```bash
curl -X POST http://localhost:8006/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是測試文字",
    "voice": "zh-TW-HsiaoChenNeural"
  }'
```

#### POST /api/v1/llm/chat
LLM 聊天

```bash
curl -X POST http://localhost:8006/api/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，請介紹一下自己",
    "user_id": "user_001"
  }'
```

#### POST /api/v1/rag/query
RAG 查詢

```bash
curl -X POST http://localhost:8006/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什麼是機器學習？",
    "user_id": "user_001"
  }'
```

#### POST /api/v1/ml/recommend
ML 推薦

```bash
curl -X POST http://localhost:8006/api/v1/ml/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "context": "用戶偏好科技類內容"
  }'
```

#### POST /api/v1/init/database
初始化資料庫

```bash
curl -X POST http://localhost:8006/api/v1/init/database
```

## 🔧 錯誤處理

### HTTP 狀態碼

- **200**: 成功
- **400**: 請求錯誤
- **404**: 服務未找到
- **503**: 服務不可用
- **500**: 內部伺服器錯誤

### 錯誤回應格式

```json
{
  "error": "錯誤描述",
  "detail": "詳細錯誤資訊"
}
```

## 🛠️ 開發指南

### 添加新服務

1. 在 `SERVICE_CONFIG` 中添加服務配置
2. 創建對應的 Pydantic 模型
3. 添加 API 端點
4. 更新測試腳本

### 本地開發

```bash
# 安裝開發依賴
pip install -r requirements.txt

# 啟動開發模式
uvicorn main:app --host 0.0.0.0 --port 8006 --reload

# 運行測試
python test_api_gateway.py
```

### Docker 部署

```bash
# 建構映像
docker build -t podwise-api-gateway .

# 運行容器
docker run -p 8006:8006 \
  -e STT_SERVICE_URL=http://stt-service:8001 \
  -e TTS_SERVICE_URL=http://tts-service:8003 \
  -e LLM_SERVICE_URL=http://llm-service:8000 \
  -e RAG_SERVICE_URL=http://rag-service:8011 \
  -e ML_SERVICE_URL=http://ml-service:8004 \
  -e CONFIG_SERVICE_URL=http://config-service:8008 \
  podwise-api-gateway
```

## 📊 監控與日誌

### 日誌配置

服務使用 Python 標準 logging 模組，預設級別為 INFO。

### 健康檢查

定期檢查 `/health` 端點以監控服務狀態：

```bash
# 檢查服務健康狀態
curl http://localhost:8006/health | jq '.status'

# 檢查特定服務狀態
curl http://localhost:8006/health | jq '.services.rag.status'
```

## 🔒 安全性

### CORS 配置

服務已配置 CORS 中間件，允許所有來源的請求。在生產環境中，建議限制允許的來源。

### 請求驗證

所有請求都使用 Pydantic 模型進行驗證，確保資料格式正確。

## 📝 注意事項

1. **服務依賴**: API 閘道依賴於其他微服務，確保所有服務都在運行
2. **超時設定**: 預設請求超時為 30 秒，健康檢查超時為 5 秒
3. **錯誤處理**: 服務不可用時會返回 503 狀態碼
4. **日誌記錄**: 所有錯誤都會記錄到日誌中

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個服務。 