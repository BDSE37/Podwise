# Vector Pipeline 架構設計

## 概述

Vector Pipeline 已重構為符合 Google Clean Code 原則的物件導向架構，與其他 backend 模組保持一致。

## 架構對比

### 重構前 (v1.0.0)
```
vector_pipeline/
├── text_processor.py     # 程序式設計，功能混雜
├── vector_pipeline.py    # 單一大型類別
└── main.py              # 簡單的命令列介面
```

### 重構後 (v2.0.0)
```
vector_pipeline/
├── core/                          # 核心組件 (單一職責)
│   ├── __init__.py               # 模組匯出
│   ├── mongo_processor.py        # MongoDB 處理器
│   ├── postgresql_mapper.py      # PostgreSQL 映射器
│   ├── text_chunker.py           # 文本切分器
│   ├── vector_processor.py       # 向量處理器
│   └── milvus_writer.py          # Milvus 寫入器
├── pipeline_orchestrator.py      # 協調器 (依賴反轉)
├── main.py                       # 主程式入口
├── __init__.py                   # 模組匯出
└── README.md                     # 完整文件
```

## Google Clean Code 原則應用

### 1. 單一職責原則 (Single Responsibility Principle)

每個類別只負責一個特定功能：

```python
# ✅ 正確：單一職責
class MongoDBProcessor:
    """只負責 MongoDB 資料處理"""
    
class TextChunker:
    """只負責文本切分"""
    
class VectorProcessor:
    """只負責向量化處理"""

# ❌ 錯誤：多重職責
class TextProcessor:
    """處理文本、查詢資料庫、生成向量、寫入 Milvus"""
```

### 2. 開放封閉原則 (Open/Closed Principle)

易於擴展，無需修改現有程式碼：

```python
# ✅ 正確：可擴展的設計
class BaseProcessor:
    def process(self, data):
        raise NotImplementedError

class MongoDBProcessor(BaseProcessor):
    def process(self, data):
        # MongoDB 特定處理邏輯
        pass

class PostgreSQLProcessor(BaseProcessor):
    def process(self, data):
        # PostgreSQL 特定處理邏輯
        pass
```

### 3. 依賴反轉原則 (Dependency Inversion Principle)

依賴抽象而非具體實作：

```python
# ✅ 正確：依賴抽象
class PipelineOrchestrator:
    def __init__(self, mongo_processor, postgres_mapper, vector_processor):
        self.mongo_processor = mongo_processor
        self.postgres_mapper = postgres_mapper
        self.vector_processor = vector_processor

# ❌ 錯誤：依賴具體實作
class PipelineOrchestrator:
    def __init__(self):
        self.mongo_processor = MongoDBProcessor()  # 硬編碼依賴
```

### 4. 介面隔離原則 (Interface Segregation Principle)

提供精確的介面定義：

```python
# ✅ 正確：精確的介面
@dataclass
class MongoDocument:
    document_id: str
    text: str
    file: str
    created: datetime
    episode_number: Optional[int]
    podcast_name: Optional[str]
    title: Optional[str]

# ❌ 錯誤：過度複雜的介面
class MongoDocument:
    def __init__(self, raw_data):
        self.raw_data = raw_data  # 暴露內部實作
```

## 核心組件設計

### 1. MongoDBProcessor

**職責**: MongoDB 資料處理和 file 欄位解析

```python
class MongoDBProcessor:
    def connect(self) -> None:
        """連接到 MongoDB"""
    
    def parse_file_field(self, file_name: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """解析 file 欄位"""
    
    def fetch_documents(self, collection_name: str, query: Optional[Dict] = None) -> List[MongoDocument]:
        """獲取文檔"""
```

### 2. PostgreSQLMapper

**職責**: PostgreSQL metadata 查詢和映射

```python
class PostgreSQLMapper:
    def get_episode_metadata(self, episode_id: int) -> Optional[EpisodeMetadata]:
        """獲取 episode metadata"""
    
    def search_episode_by_title_and_podcast(self, title: str, podcast_name: str) -> Optional[EpisodeMetadata]:
        """搜尋 episode"""
```

### 3. TextChunker

**職責**: 文本切分處理

```python
class TextChunker:
    def split_text_into_chunks(self, text: str, document_id: str) -> List[TextChunk]:
        """文本切分"""
    
    def split_text_by_sentences(self, text: str, document_id: str) -> List[TextChunk]:
        """按句子切分"""
```

### 4. VectorProcessor

**職責**: 向量化處理

```python
class VectorProcessor:
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """生成嵌入向量"""
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """計算相似度"""
```

### 5. MilvusWriter

**職責**: Milvus 資料寫入

```python
class MilvusWriter:
    def create_collection(self, collection_name: str) -> str:
        """創建集合"""
    
    def batch_insert(self, collection_name: str, data_list: List[Dict]) -> int:
        """批次插入"""
```

### 6. PipelineOrchestrator

**職責**: 協調整個處理流程

```python
class PipelineOrchestrator:
    def process_collection(self, mongo_collection: str, milvus_collection: str) -> Dict[str, Any]:
        """處理完整流程"""
    
    def _extract_tags(self, chunk_text: str) -> List[str]:
        """標籤提取邏輯"""
```

## 標籤處理邏輯

### 智能標籤系統設計

```python
def _extract_tags(self, chunk_text: str) -> List[str]:
    """提取標籤 - 符合單一職責原則"""
    try:
        if self.tag_processor:
            # 1. 優先使用 CSV 標籤
            result = self.tag_processor.categorize_content(chunk_text)
            return result.get('tags', [])
        else:
            # 2. Fallback 到智能標籤
            return self._simple_tag_extraction(chunk_text)
    except Exception as e:
        # 3. 錯誤處理
        logger.error(f"提取標籤失敗: {e}")
        return []
```

### 標籤處理流程

1. **優先使用 CSV 標籤** (`TAG_info.csv`)
2. **Fallback 智能標籤** (`rag_pipeline/utils/tag_processor.py`)
3. **簡單關鍵字匹配** (最後防線)
4. **錯誤處理** (返回空標籤)

## 模組化設計

### 可獨立引用

```python
# 獨立使用 MongoDB 處理器
from vector_pipeline.core import MongoDBProcessor
processor = MongoDBProcessor(mongo_config)
documents = processor.fetch_documents("collection_name")

# 獨立使用文本切分器
from vector_pipeline.core import TextChunker
chunker = TextChunker(max_chunk_size=1024)
chunks = chunker.split_text_into_chunks(text, document_id)

# 獨立使用向量處理器
from vector_pipeline.core import VectorProcessor
vector_processor = VectorProcessor(embedding_model="BAAI/bge-m3")
embeddings = vector_processor.generate_embeddings(texts)
```

### 組合使用

```python
# 組合使用完整流程
from vector_pipeline import PipelineOrchestrator
orchestrator = PipelineOrchestrator(mongo_config, postgres_config, milvus_config)
stats = orchestrator.process_collection("mongo_collection", "milvus_collection")
```

## 錯誤處理

### 分層錯誤處理

```python
# 1. 組件層級錯誤處理
class MongoDBProcessor:
    def connect(self) -> None:
        try:
            # 連接邏輯
            pass
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            raise

# 2. 協調器層級錯誤處理
class PipelineOrchestrator:
    def process_collection(self, ...):
        try:
            # 處理邏輯
            pass
        except Exception as e:
            logger.error(f"處理集合失敗: {e}")
            raise

# 3. 應用層級錯誤處理
def main():
    try:
        orchestrator = PipelineOrchestrator(...)
        stats = orchestrator.process_collection(...)
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)
```

## 測試設計

### 單元測試

每個核心組件都有對應的測試：

```python
def test_mongo_processor():
    """測試 MongoDB 處理器"""
    
def test_text_chunker():
    """測試文本切分器"""
    
def test_vector_processor():
    """測試向量處理器"""
```

### 整合測試

```python
def test_pipeline_orchestrator():
    """測試完整流程"""
    
def test_tag_processing():
    """測試標籤處理邏輯"""
```

## 效能優化

### 批次處理

```python
def batch_insert(self, collection_name: str, data_list: List[Dict], batch_size: int = 100):
    """批次插入，避免記憶體溢出"""
    for i in range(0, len(data_list), batch_size):
        batch_data = data_list[i:i + batch_size]
        self.insert_data(collection_name, batch_data)
```

### 連接管理

```python
def __enter__(self):
    """上下文管理器"""
    self.connect()
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """自動關閉連接"""
    self.close()
```

## 配置管理

### 環境配置

```python
# config/mongo_config.py
MONGO_CONFIG = {
    "host": "192.168.32.86",
    "port": 30017,
    "database": "podcast",
    "username": "bdse37",
    "password": "111111"
}

# config/db_config.py
POSTGRES_CONFIG = {...}
MILVUS_CONFIG = {...}
```

### 參數化配置

```python
class PipelineOrchestrator:
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 milvus_config: Dict[str, Any],
                 tag_csv_path: str = "TAG_info.csv",
                 embedding_model: str = "BAAI/bge-m3",
                 max_chunk_size: int = 1024,
                 batch_size: int = 100):
        """可配置的參數"""
```

## 總結

### 架構優勢

1. **模組化**: 每個組件可獨立使用和測試
2. **可擴展**: 易於添加新功能和組件
3. **可維護**: 清晰的職責分離和錯誤處理
4. **可測試**: 完整的測試覆蓋
5. **符合標準**: 遵循 Google Clean Code 原則

### 與其他 Backend 模組一致性

- **目錄結構**: 與 `rag_pipeline`、`stt`、`tts` 等模組保持一致
- **命名規範**: 使用相同的命名約定
- **配置管理**: 統一的配置檔案結構
- **錯誤處理**: 一致的錯誤處理模式
- **日誌記錄**: 統一的日誌格式和級別

### 版本升級

- **v1.0.0 → v2.0.0**: 從程序式設計升級為 OOP 架構
- **向後相容**: 保持 API 相容性
- **功能增強**: 新增智能標籤系統和向量標籤支援
- **效能提升**: 批次處理和連接池優化 