# Milvus Standalone 向量資料庫部署

本目錄包含 Podwise 專案的 Milvus Standalone 向量資料庫部署配置，支援 bge-m3 embedding 模型與 podcast 內容檢索。

## 📋 功能特色

- **Milvus Standalone**: 輕量級向量資料庫，適合本地開發
- **BGE-M3 整合**: 支援多語言 embedding 模型
- **外掛硬碟支援**: 使用外掛硬碟儲存資料，節省系統空間
- **完整欄位結構**: 支援 20 個標籤欄位與豐富的元資料
- **自動化部署**: 一鍵部署與初始化腳本

## 🏗️ 系統架構

```
Milvus Standalone
├── Milvus 服務 (port: 19530)
├── MinIO 物件儲存 (port: 9000/9001)
└── 資料儲存
    ├── 向量資料
    ├── 索引檔案
    └── 元資料
```

## 📊 集合結構

### 主要欄位

| 欄位名稱 | 資料型態 | 說明 |
|---------|---------|------|
| chunk_id | VARCHAR(64) | 唯一主鍵 |
| chunk_index | INT64 | 片段順序 |
| episode_id | INT64 | 集數 ID |
| podcast_id | INT64 | 節目 ID |
| episode_title | VARCHAR(255) | 集數標題 |
| chunk_text | VARCHAR(1024) | 文字內容 |
| embedding | FLOAT_VECTOR(768) | BGE-M3 向量 |
| language | VARCHAR(16) | 語言代碼 |
| created_at | VARCHAR(32) | 建立時間 |
| source_model | VARCHAR(64) | 模型名稱 |
| podcast_name | VARCHAR(255) | 節目名稱 |
| author | VARCHAR(255) | 作者/主持人 |
| category | VARCHAR(64) | 節目分類 |

### 標籤欄位 (tag_1 到 tag_20)

每個標籤欄位都是 VARCHAR(1024)，支援靈活的主題標記。

## 🚀 快速開始

### 1. 前置需求

- Docker & Docker Compose
- Python 3.8+
- 外掛硬碟 (建議 50GB+ 可用空間)

### 2. 部署步驟

```bash
# 進入 Milvus 目錄
cd deploy/milvus

# 完整部署 (推薦)
./deploy.sh deploy

# 或分步驟部署
./deploy.sh start    # 僅啟動服務
./deploy.sh init     # 僅初始化集合
./deploy.sh test     # 僅測試模型
```

### 3. 驗證部署

```bash
# 檢查服務狀態
docker-compose ps

# 檢查健康狀態
curl http://localhost:9091/healthz

# 查看 MinIO Console
# 開啟瀏覽器: http://localhost:9001
# 帳號: bdse37, 密碼: 11111111
```

## 🔧 配置說明

### Docker 配置

- **資料目錄**: `/Volumes/Transcend/docker-data`
- **網路**: `milvus_network`
- **持久化**: 使用 Docker volumes

### Milvus 配置

- **索引類型**: IVF_FLAT
- **相似度度量**: COSINE
- **向量維度**: 768 (BGE-M3)
- **分區策略**: 按語言與分類

### BGE-M3 模型

- **模型名稱**: `BAAI/bge-m3`
- **支援語言**: 中文、英文、日文、韓文
- **向量維度**: 768
- **正規化**: 啟用

## 📝 使用範例

### Python 客戶端

```python
from pymilvus import connections, Collection

# 連接到 Milvus
connections.connect("default", host="localhost", port="19530")

# 載入集合
collection = Collection("podcast_chunks")
collection.load()

# 搜尋相似內容
search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
results = collection.search(
    data=[embedding_vector],
    anns_field="embedding",
    param=search_params,
    limit=10,
    output_fields=["chunk_text", "episode_title"]
)
```

### 批次插入資料

```python
from deploy.milvus.bge_m3_integration import BGEM3Embedding, create_podcast_embeddings

# 建立 embedding
model = BGEM3Embedding()
texts = ["podcast 內容 1", "podcast 內容 2", ...]
result = create_podcast_embeddings(texts, model)

# 插入到 Milvus
collection.insert(data)
```

## 🛠️ 管理命令

### 服務管理

```bash
# 啟動服務
./start-milvus.sh start

# 停止服務
./start-milvus.sh stop

# 重啟服務
./start-milvus.sh restart

# 查看狀態
./start-milvus.sh status

# 查看日誌
./start-milvus.sh logs
```

### 部署管理

```bash
# 完整部署
./deploy.sh deploy

# 清理資源
./deploy.sh cleanup

# 查看幫助
./deploy.sh help
```

## 📊 監控與維護

### 健康檢查

- **Milvus**: `http://localhost:9091/healthz`
- **MinIO**: `http://localhost:9000/minio/health/live`

### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f milvus
docker-compose logs -f minio
```

### 資料備份

```bash
# 備份 Milvus 資料
docker run --rm -v milvus_data:/data -v $(pwd):/backup alpine tar czf /backup/milvus_backup.tar.gz -C /data .

# 備份 MinIO 資料
docker run --rm -v minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup.tar.gz -C /data .
```

## 🔍 故障排除

### 常見問題

1. **服務啟動失敗**
   - 檢查 Docker 是否運行
   - 檢查端口是否被佔用
   - 查看服務日誌

2. **空間不足**
   - 清理 Docker 映像: `docker system prune -f`
   - 檢查外掛硬碟空間
   - 清理舊的備份檔案

3. **連接失敗**
   - 檢查防火牆設定
   - 確認服務狀態
   - 檢查網路配置

### 效能優化

- **索引參數**: 根據資料量調整 `nlist` 參數
- **批次大小**: 調整 BGE-M3 批次處理大小
- **記憶體配置**: 根據硬體調整 Docker 記憶體限制

## 📚 參考資料

- [Milvus 官方文件](https://milvus.io/docs)
- [BGE-M3 模型說明](https://huggingface.co/BAAI/bge-m3)
- [PyMilvus Python SDK](https://milvus.io/docs/pymilvus.md)

## 🤝 貢獻

如有問題或建議，請提交 Issue 或 Pull Request。 