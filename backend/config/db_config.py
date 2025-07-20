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
    "collection_name": os.getenv("MILVUS_COLLECTION_NAME", "podcast_chunks"),
    "dim": int(os.getenv("MILVUS_DIM", "1024")),
    "index_type": os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT"),
    "metric_type": os.getenv("MILVUS_METRIC_TYPE", "L2"),
    "params": {
        "nlist": int(os.getenv("MILVUS_NLIST", "1024"))
    }
}

# MinIO 配置
MINIO_CONFIG: Dict = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "192.168.32.66:30090"),
    "access_key": os.getenv("MINIO_ROOT_USER", "bdse37"),
    "secret_key": os.getenv("MINIO_ROOT_PASSWORD", "11111111"),
    "secure": False,
    "bucket_name": os.getenv("MINIO_BUCKET_NAME", "podcast")
}

# MongoDB 配置
MONGO_CONFIG: Dict = {
    "host": os.getenv("MONGO_HOST", "192.168.32.86"),  # worker3 節點 IP
    "port": int(os.getenv("MONGO_PORT", "30017")),  # NodePort
    "username": os.getenv("MONGO_USER", "bdse37"),
    "password": os.getenv("MONGO_PASSWORD", "111111"),
    "database": os.getenv("MONGO_DB", "podcast"),
    "collections": {
        "transcripts": "transcripts",
        "summaries": "summaries",
        "topics": "topics"
    }
}

# MongoDB 連接字串
MONGO_URI = f"mongodb://{MONGO_CONFIG['username']}:{MONGO_CONFIG['password']}@{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"

# MongoDB 索引配置
MONGO_INDEXES = {
    "transcripts": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1)],
            "unique": True
        },
        {
            "keys": [("created_at", -1)]
        }
    ],
    "summaries": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1)],
            "unique": True
        }
    ],
    "topics": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1), ("topic", 1)],
            "unique": True
        }
    ]
}

# 合併所有配置
DB_CONFIG: Dict = {
    "postgres": POSTGRES_CONFIG,
    "milvus": MILVUS_CONFIG,
    "minio": MINIO_CONFIG,
    "mongo": MONGO_CONFIG
} 