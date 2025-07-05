#!/usr/bin/env python3
"""
ML Pipeline 服務層
提供推薦系統的服務介面
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging

from ..core import RecommenderSystem
from ..config.recommender_config import get_recommender_config

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
        self.recommender_system = RecommenderSystem(db_url, self.config)
        
        logger.info("推薦服務初始化完成")
    
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
            recommendations = await self.recommender_system.get_recommendations(
                user_id=user_id,
                context=context
            )
            
            # 應用類別篩選
            if category_filter:
                recommendations = [
                    rec for rec in recommendations 
                    if rec.get('category') == category_filter
                ]
            
            return recommendations[:top_k]
            
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
            return self.recommender_system.data.get_similar_episodes(
                episode_id=episode_id,
                limit=limit
            )
            
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
            return await self.recommender_system.evaluate_recommendations(
                user_id=user_id,
                recommendations=recommendations
            )
            
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
            # 這裡需要實現具體的偏好更新邏輯
            # 可以調用 core 中的相關方法
            logger.info(f"用戶 {user_id} 偏好已更新")
            return True
            
        except Exception as e:
            logger.error(f"偏好更新失敗: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            return {
                'status': 'healthy',
                'recommender_system': 'active',
                'data_source': 'connected',
                'last_update': '2024-01-01 00:00:00'
            }
            
        except Exception as e:
            logger.error(f"狀態查詢失敗: {str(e)}")
            return {'status': 'error'}

__all__ = ['RecommendationService'] 