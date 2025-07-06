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
            
            logger.info(f"已載入 {len(self.episodes)} 個節目，{len(self.users)} 個使用者，{len(self.interactions)} 個互動")
            
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
            
            # 獲取節目互動統計
            episode_interactions = [
                i for i in self.interactions 
                if i['episode_id'] == episode_id
            ]
            
            # 計算統計資訊
            total_listeners = len(set(i['user_id'] for i in episode_interactions))
            average_rating = self._calculate_average_rating([
                i for i in episode_interactions 
                if i['interaction_type'] == 'rating'
            ])
            total_listen_time = sum(
                i['listen_time'] for i in episode_interactions 
                if i['interaction_type'] == 'listen'
            )
            
            episode.update({
                'total_listeners': total_listeners,
                'average_rating': average_rating,
                'total_listen_time': total_listen_time,
                'interaction_count': len(episode_interactions)
            })
            
            return episode
            
        except Exception as e:
            logger.error(f"獲取節目資料失敗: {str(e)}")
            return {}
    
    def get_similar_episodes(self, episode_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取相似節目
        
        Args:
            episode_id: 節目ID
            limit: 返回數量限制
            
        Returns:
            List[Dict[str, Any]]: 相似節目列表
        """
        try:
            target_episode = self.get_episode_data(episode_id)
            
            if not target_episode:
                return []
            
            # 基於類別和標籤的簡單相似度計算
            similar_episodes = []
            
            for episode in self.episodes:
                if episode['episode_id'] == episode_id:
                    continue
                
                # 計算相似度分數
                similarity_score = 0
                
                # 類別相似度
                if episode['category'] == target_episode['category']:
                    similarity_score += 0.5
                
                # 標籤相似度
                target_tags = set(target_episode.get('tags', '').split(','))
                episode_tags = set(episode.get('tags', '').split(','))
                tag_overlap = len(target_tags.intersection(episode_tags))
                similarity_score += min(tag_overlap * 0.1, 0.3)
                
                if similarity_score > 0:
                    episode_copy = episode.copy()
                    episode_copy['similarity_score'] = similarity_score
                    similar_episodes.append(episode_copy)
            
            # 按相似度排序
            similar_episodes.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_episodes[:limit]
            
        except Exception as e:
            logger.error(f"獲取相似節目失敗: {str(e)}")
            return []
    
    def _calculate_average_rating(self, ratings: List[Dict[str, Any]]) -> float:
        """計算平均評分"""
        try:
            if not ratings:
                return 0.0
            
            total_rating = sum(r['rating'] for r in ratings)
            return round(total_rating / len(ratings), 2)
            
        except Exception as e:
            logger.error(f"平均評分計算失敗: {str(e)}")
            return 0.0
    
    def update_data(self):
        """更新資料快取"""
        try:
            logger.info("開始更新資料快取...")
            self._load_data()
            logger.info("資料快取更新完成")
            
        except Exception as e:
            logger.error(f"資料快取更新失敗: {str(e)}")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """獲取資料摘要"""
        try:
            return {
                'total_episodes': len(self.episodes),
                'total_users': len(self.users),
                'total_interactions': len(self.interactions),
                'categories': list(set(e['category'] for e in self.episodes)),
                'data_last_updated': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"資料摘要獲取失敗: {str(e)}")
            return {} 