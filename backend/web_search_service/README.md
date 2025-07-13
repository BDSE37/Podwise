# Web Search Service

基於 OpenAI API 的智能網路搜尋服務，整合到 RAG Pipeline 的 fallback 機制中。

## 功能特色

- 🔍 **智能網路搜尋**: 基於 OpenAI API 的智能搜尋功能
- 🌐 **多語言支援**: 支援繁體中文、簡體中文、英文、日文
- 📝 **智能摘要**: 自動生成搜尋結果摘要
- 🎯 **信心度評估**: 提供搜尋結果的信心度評分
- 🔄 **Fallback 機制**: 整合到 RAG Pipeline 的三層式 fallback 機制

## 快速開始

### 環境需求

- Python 3.11+
- OpenAI API 金鑰
- 網路連線

### 安裝依賴

```bash
cd backend/web_search_service
pip install -r requirements.txt
```

### 環境變數設定

建立 `.env` 檔案：

```bash
# OpenAI API 設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
WEB_SEARCH_MODEL=gpt-3.5-turbo

# 服務設定
WEB_SEARCH_HOST=0.0.0.0
WEB_SEARCH_PORT=8006
WEB_SEARCH_RELOAD=false
```

### 啟動服務

```bash
# 直接啟動
python web_search_service.py

# 或使用 uvicorn
uvicorn web_search_service:app --host 0.0.0.0 --port 8006
```

### Docker 啟動

```bash
# 建立映像檔
docker build -t podwise-web-search .

# 執行容器
docker run -d \
  --name web-search-service \
  -p 8006:8006 \
  -e OPENAI_API_KEY=your_api_key \
  podwise-web-search
```

## API 端點

### 健康檢查

```bash
GET /health
```

回應範例：
```json
{
  "status": "healthy",
  "service_name": "Web Search Service",
  "timestamp": "2024-01-01T12:00:00",
  "details": {
    "api_key_configured": true,
    "model": "gpt-3.5-turbo"
  }
}
```

### 網路搜尋

```bash
POST /search
```

請求範例：
```json
{
  "query": "台灣最新科技新聞",
  "max_results": 3,
  "language": "zh-TW",
  "search_type": "web",
  "include_summary": true
}
```

回應範例：
```json
{
  "query": "台灣最新科技新聞",
  "results": [
    {
      "title": "台灣科技產業最新發展",
      "url": "https://example.com/news",
      "snippet": "台灣科技產業在AI和半導體領域的最新發展...",
      "source": "OpenAI Web Search",
      "confidence": 0.85,
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "summary": "根據最新搜尋結果，台灣科技產業在AI和半導體領域有顯著發展...",
  "total_results": 1,
  "processing_time": 2.5,
  "confidence": 0.85,
  "source": "openai_web_search"
}
```

### 簡化搜尋

```bash
POST /search/simple?query=台灣科技新聞&max_results=3
```

### 服務資訊

```bash
GET /info
```

## 整合到 RAG Pipeline

### 在 RAG Pipeline 中使用

```python
from rag_pipeline.tools.web_search_tool import get_web_search_expert

# 獲取 WebSearchExpert 實例
expert = get_web_search_expert()

# 執行搜尋
from rag_pipeline.tools.web_search_tool import SearchRequest
request = SearchRequest(
    query="用戶查詢",
    max_results=3,
    language="zh-TW"
)
response = await expert.search(request)
```

### Fallback 機制整合

```python
# 在 RAG Pipeline 的 fallback 機制中
async def fallback_to_web_search(query: str):
    """當 RAG 信心度不足時，使用網路搜尋"""
    try:
        expert = get_web_search_expert()
        request = SearchRequest(query=query)
        response = await expert.search(request)
        
        if response.confidence > 0.7:
            return {
                "answer": response.summary or response.results[0].snippet,
                "source": "web_search",
                "confidence": response.confidence
            }
    except Exception as e:
        logger.error(f"網路搜尋失敗: {e}")
    
    return None
```

## 配置選項

### 環境變數

| 變數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API 金鑰（必需） |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | OpenAI API 基礎 URL |
| `WEB_SEARCH_MODEL` | `gpt-3.5-turbo` | 使用的 OpenAI 模型 |
| `WEB_SEARCH_HOST` | `0.0.0.0` | 服務監聽主機 |
| `WEB_SEARCH_PORT` | `8006` | 服務監聽端口 |
| `WEB_SEARCH_RELOAD` | `false` | 是否啟用自動重載 |

### 搜尋參數

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `query` | string | - | 搜尋查詢（必需） |
| `max_results` | integer | 3 | 最大結果數量 (1-10) |
| `language` | string | "zh-TW" | 搜尋語言 |
| `search_type` | string | "web" | 搜尋類型 |
| `include_summary` | boolean | true | 是否包含摘要 |

## 故障排除

### 常見問題

1. **API 金鑰錯誤**
   ```
   錯誤: OpenAI API 金鑰未設定
   解決: 檢查 OPENAI_API_KEY 環境變數
   ```

2. **網路連線問題**
   ```
   錯誤: OpenAI API 調用失敗
   解決: 檢查網路連線和 API 端點
   ```

3. **模型不可用**
   ```
   錯誤: 模型不存在
   解決: 檢查 WEB_SEARCH_MODEL 設定
   ```

### 日誌檢查

```bash
# 查看服務日誌
docker logs web-search-service

# 或直接查看 Python 日誌
tail -f web_search_service.log
```

## 開發指南

### 本地開發

```bash
# 安裝開發依賴
pip install -r requirements.txt

# 啟動開發模式
WEB_SEARCH_RELOAD=true python web_search_service.py
```

### 測試

```bash
# 執行單元測試
python -m pytest tests/

# 測試 API 端點
curl -X GET http://localhost:8006/health
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{"query": "測試查詢"}'
```

## 部署

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-search-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-search-service
  template:
    metadata:
      labels:
        app: web-search-service
    spec:
      containers:
      - name: web-search
        image: podwise/web-search:latest
        ports:
        - containerPort: 8006
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: WEB_SEARCH_PORT
          value: "8006"
```

### Docker Compose

```yaml
version: '3.8'
services:
  web-search:
    build: ./backend/web_search_service
    ports:
      - "8006:8006"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEB_SEARCH_PORT=8006
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 監控與維護

### 健康檢查

服務提供內建的健康檢查端點：

```bash
curl http://localhost:8006/health
```

### 效能監控

- 處理時間：記錄每次搜尋的處理時間
- 信心度：追蹤搜尋結果的信心度分佈
- 錯誤率：監控 API 調用失敗率

### 備份與恢復

- 配置備份：定期備份環境變數配置
- 日誌備份：保留搜尋日誌用於分析

## 未來規劃

- [ ] 支援更多搜尋引擎（Google、Bing）
- [ ] 快取機制優化
- [ ] 更精確的結果解析
- [ ] 多語言摘要生成
- [ ] 搜尋歷史記錄
- [ ] 自定義搜尋過濾器

## 授權

MIT License - 詳見 [LICENSE](../LICENSE) 檔案

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡資訊

- 專案維護者：Podwise Team
- 電子郵件：support@podwise.com
- 專案網址：https://github.com/podwise/web-search-service 