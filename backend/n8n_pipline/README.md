# Podwise N8N Pipeline

## 概述

Podwise N8N Pipeline 是工作流程自動化服務模組，使用 N8N 平台進行數據採集和處理自動化。採用 OOP 設計原則，提供統一的工作流程管理介面。

## 架構設計

### 核心組件

#### 1. 工作流程管理器 (Workflow Manager)
- **職責**：核心工作流程管理功能
- **實現**：`WorkflowManager` 類別
- **功能**：
  - 工作流程定義
  - 流程執行控制
  - 狀態監控

#### 2. 數據採集器 (Data Ingestion)
- **職責**：數據採集和處理
- **實現**：`DataIngestion` 類別
- **功能**：
  - 自動數據採集
  - 數據清理和轉換
  - 數據驗證

#### 3. 觸發器管理器 (Trigger Manager)
- **職責**：工作流程觸發管理
- **實現**：`TriggerManager` 類別
- **功能**：
  - 觸發條件設定
  - 自動觸發控制
  - 觸發歷史追蹤

#### 4. 執行監控器 (Execution Monitor)
- **職責**：工作流程執行監控
- **實現**：`ExecutionMonitor` 類別
- **功能**：
  - 執行狀態監控
  - 性能指標收集
  - 錯誤處理和重試

## 統一服務管理器

### N8NPipelineManager 類別
- **職責**：整合所有 N8N 功能，提供統一的 OOP 介面
- **主要方法**：
  - `create_workflow()`: 創建工作流程
  - `execute_workflow()`: 執行工作流程
  - `monitor_execution()`: 監控執行
  - `health_check()`: 健康檢查

### 工作流程執行流程
1. **流程定義**：定義工作流程結構
2. **觸發設定**：設定觸發條件
3. **執行監控**：監控執行狀態
4. **結果處理**：處理執行結果
5. **錯誤處理**：處理執行錯誤

## 配置系統

### N8N 配置
- **檔案**：`config/n8n_config.py`
- **功能**：
  - N8N 連接配置
  - 工作流程參數
  - 執行策略設定

### 採集配置
- **檔案**：`config/ingestion_config.py`
- **功能**：
  - 數據源配置
  - 採集頻率設定
  - 數據格式定義

## 數據模型

### 核心數據類別
- `WorkflowDefinition`: 工作流程定義
- `ExecutionStatus`: 執行狀態
- `TriggerConfig`: 觸發配置
- `IngestionResult`: 採集結果

### 工廠函數
- `create_workflow_definition()`: 創建工作流程定義
- `create_execution_status()`: 創建執行狀態
- `create_trigger_config()`: 創建觸發配置

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的工作流程功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的工作流程類型
- 可擴展的觸發機制

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的執行引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有管理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合 N8N 管道管理器
  - 工作流程控制
  - 健康檢查和監控

### 使用方式
```python
# 創建 N8N 管道實例
from n8n_pipeline.n8n_pipeline_manager import N8NPipelineManager

manager = N8NPipelineManager()

# 創建工作流程
workflow = await manager.create_workflow(
    name="podcast_ingestion",
    triggers=["schedule", "webhook"],
    nodes=["data_collection", "data_cleaning", "data_storage"]
)

# 執行工作流程
execution_result = await manager.execute_workflow(
    workflow_id=workflow.id,
    parameters={"source": "rss_feed"}
)

# 監控執行
monitoring_result = await manager.monitor_execution(
    execution_id=execution_result.id
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證 N8N 連接
- 監控工作流程性能
- 檢查觸發器狀態

### 性能指標
- 工作流程執行時間
- 觸發頻率統計
- 錯誤率監控
- 資源使用效率

## 技術棧

- **框架**：FastAPI
- **工作流程**：N8N
- **數據處理**：Pandas, NumPy
- **自動化**：Selenium, Requests
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-n8n-pipeline .

# 運行容器
docker run -p 8013:8013 podwise-n8n-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/workflows` - 創建工作流程
- `POST /api/v1/workflows/{id}/execute` - 執行工作流程
- `GET /api/v1/executions` - 獲取執行狀態
- `GET /api/v1/statistics` - 統計資訊

## 架構優勢

1. **自動化**：提供完整的工作流程自動化
2. **可擴展性**：支援新的工作流程和觸發方式
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的執行監控和錯誤處理
5. **一致性**：統一的工作流程定義和執行介面 