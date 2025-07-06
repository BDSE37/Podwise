"""
資料庫配置文件
"""

import os
from typing import Dict
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# PostgreSQL 配置
POSTGRES_CONFIG: Dict = {
    "host": os.getenv("POSTGRES_HOST", "192.168.32.56"),  # worker1 節點 IP
    "port": int(os.getenv("POSTGRES_PORT", "32432")),  # NodePort
    "database": os.getenv("POSTGRES_DB", "podcast"),
    "user": os.getenv("POSTGRES_USER", "bdse37"),
    "password": os.getenv("POSTGRES_PASSWORD", "111111")
}

# Milvus 配置
MILVUS_CONFIG: Dict = {
    "host": os.getenv("MILVUS_HOST", "192.168.32.86"),  # worker3 節點 IP
    "port": int(os.getenv("MILVUS_PORT", "19530")),
    "collection_name": os.getenv("MILVUS_COLLECTION_NAME", "podwise_embeddings"),
    "dim": int(os.getenv("MILVUS_DIM", "1536")),
    "index_type": os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT"),
    "metric_type": os.getenv("MILVUS_METRIC_TYPE", "L2"),
    "params": {
        "nlist": int(os.getenv("MILVUS_NLIST", "1024"))
    }
}

# MinIO 配置
MINIO_CONFIG: Dict = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    "access_key": os.getenv("MINIO_ROOT_USER", "bdse37"),
    "secret_key": os.getenv("MINIO_ROOT_PASSWORD", "11111111"),
    "secure": False,
    "bucket_name": os.getenv("MINIO_BUCKET_NAME", "podwise")
}

# 合併所有配置
DB_CONFIG: Dict = {
    "postgres": POSTGRES_CONFIG,
    "milvus": MILVUS_CONFIG,
    "minio": MINIO_CONFIG
} 