# 🎧 Podwise RAG Pipeline - CrewAI + LangChain + LLM 完整工作流程

## 📋 架構總覽

本系統實現了一套完整的智能 Podcast 推薦系統，整合了 CrewAI 多代理人架構、LangChain 工具生態系統和多種 LLM 模型，提供高互動性、高可解釋性的推薦流程。

### 🔄 完整工作流程

```
用戶查詢 → 三層 CrewAI 架構 → LangChain 工具 → LLM 生成 → 結果返回
    │
    ├─ 第一層：領導者層 (Leader Layer)
    │   ├─ 協調整體流程
    │   ├─ 判斷查詢類別
    │   └─ 分派任務給專家
    │
    ├─ 第二層：類別專家層 (Category Expert Layer)
    │   ├─ 商業專家：處理商業類查詢
    │   ├─ 教育專家：處理教育類查詢
    │   └─ 語意專家：處理泛用查詢
    │
    ├─ 第三層：功能專家層 (Functional Expert Layer)
    │   ├─ RAG 專家：語意檢索
    │   ├─ 摘要專家：內容摘要
    │   ├─ 評分專家：質量評估
    │   ├─ TTS 專家：語音合成
    │   └─ 用戶管理專家：用戶管理
    │
    ├─ LangChain 工具整合
    │   ├─ 統一 LLM 工具
    │   ├─ 向量搜尋工具
    │   ├─ 關鍵詞映射工具
    │   └─ KNN 推薦工具
    │
    └─ LLM 模型管理
        ├─ Qwen3 系列模型
        ├─ DeepSeek 模型
        ├─ 模型健康檢查
        └─ 自動回退機制
```

## 🧱 核心組件

### 🔹 CrewAI 三層架構

#### 第一層：領導者層 (Leader Layer)
- **Podcast 推薦總監（Leader Agent）**
  - 協調整體推薦流程
  - 判斷請求是否為跨類別（Multi-tag）
  - 呼叫 RAG Expert 統一檢索
  - 將每筆節目分派至類別專家評估信心值
  - 根據排序規則產生最終推薦

#### 第二層：類別專家層 (Category Expert Layer)

| 專家名稱 | 商業類別專家 | 教育類別專家 | 語意專家 |
|----------|-------------|-------------|----------|
| 🎯 職責 | 推薦商業類 Podcast | 推薦教育類 Podcast | 分析泛用語意與冷門主題 |
| 🧰 工具 | 商業知識庫、信心值標準 (>0.7) | 教育知識庫、信心值標準 (>0.7) | 語意標籤庫、分類相似度規則 |
| 📨 輸入 | 用戶偏好、類別向量檢索結果 | 用戶偏好、類別向量檢索結果 | 用戶輸入語意 |
| 📤 輸出 | 篩選信心值 > 0.7 的節目，依更新時間排序，若信心值相同 → 依 RSS ID 升冪排序 |

#### 第三層：功能專家層 (Functional Expert Layer)

| 專家模組 | 職責說明 | LangChain 工具 |
|----------|----------|----------------|
| 🔍 RAG Expert | 語意檢索和向量搜尋 | EnhancedVectorSearchTool |
| 🧠 Keyword Mapper | 使用關聯詞庫分類用戶輸入 | KeywordMapper |
| 📊 KNN Recommender | 基於向量相似度的推薦 | KNNRecommender |
| ✏️ Summary Expert | 提供節目摘要 | UnifiedLLMTool |
| 🗣️ TTS Expert | 提供語音播放回應 | TTS 相關工具 |
| 👤 User Manager | 管理用戶登入、偏好設定 | ChatHistoryService |

### 🔹 LangChain 工具生態系統

#### 統一 LLM 工具 (UnifiedLLMTool)
```python
# 支援多種 LLM 模型
- Qwen3 系列模型
- DeepSeek 模型
- 自動模型切換
- 健康檢查機制
- 異步處理支援
```

#### 向量搜尋工具 (EnhancedVectorSearchTool)
```python
# 提供高級向量搜尋功能
- 多維度相似度計算
- 類別過濾
- 結果排序
- 性能優化
```

#### 關鍵詞映射工具 (KeywordMapper)
```python
# 智能查詢分類
- 商業類別關鍵詞庫
- 教育類別關鍵詞庫
- 信心值計算
- 推理說明生成
```

#### KNN 推薦工具 (KNNRecommender)
```python
# 基於向量相似度的推薦
- K-Nearest Neighbors 算法
- 多種相似度度量
- 類別過濾
- 推薦結果分析
```

### 🔹 LLM 模型管理

#### Qwen3 LLM 管理器 (Qwen3LLMManager)
```python
# 支援多種 LLM 模型，具備優先級和備援機制
- Qwen2.5-Taiwan (第一優先，台灣優化版本)
- Qwen3:8b (第二優先，主要模型)
- OpenAI GPT-3.5 (備援，需要 API Key)
- OpenAI GPT-4 (最後備援，需要 API Key)
- 模型健康檢查
- 自動回退機制
- 優先級順序管理
```

#### 統一 LLM 工具 (UnifiedLLMTool)
```python
# 多模型整合
- 模型提供者抽象
- 異步文本生成
- 提示格式化
- 結果提取
```

## 🚀 快速開始

### 1. 環境準備

```bash
# 進入 RAG Pipeline 目錄
cd backend/rag_pipeline

# 安裝依賴
pip install -r requirements.txt
```

### 2. 使用 Podman 部署

```bash
# 執行部署腳本
chmod +x deploy/podman/rag-pipeline-crewai.sh
./deploy/podman/rag-pipeline-crewai.sh
```

### 3. 測試功能

```bash
# 執行簡化整合測試
python test_crewai_langchain_simple.py

# 執行完整整合測試
python test_crewai_langchain_integration.py
```

### 4. API 使用

#### 用戶驗證
```bash
curl -X POST http://localhost:8004/api/v1/validate-user \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "test_user"}'
```

#### 智能查詢
```bash
curl -X POST http://localhost:8004/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "query": "我想了解股票投資和理財規劃"
  }'
```

#### 查看聊天歷史
```bash
curl http://localhost:8004/api/v1/chat-history/test_user
```

## 🛠️ 核心組件詳解

### Keyword Mapper
- **檔案**: `tools/keyword_mapper.py`
- **功能**: 使用關聯詞庫分類用戶輸入
- **支援類別**: 商業、教育、雙類別
- **信心值計算**: 基於關鍵詞匹配和密度
- **LangChain 整合**: 作為 LangChain 工具使用

### KNN 推薦器
- **檔案**: `tools/knn_recommender.py`
- **算法**: K-Nearest Neighbors
- **相似度度量**: Cosine Similarity, Euclidean, Manhattan
- **支援過濾**: 類別過濾、信心值閾值
- **LangChain 整合**: 提供標準化介面

### 三層代理人架構
- **檔案**: `core/crew_agents.py`
- **架構**: Leader → Category Experts → Functional Experts
- **協調模式**: 層級式協調
- **決策機制**: 信心值評估和排序
- **CrewAI 整合**: 使用 CrewAI 框架

### 統一 LLM 工具
- **檔案**: `tools/unified_llm_tool.py`
- **支援模型**: Qwen3, DeepSeek
- **功能**: 文本生成、模型管理、健康檢查
- **LangChain 整合**: 繼承 BaseTool
- **異步支援**: 完整的異步處理

### Qwen3 LLM 管理器
- **檔案**: `core/qwen3_llm_manager.py`
- **模型管理**: 多模型切換、健康檢查
- **回退機制**: 自動模型切換
- **指標監控**: 使用統計和性能指標
- **配置管理**: 靈活的模型配置

## 📊 推薦算法

### KNN 推薦流程
1. **向量化**: 將用戶查詢轉換為向量表示
2. **相似度計算**: 使用多種相似度度量方法
3. **鄰居選擇**: 選擇 K 個最相似的 Podcast
4. **類別過濾**: 根據分類結果過濾相關類別
5. **排序**: 按相似度和更新時間排序
6. **返回**: 返回 Top-N 推薦結果

### 信心值評估
- **商業類別**: 基於財經關鍵詞匹配
- **教育類別**: 基於學習成長關鍵詞匹配
- **閾值**: 0.7（低於此值會觸發重新檢索）
- **排序規則**: 信心值 → 更新時間 → RSS ID

### CrewAI 決策流程
1. **用戶查詢接收**: Leader Agent 接收用戶查詢
2. **類別判定**: 使用 Keyword Mapper 分類查詢
3. **專家分派**: 根據類別分派給對應專家
4. **內容檢索**: RAG Expert 執行語意檢索
5. **專家評估**: 類別專家評估內容質量
6. **結果整合**: Leader Agent 整合專家建議
7. **最終決策**: 生成最終推薦結果

## 🔧 配置說明

### 環境變數
```bash
# 資料庫配置
MONGODB_URI=mongodb://worker3:27017/podwise
POSTGRES_HOST=worker3
POSTGRES_PORT=5432

# LLM 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:8b

# OpenAI 備援配置 (可選)
OPENAI_API_KEY=your_openai_api_key_here

# 向量搜尋配置
MILVUS_HOST=worker3
MILVUS_PORT=19530

# CrewAI 配置
AGENT_CONFIDENCE_THRESHOLD=0.7
AGENT_MAX_PROCESSING_TIME=30.0
```

### 配置檔案
- **主要配置**: `config/integrated_config.py`
- **RAG 配置**: `config/hierarchical_rag_config.yaml`
- **環境配置**: `env.local`

## 🤖 LLM 優先級與備援機制

### 模型優先級順序
系統按照以下優先級順序選擇 LLM 模型：

1. **Qwen2.5-Taiwan** (第一優先)
   - 台灣優化版本，針對繁體中文優化
   - 模型名稱: `weiren119/Qwen2.5-Taiwan-8B-Instruct`
   - 系統提示: 針對台灣地區優化的專業 AI 助手

2. **Qwen3:8b** (第二優先)
   - 標準 Qwen3 模型
   - 模型名稱: `Qwen/Qwen2.5-8B-Instruct`
   - 系統提示: 擅長中文和英文對話的專業 AI 助手

3. **OpenAI GPT-3.5** (備援)
   - 需要設置 `OPENAI_API_KEY` 環境變數
   - 模型名稱: `gpt-3.5-turbo`
   - 只有在前面模型都不可用時才會使用

4. **OpenAI GPT-4** (最後備援)
   - 需要設置 `OPENAI_API_KEY` 環境變數
   - 模型名稱: `gpt-4`
   - 最高品質但成本較高的備援選項

### 備援機制運作流程
```python
# 1. 檢查當前模型健康狀態
if current_model.is_healthy():
    return current_model

# 2. 按優先級順序檢查其他模型
for model in priority_models:
    if model.is_available() and model.is_healthy():
        switch_to_model(model)
        return model

# 3. 如果所有模型都不可用，使用預設模型
return default_model
```

### 測試 LLM 備援機制
```bash
# 執行 LLM 備援測試
python test_llm_fallback.py

# 測試結果包含：
# - 模型可用性檢查
# - 優先級順序驗證
# - 備援機制測試
# - OpenAI 配置檢查
# - 台灣模型優先級確認
```

### 配置 OpenAI 備援
1. **設置環境變數**:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

2. **或在 .env 檔案中設置**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **驗證配置**:
   ```bash
   python -c "
   from config.integrated_config import get_config
   config = get_config()
   print(f'OpenAI 配置: {bool(config.api.openai_api_key)}')
   "
   ```

## 📈 監控與日誌

### 健康檢查
```bash
curl http://localhost:8004/health
```

### 系統資訊
```bash
curl http://localhost:8004/api/v1/system-info
```

### LLM 模型狀態
```bash
curl http://localhost:8004/api/v1/llm-status
```

### 容器監控
```bash
# 查看容器狀態
podman ps

# 查看日誌
podman logs -f podwise-rag-crewai

# 進入容器
podman exec -it podwise-rag-crewai bash
```

### LLM 模型監控
```bash
# 檢查模型健康狀態
curl http://localhost:8004/api/v1/llm/health

# 查看模型指標
curl http://localhost:8004/api/v1/llm/metrics
```

## 🧪 測試

### 單元測試
```bash
# 測試 Keyword Mapper
python -c "from tools.keyword_mapper import KeywordMapper; mapper = KeywordMapper(); print(mapper.categorize_query('我想了解股票投資'))"

# 測試 KNN 推薦器
python -c "from tools.knn_recommender import KNNRecommender; print('KNN 推薦器測試完成')"

# 測試統一 LLM 工具
python -c "from tools.unified_llm_tool import get_unified_llm_tool; tool = get_unified_llm_tool(); print(tool.get_available_models())"
```

### 整合測試
```bash
# 執行簡化整合測試
python test_crewai_langchain_simple.py

# 執行完整整合測試
python test_crewai_langchain_integration.py
```

### 端到端測試
```bash
# 測試完整工作流程
curl -X POST http://localhost:8004/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "query": "我想了解股票投資和理財規劃"
  }'
```

## 🔄 擴展開發

### 添加新的類別專家
1. 在 `core/crew_agents.py` 中創建新的專家類別
2. 在 `tools/keyword_mapper.py` 中添加對應關鍵詞
3. 更新配置檔案中的專家配置
4. 測試新專家的功能

### 自定義推薦算法
1. 繼承 `KNNRecommender` 類別
2. 實作自定義的相似度計算方法
3. 更新推薦邏輯
4. 整合到主應用程式

### 添加新的 LLM 模型
1. 在 `tools/unified_llm_tool.py` 中創建新的模型提供者
2. 繼承 `BaseLLMProvider` 類別
3. 實作模型載入和文本生成方法
4. 更新模型配置

### 添加新的 LangChain 工具
1. 在 `tools/` 目錄下創建新工具
2. 繼承 LangChain 的 `BaseTool` 類別
3. 實作 `_run` 和 `_arun` 方法
4. 在主應用程式中整合新工具

## 📝 注意事項

1. **依賴管理**: 確保所有 Python 依賴都已正確安裝
2. **資料庫連接**: 確保 MongoDB、PostgreSQL、Milvus 等服務正常運行
3. **向量模型**: 確保 BGE-M3 等嵌入模型已正確載入
4. **LLM 模型**: 確保 Qwen3 等 LLM 模型已正確配置
5. **記憶體使用**: 監控容器記憶體使用情況，避免 OOM
6. **日誌管理**: 定期清理日誌檔案，避免磁碟空間不足
7. **模型健康檢查**: 定期檢查 LLM 模型健康狀態
8. **性能監控**: 監控系統性能和響應時間

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 授權

本專案採用 MIT 授權條款。

## 📞 支援

如有問題或建議，請提交 Issue 或聯繫開發團隊。

---

## 🎯 總結

本系統成功整合了 CrewAI 多代理人架構、LangChain 工具生態系統和多種 LLM 模型，提供了一個完整的智能 Podcast 推薦解決方案。通過三層代理人架構，系統能夠智能地處理用戶查詢，並提供高質量的推薦結果。LangChain 工具的整合使得系統更加模組化和可擴展，而多種 LLM 模型的支援確保了系統的穩定性和性能。 