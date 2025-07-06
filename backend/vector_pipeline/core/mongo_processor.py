"""
MongoDB 資料處理器
負責從 MongoDB 抓取長文本資料並解析 file 欄位
整合 data_cleaning 模組的清理功能
"""

import re
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from pymongo import MongoClient
from dataclasses import dataclass
from datetime import datetime

# 添加父目錄到路徑以支援 data_cleaning import
sys.path.append(str(Path(__file__).parent.parent.parent))

# 導入 data_cleaning 模組的清理器
try:
    from data_cleaning.core.mongo_cleaner import MongoCleaner
    from data_cleaning.core.stock_cancer_cleaner import StockCancerCleaner
    from data_cleaning.core.longtext_cleaner import LongTextCleaner
    DATA_CLEANING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"無法載入 data_cleaning 模組: {e}")
    DATA_CLEANING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MongoDocument:
    """MongoDB 文檔資料類別"""
    episode_id: str
    title: str
    content: str
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MongoDBProcessor:
    """MongoDB 資料處理器 - 整合 data_cleaning 模組"""
    
    def __init__(self, mongo_uri: str, database_name: str):
        """初始化 MongoDB 處理器"""
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        # 初始化清理器
        if not DATA_CLEANING_AVAILABLE:
            raise ImportError("data_cleaning 模組不可用，請確認依賴安裝與路徑設定")
        self.mongo_cleaner = MongoCleaner()
        self.stock_cancer_cleaner = StockCancerCleaner()
        self.longtext_cleaner = LongTextCleaner()
        logger.info("✅ data_cleaning 模組整合成功")
    
    def connect(self) -> bool:
        """建立 MongoDB 連接"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            logger.info(f"✅ MongoDB 連接成功: {self.database_name}")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB 連接失敗: {e}")
            return False
    
    def disconnect(self):
        """關閉 MongoDB 連接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 連接已關閉")
    
    def get_collections(self) -> List[str]:
        """獲取所有 collection 名稱"""
        try:
            collections = self.db.list_collection_names()
            logger.info(f"找到 {len(collections)} 個 collections")
            return collections
        except Exception as e:
            logger.error(f"獲取 collections 失敗: {e}")
            return []
    
    def process_collection(self, collection_name: str, limit: Optional[int] = None) -> List[MongoDocument]:
        """處理單個 collection"""
        try:
            collection = self.db[collection_name]
            documents = []
            
            # 查詢文檔
            cursor = collection.find({})
            if limit:
                cursor = cursor.limit(limit)
            
            for doc in cursor:
                try:
                    processed_doc = self._process_document(doc, collection_name)
                    if processed_doc:
                        documents.append(processed_doc)
                except Exception as e:
                    logger.error(f"處理文檔失敗 {doc.get('_id')}: {e}")
                    continue
            
            logger.info(f"✅ 處理完成 {collection_name}: {len(documents)} 個文檔")
            return documents
            
        except Exception as e:
            logger.error(f"處理 collection {collection_name} 失敗: {e}")
            return []
    
    def _process_document(self, doc: Dict[str, Any], collection_name: str) -> Optional[MongoDocument]:
        """處理單個文檔"""
        try:
            # 提取基本資訊
            episode_id = str(doc.get('_id', ''))
            title = doc.get('title', '')
            content = doc.get('content', '')
            file_path = doc.get('file', '')
            
            # 使用 data_cleaning 模組進行清理
            if DATA_CLEANING_AVAILABLE:
                cleaned_data = self._clean_with_data_cleaning(
                    title, content, episode_id, collection_name
                )
                title = cleaned_data['title']
                content = cleaned_data['content']
            else:
                # 基本清理（fallback）
                title = self._basic_clean_text(title)
                content = self._basic_clean_text(content)
            
            return MongoDocument(
                episode_id=episode_id,
                    title=title,
                content=content,
                file_path=file_path,
                metadata=doc
                )
            
        except Exception as e:
            logger.error(f"處理文檔失敗: {e}")
            return None
    
    def _clean_with_data_cleaning(self, title: str, content: str, episode_id: str, collection_name: str) -> Dict[str, str]:
        """使用 data_cleaning 模組進行清理"""
        try:
            # 檢查是否為股癌節目
            if collection_name == 'RSS_1500839292' or '股癌' in title:
                # 強制標題格式
                cleaned_title = self.stock_cancer_cleaner._clean_stock_cancer_title(title)
                cleaned_content = self.longtext_cleaner.clean(content)
                logger.debug(f"使用股癌清理器處理: {title[:50]}...")
            else:
                # 使用一般 MongoDB 清理器
                cleaned_title = self.mongo_cleaner._clean_title(title)
                cleaned_content = self.longtext_cleaner.clean(content)
            return {
                'title': cleaned_title,
                'content': cleaned_content
            }
        except Exception as e:
            logger.error(f"data_cleaning 清理失敗: {e}")
            # fallback 到基本清理
            return {
                'title': self._basic_clean_text(title),
                'content': self._basic_clean_text(content)
            }
    
    def _basic_clean_text(self, text: str) -> str:
        """基本文本清理（fallback）"""
        if not text:
            return ""
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        return text
    
    def process_all_collections(self, limit_per_collection: Optional[int] = None) -> Dict[str, List[MongoDocument]]:
        """處理所有 collections"""
        collections = self.get_collections()
        results = {}
        
        for collection_name in collections:
            try:
                documents = self.process_collection(collection_name, limit_per_collection)
                results[collection_name] = documents
            except Exception as e:
                logger.error(f"處理 collection {collection_name} 失敗: {e}")
                results[collection_name] = []
        
        return results 