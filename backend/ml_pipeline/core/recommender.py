#!/usr/bin/env python3
"""
核心推薦器模組
提供統一的推薦介面，整合各種推薦策略
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Recommender:
    """
    核心推薦器類別
    整合各種推薦策略，提供統一的推薦介面
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化推薦器
        
        Args:
            config: 推薦配置參數
        """
        self.config = config
        self.strategies = {}
        self._init_strategies()
        
        logger.info("核心推薦器初始化完成")
    
    def _init_strategies(self):
        """初始化推薦策略"""
        try:
            # 這裡可以根據配置載入不同的推薦策略
            # 例如：協同過濾、內容式推薦、深度學習等
            self.strategies = {
                'collaborative': self._collaborative_strategy,
                'content': self._content_strategy,
                'hybrid': self._hybrid_strategy
            }
            
            logger.info(f"已載入 {len(self.strategies)} 個推薦策略")
            
        except Exception as e:
            logger.error(f"推薦策略初始化失敗: {str(e)}")
    
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
            # 根據上下文選擇推薦策略
            strategy = self._select_strategy(context)
            
            # 執行推薦策略
            recommendations = await self.strategies[strategy](
                user_id=user_id,
                episode_id=episode_id,
                context=context,
                rag_result=rag_result
            )
            
            # 後處理推薦結果
            recommendations = self._post_process_recommendations(
                recommendations, context, rag_result
            )
            
            logger.info(f"為用戶 {user_id} 生成 {len(recommendations)} 個推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
            return []
    
    def _select_strategy(self, context: Optional[Dict]) -> str:
        """選擇推薦策略"""
        if not context:
            return 'hybrid'
        
        # 根據上下文選擇策略
        if context.get('prefer_collaborative', False):
            return 'collaborative'
        elif context.get('prefer_content', False):
            return 'content'
        else:
            return 'hybrid'
    
    async def _collaborative_strategy(
        self,
        user_id: int,
        episode_id: Optional[int] = None,
        context: Optional[Dict] = None,
        rag_result: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """協同過濾策略"""
        try:
            # 這裡實現協同過濾邏輯
            # 暫時返回模擬數據
            return [
                {
                    'episode_id': 1,
                    'title': '協同過濾推薦節目',
                    'score': 0.85,
                    'strategy': 'collaborative'
                }
            ]
            
        except Exception as e:
            logger.error(f"協同過濾策略失敗: {str(e)}")
            return []
    
    async def _content_strategy(
        self,
        user_id: int,
        episode_id: Optional[int] = None,
        context: Optional[Dict] = None,
        rag_result: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """內容式推薦策略"""
        try:
            # 這裡實現內容式推薦邏輯
            # 暫時返回模擬數據
            return [
                {
                    'episode_id': 2,
                    'title': '內容式推薦節目',
                    'score': 0.78,
                    'strategy': 'content'
                }
            ]
            
        except Exception as e:
            logger.error(f"內容式推薦策略失敗: {str(e)}")
            return []
    
    async def _hybrid_strategy(
        self,
        user_id: int,
        episode_id: Optional[int] = None,
        context: Optional[Dict] = None,
        rag_result: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """混合推薦策略"""
        try:
            # 結合多種策略
            cf_results = await self._collaborative_strategy(user_id, episode_id, context, rag_result)
            cb_results = await self._content_strategy(user_id, episode_id, context, rag_result)
            
            # 合併結果
            all_results = cf_results + cb_results
            
            # 去重並排序
            seen = set()
            unique_results = []
            for result in all_results:
                if result['episode_id'] not in seen:
                    seen.add(result['episode_id'])
                    unique_results.append(result)
            
            # 按分數排序
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"混合推薦策略失敗: {str(e)}")
            return []
    
    def _post_process_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context: Optional[Dict],
        rag_result: Optional[str]
    ) -> List[Dict[str, Any]]:
        """後處理推薦結果"""
        try:
            processed_recommendations = []
            
            for rec in recommendations:
                # 添加 RAG 結果（如果可用）
                if rag_result:
                    rec['rag_context'] = rag_result
                
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
            self._init_strategies()
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