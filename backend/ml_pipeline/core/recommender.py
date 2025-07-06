#!/usr/bin/env python3
"""
核心推薦器模組
提供統一的推薦介面，整合各種推薦策略
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
import pandas as pd

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Recommender:
    """
    核心推薦器類別
    整合各種推薦策略，提供統一的推薦介面
    """
    
    def __init__(self, podcast_data: pd.DataFrame, user_history: pd.DataFrame, config: Dict[str, Any]):
        """
        初始化推薦器
        
        Args:
            podcast_data: Podcast 資料
            user_history: 使用者收聽紀錄
            config: 推薦配置參數
        """
        self.podcast_data = podcast_data
        self.user_history = user_history
        self.config = config
        
        # 初始化各推薦策略
        self._init_strategies()
        
        logger.info("核心推薦器初始化完成")
    
    def _init_strategies(self):
        """初始化推薦策略"""
        try:
            from .podcast_recommender import PodcastRecommender
            from .gnn_podcast_recommender import GNNPodcastRecommender
            from .hybrid_gnn_recommender import HybridGNNRecommender
            
            # 初始化各推薦策略
            self.podcast_recommender = PodcastRecommender(self.podcast_data, self.user_history)
            self.gnn_recommender = GNNPodcastRecommender(self.podcast_data, self.user_history)
            self.hybrid_recommender = HybridGNNRecommender(self.podcast_data, self.user_history)
            
            # 策略映射
            self.strategies = {
                'collaborative': self._collaborative_strategy,
                'content': self._content_strategy,
                'gnn': self._gnn_strategy,
                'hybrid': self._hybrid_strategy
            }
            
            logger.info(f"已載入 {len(self.strategies)} 個推薦策略")
            
        except Exception as e:
            logger.error(f"推薦策略初始化失敗: {str(e)}")
    
    async def get_recommendations(
        self,
        user_id: str,
        top_k: int = 5,
        strategy: str = 'hybrid',
        category_filter: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取推薦結果
        
        Args:
            user_id: 用戶ID
            top_k: 推薦數量
            strategy: 推薦策略 ('collaborative', 'content', 'gnn', 'hybrid')
            category_filter: 類別篩選
            context: 上下文資訊
            
        Returns:
            List[Dict[str, Any]]: 推薦結果列表
        """
        try:
            # 選擇推薦策略
            if strategy not in self.strategies:
                logger.warning(f"未知策略 {strategy}，使用 hybrid")
                strategy = 'hybrid'
            
            # 執行推薦策略
            recommendations = await self.strategies[strategy](
                user_id=user_id,
                top_k=top_k,
                category_filter=category_filter,
                context=context
            )
            
            # 後處理推薦結果
            recommendations = self._post_process_recommendations(
                recommendations, context
            )
            
            logger.info(f"為用戶 {user_id} 生成 {len(recommendations)} 個 {strategy} 推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
            return []
    
    async def _collaborative_strategy(
        self,
        user_id: str,
        top_k: int,
        category_filter: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """協同過濾策略"""
        try:
            # 委派給 PodcastRecommender 的協同過濾功能
            recommendations = self.podcast_recommender.get_recommendations(
                user_id=user_id,
                top_k=top_k,
                category_filter=category_filter
            )
            
            # 標記策略來源
            for rec in recommendations:
                rec['strategy'] = 'collaborative'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"協同過濾策略失敗: {str(e)}")
            return []
    
    async def _content_strategy(
        self,
        user_id: str,
        top_k: int,
        category_filter: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """內容式推薦策略"""
        try:
            # 委派給 PodcastRecommender 的內容式推薦功能
            recommendations = self.podcast_recommender.get_recommendations(
                user_id=user_id,
                top_k=top_k,
                category_filter=category_filter
            )
            
            # 標記策略來源
            for rec in recommendations:
                rec['strategy'] = 'content'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"內容式推薦策略失敗: {str(e)}")
            return []
    
    async def _gnn_strategy(
        self,
        user_id: str,
        top_k: int,
        category_filter: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """圖神經網路策略"""
        try:
            # 委派給 GNNPodcastRecommender
            recommendations = self.gnn_recommender.get_recommendations(
                user_id=user_id,
                top_k=top_k,
                category_filter=category_filter
            )
            
            # 標記策略來源
            for rec in recommendations:
                rec['strategy'] = 'gnn'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"GNN 策略失敗: {str(e)}")
            return []
    
    async def _hybrid_strategy(
        self,
        user_id: str,
        top_k: int,
        category_filter: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """混合推薦策略"""
        try:
            # 委派給 HybridGNNRecommender
            recommendations = self.hybrid_recommender.get_recommendations(
                user_id=user_id,
                top_k=top_k,
                category_filter=category_filter
            )
            
            # 標記策略來源
            for rec in recommendations:
                rec['strategy'] = 'hybrid'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"混合推薦策略失敗: {str(e)}")
            return []
    
    def _post_process_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """後處理推薦結果"""
        try:
            processed_recommendations = []
            
            for rec in recommendations:
                # 添加上下文資訊
                if context:
                    rec['context'] = context
                
                # 添加時間戳
                rec['timestamp'] = asyncio.get_event_loop().time()
                
                processed_recommendations.append(rec)
            
            return processed_recommendations
            
        except Exception as e:
            logger.error(f"推薦結果後處理失敗: {str(e)}")
            return recommendations
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            new_config: 新的配置參數
        """
        try:
            self.config.update(new_config)
            logger.info("推薦器配置已更新")
            
        except Exception as e:
            logger.error(f"配置更新失敗: {str(e)}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略資訊"""
        return {
            'available_strategies': list(self.strategies.keys()),
            'config': self.config,
            'status': 'active'
        } 