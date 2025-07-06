#!/usr/bin/env python3
"""
播客資料處理管線
處理 MongoDB collection 的長文本切分、標籤貼標和向量化

功能：
1. 從 MongoDB 讀取長文本
2. 清理表情符號和特殊字元
3. 智能切分文本為 chunks
4. 基於 TAG_info.csv 進行標籤匹配
5. 如果沒有匹配標籤，使用智能標籤系統
6. 生成向量嵌入
7. 儲存到 Milvus
8. 錯誤記錄和處理
9. 批次進度管理
"""

import logging
import json
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility
import emoji

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from vector_pipeline.error_logger import ErrorLogger, ErrorRecord
from rag_pipeline.utils.tag_processor import TagProcessor

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，移除表情符號和特殊字元
        
        Args:
            text: 原始文本
            
        Returns:
            清理後的文本
        """
        if not text:
            return ""
        
        # 移除表情符號
        text = emoji.replace_emojis(text, replace='')
        
        # 移除顏文字
        text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', text)
        
        # 移除多餘的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除開頭和結尾的空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_title(title: str) -> str:
        """
        清理標題，移除表情符號和特殊字元
        
        Args:
            title: 原始標題
            
        Returns:
            清理後的標題
        """
        if not title:
            return ""
        
        # 移除表情符號
        title = emoji.replace_emojis(title, replace='')
        
        # 移除特殊字元，保留中文、英文、數字和基本標點
        title = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', title)
        
        # 移除多餘的空白
        title = re.sub(r'\s+', ' ', title)
        
        # 移除開頭和結尾的空白
        title = title.strip()
        
        return title


class CollectionProcessor:
    """Collection 處理器"""
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 milvus_config: Dict[str, Any],
                 tag_csv_path: str = "TAG_info.csv",
                 embedding_model: str = "BAAI/bge-m3",
                 max_chunk_size: int = 1024,
                 batch_size: int = 100):
        """
        初始化處理器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置
            milvus_config: Milvus 配置
            tag_csv_path: 標籤檔案路徑
            embedding_model: 嵌入模型名稱
            max_chunk_size: 最大分塊大小
            batch_size: 批次大小
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.milvus_config = milvus_config
        self.tag_csv_path = tag_csv_path
        self.embedding_model = embedding_model
        self.max_chunk_size = max_chunk_size
        self.batch_size = batch_size
        
        # 初始化組件
        self.mongo_client: Optional[MongoClient] = None
        self.postgres_conn: Optional[psycopg2.extensions.connection] = None
        self.embedding_model_instance: Optional[SentenceTransformer] = None
        self.tag_processor: Optional[TagProcessor] = None
        self.error_logger = ErrorLogger()
        self.text_cleaner = TextCleaner()
        
        # 初始化連接
        self._initialize_connections()
        self._initialize_components()
        
    def _initialize_connections(self):
        """初始化資料庫連接"""
        try:
            # MongoDB 連接
            if self.mongo_config.get("password"):
                uri = f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@{self.mongo_config['host']}:{self.mongo_config['port']}"
            else:
                uri = f"mongodb://{self.mongo_config['host']}:{self.mongo_config['port']}"
            
            self.mongo_client = MongoClient(uri)
            logger.info(f"成功連接到 MongoDB: {self.mongo_config['host']}:{self.mongo_config['port']}")
            
            # PostgreSQL 連接
            self.postgres_conn = psycopg2.connect(
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=self.postgres_config['database'],
                user=self.postgres_config['user'],
                password=self.postgres_config['password']
            )
            logger.info(f"成功連接到 PostgreSQL: {self.postgres_config['host']}:{self.postgres_config['port']}")
            
            # Milvus 連接
            connections.connect(
                alias="default",
                host=self.milvus_config['host'],
                port=self.milvus_config['port']
            )
            logger.info(f"成功連接到 Milvus: {self.milvus_config['host']}:{self.milvus_config['port']}")
            
        except Exception as e:
            logger.error(f"初始化連接失敗: {e}")
            raise
    
    def _initialize_components(self):
        """初始化組件"""
        try:
            # 載入嵌入模型
            self.embedding_model_instance = SentenceTransformer(self.embedding_model)
            logger.info(f"成功載入嵌入模型: {self.embedding_model}")
            
            # 載入標籤處理器
            if Path(self.tag_csv_path).exists():
                self.tag_processor = TagProcessor(self.tag_csv_path)
                logger.info(f"成功載入標籤處理器: {self.tag_csv_path}")
            else:
                logger.warning(f"標籤檔案不存在: {self.tag_csv_path}")
                
        except Exception as e:
            logger.error(f"初始化組件失敗: {e}")
            raise
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        將文本切分為 chunks
        
        Args:
            text: 原始文本
            
        Returns:
            文本塊列表
        """
        if not text:
            return []
        
        # 清理文本
        text = self.text_cleaner.clean_text(text)
        
        # 按句子切分
        sentences = re.split(r'[。！？.!?]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果當前 chunk 加上新句子超過最大長度，保存當前 chunk
            if len(current_chunk) + len(sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + "。"
        
        # 添加最後一個 chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_tags(self, chunk_text: str) -> List[str]:
        """
        提取標籤
        
        Args:
            chunk_text: 文本塊
            
        Returns:
            標籤列表
        """
        try:
            tags = []
            
            # 第一階段：使用 TagProcessor
            if self.tag_processor:
                try:
                    result = self.tag_processor.categorize_content(chunk_text)
                    tags = result.get('tags', [])
                    logger.debug(f"TagProcessor 提取標籤: {tags}")
                except Exception as e:
                    logger.warning(f"TagProcessor 提取標籤失敗: {e}")
                    tags = []
            
            # 第二階段：如果沒有標籤，使用智能標籤系統
            if not tags:
                tags = self._intelligent_tag_extraction(chunk_text)
                logger.debug(f"智能標籤提取: {tags}")
            
            # 第三階段：最終備援
            if not tags:
                tags = self._fallback_tag_extraction(chunk_text)
                logger.debug(f"備援標籤提取: {tags}")
            
            # 驗證和清理標籤
            tags = self._validate_and_clean_tags(tags, chunk_text)
            
            return tags[:3]  # 限制最多 3 個標籤
            
        except Exception as e:
            logger.error(f"提取標籤失敗: {e}")
            return self._fallback_tag_extraction(chunk_text)
    
    def _intelligent_tag_extraction(self, chunk_text: str) -> List[str]:
        """智能標籤提取"""
        tags = []
        chunk_lower = chunk_text.lower()
        
        # 關鍵字匹配
        keyword_mapping = {
            'ai': ['AI', '人工智慧'],
            '科技': ['科技', '技術'],
            '商業': ['商業', '企業'],
            '教育': ['教育', '學習'],
            '創業': ['創業', '新創'],
            '管理': ['管理', '領導'],
            '投資': ['投資', '理財'],
            '健康': ['健康', '運動'],
            '娛樂': ['娛樂', '音樂'],
            '政治': ['政治', '政策']
        }
        
        for keyword, tag_list in keyword_mapping.items():
            if keyword in chunk_lower:
                tags.extend(tag_list)
        
        return list(set(tags))  # 去重
    
    def _fallback_tag_extraction(self, chunk_text: str) -> List[str]:
        """備援標籤提取"""
        # 基於文本長度和內容的基本標籤
        if len(chunk_text) > 500:
            return ['長文本', '詳細內容']
        elif len(chunk_text) > 200:
            return ['中等文本', '一般內容']
        else:
            return ['短文本', '簡要內容']
    
    def _validate_and_clean_tags(self, tags: List[str], chunk_text: str) -> List[str]:
        """驗證和清理標籤"""
        valid_tags = []
        
        for tag in tags:
            if tag and len(tag.strip()) > 0:
                # 清理標籤
                clean_tag = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s]', '', tag.strip())
                if clean_tag and len(clean_tag) <= 20:  # 限制標籤長度
                    valid_tags.append(clean_tag)
        
        return valid_tags
    
    def get_episode_metadata(self, episode_id: int) -> Dict[str, Any]:
        """
        從 PostgreSQL 獲取 episode 元資料
        
        Args:
            episode_id: Episode ID
            
        Returns:
            Episode 元資料字典
        """
        try:
            with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.id as episode_id,
                    e.podcast_id,
                    e.title as episode_title,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    e.created_at
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.id
                WHERE e.id = %s
                """
                
                cursor.execute(query, (episode_id,))
                result = cursor.fetchone()
                
                if result:
                    metadata = dict(result)
                    # 清理標題
                    metadata['episode_title'] = self.text_cleaner.clean_title(metadata['episode_title'])
                    return metadata
                else:
                    logger.warning(f"找不到 episode_id {episode_id} 的元資料")
                    return {
                        'episode_id': episode_id,
                        'podcast_id': 0,
                        'episode_title': '',
                        'podcast_name': '',
                        'author': '',
                        'category': '',
                        'created_at': None
                    }
                    
        except Exception as e:
            logger.error(f"獲取 episode 元資料失敗: {e}")
            return {
                'episode_id': episode_id,
                'podcast_id': 0,
                'episode_title': '',
                'podcast_name': '',
                'author': '',
                'category': '',
                'created_at': None
            }
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        生成文本嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量陣列
        """
        try:
            embeddings = self.embedding_model_instance.encode(texts, normalize_embeddings=True)
            return embeddings
        except Exception as e:
            logger.error(f"生成嵌入向量失敗: {e}")
            raise
    
    def write_to_milvus(self, collection_name: str, data: List[Dict[str, Any]]) -> None:
        """
        寫入資料到 Milvus
        
        Args:
            collection_name: Collection 名稱
            data: 資料列表
        """
        try:
            if not utility.has_collection(collection_name):
                logger.warning(f"Collection {collection_name} 不存在")
                return
            
            collection = Collection(collection_name)
            collection.load()
            
            # 準備插入資料
            insert_data = []
            for item in data:
                insert_data.append({
                    'chunk_id': item['chunk_id'],
                    'chunk_text': item['chunk_text'],
                    'embedding': item['embedding'].tolist(),
                    'episode_id': item['episode_id'],
                    'podcast_id': item['podcast_id'],
                    'tags': item['tags']
                })
            
            # 插入資料
            collection.insert(insert_data)
            logger.info(f"成功插入 {len(insert_data)} 筆資料到 {collection_name}")
            
        except Exception as e:
            logger.error(f"寫入 Milvus 失敗: {e}")
            raise
    
    def process_collection(self, collection_name: str, text_field: str = 'content') -> Dict[str, Any]:
        """
        處理單個 collection
        
        Args:
            collection_name: Collection 名稱
            text_field: 文本欄位名稱
            
        Returns:
            處理結果統計
        """
        try:
            logger.info(f"開始處理 collection: {collection_name}")
            
            # 獲取 MongoDB collection
            db = self.mongo_client[self.mongo_config['database']]
            collection = db[collection_name]
            
            # 獲取所有文件
            documents = list(collection.find({}))
            logger.info(f"找到 {len(documents)} 個文件")
            
            processed_count = 0
            error_count = 0
            total_chunks = 0
            
            for doc in documents:
                try:
                    # 提取文本
                    text = doc.get(text_field, '')
                    if not text:
                        logger.warning(f"文件 {doc.get('_id')} 沒有文本內容")
                        continue
                    
                    # 提取 episode_id
                    episode_id = doc.get('episode_id', 0)
                    if not episode_id:
                        logger.warning(f"文件 {doc.get('_id')} 沒有 episode_id")
                        continue
                    
                    # 獲取元資料
                    metadata = self.get_episode_metadata(episode_id)
                    
                    # 切分文本
                    chunks = self.split_text_into_chunks(text)
                    if not chunks:
                        logger.warning(f"文件 {doc.get('_id')} 切分後沒有 chunks")
                        continue
                    
                    # 處理每個 chunk
                    chunk_data = []
                    for i, chunk in enumerate(chunks):
                        try:
                            # 提取標籤
                            tags = self.extract_tags(chunk)
                            
                            # 生成嵌入向量
                            embedding = self.generate_embeddings([chunk])[0]
                            
                            # 準備 chunk 資料
                            chunk_info = {
                                'chunk_id': f"{episode_id}_{i}",
                                'chunk_index': i,
                                'chunk_text': chunk,
                                'chunk_length': len(chunk),
                                'episode_id': episode_id,
                                'podcast_id': metadata.get('podcast_id', 0),
                                'episode_title': metadata.get('episode_title', ''),
                                'podcast_name': metadata.get('podcast_name', ''),
                                'author': metadata.get('author', ''),
                                'category': metadata.get('category', ''),
                                'created_at': metadata.get('created_at'),
                                'source_model': self.embedding_model,
                                'language': 'zh',
                                'embedding': embedding,
                                'tags': tags
                            }
                            
                            chunk_data.append(chunk_info)
                            total_chunks += 1
                            
                        except Exception as e:
                            error_msg = f"處理 chunk {i} 失敗: {str(e)}"
                            logger.error(error_msg)
                            
                            # 記錄錯誤
                            self.error_logger.log_error(
                                collection_name=collection_name,
                                rss_id=str(doc.get('_id')),
                                title=metadata.get('episode_title', ''),
                                error_type="chunk_processing",
                                error_message=error_msg,
                                additional_info={
                                    'episode_id': episode_id,
                                    'chunk_index': i,
                                    'chunk_text': chunk[:100] + "..." if len(chunk) > 100 else chunk
                                }
                            )
                            error_count += 1
                    
                    # 批次寫入 Milvus
                    if chunk_data:
                        self.write_to_milvus("podcast_chunks", chunk_data)
                        processed_count += 1
                    
                except Exception as e:
                    error_msg = f"處理文件失敗: {str(e)}"
                    logger.error(error_msg)
                    
                    # 記錄錯誤
                    self.error_logger.log_error(
                        collection_name=collection_name,
                        rss_id=str(doc.get('_id')),
                        title=doc.get('title', ''),
                        error_type="document_processing",
                        error_message=error_msg,
                        additional_info={
                            'episode_id': doc.get('episode_id', 0),
                            'text_length': len(doc.get(text_field, ''))
                        }
                    )
                    error_count += 1
            
            result = {
                'collection_name': collection_name,
                'total_documents': len(documents),
                'processed_documents': processed_count,
                'error_count': error_count,
                'total_chunks': total_chunks,
                'success_rate': (processed_count / len(documents)) * 100 if documents else 0
            }
            
            logger.info(f"Collection {collection_name} 處理完成: {result}")
            return result
            
        except Exception as e:
            error_msg = f"處理 collection {collection_name} 失敗: {str(e)}"
            logger.error(error_msg)
            
            # 記錄錯誤
            self.error_logger.log_error(
                collection_name=collection_name,
                rss_id="",
                title="",
                error_type="collection_processing",
                error_message=error_msg
            )
            
            return {
                'collection_name': collection_name,
                'total_documents': 0,
                'processed_documents': 0,
                'error_count': 1,
                'total_chunks': 0,
                'success_rate': 0
            }
    
    def update_collection_titles(self, collection_name: str, pattern: str = "EPXXX_股癌") -> None:
        """
        更新 collection 中的節目標題
        
        Args:
            collection_name: Collection 名稱
            pattern: 標題模式
        """
        try:
            logger.info(f"開始更新 collection {collection_name} 的標題")
            
            db = self.mongo_client[self.mongo_config['database']]
            collection = db[collection_name]
            
            # 獲取所有文件
            documents = list(collection.find({}))
            logger.info(f"找到 {len(documents)} 個文件需要更新標題")
            
            updated_count = 0
            for i, doc in enumerate(documents):
                try:
                    # 生成新標題
                    new_title = f"EP{i+1:03d}_股癌"
                    
                    # 更新標題
                    collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': {'title': new_title}}
                    )
                    
                    updated_count += 1
                    logger.debug(f"更新標題: {doc.get('title', '')} -> {new_title}")
                    
                except Exception as e:
                    logger.error(f"更新標題失敗: {e}")
            
            logger.info(f"成功更新 {updated_count} 個標題")
            
        except Exception as e:
            logger.error(f"更新標題失敗: {e}")
            raise
    
    def close(self):
        """關閉連接"""
        try:
            if self.mongo_client:
                self.mongo_client.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            logger.info("已關閉所有資料庫連接")
        except Exception as e:
            logger.error(f"關閉連接失敗: {e}")


def main():
    """主函數"""
    # 配置
    mongo_config = {
        'host': 'localhost',
        'port': 27017,
        'database': 'podwise',
        'username': '',
        'password': ''
    }
    
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'podwise',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    milvus_config = {
        'host': 'localhost',
        'port': 19530
    }
    
    # 要處理的 collections
    collections = ['1500839292']  # 可以添加更多 collection
    
    try:
        # 初始化處理器
        processor = CollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            tag_csv_path="TAG_info.csv",
            embedding_model="BAAI/bge-m3",
            max_chunk_size=1024,
            batch_size=100
        )
        
        # 處理每個 collection
        results = []
        for collection_name in collections:
            try:
                # 更新標題
                processor.update_collection_titles(collection_name)
                
                # 處理 collection
                result = processor.process_collection(collection_name)
                results.append(result)
                
            except Exception as e:
                logger.error(f"處理 collection {collection_name} 失敗: {e}")
                results.append({
                    'collection_name': collection_name,
                    'total_documents': 0,
                    'processed_documents': 0,
                    'error_count': 1,
                    'total_chunks': 0,
                    'success_rate': 0
                })
        
        # 輸出結果
        logger.info("處理完成，結果統計:")
        for result in results:
            logger.info(f"Collection {result['collection_name']}: "
                       f"處理 {result['processed_documents']}/{result['total_documents']} 文件, "
                       f"成功率 {result['success_rate']:.2f}%, "
                       f"錯誤 {result['error_count']} 個, "
                       f"總 chunks {result['total_chunks']} 個")
        
        # 關閉連接
        processor.close()
        
    except Exception as e:
        logger.error(f"主程序執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 