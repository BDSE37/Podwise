#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 統一服務管理器

整合所有 RAG Pipeline 功能，提供統一的 OOP 介面
按照三層 CrewAI 架構組織，遵循 agent_roles_config.py 的規則

架構層次：
- 第一層：領導者層 (Leader Layer) - 決策統籌
- 第二層：類別專家層 (Category Expert Layer) - 商業/教育專家  
- 第三層：功能專家層 (Functional Expert Layer) - 專業功能處理

作者: Podwise Team
版本: 4.0.0
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入統一數據模型
from .data_models import (
    RAGResponse, UserQuery, AgentResponse, SearchResult, QueryContext,
    AgentStatus, RecommendationResult, SummaryResult, ClassificationResult,
    WebSearchResult, ProcessingMetrics, SystemHealth,
    create_rag_response, create_agent_response, create_user_query, create_processing_metrics
)

# 導入基礎代理類別
from .base_agent import BaseAgent

# 導入三層架構代理
from .crew_agents import (
    LeaderAgent, BusinessExpertAgent, EducationExpertAgent,
    UserManagerAgent, WebSearchAgent, RAGExpertAgent,
    SummaryExpertAgent, TagClassificationExpertAgent, TTSExpertAgent
)

# 導入核心服務
from .hierarchical_rag_pipeline import HierarchicalRAGPipeline
from .enhanced_vector_search import RAGVectorSearch
from .qwen_llm_manager import Qwen3LLMManager
from .content_categorizer import ContentCategorizer
from .apple_podcast_ranking import ApplePodcastRankingSystem
from .default_qa_processor import DefaultQAProcessor, create_default_qa_processor

# 導入配置和工具
try:
    from .config_utils import get_agent_roles_manager, get_prompt_templates, safe_import_config
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"配置工具模組導入失敗: {e}")
    CONFIG_AVAILABLE = False

try:
    from .config_utils import get_tools_module
    WebSearchExpert = get_tools_module('web_search_tool')
    PodcastFormatter = get_tools_module('podcast_formatter')
    EnhancedPodcastRecommender = get_tools_module('enhanced_podcast_recommender')
    TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"工具模組導入失敗: {e}")
    TOOLS_AVAILABLE = False


@dataclass
class ServiceConfig:
    """服務配置"""
    enable_monitoring: bool = True
    enable_semantic_retrieval: bool = True
    enable_chat_history: bool = True
    enable_apple_ranking: bool = True
    confidence_threshold: float = 0.7
    max_processing_time: float = 30.0
    enable_mcp_enhancement: bool = True


class UnifiedServiceManager:
    """
    Podwise RAG Pipeline 統一服務管理器
    
    整合所有功能模組，提供統一的 OOP 介面
    按照三層 CrewAI 架構組織
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        """
        初始化統一服務管理器
        
        Args:
            config: 服務配置
        """
        self.config = config or ServiceConfig()
        self.agent_roles_manager = None
        self.prompt_templates_available = False
        
        # 初始化指標
        self.metrics = create_processing_metrics()
        
        # 初始化所有組件
        self._initialize_components()
        
        logger.info("✅ UnifiedServiceManager 初始化完成")
    
    def _initialize_components(self):
        """初始化所有組件"""
        # 初始化配置
        self._initialize_config()
        
        # 初始化三層架構代理
        self._initialize_agents()
        
        # 初始化核心服務
        self._initialize_core_services()
        
        # 初始化工具
        self._initialize_tools()
        
        # 初始化 MCP 增強
        if self.config.enable_mcp_enhancement:
            self._initialize_mcp_enhancement()
    
    def _initialize_config(self):
        """初始化配置"""
        if CONFIG_AVAILABLE:
            try:
                self.agent_roles_manager = get_agent_roles_manager()
                self.prompt_templates_available = True
                logger.info("✅ 配置管理器初始化成功")
            except Exception as e:
                logger.warning(f"配置管理器初始化失敗: {e}")
                self.agent_roles_manager = None
                self.prompt_templates_available = False
        else:
            logger.warning("配置模組不可用")
    
    def _initialize_agents(self):
        """初始化三層架構代理"""
        agent_config = {
            'confidence_threshold': self.config.confidence_threshold,
            'max_processing_time': self.config.max_processing_time
        }
        
        try:
            # 第一層：領導者層
            self.leader_agent = LeaderAgent(agent_config)
            logger.info("✅ 領導者代理初始化成功")
        except Exception as e:
            logger.info(f"ℹ️ 領導者代理初始化失敗: {e}")
            self.leader_agent = None
        
        try:
            # 第二層：類別專家層
            self.business_expert = BusinessExpertAgent(agent_config)
            self.education_expert = EducationExpertAgent(agent_config)
            logger.info("✅ 類別專家代理初始化成功")
        except Exception as e:
            logger.info(f"ℹ️ 類別專家代理初始化失敗: {e}")
            self.business_expert = None
            self.education_expert = None
        
        try:
            # 第三層：功能專家層
            self.user_manager = UserManagerAgent(agent_config)
            self.web_search_agent = WebSearchAgent(agent_config)
            self.rag_expert = RAGExpertAgent(agent_config)
            self.summary_expert = SummaryExpertAgent(agent_config)
            self.tag_classification_expert = TagClassificationExpertAgent(agent_config)
            self.tts_expert = TTSExpertAgent(agent_config)
            logger.info("✅ 功能專家代理初始化成功")
        except Exception as e:
            logger.info(f"ℹ️ 功能專家代理初始化失敗: {e}")
            self.user_manager = None
            self.web_search_agent = None
            self.rag_expert = None
            self.summary_expert = None
            self.tag_classification_expert = None
            self.tts_expert = None
    
    def _initialize_core_services(self):
        """初始化核心服務"""
        try:
            self.rag_pipeline = HierarchicalRAGPipeline()
            logger.info("✅ 層級化 RAG Pipeline 初始化成功")
        except Exception as e:
            logger.warning(f"層級化 RAG Pipeline 初始化失敗: {e}")
            self.rag_pipeline = None
        
        try:
            self.vector_search = RAGVectorSearch()
            logger.info("✅ 向量搜尋初始化成功")
        except Exception as e:
            logger.warning(f"向量搜尋初始化失敗: {e}")
            self.vector_search = None
        
        try:
            self.llm_manager = Qwen3LLMManager()
            logger.info("✅ LLM 管理器初始化成功")
        except Exception as e:
            logger.warning(f"LLM 管理器初始化失敗: {e}")
            self.llm_manager = None
        
        try:
            self.categorizer = ContentCategorizer()
            logger.info("✅ 內容分類器初始化成功")
        except Exception as e:
            logger.warning(f"內容分類器初始化失敗: {e}")
            self.categorizer = None
        
        try:
            if self.config.enable_apple_ranking:
                self.apple_ranking = ApplePodcastRankingSystem()
                logger.info("✅ Apple Podcast 排名系統初始化成功")
            else:
                self.apple_ranking = None
        except Exception as e:
            logger.warning(f"Apple Podcast 排名系統初始化失敗: {e}")
            self.apple_ranking = None
        
        try:
            self.default_qa_processor = create_default_qa_processor()
            logger.info("✅ 預設問答處理器初始化成功")
        except Exception as e:
            logger.warning(f"預設問答處理器初始化失敗: {e}")
            self.default_qa_processor = None
    
    def _initialize_tools(self):
        """初始化工具"""
        if TOOLS_AVAILABLE:
            try:
                # 檢查工具模組是否正確導入
                if hasattr(WebSearchExpert, '__call__'):
                    self.web_search_tool = WebSearchExpert()
                    logger.info("✅ Web 搜尋工具初始化成功")
                else:
                    logger.info("ℹ️ Web 搜尋工具模組不可用")
                    self.web_search_tool = None
            except Exception as e:
                logger.info(f"ℹ️ Web 搜尋工具初始化失敗: {e}")
                self.web_search_tool = None
            
            try:
                if hasattr(PodcastFormatter, '__call__'):
                    self.podcast_formatter = PodcastFormatter()
                    logger.info("✅ Podcast 格式化器初始化成功")
                else:
                    logger.info("ℹ️ Podcast 格式化器模組不可用")
                    self.podcast_formatter = None
            except Exception as e:
                logger.info(f"ℹ️ Podcast 格式化器初始化失敗: {e}")
                self.podcast_formatter = None
            
            try:
                if hasattr(EnhancedPodcastRecommender, '__call__'):
                    self.enhanced_recommender = EnhancedPodcastRecommender()
                    logger.info("✅ 增強推薦器初始化成功")
                else:
                    logger.info("ℹ️ 增強推薦器模組不可用")
                    self.enhanced_recommender = None
            except Exception as e:
                logger.info(f"ℹ️ 增強推薦器初始化失敗: {e}")
                self.enhanced_recommender = None
        else:
            self.web_search_tool = None
            self.podcast_formatter = None
            self.enhanced_recommender = None
    
    def _initialize_mcp_enhancement(self):
        """初始化 MCP 增強功能"""
        try:
            # 檢查 utils 目錄是否存在
            utils_dir = os.path.join(os.path.dirname(__file__), '..', 'utils')
            if os.path.exists(utils_dir):
                # 導入 MCP 整合模組
                import sys
                if utils_dir not in sys.path:
                    sys.path.insert(0, utils_dir)
                
                try:
                    from mcp_integration import get_mcp_integration
                    self.mcp_integration = get_mcp_integration()
                    logger.info("✅ MCP 增強功能初始化成功")
                except ImportError:
                    logger.info("ℹ️ MCP 整合模組不可用")
                    self.mcp_integration = None
            else:
                logger.info("ℹ️ utils 目錄不存在，跳過 MCP 增強功能")
                self.mcp_integration = None
        except Exception as e:
            logger.info(f"ℹ️ MCP 增強功能初始化失敗: {e}")
            self.mcp_integration = None
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "Podwise0001",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢 - 主要入口點
        
        按照三層架構流程：
        1. 第一層：領導者層 - 決策統籌
        2. 第二層：類別專家層 - 商業/教育專家
        3. 第三層：功能專家層 - 專業功能處理
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        self.metrics.steps_completed.append("query_received")
        
        try:
            # 創建用戶查詢對象
            user_query = create_user_query(
                query=query,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # 步驟 1: 語意分析和標籤萃取
            semantic_analysis = await self._perform_semantic_analysis(user_query)
            self.metrics.steps_completed.append("semantic_analysis")
            
            # 步驟 2: 根據三層架構處理
            response = await self._process_with_three_layer_architecture(
                user_query, session_id, semantic_analysis
            )
            
            # 步驟 3: 更新指標
            self.metrics.end_time = datetime.now()
            self.metrics.steps_completed.append("query_completed")
            
            return response
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {e}")
            self.metrics.errors.append(str(e))
            self.metrics.end_time = datetime.now()
            
            return create_rag_response(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                error=str(e)
            )
    
    async def _perform_semantic_analysis(self, user_query: UserQuery) -> Dict[str, Any]:
        """
        執行語意分析和標籤萃取
        
        Args:
            user_query: 用戶查詢對象
            
        Returns:
            Dict[str, Any]: 語意分析結果
        """
        try:
            # 使用智能檢索專家進行語意分析
            if self.rag_expert:
                analysis_result = await self.rag_expert.process(user_query)
                return {
                    "intent": "general",
                    "keywords": user_query.query.split(),
                    "primary_category": analysis_result.metadata.get("category", "其他"),
                    "is_summary_request": "摘要" in user_query.query or "總結" in user_query.query,
                    "confidence": analysis_result.confidence,
                    "role_config": self.agent_roles_manager.get_role("intelligent_retrieval_expert") if self.agent_roles_manager else None,
                    "prompt_templates_used": self.prompt_templates_available
                }
            else:
                # 備用分析邏輯
                return self._fallback_semantic_analysis(user_query)
                
        except Exception as e:
            logger.error(f"語意分析失敗: {e}")
            return self._fallback_semantic_analysis(user_query)
    
    def _fallback_semantic_analysis(self, user_query: UserQuery) -> Dict[str, Any]:
        """備用語意分析邏輯"""
        query = user_query.query.lower()
        
        # 簡單的關鍵字分類
        business_keywords = ['投資', '理財', '股票', '創業', '職場', '科技', '經濟']
        education_keywords = ['學習', '成長', '職涯', '心理', '溝通', '語言', '親子']
        
        business_score = sum(1 for keyword in business_keywords if keyword in query)
        education_score = sum(1 for keyword in education_keywords if keyword in query)
        
        if business_score > education_score:
            primary_category = "商業"
        elif education_score > business_score:
            primary_category = "教育"
        else:
            primary_category = "其他"
        
        return {
            "intent": "general",
            "keywords": user_query.query.split(),
            "primary_category": primary_category,
            "is_summary_request": "摘要" in query or "總結" in query,
            "business_score": business_score,
            "education_score": education_score,
            "confidence": 0.6,
            "role_config": None,
            "prompt_templates_used": False
        }
    
    async def _process_with_three_layer_architecture(self, 
                                                    user_query: UserQuery,
                                                    session_id: Optional[str],
                                                    semantic_analysis: Dict[str, Any]) -> RAGResponse:
        """
        按照三層架構處理查詢
        
        Args:
            user_query: 用戶查詢對象
            session_id: 會話 ID
            semantic_analysis: 語意分析結果
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        
        try:
            # 第三層：功能專家層處理
            functional_results = await self._process_functional_layer(user_query, semantic_analysis)
            self.metrics.steps_completed.append("functional_layer")
            
            # 第二層：類別專家層處理
            category_results = await self._process_category_layer(user_query, semantic_analysis, functional_results)
            self.metrics.steps_completed.append("category_layer")
            
            # 第一層：領導者層決策
            final_response = await self._process_leader_layer(user_query, semantic_analysis, functional_results, category_results)
            self.metrics.steps_completed.append("leader_layer")
            
            return final_response
            
        except Exception as e:
            logger.error(f"三層架構處理失敗: {e}")
            return await self._fallback_processing(user_query, semantic_analysis)
    
    async def _process_functional_layer(self, 
                                       user_query: UserQuery,
                                       semantic_analysis: Dict[str, Any]) -> Dict[str, AgentResponse]:
        """處理第三層：功能專家層"""
        results = {}
        
        # 用戶管理專家
        if self.user_manager:
            try:
                results['user_management'] = await self.user_manager.process(user_query)
            except Exception as e:
                logger.warning(f"用戶管理專家處理失敗: {e}")
        
        # 標籤分類專家
        if self.tag_classification_expert:
            try:
                results['tag_classification'] = await self.tag_classification_expert.process(user_query)
            except Exception as e:
                logger.warning(f"標籤分類專家處理失敗: {e}")
        
        # RAG 專家
        if self.rag_expert:
            try:
                results['rag_retrieval'] = await self.rag_expert.process(user_query)
            except Exception as e:
                logger.warning(f"RAG 專家處理失敗: {e}")
        
        # 摘要專家（如果是摘要請求）
        if semantic_analysis.get("is_summary_request") and self.summary_expert:
            try:
                # 這裡需要準備摘要數據
                summary_data = [{"content": user_query.query}]  # 簡化處理
                results['summary'] = await self.summary_expert.process(summary_data)
            except Exception as e:
                logger.warning(f"摘要專家處理失敗: {e}")
        
        return results

    async def _process_category_layer(self, 
                                     user_query: UserQuery,
                                     semantic_analysis: Dict[str, Any],
                                     functional_results: Dict[str, AgentResponse]) -> Dict[str, AgentResponse]:
        """處理第二層：類別專家層"""
        results = {}
        primary_category = semantic_analysis.get("primary_category", "其他")
        
        # 商業專家
        if primary_category == "商業" and self.business_expert:
            try:
                results['business'] = await self.business_expert.process(user_query)
            except Exception as e:
                logger.warning(f"商業專家處理失敗: {e}")
        
        # 教育專家
        if primary_category == "教育" and self.education_expert:
            try:
                results['education'] = await self.education_expert.process(user_query)
            except Exception as e:
                logger.warning(f"教育專家處理失敗: {e}")
        
        # 如果是跨類別，兩個專家都處理
        if semantic_analysis.get("is_cross_category"):
            if self.business_expert:
                try:
                    results['business_cross'] = await self.business_expert.process(user_query)
                except Exception as e:
                    logger.warning(f"商業專家跨類別處理失敗: {e}")
            
            if self.education_expert:
                try:
                    results['education_cross'] = await self.education_expert.process(user_query)
                except Exception as e:
                    logger.warning(f"教育專家跨類別處理失敗: {e}")
        
        return results
    
    async def _process_leader_layer(self, 
                                   user_query: UserQuery,
                                   semantic_analysis: Dict[str, Any],
                                   functional_results: Dict[str, AgentResponse],
                                   category_results: Dict[str, AgentResponse]) -> RAGResponse:
        """處理第一層：領導者層決策"""
        if self.leader_agent:
            try:
                # 整合所有結果
                integrated_results = {
                    'functional': functional_results,
                    'category': category_results,
                    'semantic_analysis': semantic_analysis
                }
                
                leader_response = await self.leader_agent.process(user_query)
                
                # MCP 增強處理
                enhanced_content = await self._enhance_with_mcp(
                    leader_response.content, 
                    user_query, 
                    semantic_analysis
                )
                
                # 轉換為 RAGResponse
                return create_rag_response(
                    content=enhanced_content,
                    confidence=leader_response.confidence,
                    sources=["leader_agent", "mcp_enhancement"],
                    processing_time=leader_response.processing_time,
                    level_used="leader_layer",
                    reasoning=leader_response.reasoning,
                    metadata={
                        **leader_response.metadata,
                        "mcp_enhanced": True,
                        "original_content": leader_response.content
                    }
                )
                
            except Exception as e:
                logger.warning(f"領導者層處理失敗: {e}")
        
        # 如果領導者層失敗，使用備用處理
        return await self._fallback_processing(user_query, semantic_analysis)
    
    async def _enhance_with_mcp(self, content: str, user_query: UserQuery, semantic_analysis: Dict[str, Any]) -> str:
        """使用 MCP 增強回應內容"""
        if not self.mcp_integration:
            return content
        
        try:
            # 使用 MCP 工具增強內容
            enhanced_result = await self.mcp_integration.enhance_response(
                original_content=content,
                user_query=user_query.query,
                category=semantic_analysis.get("primary_category", "其他"),
                context=semantic_analysis
            )
            
            if enhanced_result and enhanced_result.get("success"):
                return enhanced_result.get("enhanced_content", content)
            else:
                logger.warning("MCP 增強失敗，使用原始內容")
                return content
    
        except Exception as e:
            logger.warning(f"MCP 增強處理失敗: {e}")
            return content
    
    async def _fallback_processing(self, 
                                  user_query: UserQuery,
                                  semantic_analysis: Dict[str, Any]) -> RAGResponse:
        """備用處理邏輯"""
        start_time = datetime.now()
        
        try:
            # 使用預設問答處理器
            if self.default_qa_processor:
                response = await self.default_qa_processor.process_query(
                    user_query.query, user_query.user_id
                )
                return create_rag_response(
                    content=response.content,
                    confidence=response.confidence,
                    sources=["default_qa_processor"],
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    level_used="fallback",
                    metadata={"fallback_used": True}
                )
            
            # 最終備用回應
            return create_rag_response(
                content="抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="final_fallback",
                metadata={"fallback_used": True}
            )
            
        except Exception as e:
            logger.error(f"備用處理失敗: {e}")
            return create_rag_response(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                error=str(e)
            )
    
    async def health_check(self) -> SystemHealth:
        """健康檢查"""
        try:
            components = {
                "leader_agent": self.leader_agent is not None,
                "business_expert": self.business_expert is not None,
                "education_expert": self.education_expert is not None,
                "user_manager": self.user_manager is not None,
                "web_search_agent": self.web_search_agent is not None,
                "rag_expert": self.rag_expert is not None,
                "summary_expert": self.summary_expert is not None,
                "tag_classification_expert": self.tag_classification_expert is not None,
                "tts_expert": self.tts_expert is not None,
                "rag_pipeline": self.rag_pipeline is not None,
                "vector_search": self.vector_search is not None,
                "llm_manager": self.llm_manager is not None,
                "categorizer": self.categorizer is not None,
                "apple_ranking": self.apple_ranking is not None,
                "default_qa_processor": self.default_qa_processor is not None,
                "web_search_tool": self.web_search_tool is not None,
                "podcast_formatter": self.podcast_formatter is not None,
                "enhanced_recommender": self.enhanced_recommender is not None
            }
            
            # 計算健康狀態
            healthy_components = sum(components.values())
            total_components = len(components)
            health_percentage = healthy_components / total_components if total_components > 0 else 0
            
            status = "healthy" if health_percentage >= 0.8 else "degraded" if health_percentage >= 0.5 else "unhealthy"
            
            return SystemHealth(
                status=status,
                timestamp=datetime.now(),
                components=components,
                version="4.0.0",
                uptime=0.0,  # 需要實現運行時間追蹤
                memory_usage=0.0,  # 需要實現記憶體使用追蹤
                cpu_usage=0.0,  # 需要實現 CPU 使用追蹤
                active_connections=0,  # 需要實現連接追蹤
                metadata={
                    "health_percentage": health_percentage,
                    "healthy_components": healthy_components,
                    "total_components": total_components
                }
            )
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return SystemHealth(
                status="error",
                timestamp=datetime.now(),
                components={},
                version="4.0.0",
                uptime=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                active_connections=0,
                metadata={"error": str(e)}
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "name": "Podwise RAG Pipeline - Unified Service Manager",
            "version": "4.0.0",
            "description": "三層 CrewAI 架構智能 Podcast 推薦系統",
            "architecture": {
                "layer_1": "領導者層 - 決策統籌",
                "layer_2": "類別專家層 - 商業/教育專家",
                "layer_3": "功能專家層 - 專業功能處理"
            },
            "features": {
                "semantic_retrieval": self.config.enable_semantic_retrieval,
                "chat_history": self.config.enable_chat_history,
                "apple_ranking": self.config.enable_apple_ranking,
                "monitoring": self.config.enable_monitoring,
                "mcp_enhancement": self.config.enable_mcp_enhancement
            },
            "config": {
                "confidence_threshold": self.config.confidence_threshold,
                "max_processing_time": self.config.max_processing_time
            }
        }
    
    def get_metrics(self) -> ProcessingMetrics:
        """獲取處理指標"""
        return self.metrics 