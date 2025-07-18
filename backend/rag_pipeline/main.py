#!/usr/bin/env python3
"""
Podwise RAG Pipeline 統一服務

整合所有 RAG Pipeline 功能模組的統一 OOP 介面
提供完整的智能 Podcast 推薦和問答服務

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

# 設定路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path = [current_dir, backend_root] + sys.path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 導入所有核心模組
try:
    # 核心服務
    from core.integrated_core import IntegratedCore
    from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
    from core.enhanced_vector_search import RAGVectorSearch
    from core.crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent
    from core.apple_podcast_ranking import ApplePodcastRankingSystem
    from core.content_categorizer import ContentCategorizer
    from core.qwen_llm_manager import Qwen3LLMManager
    from core.chat_history_service import ChatHistoryService
    from core.default_qa_processor import DefaultQAProcessor, create_default_qa_processor
    from core.enhanced_podcast_recommender import MCPEnhancedPodcastRecommender
    
    # 配置
    from config.integrated_config import get_config, PodwiseIntegratedConfig
    from config.prompt_templates import PodwisePromptTemplates
    
    # 工具
    from tools.web_search_tool import WebSearchExpert
    from tools.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult
    from tools.enhanced_podcast_recommender import EnhancedPodcastRecommender
    
    # TTS 服務
    from tts.config.voice_config import VoiceConfig
    from tts.core.tts_service import TTSService
    
    # API 模型
    from core.api_models import (
        UserQueryRequest, UserQueryResponse, UserValidationRequest, UserValidationResponse,
        TTSRequest, TTSResponse, ErrorResponse, SystemInfoResponse, HealthCheckResponse,
        AgentResponse, UserQuery, RAGResponse
    )
    
    ALL_MODULES_AVAILABLE = True
    logger.info("✅ 所有核心模組導入成功")
    
except ImportError as e:
    logger.warning(f"⚠️ 部分模組導入失敗: {e}")
    ALL_MODULES_AVAILABLE = False
    # 創建虛擬類別避免錯誤
    class DummyClass:
        def __init__(self, *args, **kwargs): pass
        async def __call__(self, *args, **kwargs): return None
    
    IntegratedCore = HierarchicalRAGPipeline = RAGVectorSearch = DummyClass
    LeaderAgent = BusinessExpertAgent = EducationExpertAgent = UserManagerAgent = DummyClass
    ApplePodcastRankingSystem = ContentCategorizer = Qwen3LLMManager = DummyClass
    ChatHistoryService = DefaultQAProcessor = MCPEnhancedPodcastRecommender = DummyClass
    WebSearchExpert = PodcastFormatter = EnhancedPodcastRecommender = DummyClass
    VoiceConfig = TTSService = DummyClass
    
    # 虛擬 API 模型
    class UserQueryRequest(BaseModel):
        query: str = Field(..., description="用戶查詢內容")
        user_id: str = Field(default="default_user", description="用戶ID")
        session_id: Optional[str] = Field(None, description="會話ID")
        metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外元數據")
        enable_tts: bool = Field(default=True, description="是否啟用TTS")
        voice: str = Field(default="podrina", description="語音模型")
        speed: float = Field(default=1.0, description="語音速度")
    
    class UserQueryResponse(BaseModel):
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
        tts_enabled: bool = True
    
    class TTSRequest(BaseModel):
        text: str = Field(..., description="要合成的文字")
        voice: str = Field(default="podrina", description="語音模型")
        speed: float = Field(default=1.0, description="語音速度")
    
    class TTSResponse(BaseModel):
        success: bool
        audio_data: Optional[str] = None
        voice: Optional[str] = None
        speed: Optional[float] = None
        text: Optional[str] = None
        processing_time: float
        message: str = ""
    
    class UserValidationRequest(BaseModel):
        user_id: str = Field(..., description="用戶ID")
    
    class UserValidationResponse(BaseModel):
        user_id: str
        is_valid: bool
        has_history: bool
        preferred_category: Optional[str] = None
        message: str
    
    class ErrorResponse(BaseModel):
        error: str
        detail: str
        timestamp: str
    
    class SystemInfoResponse(BaseModel):
        name: str
        version: str
        description: str
        features: Dict[str, Any]
        config: Dict[str, Any]
    
    class HealthCheckResponse(BaseModel):
        status: str
        timestamp: str
        components: Dict[str, bool]
    
    class AgentResponse(BaseModel):
        content: str
        confidence: float
        reasoning: str
        agent_name: str
    
    class RAGResponse(BaseModel):
        content: str
        confidence: float
        sources: List[str]
        processing_time: float
        level_used: str
        metadata: Dict[str, Any]


@dataclass
class PodwiseRAGPipeline:
    """
    Podwise RAG Pipeline 統一服務類別
    
    整合所有 RAG Pipeline 功能模組，提供統一的 OOP 介面
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
        
        # 初始化配置
        self.config = get_config() if 'get_config' in globals() else {}
        self.prompt_templates = PodwisePromptTemplates() if 'PodwisePromptTemplates' in globals() else None
        
        # 初始化核心組件
        self._initialize_core_components()
        
        # 初始化代理
        self._initialize_agents()
        
        # 初始化工具
        self._initialize_tools()
        
        # 初始化 TTS 服務
        self._initialize_tts()
        
        logger.info("✅ Podwise RAG Pipeline 初始化完成")
    
    def _initialize_core_components(self):
        """初始化核心組件"""
        try:
            # 層級化 RAG Pipeline
            self.rag_pipeline = HierarchicalRAGPipeline()
            logger.info("✅ 層級化 RAG Pipeline 初始化成功")
        except Exception as e:
            logger.warning(f"層級化 RAG Pipeline 初始化失敗: {e}")
            self.rag_pipeline = None
        
        try:
            # 向量搜尋
            self.vector_search = RAGVectorSearch()
            logger.info("✅ 向量搜尋初始化成功")
        except Exception as e:
            logger.warning(f"向量搜尋初始化失敗: {e}")
            self.vector_search = None
        
        try:
            # LLM 管理器
            self.llm_manager = Qwen3LLMManager()
            logger.info("✅ LLM 管理器初始化成功")
        except Exception as e:
            logger.warning(f"LLM 管理器初始化失敗: {e}")
            self.llm_manager = None
        
        try:
            # 內容分類器
            self.categorizer = ContentCategorizer()
            logger.info("✅ 內容分類器初始化成功")
        except Exception as e:
            logger.warning(f"內容分類器初始化失敗: {e}")
            self.categorizer = None
        
        try:
            # 聊天歷史服務
            if self.enable_chat_history:
                self.chat_history = ChatHistoryService()
                logger.info("✅ 聊天歷史服務初始化成功")
            else:
                self.chat_history = None
        except Exception as e:
            logger.warning(f"聊天歷史服務初始化失敗: {e}")
            self.chat_history = None
        
        try:
            # Apple Podcast 排名系統
            if self.enable_apple_ranking:
                self.apple_ranking = ApplePodcastRankingSystem()
                logger.info("✅ Apple Podcast 排名系統初始化成功")
            else:
                self.apple_ranking = None
        except Exception as e:
            logger.warning(f"Apple Podcast 排名系統初始化失敗: {e}")
            self.apple_ranking = None
        
        try:
            # 預設問答處理器
            self.default_qa_processor = create_default_qa_processor()
            logger.info("✅ 預設問答處理器初始化成功")
        except Exception as e:
            logger.warning(f"預設問答處理器初始化失敗: {e}")
            self.default_qa_processor = None
        
        try:
            # 增強推薦器
            self.enhanced_recommender = MCPEnhancedPodcastRecommender()
            logger.info("✅ 增強推薦器初始化成功")
        except Exception as e:
            logger.warning(f"增強推薦器初始化失敗: {e}")
            self.enhanced_recommender = None
    
    def _initialize_agents(self):
        """初始化 CrewAI 代理"""
        try:
            config = {
                'confidence_threshold': self.confidence_threshold,
                'max_processing_time': 30.0
            }
            
            self.user_manager = UserManagerAgent(config)
            self.business_expert = BusinessExpertAgent(config)
            self.education_expert = EducationExpertAgent(config)
            self.leader_agent = LeaderAgent(config)
            
            logger.info("✅ CrewAI 代理初始化完成")
        except Exception as e:
            logger.warning(f"CrewAI 代理初始化失敗: {e}")
            self.user_manager = self.business_expert = self.education_expert = self.leader_agent = None
    
    def _initialize_tools(self):
        """初始化工具"""
        try:
            # Web 搜尋工具
            self.web_search_tool = WebSearchExpert()
            logger.info("✅ Web 搜尋工具初始化成功")
        except Exception as e:
            logger.warning(f"Web 搜尋工具初始化失敗: {e}")
            self.web_search_tool = None
        
        try:
            # Podcast 格式化器
            self.podcast_formatter = PodcastFormatter()
            logger.info("✅ Podcast 格式化器初始化成功")
        except Exception as e:
            logger.warning(f"Podcast 格式化器初始化失敗: {e}")
            self.podcast_formatter = None
        
        try:
            # 增強推薦工具
            self.enhanced_recommender_tool = EnhancedPodcastRecommender()
            logger.info("✅ 增強推薦工具初始化成功")
        except Exception as e:
            logger.warning(f"增強推薦工具初始化失敗: {e}")
            self.enhanced_recommender_tool = None
    
    def _initialize_tts(self):
        """初始化 TTS 服務"""
        try:
            self.tts_service = TTSService()
            logger.info("✅ TTS 服務初始化成功")
        except Exception as e:
            logger.warning(f"TTS 服務初始化失敗: {e}")
            self.tts_service = None
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "default_user",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        
        try:
            # 記錄用戶查詢
            if self.chat_history:
                self.chat_history.save_chat_message(
                    user_id=user_id,
                    session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                    role="user",
                    content=query,
                    chat_mode="rag",
                    metadata=metadata or {}
                )
            
            # 使用層級化 RAG Pipeline 處理
            if self.rag_pipeline:
                response = await self.rag_pipeline.process_query(query, user_id, session_id, metadata)
            else:
                # 備用處理方式
                response = await self._fallback_process_query(query, user_id, session_id, metadata)
            
            # 記錄回應
            if self.chat_history:
                self.chat_history.save_chat_message(
                    user_id=user_id,
                    session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                    role="assistant",
                    content=response.content,
                    chat_mode="rag",
                    metadata={"confidence": response.confidence}
                )
            
            return response
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {e}")
            return RAGResponse(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                metadata={"error": str(e)}
            )
    
    async def _fallback_process_query(self, query: str, user_id: str, session_id: Optional[str], metadata: Optional[Dict[str, Any]]) -> RAGResponse:
        """備用查詢處理方式"""
        start_time = datetime.now()
        
        # 檢查預設問答
        if self.default_qa_processor:
            match_result = self.default_qa_processor.find_best_match(query, 0.6)
            if match_result:
                qa, confidence = match_result
                return RAGResponse(
                    content=qa.answer,
                    confidence=confidence,
                    sources=["default_qa"],
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    level_used="default_qa",
                    metadata={"category": qa.category, "tags": qa.tags}
                )
        
        # 使用向量搜尋
        if self.vector_search:
            search_results = await self.vector_search.search(query)
            if search_results:
                avg_confidence = sum(result.confidence for result in search_results) / len(search_results)
                if avg_confidence >= self.confidence_threshold:
                    content = self._format_search_results(search_results)
                    return RAGResponse(
                        content=content,
                        confidence=avg_confidence,
                        sources=["vector_search"],
                        processing_time=(datetime.now() - start_time).total_seconds(),
                        level_used="vector_search",
                        metadata={"results_count": len(search_results)}
                    )
        
        # 使用 Web 搜尋
        if self.web_search_tool:
            web_results = await self.web_search_tool.search_with_openai(query)
            if web_results.get("success") and web_results.get("results"):
                content = self._format_web_results(web_results["results"])
                return RAGResponse(
                    content=content,
                    confidence=0.7,
                    sources=["web_search"],
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    level_used="web_search",
                    metadata={"results_count": len(web_results.get("results", []))}
                )
        
        # 預設回應
        return RAGResponse(
            content="抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。",
            confidence=0.0,
            sources=[],
            processing_time=(datetime.now() - start_time).total_seconds(),
            level_used="fallback",
            metadata={}
        )
    
    def _format_search_results(self, search_results: List) -> str:
        """格式化搜尋結果"""
        if not search_results:
            return "抱歉，我無法找到相關的 Podcast 推薦。"
        
        responses = []
        for i, result in enumerate(search_results[:3], 1):
            content = result.content
            if hasattr(result, 'episode_title') and result.episode_title:
                content = f"{result.episode_title}: {content}"
            responses.append(content)
        
        return "\n".join(responses)
    
    def _format_web_results(self, web_results: List[Dict[str, Any]]) -> str:
        """格式化 Web 搜尋結果"""
        if not web_results:
            return "抱歉，我無法找到相關的資訊。"
        
        responses = []
        for result in web_results[:2]:
            title = result.get("title", "")
            content = result.get("content", "")
            
            if content and len(content) > 30:
                if len(content) > 200:
                    content = content[:200] + "..."
                
                if title and title != "未知標題":
                    responses.append(f"{title}：{content}")
                else:
                    responses.append(content)
        
        return " ".join(responses) if responses else "抱歉，我無法找到相關的資訊。"
    
    async def get_recommendations(self, query: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """獲取推薦結果"""
        try:
            if self.enhanced_recommender:
                results = await self.enhanced_recommender.get_recommendations(query, user_id)
                return results
            elif self.vector_search:
                search_results = await self.vector_search.search(query)
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
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """語音合成"""
        if not self.tts_service:
            return None
        
        try:
            # 轉換語速參數
            if speed != 1.0:
                rate = f"{int((speed - 1) * 100):+d}%"
            else:
                rate = "+0%"
            
            # 執行語音合成
            audio_data = await self.tts_service.synthesize_speech(
                text=text,
                voice_id=voice,
                rate=rate,
                volume="+0%",
                pitch="+0%"
            )
            
            if audio_data:
                import base64
                return {
                    "success": True,
                    "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                    "text": text,
                    "voice": voice,
                    "speed": speed,
                    "audio_size": len(audio_data)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"語音合成錯誤: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            components_status = {
                "rag_pipeline": self.rag_pipeline is not None,
                "vector_search": self.vector_search is not None,
                "llm_manager": self.llm_manager is not None,
                "categorizer": self.categorizer is not None,
                "chat_history": self.chat_history is not None,
                "apple_ranking": self.apple_ranking is not None,
                "default_qa_processor": self.default_qa_processor is not None,
                "enhanced_recommender": self.enhanced_recommender is not None,
                "web_search_tool": self.web_search_tool is not None,
                "podcast_formatter": self.podcast_formatter is not None,
                "tts_service": self.tts_service is not None
            }
            
            agents_status = {
                "user_manager": self.user_manager is not None,
                "business_expert": self.business_expert is not None,
                "education_expert": self.education_expert is not None,
                "leader_agent": self.leader_agent is not None
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
                "monitoring": self.enable_monitoring,
                "tts_available": self.tts_service is not None
            },
            "config": {
                "confidence_threshold": self.confidence_threshold,
                "max_processing_time": 30.0
            }
        }


# FastAPI 應用
app = FastAPI(
    title="Podwise RAG Pipeline",
    description="提供 REST API 介面的智能 Podcast 推薦系統",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 RAG Pipeline 實例
rag_pipeline: Optional[PodwiseRAGPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理器"""
    global rag_pipeline
    
    # 啟動時初始化
    logger.info("🚀 初始化 Podwise RAG Pipeline...")
    rag_pipeline = PodwiseRAGPipeline()
    logger.info("✅ Podwise RAG Pipeline 初始化完成")
    
    yield
    
    # 關閉時清理
    logger.info("應用程式關閉，清理資源...")


# 依賴注入
def get_rag_pipeline() -> PodwiseRAGPipeline:
    """獲取 RAG Pipeline 實例"""
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
    return rag_pipeline


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


@app.get("/health")
async def health_check(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)):
    """健康檢查端點"""
    return await pipeline.health_check()


@app.post("/api/v1/validate-user")
async def validate_user(
    request: UserValidationRequest,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
):
    """驗證用戶"""
    try:
        # 簡單的用戶驗證邏輯
        is_valid = len(request.user_id) > 0 and request.user_id != "invalid"
        
        return UserValidationResponse(
            user_id=request.user_id,
            is_valid=is_valid,
            has_history=False,
            preferred_category=None,
            message="用戶驗證成功" if is_valid else "用戶驗證失敗"
        )
        
    except Exception as e:
        logger.error(f"用戶驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"用戶驗證失敗: {str(e)}")


@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(
    request: UserQueryRequest,
    background_tasks: BackgroundTasks,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
) -> UserQueryResponse:
    """處理用戶查詢"""
    try:
        # 處理查詢
        response = await pipeline.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        # 獲取推薦結果
        recommendations = await pipeline.get_recommendations(request.query, request.user_id)
        
        # 處理 TTS 語音合成
        audio_data = None
        voice_used = None
        speed_used = None
        
        if request.enable_tts and pipeline.tts_service:
            try:
                tts_result = await pipeline.synthesize_speech(
                    text=response.content,
                    voice=request.voice,
                    speed=request.speed
                )
                if tts_result and tts_result.get("success"):
                    audio_data = tts_result.get("audio_data")
                    voice_used = tts_result.get("voice")
                    speed_used = tts_result.get("speed")
                    logger.info(f"TTS 語音合成成功: 語音={voice_used}, 速度={speed_used}")
            except Exception as e:
                logger.warning(f"TTS 語音合成失敗: {e}")
        
        return UserQueryResponse(
            user_id=request.user_id,
            query=request.query,
            response=response.content,
            category=response.metadata.get("category", "general"),
            confidence=response.confidence,
            recommendations=recommendations,
            reasoning=response.metadata.get("reasoning", ""),
            processing_time=response.processing_time,
            timestamp=datetime.now().isoformat(),
            audio_data=audio_data,
            voice_used=voice_used,
            speed_used=speed_used,
            tts_enabled=request.enable_tts
        )
        
    except Exception as e:
        logger.error(f"處理查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理查詢失敗: {str(e)}")


@app.post("/api/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    request: TTSRequest,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
) -> TTSResponse:
    """TTS 語音合成端點"""
    try:
        if not pipeline.tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務不可用")
        
        start_time = datetime.now()
        
        # 執行語音合成
        tts_result = await pipeline.synthesize_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if tts_result and tts_result.get("success"):
            return TTSResponse(
                success=True,
                audio_data=tts_result.get("audio_data"),
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                processing_time=processing_time,
                message="語音合成成功"
            )
        else:
            return TTSResponse(
                success=False,
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                processing_time=processing_time,
                message="語音合成失敗"
            )
        
    except Exception as e:
        logger.error(f"TTS 語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 語音合成失敗: {str(e)}")


@app.get("/api/v1/tts/voices")
async def get_available_voices(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)) -> Dict[str, Any]:
    """獲取可用的語音列表"""
    try:
        if not pipeline.tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務不可用")
        
        voices = pipeline.tts_service.get_available_voices()
        return {
            "success": True,
            "voices": voices,
            "count": len(voices)
        }
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")


@app.get("/api/v1/system-info", response_model=SystemInfoResponse)
async def get_system_info(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)) -> SystemInfoResponse:
    """獲取系統資訊"""
    try:
        system_info = pipeline.get_system_info()
        
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


# 主函數
async def main():
    """主函數 - 用於直接運行"""
    import uvicorn
    
    logger.info("🚀 啟動 Podwise RAG Pipeline 服務...")
    
    # 啟動 FastAPI 服務
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=False, log_level="info") 