"""
初始化 Milvus 集合
創建必要的集合和索引
"""

import os
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from config import MILVUS_CONFIG

def init_milvus():
    """初始化 Milvus 集合"""
    try:
        # 連接到 Milvus
        connections.connect(
            alias="default",
            host=MILVUS_CONFIG["host"],
            port=MILVUS_CONFIG["port"]
        )
        
        # 檢查集合是否存在
        if utility.has_collection(MILVUS_CONFIG["collection_name"]):
            print(f"集合 {MILVUS_CONFIG['collection_name']} 已存在")
            return
            
        # 定義字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=MILVUS_CONFIG["dim"]),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        
        # 創建集合
        schema = CollectionSchema(fields=fields, description="Podwise 文檔集合")
        collection = Collection(name=MILVUS_CONFIG["collection_name"], schema=schema)
        
        # 創建索引
        index_params = {
            "metric_type": MILVUS_CONFIG["metric_type"],
            "index_type": MILVUS_CONFIG["index_type"],
            "params": {"nlist": MILVUS_CONFIG["nlist"]}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        print(f"成功創建集合 {MILVUS_CONFIG['collection_name']}")
        
    except Exception as e:
        print(f"初始化 Milvus 失敗: {str(e)}")
        raise
    finally:
        connections.disconnect("default")

if __name__ == "__main__":
    init_milvus() 