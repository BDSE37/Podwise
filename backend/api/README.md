# Podwise API 閘道服務

統一的 API 閘道，整合所有後端服務的介面。

## 🎯 功能特色

### 🌐 服務整合
- **STT 服務**：語音轉文字功能
- **TTS 服務**：文字轉語音功能
- **LLM 服務**：大語言模型聊天功能
- **RAG 服務**：檢索增強生成功能
- **ML 服務**：機器學習推薦功能
- **Config 服務**：配置管理和資料庫初始化

### 🔧 API 功能
- **服務健康檢查**：監控所有微服務狀態
- **統一介面**：提供標準化的 API 端點
- **錯誤處理**：全域異常處理和錯誤回應
- **配置查詢**：統一獲取所有服務配置

## 🏗️ 系統架構

```
Client Request → API Gateway → Microservice → Response
```

1. 客戶端發送請求到 API 閘道
2. API 閘道驗證請求並路由到對應服務
3. 微服務處理請求並返回結果
4. API 閘道統一格式化回應並返回給客戶端

## 🚀 快速開始

### 本地開發
```bash
cd Podwise/backend/api
pip install -r requirements.txt
python app.py
```

### Docker 部署
```bash
docker build -t podwise-api .
docker run -p 8006:8006 podwise-api
```

## 🔧 主要設定

### 環境變數

```bash
# 服務 URL 配置
STT_SERVICE_URL=http://stt-service:8001
TTS_SERVICE_URL=http://tts-service:8003
LLM_SERVICE_URL=http://llm-service:8000
RAG_SERVICE_URL=http://rag-pipeline-service:8005
ML_SERVICE_URL=http://ml-pipeline-service:8004
CONFIG_SERVICE_URL=http://config-service:8008
```

## 📋 API 端點

### 基礎端點
- `GET /` - 服務狀態和端點列表
- `GET /health` - 健康檢查
- `GET /api/v1/services` - 所有服務狀態
- `GET /api/v1/configs` - 所有配置

### 服務端點
- `POST /api/v1/stt/transcribe` - 語音轉文字
- `POST /api/v1/tts/synthesize` - 文字轉語音
- `POST /api/v1/llm/chat` - LLM 聊天
- `POST /api/v1/rag/query` - RAG 查詢
- `POST /api/v1/ml/recommend` - ML 推薦
- `POST /api/v1/init/database` - 資料庫初始化

## 🛠️ 依賴項目

- fastapi
- uvicorn
- httpx
- pydantic

## ⚠️ 注意事項

- 確保所有微服務正在運行
- 檢查服務 URL 配置是否正確
- 監控服務健康狀態
- 處理服務間通訊錯誤 