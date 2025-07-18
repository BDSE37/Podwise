# Podwise RAG Pipeline 整合系統

## 系統概述

Podwise RAG Pipeline 是一個整合了多個模組的智能檢索與推薦系統，採用三層式 CrewAI agent 架構，提供完整的 Podcast 內容檢索、推薦和語音合成服務。系統遵循 Google Clean Code 原則，確保模組化設計和易於維護。

## 核心架構

### 三層式 CrewAI Agent 架構

根據 `agent_roles_config.py` 的配置，系統採用以下三層架構：

#### 第一層：領導者層 (Leader Layer)
- **chief_decision_orchestrator**: 決策統籌長
  - 整合多元專家觀點
  - 量化評估與清晰比較
  - 提供最契合用戶需求的行動建議

#### 第二層：類別專家層 (Category Expert Layer)
- **business_intelligence_expert**: 商業智慧專家
  - 專注商業/投資/創業內容推薦
  - 個人化學習建議
- **educational_growth_strategist**: 教育成長專家
  - 專注教育/學習方法/個人成長內容
  - 行為改變與反思思維

#### 第三層：功能專家層 (Functional Expert Layer)
- **intelligent_retrieval_expert**: 智能檢索專家 ⭐
  - 語意分析與向量檢索
  - 標籤匹配與查詢改寫
  - 25秒內完成完整檢索循環
- **content_summary_expert**: 內容摘要專家
  - 生成 ≤200 字中文摘要
  - 關鍵事實核對
- **tag_classification_expert**: TAG 分類專家
  - 關鍵詞映射與內容分類
  - 商業/教育/其他分類
- **tts_expert**: 語音合成專家
  - 自然流暢語音生成
  - 情感豐富表達
- **user_experience_expert**: 用戶體驗專家
  - 個人化用戶洞察報告
  - 行為分析與偏好建模

## 模組整合

### 1. 資料庫整合

```python
# 統一的資料庫配置管理
from config.database_config import get_database_config_manager

# 支援的資料庫：
# - MongoDB: 聊天歷史和會話管理
# - PostgreSQL: 結構化資料儲存
# - Redis: 快取和會話狀態
# - Milvus: 向量資料庫
```

### 2. ML Pipeline 整合

```python
# 智能推薦系統整合
from ml_pipeline.core.recommender import Recommender
from ml_pipeline.core.data_manager import DataManager

# 功能：
# - 智能推薦系統
# - 用戶偏好建模
# - 內容相似度計算
```

### 3. TTS 整合

```python
# 語音合成服務
from tts.core.tts_service import TTSService

# 支援的語音模型：
# - podrina: 女聲
# - podrisa: 女聲變體
# - podrino: 男聲
# - 語速調節: 0.5x - 1.5x
```

### 4. LLM 整合

```python
# 支援多種 LLM 模型
from llm.core.ollama_llm import OllamaLLM
from llm.core.qwen_llm_manager import Qwen3LLMManager

# 支援模型：
# - qwen2.5-Taiwan: 繁體中文優化
# - qwen3:8b: 輕量級模型
# - Ollama 本地模型: 自定義模型
```

### 5. STT 整合

```python
# 語音轉文字服務
from stt.stt_service import STTService

# 功能：
# - 語音識別
# - 多語言支援
# - 實時轉錄
```

### 6. User Management 整合

```python
# 用戶管理服務
from user_management.user_service import UserService

# 功能：
# - 用戶註冊/登入
# - 個人化設定
# - 使用歷史記錄
```

## 工具模組

### 1. CrossDBTextFetcher
跨資料庫文本擷取工具，支援 PostgreSQL 和 MongoDB 的模糊及精確比對。

```python
from tools import get_cross_db_fetcher

fetcher = get_cross_db_fetcher()
results = await fetcher.fetch_text("查詢內容", limit=10)
```

### 2. SummaryGenerator
長文本摘要生成工具，支援 OpenAI API 和備援方法。

```python
from tools import get_summary_generator

generator = get_summary_generator()
summary = await generator.generate_summary("長文本內容", max_length=150)
```

### 3. SimilarityMatcher
餘弦相似度計算工具，含向量正規化、批量計算和最佳匹配功能。

```python
from tools import get_similarity_matcher

matcher = get_similarity_matcher()
similarity = matcher.calculate_cosine_similarity(vector1, vector2)
```

### 4. PodcastFormatter
Podcast 資料格式化工具，統一處理標題、描述和標籤。

```python
from tools import get_podcast_formatter

formatter = get_podcast_formatter()
formatted_data = formatter.format_podcast(podcast_data)
```

### 5. WebSearchExpert
Web 搜尋專家，提供智能網路搜尋功能。

```python
from tools import get_web_search

web_search = get_web_search()
results = await web_search.search("搜尋查詢", max_results=5)
```

## 智能檢索 Fallback 機制

### 三層式回覆機制

1. **RAG 向量搜尋** (信心度 ≥ 0.7) → 使用本地知識庫
2. **Web 搜尋 + OpenAI** (信心度 < 0.7) → 使用 OpenAI API 智能搜尋
3. **預設問答** (最後保障) → 使用預設回應

### 信心度閾值

- **intelligent_retrieval_expert**: 0.7 (低於此值回傳 NO_MATCH)
- **business_intelligence_expert**: 0.75
- **educational_growth_strategist**: 0.75
- **chief_decision_orchestrator**: 0.8

## 快速使用

### 使用 min.py 統一介面

```python
from min import start_pipeline, query, get_recommendations, synthesize_speech

# 啟動 Pipeline
await start_pipeline()

# 執行查詢
response = await query("什麼是機器學習？", "user123")
print(f"回應: {response.response}")
print(f"信心度: {response.confidence}")

# 獲取推薦
recommendations = await get_recommendations("機器學習", "user123", 5)

# 語音合成
tts_result = await synthesize_speech("這是一個測試", "podrina", 1.0)

# 停止 Pipeline
await stop_pipeline()
```

### 使用核心類別

```python
from core.rag_pipeline_core import RAGPipelineCore

# 初始化核心
core = RAGPipelineCore(
    enable_monitoring=True,
    enable_semantic_retrieval=True,
    confidence_threshold=0.7
)

# 啟動
await core.initialize()

# 處理查詢
request = QueryRequest(
    query="查詢內容",
    user_id="user123",
    enable_tts=True
)
response = await core.process_query(request)

# 清理
await core.cleanup()
```

### 使用服務管理器

```python
from core.unified_service_manager import get_service_manager

# 獲取服務管理器
manager = get_service_manager()

# 初始化所有服務
await manager.initialize()

# 使用特定服務
db_service = manager.get_database_service()
llm_service = manager.get_llm_service()
tts_service = manager.get_tts_service()

# 健康檢查
health = await manager.health_check()
```

## API 端點

### 主要查詢端點

```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "用戶查詢內容",
  "user_id": "用戶ID",
  "session_id": "會話ID",
  "enable_tts": true,
  "voice": "podrina",
  "speed": 1.0,
  "metadata": {
                "source": "rag_test",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 回應格式

```json
{
  "user_id": "用戶ID",
  "query": "用戶查詢",
  "response": "AI 回應內容",
  "category": "內容分類",
  "confidence": 0.85,
  "recommendations": [
    {
      "title": "推薦標題",
      "description": "推薦描述",
      "category": "分類",
      "confidence": 0.8,
      "source": "來源"
    }
  ],
  "reasoning": "推理過程",
  "processing_time": 2.5,
  "timestamp": "2024-01-01T00:00:00Z",
  "audio_data": "base64編碼的音頻數據",
  "voice_used": "podrina",
  "speed_used": 1.0,
  "tts_enabled": true
}
```

### TTS 專用端點

```http
POST /api/v1/tts/synthesize
Content-Type: application/json

{
  "text": "要合成的文本",
  "voice": "podrina",
  "speed": 1.0
}
```

### 健康檢查端點

```http
GET /health
```

### 系統資訊端點

```http
GET /api/v1/system-info
```

## 配置管理

### 環境變數配置

系統支援多種環境檔案：
- `env.local`: 本地開發環境
- `.env`: 生產環境
- `.env.example`: 範例配置

```bash
# 資料庫配置
MONGODB_URI=mongodb://localhost:27017/podwise
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=podwise
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=podcast_chunks

# API 配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# 服務配置
RAG_PIPELINE_HOST=localhost
RAG_PIPELINE_PORT=8004
TTS_HOST=localhost
TTS_PORT=8002
STT_HOST=localhost
STT_PORT=8003
LLM_HOST=localhost
LLM_PORT=8004

# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:8b
```

### 配置驗證

```python
from config.database_config import get_database_config_manager

config_manager = get_database_config_manager()
validation = config_manager.validate_config()

for component, is_valid in validation.items():
    print(f"{component}: {'✅' if is_valid else '❌'}")
```

## 部署指南

### 本地開發

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定環境變數
cp env.local.example env.local
# 編輯 env.local 檔案

# 3. 啟動服務
python min.py
```

### Docker 部署

```bash
# 1. 建構映像
docker build -t podwise-rag-pipeline .

# 2. 執行容器
docker run -d \
  --name rag-pipeline \
  -p 8004:8004 \
  --env-file env.local \
  podwise-rag-pipeline
```

### Kubernetes 部署

```bash
# 1. 套用配置
kubectl apply -f deploy/k8s/rag-pipeline/

# 2. 檢查部署狀態
kubectl get pods -l app=rag-pipeline
```

## 監控與日誌

### 日誌配置

系統使用結構化日誌，支援不同等級：
- DEBUG: 詳細除錯資訊
- INFO: 一般資訊
- WARNING: 警告訊息
- ERROR: 錯誤訊息

### 健康檢查

```python
# 檢查系統健康狀態
health = await health_check()
print(f"系統狀態: {health['status']}")
print(f"服務狀態: {health['services']}")
```

### 性能監控

系統內建性能監控：
- 查詢處理時間
- 服務響應時間
- 資源使用率
- 錯誤率統計

## 故障排除

### 常見問題

1. **資料庫連接失敗**
   - 檢查環境變數配置
   - 確認資料庫服務運行狀態
   - 驗證網路連接

2. **LLM 服務無回應**
   - 檢查 Ollama 服務狀態
   - 確認模型檔案存在
   - 驗證 API 金鑰

3. **向量搜尋失敗**
   - 檢查 Milvus 服務狀態
   - 確認集合存在
   - 驗證向量維度匹配

### 除錯模式

```python
# 啟用除錯模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 或設定環境變數
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 開發指南

### 代碼風格

遵循 Google Clean Code 原則：
- 清晰的函數和變數命名
- 適當的註解和文檔
- 模組化設計
- 錯誤處理
- 單元測試

### 新增功能

1. 在適當的模組中新增功能
2. 更新服務管理器
3. 添加單元測試
4. 更新文檔
5. 提交 Pull Request

### 測試

```bash
# 執行單元測試
python -m pytest tests/

# 執行整合測試
python -m pytest tests/integration/

# 執行性能測試
python -m pytest tests/performance/
```

## 版本歷史

### v3.0.0 (最新)
- 重構為模組化架構
- 新增統一服務管理器
- 整合所有工具模組
- 改善錯誤處理和日誌
- 新增健康檢查功能

### v2.0.0
- 新增 CrewAI 三層架構
- 整合 Apple Podcast 排名
- 新增語音合成功能
- 改善向量搜尋性能

### v1.0.0
- 初始版本
- 基本 RAG 功能
- 向量搜尋
- Web 搜尋整合

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 授權

本專案採用 MIT 授權條款。

## 聯絡資訊

- 專案維護者: Podwise Team
- 電子郵件: support@podwise.com
- 專案網址: https://github.com/podwise/rag-pipeline
