# Podwise RAG Pipeline 系統

## 📋 概述

Podwise RAG Pipeline 是一個基於 CrewAI 的三層架構檢索增強生成系統，整合了層級化 RAG 處理、智能代理人協作和向量搜尋功能。系統遵循 OOP 原則和 Google Clean Code 標準，提供高效的播客推薦和內容檢索服務。

## 🏗️ 三層架構設計

### 代理人層級結構
```
第一層：領導者層 (Leader Layer)
├── chief_decision_orchestrator - 決策統籌長

第二層：類別專家層 (Category Expert Layer)  
├── business_intelligence_expert - 商業智慧專家
└── educational_growth_strategist - 教育成長專家

第三層：功能專家層 (Functional Expert Layer)
├── intelligent_retrieval_expert - 智能檢索專家
├── content_summary_expert - 內容摘要專家
├── tag_classification_expert - TAG 分類專家
├── tts_expert - 語音合成專家
├── user_experience_expert - 用戶體驗專家
└── web_search_expert - Web 搜尋專家
```

### 六層 RAG 處理架構
1. **Level 1 - 查詢處理**: 查詢重寫、意圖識別、實體提取
2. **Level 2 - 混合搜尋**: 密集檢索、稀疏檢索、語義搜尋
3. **Level 3 - 檢索增強**: 上下文增強、知識圖譜整合
4. **Level 4 - 重新排序**: 多準則排序、個人化、多樣性
5. **Level 5 - 上下文壓縮**: 內容壓縮、信息過濾
6. **Level 6 - 混合式RAG**: 多模型生成、自適應生成

## 🎯 核心功能

### 📝 統一核心模組 (integrated_core.py)
- **統一數據模型**: SearchResult、QueryContext、RAGResponse、AgentResponse
- **信心值控制器**: 多因素評估的統一信心值計算
- **基礎代理類別**: BaseAgent 抽象基類，內建監控和錯誤處理

### 🤖 智能代理人系統 (crew_agents.py)
- **WebSearchAgent**: OpenAI 驅動的網路搜尋備援
- **RAGExpertAgent**: 專業 RAG 檢索處理
- **SummaryExpertAgent**: 內容摘要生成
- **TagClassificationExpertAgent**: 智能標籤分類
- **TTSExpertAgent**: 語音合成服務
- **UserManagerAgent**: 用戶管理和體驗優化

### 🔍 層級化 RAG 處理 (hierarchical_rag_pipeline.py)
- **多層級處理**: 六層樹狀結構，逐層優化
- **並行處理**: 多個檢索策略並行執行
- **自適應生成**: 根據查詢類型選擇最佳生成策略
- **上下文壓縮**: 智能內容過濾和壓縮

### 🛠️ 統一向量處理器 (unified_vector_processor.py)
- **文本分塊**: UnifiedTextChunker 統一分塊策略
- **向量搜尋**: 整合 Milvus 向量資料庫
- **標籤管理**: 統一標籤提取和管理
- **混合搜尋**: 結合密集和稀疏檢索

### 🔧 增強向量搜尋 (enhanced_vector_search.py)
- **ML Pipeline 整合**: 協同過濾推薦
- **多策略搜尋**: 向量搜尋、協同過濾、Web 搜尋
- **智能備援**: 自動選擇最佳搜尋策略
- **結果融合**: 多來源結果智能融合

## 🚀 快速開始

### 環境設置
```bash
# 進入虛擬環境
source venv_podwise/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 基本使用

#### 1. 層級化 RAG 處理
```python
from rag_pipeline.core.hierarchical_rag_pipeline import HierarchicalRAGPipeline

# 創建 RAG 管道
pipeline = HierarchicalRAGPipeline()

# 處理查詢
response = await pipeline.process_query(
    query="推薦一些科技播客",
    user_id="user123"
)

print(f"回應: {response.content}")
print(f"信心度: {response.confidence}")
```

#### 2. 代理人管理器
```python
from rag_pipeline.core.crew_agents import AgentManager

# 創建代理人管理器
config = {
    'openai_api_key': 'your_api_key',
    'confidence_threshold': 0.7
}
manager = AgentManager(config)

# 處理查詢
response = await manager.process_query(
    query="推薦商業類的 podcast",
    user_id="user_001",
    category="商業"
)
```

#### 3. 向量搜尋
```python
from rag_pipeline.core.unified_vector_processor import UnifiedVectorProcessor

# 創建向量處理器
processor = UnifiedVectorProcessor(config)

# 執行混合搜尋
results = await processor.hybrid_search(
    query="科技播客推薦",
    top_k=5
)

for result in results:
    print(f"標題: {result.title}")
    print(f"相似度: {result.similarity}")
```

#### 4. 增強向量搜尋
```python
from rag_pipeline.tools.enhanced_vector_search import EnhancedVectorSearch

# 創建增強搜尋
search = EnhancedVectorSearch()

# 執行搜尋
results = await search.search(
    query="投資理財播客",
    user_id="user123",
    top_k=10
)

print(f"找到 {len(results)} 個結果")
for result in results:
    print(f"- {result.title} (信心度: {result.confidence})")
```

## 🔧 配置管理

### 環境變數設置
```bash
# OpenAI 配置
export OPENAI_API_KEY="your_api_key"

# 資料庫配置
export DATABASE_URL="postgresql://user:pass@host:port/db"
export POSTGRES_PASSWORD="your_password"

# 服務配置
export ML_PIPELINE_URL="http://ml-pipeline-service:8004"
export VECTOR_PIPELINE_URL="http://vector-pipeline-service:8003"
```

### 配置檔案 (config/hierarchical_rag_config.yaml)
```yaml
# 層級配置
levels:
  level1:
    query_processing:
      enable_rewrite: true
      enable_intent_detection: true
  level2:
    hybrid_search:
      dense_weight: 0.6
      sparse_weight: 0.4

# 向量搜尋配置
vector_search:
  milvus:
    host: "worker3"
    port: 19530
    collection_name: "podwise_vectors"
  
# 代理人配置
agents:
  web_search_expert:
    confidence_threshold: 0.7
    max_retries: 3
```

## 📁 檔案結構

```
rag_pipeline/
├── __init__.py
├── main.py                          # 主程式入口
├── Dockerfile                       # Docker 容器配置
├── requirements.txt                 # 依賴包清單
├── env.local                       # 本地環境變數
├── app/
│   ├── __init__.py
│   └── main_crewai.py              # CrewAI 主程式
├── config/
│   ├── __init__.py
│   ├── agent_roles_config.py       # 代理人角色配置
│   ├── integrated_config.py        # 整合配置
│   ├── prompt_templates.py         # 提示模板
│   └── hierarchical_rag_config.yaml # RAG 配置
├── core/
│   ├── __init__.py
│   ├── integrated_core.py          # 統一核心模組
│   ├── crew_agents.py              # 代理人系統
│   ├── hierarchical_rag_pipeline.py # 層級化 RAG
│   ├── unified_vector_processor.py  # 統一向量處理
│   ├── agent_manager.py            # 代理人管理器
│   ├── api_models.py               # API 數據模型
│   ├── chat_history_service.py     # 聊天歷史服務
│   ├── content_categorizer.py      # 內容分類器
│   ├── prompt_processor.py         # 提示處理器
│   └── qwen_llm_manager.py         # Qwen LLM 管理器
├── tools/
│   ├── __init__.py
│   ├── enhanced_vector_search.py   # 增強向量搜尋
│   ├── podcast_formatter.py        # 播客格式化
│   └── train_word2vec_model.py     # Word2Vec 模型訓練
├── scripts/
│   ├── __init__.py
│   ├── audio_transcription_pipeline.py # 音頻轉錄
│   └── tag_processor.py            # 標籤處理器
└── evaluation/
    ├── __init__.py
    ├── README.md                   # 評估說明
    └── rag_evaluator.py            # RAG 評估器
```

## 🔄 工作流程

### 1. 正常處理流程
```
用戶查詢 → 查詢處理 → 混合搜尋 → 檢索增強 → 重新排序 → 上下文壓縮 → 混合式RAG → 回應生成
```

### 2. 備援處理流程
```
用戶查詢 → RAG 檢索 → 信心度評估 → 信心度 < 0.7 → Web 搜尋 → OpenAI 處理 → 回應生成
```

### 3. 代理人協作流程
```
查詢接收 → 領導者層分析 → 類別專家層處理 → 功能專家層執行 → 結果整合 → 最終回應
```

## 🎯 整合成果

### 已整合的重複功能
1. **標籤管理**: 統一標籤提取和管理策略
2. **文本分塊**: 統一文本分塊介面和邏輯
3. **向量搜尋**: 整合多種向量搜尋策略
4. **Milvus 操作**: 統一向量資料庫操作
5. **信心值計算**: 統一信心值評估邏輯

### 已刪除的重複檔案
- `unified_models.py` → 整合到 `integrated_core.py`
- `confidence_controller.py` → 整合到 `integrated_core.py`
- `base_agent.py` → 整合到 `integrated_core.py`
- `web_search_tool.py` → 整合到 `crew_agents.py`
- 各種測試和範例檔案

## 🧪 測試和評估

### 架構驗證
```bash
# 執行架構驗證
python test_unified_architecture.py
```

### RAG 評估
```bash
# 執行 RAG 評估
python evaluation/rag_evaluator.py
```

### 代理人配置測試
```bash
# 測試代理人配置整合
python test_agent_config_integration.py
```

## 📊 效能優化

### 並行處理
- 多個代理人並行執行
- 異步 I/O 操作
- 批次處理優化

### 快取機制
- Redis 查詢結果快取
- 向量搜尋結果快取
- 代理人回應快取

### 監控指標
- 處理時間統計
- 信心值分佈
- 錯誤率追蹤
- 各層級使用統計

## 🔍 故障排除

### 常見問題

1. **OpenAI API 錯誤**
   ```bash
   # 檢查 API 金鑰
   echo $OPENAI_API_KEY
   
   # 測試 API 連接
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

2. **Milvus 連接失敗**
   ```bash
   # 檢查 Milvus 服務
   curl http://worker3:19530/health
   
   # 檢查集合狀態
   python -c "from pymilvus import connections; connections.connect('default', host='worker3', port='19530')"
   ```

3. **ML Pipeline 整合問題**
   ```bash
   # 檢查 ML Pipeline 服務
   curl http://ml-pipeline-service:8004/health
   
   # 測試協同過濾
   curl -X POST http://ml-pipeline-service:8004/recommend \
        -H "Content-Type: application/json" \
        -d '{"user_id": "test", "top_k": 5}'
   ```

## 🚀 部署指南

### Docker 部署
```bash
# 構建鏡像
docker build -t rag-pipeline .

# 運行容器
docker run -p 8004:8004 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e DATABASE_URL=$DATABASE_URL \
  rag-pipeline
```

### Kubernetes 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-pipeline
  template:
    metadata:
      labels:
        app: rag-pipeline
    spec:
      containers:
      - name: rag-pipeline
        image: rag-pipeline:latest
        ports:
        - containerPort: 8004
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
```

## 🤝 貢獻指南

1. **代碼風格**: 遵循 PEP 8 和 Google Python Style Guide
2. **測試覆蓋**: 新功能需要添加相應測試
3. **文檔更新**: 更新相關文檔和註釋
4. **OOP 原則**: 遵循 SOLID 原則
5. **Clean Code**: 遵循 Google Clean Code 標準

## 📄 授權

MIT License

---

**Podwise Team** | 版本: 2.0.0

## CrewAI 整合指南

### 配置系統
所有代理人的角色定義都在 `config/agent_roles_config.py` 中統一管理，使用 `AgentRoleConfig` 數據類別進行配置。

### Web Search Expert 詳細說明
- **角色**: 網路搜尋備援專家
- **觸發條件**: 當 RAG 檢索信心度 < 0.7 時啟動
- **主要功能**: OpenAI 搜尋、結果格式化、備援日誌記錄

### 最佳實踐
- ✅ 所有代理人都應該載入 `role_config`
- ✅ 使用配置系統的參數設定
- ✅ 在 `crew_agents.py` 中統一管理
- ❌ 不要創建獨立的代理人檔案

通過統一的配置系統，確保所有代理人都遵循相同的架構模式，配置管理集中化和標準化，系統具有良好的可維護性和擴展性。 