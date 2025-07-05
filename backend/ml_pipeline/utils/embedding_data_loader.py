#!/usr/bin/env python3
"""
嵌入數據載入器
用於從 PostgreSQL 載入節目轉錄數據
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class EmbeddingDataLoader:
    """嵌入數據載入器類別"""
    
    def __init__(self, connection_string: str):
        """
        初始化數據載入器
        
        Args:
            connection_string: PostgreSQL 連接字串
        """
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
        
        logger.info("嵌入數據載入器初始化完成")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def connect(self) -> bool:
        """
        建立資料庫連接
        
        Returns:
            連接是否成功
        """
        try:
            self.connection = psycopg2.connect(
                self.connection_string, 
                cursor_factory=RealDictCursor
            )
            self.cursor = self.connection.cursor()
            logger.info("資料庫連接建立成功")
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {str(e)}")
            return False
    
    def close(self):
        """關閉資料庫連接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("資料庫連接已關閉")
            
        except Exception as e:
            logger.error(f"關閉連接失敗: {str(e)}")
    
    def load_episode_transcripts(
        self, 
        min_length: int = 30,
        language_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        載入節目轉錄數據
        
        Args:
            min_length: 最小轉錄長度
            language_filter: 語言篩選
            
        Returns:
            節目轉錄數據列表
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return []
            
            query = """
                SELECT 
                    episode_id, 
                    transcript_path, 
                    transcript_length, 
                    language,
                    created_at,
                    updated_at
                FROM transcripts
                WHERE transcript_length > %s
            """
            params = [min_length]
            
            if language_filter:
                query += " AND language = %s"
                params.append(language_filter)
            
            query += " ORDER BY created_at DESC"
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            # 轉換為字典列表
            transcripts = [dict(row) for row in results]
            
            logger.info(f"載入 {len(transcripts)} 個節目轉錄")
            return transcripts
            
        except Exception as e:
            logger.error(f"載入轉錄數據失敗: {str(e)}")
            return []
    
    def load_episode_metadata(self, episode_ids: List[int]) -> List[Dict]:
        """
        載入節目元數據
        
        Args:
            episode_ids: 節目ID列表
            
        Returns:
            節目元數據列表
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return []
            
            if not episode_ids:
                return []
            
            # 建立 IN 查詢的參數
            placeholders = ','.join(['%s'] * len(episode_ids))
            
            query = f"""
                SELECT 
                    e.episode_id,
                    e.episode_title,
                    e.podcast_id,
                    p.podcast_name,
                    p.author,
                    p.category,
                    e.duration,
                    e.published_date
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.episode_id IN ({placeholders})
            """
            
            self.cursor.execute(query, episode_ids)
            results = self.cursor.fetchall()
            
            metadata = [dict(row) for row in results]
            
            logger.info(f"載入 {len(metadata)} 個節目元數據")
            return metadata
            
        except Exception as e:
            logger.error(f"載入元數據失敗: {str(e)}")
            return []
    
    def get_transcript_statistics(self) -> Dict[str, Any]:
        """
        獲取轉錄統計信息
        
        Returns:
            統計信息字典
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return {}
            
            # 總數量統計
            self.cursor.execute("SELECT COUNT(*) as total FROM transcripts")
            total_count = self.cursor.fetchone()['total']
            
            # 語言分布
            self.cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM transcripts
                GROUP BY language
                ORDER BY count DESC
            """)
            language_dist = dict(self.cursor.fetchall())
            
            # 長度分布
            self.cursor.execute("""
                SELECT 
                    AVG(transcript_length) as avg_length,
                    MIN(transcript_length) as min_length,
                    MAX(transcript_length) as max_length
                FROM transcripts
            """)
            length_stats = dict(self.cursor.fetchone())
            
            stats = {
                'total_transcripts': total_count,
                'language_distribution': language_dist,
                'length_statistics': length_stats
            }
            
            logger.info(f"統計信息: {total_count} 個轉錄")
            return stats
            
        except Exception as e:
            logger.error(f"獲取統計信息失敗: {str(e)}")
            return {}