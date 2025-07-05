#!/usr/bin/env python3
"""
推薦系統主控制器
整合所有推薦組件，提供統一的推薦服務
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .recommender import Recommender
from .recommender_data import RecommenderData
from .recommender_evaluator import RecommenderEvaluator
from ..config.recommender_config import get_recommender_config

logger = logging.getLogger(__name__)

class RecommenderSystem:
    """推薦系統主控制器"""
    
    def __init__(self, db_url: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化推薦系統
        
        Args:
            db_url: 資料庫連接 URL
            config: 配置參數
        """
        self.db_url = db_url
        self.data = RecommenderData(db_url)
        self.evaluator = RecommenderEvaluator()
        
        # 設定配置
        self.config = config or get_recommender_config()
        self.recommender = Recommender(self.config["base"])
        
        logger.info("推薦系統初始化完成")
    
    async def get_recommendations(
        self, 
        user_id: int, 
        episode_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取推薦結果
        
        Args:
            user_id: 用戶ID
            episode_id: 目標節目ID（可選）
            context: 上下文資訊
            
        Returns:
            推薦結果列表
        """
        try:
            logger.info(f"為用戶 {user_id} 生成推薦")
            
            # 獲取用戶數據
            user_data = self.data.get_user_data(user_id)
            if not user_data:
                logger.warning(f"用戶 {user_id} 數據不存在")
                return []
            
            # 獲取推薦
            recommendations = await self.recommender.get_recommendations(
                user_id=user_id,
                episode_id=episode_id,
                context=context
            )
            
            # 添加元數據
            enhanced_recommendations = []
            for rec in recommendations:
                episode_data = self.data.get_episode_data(rec.get('episode_id'))
                if episode_data:
                    rec.update(episode_data)
                enhanced_recommendations.append(rec)
            
            logger.info(f"為用戶 {user_id} 生成 {len(enhanced_recommendations)} 個推薦")
            return enhanced_recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
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
            recommendations: 推薦結果列表
            
        Returns:
            評估指標
        """
        try:
            logger.info(f"評估用戶 {user_id} 的推薦結果")
            
            # 獲取用戶真實偏好
            user_preferences = self.data.get_user_preferences(user_id)
            
            # 執行評估
            metrics = self.evaluator.evaluate_recommendations(
                recommendations=recommendations,
                user_preferences=user_preferences
            )
            
            logger.info(f"評估完成，指標: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"推薦評估失敗: {str(e)}")
            return {}
    
    def update_data(self):
        """更新數據快取"""
        try:
            logger.info("開始更新數據快取")
            self.data.refresh_cache()
            logger.info("數據快取更新完成")
            
        except Exception as e:
            logger.error(f"數據更新失敗: {str(e)}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            new_config: 新配置
        """
        try:
            self.config.update(new_config)
            self.recommender.update_config(self.config["base"])
            logger.info("配置更新完成")
            
        except Exception as e:
            logger.error(f"配置更新失敗: {str(e)}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統信息"""
        return {
            'version': '1.0.0',
            'config': self.config,
            'data_summary': self.data.get_data_summary(),
            'last_update': datetime.now().isoformat()
        }

# 使用範例
async def main():
    """主函數範例"""
    # 初始化推薦系統
    config = get_recommender_config()
    recommender_system = RecommenderSystem(
        db_url="postgresql://user:password@localhost:5432/podwise",
        config=config
    )
    
    # 獲取推薦
    recommendations = await recommender_system.get_recommendations(
        user_id=1,
        context={"limit": 10}
    )
    
    # 評估推薦
    evaluation = await recommender_system.evaluate_recommendations(
        user_id=1,
        recommendations=recommendations
    )
    
    print(f"推薦結果: {recommendations}")
    print(f"評估指標: {evaluation}")

if __name__ == "__main__":
    asyncio.run(main()) 