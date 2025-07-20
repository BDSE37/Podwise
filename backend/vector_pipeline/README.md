# Podwise Vector Pipeline

## 概述

Podwise Vector Pipeline 是專門處理向量化數據的模組，負責將文本內容轉換為向量表示，並提供高效的向量檢索服務。採用 OOP 設計原則，提供統一的介面。

## 架構設計

### 核心組件

#### 1. 數據管理器 (Data Manager)
- **職責**：管理向量數據的載入、處理和存儲
- **實現**：`DataManager` 類別
- **功能**：
  - 批量數據處理
  - 數據驗證和清理
  - 進度追蹤和錯誤處理

#### 2. 向量處理器 (Vector Processor)
- **職責**：文本向量化和嵌入處理
- **實現**：`VectorProcessor` 類別
- **功能**：
  - 文本預處理
  - 向量化轉換
  - 嵌入模型管理

#### 3. 檢索引擎 (Retrieval Engine)
- **職責**：向量檢索和相似度計算
- **實現**：`RetrievalEngine` 類別
- **功能**：
  - 向量索引管理
  - 相似度搜索
  - 結果排序和過濾

#### 4. 批處理器 (Batch Processor)
- **職責**：大規模數據批處理
- **實現**：`BatchProcessor` 類別
- **功能**：
  - 分批處理控制
  - 記憶體優化
  - 並行處理支援

## 統一服務管理器

### VectorPipelineManager 類別
- **職責**：整合所有向量處理功能，提供統一的 OOP 介面
- **主要方法**：
  - `process_batch()`: 批量處理入口
  - `search_vectors()`: 向量檢索
  - `get_statistics()`: 獲取統計資訊
  - `health_check()`: 健康檢查

### 處理流程
1. **數據載入**：從多個來源載入文本數據
2. **預處理**：清理和標準化文本
3. **向量化**：使用嵌入模型轉換為向量
4. **索引建立**：建立向量索引
5. **存儲**：將向量存儲到向量數據庫

## 配置系統

### 向量配置
- **檔案**：`config/config.py`
- **功能**：
  - 嵌入模型配置
  - 向量維度設定
  - 批處理參數
  - 數據庫連接配置

### 處理配置
- **檔案**：`config/config_manager.py`
- **功能**：
  - 動態配置管理
  - 環境變數處理
  - 配置驗證

## 數據模型

### 核心數據類別
- `VectorData`: 向量數據封裝
- `SearchResult`: 檢索結果
- `ProcessingMetrics`: 處理指標
- `BatchStatus`: 批處理狀態

### 工廠函數
- `create_vector_data()`: 創建向量數據
- `create_search_result()`: 創建檢索結果
- `create_processing_metrics()`: 創建處理指標

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的向量處理功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的嵌入模型和檢索算法
- 可擴展的處理流程

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的向量數據庫

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有處理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合向量處理管理器
  - 批量處理控制
  - 健康檢查和統計資訊

### 使用方式
```python
# 創建向量處理實例
from core.vector_pipeline_manager import VectorPipelineManager

pipeline = VectorPipelineManager()

# 批量處理
result = await pipeline.process_batch(
    data_source="stage4_embedding_prep",
    batch_size=1000
)

# 向量檢索
search_results = await pipeline.search_vectors(
    query_vector=query_vector,
    top_k=10,
    similarity_threshold=0.7
)

# 獲取統計資訊
stats = pipeline.get_statistics()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證數據庫連接
- 監控記憶體使用
- 檢查嵌入模型狀態

### 處理指標
- 批處理進度追蹤
- 處理時間統計
- 錯誤率和成功率
- 記憶體使用監控

## 技術棧

- **框架**：FastAPI
- **向量數據庫**：Milvus
- **嵌入模型**：BGE-M3, text2vec-base-chinese
- **數據處理**：Pandas, NumPy
- **並行處理**：asyncio, multiprocessing
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-vector-pipeline .

# 運行容器
docker run -p 8001:8001 podwise-vector-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/process-batch` - 批量處理
- `POST /api/v1/search` - 向量檢索
- `GET /api/v1/statistics` - 統計資訊
- `GET /api/v1/status` - 處理狀態

## 架構優勢

1. **高效性**：優化的批處理和並行處理
2. **可擴展性**：支援多種嵌入模型和檢索算法
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的指標和健康檢查
5. **一致性**：統一的數據模型和介面設計 