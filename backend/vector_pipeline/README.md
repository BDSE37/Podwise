# Podwise Vector Pipeline 模組

整合的文本處理和向量化模組，提供完整的資料處理管道。

## 功能特色

### 核心功能
- **MongoDB 資料下載**：從 MongoDB 獲取長文本資料
- **PostgreSQL 元資料查詢**：從 PostgreSQL 獲取 episode 相關元資料
- **智能文本分塊**：以空白或換行符進行文本分割
- **標籤匹配**：基於 TAG_info.csv 的關鍵字標籤匹配
- **語意相似度標籤選擇**：當標籤超過3個時，保留語意相似度最高的三個
- **智能標籤提取**：僅當 tag_info 中沒有相關標籤時才進行智能貼標
- **向量嵌入生成**：使用 BGE-M3 模型生成高品質向量
- **Milvus 向量資料庫**：高效的向量儲存和檢索

### 整合優勢
- **一站式處理**：從原始文本到向量檢索的完整流程
- **多資料庫整合**：MongoDB + PostgreSQL + Milvus 完整生態
- **智能標籤策略**：結合規則匹配、語意相似度和智能提取
- **批次處理**：支援大量資料的批次處理和向量化
- **靈活配置**：可自定義分塊大小、嵌入模型等參數

## 檔案結構

```
vector_pipeline/
├── __init__.py           # 模組初始化
├── text_processor.py     # 文本處理器 (整合 PostgreSQL 查詢)
├── vector_pipeline.py    # 向量化管道
├── main.py              # 主執行腳本
├── requirements.txt     # 依賴套件
├── README.md           # 說明文件
├── test_integration.py # 整合測試
└── quick_test.py       # 快速測試
```

## 安裝依賴

```bash
cd Podwise/backend/vector_pipeline
pip install -r requirements.txt
```

## 使用方式

### 1. 命令列模式

#### 處理和向量化文檔
```bash
python main.py --action process \
    --mongo-collection transcripts \
    --milvus-collection podwise_podcasts \
    --limit 1000
```

#### 重建集合
```bash
python main.py --action recreate \
    --milvus-collection podwise_podcasts
```

#### 搜尋相似文檔
```bash
python main.py --action search \
    --query-text "人工智慧技術發展" \
    --top-k 5
```

#### 查看統計資訊
```bash
python main.py --action stats \
    --milvus-collection podwise_podcasts
```

### 2. 互動模式

```bash
python main.py
```

互動模式提供友好的選單介面，支援：
- 處理和向量化文檔
- 重建集合
- 搜尋相似文檔
- 查看統計資訊

### 3. 程式化使用

```python
from vector_pipeline.vector_pipeline import VectorPipeline
from config.mongo_config import MONGO_CONFIG
from config.db_config import POSTGRES_CONFIG, MILVUS_CONFIG

# 初始化管道
pipeline = VectorPipeline(
    mongo_config=MONGO_CONFIG,
    milvus_config=MILVUS_CONFIG,
    postgres_config=POSTGRES_CONFIG
)

# 處理和向量化
stats = pipeline.process_and_vectorize(
    collection_name="podwise_podcasts",
    mongo_collection="transcripts",
    limit=1000
)

# 搜尋相似文檔
results = pipeline.search_similar(
    query_text="人工智慧技術發展",
    collection_name="podwise_podcasts",
    top_k=10
)

# 關閉連接
pipeline.close()
```

## 配置說明

### MongoDB 配置
```python
MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "podwise",
    "username": "bdse37",
    "password": "111111"
}
```

### PostgreSQL 配置
```python
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "podcast",
    "user": "bdse37",
    "password": "111111"
}
```

### Milvus 配置
```python
MILVUS_CONFIG = {
    "host": "localhost",
    "port": "19530",
    "collection_name": "podwise_podcasts",
    "dim": 1024,
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "nlist": 1024
}
```

### 標籤配置
- **TAG_info.csv**：包含標籤和同義詞的對應關係
- **語意相似度選擇**：當標籤超過3個時，按語意相似度排序選擇
- **智能標籤提取**：僅當 tag_info 中沒有相關標籤時才進行
- **標籤數量限制**：每個文本塊最多 0-3 個標籤

## 資料庫結構

### PostgreSQL 表結構
```sql
-- episodes 表
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY,
    podcast_id INTEGER,
    title VARCHAR(500),
    created_at TIMESTAMP
);

-- podcasts 表
CREATE TABLE podcasts (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    author VARCHAR(200),
    category VARCHAR(100)
);
```

### MongoDB 文檔結構
```json
{
    "_id": "ObjectId",
    "episode_id": 123,
    "content": "長文本內容...",
    "created_at": "2024-01-01T00:00:00Z"
}
```

## 處理流程

### 1. 資料獲取
- 從 MongoDB 指定集合獲取文檔
- 支援查詢條件和數量限制

### 2. 元資料查詢
- 根據 episode_id 從 PostgreSQL 查詢元資料
- 獲取 episode_title、podcast_name、author、category 等資訊

### 3. 智能文本分塊
- 以空白或換行符進行文本分割
- 可配置最大分塊大小
- 保持語義完整性

### 4. 標籤匹配
- 基於 TAG_info.csv 的關鍵字匹配
- 支援多個同義詞欄位
- 規則引擎增強匹配

### 5. 語意相似度標籤選擇
- 當標籤超過3個時，計算語意相似度
- 使用 BGE-M3 模型計算文本與標籤的相似度
- 保留相似度最高的三個標籤

### 6. 智能標籤提取
- 僅當 tag_info 中沒有相關標籤時才進行
- 基於主題關鍵詞的智能提取
- 避免重複標籤

### 7. 向量化
- 使用 BGE-M3 模型生成 1024 維向量
- 支援批次處理提高效率
- 向量正規化確保品質

### 8. 向量儲存
- 儲存到 Milvus 向量資料庫
- 自動建立索引優化檢索
- 支援元資料儲存

## 語意相似度計算

### 計算方法
```python
def calculate_semantic_similarity(self, chunk: str, tags: List[str]) -> List[Tuple[str, float]]:
    """
    計算文本塊與標籤的語意相似度
    
    Args:
        chunk: 文本塊
        tags: 標籤列表
        
    Returns:
        標籤和相似度的元組列表，按相似度降序排列
    """
    # 生成文本塊和標籤的嵌入向量
    texts = [chunk] + tags
    embeddings = self.embedding_model_instance.encode(texts, normalize_embeddings=True)
    
    # 計算餘弦相似度
    chunk_embedding = embeddings[0].reshape(1, -1)
    tag_embeddings = embeddings[1:]
    similarities = cosine_similarity(chunk_embedding, tag_embeddings)[0]
    
    # 返回排序後的標籤和相似度
    tag_similarities = list(zip(tags, similarities))
    tag_similarities.sort(key=lambda x: x[1], reverse=True)
    
    return tag_similarities
```

### 標籤選擇策略
1. **關鍵字匹配**：基於 TAG_info.csv 進行匹配
2. **規則引擎**：應用預定義的標籤規則
3. **語意相似度**：當標籤超過3個時，計算相似度並選擇最高的三個
4. **智能提取**：僅當沒有相關標籤時才進行智能提取

## 效能優化

### 批次處理
- 預設批次大小：100 個文檔
- 可根據記憶體調整批次大小
- 進度顯示和錯誤處理

### 記憶體管理
- 自動載入和釋放嵌入模型
- 批次處理減少記憶體佔用
- 連接池管理

### 錯誤處理
- 完整的異常處理機制
- 詳細的日誌記錄
- 優雅的錯誤恢復

## 擴展功能

### 自定義嵌入模型
```python
pipeline = VectorPipeline(
    mongo_config=MONGO_CONFIG,
    milvus_config=MILVUS_CONFIG,
    postgres_config=POSTGRES_CONFIG,
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # 自定義模型
)
```

### 自定義標籤規則
```python
# 在 text_processor.py 中修改 apply_tag_rules 方法
rules = {
    r'\b自定義關鍵詞\b': ['自定義標籤'],
    # 添加更多規則...
}
```

### 自定義分塊策略
```python
# 修改 split_text_into_chunks 方法
# 可實現基於段落、章節等的分塊策略
```

## 監控和除錯

### 日誌記錄
- 詳細的處理進度日誌
- 錯誤和警告資訊
- 效能統計資料

### 統計資訊
- 處理文檔數量
- 標籤分佈統計
- 向量維度和品質
- 語意相似度分佈

### 健康檢查
- MongoDB 連接狀態
- PostgreSQL 連接狀態
- Milvus 集合狀態
- 嵌入模型載入狀態

## 最佳實踐

1. **資料預處理**：確保 MongoDB 文檔格式正確
2. **批次大小**：根據記憶體調整批次處理大小
3. **標籤品質**：定期更新 TAG_info.csv 提升標籤品質
4. **效能監控**：監控處理時間和資源使用
5. **備份策略**：定期備份向量資料庫
6. **資料庫連接**：確保 MongoDB 和 PostgreSQL 服務穩定運行

## 故障排除

### 常見問題

1. **MongoDB 連接失敗**
   - 檢查網路連接和認證資訊
   - 確認 MongoDB 服務運行狀態

2. **PostgreSQL 連接失敗**
   - 檢查網路連接和認證資訊
   - 確認 PostgreSQL 服務運行狀態
   - 檢查資料庫和表是否存在

3. **Milvus 連接失敗**
   - 檢查 Milvus 服務狀態
   - 確認端口和認證配置

4. **嵌入模型載入失敗**
   - 檢查網路連接
   - 確認模型名稱正確

5. **記憶體不足**
   - 減少批次處理大小
   - 增加系統記憶體

6. **語意相似度計算失敗**
   - 檢查 scikit-learn 安裝
   - 確認嵌入模型載入成功

### 除錯技巧

1. 啟用詳細日誌記錄
2. 使用小量資料測試
3. 檢查配置檔案格式
4. 監控系統資源使用
5. 驗證資料庫連接狀態
6. 測試語意相似度計算

## 版本資訊

- **版本**：1.0.0
- **作者**：Podwise Team
- **更新日期**：2024年
- **支援**：Python 3.8+
- **資料庫**：MongoDB 4.4+, PostgreSQL 12+, Milvus 2.3+
- **新增功能**：語意相似度標籤選擇、智能文本分塊 