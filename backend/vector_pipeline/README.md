# Vector Pipeline

## 概述

Vector Pipeline 是 Podwise 專案的核心資料處理模組，提供完整的資料處理流程：
**MongoDB 長文本 → 切分 chunks → 標籤貼標 → PostgreSQL metadata mapping → 向量化 → 寫入 Milvus**

## 架構設計

### 核心組件 (Core Components)

```
vector_pipeline/
├── core/                          # 核心組件
│   ├── __init__.py               # 模組匯出
│   ├── mongo_processor.py        # MongoDB 資料處理器
│   ├── postgresql_mapper.py      # PostgreSQL metadata mapping
│   ├── text_chunker.py           # 文本切分處理器
│   ├── vector_processor.py       # 向量化處理器
│   └── milvus_writer.py          # Milvus 資料寫入器
├── pipeline_orchestrator.py      # Pipeline 協調器
├── main.py                       # 主程式入口
├── __init__.py                   # 模組匯出
├── TAG_info.csv                  # 標籤定義檔案
└── requirements.txt              # 依賴套件
```

### OOP 架構

所有組件都採用物件導向設計，符合 Google Clean Code 原則：

- **單一職責原則**: 每個類別只負責一個特定功能
- **開放封閉原則**: 易於擴展，無需修改現有程式碼
- **依賴反轉原則**: 依賴抽象而非具體實作
- **介面隔離原則**: 提供精確的介面定義

## 核心類別

### 1. MongoDBProcessor
```python
from vector_pipeline.core import MongoDBProcessor

# 初始化
processor = MongoDBProcessor(mongo_config)

# 獲取文檔
documents = processor.fetch_documents("collection_name")

# 解析 file 欄位
episode_number, podcast_name, title = processor.parse_file_field(file_name)
```

### 2. PostgreSQLMapper
```python
from vector_pipeline.core import PostgreSQLMapper

# 初始化
mapper = PostgreSQLMapper(postgres_config)

# 搜尋 episode metadata
metadata = mapper.search_episode_by_title_and_podcast(title, podcast_name)

# 獲取完整 metadata
episode_meta = mapper.get_episode_metadata(episode_id)
```

### 3. TextChunker
```python
from vector_pipeline.core import TextChunker

# 初始化
chunker = TextChunker(max_chunk_size=1024, overlap_size=100)

# 文本切分
chunks = chunker.split_text_into_chunks(text, document_id)

# 按句子切分
chunks = chunker.split_text_by_sentences(text, document_id)
```

### 4. VectorProcessor
```python
from vector_pipeline.core import VectorProcessor

# 初始化
processor = VectorProcessor(embedding_model="BAAI/bge-m3")

# 生成嵌入向量
embeddings = processor.generate_embeddings(texts)

# 計算相似度
similarity = processor.calculate_similarity(text1, text2)
```

### 5. MilvusWriter
```python
from vector_pipeline.core import MilvusWriter

# 初始化
writer = MilvusWriter(milvus_config)

# 創建集合
collection_name = writer.create_collection("podcast_chunks")

# 批次插入資料
total_inserted = writer.batch_insert(collection_name, data_list)
```

### 6. PipelineOrchestrator
```python
from vector_pipeline import PipelineOrchestrator

# 初始化
orchestrator = PipelineOrchestrator(
    mongo_config=mongo_config,
    postgres_config=postgres_config,
    milvus_config=milvus_config,
    tag_csv_path="TAG_info.csv"
)

# 處理完整流程
stats = orchestrator.process_collection(
    mongo_collection="RSS_1567737523",
    milvus_collection="podcast_chunks"
)
```

## 標籤處理邏輯

### 智能標籤系統

1. **優先使用 CSV 標籤**:
   - 讀取 `TAG_info.csv` 檔案
   - 根據內容匹配預定義標籤
   - 使用權重系統進行分類

2. **Fallback 智能標籤**:
   - 如果 CSV 中沒有對應標籤，使用 `rag_pipeline/utils/tag_processor.py`
   - 基於關鍵字匹配和語意分析
   - 自動生成相關標籤

3. **標籤向量化**:
   - 每個 chunk 最多支援 3 個標籤向量 (tag_1, tag_2, tag_3)
   - 標籤向量使用與主要內容相同的嵌入模型
   - 支援語義相似性查詢

### 標籤處理流程

```python
def _extract_tags(self, chunk_text: str) -> List[str]:
    """提取標籤"""
    try:
        if self.tag_processor:
            # 1. 優先使用 TagProcessor 進行分類
            result = self.tag_processor.categorize_content(chunk_text)
            return result.get('tags', [])
        else:
            # 2. Fallback: 使用簡單的關鍵字匹配
            return self._simple_tag_extraction(chunk_text)
    except Exception as e:
        # 3. 錯誤處理: 返回空標籤
        return []
```

## 使用範例

### 基本使用

```python
from vector_pipeline import PipelineOrchestrator
from config.mongo_config import MONGO_CONFIG
from config.db_config import POSTGRES_CONFIG, MILVUS_CONFIG

# 初始化
orchestrator = PipelineOrchestrator(
    mongo_config=MONGO_CONFIG,
    postgres_config=POSTGRES_CONFIG,
    milvus_config=MILVUS_CONFIG
)

# 處理集合
stats = orchestrator.process_collection(
    mongo_collection="RSS_1567737523",
    milvus_collection="podcast_chunks",
    limit=100  # 限制處理文檔數量
)

print(f"處理完成: {stats}")
```

### 命令列使用

```bash
# 處理和向量化
python -m vector_pipeline.main --action process \
    --mongo-collection RSS_1567737523 \
    --milvus-collection podcast_chunks \
    --limit 50

# 重建集合
python -m vector_pipeline.main --action recreate \
    --milvus-collection podcast_chunks

# 查看統計
python -m vector_pipeline.main --action stats \
    --milvus-collection podcast_chunks
```

### 互動模式

```bash
python -m vector_pipeline.main
```

## 配置

### MongoDB 配置
```python
MONGO_CONFIG = {
    "host": "192.168.32.86",
    "port": 30017,
    "database": "podcast",
    "username": "bdse37",
    "password": "111111"
}
```

### PostgreSQL 配置
```python
POSTGRES_CONFIG = {
    "host": "192.168.32.56",
    "port": 32432,
    "database": "podcast",
    "user": "bdse37",
    "password": "111111"
}
```

### Milvus 配置
```python
MILVUS_CONFIG = {
    "host": "192.168.32.86",
    "port": 19530,
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "nlist": 1024
}
```

## 測試

執行完整測試：
```bash
python test_pipeline.py
```

測試包含：
- MongoDB 連接測試
- PostgreSQL 連接測試
- Milvus 連接測試
- 文本切分測試
- 向量處理測試
- 完整流程測試

## 依賴套件

```
pymongo>=4.0.0
psycopg2-binary>=2.9.0
pymilvus>=2.3.0
sentence-transformers>=2.2.0
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
```

## 版本歷史

- **v2.0.0**: 重構為 OOP 架構，新增 PipelineOrchestrator
- **v1.0.0**: 初始版本，程序式設計 