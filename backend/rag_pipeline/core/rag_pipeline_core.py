#!/usr/bin/env python3
"""
RAG Pipeline Core

統一的 RAG Pipeline 核心類別，整合所有功能並提供 OOP 介面
遵循 Google Clean Code 原則，確保模組化設計

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from .unified_service_manager import get_service_manager, UnifiedServiceManager

logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    """查詢請求數據類別"""
    query: str
    user_id: str = "default_user"
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    enable_tts: bool = False
    voice: str = "podrina"
    speed: float = 1.0


@dataclass
class QueryResponse:
    """查詢回應數據類別"""
    user_id: str
    query: str
    response: str
    category: str
    confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning: str
    processing_time: float
    timestamp: str
    audio_data: Optional[str] = None
    voice_used: Optional[str] = None
    speed_used: Optional[float] = None
    tts_enabled: bool = False


@dataclass
class SystemInfo:
    """系統資訊數據類別"""
    version: str
    status: str
    components: Dict[str, bool]
    timestamp: str


class RAGPipelineCore:
    """RAG Pipeline 核心類別"""
    
    def __init__(self, 
                 enable_monitoring: bool = True,
                 enable_semantic_retrieval: bool = True,
                 enable_chat_history: bool = True,
                 enable_apple_ranking: bool = True,
                 confidence_threshold: float = 0.7):
        """
        初始化 RAG Pipeline 核心
        
        Args:
            enable_monitoring: 是否啟用監控
            enable_semantic_retrieval: 是否啟用語意檢索
            enable_chat_history: 是否啟用聊天歷史
            enable_apple_ranking: 是否啟用 Apple 排名
            confidence_threshold: 信心度閾值
        """
        self.service_manager = get_service_manager()
        self.agent_config = None
        
        # 功能開關
        self.enable_monitoring = enable_monitoring
        self.enable_semantic_retrieval = enable_semantic_retrieval
        self.enable_chat_history = enable_chat_history
        self.enable_apple_ranking = enable_apple_ranking
        self.confidence_threshold = confidence_threshold
        
        # 初始化狀態
        self.is_initialized = False
        self.version = "3.0.0"
        
        # 初始化代理人
        self.agents = {}
        
        logger.info("RAG Pipeline 核心初始化完成")
    
    async def initialize(self) -> bool:
        """初始化 RAG Pipeline"""
        try:
            # 初始化服務管理器
            success = await self.service_manager.initialize()
            if not success:
                raise RuntimeError("服務管理器初始化失敗")
            
            # 初始化代理人
            await self._initialize_agents()
            
            self.is_initialized = True
            logger.info("RAG Pipeline 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"RAG Pipeline 初始化失敗: {e}")
            return False
    
    async def _initialize_agents(self) -> None:
        """初始化代理人"""
        try:
            # 初始化 CrewAI 代理人
            try:
                from .crew_agents import (
                    LeaderAgent, BusinessExpertAgent, 
                    EducationExpertAgent, UserManagerAgent
                )
                
                self.agents['leader'] = LeaderAgent()
                self.agents['business'] = BusinessExpertAgent()
                self.agents['education'] = EducationExpertAgent()
                self.agents['user_manager'] = UserManagerAgent()
                
                logger.info("CrewAI 代理人初始化成功")
            except ImportError as e:
                logger.warning(f"CrewAI 代理人導入失敗: {e}")
            
            # 初始化智能檢索專家
            try:
                from .intelligent_retrieval_expert import IntelligentRetrievalExpert
                self.agents['retrieval'] = IntelligentRetrievalExpert()
                logger.info("智能檢索專家初始化成功")
            except ImportError as e:
                logger.warning(f"智能檢索專家導入失敗: {e}")
            
        except Exception as e:
            logger.error(f"代理人初始化失敗: {e}")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        處理用戶查詢
        
        Args:
            request: 查詢請求
            
        Returns:
            查詢回應
        """
        start_time = datetime.now()
        
        try:
            # 檢查初始化狀態
            if not self.is_initialized:
                raise RuntimeError("RAG Pipeline 未初始化")
            
            # 處理查詢
            response = await self._process_query_internal(request)
            
            # 計算處理時間
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 構建回應
            query_response = QueryResponse(
                user_id=request.user_id,
                query=request.query,
                response=response.get('response', ''),
                category=response.get('category', 'general'),
                confidence=response.get('confidence', 0.0),
                recommendations=response.get('recommendations', []),
                reasoning=response.get('reasoning', ''),
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                audio_data=response.get('audio_data'),
                voice_used=response.get('voice_used'),
                speed_used=response.get('speed_used'),
                tts_enabled=request.enable_tts
            )
            
            # 記錄成功查詢
            self._log_successful_query(
                request.user_id, 
                'pipeline', 
                request.query, 
                query_response.confidence
            )
            
            return query_response
            
        except Exception as e:
            # 記錄失敗查詢
            self._log_failed_query(request.user_id, request.query, str(e))
            
            # 返回錯誤回應
            return QueryResponse(
                user_id=request.user_id,
                query=request.query,
                response=f"處理查詢時發生錯誤: {str(e)}",
                category="error",
                confidence=0.0,
                recommendations=[],
                reasoning="查詢處理失敗",
                processing_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now().isoformat(),
                tts_enabled=False
            )
    
    async def _process_query_internal(self, request: QueryRequest) -> Dict[str, Any]:
        """內部查詢處理邏輯"""
        # 1. 嘗試智能檢索
        if self.enable_semantic_retrieval:
            retrieval_result = await self._process_semantic_retrieval(request.query)
            if retrieval_result and retrieval_result.get('confidence', 0) >= self.confidence_threshold:
                return retrieval_result
        
        # 2. 嘗試向量搜尋
        vector_result = await self._process_vector_search(request.query)
        if vector_result and vector_result.get('confidence', 0) >= self.confidence_threshold:
            return vector_result
        
        # 3. 嘗試 Web 搜尋
        web_result = await self._process_web_search(request.query)
        if web_result:
            return web_result
        
        # 4. 使用預設回應
        return await self._get_default_response(request.query)
    
    async def _process_semantic_retrieval(self, query: str) -> Optional[Dict[str, Any]]:
        """處理語意檢索"""
        try:
            retrieval_agent = self.agents.get('retrieval')
            if retrieval_agent and hasattr(retrieval_agent, 'process_query'):
                result = await retrieval_agent.process_query(query)
                if result and result.get('confidence', 0) >= self.confidence_threshold:
                    return result
        except Exception as e:
            logger.error(f"語意檢索失敗: {e}")
        return None
    
    async def _process_vector_search(self, query: str) -> Optional[Dict[str, Any]]:
        """處理向量搜尋"""
        try:
            vector_service = self.service_manager.get_vector_search_service()
            if vector_service:
                results = await vector_service.search(query, limit=5)
                if results:
                    # 格式化向量搜尋結果
                    formatted_response = self._format_vector_search_response(results)
                    return {
                        'response': formatted_response,
                        'category': 'vector_search',
                        'confidence': 0.8,
                        'recommendations': results[:3],
                        'reasoning': '基於向量相似度的檢索結果'
                    }
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
        return None
    
    async def _process_web_search(self, query: str) -> Optional[Dict[str, Any]]:
        """處理 Web 搜尋"""
        try:
            # 使用 Web 搜尋服務
            web_service = self.service_manager.get_service('web_search')
            if web_service and hasattr(web_service, 'search'):
                results = await web_service.search(query)
                if results:
                    formatted_response = self._format_web_search_response(results)
                    return {
                        'response': formatted_response,
                        'category': 'web_search',
                        'confidence': 0.6,
                        'recommendations': results[:3],
                        'reasoning': '基於 Web 搜尋的結果'
                    }
        except Exception as e:
            logger.error(f"Web 搜尋失敗: {e}")
        return None
    
    async def _get_default_response(self, query: str) -> Dict[str, Any]:
        """獲取預設回應"""
        try:
            # 嘗試使用預設問答處理器
            from .default_qa_processor import DefaultQAProcessor
            processor = DefaultQAProcessor()
            response = await processor.get_response(query)
            
            return {
                'response': response,
                'category': 'default',
                'confidence': 0.5,
                'recommendations': [],
                'reasoning': '使用預設問答回應'
            }
        except Exception as e:
            logger.error(f"預設回應處理失敗: {e}")
            return {
                'response': '抱歉，我無法處理您的查詢。請稍後再試。',
                'category': 'error',
                'confidence': 0.0,
                'recommendations': [],
                'reasoning': '所有處理方法都失敗了'
            }
    
    def _format_vector_search_response(self, results: List[Dict[str, Any]]) -> str:
        """格式化向量搜尋回應"""
        if not results:
            return "未找到相關內容。"
        
        response_parts = ["根據您的查詢，我找到了以下相關內容：\n"]
        
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', '無標題')
            content = result.get('content', '無內容')
            confidence = result.get('confidence', 0)
            
            response_parts.append(f"{i}. {title}")
            response_parts.append(f"   相關度: {confidence:.2f}")
            response_parts.append(f"   內容: {content[:200]}...\n")
        
        return "\n".join(response_parts)
    
    def _format_web_search_response(self, results: List[Dict[str, Any]]) -> str:
        """格式化 Web 搜尋回應"""
        if not results:
            return "未找到相關的網路資訊。"
        
        response_parts = ["根據網路搜尋，我找到了以下資訊：\n"]
        
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', '無標題')
            snippet = result.get('snippet', '無摘要')
            url = result.get('url', '')
            
            response_parts.append(f"{i}. {title}")
            response_parts.append(f"   {snippet}")
            if url:
                response_parts.append(f"   來源: {url}\n")
        
        return "\n".join(response_parts)
    
    async def get_recommendations(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """獲取推薦"""
        try:
            recommendation_service = self.service_manager.get_recommendation_service()
            if recommendation_service:
                return await recommendation_service.get_recommendations(query, user_id, limit)
        except Exception as e:
            logger.error(f"獲取推薦失敗: {e}")
        return []
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """語音合成"""
        try:
            tts_service = self.service_manager.get_tts_service()
            if tts_service:
                return await tts_service.synthesize_speech(text, voice, speed)
        except Exception as e:
            logger.error(f"語音合成失敗: {e}")
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查服務管理器
            service_health = await self.service_manager.health_check()
            
            # 檢查代理人
            agent_health = {}
            for name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'health_check'):
                        is_healthy = await agent.health_check()
                    else:
                        is_healthy = True
                    agent_health[name] = is_healthy
                except Exception as e:
                    agent_health[name] = False
            
            return {
                'status': 'healthy' if self.is_initialized else 'unhealthy',
                'version': self.version,
                'services': service_health,
                'agents': agent_health,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_info(self) -> SystemInfo:
        """獲取系統資訊"""
        service_status = self.service_manager.get_system_status()
        
        return SystemInfo(
            version=self.version,
            status='ready' if self.is_initialized else 'initializing',
            components={
                'database': service_status['services'].get('database', {}).get('is_available', False),
                'llm': service_status['services'].get('llm', {}).get('is_available', False),
                'tts': service_status['services'].get('tts', {}).get('is_available', False),
                'recommendation': service_status['services'].get('recommendation', {}).get('is_available', False),
                'vector_search': service_status['services'].get('vector_search', {}).get('is_available', False)
            },
            timestamp=datetime.now().isoformat()
        )
    
    def _log_successful_query(self, user_id: str, method: str, query: str, confidence: float) -> None:
        """記錄成功查詢"""
        if self.enable_monitoring:
            logger.info(f"成功查詢 - 用戶: {user_id}, 方法: {method}, 信心度: {confidence:.2f}")
    
    def _log_failed_query(self, user_id: str, query: str, error: str) -> None:
        """記錄失敗查詢"""
        if self.enable_monitoring:
            logger.error(f"查詢失敗 - 用戶: {user_id}, 錯誤: {error}")
    
    async def cleanup(self) -> None:
        """清理資源"""
        try:
            # 清理服務管理器
            await self.service_manager.cleanup()
            
            # 清理代理人
            for agent in self.agents.values():
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
            
            logger.info("RAG Pipeline 核心已清理")
            
        except Exception as e:
            logger.error(f"清理 RAG Pipeline 核心失敗: {e}")


# 全域 RAG Pipeline 核心實例
rag_pipeline_core = RAGPipelineCore()


def get_rag_pipeline_core() -> RAGPipelineCore:
    """獲取 RAG Pipeline 核心"""
    return rag_pipeline_core


async def initialize_rag_pipeline() -> bool:
    """初始化 RAG Pipeline"""
    return await rag_pipeline_core.initialize()


async def cleanup_rag_pipeline() -> None:
    """清理 RAG Pipeline"""
    await rag_pipeline_core.cleanup()


if __name__ == "__main__":
    # 測試 RAG Pipeline 核心
    async def test_rag_pipeline_core():
        print("RAG Pipeline 核心測試")
        print("=" * 50)
        
        # 初始化
        success = await initialize_rag_pipeline()
        print(f"初始化: {'成功' if success else '失敗'}")
        
        if success:
            # 測試查詢
            request = QueryRequest(
                query="什麼是機器學習？",
                user_id="test_user",
                enable_tts=False
            )
            
            response = await rag_pipeline_core.process_query(request)
            print(f"\n查詢測試:")
            print(f"  查詢: {response.query}")
            print(f"  回應: {response.response[:100]}...")
            print(f"  分類: {response.category}")
            print(f"  信心度: {response.confidence:.2f}")
            print(f"  處理時間: {response.processing_time:.2f}秒")
            
            # 健康檢查
            health = await rag_pipeline_core.health_check()
            print(f"\n健康檢查:")
            print(f"  狀態: {health['status']}")
            print(f"  版本: {health['version']}")
            
            # 系統資訊
            system_info = rag_pipeline_core.get_system_info()
            print(f"\n系統資訊:")
            print(f"  版本: {system_info.version}")
            print(f"  狀態: {system_info.status}")
            for component, available in system_info.components.items():
                status = "✅" if available else "❌"
                print(f"  {component}: {status}")
            
            # 清理
            await cleanup_rag_pipeline()
            print(f"\n已清理")
    
    # 執行測試
    asyncio.run(test_rag_pipeline_core()) 