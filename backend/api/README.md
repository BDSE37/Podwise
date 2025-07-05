# Podwise API 閘道服務

統一的 API 閘道，整合所有後端服務的介面。

## 功能特色

### 服務整合
- **STT 服務**：語音轉文字功能
- **TTS 服務**：文字轉語音功能
- **LLM 服務**：大語言模型聊天功能
- **RAG 服務**：檢索增強生成功能
- **ML 服務**：機器學習推薦功能
- **Config 服務**：配置管理和資料庫初始化

### API 功能
- **服務健康檢查**：監控所有微服務狀態
- **統一介面**：提供標準化的 API 端點
- **錯誤處理**：全域異常處理和錯誤回應
- **配置查詢**：統一獲取所有服務配置

## API 端點

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

## 檔案結構

```
api/
├── app.py              # FastAPI 主應用程式
├── requirements.txt    # Python 依賴
├── Dockerfile         # 容器化配置
├── __init__.py        # 套件初始化
└── README.md          # 說明文件
```

## 使用方式

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

### 環境變數

#### 服務 URL 配置
- `STT_SERVICE_URL` - STT 服務 URL (預設: http://stt-service:8001)
- `TTS_SERVICE_URL` - TTS 服務 URL (預設: http://tts-service:8003)
- `LLM_SERVICE_URL` - LLM 服務 URL (預設: http://llm-service:8000)
- `RAG_SERVICE_URL` - RAG 服務 URL (預設: http://rag-pipeline-service:8005)
- `ML_SERVICE_URL` - ML 服務 URL (預設: http://ml-pipeline-service:8004)
- `CONFIG_SERVICE_URL` - Config 服務 URL (預設: http://config-service:8008)

## 整合說明

本服務作為 API 閘道，提供以下整合功能：

1. **服務發現**：自動檢查所有微服務的健康狀態
2. **請求路由**：將請求轉發到對應的微服務
3. **錯誤處理**：統一處理服務錯誤和異常
4. **配置管理**：統一獲取和管理所有服務配置
5. **監控**：提供服務狀態監控和健康檢查

### 服務通訊流程

```
Client Request → API Gateway → Microservice → Response
```

1. 客戶端發送請求到 API 閘道
2. API 閘道驗證請求並路由到對應服務
3. 微服務處理請求並返回結果
4. API 閘道統一格式化回應並返回給客戶端

### 錯誤處理

- **服務不可用**：返回 503 錯誤
- **請求超時**：返回 408 錯誤
- **服務錯誤**：返回對應的 HTTP 狀態碼
- **全域異常**：返回 500 錯誤

## 部署建議

1. **負載均衡**：使用 Nginx 或 HAProxy 進行負載均衡
2. **監控**：整合 Prometheus 和 Grafana 進行監控
3. **日誌**：使用 ELK Stack 進行日誌收集和分析
4. **安全**：添加 API 金鑰驗證和速率限制
5. **快取**：使用 Redis 進行回應快取

## 開發指南

### 添加新服務
1. 在 `SERVICE_CONFIGS` 中添加服務配置
2. 添加對應的 API 端點
3. 實作服務健康檢查
4. 更新文檔

### 擴展功能
1. 添加認證和授權
2. 實作請求限流
3. 添加請求日誌記錄
4. 實作回應快取
5. 添加 API 版本控制 