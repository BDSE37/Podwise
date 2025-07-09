#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主模組

提供統一的 OOP 介面，整合所有 RAG Pipeline 功能：
- Apple Podcast 優先推薦系統
- 層級化 CrewAI 架構
- 語意檢索（text2vec-base-chinese + TAG_info.csv）
- 提示詞模板系統
- 聊天歷史記錄
- 效能優化

作者: Podwise Team
版本: 2.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入核心模組
from .core.crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent, UserQuery, AgentResponse
from .core.hierarchical_rag_pipeline import HierarchicalRAGPipeline, RAGResponse
from .core.apple_podcast_ranking import ApplePodcastRankingSystem
from .core.integrated_core import UnifiedQueryProcessor
from .core.content_categorizer import ContentCategorizer
from .core.qwen_llm_manager import Qwen3LLMManager
from .core.chat_history_service import get_chat_history_service
from .config.prompt_templates import PodwisePromptTemplates
from .config.integrated_config import get_config
from .tools.enhanced_podcast_recommender import EnhancedPodcastRecommender


class PodwiseRAGPipeline:
    """
    Podwise RAG Pipeline 主類別
    
    提供統一的介面來使用所有 RAG Pipeline 功能
    專注於核心 RAG 處理邏輯，符合 OOP 和 Google Clean Code 原則
    """
    
    def __init__(self, 
                 enable_monitoring: bool = True,
                 enable_semantic_retrieval: bool = True,
                 enable_chat_history: bool = True,
                 enable_apple_ranking: bool = True,
                 confidence_threshold: float = 0.7):
        """
        初始化 RAG Pipeline
        
        Args:
            enable_monitoring: 是否啟用監控
            enable_semantic_retrieval: 是否啟用語意檢索
            enable_chat_history: 是否啟用聊天歷史記錄
            enable_apple_ranking: 是否啟用 Apple Podcast 排名系統
            confidence_threshold: 信心度閾值
        """
        self.enable_monitoring = enable_monitoring
        self.enable_semantic_retrieval = enable_semantic_retrieval
        self.enable_chat_history = enable_chat_history
        self.enable_apple_ranking = enable_apple_ranking
        self.confidence_threshold = confidence_threshold
        
        # 初始化整合配置
        self.config = get_config()
        
        # 初始化提示詞模板
        self.prompt_templates = PodwisePromptTemplates()
        
        # 初始化 LLM 管理器
        self.llm_manager = Qwen3LLMManager()
        
        # 初始化內容處理器
        self.categorizer = ContentCategorizer()
        
        # 初始化聊天歷史服務
        self.chat_history = get_chat_history_service() if enable_chat_history else None
        
        # 初始化 Apple Podcast 排名系統
        self.apple_ranking = ApplePodcastRankingSystem() if enable_apple_ranking else None
        
        # 初始化增強推薦器
        self.enhanced_recommender = EnhancedPodcastRecommender()
        
        # 初始化 CrewAI 代理
        self._initialize_agents()
        
        # 初始化層級化 RAG Pipeline
        self.rag_pipeline = HierarchicalRAGPipeline()
        
        # 初始化整合核心
        self.integrated_core = UnifiedQueryProcessor({})
        
        logger.info("✅ Podwise RAG Pipeline 初始化完成")
    
    def _initialize_agents(self):
        """初始化 CrewAI 代理"""
        config = {
            'confidence_threshold': self.confidence_threshold,
            'max_processing_time': 30.0
        }
        
        self.user_manager = UserManagerAgent(config)
        self.business_expert = BusinessExpertAgent(config)
        self.education_expert = EducationExpertAgent(config)
        self.leader_agent = LeaderAgent(config)
        
        logger.info("✅ CrewAI 代理初始化完成")
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "default_user",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢（核心 RAG 功能）
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        
        # 記錄用戶查詢到聊天歷史
        if self.enable_chat_history and self.chat_history:
            try:
                self.chat_history.save_chat_message(
                    user_id=user_id,
                    session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                    role="user",
                    content=query,
                    chat_mode="rag",
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"記錄用戶查詢失敗: {e}")
        
        try:
            # 使用層級化 RAG Pipeline 處理
            response = await self.rag_pipeline.process_query(query)
            
            # 應用 Apple Podcast 排名（如果啟用）
            if self.enable_apple_ranking and self.apple_ranking:
                response = await self._apply_apple_ranking(response, query)
            
            # 記錄助手回應到聊天歷史
            if self.enable_chat_history and self.chat_history:
                try:
                    self.chat_history.save_chat_message(
                        user_id=user_id,
                        session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                        role="assistant",
                        content=response.content,
                        chat_mode="rag",
                        metadata={
                            "confidence": response.confidence,
                            "level_used": response.level_used,
                            "sources_count": len(response.sources),
                            "apple_ranking_applied": self.enable_apple_ranking,
                            **(metadata or {})
                        }
                    )
                except Exception as e:
                    logger.warning(f"記錄助手回應失敗: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"處理查詢失敗: {e}")
            
            # 記錄錯誤回應
            if self.enable_chat_history and self.chat_history:
                try:
                    self.chat_history.save_chat_message(
                        user_id=user_id,
                        session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                        role="assistant",
                        content=f"抱歉，處理您的查詢時發生錯誤: {str(e)}",
                        chat_mode="rag",
                        metadata={"error": str(e), "error_type": type(e).__name__}
                    )
                except Exception as history_error:
                    logger.warning(f"記錄錯誤回應失敗: {history_error}")
            
            # 返回錯誤回應
            return RAGResponse(
                content=f"抱歉，處理您的查詢時發生錯誤: {str(e)}",
                confidence=0.0,
                level_used="error",
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error": str(e)}
            )
    
    async def _apply_apple_ranking(self, response: RAGResponse, query: str) -> RAGResponse:
        """應用 Apple Podcast 排名系統"""
        try:
            # 從 metadata 中獲取推薦結果
            recommendations = response.metadata.get('recommendations', [])
            if recommendations and self.apple_ranking:
                # 轉換為 ApplePodcastRating 格式
                from .core.apple_podcast_ranking import ApplePodcastRating
                podcast_ratings = []
                for rec in recommendations:
                    if isinstance(rec, dict) and 'rss_id' in rec:
                        rating = ApplePodcastRating(
                            rss_id=rec.get('rss_id', ''),
                            title=rec.get('title', ''),
                            apple_rating=rec.get('apple_rating', 3.0),
                            apple_review_count=rec.get('apple_review_count', 0),
                            user_click_rate=rec.get('user_click_rate', 0.5),
                            comment_sentiment_score=rec.get('comment_sentiment_score', 0.0),
                            total_comments=rec.get('total_comments', 0),
                            positive_comments=rec.get('positive_comments', 0),
                            negative_comments=rec.get('negative_comments', 0),
                            neutral_comments=rec.get('neutral_comments', 0)
                        )
                        podcast_ratings.append(rating)
                
                if podcast_ratings:
                    ranked_scores = self.apple_ranking.rank_podcasts(podcast_ratings)
                    # 更新推薦結果
                    response.metadata['ranked_recommendations'] = ranked_scores
                    logger.info("✅ Apple Podcast 排名已應用")
        except Exception as e:
            logger.warning(f"應用 Apple Podcast 排名失敗: {e}")
        
        return response
    
    async def process_with_agents(self, 
                                 query: str, 
                                 user_id: str = "default_user") -> AgentResponse:
        """
        使用 CrewAI 代理處理查詢
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            
        Returns:
            AgentResponse: 代理處理結果
        """
        try:
            # 創建用戶查詢對象
            user_query = UserQuery(
                query=query,
                user_id=user_id
            )
            
            # 使用領導者代理處理
            response = await self.leader_agent.process(user_query)
            
            return response
            
        except Exception as e:
            logger.error(f"代理處理查詢失敗: {e}")
            return AgentResponse(
                content=f"抱歉，代理處理您的查詢時發生錯誤: {str(e)}",
                confidence=0.0,
                reasoning="處理失敗",
                metadata={"error": str(e)}
            )
    
    async def get_enhanced_recommendations(self, 
                                         query: str, 
                                         user_id: str = "default_user") -> Dict[str, Any]:
        """
        獲取增強推薦結果
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            
        Returns:
            Dict[str, Any]: 增強推薦結果
        """
        try:
            # 使用整合核心處理
            from .core.integrated_core import UserQuery as IntegratedUserQuery
            user_query = IntegratedUserQuery(query=query, user_id=user_id)
            result = await self.integrated_core.process_query(user_query)
            
            return {
                "success": True,
                "content": result.content,
                "confidence": result.confidence,
                "sources": result.sources,
                "processing_time": result.processing_time
            }
            
        except Exception as e:
            logger.error(f"獲取增強推薦失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "confidence": 0.0
            }
    
    def get_semantic_config(self) -> Optional[Dict[str, Any]]:
        """獲取語意檢索配置"""
        return self.config.get_semantic_config() if self.enable_semantic_retrieval else None
    
    def get_prompt_templates(self) -> Dict[str, str]:
        """獲取提示詞模板"""
        return {
            "system": self.prompt_templates.SYSTEM_PROMPT.content,
            "category_classifier": self.prompt_templates.CATEGORY_CLASSIFIER_PROMPT.content,
            "business_expert": self.prompt_templates.BUSINESS_EXPERT_PROMPT.content,
            "education_expert": self.prompt_templates.EDUCATION_EXPERT_PROMPT.content,
            "leader_decision": self.prompt_templates.LEADER_DECISION_PROMPT.content
        }
    
    def is_monitoring_enabled(self) -> bool:
        """檢查是否啟用監控"""
        return self.enable_monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "llm_manager": self.llm_manager.get_best_model() is not None,
                "chat_history": self.chat_history is not None if self.enable_chat_history else True,
                "apple_ranking": self.apple_ranking is not None if self.enable_apple_ranking else True,
                "enhanced_recommender": self.enhanced_recommender is not None,
                "rag_pipeline": True,
                "integrated_core": True
            },
            "config": {
                "enable_monitoring": self.enable_monitoring,
                "enable_semantic_retrieval": self.enable_semantic_retrieval,
                "enable_chat_history": self.enable_chat_history,
                "enable_apple_ranking": self.enable_apple_ranking,
                "confidence_threshold": self.confidence_threshold
            }
        }
        
        # 檢查各組件健康狀態
        for component, status in health_status["components"].items():
            if not status:
                health_status["status"] = "degraded"
        
        return health_status
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "version": "2.0.0",
            "name": "Podwise RAG Pipeline",
            "description": "整合 Apple Podcast 排名系統的智能推薦引擎",
            "features": [
                "Apple Podcast 優先推薦系統",
                "層級化 CrewAI 架構",
                "語意檢索",
                "提示詞模板系統",
                "聊天歷史記錄",
                "效能優化"
            ],
            "config": self.config.get_rag_config()
        }


# 全域實例
_rag_pipeline_instance: Optional[PodwiseRAGPipeline] = None


def get_rag_pipeline() -> PodwiseRAGPipeline:
    """獲取 RAG Pipeline 實例（單例模式）"""
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = PodwiseRAGPipeline()
    return _rag_pipeline_instance


async def main():
    """主函數 - 用於測試"""
    # 創建 RAG Pipeline 實例
    pipeline = PodwiseRAGPipeline()
    
    # 測試查詢
    test_query = "推薦一些投資理財的 Podcast"
    print(f"測試查詢: {test_query}")
    
    # 處理查詢
    response = await pipeline.process_query(test_query, "test_user")
    
    print(f"回應: {response.content}")
    print(f"信心度: {response.confidence}")
    print(f"處理時間: {response.processing_time:.2f}秒")
    
    # 健康檢查
    health = await pipeline.health_check()
    print(f"健康狀態: {health['status']}")


if __name__ == "__main__":
    asyncio.run(main()) 