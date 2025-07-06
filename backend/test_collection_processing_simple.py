#!/usr/bin/env python3
"""
簡化版 Collection 處理測試
測試基本功能，不依賴 sentence-transformers
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

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from vector_pipeline.error_logger import ErrorLogger, ErrorRecord

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本，移除表情符號和特殊字元"""
        if not text:
            return ""
        
        # 移除表情符號（使用 Unicode 範圍）
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # 表情符號
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # 雜項符號
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # 交通運輸
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # 國旗
        text = re.sub(r'[\U00002600-\U000027BF]', '', text)  # 雜項符號
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # 補充符號
        
        # 移除顏文字
        text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', text)
        
        # 移除多餘的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除開頭和結尾的空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_title(title: str) -> str:
        """清理標題，移除表情符號和特殊字元"""
        if not title:
            return ""
        
        # 移除表情符號
        title = re.sub(r'[\U0001F600-\U0001F64F]', '', title)
        title = re.sub(r'[\U0001F300-\U0001F5FF]', '', title)
        title = re.sub(r'[\U0001F680-\U0001F6FF]', '', title)
        title = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', title)
        title = re.sub(r'[\U00002600-\U000027BF]', '', title)
        title = re.sub(r'[\U0001F900-\U0001F9FF]', '', title)
        
        # 移除特殊字元，保留中文、英文、數字和基本標點
        title = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', title)
        
        # 移除多餘的空白
        title = re.sub(r'\s+', ' ', title)
        
        # 移除開頭和結尾的空白
        title = title.strip()
        
        return title


class TagProcessor:
    """標籤處理器"""
    
    def __init__(self, tag_csv_path: str = "TAG_info.csv"):
        self.tag_csv_path = Path(tag_csv_path)
        self.tag_mappings: Dict[str, str] = {}
        self.keyword_to_tags: Dict[str, List[str]] = {}
        self._load_tags()
    
    def _load_tags(self):
        """載入標籤資料"""
        try:
            if not self.tag_csv_path.exists():
                logger.warning(f"標籤檔案不存在: {self.tag_csv_path}")
                self._create_default_tags()
                return
            
            # 讀取 CSV 檔案
            df = pd.read_csv(self.tag_csv_path)
            logger.info(f"成功載入標籤檔案: {self.tag_csv_path}")
            
            # 處理每個類別
            for _, row in df.iterrows():
                main_category = row.get("主要類別", "")
                sub_category = row.get("子類別", "")
                tags_str = row.get("標籤", "")
                weight = row.get("權重", 1.0)
                
                if tags_str and isinstance(tags_str, str):
                    # 分割標籤
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    
                    # 建立關鍵字映射
                    for tag in tags:
                        self.tag_mappings[tag] = main_category
                        self.keyword_to_tags[tag.lower()] = tags
                        
                        # 也將主要類別和子類別加入映射
                        if main_category:
                            self.keyword_to_tags[main_category.lower()] = tags
                        if sub_category:
                            self.keyword_to_tags[sub_category.lower()] = tags
            
            logger.info(f"載入的標籤映射: {self.tag_mappings}")
            
        except Exception as e:
            logger.error(f"載入標籤檔案失敗: {e}")
            self._create_default_tags()
    
    def _create_default_tags(self):
        """建立預設標籤"""
        default_tags = {
            "科技": ["AI", "人工智慧", "科技", "技術"],
            "商業": ["商業", "企業", "投資", "理財"],
            "教育": ["教育", "學習", "知識"],
            "健康": ["健康", "運動", "飲食"],
            "娛樂": ["娛樂", "音樂", "電影"]
        }
        
        for category, tags in default_tags.items():
            for tag in tags:
                self.tag_mappings[tag] = category
                self.keyword_to_tags[tag.lower()] = tags
    
    def extract_tags(self, chunk_text: str) -> List[str]:
        """提取標籤（最少一個，最多三個）"""
        try:
            tags = []
            chunk_lower = chunk_text.lower()
            
            # 第一階段：基於 TAG_info.csv 的標籤匹配
            for keyword, tag_list in self.keyword_to_tags.items():
                if keyword in chunk_lower:
                    tags.extend(tag_list)
            
            # 第二階段：如果沒有標籤，使用智能標籤系統
            if not tags:
                tags = self._intelligent_tag_extraction(chunk_text)
            
            # 第三階段：最終備援
            if not tags:
                tags = self._fallback_tag_extraction(chunk_text)
            
            # 驗證和清理標籤
            tags = self._validate_and_clean_tags(tags, chunk_text)
            
            # 確保至少有一個標籤，最多三個
            if not tags:
                tags = ['一般內容']
            
            return tags[:3]  # 限制最多 3 個標籤
            
        except Exception as e:
            logger.error(f"提取標籤失敗: {e}")
            return ['一般內容']  # 確保至少有一個標籤
    
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


class SimpleCollectionProcessor:
    """簡化版 Collection 處理器"""
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 tag_csv_path: str = "TAG_info.csv",
                 max_chunk_size: int = 1024):
        """
        初始化處理器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置
            tag_csv_path: 標籤檔案路徑
            max_chunk_size: 最大分塊大小
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.tag_csv_path = tag_csv_path
        self.max_chunk_size = max_chunk_size
        
        # 初始化組件
        self.mongo_client: Optional[MongoClient] = None
        self.postgres_conn: Optional[psycopg2.extensions.connection] = None
        self.tag_processor = TagProcessor(tag_csv_path)
        self.error_logger = ErrorLogger()
        self.text_cleaner = TextCleaner()
        
        # 初始化連接
        self._initialize_connections()
        
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
            
        except Exception as e:
            logger.error(f"初始化連接失敗: {e}")
            raise
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """將文本切分為 chunks（依據空白和換行）"""
        if not text:
            return []
        
        # 清理文本
        text = self.text_cleaner.clean_text(text)
        
        # 按空白和換行切分
        chunks = []
        current_chunk = ""
        
        # 分割文本為段落
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果當前 chunk 加上新段落超過最大長度，保存當前 chunk
            if len(current_chunk) + len(paragraph) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 添加最後一個 chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_episode_metadata(self, episode_id: int) -> Dict[str, Any]:
        """從 PostgreSQL 獲取 episode 元資料"""
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
    
    def process_collection(self, collection_name: str, text_field: str = 'content') -> Dict[str, Any]:
        """處理單個 collection"""
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
                    for i, chunk in enumerate(chunks):
                        try:
                            # 提取標籤
                            tags = self.tag_processor.extract_tags(chunk)
                            
                            logger.info(f"Chunk {i+1}: 標籤 = {tags}")
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
    
    # 要處理的 collections
    collections = ['1500839292']  # 可以添加更多 collection
    
    try:
        # 初始化處理器
        processor = SimpleCollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            tag_csv_path="TAG_info.csv",
            max_chunk_size=1024
        )
        
        # 處理每個 collection
        results = []
        for collection_name in collections:
            try:
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