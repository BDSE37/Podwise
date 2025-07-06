# Podwise 配置服務

統一的配置管理和資料庫初始化服務。

## 功能特色

### 配置管理
- **MongoDB 配置**：資料庫連接、集合設定、索引配置
- **PostgreSQL 配置**：關聯式資料庫設定
- **Milvus 配置**：向量資料庫設定
- **MinIO 配置**：物件儲存設定

### 資料庫初始化
- **PostgreSQL 初始化**：自動建立資料表結構和測試資料
- **等待腳本**：確保資料庫服務就緒後再執行初始化

## API 端點

### 配置查詢
- `GET /` - 服務狀態
- `GET /health` - 健康檢查
- `GET /api/v1/configs/mongo` - MongoDB 配置
- `GET /api/v1/configs/postgres` - PostgreSQL 配置
- `GET /api/v1/configs/milvus` - Milvus 配置
- `GET /api/v1/configs/minio` - MinIO 配置
- `GET /api/v1/configs/all` - 所有配置

### 資料庫初始化
- `POST /api/v1/init/database` - 執行資料庫初始化
- `GET /api/v1/init/status` - 初始化狀態

## 使用方法

### 本地開發
```bash
cd Podwise/backend/config
pip install -r requirements.txt
python config_service.py
```

### Docker 部署
```bash
docker build -t podwise-config .
docker run -p 8008:8008 podwise-config
```

### 初始化資料庫
```bash
# 透過 API 初始化
curl -X POST http://localhost:8008/api/v1/init/database

# 或直接執行腳本
psql -h localhost -U bdse37 -d podcast -f init-scripts/01-init.sql
```

## 環境變數

### PostgreSQL
- `POSTGRES_HOST` - 主機地址 (預設: localhost)
- `POSTGRES_PORT` - 端口 (預設: 5432)
- `POSTGRES_DB` - 資料庫名稱 (預設: podcast)
- `POSTGRES_USER` - 使用者名稱 (預設: bdse37)
- `POSTGRES_PASSWORD` - 密碼 (預設: 111111)

### Milvus
- `MILVUS_HOST` - 主機地址 (預設: localhost)
- `MILVUS_PORT` - 端口 (預設: 19530)
- `MILVUS_COLLECTION_NAME` - 集合名稱 (預設: podwise_embeddings)
- `MILVUS_DIM` - 向量維度 (預設: 1536)

### MinIO
- `MINIO_ENDPOINT` - 端點 (預設: localhost:9000)
- `MINIO_ROOT_USER` - 使用者名稱 (預設: bdse37)
- `MINIO_ROOT_PASSWORD` - 密碼 (預設: 11111111)
- `MINIO_BUCKET_NAME` - 儲存桶名稱 (預設: podwise)

## 依賴項目

- fastapi
- uvicorn
- psycopg2-binary
- pymongo
- pymilvus
- minio

## 注意事項

- 確保 PostgreSQL 服務正在運行
- 檢查資料庫連接配置
- 初始化腳本需要適當的資料庫權限
- 配置變更後需要重啟服務 