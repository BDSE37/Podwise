# Vector Pipeline 模組

## 功能概述

Vector Pipeline 是一個完整的資料處理流程模組，專門處理 MongoDB 中的 podcast 資料，將其轉換為向量並存入 Milvus 向量資料庫。

### 主要功能

- **MongoDB 資料處理**: 從 MongoDB 讀取 podcast 文檔
- **資料清理**: 整合 data_cleaning 模組進行文本清理
- **文本切分**: 將長文本切分為適合向量化的 chunks
- **標籤提取**: 為每個 chunk 提取 1-3 個標籤
- **向量化**: 使用 BAAI/bge-m3 模型生成嵌入向量
- **Milvus 寫入**: 將處理結果批次寫入 Milvus
- **錯誤處理**: 完整的錯誤記錄和報告機制

## 架構設計

### 核心組件

- **PipelineOrchestrator**: 主要協調器，整合所有處理流程
- **MongoDBProcessor**: MongoDB 資料處理器（整合 data_cleaning）
- **PostgreSQLMapper**: PostgreSQL metadata mapping
- **TextChunker**: 文本切分處理器
- **VectorProcessor**: 向量化處理器
- **MilvusWriter**: Milvus 資料寫入器
- **UnifiedTagManager**: 統一標籤管理器
- **ErrorLogger**: 錯誤記錄器

### 資料流程

```
MongoDB → 資料清理 → 文本切分 → 標籤提取 → PostgreSQL metadata → 向量化 → Milvus
```

## 使用方法

### 1. 基本使用

```python
from vector_pipeline import PipelineOrchestrator

# 配置
mongo_config = {
    "host": "localhost",
    "port": 27017,
    "database": "podcast"
}

postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "podcast",
    "user": "user",
    "password": "password"
}

milvus_config = {
    "host": "localhost",
    "port": "19530",
    "collection_name": "podcast_chunks",
    "dim": 1024
}

# 初始化協調器
orchestrator = PipelineOrchestrator(
    mongo_config=mongo_config,
    postgres_config=postgres_config,
    milvus_config=milvus_config
)

# 處理單個 collection
result = orchestrator.process_collection(
    mongo_collection="RSS_1500839292",
    milvus_collection="podcast_chunks"
)
```

### 2. RSS 處理器

```python
from vector_pipeline.rss_processor import RSSProcessor

# 初始化 RSS 處理器
processor = RSSProcessor(mongo_config, postgres_config, milvus_config)

# 處理所有 RSS collections
results = processor.process_all_rss_collections()

# 獲取錯誤報告
error_report = processor.get_error_report()
```

### 3. 命令列使用

```bash
# 列出所有組件
python main.py --list-components

# 測試組件
python main.py --test-components

# 處理特定 RSS collection
python main.py --process-rss RSS_1500839292

# 執行完整 Pipeline
python main.py --run-pipeline
```

## 錯誤處理

### 錯誤記錄

模組提供完整的錯誤記錄機制：

- **自動記錄**: 處理過程中的錯誤會自動記錄
- **RSS_ID 追蹤**: 每個錯誤都包含對應的 RSS_ID 和標題
- **多種格式**: 支援 JSON 和 CSV 格式的錯誤報告
- **錯誤摘要**: 提供錯誤統計和檔案清單

### 錯誤報告格式

```json
{
  "summary": {
    "total_errors": 5,
    "collections_affected": 2,
    "error_types": {
      "vectorization_error": 3,
      "milvus_write_error": 2
    }
  },
  "error_files": [
    {
      "rss_id": "1500839292",
      "title": "股癌 EP123 投資策略",
      "collection_id": "RSS_1500839292",
      "error_type": "vectorization_error",
      "processing_stage": "vectorization"
    }
  ]
}
```

### 查看錯誤檔案清單

```python
# 獲取錯誤報告
error_report = processor.get_error_report()

# 顯示錯誤檔案清單
for error in error_report["error_files"]:
    print(f"RSS_{error['rss_id']} - {error['title']}")
```

## 配置選項

### MongoDB 配置

```python
mongo_config = {
    "host": "localhost",
    "port": 27017,
    "database": "podcast",
    "username": "user",
    "password": "password"
}
```

### PostgreSQL 配置

```python
postgres_config = {
    "host": "localhost",
    "port": 5432,
    "database": "podcast",
    "user": "user",
    "password": "password"
}
```

### Milvus 配置

```python
milvus_config = {
    "host": "localhost",
    "port": "19530",
    "collection_name": "podcast_chunks",
    "dim": 1024,
    "index_type": "IVF_FLAT",
    "metric_type": "L2"
}
```

## 特殊處理

### 股癌節目 (RSS_1500839292)

對於股癌節目，模組會自動使用專門的清理器：

- 移除表情符號和 kaomoji
- 統一標題格式
- 提取集數資訊
- 特殊字符處理

### 標籤提取策略

1. **CSV 優先**: 使用預定義的標籤分類
2. **智能提取**: 使用 AI 模型提取標籤
3. **備援提取**: 基於關鍵字匹配

## 依賴項目

- pymongo
- psycopg2-binary
- pymilvus
- sentence-transformers
- numpy
- pandas
- data_cleaning 模組

## 注意事項

- 確保 MongoDB、PostgreSQL 和 Milvus 服務正在運行
- 向量化需要足夠的記憶體和 GPU 資源
- 大量資料處理時建議使用批次處理
- 錯誤報告會自動儲存在 `error_logs` 目錄中 