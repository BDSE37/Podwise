# Podwise RAG Pipeline

## 概述

Podwise RAG Pipeline 是一個基於三層 CrewAI 架構的智能 Podcast 推薦系統，整合了向量搜尋、智能 TAG 提取、Web Search 備援等功能，提供高品質的 Podcast 推薦服務。

## 架構設計

### 三層 CrewAI 架構

```
┌─────────────────────────────────────────────────────────────┐
│                    第一層：領導者層                          │
│                    (Leader Layer)                          │
│                 ┌─────────────────┐                        │
│                 │   LeaderAgent   │                        │
│                 │   協調與決策    │                        │
│                 └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  第二層：類別專家層                          │
│                (Category Expert Layer)                     │
│         ┌─────────────────┐    ┌─────────────────┐         │
│         │ BusinessExpert  │    │EducationExpert  │         │
│         │   商業專家      │    │   教育專家      │         │
│         └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 第三層：功能專家層                           │
│               (Functional Expert Layer)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │RAGExpert    │ │SummaryExpert│ │RatingExpert │          │
│  │檢索專家     │ │摘要專家     │ │評分專家     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 核心組件

#### 1. 代理人系統 (Agents)
- **LeaderAgent**: 三層架構協調者，負責最終決策
- **BusinessExpertAgent**: 商業類別專家，處理商業相關查詢
- **EducationExpertAgent**: 教育類別專家，處理教育相關查詢
- **RAGExpertAgent**: 檢索專家，負責向量搜尋和內容檢索
- **SummaryExpertAgent**: 摘要專家，生成內容摘要
- **RatingExpertAgent**: 評分專家，評估內容品質

#### 2. 工具系統 (Tools)
- **EnhancedVectorSearchTool**: 增強型向量搜尋工具
- **KeywordMapper**: 關鍵詞映射工具
- **KNNRecommender**: KNN 推薦器
- **WebSearchTool**: Web 搜尋備援工具
- **PodcastFormatter**: Podcast 格式化工具
- **SmartTagExtractor**: 智能 TAG 提取工具

#### 3. 服務系統 (Services)
- **ChatHistoryService**: 聊天歷史管理服務
- **Qwen3LLMManager**: Qwen3 LLM 管理器
- **AgentManager**: 代理人管理器

## 功能特點

### 1. 智能 TAG 提取
- 結合 Word2Vec 與 Transformer 的語義理解
- 自動識別查詢中的關鍵詞並映射到現有標籤
- 支援模糊匹配和語義相似度計算

### 2. Podcast 格式化
- 自動生成 Apple Podcast 連結格式
- 智能 TAG 標註（紅色顯示）
- 節目去重和信心度排序
- RSS ID 字典序排序

### 3. Web Search 備援
- 當信心度低於 0.7 時自動觸發
- 支援 OpenAI 查詢
- 主題自動切換
- 結果轉換為 Podcast 格式

### 4. 三層協調架構
- 所有功能必須通過 Leader Agent 協調
- 類別專家負責特定領域分析
- 功能專家提供專業技術支援

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
# 複製環境變數範例
cp env.local .env

# 編輯 .env 檔案
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=mongodb://localhost:27017
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. 使用客戶端

```python
import asyncio
from rag_pipeline_client import RAGPipelineClient, QueryRequest

async def main():
    # 初始化客戶端
    client = RAGPipelineClient()
    await client.initialize()
    
    # 處理查詢
    request = QueryRequest(
        query="我想了解台積電的投資分析",
        user_id="user_001",
        use_web_search=True,
        use_smart_tags=True
    )
    
    response = await client.process_query(request)
    print(f"回應: {response.response}")
    print(f"推薦: {response.recommendations}")

# 執行
asyncio.run(main())
```

### 4. 使用便捷函數

```python
import asyncio
from rag_pipeline_client import process_query_simple

async def main():
    # 簡單查詢處理
    response = await process_query_simple(
        query="我想了解台積電的投資分析",
        user_id="user_001"
    )
    print(response)

asyncio.run(main())
```

## API 端點

### 主要端點

- `POST /api/v1/query`: 處理用戶查詢
- `POST /api/v1/validate-user`: 驗證用戶
- `GET /api/v1/chat-history/{user_id}`: 獲取聊天歷史
- `GET /api/v1/system-info`: 獲取系統資訊
- `GET /health`: 健康檢查

### 範例請求

```bash
# 處理查詢
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "query": "我想了解台積電的投資分析",
    "session_id": "session_001"
  }'

# 驗證用戶
curl -X POST "http://localhost:8000/api/v1/validate-user" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001"}'
```

## 配置說明

### 主要配置檔案

- `config/integrated_config.py`: 整合配置
- `config/crewai_config.py`: CrewAI 架構配置
- `config/hierarchical_rag_config.yaml`: 分層 RAG 配置

### 環境變數

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# 資料庫配置
MONGODB_URI=mongodb://localhost:27017
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 服務配置
RAG_PIPELINE_HOST=localhost
RAG_PIPELINE_PORT=8000
```

## 開發指南

### 目錄結構

```
rag_pipeline/
├── app/                    # 應用程式層
│   ├── main_crewai.py     # CrewAI 主應用程式
│   └── __init__.py
├── core/                   # 核心組件
│   ├── crew_agents.py     # 代理人系統
│   ├── chat_history_service.py
│   ├── qwen3_llm_manager.py
│   └── ...
├── tools/                  # 工具層
│   ├── enhanced_vector_search.py
│   ├── podcast_formatter.py
│   ├── smart_tag_extractor.py
│   └── ...
├── config/                 # 配置層
│   ├── integrated_config.py
│   ├── crewai_config.py
│   └── ...
├── utils/                  # 工具函數
├── monitoring/             # 監控組件
├── optimization/           # 優化組件
├── rag_pipeline_client.py # 客戶端
└── README.md
```

### 添加新功能

1. **添加新代理人**:
   ```python
   class NewExpertAgent(BaseAgent):
       async def process(self, input_data: Any) -> AgentResponse:
           # 實作處理邏輯
           pass
   ```

2. **添加新工具**:
   ```python
   class NewTool:
       def __init__(self, config: Dict[str, Any]):
           # 初始化邏輯
           pass
   ```

3. **更新配置**:
   - 在 `crewai_config.py` 中添加新代理人配置
   - 在 `integrated_config.py` 中添加新工具配置

### 測試

```bash
# 運行測試
python -m pytest tests/

# 運行特定測試
python test_smart_tag_extraction.py
```

## 監控與優化

### 性能監控

- 使用 `PerformanceMonitor` 監控系統性能
- 使用 `ABTestingManager` 進行 A/B 測試
- 使用 `HierarchicalRAGMonitor` 監控 RAG 流程

### 優化建議

1. **向量搜尋優化**:
   - 調整 Milvus 搜尋參數
   - 使用適當的索引類型
   - 定期重建索引

2. **LLM 優化**:
   - 使用快取減少重複請求
   - 調整模型參數
   - 實作模型輪換策略

3. **記憶體優化**:
   - 定期清理快取
   - 使用流式處理
   - 實作分頁載入

## 故障排除

### 常見問題

1. **初始化失敗**:
   - 檢查環境變數配置
   - 確認資料庫連接
   - 檢查模型載入

2. **搜尋結果不佳**:
   - 調整信心度閾值
   - 檢查向量資料品質
   - 優化查詢預處理

3. **回應速度慢**:
   - 檢查網路連接
   - 優化資料庫查詢
   - 使用快取機制

### 日誌分析

```bash
# 查看詳細日誌
tail -f logs/rag_pipeline.log

# 搜尋錯誤日誌
grep "ERROR" logs/rag_pipeline.log
```

## 版本歷史

### v3.0.0 (當前版本)
- 完整的三層 CrewAI 架構
- 智能 TAG 提取功能
- Web Search 備援機制
- Podcast 格式化工具
- 完整的客戶端 API

### v2.0.0
- 基礎 RAG 功能
- 向量搜尋整合
- 用戶管理系統

### v1.0.0
- 基礎架構
- 簡單查詢處理

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