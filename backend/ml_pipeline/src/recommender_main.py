"""
推薦系統主入口模組
整合所有推薦系統組件
"""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime

from .recommender import Recommender
from .recommender_data import RecommenderData
from .recommender_evaluator import RecommenderEvaluator
from .recommender_config import get_recommender_config

class RecommenderSystem:
    """推薦系統主控制器"""

    def __init__(self, db_url: str, config: Optional[Dict] = None):
        """
        初始化推薦系統
        
        Args:
            db_url: 數據庫連接 URL
            config: 配置參數（可選）
        """
        # 初始化組件
        self.data = RecommenderData(db_url)
        self.evaluator = RecommenderEvaluator()
        
        # 載入配置
        self.config = config or get_recommender_config()
        self.recommender = Recommender(self.config["base"])

    async def get_recommendations(
        self,
        user_id: int,
        episode_id: Optional[int] = None,
        context: Optional[Dict] = None,
        rag_result: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取推薦結果
        
        Args:
            user_id: 用戶ID
            episode_id: 目標節目ID（可選）
            context: 上下文資訊（可選）
            rag_result: RAG 處理結果（可選）
            
        Returns:
            List[Dict[str, Any]]: 推薦結果列表
        """
        try:
            # 獲取用戶數據
            user_data = self.data.get_user_data(user_id)
            
            # 整合上下文
            if not context:
                context = {}
            context["user_data"] = user_data
            
            # 獲取推薦結果
            recommendations = await self.recommender.get_recommendations(
                user_id=user_id,
                episode_id=episode_id,
                context=context,
                rag_result=rag_result
            )
            
            # 評估推薦結果
            if episode_id:
                episode_data = self.data.get_episode_data(episode_id)
                evaluation = self.evaluator.evaluate(
                    recommendations=recommendations,
                    ground_truth=[episode_data],
                    user_history=user_data.get("interactions", []),
                    total_items=len(self.data.episodes)
                )
                context["evaluation"] = evaluation
            
            return recommendations
            
        except Exception as e:
            print(f"生成推薦時發生錯誤: {str(e)}")
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
            Dict[str, float]: 評估指標
        """
        try:
            # 獲取用戶數據
            user_data = self.data.get_user_data(user_id)
            
            # 獲取用戶歷史數據
            user_history = user_data.get("interactions", [])
            
            # 獲取用戶評分數據作為真實數據
            ground_truth = [
                self.data.get_episode_data(rating["episode_id"])
                for rating in user_data.get("ratings", [])
            ]
            
            # 評估推薦結果
            evaluation = self.evaluator.evaluate(
                recommendations=recommendations,
                ground_truth=ground_truth,
                user_history=user_history,
                total_items=len(self.data.episodes)
            )
            
            return evaluation
            
        except Exception as e:
            print(f"評估推薦結果時發生錯誤: {str(e)}")
            return {}

    def update_config(self, new_config: Dict):
        """
        更新配置
        
        Args:
            new_config: 新的配置參數
        """
        self.config.update(new_config)
        self.recommender.update_config(self.config["base"])

    def update_data(self):
        """更新數據"""
        self.data.update_data()

async def main():
    """主函數"""
    # 初始化推薦系統
    recommender = RecommenderSystem(
        db_url="postgresql://user:password@localhost:5432/podwise"
    )
    
    # 獲取推薦結果
    recommendations = await recommender.get_recommendations(
        user_id=1,
        episode_id=1
    )
    
    # 評估推薦結果
    evaluation = await recommender.evaluate_recommendations(
        user_id=1,
        recommendations=recommendations
    )
    
    print("推薦結果:", recommendations)
    print("評估指標:", evaluation)

if __name__ == "__main__":
    asyncio.run(main()) 