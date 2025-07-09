#!/usr/bin/env python3
"""
Milvus 集合初始化腳本
建立 podcast chunks 集合，支援 bge-m3 embedding 模型
"""

import time
import uuid
from typing import List, Dict, Any
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    MilvusException
)

# Milvus 連接配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "podcast_chunks"
DIMENSION = 768  # bge-m3 模型維度

def connect_to_milvus():
    """連接到 Milvus 服務"""
    try:
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT
        )
        print(f"✅ 成功連接到 Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        return True
    except Exception as e:
        print(f"❌ 連接 Milvus 失敗: {e}")
        return False

def create_collection_schema():
    """建立集合結構定義"""
    
    # 定義欄位結構
    fields = [
        # 主要識別欄位
        FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="episode_id", dtype=DataType.INT64),
        FieldSchema(name="podcast_id", dtype=DataType.INT64),
        
        # 內容欄位
        FieldSchema(name="episode_title", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
        
        # 元資料欄位
        FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=64),
        
        # 節目資訊欄位
        FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
        
        # 標籤欄位 (tag_1 到 tag_20)
        FieldSchema(name="tag_1", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_2", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_3", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_4", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_5", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_6", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_7", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_8", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_9", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_10", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_11", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_12", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_13", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_14", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_15", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_16", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_17", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_18", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_19", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="tag_20", dtype=DataType.VARCHAR, max_length=1024),
    ]
    
    # 建立集合結構
    schema = CollectionSchema(
        fields=fields,
        description="Podcast 內容片段集合，支援語意搜尋與標籤分類"
    )
    
    return schema

def create_collection():
    """建立集合"""
    try:
        # 檢查集合是否已存在
        if utility.has_collection(COLLECTION_NAME):
            print(f"⚠️  集合 {COLLECTION_NAME} 已存在")
            return utility.load_collection(COLLECTION_NAME)
        
        # 建立集合結構
        schema = create_collection_schema()
        
        # 建立集合
        collection = Collection(
            name=COLLECTION_NAME,
            schema=schema,
            using="default"
        )
        
        print(f"✅ 成功建立集合: {COLLECTION_NAME}")
        
        # 建立索引
        create_indexes(collection)
        
        return collection
        
    except Exception as e:
        print(f"❌ 建立集合失敗: {e}")
        return None

def create_indexes(collection: Collection):
    """建立索引"""
    try:
        # 為 embedding 欄位建立 IVF_FLAT 索引
        index_params = {
            "metric_type": "COSINE",  # 使用餘弦相似度
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        print("✅ 成功建立 embedding 索引")
        
        # 為其他欄位建立索引
        scalar_fields = [
            "episode_id", "podcast_id", "language", 
            "category", "author", "source_model"
        ]
        
        for field in scalar_fields:
            try:
                collection.create_index(
                    field_name=field,
                    index_params={"index_type": "FLAT", "metric_type": "L2"}
                )
                print(f"✅ 成功建立 {field} 索引")
            except Exception as e:
                print(f"⚠️  建立 {field} 索引失敗: {e}")
        
    except Exception as e:
        print(f"❌ 建立索引失敗: {e}")

def insert_sample_data(collection: Collection):
    """插入範例資料"""
    try:
        # 準備範例資料
        sample_data = {
            "chunk_id": [str(uuid.uuid4())],
            "chunk_index": [1],
            "episode_id": [1001],
            "podcast_id": [2001],
            "episode_title": ["AI 與未來工作"],
            "chunk_text": ["人工智慧正在改變我們的工作方式，從自動化到增強人類能力。"],
            "embedding": [[0.1] * DIMENSION],  # 範例向量
            "language": ["zh"],
            "created_at": [time.strftime("%Y-%m-%d %H:%M:%S")],
            "source_model": ["bge-m3"],
            "podcast_name": ["科技趨勢"],
            "author": ["張小明"],
            "category": ["科技"],
            "tag_1": ["人工智慧"],
            "tag_2": ["工作"],
            "tag_3": ["自動化"],
            "tag_4": ["未來"],
            "tag_5": ["科技"],
            "tag_6": [""],
            "tag_7": [""],
            "tag_8": [""],
            "tag_9": [""],
            "tag_10": [""],
            "tag_11": [""],
            "tag_12": [""],
            "tag_13": [""],
            "tag_14": [""],
            "tag_15": [""],
            "tag_16": [""],
            "tag_17": [""],
            "tag_18": [""],
            "tag_19": [""],
            "tag_20": [""],
        }
        
        # 插入資料
        collection.insert(sample_data)
        collection.flush()
        
        print("✅ 成功插入範例資料")
        
    except Exception as e:
        print(f"❌ 插入範例資料失敗: {e}")

def create_partitions(collection: Collection):
    """建立分區"""
    try:
        # 建立語言分區
        partitions = ["zh", "en", "ja", "ko"]
        
        for lang in partitions:
            try:
                collection.create_partition(partition_name=f"lang_{lang}")
                print(f"✅ 成功建立分區: lang_{lang}")
            except Exception as e:
                print(f"⚠️  建立分區 lang_{lang} 失敗: {e}")
        
        # 建立分類分區
        categories = ["科技", "商業", "教育", "娛樂", "新聞"]
        
        for cat in categories:
            try:
                collection.create_partition(partition_name=f"cat_{cat}")
                print(f"✅ 成功建立分區: cat_{cat}")
            except Exception as e:
                print(f"⚠️  建立分區 cat_{cat} 失敗: {e}")
        
    except Exception as e:
        print(f"❌ 建立分區失敗: {e}")

def main():
    """主函數"""
    print("🚀 開始初始化 Milvus 集合...")
    
    # 連接到 Milvus
    if not connect_to_milvus():
        return
    
    # 建立集合
    collection = create_collection()
    if not collection:
        return
    
    # 建立分區
    create_partitions(collection)
    
    # 插入範例資料
    insert_sample_data(collection)
    
    # 載入集合
    collection.load()
    
    print("\n🎉 Milvus 集合初始化完成！")
    print(f"📊 集合名稱: {COLLECTION_NAME}")
    print(f"🔢 向量維度: {DIMENSION}")
    print(f"🏷️  標籤數量: 20")
    print(f"🌐 支援語言: zh, en, ja, ko")
    print(f"📂 支援分類: 科技, 商業, 教育, 娛樂, 新聞")
    
    # 顯示集合統計
    print(f"\n📈 集合統計:")
    print(f"   - 實體數量: {collection.num_entities}")
    print(f"   - 分區數量: {len(collection.partitions)}")

if __name__ == "__main__":
    main() 