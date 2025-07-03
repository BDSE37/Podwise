#!/usr/bin/env python3
"""
重建 Milvus 集合腳本
將現有的 384 維度集合重建為 1024 維度以匹配 BGE-M3 模型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from sentence_transformers import SentenceTransformer
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_collection():
    """重建 Milvus 集合"""
    
    # 連接參數
    MILVUS_HOST = "192.168.32.86"
    MILVUS_PORT = "19530"
    OLD_COLLECTION_NAME = "podwise_podcasts"
    NEW_COLLECTION_NAME = "podwise_podcasts_v2"
    
    try:
        # 1. 連接到 Milvus
        logger.info("🔗 連接到 Milvus...")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        
        # 2. 檢查舊集合是否存在
        if utility.has_collection(OLD_COLLECTION_NAME):
            logger.info(f"📋 找到舊集合: {OLD_COLLECTION_NAME}")
            old_collection = Collection(OLD_COLLECTION_NAME)
            logger.info(f"📊 舊集合實體數量: {old_collection.num_entities}")
        else:
            logger.warning(f"⚠️ 舊集合不存在: {OLD_COLLECTION_NAME}")
            old_collection = None
        
        # 3. 刪除新集合（如果存在）
        if utility.has_collection(NEW_COLLECTION_NAME):
            logger.info(f"🗑️ 刪除現有的新集合: {NEW_COLLECTION_NAME}")
            utility.drop_collection(NEW_COLLECTION_NAME)
        
        # 4. 定義新的 schema (1024 維度)
        logger.info("📝 定義新的 collection schema...")
        
        # 定義欄位
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="episode_id", dtype=DataType.INT64),
            FieldSchema(name="podcast_id", dtype=DataType.INT64),
            FieldSchema(name="episode_title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # 1024 維度
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=10),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1000)
        ]
        
        # 創建 schema
        schema = CollectionSchema(
            fields=fields,
            description="Podwise Podcasts Collection with BGE-M3 embeddings (1024 dimensions)"
        )
        
        # 5. 創建新集合
        logger.info(f"🏗️ 創建新集合: {NEW_COLLECTION_NAME}")
        new_collection = Collection(
            name=NEW_COLLECTION_NAME,
            schema=schema,
            using="default"
        )
        
        # 6. 創建索引
        logger.info("🔍 創建向量索引...")
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        new_collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        # 7. 載入集合
        logger.info("📥 載入集合...")
        new_collection.load()
        
        # 8. 驗證新集合
        logger.info("✅ 驗證新集合...")
        logger.info(f"📊 新集合實體數量: {new_collection.num_entities}")
        
        # 檢查嵌入欄位維度
        emb_field = next((f for f in new_collection.schema.fields if f.name == "embedding"), None)
        if emb_field:
            logger.info(f"🔢 嵌入欄位維度: {emb_field.dim}")
        
        logger.info("🎉 集合重建完成！")
        logger.info(f"📋 新集合名稱: {NEW_COLLECTION_NAME}")
        logger.info(f"🔢 嵌入維度: 1024 (匹配 BGE-M3)")
        
        return NEW_COLLECTION_NAME
        
    except Exception as e:
        logger.error(f"❌ 重建集合失敗: {e}")
        raise

if __name__ == "__main__":
    recreate_collection() 