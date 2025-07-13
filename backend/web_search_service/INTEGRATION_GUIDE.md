# Web Search Service 整合指南

本指南說明如何將 Web Search Service 整合到 Podwise 系統中，特別是 RAG Pipeline 的 fallback 機制。

## 整合架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Pipeline  │───▶│  Web Search     │───▶│  OpenAI API     │
│   (Port 8005)   │    │  (Port 8006)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   TTS Service   │    │   Fallback      │
│   (Port 8003)   │    │   Response      │
└─────────────────┘    └─────────────────┘
```

## 三層式 Fallback 機制

### 第一層：RAG 檢索
- 使用 Milvus 向量資料庫檢索相關內容
- 信心度閾值：0.8

### 第二層：Web Search
- 當 RAG 信心度 < 0.8 時啟動
- 使用 OpenAI API 進行網路搜尋
- 信心度閾值：0.7

### 第三層：預設回應
- 當 Web Search 也失敗時使用
- 提供基本問答功能

## 環境變數配置

### backend/.env 檔案

```bash
# OpenAI API 設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
WEB_SEARCH_MODEL=gpt-3.5-turbo

# Web Search Service 設定
WEB_SEARCH_HOST=0.0.0.0
WEB_SEARCH_PORT=8006
WEB_SEARCH_RELOAD=false

# RAG Pipeline 整合設定
WEB_SEARCH_ENABLED=true
WEB_SEARCH_FALLBACK_THRESHOLD=0.7
```

## 啟動順序

### 1. 啟動 Web Search Service

```bash
# 使用 Docker Compose
docker-compose up web_search -d

# 或直接啟動
cd backend/web_search_service
python web_search_service.py
```

### 2. 啟動 RAG Pipeline

```bash
# 使用 Docker Compose
docker-compose up rag_pipeline -d

# 或直接啟動
cd backend/rag_pipeline
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### 3. 啟動其他服務

```bash
# 啟動完整系統
docker-compose up -d
```

## API 整合範例

### 在 RAG Pipeline 中使用

```python
# backend/rag_pipeline/core/agent_manager.py

import asyncio
from typing import Dict, Any, Optional
from rag_pipeline.tools.web_search_tool import get_web_search_expert, SearchRequest

class AgentManager:
    def __init__(self):
        self.web_search_expert = None
        self.web_search_enabled = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
        self.fallback_threshold = float(os.getenv("WEB_SEARCH_FALLBACK_THRESHOLD", "0.7"))
    
    async def initialize(self):
        """初始化 Web Search Expert"""
        if self.web_search_enabled:
            try:
                self.web_search_expert = get_web_search_expert()
                await self.web_search_expert.initialize()
                logger.info("Web Search Expert 初始化成功")
            except Exception as e:
                logger.error(f"Web Search Expert 初始化失敗: {e}")
    
    async def process_query_with_fallback(self, query: str) -> Dict[str, Any]:
        """使用 fallback 機制處理查詢"""
        
        # 第一層：RAG 檢索
        rag_result = await self._rag_retrieval(query)
        
        if rag_result["confidence"] >= 0.8:
            return {
                "answer": rag_result["answer"],
                "source": "rag_pipeline",
                "confidence": rag_result["confidence"],
                "fallback_used": False
            }
        
        # 第二層：Web Search
        if self.web_search_expert and self.web_search_enabled:
            web_result = await self._web_search_fallback(query)
            
            if web_result and web_result["confidence"] >= self.fallback_threshold:
                return {
                    "answer": web_result["answer"],
                    "source": "web_search",
                    "confidence": web_result["confidence"],
                    "fallback_used": True
                }
        
        # 第三層：預設回應
        return {
            "answer": "抱歉，我無法找到相關資訊。請嘗試重新描述您的問題。",
            "source": "default",
            "confidence": 0.0,
            "fallback_used": True
        }
    
    async def _web_search_fallback(self, query: str) -> Optional[Dict[str, Any]]:
        """Web Search Fallback"""
        try:
            request = SearchRequest(
                query=query,
                max_results=3,
                language="zh-TW"
            )
            
            response = await self.web_search_expert.search(request)
            
            if response.results:
                return {
                    "answer": response.summary or response.results[0].snippet,
                    "confidence": response.confidence,
                    "results": response.results
                }
            
        except Exception as e:
            logger.error(f"Web Search Fallback 失敗: {e}")
        
        return None
```

### 在 main.py 中整合

```python
# backend/rag_pipeline/main.py

from core.agent_manager import AgentManager

class RAGPipeline:
    def __init__(self):
        self.agent_manager = AgentManager()
    
    async def startup(self):
        """啟動時初始化"""
        await self.agent_manager.initialize()
    
    async def query(self, user_query: str) -> Dict[str, Any]:
        """處理用戶查詢"""
        return await self.agent_manager.process_query_with_fallback(user_query)
```

## 測試整合

### 1. 測試 Web Search Service

```bash
# 測試健康檢查
curl http://localhost:8006/health

# 測試搜尋功能
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{"query": "台灣最新科技新聞", "max_results": 3}'
```

### 2. 測試 RAG Pipeline 整合

```bash
# 測試 RAG Pipeline
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"query": "最新的 AI 技術發展"}'
```

### 3. 執行完整測試

```bash
cd backend/web_search_service
python test_web_search.py
```

## 監控與日誌

### 健康檢查

```bash
# 檢查 Web Search Service 狀態
curl http://localhost:8006/health

# 檢查 RAG Pipeline 狀態
curl http://localhost:8005/health
```

### 日誌監控

```bash
# 查看 Web Search Service 日誌
docker logs podwise_web_search

# 查看 RAG Pipeline 日誌
docker logs podwise_rag_pipeline
```

## 故障排除

### 常見問題

1. **Web Search Service 無法啟動**
   ```
   錯誤: OpenAI API 金鑰未設定
   解決: 檢查 OPENAI_API_KEY 環境變數
   ```

2. **RAG Pipeline 無法連接到 Web Search**
   ```
   錯誤: 連接到 Web Search Service 失敗
   解決: 檢查 WEB_SEARCH_HOST 和端口設定
   ```

3. **Fallback 機制不工作**
   ```
   錯誤: Web Search 未在 fallback 中啟動
   解決: 檢查 WEB_SEARCH_ENABLED 設定
   ```

### 除錯步驟

1. 檢查環境變數設定
2. 確認服務啟動順序
3. 檢查網路連線
4. 查看服務日誌
5. 測試個別服務功能

## 效能優化

### 快取機制

```python
# 在 WebSearchExpert 中添加快取
import asyncio
from functools import lru_cache

class WebSearchExpert:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1小時
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        # 檢查快取
        cache_key = f"{request.query}_{request.language}_{request.max_results}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if time.time() - cached_result["timestamp"] < self.cache_ttl:
                return cached_result["response"]
        
        # 執行搜尋
        response = await self._perform_search(request)
        
        # 儲存到快取
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        return response
```

### 並發控制

```python
# 限制並發請求數量
import asyncio
from asyncio import Semaphore

class WebSearchExpert:
    def __init__(self):
        self.semaphore = Semaphore(5)  # 最多5個並發請求
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        async with self.semaphore:
            return await self._perform_search(request)
```

## 安全考量

### API 金鑰保護

```bash
# 使用 Kubernetes Secrets
kubectl create secret generic openai-secret \
  --from-literal=api-key=your_openai_api_key

# 在部署中使用
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: openai-secret
      key: api-key
```

### 請求限制

```python
# 添加速率限制
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 100, window: int = 3600):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]
        
        # 清理過期請求
        user_requests = [req for req in user_requests if now - req < self.window]
        self.requests[user_id] = user_requests
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True
```

## 未來擴展

### 支援更多搜尋引擎

```python
class MultiSearchEngine:
    def __init__(self):
        self.engines = {
            "openai": OpenAISearchEngine(),
            "google": GoogleSearchEngine(),
            "bing": BingSearchEngine()
        }
    
    async def search(self, query: str, engine: str = "openai"):
        if engine in self.engines:
            return await self.engines[engine].search(query)
        else:
            raise ValueError(f"不支援的搜尋引擎: {engine}")
```

### 智能路由

```python
class SmartRouter:
    def __init__(self):
        self.routing_rules = {
            "news": "google",
            "academic": "bing",
            "general": "openai"
        }
    
    def select_engine(self, query: str, query_type: str = "general"):
        return self.routing_rules.get(query_type, "openai")
```

## 總結

Web Search Service 成功整合到 Podwise 系統中，提供了完整的三層式 fallback 機制：

1. **RAG 檢索**：基於向量資料庫的智能檢索
2. **Web Search**：基於 OpenAI API 的網路搜尋
3. **預設回應**：保障系統可用性的基本回應

這個整合確保了系統在任何情況下都能提供有用的回應，提升了用戶體驗和系統可靠性。 