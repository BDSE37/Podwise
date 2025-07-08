#!/usr/bin/env python3
"""
推薦系統資料管理模組
提供資料庫連接和資料存取功能
"""

from typing import Dict, List, Optional, Any
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommenderData:
    """
    推薦系統資料管理類別
    負責資料庫連接、資料存取和快取管理
    """
    
    def __init__(self, db_url: str):
        """
        初始化資料管理器
        
        Args:
            db_url: 資料庫連接 URL
        """
        self.db_url = db_url
        self.engine = None
        self.Session = None
        self._init_database()
        
        # 資料快取
        self.episodes = []
        self.users = []
        self.interactions = []
        self.transcripts = []
        self._load_data()
        
        logger.info("推薦系統資料管理器初始化完成")
    
    def _init_database(self):
        """初始化資料庫連接"""
        try:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
            
            # 測試連接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("資料庫連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {str(e)}")
            raise
    
    def _load_data(self):
        """載入資料到快取"""
        try:
            # 載入節目資料
            self.episodes = self._load_episodes()
            
            # 載入使用者資料
            self.users = self._load_users()
            
            # 載入互動資料
            self.interactions = self._load_interactions()
            
            # 載入轉錄資料
            self.transcripts = self._load_episode_transcripts()
            
            logger.info(f"已載入 {len(self.episodes)} 個節目，{len(self.users)} 個使用者，{len(self.interactions)} 個互動，{len(self.transcripts)} 個轉錄")
            
        except Exception as e:
            logger.error(f"資料載入失敗: {str(e)}")
    
    def _load_episodes(self) -> List[Dict[str, Any]]:
        """載入節目資料"""
        try:
            query = """
                SELECT 
                    episode_id,
                    podcast_id,
                    episode_title,
                    podcast_name,
                    author,
                    category,
                    tags,
                    description,
                    duration,
                    created_at
                FROM episodes
                WHERE status = 'active'
                ORDER BY created_at DESC
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                episodes = [dict(row) for row in result]
            
            return episodes
            
        except Exception as e:
            logger.error(f"節目資料載入失敗: {str(e)}")
            return []
    
    def _load_users(self) -> List[Dict[str, Any]]:
        """載入使用者資料"""
        try:
            query = """
                SELECT 
                    user_id,
                    username,
                    email,
                    preferences,
                    created_at
                FROM users
                WHERE status = 'active'
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                users = [dict(row) for row in result]
            
            return users
            
        except Exception as e:
            logger.error(f"使用者資料載入失敗: {str(e)}")
            return []
    
    def _load_interactions(self) -> List[Dict[str, Any]]:
        """載入互動資料"""
        try:
            query = """
                SELECT 
                    user_id,
                    episode_id,
                    interaction_type,
                    rating,
                    listen_time,
                    created_at
                FROM user_interactions
                WHERE created_at >= NOW() - INTERVAL '90 days'
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                interactions = [dict(row) for row in result]
            
            return interactions
            
        except Exception as e:
            logger.error(f"互動資料載入失敗: {str(e)}")
            return []
    
    def _load_episode_transcripts(self, min_length: int = 30, language_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        載入節目轉錄數據（整合自 EmbeddingDataLoader）
        
        Args:
            min_length: 最小轉錄長度
            language_filter: 語言篩選
            
        Returns:
            節目轉錄數據列表
        """
        try:
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
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                transcripts = [dict(row) for row in result]
            
            logger.info(f"載入 {len(transcripts)} 個節目轉錄")
            return transcripts
            
        except Exception as e:
            logger.error(f"載入轉錄數據失敗: {str(e)}")
            return []
    
    def load_episode_metadata(self, episode_ids: List[int]) -> List[Dict[str, Any]]:
        """
        載入節目元數據（整合自 EmbeddingDataLoader）
        
        Args:
            episode_ids: 節目ID列表
            
        Returns:
            節目元數據列表
        """
        try:
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
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), episode_ids)
                metadata = [dict(row) for row in result]
            
            logger.info(f"載入 {len(metadata)} 個節目元數據")
            return metadata
            
        except Exception as e:
            logger.error(f"載入元數據失敗: {str(e)}")
            return []
    
    def get_transcript_statistics(self) -> Dict[str, Any]:
        """
        獲取轉錄統計信息（整合自 EmbeddingDataLoader）
        
        Returns:
            統計信息字典
        """
        try:
            # 總數量統計
            total_count = len(self.transcripts)
            
            # 語言分布
            language_dist = {}
            for transcript in self.transcripts:
                lang = transcript.get('language', 'unknown')
                language_dist[lang] = language_dist.get(lang, 0) + 1
            
            # 長度分布
            if self.transcripts:
                lengths = [t.get('transcript_length', 0) for t in self.transcripts]
                length_stats = {
                    'avg_length': sum(lengths) / len(lengths),
                    'min_length': min(lengths),
                    'max_length': max(lengths)
                }
            else:
                length_stats = {'avg_length': 0, 'min_length': 0, 'max_length': 0}
            
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
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        獲取使用者資料
        
        Args:
            user_id: 使用者ID
            
        Returns:
            Dict[str, Any]: 使用者資料
        """
        try:
            # 從快取中查找使用者
            user = next((u for u in self.users if u['user_id'] == user_id), None)
            
            if not user:
                return {}
            
            # 獲取使用者互動
            user_interactions = [
                i for i in self.interactions 
                if i['user_id'] == user_id
            ]
            
            # 獲取使用者評分
            user_ratings = [
                i for i in user_interactions 
                if i['interaction_type'] == 'rating'
            ]
            
            return {
                'user_info': user,
                'interactions': user_interactions,
                'ratings': user_ratings,
                'total_interactions': len(user_interactions),
                'average_rating': self._calculate_average_rating(user_ratings)
            }
            
        except Exception as e:
            logger.error(f"獲取使用者資料失敗: {str(e)}")
            return {}
    
    def get_episode_data(self, episode_id: int) -> Dict[str, Any]:
        """
        獲取節目資料
        
        Args:
            episode_id: 節目ID
            
        Returns:
            Dict[str, Any]: 節目資料
        """
        try:
            # 從快取中查找節目
            episode = next((e for e in self.episodes if e['episode_id'] == episode_id), None)
            
            if not episode:
                return {}
            
            # 獲取節目互動
            episode_interactions = [
                i for i in self.interactions 
                if i['episode_id'] == episode_id
            ]
            
            # 獲取轉錄資料
            transcript = next((t for t in self.transcripts if t['episode_id'] == episode_id), None)
            
            return {
                'episode_info': episode,
                'interactions': episode_interactions,
                'transcript': transcript,
                'total_interactions': len(episode_interactions),
                'average_rating': self._calculate_average_rating([
                    i for i in episode_interactions 
                    if i['interaction_type'] == 'rating'
                ])
            }
            
        except Exception as e:
            logger.error(f"獲取節目資料失敗: {str(e)}")
            return {}
    
    def get_similar_episodes(self, episode_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取相似節目
        
        Args:
            episode_id: 節目ID
            limit: 返回數量
            
        Returns:
            List[Dict[str, Any]]: 相似節目列表
        """
        try:
            # 獲取目標節目資料
            target_episode = self.get_episode_data(episode_id)
            
            if not target_episode:
                return []
            
            target_category = target_episode['episode_info']['category']
            
            # 找出同類別的節目
            similar_episodes = [
                e for e in self.episodes 
                if e['category'] == target_category and e['episode_id'] != episode_id
            ]
            
            # 按評分排序
            similar_episodes.sort(
                key=lambda x: self._calculate_average_rating([
                    i for i in self.interactions 
                    if i['episode_id'] == x['episode_id'] and i['interaction_type'] == 'rating'
                ]),
                reverse=True
            )
            
            return similar_episodes[:limit]
            
        except Exception as e:
            logger.error(f"獲取相似節目失敗: {str(e)}")
            return []
    
    def _calculate_average_rating(self, ratings: List[Dict[str, Any]]) -> float:
        """
        計算平均評分
        
        Args:
            ratings: 評分列表
            
        Returns:
            float: 平均評分
        """
        if not ratings:
            return 0.0
        
        total_rating = sum(r.get('rating', 0) for r in ratings)
        return total_rating / len(ratings)
    
    def update_data(self):
        """更新資料快取"""
        try:
            self._load_data()
            logger.info("資料快取更新完成")
            
        except Exception as e:
            logger.error(f"資料快取更新失敗: {str(e)}")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        獲取資料摘要
        
        Returns:
            Dict[str, Any]: 資料摘要
        """
        try:
            return {
                'total_episodes': len(self.episodes),
                'total_users': len(self.users),
                'total_interactions': len(self.interactions),
                'total_transcripts': len(self.transcripts),
                'transcript_stats': self.get_transcript_statistics(),
                'last_update': '2024-01-01 00:00:00'
            }
            
        except Exception as e:
            logger.error(f"獲取資料摘要失敗: {str(e)}")
            return {} 