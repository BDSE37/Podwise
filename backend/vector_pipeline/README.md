# Vector Pipeline

一個完整的向量處理管道系統，用於處理 podcast 內容的文本分塊、標籤化、向量化和存儲。

## 功能特色

- **文本分塊**: 智能文本分割，支援重疊分塊
- **向量化**: 使用 BGE-M3 模型生成高品質向量嵌入
- **智能標籤**: 自動標籤提取和分類
- **向量存儲**: 與 Milvus 向量資料庫整合
- **批次處理**: 支援大量資料的批次處理
- **錯誤處理**: 完整的錯誤記錄和恢復機制

## 架構設計

```
vector_pipeline/
├── main.py              # 主要入口點和 API
├── core/                # 核心業務邏輯
│   ├── vector_processor.py
│   ├── text_chunker.py
│   ├── tag_processor.py
│   ├── milvus_writer.py
│   └── ...
├── services/            # 服務層
│   ├── embedding_service.py
│   ├── search_service.py
│   ├── tagging_service.py
│   └── ...
├── config/              # 配置檔案
├── data/                # 資料目錄
└── logs/                # 日誌檔案
```

## 快速開始

### 基本使用

```python
from vector_pipeline.main import VectorPipeline

# 建立管道實例
pipeline = VectorPipeline()

# 處理單一文本
result = pipeline.process_text(
    "這是一個測試文本",
    metadata={'source': 'test', 'author': 'user'}
)

# 批次處理
texts = ["文本1", "文本2", "文本3"]
batch_result = pipeline.batch_process(texts)

# 向量搜尋
search_result = pipeline.search_similar("搜尋查詢", limit=10)
```

### 便利函數

```python
from vector_pipeline.main import process_single_text, search_similar_content

# 快速處理單一文本
result = process_single_text("測試文本")

# 快速搜尋
results = search_similar_content("查詢內容")
```

## API 參考

### VectorPipeline 類別

#### 初始化
```python
pipeline = VectorPipeline(config_path="config.json")
```

#### 主要方法

##### process_text(text, metadata=None)
處理單一文本通過完整管道。

**參數:**
- `text` (str): 要處理的文本
- `metadata` (dict, optional): 文本的元資料

**返回:**
- `dict`: 包含處理結果的字典

##### batch_process(texts, metadata_list=None)
批次處理多個文本。

**參數:**
- `texts` (List[str]): 要處理的文本列表
- `metadata_list` (List[dict], optional): 每個文本的元資料列表

**返回:**
- `dict`: 包含批次處理結果的字典

##### search_similar(query, limit=10)
使用向量相似度搜尋相似內容。

**參數:**
- `query` (str): 搜尋查詢
- `limit` (int): 返回結果的最大數量

**返回:**
- `dict`: 包含搜尋結果的字典

##### store_to_milvus(data)
將處理後的資料存儲到 Milvus 向量資料庫。

**參數:**
- `data` (List[dict]): 要存儲的資料列表

**返回:**
- `dict`: 包含存儲結果的字典

##### sync_stages(source_stage, target_stage)
同步管道階段之間的資料。

**參數:**
- `source_stage` (str): 來源階段名稱
- `target_stage` (str): 目標階段名稱

**返回:**
- `dict`: 包含同步結果的字典

##### normalize_titles(titles)
標準化標題以保持一致性。

**參數:**
- `titles` (List[str]): 要標準化的標題列表

**返回:**
- `List[str]`: 標準化後的標題列表

##### get_pipeline_status()
獲取所有管道組件的當前狀態。

**返回:**
- `dict`: 包含組件狀態的字典

## 配置

### 預設配置

```json
{
  "milvus": {
    "host": "192.168.32.86",
    "port": "19530",
    "collection_name": "podcast_chunks"
  },
  "embedding": {
    "model": "bge-m3",
    "dimension": 1024
  },
  "chunking": {
    "chunk_size": 512,
    "overlap": 50
  }
}
```

### 自定義配置

建立 `config.json` 檔案：

```json
{
  "milvus": {
    "host": "your-milvus-host",
    "port": "19530",
    "collection_name": "your-collection"
  },
  "embedding": {
    "model": "bge-m3",
    "dimension": 1024
  },
  "chunking": {
    "chunk_size": 256,
    "overlap": 25
  }
}
```

## 核心組件

### Core 模組

- **VectorProcessor**: 向量處理核心邏輯
- **TextChunker**: 文本分塊處理
- **TagProcessor**: 標籤處理和提取
- **TagManager**: 標籤管理
- **MilvusWriter**: Milvus 資料庫寫入
- **PostgreSQLMapper**: PostgreSQL 資料映射
- **MongoProcessor**: MongoDB 資料處理
- **PipelineStages**: 管道階段管理
- **BatchProcessor**: 批次處理
- **StageSyncManager**: 階段同步管理
- **TitleNormalizer**: 標題標準化
- **ErrorLogger**: 錯誤記錄

### Services 模組

- **EmbeddingService**: 向量嵌入服務
- **SearchService**: 向量搜尋服務
- **TaggingService**: 標籤服務
- **ErrorLogger**: 錯誤記錄服務

## 使用範例

### 完整管道處理

```python
from vector_pipeline.main import VectorPipeline

# 建立管道
pipeline = VectorPipeline()

# 處理 podcast 內容
podcast_text = """
這是一個關於人工智慧的 podcast 內容。
我們將討論機器學習的最新發展和應用。
"""

metadata = {
    'podcast_name': 'AI Talk',
    'episode_title': '機器學習入門',
    'author': '張三',
    'category': '科技'
}

# 執行完整處理
result = pipeline.process_text(podcast_text, metadata)

if result['status'] == 'success':
    print(f"處理成功: {result['chunks']} 個分塊")
    print(f"生成 {result['embeddings']} 個向量")
else:
    print(f"處理失敗: {result['message']}")
```

### 向量搜尋

```python
# 搜尋相似內容
search_query = "人工智慧應用"
results = pipeline.search_similar(search_query, limit=5)

if results['status'] == 'success':
    print(f"找到 {results['results_count']} 個相關結果:")
    for i, result in enumerate(results['results']):
        print(f"{i+1}. {result['episode_title']}")
        print(f"   相似度: {result['score']:.4f}")
        print(f"   內容: {result['chunk_text'][:100]}...")
```

### 批次處理

```python
# 批次處理多個文本
texts = [
    "第一個 podcast 內容",
    "第二個 podcast 內容", 
    "第三個 podcast 內容"
]

metadata_list = [
    {'source': 'podcast1', 'category': '科技'},
    {'source': 'podcast2', 'category': '商業'},
    {'source': 'podcast3', 'category': '教育'}
]

batch_result = pipeline.batch_process(texts, metadata_list)

print(f"總處理: {batch_result['total_processed']}")
print(f"成功: {batch_result['successful']}")
print(f"失敗: {batch_result['failed']}")
```

## 錯誤處理

系統提供完整的錯誤處理機制：

```python
# 檢查管道狀態
status = pipeline.get_pipeline_status()
print(f"Milvus 連接: {status['milvus_connection']}")
print(f"嵌入服務: {status['embedding_service']}")
print(f"搜尋服務: {status['search_service']}")
print(f"錯誤數量: {status['error_count']}")
```

## 依賴項目

```
pymilvus>=2.4.0
numpy>=1.21.0
pandas>=1.3.0
psycopg2-binary>=2.9.0
pymongo>=4.0.0
sentence-transformers>=2.2.0
```

## 安裝

```bash
# 安裝依賴
pip install -r requirements.txt

# 或使用 conda
conda install --file requirements.txt
```

## 開發

### 程式碼風格

本專案遵循 Google Python Style Guide：

- 使用 4 空格縮排
- 行長度限制在 80 字元
- 使用類型提示
- 完整的 docstring 文件
- 單元測試覆蓋

### 測試

```bash
# 執行測試
python -m pytest tests/

# 執行特定測試
python -m pytest tests/test_vector_processor.py
```

## 授權

本專案採用 MIT 授權條款。

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 更新日誌

### v1.0.0 (2025-07-16)
- 初始版本發布
- 完整的向量處理管道
- Milvus 整合
- 智能標籤系統
- 批次處理支援 