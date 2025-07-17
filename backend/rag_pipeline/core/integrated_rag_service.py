#!/usr/bin/env python3
"""
整合 RAG 服務

整合所有 RAG Pipeline 組件：
- LLM 整合服務
- 增強版 Milvus 搜尋
- 現有 RAG Pipeline
- CrewAI 代理
- TTS 服務

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 導入現有組件
from core.llm_integration import LLMIntegrationService, LLMConfig
from core.enhanced_milvus_search import EnhancedMilvusSearch, EnhancedSearchConfig
from core.crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent
from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline, RAGResponse
from core.apple_podcast_ranking import ApplePodcastRankingSystem
from core.content_categorizer import ContentCategorizer
from core.qwen_llm_manager import Qwen3LLMManager
from core.chat_history_service import get_chat_history_service
from core.api_models import UserQueryRequest, UserQueryResponse

logger = logging.getLogger(__name__)


@dataclass
class IntegratedRAGConfig:
    """整合 RAG 配置"""
    # LLM 配置
    llm_host: str = "localhost"
    llm_port: int = 8003
    enable_llm_enhancement: bool = True
    
    # Milvus 配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
            collection_name: str = "podcast_chunks"
    
    # 搜尋配置
    similarity_threshold: float = 0.7
    top_k: int = 10
    enable_rerank: bool = True
    
    # 系統配置
    enable_monitoring: bool = True
    enable_chat_history: bool = True
    enable_apple_ranking: bool = True
    confidence_threshold: float = 0.7


class IntegratedRAGService:
    """整合 RAG 服務"""
    
    def __init__(self, config: Optional[IntegratedRAGConfig] = None):
        self.config = config or IntegratedRAGConfig()
        
        # 初始化 LLM 整合服務
        llm_config = LLMConfig(
            host=self.config.llm_host,
            port=self.config.llm_port
        )
        self.llm_service = LLMIntegrationService(llm_config)
        
        # 初始化增強版 Milvus 搜尋
        enhanced_config = EnhancedSearchConfig(
            milvus_host=self.config.milvus_host,
            milvus_port=self.config.milvus_port,
            collection_name=self.config.collection_name,
            similarity_threshold=self.config.similarity_threshold,
            llm_host=self.config.llm_host,
            llm_port=self.config.llm_port,
            enable_llm_enhancement=self.config.enable_llm_enhancement,
            enable_result_rerank=self.config.enable_rerank,
            top_k=self.config.top_k
        )
        self.enhanced_search = EnhancedMilvusSearch(enhanced_config)
        
        # 初始化現有組件
        self._init_existing_components()
        
        # 搜尋統計
        self.search_stats = {
            "total_queries": 0,
            "llm_enhanced_queries": 0,
            "milvus_searches": 0,
            "fallback_searches": 0,
            "average_response_time": 0.0
        }
    
    def _init_existing_components(self):
        """初始化現有組件"""
        try:
            # 初始化 LLM 管理器
            self.llm_manager = Qwen3LLMManager()
            
            # 初始化內容分類器
            self.categorizer = ContentCategorizer()
            
            # 初始化聊天歷史服務
            self.chat_history = get_chat_history_service() if self.config.enable_chat_history else None
            
            # 初始化 Apple Podcast 排名系統
            self.apple_ranking = ApplePodcastRankingSystem() if self.config.enable_apple_ranking else None
            
            # 初始化 CrewAI 代理
            self._init_crew_agents()
            
            # 初始化層級化 RAG Pipeline
            self.rag_pipeline = HierarchicalRAGPipeline()
            
            logger.info("✅ 現有組件初始化完成")
            
        except Exception as e:
            logger.error(f"現有組件初始化失敗: {e}")
    
    def _init_crew_agents(self):
        """初始化 CrewAI 代理"""
        config = {
            'confidence_threshold': self.config.confidence_threshold,
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
                           enable_tts: bool = True,
                           voice: str = "podrina",
                           speed: float = 1.0) -> Dict[str, Any]:
        """處理用戶查詢"""
        start_time = datetime.now()
        
        try:
            self.search_stats["total_queries"] += 1
            
            # 1. LLM 查詢增強
            enhanced_query = await self._enhance_query_with_llm(query)
            
            # 2. 增強版 Milvus 搜尋
            search_results = await self._enhanced_search_with_milvus(enhanced_query)
            
            # 3. 生成回應
            response = await self._generate_response(query, search_results, enhanced_query)
            
            # 4. 應用 Apple Podcast 排名（如果可用）
            if self.apple_ranking:
                response = await self._apply_apple_ranking(response, query)
            
            # 5. TTS 合成（如果需要）
            audio_data = None
            if enable_tts and response.get("content"):
                audio_data = await self._synthesize_speech(response["content"], voice, speed)
            
            # 6. 記錄聊天歷史
            if self.chat_history:
                await self._log_chat_history(user_id, session_id, query, response.get("content", ""))
            
            # 7. 更新統計
            self._update_stats(start_time)
            
            # 8. 構建最終回應
            final_response = {
                "query": query,
                "response": response.get("content", ""),
                "recommendations": response.get("recommendations", []),
                "confidence": response.get("confidence", 0.0),
                "sources": response.get("sources", []),
                "enhanced_query": enhanced_query,
                "search_results": search_results[:3],  # 只返回前3個結果
                "tts_enabled": enable_tts,
                "voice_used": voice if enable_tts else None,
                "speed_used": speed if enable_tts else None,
                "audio_data": audio_data,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
            return final_response
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {e}")
            return {
                "query": query,
                "response": "抱歉，處理您的查詢時發生錯誤。",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _enhance_query_with_llm(self, query: str) -> Dict[str, Any]:
        """使用 LLM 增強查詢"""
        try:
            if not self.config.enable_llm_enhancement:
                return {
                    "original_query": query,
                    "rewritten_query": query,
                    "tags": {},
                    "expansions": [],
                    "enhanced_at": datetime.now().isoformat()
                }
            
            enhanced = await self.llm_service.enhance_query(query)
            if enhanced["rewritten_query"] != query:
                self.search_stats["llm_enhanced_queries"] += 1
            
            return enhanced
            
        except Exception as e:
            logger.error(f"LLM 查詢增強失敗: {e}")
            return {
                "original_query": query,
                "rewritten_query": query,
                "tags": {},
                "expansions": [],
                "enhanced_at": datetime.now().isoformat()
            }
    
    async def _enhanced_search_with_milvus(self, enhanced_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用增強版 Milvus 搜尋"""
        try:
            query_text = enhanced_query.get("rewritten_query", enhanced_query.get("original_query", ""))
            
            # 執行增強搜尋
            results = await self.enhanced_search.search(query_text)
            
            if results:
                self.search_stats["milvus_searches"] += 1
            else:
                self.search_stats["fallback_searches"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"增強 Milvus 搜尋失敗: {e}")
            self.search_stats["fallback_searches"] += 1
            return []
    
    async def _generate_response(self, query: str, search_results: List[Dict[str, Any]], 
                                enhanced_query: Dict[str, Any]) -> Dict[str, Any]:
        """生成回應"""
        try:
            # 使用現有的 RAG Pipeline 生成回應
            if search_results:
                # 格式化搜尋結果
                formatted_results = self._format_search_results(search_results)
                
                # 使用 LLM 生成回應
                response_prompt = f"""
                基於以下搜尋結果，為用戶查詢生成一個自然、有用的回應：
                
                用戶查詢：{query}
                增強查詢：{enhanced_query.get('rewritten_query', query)}
                
                搜尋結果：
                {formatted_results}
                
                請生成一個自然、有用的回應，包含：
                1. 直接回答用戶問題
                2. 提供相關的 Podcast 推薦
                3. 保持對話的自然性
                
                回應：
                """
                
                response_text = await self.llm_service.generate_text(response_prompt)
                if not response_text:
                    response_text = self._generate_fallback_response(query, search_results)
                
                return {
                    "content": response_text,
                    "recommendations": self._extract_recommendations(search_results),
                    "confidence": self._calculate_confidence(search_results),
                    "sources": self._extract_sources(search_results)
                }
            else:
                # 沒有搜尋結果，使用 CrewAI 代理
                return await self._use_crew_agents(query)
                
        except Exception as e:
            logger.error(f"回應生成失敗: {e}")
            return {
                "content": "抱歉，我無法找到相關的資訊。",
                "recommendations": [],
                "confidence": 0.0,
                "sources": []
            }
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化搜尋結果"""
        formatted = []
        for i, result in enumerate(results[:5], 1):  # 只使用前5個結果
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            title = metadata.get("title", f"結果 {i}")
            score = result.get("similarity_score", 0.0)
            
            formatted.append(f"{i}. {title} (相關度: {score:.2f}): {content[:200]}...")
        
        return "\n".join(formatted)
    
    def _generate_fallback_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        """生成回退回應"""
        if not results:
            return "抱歉，我無法找到相關的資訊。"
        
        # 基於搜尋結果生成簡單回應
        top_result = results[0]
        content = top_result.get("content", "")
        metadata = top_result.get("metadata", {})
        title = metadata.get("title", "相關內容")
        
        return f"根據搜尋結果，我找到了一些相關資訊：\n\n{title}：{content[:300]}..."
    
    async def _use_crew_agents(self, query: str) -> Dict[str, Any]:
        """使用 CrewAI 代理"""
        try:
            # 使用現有的 CrewAI 代理處理查詢
            if hasattr(self, 'leader_agent'):
                response = await self.leader_agent.process_query(query)
                return {
                    "content": response.content,
                    "recommendations": response.recommendations or [],
                    "confidence": response.confidence or 0.0,
                    "sources": response.sources or []
                }
            else:
                return {
                    "content": "抱歉，我無法處理您的查詢。",
                    "recommendations": [],
                    "confidence": 0.0,
                    "sources": []
                }
        except Exception as e:
            logger.error(f"CrewAI 代理處理失敗: {e}")
            return {
                "content": "抱歉，處理您的查詢時發生錯誤。",
                "recommendations": [],
                "confidence": 0.0,
                "sources": []
            }
    
    def _extract_recommendations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取推薦"""
        recommendations = []
        for result in results[:3]:  # 只取前3個推薦
            metadata = result.get("metadata", {})
            recommendations.append({
                "title": metadata.get("title", "未知標題"),
                "source": metadata.get("source", "未知來源"),
                "description": result.get("content", "")[:200],
                "confidence": result.get("similarity_score", 0.0)
            })
        return recommendations
    
    def _calculate_confidence(self, results: List[Dict[str, Any]]) -> float:
        """計算信心度"""
        if not results:
            return 0.0
        
        # 基於最高相似度分數計算信心度
        max_score = max(result.get("similarity_score", 0.0) for result in results)
        return min(max_score, 1.0)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """提取來源"""
        sources = []
        for result in results:
            metadata = result.get("metadata", {})
            source = metadata.get("source", "")
            if source and source not in sources:
                sources.append(source)
        return sources[:3]  # 只返回前3個來源
    
    async def _apply_apple_ranking(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """應用 Apple Podcast 排名"""
        try:
            if self.apple_ranking:
                # 這裡可以添加 Apple Podcast 排名邏輯
                # 暫時返回原始回應
                return response
        except Exception as e:
            logger.error(f"Apple Podcast 排名應用失敗: {e}")
        
        return response
    
    async def _synthesize_speech(self, text: str, voice: str, speed: float) -> Optional[str]:
        """語音合成"""
        try:
            # 這裡可以整合 TTS 服務
            # 暫時返回 None
            return None
        except Exception as e:
            logger.error(f"語音合成失敗: {e}")
            return None
    
    async def _log_chat_history(self, user_id: str, session_id: Optional[str], 
                               query: str, response: str):
        """記錄聊天歷史"""
        try:
            if self.chat_history:
                await self.chat_history.add_message(
                    user_id=user_id,
                    session_id=session_id,
                    query=query,
                    response=response,
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"聊天歷史記錄失敗: {e}")
    
    def _update_stats(self, start_time: datetime):
        """更新統計"""
        duration = (datetime.now() - start_time).total_seconds()
        
        # 更新平均回應時間
        total_queries = self.search_stats["total_queries"]
        current_avg = self.search_stats["average_response_time"]
        
        if total_queries > 1:
            self.search_stats["average_response_time"] = (
                (current_avg * (total_queries - 1) + duration) / total_queries
            )
        else:
            self.search_stats["average_response_time"] = duration
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        return {
            **self.search_stats,
            "enhanced_search_stats": self.enhanced_search.get_statistics(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查 LLM 服務
            llm_healthy = await self.llm_service.health_check()
            
            # 檢查增強搜尋
            search_stats = self.enhanced_search.get_statistics()
            
            return {
                "status": "healthy" if llm_healthy else "degraded",
                "components": {
                    "llm_service": llm_healthy,
                    "enhanced_search": True,
                    "crew_agents": hasattr(self, 'leader_agent'),
                    "chat_history": self.chat_history is not None,
                    "apple_ranking": self.apple_ranking is not None
                },
                "statistics": self.get_statistics(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """關閉服務"""
        try:
            await self.llm_service.close()
            await self.enhanced_search.close()
        except Exception as e:
            logger.error(f"服務關閉失敗: {e}")


# 創建全局實例
integrated_rag_service = IntegratedRAGService() 