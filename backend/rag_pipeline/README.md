# Podwise RAG Pipeline

## 概述

Podwise RAG Pipeline 採用三層 CrewAI 架構，整合 MCP (Model Context Protocol) 增強功能，遵循 Google Clean Code 原則，提供統一的 OOP 介面。

## 三層 CrewAI 架構

### 第一層：領導者層 (Leader Layer)
- **角色**：決策統籌長 (Podwise Chief Decision Orchestrator)
- **職責**：協調各層專家代理、整合最終決策、處理跨類別請求、品質控制和備援機制
- **實現**：`LeaderAgent` 類別

### 第二層：類別專家層 (Category Expert Layer)
- **商業智慧專家** (Business Intelligence Expert)
  - 處理投資理財、創業、職場等商業相關查詢
  - 基於 `total_rating` 進行內容排序
  - 實現：`BusinessExpertAgent` 類別

- **教育成長專家** (Educational Growth Strategist)
  - 處理學習、成長、職涯等教育相關查詢
  - 評估學習價值和適用性
  - 實現：`EducationExpertAgent` 類別

### 第三層：功能專家層 (Functional Expert Layer)
- **智能檢索專家** (Intelligent Retrieval Expert) - `RAGExpertAgent`
- **用戶管理專家** (User Manager Agent) - `UserManagerAgent`
- **Web 搜尋專家** (Web Search Expert) - `WebSearchAgent`
- **摘要專家** (Summary Expert Agent) - `SummaryExpertAgent`
- **標籤分類專家** (Tag Classification Expert Agent) - `TagClassificationExpertAgent`
- **TTS 專家** (TTS Expert Agent) - `TTSExpertAgent`

## 統一服務管理器

### UnifiedServiceManager 類別
- **職責**：整合所有功能模組，提供統一的 OOP 介面
- **主要方法**：
  - `process_query()`: 主要查詢處理入口
  - `_process_with_three_layer_architecture()`: 三層架構處理流程
  - `_enhance_with_mcp()`: MCP 增強功能
  - `health_check()`: 系統健康檢查

### 處理流程
1. **語意分析**：使用智能檢索專家進行查詢分析
2. **功能專家層**：用戶管理、標籤分類、RAG 檢索
3. **類別專家層**：根據分類調用對應專家
4. **領導者層**：整合結果並使用 MCP 增強
5. **回應生成**：生成最終回應

## MCP 整合

### MCP 增強功能
- **位置**：`utils/mcp_integration.py`
- **功能**：工具註冊和管理、資源緩存、回應增強、健康檢查

### 整合點
- 在領導者層決策後自動觸發 MCP 增強
- 增強原始回應內容的上下文和準確性
- 提供額外的工具和資源支援

## 配置系統

### Agent Roles Configuration
- **檔案**：`config/agent_roles_config.py`
- **功能**：定義所有代理的角色、目標、技能、設定優先級和信心度閾值

### Prompt Templates
- **檔案**：`config/prompt_templates.py`
- **功能**：系統層級、分類層級、專家評估、領導者決策、回答生成提示詞

## 統一數據模型

### 核心數據類別
- `RAGResponse`: RAG 回應數據
- `UserQuery`: 用戶查詢數據
- `AgentResponse`: 代理回應數據
- `SearchResult`: 搜尋結果數據
- `ProcessingMetrics`: 處理指標數據
- `SystemHealth`: 系統健康狀態數據

### 工廠函數
- `create_rag_response()`: 創建 RAG 回應
- `create_agent_response()`: 創建代理回應
- `create_user_query()`: 創建用戶查詢
- `create_processing_metrics()`: 創建處理指標

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個代理類別只負責特定功能
- 服務管理器只負責協調和整合
- 數據模型只負責數據封裝

### 開放封閉原則 (OCP)
- 基礎代理類別可擴展但不可修改
- 新的專家代理可以輕鬆添加
- 配置系統支援動態調整

### 依賴反轉原則 (DIP)
- 高層模組不依賴低層模組
- 依賴抽象而非具體實現
- 使用依賴注入進行解耦

### 介面隔離原則 (ISP)
- 每個代理都有明確的介面
- 避免不必要的依賴
- 提供精確的方法簽名

### 里氏替換原則 (LSP)
- 所有代理都可以替換其基類
- 保持行為一致性
- 支援多態性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合統一服務管理器
  - 處理 TTS 合成
  - 健康檢查和系統資訊

### 使用方式
```python
# 創建服務實例
pipeline = PodwiseRAGPipeline()

# 處理查詢
response = await pipeline.process_query(
    query="推薦投資理財相關的播客",
    user_id="Podwise0001"
)

# 語音合成
audio_data = await pipeline.synthesize_speech(
    text=response.content,
    voice="podrina"
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 計算健康百分比
- 提供詳細的組件資訊
- 支援運行時間和資源使用追蹤

### 處理指標
- 追蹤處理步驟
- 記錄錯誤和警告
- 監控性能指標
- 提供統計資訊

## 架構優勢

1. **可擴展性**：三層架構支援輕鬆添加新的專家代理
2. **可維護性**：清晰的職責分離和模組化設計
3. **可測試性**：每個組件都可以獨立測試
4. **一致性**：統一的數據模型和介面設計
5. **增強性**：MCP 整合提供額外的工具和資源支援

## 技術棧

- **框架**：FastAPI
- **架構**：三層 CrewAI
- **數據庫**：PostgreSQL, Milvus
- **向量模型**：bge-m3
- **LLM**：Qwen 3.5
- **監控**：Langfuse
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-rag-pipeline .

# 運行容器
docker run -p 8000:8000 podwise-rag-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/query` - 處理查詢
- `POST /api/v1/tts/synthesize` - 語音合成
- `GET /api/v1/system-info` - 系統資訊
