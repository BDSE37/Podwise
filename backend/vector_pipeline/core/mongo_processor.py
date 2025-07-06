"""
MongoDB 資料處理器
負責從 MongoDB 抓取長文本資料並解析 file 欄位
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pymongo import MongoClient
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MongoDocument:
    """MongoDB 文檔資料類別"""
    document_id: str
    text: str
    file: str
    created: datetime
    episode_number: Optional[int]
    podcast_name: Optional[str]
    title: Optional[str]
    raw_data: Dict[str, Any]


class MongoDBProcessor:
    """MongoDB 資料處理器"""
    
    def __init__(self, mongo_config: Dict[str, Any]):
        """
        初始化 MongoDB 處理器
        
        Args:
            mongo_config: MongoDB 配置字典
        """
        self.mongo_config = mongo_config
        self.client: Optional[MongoClient] = None
        self.db = None
        
    def connect(self) -> None:
        """連接到 MongoDB"""
        try:
            if self.mongo_config.get("password"):
                uri = f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@{self.mongo_config['host']}:{self.mongo_config['port']}"
            else:
                uri = f"mongodb://{self.mongo_config['host']}:{self.mongo_config['port']}"
            
            self.client = MongoClient(uri)
            self.db = self.client[self.mongo_config['database']]
            logger.info(f"成功連接到 MongoDB: {self.mongo_config['host']}:{self.mongo_config['port']}")
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            raise
    
    def parse_file_field(self, file_name: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        解析 file 欄位，提取 episode_number、podcast_name、title
        
        Args:
            file_name: 檔案名稱
            
        Returns:
            Tuple[episode_number, podcast_name, title]
        """
        try:
            # 解析 episode number
            episode_match = re.search(r'podcast_(\d+)', file_name)
            episode_number = int(episode_match.group(1)) if episode_match else None
            
            # 解析 podcast name (取【】內文)
            podcast_match = re.search(r'【(.+?)】', file_name)
            podcast_name = podcast_match.group(1) if podcast_match else None
            
            # 解析 title (取】之後到.mp3之前)
            title_match = re.search(r'】(.+?)\.mp3', file_name)
            title = title_match.group(1).strip() if title_match else None
            
            return episode_number, podcast_name, title
            
        except Exception as e:
            logger.error(f"解析 file 欄位失敗: {e}")
            return None, None, None
    
    def fetch_documents(self, collection_name: str, query: Optional[Dict[str, Any]] = None, 
                       limit: Optional[int] = None) -> List[MongoDocument]:
        """
        從 MongoDB 獲取文檔並解析
        
        Args:
            collection_name: 集合名稱
            query: 查詢條件
            limit: 限制數量
            
        Returns:
            解析後的文檔列表
        """
        if self.db is None:
            self.connect()
            
        try:
            collection = self.db[collection_name]
            query = query or {}
            
            if limit:
                documents = list(collection.find(query).limit(limit))
            else:
                documents = list(collection.find(query))
                
            logger.info(f"從 MongoDB 獲取 {len(documents)} 個文檔")
            
            processed_documents = []
            for doc in documents:
                # 解析 file 欄位
                episode_number, podcast_name, title = self.parse_file_field(doc.get('file', ''))
                
                # 建立 MongoDocument 物件
                mongo_doc = MongoDocument(
                    document_id=str(doc.get('_id')),
                    text=doc.get('text', ''),
                    file=doc.get('file', ''),
                    created=doc.get('created'),
                    episode_number=episode_number,
                    podcast_name=podcast_name,
                    title=title,
                    raw_data=doc
                )
                processed_documents.append(mongo_doc)
                
            return processed_documents
            
        except Exception as e:
            logger.error(f"獲取 MongoDB 文檔失敗: {e}")
            raise
    
    def get_collection_names(self) -> List[str]:
        """獲取所有集合名稱"""
        if self.db is None:
            self.connect()
        return self.db.list_collection_names()
    
    def get_document_count(self, collection_name: str) -> int:
        """獲取集合文檔數量"""
        if self.db is None:
            self.connect()
        return self.db[collection_name].count_documents({})
    
    def close(self) -> None:
        """關閉連接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 連接已關閉") 