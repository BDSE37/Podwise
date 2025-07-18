# Podwise LLM 服務

## 概述

Podwise LLM 服務是一個整合多種語言模型的統一服務，採用 OOP 架構設計，支援 Qwen2.5-Taiwan、Qwen3:8b 等模型，並整合 Langfuse 追蹤功能。

## 功能特色

### 🎯 核心功能
- **多模型支援** - 支援 Qwen2.5-Taiwan、Qwen3:8b、DeepSeek 等模型
- **OOP 架構** - 採用物件導向設計，易於擴展和維護
- **自動 Fallback** - 當主要模型失敗時自動切換到備用模型
- **Langfuse 追蹤** - 完整的請求追蹤和監控
- **向量嵌入** - 支援 BGE-M3 向量嵌入模型

### 📊 模型配置
- **Qwen2.5-Taiwan** (優先級 1) - 台灣優化的 Qwen 模型
- **Qwen3:8b** (優先級 2) - 標準 Qwen3 模型
- **Qwen** (優先級 3) - 通用 Qwen 模型（向後相容）
- **DeepSeek** (優先級 4) - DeepSeek 編程模型

## 系統架構

### 目錄結構
```
llm/
├── main.py                    # 統一主介面 (FastAPI)
├── core/                      # 核心模組
│   ├── ollama_llm.py          # Ollama 整合
│   └── base_llm.py            # 基礎 LLM 類別
├── config/                    # 配置模組
├── requirements.txt           # 依賴套件
└── Dockerfile                 # 容器化配置
```

### 類別架構
```
LLMService
├── ModelConfig               # 模型配置
├── GenerationRequest         # 生成請求
├── GenerationResponse        # 生成回應
└── 核心方法
    ├── generate_text()       # 文字生成
    ├── _select_best_model()  # 模型選擇
    ├── _fallback_generation() # Fallback 機制
    └── _calculate_confidence() # 信心度計算
```

## API 端點

### 健康檢查
```http
GET /health
```

回應：
```json
{
  "status": "healthy",
  "models": [
    {
      "name": "qwen2.5-Taiwan",
      "model_id": "qwen2.5:7b",
      "enabled": true,
      "priority": 1
    }
  ],
  "embedding_models": ["bge-m3"]
}
```

### 文字生成
```http
POST /generate
Content-Type: application/json

{
  "prompt": "請推薦投資理財的 podcast",
  "model": "qwen2.5-Taiwan",
  "max_tokens": 2048,
  "temperature": 0.7,
  "system_prompt": "你是一個專業的 podcast 推薦助手",
  "user_id": "user123",
  "metadata": {
    "source": "llm_test"
  }
}
```

回應：
```json
{
  "text": "根據您的需求，我推薦以下投資理財 podcast...",
  "model_used": "qwen2.5-Taiwan",
  "tokens_used": 150,
  "processing_time": 2.5,
  "confidence": 0.85,
  "trace_id": "trace_123"
}
```

### 向量嵌入
```http
POST /embed
Content-Type: application/json

{
  "text": "投資理財 podcast",
  "model": "bge-m3"
}
```

回應：
```json
{
  "embedding": [[0.1, 0.2, 0.3, ...]]
}
```

### 模型列表
```http
GET /models
```

回應：
```json
{
  "llm_models": [
    {
      "name": "qwen2.5-Taiwan",
      "model_id": "qwen2.5:7b",
      "enabled": true,
      "priority": 1
    }
  ],
  "embedding_models": ["bge-m3"]
}
```

## 配置說明

### 環境變數
```bash
# Ollama 配置
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# Langfuse 追蹤
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=http://localhost:3000

# 向量模型路徑
BGE_MODEL_PATH=/app/models/external/bge-m3

# 服務配置
LLM_SERVICE_PORT=8004
LLM_SERVICE_HOST=0.0.0.0
```

### 模型配置
```python
# 在 main.py 中的 _load_model_configs 方法
self.models["qwen2.5-Taiwan"] = ModelConfig(
    model_name="Qwen2.5-Taiwan",
    model_id="qwen2.5:7b",
    host=os.getenv("OLLAMA_HOST", "localhost"),
    port=int(os.getenv("OLLAMA_PORT", "11434")),
    api_endpoint="/api/generate",
    max_tokens=2048,
    temperature=0.7,
    priority=1
)
```

## 使用範例

### Python 客戶端
```python
import httpx
import asyncio

async def test_llm_service():
    async with httpx.AsyncClient() as client:
        # 健康檢查
        response = await client.get("http://localhost:8004/health")
        print("健康狀態:", response.json())
        
        # 文字生成
        response = await client.post(
            "http://localhost:8004/generate",
            json={
                "prompt": "推薦投資理財的 podcast",
                "model": "qwen2.5-Taiwan",
                "max_tokens": 500
            }
        )
        print("生成結果:", response.json())

# 執行測試
asyncio.run(test_llm_service())
```

### JavaScript 客戶端
```javascript
// 健康檢查
const healthResponse = await fetch('http://localhost:8004/health');
const healthData = await healthResponse.json();
console.log('健康狀態:', healthData);

// 文字生成
const generateResponse = await fetch('http://localhost:8004/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        prompt: '推薦投資理財的 podcast',
        model: 'qwen2.5-Taiwan',
        max_tokens: 500
    })
});
const generateData = await generateResponse.json();
console.log('生成結果:', generateData);
```

## 啟動指南

### 1. 安裝依賴
```bash
cd backend/llm
pip install -r requirements.txt
```

### 2. 啟動 Ollama 服務
```bash
# 確保 Ollama 已安裝並運行
ollama serve

# 拉取模型
ollama pull qwen2.5:7b
ollama pull qwen3:8b
```

### 3. 啟動 LLM 服務
```bash
python main.py
```

### 4. 驗證服務
```bash
curl http://localhost:8004/health
```

## 故障排除

### 常見問題

1. **模型連接失敗**
   - 檢查 Ollama 服務是否運行
   - 確認模型是否已下載
   - 檢查網路連接

2. **Langfuse 追蹤失敗**
   - 檢查 Langfuse 配置
   - 確認 API 金鑰是否正確

3. **向量模型載入失敗**
   - 檢查模型路徑是否正確
   - 確認模型檔案是否完整

### 日誌檢查
```bash
# 查看服務日誌
tail -f logs/llm_service.log

# 查看 Ollama 日誌
ollama logs
```

## 整合測試

### 與 RAG Pipeline 整合
```python
# 在 RAG Pipeline 中使用 LLM 服務
import httpx

async def get_llm_response(prompt: str, model: str = "qwen2.5-Taiwan"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/generate",
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": 2048
            }
        )
        return response.json()
```

### 與 TTS 服務整合
```python
# 生成文字後轉為語音
async def generate_and_speak(prompt: str):
    # 1. 生成文字
    llm_response = await get_llm_response(prompt)
    text = llm_response["text"]
    
    # 2. 轉為語音
    tts_response = await generate_tts(text)
    return tts_response
```

## 效能優化

### 1. 模型快取
- 使用 HTTP 連接池
- 實作模型回應快取
- 優化模型載入時間

### 2. 並行處理
- 支援多個並發請求
- 實作請求隊列
- 優化資源使用

### 3. 監控指標
- 請求延遲監控
- 模型使用率統計
- 錯誤率追蹤

## 未來規劃

1. **模型擴展**
   - 支援更多語言模型
   - 實作模型自動選擇
   - 支援模型微調

2. **功能增強**
   - 支援串流回應
   - 實作對話記憶
   - 支援多語言

3. **效能提升**
   - 實作模型量化
   - 優化記憶體使用
   - 支援 GPU 加速

這個 LLM 服務確保了與其他 Podwise 模組的無縫整合，為整個系統提供強大的語言模型支援。 