"""資料庫工具模組，負責資料庫連線和操作。"""

import psycopg2
import psycopg2.extras
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from contextlib import contextmanager

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.config.config import DatabaseConfig
except ImportError:
    # Fallback: 相對導入
    from config.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DBUtils:
    """資料庫操作工具類別。"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """初始化資料庫工具。
        
        Args:
            db_config: 資料庫設定字典
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """建立資料庫連線。
        
        Returns:
            連線是否成功
        """
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            self.logger.info("資料庫連線成功")
            return True
            
        except Exception as e:
            self.logger.error(f"資料庫連線失敗: {e}")
            return False
    
    def disconnect(self):
        """關閉資料庫連線。"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.logger.info("資料庫連線已關閉")
        except Exception as e:
            self.logger.error(f"關閉資料庫連線時發生錯誤: {e}")
    
    @contextmanager
    def get_connection(self):
        """取得資料庫連線的上下文管理器。
        
        Yields:
            資料庫游標
        """
        if not self.connection or self.connection.closed:
            if not self.connect():
                raise Exception("無法建立資料庫連線")
        
        try:
            if self.cursor:
                yield self.cursor
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise e
        finally:
            pass  # 不在此處關閉連線，由外部管理
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """執行查詢語句。
        
        Args:
            query: SQL查詢語句
            params: 查詢參數
            
        Returns:
            查詢結果列表
        """
        try:
            with self.get_connection() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    # 將 RealDictRow 轉換為普通字典
                    return [dict(row) for row in results]
                else:
                    if self.connection:
                        self.connection.commit()
                    return []
                    
        except Exception as e:
            self.logger.error(f"執行查詢時發生錯誤: {e}")
            self.logger.error(f"查詢語句: {query}")
            if params:
                self.logger.error(f"查詢參數: {params}")
            raise e
    
    def fetch_episodes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """查詢episodes資料。
        
        Args:
            limit: 查詢筆數限制
            
        Returns:
            episodes資料列表
        """
        query = "SELECT * FROM episodes"
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)
    
    def fetch_episode_by_id(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """根據ID查詢單個episode。
        
        Args:
            episode_id: episode ID
            
        Returns:
            episode資料，如果找不到則返回None
        """
        query = "SELECT * FROM episodes WHERE episode_id = %s"
        results = self.execute_query(query, (episode_id,))
        return results[0] if results else None
    
    def update_episode(self, episode: Dict[str, Any]) -> bool:
        """更新episode資料。
        
        Args:
            episode: episode資料字典
            
        Returns:
            更新是否成功
        """
        try:
            query = """
                UPDATE episodes SET
                    episode_title = %s,
                    description = %s,
                    audio_url = %s,
                    audio_preview_url = %s,
                    languages = %s,
                    explicit = %s,
                    updated_at = NOW()
                WHERE episode_id = %s
            """
            
            params = (
                episode.get('episode_title'),
                episode.get('description'),
                episode.get('audio_url'),
                episode.get('audio_preview_url'),
                episode.get('languages'),
                episode.get('explicit'),
                episode.get('episode_id')
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"更新episode時發生錯誤: {e}")
            return False
    
    def insert_episode(self, episode: Dict[str, Any]) -> bool:
        """插入新的episode資料。
        
        Args:
            episode: episode資料字典
            
        Returns:
            插入是否成功
        """
        try:
            query = """
                INSERT INTO episodes (
                    episode_id, podcast_id, episode_title, published_date,
                    audio_url, duration, description, audio_preview_url,
                    languages, explicit, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """
            
            params = (
                episode.get('episode_id'),
                episode.get('podcast_id'),
                episode.get('episode_title'),
                episode.get('published_date'),
                episode.get('audio_url'),
                episode.get('duration'),
                episode.get('description'),
                episode.get('audio_preview_url'),
                episode.get('languages'),
                episode.get('explicit')
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"插入episode時發生錯誤: {e}")
            return False
    
    def delete_episode(self, episode_id: str) -> bool:
        """刪除episode資料。
        
        Args:
            episode_id: episode ID
            
        Returns:
            刪除是否成功
        """
        try:
            query = "DELETE FROM episodes WHERE episode_id = %s"
            self.execute_query(query, (episode_id,))
            return True
            
        except Exception as e:
            self.logger.error(f"刪除episode時發生錯誤: {e}")
            return False
    
    def create_episode_metadata_table(self) -> bool:
        """建立episode_metadata表格。
        
        Returns:
            建立是否成功
        """
        try:
            query = """
                CREATE TABLE IF NOT EXISTS episode_metadata (
                    id SERIAL PRIMARY KEY,
                    episode_id VARCHAR(255) UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    audio_url TEXT,
                    published_date VARCHAR(100),
                    published_timestamp TIMESTAMP,
                    published_year INTEGER,
                    published_month INTEGER,
                    published_day INTEGER,
                    channel_id VARCHAR(50) NOT NULL,
                    channel_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    episode_number VARCHAR(20),
                    processed_at TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """
            
            self.execute_query(query)
            self.logger.info("episode_metadata表格建立成功")
            return True
            
        except Exception as e:
            self.logger.error(f"建立episode_metadata表格時發生錯誤: {e}")
            return False
    
    def insert_episode_metadata(self, metadata: Dict[str, Any]) -> bool:
        """插入episode_metadata資料。
        
        Args:
            metadata: metadata資料字典
            
        Returns:
            插入是否成功
        """
        try:
            query = """
                INSERT INTO episode_metadata (
                    episode_id, title, description, audio_url, published_date,
                    published_timestamp, published_year, published_month, published_day,
                    channel_id, channel_name, category, episode_number
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (episode_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    audio_url = EXCLUDED.audio_url,
                    published_date = EXCLUDED.published_date,
                    published_timestamp = EXCLUDED.published_timestamp,
                    published_year = EXCLUDED.published_year,
                    published_month = EXCLUDED.published_month,
                    published_day = EXCLUDED.published_day,
                    channel_id = EXCLUDED.channel_id,
                    channel_name = EXCLUDED.channel_name,
                    category = EXCLUDED.category,
                    episode_number = EXCLUDED.episode_number,
                    updated_at = NOW()
            """
            
            params = (
                metadata.get('episode_id'),
                metadata.get('title'),
                metadata.get('description'),
                metadata.get('audio_url'),
                metadata.get('published_date'),
                metadata.get('published_timestamp'),
                metadata.get('published_year'),
                metadata.get('published_month'),
                metadata.get('published_day'),
                metadata.get('channel_id'),
                metadata.get('channel_name'),
                metadata.get('category'),
                metadata.get('episode_number')
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"插入episode_metadata時發生錯誤: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """取得表格結構資訊。
        
        Args:
            table_name: 表格名稱
            
        Returns:
            表格結構資訊列表
        """
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        
        return self.execute_query(query, (table_name,))
    
    def check_table_exists(self, table_name: str) -> bool:
        """檢查表格是否存在。
        
        Args:
            table_name: 表格名稱
            
        Returns:
            表格是否存在
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """
        
        results = self.execute_query(query, (table_name,))
        return results[0]['exists'] if results else False
    
    def get_table_count(self, table_name: str) -> int:
        """取得表格記錄數。
        
        Args:
            table_name: 表格名稱
            
        Returns:
            記錄數
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        results = self.execute_query(query)
        return results[0]['count'] if results else 0 