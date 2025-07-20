#!/usr/bin/env python3
"""
Cross Database Text Fetcher

跨資料庫文本擷取工具，用於從 PostgreSQL 和 MongoDB 中擷取 Podcast 內容

功能：
1. PostgreSQL podcasts 表模糊比對取得 podcast_id
2. PostgreSQL episodes 表精確比對取得 episode_title
3. MongoDB collection 模糊比對取得 text 內容

作者: Podwise Team
版本: 1.0.0
"""

import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

# 資料庫相關導入
try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("psycopg2 未安裝，PostgreSQL 功能不可用")

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("pymongo 未安裝，MongoDB 功能不可用")

logger = logging.getLogger(__name__)


@dataclass
class TextFetchResult:
    """文本擷取結果"""
    success: bool
    text: str = ""
    podcast_id: str = ""
    episode_title: str = ""
    error_message: str = ""
    processing_time: float = 0.0


class CrossDBTextFetcher:
    """跨資料庫文本擷取器"""
    
    def __init__(self, 
                 postgres_config: Optional[Dict[str, str]] = None,
                 mongodb_config: Optional[Dict[str, str]] = None):
        """
        初始化擷取器
        
        Args:
            postgres_config: PostgreSQL 連接配置
            mongodb_config: MongoDB 連接配置
        """
        self.postgres_config = postgres_config or {
            "host": "postgres.podwise.svc.cluster.local",
            "port": "5432",
            "database": "podcast",
            "user": "bdse37",
            "password": "111111"
        }
        
        self.mongodb_config = mongodb_config or {
            "host": "mongodb.podwise.svc.cluster.local",
            "port": "27017",
            "database": "podcast",
            "username": "bdse37",
            "password": "111111"
        }
        
        self.postgres_conn = None
        self.mongodb_client = None
        self.mongodb_db = None
        
        logger.info("CrossDBTextFetcher 初始化完成")
    
    async def connect_databases(self) -> bool:
        """連接資料庫"""
        try:
            # 連接 PostgreSQL
            if POSTGRES_AVAILABLE:
                self.postgres_conn = psycopg2.connect(**self.postgres_config)
                logger.info("PostgreSQL 連接成功")
            
            # 連接 MongoDB
            if MONGODB_AVAILABLE:
                # 構建 MongoDB 連接字串
                if 'username' in self.mongodb_config and 'password' in self.mongodb_config:
                    mongo_uri = f"mongodb://{self.mongodb_config['username']}:{self.mongodb_config['password']}@{self.mongodb_config['host']}:{self.mongodb_config['port']}/{self.mongodb_config['database']}?authSource=admin"
                else:
                    mongo_uri = f"mongodb://{self.mongodb_config['host']}:{self.mongodb_config['port']}/{self.mongodb_config['database']}"
                
                self.mongodb_client = MongoClient(mongo_uri)
                self.mongodb_db = self.mongodb_client[self.mongodb_config['database']]
                logger.info("MongoDB 連接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return False
    
    async def fetch_text(self, tag1: str, tag2: str) -> TextFetchResult:
        """
        跨資料庫文本擷取主流程
        
        Args:
            tag1: 用於 podcast 模糊比對的標籤
            tag2: 用於 episode 精確比對的標籤
            
        Returns:
            TextFetchResult: 擷取結果
        """
        import time
        start_time = time.time()
        
        try:
            # 步驟一：PostgreSQL podcasts 表模糊比對取得 podcast_id
            podcast_id = await self._get_podcast_id_by_tag(tag1)
            if not podcast_id:
                return TextFetchResult(
                    success=False,
                    error_message=f"無法找到匹配的 podcast (tag1: {tag1})",
                    processing_time=time.time() - start_time
                )
            
            # 步驟二：PostgreSQL episodes 表精確比對取得 episode_title
            episode_title = await self._get_episode_title_by_tag(podcast_id, tag2)
            if not episode_title:
                return TextFetchResult(
                    success=False,
                    error_message=f"無法找到匹配的 episode (podcast_id: {podcast_id}, tag2: {tag2})",
                    processing_time=time.time() - start_time
                )
            
            # 步驟三：MongoDB collection 模糊比對取得 text 內容
            text_content = await self._get_text_from_mongodb(podcast_id, episode_title)
            if not text_content:
                return TextFetchResult(
                    success=False,
                    error_message=f"無法找到文本內容 (podcast_id: {podcast_id}, episode_title: {episode_title})",
                    processing_time=time.time() - start_time
                )
            
            return TextFetchResult(
                success=True,
                text=text_content,
                podcast_id=podcast_id,
                episode_title=episode_title,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"文本擷取失敗: {e}")
            return TextFetchResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def _get_podcast_id_by_tag(self, tag1: str) -> Optional[str]:
        """
        從 PostgreSQL podcasts 表模糊比對取得 podcast_id
        
        Args:
            tag1: 用於模糊比對的標籤
            
        Returns:
            Optional[str]: podcast_id 或 None
        """
        if not POSTGRES_AVAILABLE or not self.postgres_conn:
            logger.error("PostgreSQL 不可用")
            return None
        
        try:
            with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 模糊比對 podcast_name
                query = """
                SELECT podcast_id 
                FROM podcasts 
                WHERE podcast_name ILIKE %s
                LIMIT 1
                """
                
                search_pattern = f"%{tag1}%"
                cursor.execute(query, (search_pattern,))
                
                result = cursor.fetchone()
                if result:
                    podcast_id = result['podcast_id']
                    logger.info(f"找到 podcast_id: {podcast_id} (tag1: {tag1})")
                    return podcast_id
                else:
                    logger.warning(f"未找到匹配的 podcast (tag1: {tag1})")
                    return None
                    
        except Exception as e:
            logger.error(f"PostgreSQL 查詢失敗: {e}")
            return None
    
    async def _get_episode_title_by_tag(self, podcast_id: str, tag2: str) -> Optional[str]:
        """
        從 PostgreSQL episodes 表精確比對取得 episode_title
        
        Args:
            podcast_id: podcast ID
            tag2: 用於精確比對的標籤
            
        Returns:
            Optional[str]: episode_title 或 None
        """
        if not POSTGRES_AVAILABLE or not self.postgres_conn:
            logger.error("PostgreSQL 不可用")
            return None
        
        try:
            with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 先取得該 podcast 的所有 episode_title
                query = """
                SELECT episode_title 
                FROM episodes 
                WHERE podcast_id = %s
                """
                
                cursor.execute(query, (podcast_id,))
                episode_titles = [row['episode_title'] for row in cursor.fetchall()]
                
                # 精確比對 episode_title
                logger.info(f"搜尋 episode_title，podcast_id: {podcast_id}, tag2: {tag2}")
                logger.info(f"可用的 episode_titles: {episode_titles[:5]}")  # 只顯示前5個
                
                for title in episode_titles:
                    if tag2.lower() in title.lower():
                        logger.info(f"找到 episode_title: {title} (tag2: {tag2})")
                        return title
                
                logger.warning(f"未找到匹配的 episode (podcast_id: {podcast_id}, tag2: {tag2})")
                return None
                
        except Exception as e:
            logger.error(f"PostgreSQL 查詢失敗: {e}")
            return None
    
    async def _get_text_from_mongodb(self, podcast_id: str, episode_title: str) -> Optional[str]:
        """
        從 MongoDB collection 模糊比對取得 text 內容
        
        Args:
            podcast_id: podcast ID (RSS_id)
            episode_title: episode 標題
            
        Returns:
            Optional[str]: text 內容或 None
        """
        if not MONGODB_AVAILABLE:
            logger.error("MongoDB 不可用")
            return None
        
        if self.mongodb_db is None:
            logger.error("MongoDB 連接不可用")
            return None
        
        try:
            # 使用 RSS_{podcast_id} 作為 collection 名稱
            collection_name = f"RSS_{podcast_id}"
            logger.info(f"嘗試連接 MongoDB collection: {collection_name}")
            
            # 檢查 collection 是否存在
            if collection_name not in self.mongodb_db.list_collection_names():
                logger.warning(f"MongoDB collection '{collection_name}' 不存在")
                return None
            
            collection = self.mongodb_db[collection_name]
            
            # 優先使用 file 欄位進行搜尋
            document = None
            
            # 從 episode_title 中提取 EP 編號
            episode_pattern = episode_title
            if "_" in episode_pattern:
                episode_pattern = episode_pattern.split("_")[0]  # 取 EPXXX 部分
            
            # 確保是 EP 格式
            if not episode_pattern.upper().startswith("EP"):
                if episode_pattern.isdigit():
                    episode_pattern = f"EP{episode_pattern}"
                else:
                    episode_pattern = f"EP{episode_pattern}"
            
            logger.info(f"搜尋 EP 編號: {episode_pattern}")
            
            # 優先搜尋 file 欄位包含 EP 編號的 document
            try:
                file_query = {"file": {"$regex": episode_pattern, "$options": "i"}}
                document = collection.find_one(file_query)
                if document:
                    logger.info(f"在 file 欄位中找到匹配的 document: {document.get('file', '')}")
                else:
                    logger.warning(f"file 欄位中未找到包含 {episode_pattern} 的 document")
            except Exception as e:
                logger.debug(f"搜尋 file 欄位失敗: {e}")
            
            # 如果 file 欄位沒有找到，嘗試其他欄位
            if not document:
                search_pattern = re.compile(f".*{re.escape(episode_title)}.*", re.IGNORECASE)
                possible_fields = ["episode_title", "title", "filename", "content"]
                
                for field in possible_fields:
                    try:
                        document = collection.find_one({field: search_pattern})
                        if document:
                            logger.info(f"在欄位 '{field}' 中找到匹配的 document")
                            break
                    except Exception as e:
                        logger.debug(f"搜尋欄位 '{field}' 失敗: {e}")
                        continue
                else:
                    # 如果沒有找到，嘗試搜尋所有欄位
                    document = collection.find_one({"$or": [{field: search_pattern} for field in possible_fields]})
            
            if document:
                # 嘗試取得 text 內容
                text_content = None
                text_fields = ["text", "content", "summary", "transcript"]
                
                for field in text_fields:
                    if field in document and document[field]:
                        text_content = document[field]
                        logger.info(f"從欄位 '{field}' 取得文本內容，長度: {len(text_content)} 字元")
                        break
                
                if text_content:
                    return text_content
                else:
                    logger.warning(f"Document 存在但沒有找到文本內容欄位: {list(document.keys())}")
                    return None
            else:
                logger.warning(f"未找到文本內容 (collection: {collection_name}, episode_title: {episode_title})")
                return None
                
        except Exception as e:
            logger.error(f"MongoDB 查詢失敗: {e}")
            return None
    
    def close_connections(self):
        """關閉資料庫連接"""
        try:
            if self.postgres_conn:
                self.postgres_conn.close()
                logger.info("PostgreSQL 連接已關閉")
            
            if self.mongodb_client:
                self.mongodb_client.close()
                logger.info("MongoDB 連接已關閉")
                
        except Exception as e:
            logger.error(f"關閉連接失敗: {e}")


# 全域實例
cross_db_text_fetcher = CrossDBTextFetcher()


def get_cross_db_text_fetcher() -> CrossDBTextFetcher:
    """獲取跨資料庫文本擷取器實例"""
    return cross_db_text_fetcher


async def test_cross_db_text_fetcher():
    """測試跨資料庫文本擷取器"""
    fetcher = get_cross_db_text_fetcher()
    
    # 連接資料庫
    if not await fetcher.connect_databases():
        print("資料庫連接失敗")
        return
    
    # 測試擷取
    test_tag1 = "商業"
    test_tag2 = "投資"
    
    print(f"測試擷取 (tag1: {test_tag1}, tag2: {test_tag2})")
    print("=" * 50)
    
    result = await fetcher.fetch_text(test_tag1, test_tag2)
    
    print(f"擷取成功: {result.success}")
    print(f"處理時間: {result.processing_time:.3f} 秒")
    
    if result.success:
        print(f"Podcast ID: {result.podcast_id}")
        print(f"Episode Title: {result.episode_title}")
        print(f"文本長度: {len(result.text)} 字元")
        print(f"文本預覽: {result.text[:200]}...")
    else:
        print(f"錯誤訊息: {result.error_message}")
    
    # 關閉連接
    fetcher.close_connections()


if __name__ == "__main__":
    asyncio.run(test_cross_db_text_fetcher()) 