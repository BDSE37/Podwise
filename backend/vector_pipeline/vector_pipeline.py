#!/usr/bin/env python3
"""
向量化管道
整合文本處理和 Milvus 向量資料庫操作
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
from .text_processor import TextProcessor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorPipeline:
    """
    向量化管道
    整合文本處理和 Milvus 向量資料庫操作
    """
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 milvus_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 tag_csv_path: str = "csv/TAG_info.csv",
                 embedding_model: str = "BAAI/bge-m3",
                 max_chunk_size: int = 1024) -> None:
        """
        初始化向量化管道
        
        Args:
            mongo_config: MongoDB 配置
            milvus_config: Milvus 配置
            postgres_config: PostgreSQL 配置
            tag_csv_path: 標籤 CSV 檔案路徑
            embedding_model: 嵌入模型名稱
            max_chunk_size: 最大分塊大小
        """
        self.mongo_config = mongo_config
        self.milvus_config = milvus_config
        self.postgres_config = postgres_config
        self.tag_csv_path = tag_csv_path
        self.embedding_model = embedding_model
        self.max_chunk_size = max_chunk_size
        
        # 初始化文本處理器
        self.text_processor = TextProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            tag_csv_path=tag_csv_path,
            embedding_model=embedding_model,
            max_chunk_size=max_chunk_size
        )
        
        # Milvus 連接
        self.milvus_connected = False
        
    def connect_milvus(self) -> None:
        """連接到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_config["host"],
                port=self.milvus_config["port"]
            )
            self.milvus_connected = True
            logger.info(f"成功連接到 Milvus: {self.milvus_config['host']}:{self.milvus_config['port']}")
        except Exception as e:
            logger.error(f"Milvus 連接失敗: {e}")
            raise
    
    def create_collection(self, collection_name: Optional[str] = None) -> str:
        """創建 Milvus 集合"""
        if not self.milvus_connected:
            self.connect_milvus()
            
        collection_name = collection_name or self.milvus_config.get("collection_name", "podwise_podcasts")
        
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
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # BGE-M3 維度
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=10),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1000)
            ]
            
            # 創建集合
            schema = CollectionSchema(
                fields=fields,
                description=f"Podwise Podcasts Collection with {self.embedding_model} embeddings"
            )
            collection = Collection(name=collection_name, schema=schema)
            
            # 創建索引
            index_params = {
                "metric_type": self.milvus_config.get("metric_type", "COSINE"),
                "index_type": self.milvus_config.get("index_type", "IVF_FLAT"),
                "params": {"nlist": self.milvus_config.get("nlist", 1024)}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            logger.info(f"成功創建集合 {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"創建集合失敗: {e}")
            raise
    
    def drop_collection(self, collection_name: str) -> None:
        """刪除集合"""
        if not self.milvus_connected:
            self.connect_milvus()
            
        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                logger.info(f"成功刪除集合 {collection_name}")
            else:
                logger.warning(f"集合 {collection_name} 不存在")
        except Exception as e:
            logger.error(f"刪除集合失敗: {e}")
            raise
    
    def recreate_collection(self, collection_name: Optional[str] = None) -> str:
        """重建集合"""
        collection_name = collection_name or self.milvus_config.get("collection_name", "podwise_podcasts")
        
        # 刪除舊集合
        self.drop_collection(collection_name)
        
        # 創建新集合
        return self.create_collection(collection_name)
    
    def process_and_vectorize(self, 
                             collection_name: str,
                             mongo_collection: str,
                             text_field: str = 'content',
                             query: Optional[Dict[str, Any]] = None,
                             limit: Optional[int] = None,
                             batch_size: int = 100) -> Dict[str, Any]:
        """
        處理文檔並向量化
        
        Args:
            collection_name: Milvus 集合名稱
            mongo_collection: MongoDB 集合名稱
            text_field: 文本欄位名稱
            query: MongoDB 查詢條件
            limit: 限制文檔數量
            batch_size: 批次處理大小
            
        Returns:
            處理結果統計
        """
        try:
            # 1. 處理文檔
            logger.info("開始處理 MongoDB 文檔...")
            processed_chunks = self.text_processor.process_collection(
                collection_name=mongo_collection,
                text_field=text_field,
                query=query,
                limit=limit
            )
            
            if not processed_chunks:
                logger.warning("沒有處理到任何文檔")
                return {"status": "no_documents", "processed_chunks": 0}
            
            # 2. 生成嵌入向量
            logger.info("開始生成嵌入向量...")
            texts = [chunk['chunk_text'] for chunk in processed_chunks]
            embeddings = self.text_processor.generate_embeddings(texts)
            
            # 3. 準備插入資料
            logger.info("準備插入資料到 Milvus...")
            collection = Collection(collection_name)
            
            # 分批插入
            total_inserted = 0
            for i in range(0, len(processed_chunks), batch_size):
                batch_chunks = processed_chunks[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                # 準備插入資料
                insert_data = self._prepare_insert_data(batch_chunks, batch_embeddings)
                
                # 插入到 Milvus
                collection.insert(insert_data)
                total_inserted += len(batch_chunks)
                
                logger.info(f"已插入 {total_inserted}/{len(processed_chunks)} 個文檔")
            
            # 4. 載入集合
            logger.info("載入集合...")
            collection.load()
            
            # 5. 統計資訊
            stats = {
                "status": "success",
                "processed_chunks": len(processed_chunks),
                "inserted_chunks": total_inserted,
                "embedding_dimension": embeddings.shape[1],
                "collection_name": collection_name,
                "tag_statistics": self.text_processor.get_tag_statistics()
            }
            
            logger.info(f"向量化完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"處理和向量化失敗: {e}")
            raise
    
    def _prepare_insert_data(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> Dict[str, List]:
        """準備插入資料"""
        data = {
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
            "tags": []
        }
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {})
            
            data["chunk_id"].append(chunk['chunk_id'])
            data["chunk_index"].append(chunk['chunk_index'])
            data["episode_id"].append(metadata.get('episode_id', 0))
            data["podcast_id"].append(metadata.get('podcast_id', 0))
            data["episode_title"].append(metadata.get('episode_title', ''))
            data["chunk_text"].append(chunk['chunk_text'])
            data["embedding"].append(embeddings[i].tolist())
            data["language"].append('zh')  # 預設中文
            data["created_at"].append(str(metadata.get('created_at', '')) if metadata.get('created_at') else '')
            data["source_model"].append(self.embedding_model)
            data["podcast_name"].append(metadata.get('podcast_name', ''))
            data["author"].append(metadata.get('author', ''))
            data["category"].append(metadata.get('category', ''))
            data["tags"].append(','.join(chunk['tags']))
        
        return data
    
    def search_similar(self, 
                      query_text: str, 
                      collection_name: str,
                      top_k: int = 10,
                      search_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜尋相似文檔
        
        Args:
            query_text: 查詢文本
            collection_name: 集合名稱
            top_k: 返回結果數量
            search_params: 搜尋參數
            
        Returns:
            相似文檔列表
        """
        if not self.milvus_connected:
            self.connect_milvus()
            
        try:
            collection = Collection(collection_name)
            collection.load()
            
            # 生成查詢向量
            query_embedding = self.text_processor.generate_embeddings([query_text])
            
            # 搜尋參數
            if search_params is None:
                search_params = {
                    "metric_type": "COSINE",
                    "params": {"nprobe": 10}
                }
            
            # 執行搜尋
            results = collection.search(
                data=query_embedding,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_text", "episode_title", "podcast_name", "tags"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.id,
                        "score": hit.score,
                        "chunk_text": hit.entity.get("chunk_text", ""),
                        "episode_title": hit.entity.get("episode_title", ""),
                        "podcast_name": hit.entity.get("podcast_name", ""),
                        "tags": hit.entity.get("tags", "").split(",") if hit.entity.get("tags") else []
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜尋失敗: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """獲取集合統計資訊"""
        if not self.milvus_connected:
            self.connect_milvus()
            
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
        self.text_processor.close()
        if self.milvus_connected:
            connections.disconnect("default")
            logger.info("Milvus 連接已關閉")


def test_vector_pipeline() -> None:
    """測試向量化管道"""
    # 測試配置
    mongo_config = {
        "host": "localhost",
        "port": 27017,
        "database": "podwise",
        "username": "bdse37",
        "password": "111111"
    }
    
    postgres_config = {
        "host": "localhost",
        "port": 5432,
        "database": "podcast",
        "user": "bdse37",
        "password": "111111"
    }
    
    milvus_config = {
        "host": "localhost",
        "port": "19530",
        "collection_name": "podwise_podcasts_test",
        "dim": 1024,
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "nlist": 1024
    }
    
    pipeline = VectorPipeline(mongo_config, milvus_config, postgres_config)
    
    try:
        # 創建集合
        collection_name = pipeline.create_collection()
        print(f"創建集合: {collection_name}")
        
        # 處理和向量化 (限制文檔數量)
        stats = pipeline.process_and_vectorize(
            collection_name=collection_name,
            mongo_collection="transcripts",
            limit=3  # 只處理 3 個文檔進行測試
        )
        print(f"處理結果: {stats}")
        
        # 搜尋測試
        results = pipeline.search_similar(
            query_text="人工智慧技術發展",
            collection_name=collection_name,
            top_k=2
        )
        print(f"搜尋結果: {len(results)} 個結果")
        
        # 獲取統計資訊
        collection_stats = pipeline.get_collection_stats(collection_name)
        print(f"集合統計: {collection_stats}")
        
        # 清理測試集合
        pipeline.drop_collection(collection_name)
        print(f"清理測試集合: {collection_name}")
        
    finally:
        pipeline.close()


if __name__ == "__main__":
    test_vector_pipeline() 