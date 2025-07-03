"""
統一內容處理器 - 重構版本
整合所有內容處理功能，包括文檔處理、MongoDB 文本處理和內容分類
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import numpy as np
from pymongo import MongoClient
from pymilvus import connections, Collection, utility
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
import torch

# 導入分離的模組
from .content_models import ContentCategory, ContentMetadata, ContentSummary, ParagraphMetadata
from .content_categorizer import ContentCategorizer
from .content_summarizer import ContentSummarizer

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedContentProcessor:
    """
    統一內容處理器 - 重構版本
    
    整合功能：
    - 文檔處理和結構化
    - MongoDB 長文本處理
    - 內容分類和標籤生成
    - 向量化和存儲
    - 摘要生成
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        mongodb_uri: str = "mongodb://bdse37:111111@worker3:30017/",
        mongodb_db: str = "podcast",
        mongodb_collection: str = "transcripts",
        milvus_host: str = "192.168.32.86",
        milvus_port: int = 19530,
        milvus_collection_name: str = "podwise_documents",
        qwen_model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        embedding_model_name: str = "BAAI/bge-m3",
        max_tags_per_chunk: int = 10,
        enable_mongodb: bool = True,
        enable_milvus: bool = True
    ):
        """
        初始化統一內容處理器
        
        Args:
            data_dir: 本地資料目錄路徑
            mongodb_uri: MongoDB 連接字串
            mongodb_db: MongoDB 資料庫名稱
            mongodb_collection: MongoDB 集合名稱
            milvus_host: Milvus 主機地址
            milvus_port: Milvus 端口
            milvus_collection_name: Milvus 集合名稱
            qwen_model_name: Qwen 模型名稱
            embedding_model_name: 嵌入模型名稱
            max_tags_per_chunk: 每個文本塊的最大標籤數量
            enable_mongodb: 是否啟用 MongoDB 功能
            enable_milvus: 是否啟用 Milvus 功能
        """
        self.data_dir = Path(data_dir) if data_dir else None
        self.mongodb_uri = mongodb_uri
        self.mongodb_db = mongodb_db
        self.mongodb_collection = mongodb_collection
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.milvus_collection_name = milvus_collection_name
        self.qwen_model_name = qwen_model_name
        self.embedding_model_name = embedding_model_name
        self.max_tags_per_chunk = max_tags_per_chunk
        
        # 初始化分離的組件
        self.categorizer = ContentCategorizer()
        self.summarizer = ContentSummarizer()
        
        # 初始化連接和模型
        if enable_mongodb:
            self._init_mongodb()
        if enable_milvus:
            self._init_milvus()
        if enable_mongodb or enable_milvus:
            self._init_models()
            
    def _init_mongodb(self):
        """初始化 MongoDB 連接"""
        try:
            logger.info(f"🔗 連接到 MongoDB: {self.mongodb_uri}")
            self.mongo_client = MongoClient(self.mongodb_uri)
            self.mongo_db = self.mongo_client[self.mongodb_db]
            self.mongo_collection = self.mongo_db[self.mongodb_collection]
            
            # 測試連接
            self.mongo_client.admin.command('ping')
            logger.info(f"✅ 成功連接到 MongoDB: {self.mongodb_db}.{self.mongodb_collection}")
        except Exception as e:
            logger.error(f"❌ MongoDB 連接失敗: {str(e)}")
            raise
            
    def _init_milvus(self):
        """初始化 Milvus 連接"""
        try:
            logger.info(f"🔗 連接到 Milvus: {self.milvus_host}:{self.milvus_port}")
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            
            # 檢查集合是否存在，不存在則創建
            if not utility.has_collection(self.milvus_collection_name):
                logger.info(f"📝 創建 Milvus 集合: {self.milvus_collection_name}")
                self._create_milvus_collection()
            else:
                logger.info(f"📖 載入現有 Milvus 集合: {self.milvus_collection_name}")
                self.milvus_collection = Collection(self.milvus_collection_name)
                self.milvus_collection.load()
                
            logger.info(f"✅ 成功連接到 Milvus: {self.milvus_collection_name}")
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {str(e)}")
            raise
            
    def _create_milvus_collection(self):
        """創建 Milvus 集合 (符合 podcast 資料格式，支持多個標籤)"""
        from pymilvus import FieldSchema, CollectionSchema, DataType
        
        # 根據您指定的欄位格式創建，支持更多標籤
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="episode_id", dtype=DataType.INT64),
            FieldSchema(name="podcast_id", dtype=DataType.INT64),
            FieldSchema(name="episode_title", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # BGE-M3 維度
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64),  # TIMESTAMP 用 VARCHAR 表示
            FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
            # 支持更多標籤欄位
            FieldSchema(name="tag_1", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="tag_2", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_3", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_4", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_5", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_6", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_7", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_8", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_9", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="tag_10", dtype=DataType.VARCHAR, max_length=64)
        ]
        
        schema = CollectionSchema(fields, description="Podwise 文檔向量集合")
        self.milvus_collection = Collection(self.milvus_collection_name, schema)
        
        # 創建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.milvus_collection.create_index("embedding", index_params)
        self.milvus_collection.load()
        logger.info(f"✅ 成功創建 Milvus 集合和索引: {self.milvus_collection_name}")
        
    def _init_models(self):
        """初始化模型"""
        try:
            logger.info(f"🤖 載入 Qwen 模型: {self.qwen_model_name}")
            self.qwen_tokenizer = AutoTokenizer.from_pretrained(self.qwen_model_name)
            self.qwen_model = AutoModelForCausalLM.from_pretrained(
                self.qwen_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info(f"🔤 載入嵌入模型: {self.embedding_model_name}")
            self.embedding_tokenizer = AutoTokenizer.from_pretrained(self.embedding_model_name)
            self.embedding_model = AutoModel.from_pretrained(
                self.embedding_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info("✅ 模型載入完成")
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {str(e)}")
            raise
            
    def process_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        split_paragraphs: bool = True,
        generate_summary: bool = True
    ) -> Dict[str, Any]:
        """
        處理文檔內容
        
        Args:
            content: 文檔內容
            metadata: 文檔元數據
            split_paragraphs: 是否分割段落
            generate_summary: 是否生成摘要
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        try:
            # 使用分類器進行內容分類
            category = self.categorizer.categorize_content(
                metadata.get("title", ""), 
                content
            )
            
            # 生成摘要
            summary = None
            if generate_summary:
                summary = self.summarizer.generate_summary(content, category)
            
            # 分割段落
            paragraphs = []
            if split_paragraphs:
                paragraphs = self._split_paragraphs(content)
            
            # 生成標籤
            tags = self.generate_tags_with_qwen(content)
            
            # 生成嵌入向量
            embedding = self.generate_embedding(content)
            
            return {
                "category": category,
                "summary": summary,
                "paragraphs": paragraphs,
                "tags": tags,
                "embedding": embedding,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"❌ 文檔處理失敗: {str(e)}")
            raise
            
    def _split_paragraphs(self, content: str) -> List[str]:
        """分割段落"""
        # 使用多種分隔符分割段落
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', content)
        return [p.strip() for p in paragraphs if p.strip()]
        
    def generate_tags_with_qwen(self, text: str) -> List[str]:
        """使用 Qwen 生成標籤"""
        try:
            # 簡化的標籤生成邏輯
            # 這裡可以整合更複雜的 LLM 調用
            words = text.split()
            # 簡單的關鍵詞提取
            tags = [word for word in words if len(word) > 2][:self.max_tags_per_chunk]
            return tags[:self.max_tags_per_chunk]
        except Exception as e:
            logger.error(f"❌ 標籤生成失敗: {str(e)}")
            return []
        
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        try:
            inputs = self.embedding_tokenizer(
                text,
                return_tensors="pt", 
                max_length=512,
                truncation=True,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                # 使用平均池化
                embeddings = outputs.last_hidden_state.mean(dim=1)
                return embeddings[0].cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"❌ 嵌入生成失敗: {str(e)}")
            return []
            
    def process_mongodb_documents(self, batch_size: int = 100):
        """處理 MongoDB 中的文檔"""
        try:
            cursor = self.mongo_collection.find({}).batch_size(batch_size)
            
            for i, doc in enumerate(cursor):
                    try:
                        # 提取文本內容
                        text = doc.get("transcript", "")
                        if not text:
                            continue
                            
                    # 處理文檔
                    result = self.process_document(
                        content=text,
                        metadata={
                            "episode_id": doc.get("episode_id"),
                            "podcast_id": doc.get("podcast_id"),
                            "title": doc.get("title", ""),
                            "author": doc.get("author", ""),
                            "source": "mongodb"
                        }
                    )
                    
                    # 存儲到 Milvus
                    if result["embedding"]:
                        self._insert_to_milvus(
                            text=text,
                            tags=result["tags"],
                            embedding=result["embedding"],
                            metadata=result["metadata"]
                        )
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"📊 已處理 {i + 1} 個文檔")
                        
                    except Exception as e:
                    logger.error(f"❌ 處理文檔失敗: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"❌ MongoDB 文檔處理失敗: {str(e)}")
            raise
            
    def _insert_to_milvus(self, text: str, tags: List[str], embedding: List[float], metadata: Dict[str, Any]):
        """插入數據到 Milvus"""
        try:
            # 準備標籤數據
            tag_data = tags + [""] * (10 - len(tags))  # 確保有10個標籤欄位
            
            data = [
                [f"chunk_{metadata.get('episode_id', 0)}_{len(text)}"],  # chunk_id
                [0],  # chunk_index
                [metadata.get("episode_id", 0)],  # episode_id
                [metadata.get("podcast_id", 0)],  # podcast_id
                [metadata.get("title", "")],  # episode_title
                [text[:1024]],  # chunk_text (限制長度)
                [embedding],  # embedding
                ["zh"],  # language
                [datetime.now().isoformat()],  # created_at
                [self.embedding_model_name],  # source_model
                [metadata.get("podcast_name", "")],  # podcast_name
                [metadata.get("author", "")],  # author
                [metadata.get("category", "")],  # category
                [tag_data[0]],  # tag_1
                [tag_data[1]],  # tag_2
                [tag_data[2]],  # tag_3
                [tag_data[3]],  # tag_4
                [tag_data[4]],  # tag_5
                [tag_data[5]],  # tag_6
                [tag_data[6]],  # tag_7
                [tag_data[7]],  # tag_8
                [tag_data[8]],  # tag_9
                [tag_data[9]]   # tag_10
            ]
            
            self.milvus_collection.insert(data)
            logger.debug(f"✅ 成功插入數據到 Milvus")
            
        except Exception as e:
            logger.error(f"❌ Milvus 插入失敗: {str(e)}")
            
    def search_similar_texts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜尋相似文本"""
        try:
            # 生成查詢嵌入
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # 搜尋相似向量
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = self.milvus_collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_text", "episode_title", "author", "category"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "score": hit.score,
                        "text": hit.entity.get("chunk_text", ""),
                        "title": hit.entity.get("episode_title", ""),
                        "author": hit.entity.get("author", ""),
                        "category": hit.entity.get("category", "")
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ 相似文本搜尋失敗: {str(e)}")
            return []
            
    def close(self):
        """關閉連接"""
        try:
            if hasattr(self, 'mongo_client'):
                self.mongo_client.close()
            if hasattr(self, 'milvus_collection'):
                self.milvus_collection.release()
            logger.info("✅ 連接已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉連接失敗: {str(e)}")