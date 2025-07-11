#!/usr/bin/env python3
"""
Milvus 配置文件
管理 Milvus 連線設定和集合配置
"""

import os
from typing import Dict, Any

# Milvus 連線配置
MILVUS_CONFIG = {
    'host': os.getenv('MILVUS_HOST', '192.168.32.86'),
    'port': os.getenv('MILVUS_PORT', '19530'),
    'user': os.getenv('MILVUS_USER', ''),
    'password': os.getenv('MILVUS_PASSWORD', ''),
    'db_name': os.getenv('MILVUS_DB', 'default')
}

# 集合配置
COLLECTION_CONFIG = {
    'name': 'podwise_chunks',
    'description': 'Podwise podcast chunks with embeddings and tags',
    'vector_dim': 1024,  # BGE-M3 預設維度
    'index_type': 'HNSW',
    'metric_type': 'COSINE',
    'index_params': {
        'M': 16,
        'efConstruction': 500
    }
}

# 欄位定義 - 符合您提供的 Milvus 欄位格式
FIELD_SCHEMAS = [
    {
        'name': 'chunk_id',
        'dtype': 'VARCHAR',
        'max_length': 64,
        'is_primary': True,
        'description': '唯一主鍵，每段 chunk 的 UUID'
    },
    {
        'name': 'chunk_index',
        'dtype': 'INT64',
        'description': '該段在該 episode 的順序，用來查前後文'
    },
    {
        'name': 'episode_id',
        'dtype': 'INT64',
        'description': '對應 episodes 表主鍵'
    },
    {
        'name': 'podcast_id',
        'dtype': 'INT64',
        'description': '對應 podcasts 表主鍵'
    },
    {
        'name': 'podcast_name',
        'dtype': 'VARCHAR',
        'max_length': 255,
        'description': '節目名稱，對應 podcasts.name'
    },
    {
        'name': 'author',
        'dtype': 'VARCHAR',
        'max_length': 255,
        'description': '節目作者/主持人，對應 podcasts.author'
    },
    {
        'name': 'category',
        'dtype': 'VARCHAR',
        'max_length': 64,
        'description': '節目分類，對應 podcasts.category'
    },
    {
        'name': 'episode_title',
        'dtype': 'VARCHAR',
        'max_length': 255,
        'description': '該段所屬的集數標題，方便辨識'
    },
    {
        'name': 'duration',
        'dtype': 'VARCHAR',
        'max_length': 255,
        'description': '時間長度'
    },
    {
        'name': 'published_date',
        'dtype': 'VARCHAR',
        'max_length': 64,
        'description': '發布時間'
    },
    {
        'name': 'apple_rating',
        'dtype': 'INT32',
        'description': 'apple podcast頻道星級評分'
    },
    {
        'name': 'chunk_text',
        'dtype': 'VARCHAR',
        'max_length': 1024,
        'description': '本段落的逐字稿文字內容'
    },
    {
        'name': 'embedding',
        'dtype': 'FLOAT_VECTOR',
        'dim': 1024,
        'description': '該段語意向量（如 1024 維）'
    },
    {
        'name': 'language',
        'dtype': 'VARCHAR',
        'max_length': 16,
        'description': '語言代碼（如 zh, en）'
    },
    {
        'name': 'created_at',
        'dtype': 'VARCHAR',
        'max_length': 64,
        'description': '該筆資料建立時間'
    },
    {
        'name': 'source_model',
        'dtype': 'VARCHAR',
        'max_length': 64,
        'description': '使用的 embedding 模型名稱'
    },
    {
        'name': 'tag',
        'dtype': 'VARCHAR',
        'max_length': 1024,
        'description': 'json 該段主題標籤，供 UI 呈現與檢索'
    }
]

# 處理配置
PROCESSING_CONFIG = {
    'batch_size': 50,
    'max_text_length': 1024,
    'embedding_model': 'BAAI/bge-m3',
    'language': 'zh',
    'default_rating': 0
}

# 索引配置
INDEX_CONFIG = {
    'vector_index': {
        'field_name': 'embedding',
        'index_type': 'HNSW',
        'metric_type': 'COSINE',
        'params': {
            'M': 16,
            'efConstruction': 500
        }
    },
    'scalar_indexes': [
        'podcast_id',
        'episode_id',
        'category',
        'language'
    ]
}

def get_milvus_config() -> Dict[str, Any]:
    """獲取 Milvus 配置"""
    return MILVUS_CONFIG.copy()

def get_collection_config() -> Dict[str, Any]:
    """獲取集合配置"""
    return COLLECTION_CONFIG.copy()

def get_field_schemas() -> list:
    """獲取欄位定義"""
    return FIELD_SCHEMAS.copy()

def get_processing_config() -> Dict[str, Any]:
    """獲取處理配置"""
    return PROCESSING_CONFIG.copy()

def get_index_config() -> Dict[str, Any]:
    """獲取索引配置"""
    return INDEX_CONFIG.copy()

def validate_config() -> bool:
    """驗證配置"""
    try:
        # 檢查必要配置
        required_fields = ['host', 'port']
        for field in required_fields:
            if not MILVUS_CONFIG.get(field):
                print(f"❌ 缺少必要配置: {field}")
                return False
        
        # 檢查集合配置
        if not COLLECTION_CONFIG.get('name'):
            print("❌ 缺少集合名稱配置")
            return False
        
        # 檢查欄位定義
        if not FIELD_SCHEMAS:
            print("❌ 缺少欄位定義")
            return False
        
        print("✅ 配置驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Milvus 配置檢查")
    print("=" * 30)
    
    if validate_config():
        print("\n📋 當前配置:")
        print(f"  Milvus 主機: {MILVUS_CONFIG['host']}:{MILVUS_CONFIG['port']}")
        print(f"  集合名稱: {COLLECTION_CONFIG['name']}")
        print(f"  向量維度: {COLLECTION_CONFIG['vector_dim']}")
        print(f"  欄位數量: {len(FIELD_SCHEMAS)}")
        print(f"  批次大小: {PROCESSING_CONFIG['batch_size']}")
    else:
        print("❌ 配置有問題，請檢查") 