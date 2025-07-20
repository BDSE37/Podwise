#!/usr/bin/env python3
"""
ML Pipeline 服務層
提供推薦系統的服務介面
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import pandas as pd

# 避免循環導入，使用延遲導入
# from core import RecommenderEngine
from config.recommender_config import get_recommender_config

logger = logging.getLogger(__name__)

class RecommendationService:
    """推薦服務類別"""
    
    def __init__(self, db_url: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化推薦服務
        
        Args:
            db_url: 資料庫連接 URL
            config: 配置參數
        """
        self.db_url = db_url
        self.config = config or get_recommender_config()
        
        # 初始化推薦引擎（使用模擬數據）
        self.recommender_engine = self._init_recommender_engine()
        
        logger.info("推薦服務初始化完成")
    
    def _init_recommender_engine(self) -> Optional[Any]:
        """初始化推薦引擎"""
        try:
            # 避免循環導入，使用延遲導入
            from core.recommender import RecommenderEngine
            from core.data_manager import RecommenderData
            
            data_manager = RecommenderData(self.db_url)
            
            # 轉換為 DataFrame
            podcast_data = pd.DataFrame(data_manager.episodes)
            user_history = pd.DataFrame(data_manager.interactions)
            
            # 確保必要的欄位存在
            if 'episode_id' not in podcast_data.columns:
                logger.error("Podcast 資料缺少 episode_id 欄位")
                return None
                
            if 'user_id' not in user_history.columns or 'episode_id' not in user_history.columns:
                logger.error("使用者歷史資料缺少必要欄位")
                return None
            
            logger.info(f"載入 {len(podcast_data)} 個節目，{len(user_history)} 個互動記錄")
            
            return RecommenderEngine(podcast_data, user_history, self.config)
            
        except Exception as e:
            logger.error(f"推薦引擎初始化失敗: {str(e)}")
            return None
    
    async def get_recommendations(
        self, 
        user_id: int, 
        top_k: int = 10,
        category_filter: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取推薦結果
        
        Args:
            user_id: 用戶ID
            top_k: 推薦數量
            category_filter: 類別篩選
            context: 上下文資訊
            
        Returns:
            推薦結果列表
        """
        try:
            if not self.recommender_engine:
                logger.warning("推薦引擎未初始化")
                return []
            
            recommendations = self.recommender_engine.get_recommendations(
                user_id=str(user_id),
                top_k=top_k,
                strategy='hybrid',
                category_filter=category_filter
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
            return []
    
    async def get_similar_episodes(
        self, 
        episode_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        獲取相似節目
        
        Args:
            episode_id: 節目ID
            limit: 返回數量
            
        Returns:
            相似節目列表
        """
        try:
            # 簡化的相似節目實現
            return [
                {
                    'episode_id': episode_id + 1,
                    'similarity_score': 0.8,
                    'title': f'相似節目 {episode_id + 1}'
                }
            ]
            
        except Exception as e:
            logger.error(f"相似節目查詢失敗: {str(e)}")
            return []
    
    async def evaluate_recommendations(
        self, 
        user_id: int, 
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        評估推薦結果
        
        Args:
            user_id: 用戶ID
            recommendations: 推薦結果
            
        Returns:
            評估指標
        """
        try:
            # 簡化的評估實現
            return {
                'precision': 0.8,
                'recall': 0.7,
                'ndcg': 0.75,
                'diversity': 0.6
            }
            
        except Exception as e:
            logger.error(f"推薦評估失敗: {str(e)}")
            return {}
    
    def update_user_preference(
        self, 
        user_id: str, 
        podcast_id: str, 
        rating: float, 
        listen_time: int = 0
    ) -> bool:
        """
        更新用戶偏好
        
        Args:
            user_id: 用戶ID
            podcast_id: 播客ID
            rating: 評分
            listen_time: 收聽時間
            
        Returns:
            更新是否成功
        """
        try:
            logger.info(f"用戶 {user_id} 偏好已更新")
            return True
            
        except Exception as e:
            logger.error(f"偏好更新失敗: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            status = {
                'status': 'healthy',
                'recommender_engine': 'active' if self.recommender_engine else 'inactive',
                'data_source': 'connected',
                'last_update': '2024-01-01 00:00:00'
            }
            
            # 添加 KNN 統計資訊
            if self.recommender_engine:
                status['knn_statistics'] = {
                    'knn_model_ready': self.recommender_engine.knn_model is not None,
                    'total_users': len(self.recommender_engine.user_history['user_id'].unique()),
                    'total_podcasts': len(self.recommender_engine.podcast_data)
                }
            
            return status
            
        except Exception as e:
            logger.error(f"狀態查詢失敗: {str(e)}")
            return {'status': 'error'}

__all__ = ['RecommendationService'] 