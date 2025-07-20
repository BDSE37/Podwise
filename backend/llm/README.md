# Podwise LLM Pipeline

## 概述

Podwise LLM Pipeline 是大語言模型服務模組，負責提供智能對話和文本生成服務。支援多種 LLM 模型，提供統一的 OOP 介面。

## 架構設計

### 核心組件

#### 1. 模型管理器 (Model Manager)
- **職責**：管理不同的 LLM 模型
- **實現**：`ModelManager` 類別
- **功能**：
  - 模型載入和切換
  - 模型性能優化
  - 模型版本管理

#### 2. 對話管理器 (Conversation Manager)
- **職責**：管理對話上下文和歷史
- **實現**：`ConversationManager` 類別
- **功能**：
  - 對話歷史管理
  - 上下文維護
  - 會話狀態追蹤

#### 3. 提示詞管理器 (Prompt Manager)
- **職責**：管理提示詞模板和優化
- **實現**：`PromptManager` 類別
- **功能**：
  - 提示詞模板管理
  - 動態提示詞生成
  - 提示詞優化

#### 4. 回應處理器 (Response Processor)
- **職責**：處理和優化模型回應
- **實現**：`ResponseProcessor` 類別
- **功能**：
  - 回應格式化
  - 內容過濾
  - 品質檢查

## 統一服務管理器

### LLMPipelineManager 類別
- **職責**：整合所有 LLM 功能，提供統一的 OOP 介面
- **主要方法**：
  - `generate_response()`: 生成回應
  - `start_conversation()`: 開始對話
  - `health_check()`: 健康檢查
  - `get_model_info()`: 獲取模型資訊

### 對話流程
1. **對話初始化**：建立新的對話會話
2. **上下文處理**：處理對話歷史和上下文
3. **提示詞生成**：生成優化的提示詞
4. **模型推理**：使用 LLM 生成回應
5. **回應處理**：處理和優化回應內容

## 配置系統

### LLM 配置
- **檔案**：`config/llm_config.py`
- **功能**：
  - 模型配置
  - 對話設定
  - 性能參數

### 模型配置
- **檔案**：`config/model_config.py`
- **功能**：
  - 模型參數設定
  - 推理配置
  - 資源管理

## 數據模型

### 核心數據類別
- `Conversation`: 對話會話
- `Message`: 對話訊息
- `ModelResponse`: 模型回應
- `PromptTemplate`: 提示詞模板

### 工廠函數
- `create_conversation()`: 創建對話會話
- `create_message()`: 創建訊息
- `create_model_response()`: 創建模型回應

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的 LLM 功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的 LLM 模型
- 可擴展的對話流程

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的 LLM 引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有模型都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合 LLM 管道管理器
  - 對話服務控制
  - 健康檢查和模型資訊

### 使用方式
```python
# 創建 LLM 管道實例
from core.llm_pipeline_manager import LLMPipelineManager

pipeline = LLMPipelineManager()

# 開始對話
conversation = await pipeline.start_conversation(
    user_id="Podwise0001",
    model="qwen-3.5"
)

# 生成回應
response = await pipeline.generate_response(
    conversation_id=conversation.id,
    message="推薦一些投資理財的播客",
    context="我對投資理財很感興趣"
)

# 獲取模型資訊
model_info = pipeline.get_model_info()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證模型可用性
- 監控推理性能
- 檢查記憶體使用

### 性能指標
- 回應生成時間
- 模型準確率
- 對話品質
- 資源使用統計

## 技術棧

- **框架**：FastAPI
- **LLM 引擎**：Ollama, OpenAI, Hugging Face
- **對話管理**：Redis, PostgreSQL
- **提示詞工程**：LangChain, PromptFlow
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-llm-pipeline .

# 運行容器
docker run -p 8005:8005 podwise-llm-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/chat` - 對話生成
- `POST /api/v1/conversation/start` - 開始對話
- `GET /api/v1/models` - 獲取模型資訊
- `GET /api/v1/statistics` - 統計資訊

## 架構優勢

1. **智能對話**：支援上下文感知的智能對話
2. **多模型支援**：支援多種 LLM 模型
3. **可擴展性**：支援新的模型和對話策略
4. **可維護性**：清晰的模組化設計
5. **一致性**：統一的數據模型和介面設計 