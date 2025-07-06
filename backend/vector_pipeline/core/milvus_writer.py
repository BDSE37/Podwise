"""
Milvus 資料寫入器
負責將向量資料寫入 Milvus 向量資料庫
"""

import logging
from typing import Dict, List, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np

logger = logging.getLogger(__name__)


class MilvusWriter:
    """Milvus 資料寫入器"""
    
    def __init__(self, milvus_config: Dict[str, Any]):
        """
        初始化 Milvus 寫入器
        
        Args:
            milvus_config: Milvus 配置字典
        """
        self.milvus_config = milvus_config
        self.connected = False
        
    def connect(self) -> None:
        """連接到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_config["host"],
                port=self.milvus_config["port"]
            )
            self.connected = True
            logger.info(f"成功連接到 Milvus: {self.milvus_config['host']}:{self.milvus_config['port']}")
        except Exception as e:
            logger.error(f"Milvus 連接失敗: {e}")
            raise
    
    def create_collection(self, collection_name: str, embedding_dim: int = 1024) -> str:
        """
        創建 Milvus 集合
        
        Args:
            collection_name: 集合名稱
            embedding_dim: 嵌入向量維度
            
        Returns:
            集合名稱
        """
        if not self.connected:
            self.connect()
            
        try:
            # 檢查集合是否存在
            if utility.has_collection(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return collection_name
            
            # 定義字段
            fields = [
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="episode_id", dtype=DataType.INT64),
                FieldSchema(name="podcast_id", dtype=DataType.INT64),
                FieldSchema(name="episode_title", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=10),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
                # 向量標籤欄位
                FieldSchema(name="tag_1", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
                FieldSchema(name="tag_2", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
                FieldSchema(name="tag_3", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim)
            ]
            
            # 創建集合
            schema = CollectionSchema(
                fields=fields,
                description=f"Podcast Chunks Collection with Vector Tags (dim: {embedding_dim})"
            )
            collection = Collection(name=collection_name, schema=schema)
            
            # 創建索引
            index_params = {
                "metric_type": self.milvus_config.get("metric_type", "COSINE"),
                "index_type": self.milvus_config.get("index_type", "IVF_FLAT"),
                "params": {"nlist": self.milvus_config.get("nlist", 1024)}
            }
            
            # 為所有向量欄位創建索引
            collection.create_index(field_name="embedding", index_params=index_params)
            collection.create_index(field_name="tag_1", index_params=index_params)
            collection.create_index(field_name="tag_2", index_params=index_params)
            collection.create_index(field_name="tag_3", index_params=index_params)
            
            logger.info(f"成功創建集合 {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"創建集合失敗: {e}")
            raise
    
    def drop_collection(self, collection_name: str) -> None:
        """
        刪除集合
        
        Args:
            collection_name: 集合名稱
        """
        if not self.connected:
            self.connect()
            
        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                logger.info(f"成功刪除集合 {collection_name}")
            else:
                logger.warning(f"集合 {collection_name} 不存在")
        except Exception as e:
            logger.error(f"刪除集合失敗: {e}")
            raise
    
    def insert_data(self, collection_name: str, data: Dict[str, List]) -> int:
        """
        插入資料到集合
        
        Args:
            collection_name: 集合名稱
            data: 要插入的資料字典
            
        Returns:
            插入的資料數量
        """
        if not self.connected:
            self.connect()
            
        try:
            collection = Collection(collection_name)
            
            # 定義欄位順序（必須與 schema 一致）
            field_order = [
                "chunk_id", "chunk_index", "episode_id", "podcast_id", 
                "episode_title", "chunk_text", "embedding", "language", 
                "created_at", "source_model", "podcast_name", "author", 
                "category", "tag_1", "tag_2", "tag_3"
            ]
            
            # 將 dict 轉換為 list of list（每個欄位一個 list）
            insert_data = [data[field] for field in field_order]
            
            # 插入資料
            insert_result = collection.insert(insert_data)
            inserted_count = len(data.get("chunk_id", []))
            
            logger.info(f"成功插入 {inserted_count} 筆資料到集合 {collection_name}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"插入資料失敗: {e}")
            raise
    
    def batch_insert(self, collection_name: str, data_list: List[Dict[str, Any]], 
                    batch_size: int = 100) -> int:
        """
        批次插入資料
        
        Args:
            collection_name: 集合名稱
            data_list: 資料列表
            batch_size: 批次大小
            
        Returns:
            總插入資料數量
        """
        total_inserted = 0
        
        try:
            for i in range(0, len(data_list), batch_size):
                batch_data = data_list[i:i + batch_size]
                
                # 每次批次前檢查連線
                if not self.connected:
                    self.connect()
                
                # 準備插入資料格式
                insert_data = self._prepare_batch_data(batch_data)
                
                # 插入批次資料
                inserted_count = self.insert_data(collection_name, insert_data)
                total_inserted += inserted_count
                
                logger.info(f"批次 {i//batch_size + 1}: 插入 {inserted_count} 筆資料")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"批次插入失敗: {e}")
            # 嘗試重新連線
            try:
                self.connect()
            except:
                pass
            raise
    
    def _prepare_batch_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        準備批次插入資料格式
        
        Args:
            data_list: 資料列表
            
        Returns:
            格式化後的資料字典
        """
        batch_data = {
            "chunk_id": [],
            "chunk_index": [],
            "episode_id": [],
            "podcast_id": [],
            "episode_title": [],
            "chunk_text": [],
            "embedding": [],
            "language": [],
            "created_at": [],
            "source_model": [],
            "podcast_name": [],
            "author": [],
            "category": [],
            "tag_1": [],
            "tag_2": [],
            "tag_3": []
        }
        
        for data in data_list:
            for key in batch_data:
                if key in data:
                    value = data[key]
                    # 強制 chunk_id 為 str，且如果是 list 只取第一個元素
                    if key == "chunk_id":
                        if isinstance(value, list):
                            value = value[0] if value else ""
                        value = str(value)
                    batch_data[key].append(value)
                else:
                    # 提供預設值
                    if key in ["tag_1", "tag_2", "tag_3"] and "embedding" in data:
                        # 使用主要嵌入向量作為標籤向量的預設值
                        batch_data[key].append(data["embedding"])
                    elif key in ["embedding", "tag_1", "tag_2", "tag_3"]:
                        batch_data[key].append([])
                    else:
                        batch_data[key].append("")
        
        return batch_data
    
    def load_collection(self, collection_name: str) -> None:
        """
        載入集合到記憶體
        
        Args:
            collection_name: 集合名稱
        """
        if not self.connected:
            self.connect()
            
        try:
            collection = Collection(collection_name)
            collection.load()
            logger.info(f"成功載入集合 {collection_name}")
        except Exception as e:
            logger.error(f"載入集合失敗: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        獲取集合統計資訊
        
        Args:
            collection_name: 集合名稱
            
        Returns:
            統計資訊字典
        """
        if not self.connected:
            self.connect()
            
        try:
            collection = Collection(collection_name)
            stats = {
                "collection_name": collection_name,
                "num_entities": collection.num_entities,
                "schema": {field.name: str(field.dtype) for field in collection.schema.fields}
            }
            return stats
        except Exception as e:
            logger.error(f"獲取集合統計失敗: {e}")
            raise
    
    def close(self) -> None:
        """關閉連接"""
        if self.connected:
            connections.disconnect("default")
            self.connected = False
            logger.info("Milvus 連接已關閉") 

    def clear_collection(self, collection_name: str) -> None:
        """
        清空集合內容（保留集合結構）
        
        Args:
            collection_name: 集合名稱
        """
        if not self.connected:
            self.connect()
            
        try:
            if utility.has_collection(collection_name):
                collection = Collection(collection_name)
                # 刪除所有資料（使用正確的 filter 表達式）
                collection.delete("chunk_id != ''")  # 刪除所有有 chunk_id 的資料
                logger.info(f"成功清空集合 {collection_name} 的內容")
            else:
                logger.warning(f"集合 {collection_name} 不存在")
        except Exception as e:
            logger.error(f"清空集合失敗: {e}")
            raise 