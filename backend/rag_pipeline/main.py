#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主模組

提供統一的 OOP 介面，整合所有 RAG Pipeline 功能：
- 核心 RAG Pipeline 處理邏輯
- FastAPI Web 服務
- Apple Podcast 優先推薦系統
- 層級化 CrewAI 架構
- 語意檢索（text2vec-base-chinese + TAG_info.csv）
- 提示詞模板系統
- 聊天歷史記錄
- 效能優化

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 3.0.0
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 添加當前目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入核心模組
from core.crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent, UserQuery, AgentResponse
from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline, RAGResponse
from core.apple_podcast_ranking import ApplePodcastRankingSystem
from core.integrated_core import UnifiedQueryProcessor
from core.content_categorizer import ContentCategorizer
from core.qwen_llm_manager import Qwen3LLMManager
from core.chat_history_service import get_chat_history_service
from core.mcp_integration import get_mcp_integration
from core.api_models import (
    UserQueryRequest, UserQueryResponse, UserValidationRequest, UserValidationResponse,
    ErrorResponse, SystemInfoResponse, HealthCheckResponse
)

# 導入配置
from config.prompt_templates import PodwisePromptTemplates
from config.integrated_config import get_config

# 導入工具
from core.enhanced_vector_search import RAGVectorSearch, RAGSearchConfig
from core.web_search_tool import WebSearchTool
from core.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult
from core.default_qa_processor import DefaultQAProcessor, create_default_qa_processor

# 使用相對路徑引用共用工具
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    """應用程式配置數據類別"""
    title: str = "Podwise RAG Pipeline"
    description: str = "提供 REST API 介面的智能 Podcast 推薦系統"
    version: str = "3.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass(frozen=True)
class SystemStatus:
    """系統狀態數據類別"""
    is_ready: bool
    components: Dict[str, bool]
    timestamp: str
    version: str


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
        
        # 初始化三層式回覆機制組件
        self.default_qa_processor = create_default_qa_processor()
        self.vector_search = RAGVectorSearch()
        self.web_search_tool = WebSearchTool()
        
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
    
    async def _check_default_qa(self, query: str) -> Optional[RAGResponse]:
        """
        檢查預設問答
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[RAGResponse]: 如果找到匹配的預設問答則返回回應，否則返回 None
        """
        try:
            # 使用預設問答處理器尋找最佳匹配
            match_result = self.default_qa_processor.find_best_match(
                user_query=query,
                confidence_threshold=0.6  # 預設問答的閾值
            )
            
            if match_result:
                qa, confidence = match_result
                return RAGResponse(
                    content=qa.answer,
                    confidence=confidence,
                    sources=["default_qa"],
                    processing_time=0.0,
                    level_used="default_qa",
                    metadata={
                        "category": qa.category,
                        "tags": qa.tags,
                        "source": "default_qa"
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"檢查預設問答時發生錯誤: {e}")
            return None
    
    async def _process_vector_search(self, query: str) -> Optional[RAGResponse]:
        """
        處理向量搜尋
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[RAGResponse]: 向量搜尋結果
        """
        try:
            # 使用向量搜尋
            search_results = await self.vector_search.search(query)
            
            if not search_results:
                return None
            
            # 計算平均信心度
            avg_confidence = sum(result.confidence for result in search_results) / len(search_results)
            
            # 格式化回應
            content = self._format_vector_search_response(search_results)
            
            return RAGResponse(
                content=content,
                confidence=avg_confidence,
                sources=["vector_search"],
                processing_time=0.0,
                level_used="vector_search",
                metadata={
                    "results_count": len(search_results),
                    "source": "vector_search"
                }
            )
            
        except Exception as e:
            logger.error(f"向量搜尋處理時發生錯誤: {e}")
            return None
    
    async def _process_web_search(self, query: str) -> RAGResponse:
        """
        處理 Web 搜尋
        
        Args:
            query: 用戶查詢
            
        Returns:
            RAGResponse: Web 搜尋結果
        """
        try:
            # 使用 Web 搜尋工具
            web_results = await self.web_search_tool.search_with_openai(query)
            
            if web_results.get("success") and web_results.get("results"):
                content = self._format_web_search_response(web_results["results"])
            else:
                content = "抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。"
            
            return RAGResponse(
                content=content,
                confidence=0.3,  # Web 搜尋的信心度較低
                sources=["web_search"],
                processing_time=0.0,
                level_used="web_search",
                metadata={
                    "source": "web_search",
                    "results_count": len(web_results.get("results", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Web 搜尋處理時發生錯誤: {e}")
            return RAGResponse(
                content="抱歉，搜尋服務暫時無法使用。請稍後再試。",
                confidence=0.0,
                sources=["error"],
                processing_time=0.0,
                level_used="error",
                metadata={"error": str(e)}
            )
    
    def _format_vector_search_response(self, search_results: List) -> str:
        """格式化向量搜尋回應"""
        if not search_results:
            return "抱歉，我無法找到相關的 Podcast 推薦。"
        
        response_parts = ["根據您的查詢，我為您推薦以下 Podcast：\n"]
        
        for i, result in enumerate(search_results[:3], 1):  # 最多顯示3個
            response_parts.append(f"{i}. {result.content}")
        
        response_parts.append("\n希望這些推薦對您有幫助！")
        
        return "\n".join(response_parts)
    
    def _format_web_search_response(self, web_results: List[Dict[str, Any]]) -> str:
        """格式化 Web 搜尋回應"""
        if not web_results:
            return "抱歉，我無法找到相關的資訊。"
        
        response_parts = ["根據網路搜尋結果，我為您提供以下資訊：\n"]
        
        for i, result in enumerate(web_results[:2], 1):  # 最多顯示2個
            title = result.get("title", "未知標題")
            content = result.get("content", "無內容")
            response_parts.append(f"{i}. {title}")
            response_parts.append(f"   {content}")
        
        response_parts.append("\n這些資訊可能對您有幫助。")
        
        return "\n".join(response_parts)
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "default_user",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢（三層式 RAG 功能）
        
        三層式回覆機制：
        1. 信心值 > 0.7：使用向量搜尋結果
        2. 信心值 < 0.7：使用 web_search 作為 fallback
        3. 檢查預設問答：如果符合預設問答則直接回傳
        
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
            # 第一層：向量搜尋
            vector_result = await self._process_vector_search(query)
            if vector_result and vector_result.confidence >= self.confidence_threshold:
                logger.info(f"✅ 使用向量搜尋回覆 (信心度: {vector_result.confidence:.2f})")
                return vector_result
            
            # 第二層：Web 搜尋 fallback
            logger.info("🔄 使用 Web 搜尋作為 fallback")
            web_result = await self._process_web_search(query)
            
            # 第三層：檢查預設問答（如果前兩層都失敗）
            default_qa_result = await self._check_default_qa(query)
            if default_qa_result:
                logger.info("✅ 使用預設問答回覆")
                return default_qa_result
            
            # 如果都沒有找到合適的回應，返回 web 搜尋結果
            return web_result
            
        except Exception as e:
            logger.error(f"處理查詢時發生錯誤: {e}")
            
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
                
                # 應用排名算法
                ranked_recommendations = await self.apple_ranking.rank_podcasts(
                    query=query,
                    podcast_ratings=podcast_ratings
                )
                
                # 更新回應的推薦結果
                response.metadata['recommendations'] = ranked_recommendations
                response.metadata['apple_ranking_applied'] = True
                
                logger.info(f"Apple Podcast 排名應用完成，排名了 {len(ranked_recommendations)} 個 Podcast")
            
            return response
            
        except Exception as e:
            logger.error(f"應用 Apple Podcast 排名失敗: {e}")
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
            AgentResponse: 代理回應
        """
        try:
            # 使用 Leader Agent 處理
            response = await self.leader_agent.execute_with_monitoring(query)
            return response
            
        except Exception as e:
            logger.error(f"代理處理失敗: {e}")
            return AgentResponse(
                content=f"代理處理失敗: {str(e)}",
                confidence=0.0,
                reasoning=str(e),
                agent_name="leader_agent"
            )
    
    async def get_enhanced_recommendations(self, 
                                         query: str, 
                                         user_id: str = "default_user") -> Dict[str, Any]:
        """
        獲取增強推薦結果
        
        Args:
            query: 查詢內容
            user_id: 用戶 ID
            
        Returns:
            Dict[str, Any]: 推薦結果
        """
        try:
            # 使用向量搜尋
            vector_search = RAGVectorSearch()
            search_results = await vector_search.search(query)
            
            # 格式化推薦結果
            formatter = PodcastFormatter()
            recommendations = []
            
            for result in search_results:
                formatted = formatter.format_podcast_recommendation(
                    title=result.metadata.get('title', '未知標題'),
                    description=result.content,
                    category=result.metadata.get('category', '一般'),
                    tags=result.tags_used,
                    confidence=result.confidence,
                    source=result.source
                )
                recommendations.append(formatted)
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total_count": len(recommendations),
                "query": query,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"獲取增強推薦失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    def get_semantic_config(self) -> Optional[Dict[str, Any]]:
        """獲取語意檢索配置"""
        return {
            "enable_semantic_retrieval": self.enable_semantic_retrieval,
            "confidence_threshold": self.confidence_threshold,
            "model": "text2vec-base-chinese"
        }
    
    def get_prompt_templates(self) -> Dict[str, str]:
        """獲取提示詞模板"""
        return self.prompt_templates.get_all_templates()
    
    def is_monitoring_enabled(self) -> bool:
        """檢查是否啟用監控"""
        return self.enable_monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查核心組件
            components_status = {
                "llm_manager": self.llm_manager is not None,
                "categorizer": self.categorizer is not None,
                "chat_history": self.chat_history is not None,
                "apple_ranking": self.apple_ranking is not None,
                "rag_pipeline": self.rag_pipeline is not None,
                "integrated_core": self.integrated_core is not None
            }
            
            # 檢查代理狀態
            agents_status = {
                "user_manager": self.user_manager.is_available(),
                "business_expert": self.business_expert.is_available(),
                "education_expert": self.education_expert.is_available(),
                "leader_agent": self.leader_agent.is_available()
            }
            
            return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
                "version": "3.0.0",
                "components": components_status,
                "agents": agents_status,
                "monitoring_enabled": self.enable_monitoring
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "name": "Podwise RAG Pipeline",
            "version": "3.0.0",
            "description": "智能 Podcast 推薦系統",
            "features": {
                "semantic_retrieval": self.enable_semantic_retrieval,
                "chat_history": self.enable_chat_history,
                "apple_ranking": self.enable_apple_ranking,
                "monitoring": self.enable_monitoring
            },
            "config": {
                "confidence_threshold": self.confidence_threshold,
                "max_processing_time": 30.0
            }
        }


class RAGPipelineService:
    """RAG Pipeline 服務管理器 - 整合 Web API 功能"""
    
    def __init__(self):
        """初始化服務管理器"""
        self.app_config = AppConfig()
        
        # 核心 RAG Pipeline
        self.rag_pipeline: Optional[PodwiseRAGPipeline] = None
        
        # Web API 專用組件
        self.vector_search_tool: Optional[RAGVectorSearch] = None
        self.web_search_tool: Optional[WebSearchTool] = None
        self.podcast_formatter: Optional[PodcastFormatter] = None
        
        # 系統狀態
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """初始化所有核心組件"""
        try:
            logger.info("🚀 初始化 Podwise RAG Pipeline 服務...")
            
            # 初始化核心 RAG Pipeline
            self.rag_pipeline = get_rag_pipeline()
            logger.info("✅ 核心 RAG Pipeline 初始化完成")
            
            # 初始化向量搜尋工具
            self.vector_search_tool = RAGVectorSearch()
            logger.info("✅ 向量搜尋工具初始化完成")
            
            # 初始化 Web Search 工具
            self.web_search_tool = WebSearchTool()
            if self.web_search_tool.is_configured():
                logger.info("✅ Web Search 工具初始化完成")
            else:
                logger.warning("⚠️ Web Search 工具初始化完成 (未配置)")
            
            # 初始化 Podcast 格式化工具
            self.podcast_formatter = PodcastFormatter()
            logger.info("✅ Podcast 格式化工具初始化完成")
            
            self._is_initialized = True
            logger.info("✅ 所有核心組件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {str(e)}")
            raise
    
    def get_system_status(self) -> SystemStatus:
        """獲取系統狀態"""
        return SystemStatus(
            is_ready=self._is_initialized,
            components={
                "rag_pipeline": self.rag_pipeline is not None,
                "vector_search_tool": self.vector_search_tool is not None,
                "web_search_tool": self.web_search_tool is not None and self.web_search_tool.is_configured(),
                "podcast_formatter": self.podcast_formatter is not None
            },
            timestamp=datetime.now().isoformat(),
            version="3.0.0"
        )
    
    def is_ready(self) -> bool:
        """檢查系統是否準備就緒"""
        return self._is_initialized


# 創建服務管理器實例
service_manager = RAGPipelineService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理器"""
    # 啟動時初始化
    await service_manager.initialize()
    yield
    # 關閉時清理
    logger.info("應用程式關閉，清理資源...")


# 創建 FastAPI 應用
app = FastAPI(
    title=service_manager.app_config.title,
    description=service_manager.app_config.description,
    version=service_manager.app_config.version,
    docs_url=service_manager.app_config.docs_url,
    redoc_url=service_manager.app_config.redoc_url,
    lifespan=lifespan
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 依賴注入
def get_service_manager() -> RAGPipelineService:
    """獲取服務管理器"""
    return service_manager


def validate_system_ready(manager: RAGPipelineService = Depends(get_service_manager)) -> None:
    """驗證系統是否準備就緒"""
    if not manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="系統尚未準備就緒，請稍後再試"
        )


# API 路由
@app.get("/")
async def root() -> Dict[str, Any]:
    """根路徑"""
    return {
        "message": "Podwise RAG Pipeline API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(manager: RAGPipelineService = Depends(get_service_manager)) -> HealthCheckResponse:
    """健康檢查端點"""
    if not manager.rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
    
    health_data = await manager.rag_pipeline.health_check()
    
    return HealthCheckResponse(
        status=health_data["status"],
        timestamp=health_data["timestamp"],
        version=health_data["version"],
        components=health_data.get("components", {}),
        agents=health_data.get("agents", {})
    )


@app.post("/api/v1/validate-user", response_model=UserValidationResponse)
async def validate_user(
    request: UserValidationRequest,
    manager: RAGPipelineService = Depends(get_service_manager),
    _: None = Depends(validate_system_ready)
) -> UserValidationResponse:
    """驗證用戶"""
    try:
        # 簡單的用戶驗證邏輯
        is_valid = len(request.user_id) > 0 and request.user_id != "invalid"
        
        return UserValidationResponse(
            user_id=request.user_id,
            is_valid=is_valid,
            message="用戶驗證成功" if is_valid else "用戶驗證失敗"
        )
        
    except Exception as e:
        logger.error(f"用戶驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"用戶驗證失敗: {str(e)}")


@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(
    request: UserQueryRequest,
    background_tasks: BackgroundTasks,
    manager: RAGPipelineService = Depends(get_service_manager),
    _: None = Depends(validate_system_ready)
) -> UserQueryResponse:
    """處理用戶查詢"""
    try:
        # 使用核心 RAG Pipeline 處理查詢
        response = await manager.rag_pipeline.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        # 獲取推薦結果
        recommendations = await _get_recommendations(request.query, manager)
        
        # 背景任務：記錄查詢歷史
        background_tasks.add_task(
            _log_query_history,
            request.user_id,
            request.session_id,
            request.query,
            response.content,
            response.confidence
        )
        
        return UserQueryResponse(
            query=request.query,
            response=response.content,
            confidence=response.confidence,
            recommendations=recommendations,
            processing_time=response.processing_time,
            level_used=response.level_used,
            sources_count=len(response.sources),
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"處理查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理查詢失敗: {str(e)}")


async def _get_recommendations(query: str, manager: RAGPipelineService) -> List[Dict[str, Any]]:
    """獲取推薦結果"""
    try:
        # 使用增強推薦功能
        enhanced_results = await manager.rag_pipeline.get_enhanced_recommendations(
            query=query,
            user_id="default_user"
        )
        
        if enhanced_results.get("success"):
            return enhanced_results.get("recommendations", [])
        else:
            # 備用：使用向量搜尋
            if manager.vector_search_tool:
                search_results = await manager.vector_search_tool.search(query)
                recommendations = []
                
                for result in search_results:
                    recommendations.append({
                        "title": result.metadata.get("title", "未知標題"),
                        "description": result.content,
                        "category": result.metadata.get("category", "一般"),
                        "confidence": result.confidence,
                        "source": result.source
                    })
                
                return recommendations
        
        return []
        
    except Exception as e:
        logger.error(f"獲取推薦失敗: {e}")
        return []


async def _log_query_history(
    user_id: str,
    session_id: Optional[str],
    query: str,
    response: str,
    confidence: float
) -> None:
    """記錄查詢歷史"""
    try:
        if service_manager.rag_pipeline and service_manager.rag_pipeline.chat_history:
            service_manager.rag_pipeline.chat_history.save_chat_message(
                user_id=user_id,
                session_id=session_id or f"session_{user_id}_{int(datetime.now().timestamp())}",
                role="user",
                content=query,
                chat_mode="api",
                metadata={"confidence": confidence}
            )
            
            service_manager.rag_pipeline.chat_history.save_chat_message(
                user_id=user_id,
                session_id=session_id or f"session_{user_id}_{int(datetime.now().timestamp())}",
                role="assistant",
                content=response,
                chat_mode="api",
                metadata={"confidence": confidence}
            )
    except Exception as e:
        logger.warning(f"記錄查詢歷史失敗: {e}")


@app.get("/api/v1/system-info", response_model=SystemInfoResponse)
async def get_system_info(manager: RAGPipelineService = Depends(get_service_manager)) -> SystemInfoResponse:
    """獲取系統資訊"""
    try:
        if not manager.rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
        
        system_info = manager.rag_pipeline.get_system_info()
        
        return SystemInfoResponse(
            name=system_info["name"],
            version=system_info["version"],
            description=system_info["description"],
            features=system_info["features"],
            config=system_info["config"]
        )
        
    except Exception as e:
        logger.error(f"獲取系統資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取系統資訊失敗: {str(e)}")


# 異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """全域異常處理器"""
    logger.error(f"全域異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部伺服器錯誤",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


# 工廠函數
def get_rag_pipeline() -> PodwiseRAGPipeline:
    """獲取 RAG Pipeline 實例"""
    return PodwiseRAGPipeline()


# 主函數
async def main():
    """主函數 - 用於直接運行"""
    import uvicorn
    
    logger.info("🚀 啟動 Podwise RAG Pipeline 服務...")
    
    # 初始化服務
    await service_manager.initialize()
    
    # 啟動 FastAPI 服務
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    asyncio.run(main()) 