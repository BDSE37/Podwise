"""
PostgreSQL Metadata Mapping 處理器
負責查詢 episode 和 podcast 的完整 metadata
"""

import logging
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EpisodeMetadata:
    """Episode 元資料類別"""
    episode_id: int
    podcast_id: int
    episode_title: str
    published_date: Optional[datetime]
    duration: Optional[int]
    description: Optional[str]
    created_at: Optional[datetime]
    podcast_name: str
    author: str
    category: str
    rss_link: Optional[str]
    languages: Optional[str]


class PostgreSQLMapper:
    """PostgreSQL Metadata Mapping 處理器"""
    
    def __init__(self, postgres_config: Dict[str, Any]):
        """
        初始化 PostgreSQL Mapper
        
        Args:
            postgres_config: PostgreSQL 配置字典
        """
        self.postgres_config = postgres_config
        self.connection: Optional[psycopg2.extensions.connection] = None
        
    def connect(self) -> None:
        """連接到 PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=self.postgres_config['database'],
                user=self.postgres_config['user'],
                password=self.postgres_config['password']
            )
            logger.info(f"成功連接到 PostgreSQL: {self.postgres_config['host']}:{self.postgres_config['port']}")
        except Exception as e:
            logger.error(f"PostgreSQL 連接失敗: {e}")
            raise
    
    def get_episode_metadata(self, episode_id: int) -> Optional[EpisodeMetadata]:
        """
        根據 episode_id 獲取完整 metadata
        
        Args:
            episode_id: Episode ID
            
        Returns:
            Episode 元資料，如果找不到則返回 None
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.episode_id = %s
                """
                
                cursor.execute(query, (episode_id,))
                result = cursor.fetchone()
                
                if result:
                    return EpisodeMetadata(
                        episode_id=result['episode_id'],
                        podcast_id=result['podcast_id'],
                        episode_title=result['episode_title'],
                        published_date=result['published_date'],
                        duration=result['duration'],
                        description=result['description'],
                        created_at=result['created_at'],
                        podcast_name=result['podcast_name'],
                        author=result['author'],
                        category=result['category'],
                        rss_link=result['rss_link'],
                        languages=result['languages']
                    )
                else:
                    logger.warning(f"找不到 episode_id {episode_id} 的元資料")
                    return None
                    
        except Exception as e:
            logger.error(f"獲取 episode 元資料失敗: {e}")
            return None
    
    def search_episode_by_rss_and_title(self, rss_id: str, episode_title: str) -> Optional[EpisodeMetadata]:
        """
        根據 RSS_ID 和 episode_title 搜尋 episode
        
        Args:
            rss_id: RSS ID (字串格式)
            episode_title: Episode 標題
            
        Returns:
            Episode 元資料，如果找不到則返回 None
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE p.podcast_id = %s AND e.episode_title ILIKE %s
                ORDER BY e.created_at DESC
                LIMIT 1
                """
                
                search_pattern = f"%{episode_title}%"
                cursor.execute(query, (rss_id, search_pattern))
                result = cursor.fetchone()
                
                if result:
                    return EpisodeMetadata(
                        episode_id=result['episode_id'],
                        podcast_id=result['podcast_id'],
                        episode_title=result['episode_title'],
                        published_date=result['published_date'],
                        duration=result['duration'],
                        description=result['description'],
                        created_at=result['created_at'],
                        podcast_name=result['podcast_name'],
                        author=result['author'],
                        category=result['category'],
                        rss_link=result['rss_link'],
                        languages=result['languages']
                    )
                else:
                    logger.warning(f"找不到 RSS_ID={rss_id}, title包含 '{episode_title}' 的 episode")
                    return None
                    
        except Exception as e:
            logger.error(f"搜尋 episode 失敗: {e}")
            return None
    
    def search_episode_by_podcast_and_title(self, podcast_id: int, episode_title: str) -> Optional[EpisodeMetadata]:
        """
        根據 podcast_id 和 episode_title 搜尋 episode
        
        Args:
            podcast_id: Podcast ID
            episode_title: Episode 標題
            
        Returns:
            Episode 元資料，如果找不到則返回 None
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.podcast_id = %s AND e.episode_title ILIKE %s
                ORDER BY e.created_at DESC
                LIMIT 1
                """
                
                search_pattern = f"%{episode_title}%"
                cursor.execute(query, (podcast_id, search_pattern))
                result = cursor.fetchone()
                
                if result:
                    return EpisodeMetadata(
                        episode_id=result['episode_id'],
                        podcast_id=result['podcast_id'],
                        episode_title=result['episode_title'],
                        published_date=result['published_date'],
                        duration=result['duration'],
                        description=result['description'],
                        created_at=result['created_at'],
                        podcast_name=result['podcast_name'],
                        author=result['author'],
                        category=result['category'],
                        rss_link=result['rss_link'],
                        languages=result['languages']
                    )
                else:
                    logger.warning(f"找不到 podcast_id={podcast_id}, title包含 '{episode_title}' 的 episode")
                    return None
                    
        except Exception as e:
            logger.error(f"搜尋 episode 失敗: {e}")
            return None
    
    def search_episode_by_title_and_podcast(self, title: str, podcast_name: str) -> Optional[EpisodeMetadata]:
        """
        根據標題和播客名稱搜尋 episode
        
        Args:
            title: Episode 標題
            podcast_name: 播客名稱
            
        Returns:
            Episode 元資料，如果找不到則返回 None
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE (p.name ILIKE %s OR e.episode_title ILIKE %s)
                ORDER BY e.created_at DESC
                LIMIT 1
                """
                
                search_pattern = f"%{title}%"
                cursor.execute(query, (search_pattern, search_pattern))
                result = cursor.fetchone()
                
                if result:
                    return EpisodeMetadata(
                        episode_id=result['episode_id'],
                        podcast_id=result['podcast_id'],
                        episode_title=result['episode_title'],
                        published_date=result['published_date'],
                        duration=result['duration'],
                        description=result['description'],
                        created_at=result['created_at'],
                        podcast_name=result['podcast_name'],
                        author=result['author'],
                        category=result['category'],
                        rss_link=result['rss_link'],
                        languages=result['languages']
                    )
                else:
                    logger.warning(f"找不到標題包含 '{title}' 的 episode")
                    return None
                    
        except Exception as e:
            logger.error(f"搜尋 episode 失敗: {e}")
            return None
    
    def get_podcast_metadata(self, podcast_id: int) -> Optional[Dict[str, Any]]:
        """
        根據 podcast_id 獲取播客元資料
        
        Args:
            podcast_id: Podcast ID
            
        Returns:
            播客元資料字典
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    podcast_id,
                    name,
                    description,
                    author,
                    category,
                    rss_link,
                    languages,
                    created_at,
                    updated_at
                FROM podcasts
                WHERE podcast_id = %s
                """
                
                cursor.execute(query, (podcast_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                else:
                    logger.warning(f"找不到 podcast_id {podcast_id} 的元資料")
                    return None
                    
        except Exception as e:
            logger.error(f"獲取 podcast 元資料失敗: {e}")
            return None
    
    def get_episodes_by_podcast(self, podcast_id: int, limit: int = 10) -> List[EpisodeMetadata]:
        """
        獲取指定播客的所有 episodes
        
        Args:
            podcast_id: Podcast ID
            limit: 限制數量
            
        Returns:
            Episode 元資料列表
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.podcast_id = %s
                ORDER BY e.created_at DESC
                LIMIT %s
                """
                
                cursor.execute(query, (podcast_id, limit))
                results = cursor.fetchall()
                
                episodes = []
                for result in results:
                    episode = EpisodeMetadata(
                        episode_id=result['episode_id'],
                        podcast_id=result['podcast_id'],
                        episode_title=result['episode_title'],
                        published_date=result['published_date'],
                        duration=result['duration'],
                        description=result['description'],
                        created_at=result['created_at'],
                        podcast_name=result['podcast_name'],
                        author=result['author'],
                        category=result['category'],
                        rss_link=result['rss_link'],
                        languages=result['languages']
                    )
                    episodes.append(episode)
                
                return episodes
                
        except Exception as e:
            logger.error(f"獲取播客 episodes 失敗: {e}")
            return []
    
    def close(self) -> None:
        """關閉連接"""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL 連接已關閉") 