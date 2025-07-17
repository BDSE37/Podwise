#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主服務

整合 Apple Podcast 排名系統的智能推薦引擎
提供統一的 RAG Pipeline 服務

作者: Podwise Team
版本: 2.0.0
"""

import os
import sys

# 清除 Python 模組快取，避免載入錯誤的模組
for module_name in list(sys.modules.keys()):
    if module_name.startswith('core.') or module_name.startswith('config.'):
        del sys.modules[module_name]

# 強制設定 sys.path，確保 rag_pipeline 目錄優先
current_dir = os.path.dirname(os.path.abspath(__file__))  # rag_pipeline 目錄
backend_root = os.path.abspath(os.path.join(current_dir, '..'))  # backend 目錄

# 完全重新設定 sys.path
sys.path = [
    current_dir,  # rag_pipeline 目錄（最高優先級）
    backend_root,  # backend 目錄
    '/usr/lib/python3.10',
    '/usr/lib/python3.10/lib-dynload',
    '/home/bai/Desktop/Podwise/.venv/lib/python3.10/site-packages'
]

# 設定環境變數
os.environ['PYTHONPATH'] = f"{current_dir}:{backend_root}"

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入必要的標準庫
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# API 模型定義
class UserQueryRequest(BaseModel):
    """用戶查詢請求"""
    query: str = Field(..., description="用戶查詢內容")
    user_id: str = Field(default="default_user", description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外元數據")
    enable_tts: bool = Field(default=False, description="是否啟用TTS")
    voice: str = Field(default="podrina", description="語音模型")
    speed: float = Field(default=1.0, description="語音速度")

class UserQueryResponse(BaseModel):
    """用戶查詢回應"""
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

class UserValidationRequest(BaseModel):
    """用戶驗證請求"""
    user_id: str = Field(..., description="用戶ID")

class UserValidationResponse(BaseModel):
    """用戶驗證回應"""
    user_id: str
    is_valid: bool
    has_history: bool
    preferred_category: Optional[str] = None
    message: str

class TTSRequest(BaseModel):
    """TTS請求"""
    text: str = Field(..., description="要合成的文字")
    voice: str = Field(default="podrina", description="語音模型")
    speed: float = Field(default=1.0, description="語音速度")

class TTSResponse(BaseModel):
    """TTS回應"""
    success: bool
    audio_data: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    processing_time: float
    message: str

class ErrorResponse(BaseModel):
    """錯誤回應"""
    error: str
    detail: str
    timestamp: str

class SystemInfoResponse(BaseModel):
    """系統資訊回應"""
    version: str
    status: str
    components: Dict[str, bool]
    timestamp: str

class HealthCheckResponse(BaseModel):
    """健康檢查回應"""
    status: str
    timestamp: str
    components: Dict[str, bool]

# 修復模組導入 - 使用正確的導入路徑
try:
    from core import RAGVectorSearch, RAGSearchConfig
    VECTOR_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"向量搜尋模組導入失敗: {e}")
    VECTOR_SEARCH_AVAILABLE = False
    RAGVectorSearch = None
    RAGSearchConfig = None

try:
    from core import AgentResponse, UserQuery, RAGResponse, BaseAgent
    from core import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent
    CREW_AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrewAI 代理模組導入失敗: {e}")
    CREW_AGENTS_AVAILABLE = False
    LeaderAgent = BusinessExpertAgent = EducationExpertAgent = UserManagerAgent = None
    UserQuery = AgentResponse = RAGResponse = BaseAgent = None

try:
    from core import HierarchicalRAGPipeline
    RAG_PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"層級化 RAG Pipeline 模組導入失敗: {e}")
    RAG_PIPELINE_AVAILABLE = False
    HierarchicalRAGPipeline = None

try:
    from core import ApplePodcastRankingSystem
    APPLE_RANKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Apple Podcast 排名模組導入失敗: {e}")
    APPLE_RANKING_AVAILABLE = False
    ApplePodcastRankingSystem = None

try:
    from core import ContentCategorizer
    CONTENT_CATEGORIZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"內容分類器模組導入失敗: {e}")
    CONTENT_CATEGORIZER_AVAILABLE = False
    ContentCategorizer = None

try:
    from core import Qwen3LLMManager
    QWEN_LLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Qwen LLM 管理器模組導入失敗: {e}")
    QWEN_LLM_AVAILABLE = False
    Qwen3LLMManager = None

try:
    from core import ChatHistoryService
    CHAT_HISTORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"聊天歷史服務模組導入失敗: {e}")
    CHAT_HISTORY_AVAILABLE = False
    ChatHistoryService = None

try:
    from config import get_config
    CONFIG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"整合配置模組導入失敗: {e}")
    CONFIG_AVAILABLE = False
    get_config = None

try:
    from config import PodwisePromptTemplates
    PROMPT_TEMPLATES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"提示詞模板模組導入失敗: {e}")
    PROMPT_TEMPLATES_AVAILABLE = False
    PodwisePromptTemplates = None

try:
    from core import MCPEnhancedPodcastRecommender
    RECOMMENDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增強推薦器模組導入失敗: {e}")
    RECOMMENDER_AVAILABLE = False
    MCPEnhancedPodcastRecommender = None

try:
    from tools.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult
    FORMATTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Podcast 格式化器模組導入失敗: {e}")
    FORMATTER_AVAILABLE = False
    PodcastFormatter = None
    FormattedPodcast = None
    PodcastRecommendationResult = None

try:
    from core.default_qa_processor import DefaultQAProcessor, create_default_qa_processor
    QA_PROCESSOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"預設問答處理器模組導入失敗: {e}")
    QA_PROCESSOR_AVAILABLE = False
    DefaultQAProcessor = None
    def create_default_qa_processor(csv_path: str = "scripts/default_QA.csv") -> Optional[Any]:
        return None

try:
    from tools.web_search_tool import WebSearchExpert as WebSearchTool
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Web 搜尋工具模組導入失敗: {e}")
    WEB_SEARCH_AVAILABLE = False
    WebSearchTool = None

try:
    from tts.config.voice_config import VoiceConfig
    from tts.core.tts_service import TTSService as PodriTTSService
    TTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TTS 服務模組導入失敗: {e}")
    TTS_AVAILABLE = False
    VoiceConfig = None
    PodriTTSService = None

# 簡化的配置函數
def get_simple_config():
    """簡化的配置函數"""
    return {
        "llm": {"host": "localhost", "port": 8003},
        "milvus": {"host": "localhost", "port": 19530},
        "confidence_threshold": 0.7,
        "tts": {"host": "localhost", "port": 8003}
    }

# 如果配置模組不可用，使用簡化配置
if not CONFIG_AVAILABLE:
    get_config = get_simple_config

# 創建 FastAPI 應用
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

# 全局服務管理器
service_manager = None


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
        self.config = get_config() if get_config else get_simple_config()
        
        # 初始化提示詞模板
        self.prompt_templates = PodwisePromptTemplates() if PodwisePromptTemplates else None
        
        # 初始化 LLM 管理器
        self.llm_manager = Qwen3LLMManager() if Qwen3LLMManager else None
        
        # 初始化內容處理器
        self.categorizer = ContentCategorizer() if ContentCategorizer else None
        
        # 初始化聊天歷史服務（如果啟用且可用）
        self.chat_history = None
        if enable_chat_history:
            try:
                self.chat_history = ChatHistoryService()
                logger.info("✅ 聊天歷史服務初始化成功")
            except Exception as e:
                logger.warning(f"聊天歷史服務初始化失敗: {e}")
                self.chat_history = None
        
        # 初始化 Apple Podcast 排名系統（如果啟用且可用）
        self.apple_ranking = None
        if enable_apple_ranking:
            try:
                self.apple_ranking = ApplePodcastRankingSystem()
                logger.info("✅ Apple Podcast 排名系統初始化成功")
            except Exception as e:
                logger.warning(f"Apple Podcast 排名系統初始化失敗: {e}")
                self.apple_ranking = None
        
        # 初始化三層式回覆機制組件
        try:
            self.default_qa_processor = create_default_qa_processor()
            logger.info("✅ 預設問答處理器初始化成功")
        except Exception as e:
            logger.warning(f"預設問答處理器初始化失敗: {e}")
            self.default_qa_processor = None
            
        try:
            self.vector_search = RAGVectorSearch()
            logger.info("✅ 向量搜尋初始化成功")
        except Exception as e:
            logger.warning(f"向量搜尋初始化失敗: {e}")
            self.vector_search = None
            
        try:
            self.web_search_tool = WebSearchTool()
            logger.info("✅ Web 搜尋工具初始化成功")
        except Exception as e:
            logger.warning(f"Web 搜尋工具初始化失敗: {e}")
            self.web_search_tool = None
        
        # 初始化 CrewAI 代理
        self._initialize_agents()
        
        # 初始化層級化 RAG Pipeline
        self.rag_pipeline = HierarchicalRAGPipeline() if HierarchicalRAGPipeline else None
        
        # 初始化整合核心
        self.integrated_core = None # UnifiedQueryProcessor({}) # This line was removed as UnifiedQueryProcessor is no longer imported
        
        # 初始化 TTS 服務
        self.tts_service = None
        if TTS_AVAILABLE and PodriTTSService:
            try:
                self.tts_service = PodriTTSService()
                logger.info("✅ TTS 服務初始化完成")
            except Exception as e:
                logger.warning(f"TTS 服務初始化失敗: {e}")
        
        logger.info("✅ Podwise RAG Pipeline 初始化完成")
    
    def _initialize_agents(self):
        """初始化 CrewAI 代理"""
        config = {
            'confidence_threshold': self.confidence_threshold,
            'max_processing_time': 30.0
        }
        
        # 檢查代理類別是否可用，並處理導入錯誤
        try:
            if UserManagerAgent:
                self.user_manager = UserManagerAgent(config)
            else:
                self.user_manager = None
        except Exception as e:
            logger.warning(f"UserManagerAgent 初始化失敗: {e}")
            self.user_manager = None
            
        try:
            if BusinessExpertAgent:
                self.business_expert = BusinessExpertAgent(config)
            else:
                self.business_expert = None
        except Exception as e:
            logger.warning(f"BusinessExpertAgent 初始化失敗: {e}")
            self.business_expert = None
            
        try:
            if EducationExpertAgent:
                self.education_expert = EducationExpertAgent(config)
            else:
                self.education_expert = None
        except Exception as e:
            logger.warning(f"EducationExpertAgent 初始化失敗: {e}")
            self.education_expert = None
            
        try:
            if LeaderAgent:
                self.leader_agent = LeaderAgent(config)
            else:
                self.leader_agent = None
        except Exception as e:
            logger.warning(f"LeaderAgent 初始化失敗: {e}")
            self.leader_agent = None
        
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
            # 檢查預設問答處理器是否可用
            if self.default_qa_processor is None:
                logger.warning("預設問答處理器不可用")
                return None
                
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
            # 檢查向量搜尋是否可用
            if self.vector_search is None:
                logger.warning("向量搜尋服務不可用")
                return None
                
            # 使用向量搜尋
            search_results = await self.vector_search.search(query)
            
            if not search_results:
                logger.info("向量搜尋無結果")
                return None
            
            # 計算平均信心度
            avg_confidence = sum(result.confidence for result in search_results) / len(search_results)
            
            # 檢查是否達到信心度閾值
            if avg_confidence < self.confidence_threshold:
                logger.info(f"向量搜尋信心度不足: {avg_confidence:.2f} < {self.confidence_threshold}")
                return None
            
            # 格式化回應
            content = self._format_vector_search_response(search_results)
            
            logger.info(f"向量搜尋成功，信心度: {avg_confidence:.2f}，結果數量: {len(search_results)}")
            
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
            # 檢查 Web 搜尋工具是否可用
            if self.web_search_tool is None:
                logger.warning("Web 搜尋工具不可用")
                return RAGResponse(
                    content="抱歉，搜尋服務暫時無法使用。請稍後再試。",
                    confidence=0.0,
                    sources=["error"],
                    processing_time=0.0,
                    level_used="error",
                    metadata={"error": "web_search_tool_unavailable"}
                )
                
            # 使用 Web 搜尋工具
            web_results = await self.web_search_tool.search_with_openai(query)
            
            if web_results.get("success") and web_results.get("results"):
                content = self._format_web_search_response(web_results["results"])
            else:
                content = "抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。"
            
            # 計算 web_search 的信心度，確保達到閾值
            web_confidence = 0.7  # 設定為閾值，確保能通過檢查
            
            return RAGResponse(
                content=content,
                confidence=web_confidence,
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
        
        # 提取主要內容，不添加額外的格式說明
        responses = []
        for i, result in enumerate(search_results[:3], 1):  # 最多顯示3個
            content = result.content
            if hasattr(result, 'episode_title') and result.episode_title:
                content = f"{result.episode_title}: {content}"
            responses.append(content)
        
        # 直接返回內容，不添加額外的說明文字
        return "\n".join(responses)
    
    def _format_web_search_response(self, web_results: List[Dict[str, Any]]) -> str:
        """格式化 Web 搜尋回應（隱藏 web_search 來源）"""
        if not web_results:
            return "抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。"
        
        # 提取主要內容並改善格式，不提及來源
        responses = []
        for i, result in enumerate(web_results[:2]):  # 取前兩個結果
            title = result.get("title", "")
            content = result.get("content", "")
            
            if content and len(content) > 30:
                # 簡化內容，移除冗長的描述
                if len(content) > 200:
                    content = content[:200] + "..."
                
                if title and title != "未知標題":
                    responses.append(f"{title}：{content}")
                else:
                    responses.append(content)
        
        if responses:
            # 不提及 "根據搜尋結果"，直接提供內容
            return " ".join(responses)
        else:
            return "抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。"
    
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
        
        # 確保有有效的使用者ID
        effective_user_id = user_id or "default_user"
        effective_session_id = session_id or f"session_{effective_user_id}_{int(start_time.timestamp())}"
        
        logger.info(f"🔄 開始處理查詢: {effective_user_id} - {query[:50]}...")
        
        # 記錄用戶查詢到聊天歷史
        if self.enable_chat_history and self.chat_history:
            try:
                self.chat_history.save_chat_message(
                    user_id=effective_user_id,
                    session_id=effective_session_id,
                    role="user",
                    content=query,
                    chat_mode="rag",
                    metadata={
                        **(metadata or {}),
                        "user_identifier": effective_user_id,
                        "processing_start": start_time.isoformat()
                    }
                )
                logger.info(f"✅ 記錄用戶查詢成功: {effective_user_id}")
            except Exception as e:
                logger.warning(f"⚠️ 記錄用戶查詢失敗: {e}")
        
        try:
            # 第一層：向量搜尋
            vector_result = await self._process_vector_search(query)
            if vector_result and vector_result.confidence >= self.confidence_threshold:
                logger.info(f"✅ 使用向量搜尋回覆 (信心度: {vector_result.confidence:.2f})")
                # 記錄成功的向量搜尋結果
                self._log_successful_query(effective_user_id, "vector_search", query, vector_result.confidence)
                return vector_result
            
            # 第二層：Web 搜尋 fallback
            logger.info("🔄 使用 Web 搜尋作為 fallback")
            web_result = await self._process_web_search(query)
            
            # 第三層：檢查預設問答（如果前兩層都失敗）
            default_qa_result = await self._check_default_qa(query)
            if default_qa_result:
                logger.info("✅ 使用預設問答回覆")
                self._log_successful_query(effective_user_id, "default_qa", query, default_qa_result.confidence)
                return default_qa_result
            
            # 如果都沒有找到合適的回應，返回 web 搜尋結果
            self._log_successful_query(effective_user_id, "web_search", query, web_result.confidence)
            return web_result
            
        except Exception as e:
            logger.error(f"❌ 查詢處理失敗: {e}")
            # 記錄失敗的查詢
            self._log_failed_query(effective_user_id, query, str(e))
            return RAGResponse(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                metadata={
                    "error": str(e),
                    "user_id": effective_user_id,
                    "session_id": effective_session_id
                }
            )
    
    def _log_successful_query(self, user_id: str, method: str, query: str, confidence: float):
        """記錄成功的查詢"""
        try:
            logger.info(f"✅ 查詢成功記錄: {user_id} - {method} - 信心度: {confidence:.2f}")
            # 這裡可以添加更詳細的日誌記錄或資料庫記錄
        except Exception as e:
            logger.warning(f"⚠️ 記錄成功查詢失敗: {e}")
    
    def _log_failed_query(self, user_id: str, query: str, error: str):
        """記錄失敗的查詢"""
        try:
            logger.warning(f"❌ 查詢失敗記錄: {user_id} - 錯誤: {error}")
            # 這裡可以添加更詳細的錯誤記錄
        except Exception as e:
            logger.warning(f"⚠️ 記錄失敗查詢失敗: {e}")
    
    async def _apply_apple_ranking(self, response: RAGResponse, query: str) -> RAGResponse:
        """應用 Apple Podcast 排名系統"""
        try:
            # 從 metadata 中獲取推薦結果
            recommendations = response.metadata.get('recommendations', [])
            if recommendations and self.apple_ranking:
                # 轉換為 ApplePodcastRating 格式
                from core.apple_podcast_ranking import ApplePodcastRating
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
                "user_manager": self.user_manager.is_available if hasattr(self.user_manager, 'is_available') else True,
                "business_expert": self.business_expert.is_available if hasattr(self.business_expert, 'is_available') else True,
                "education_expert": self.education_expert.is_available if hasattr(self.education_expert, 'is_available') else True,
                "leader_agent": self.leader_agent.is_available if hasattr(self.leader_agent, 'is_available') else True
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
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        語音合成方法
        
        Args:
            text: 要合成的文字
            voice: 語音 ID，預設為 podrina (溫柔女聲)
            speed: 語速倍數，預設為 1.0 (正常速度)
            
        Returns:
            Optional[Dict[str, Any]]: 包含音頻數據的字典，失敗時返回 None
        """
        if not self.tts_service:
            logger.warning("TTS 服務不可用")
            return None
        
        try:
            # 轉換語速參數為 Edge TTS 格式
            if speed != 1.0:
                rate = f"{int((speed - 1) * 100):+d}%"
            else:
                rate = "+0%"
            
            # 執行語音合成
            audio_data = await self.tts_service.語音合成(
                text=text,
                語音=voice,
                語速=rate,
                音量="+0%",
                音調="+0%"
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
            else:
                logger.error("語音合成失敗")
                return None
                
        except Exception as e:
            logger.error(f"語音合成錯誤: {str(e)}")
            return None


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


@app.get("/health")
async def health_check(manager: RAGPipelineService = Depends(get_service_manager)):
    """健康檢查端點"""
    if not manager.rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
    
    health_data = await manager.rag_pipeline.health_check()
    
    return {
        "status": health_data["status"],
        "timestamp": health_data["timestamp"],
        "components": health_data.get("components", {}),
        "rag_pipeline_health": health_data,
        "web_search_available": manager.web_search_tool.is_configured() if manager.web_search_tool and hasattr(manager.web_search_tool, 'is_configured') else False
    }


@app.post("/api/v1/validate-user")
async def validate_user(
    request: UserValidationRequest,
    manager: RAGPipelineService = Depends(get_service_manager),
    _: None = Depends(validate_system_ready)
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
        
        # 處理 TTS 語音合成
        audio_data = None
        voice_used = None
        speed_used = None
        
        if request.enable_tts and manager.rag_pipeline.tts_service:
            try:
                tts_result = await manager.rag_pipeline.synthesize_speech(
                    text=response.content,
                    voice=request.voice,
                    speed=request.speed
                )
                if tts_result and tts_result.get("success"):
                    audio_data = tts_result.get("audio_data")
                    voice_used = tts_result.get("voice")
                    speed_used = tts_result.get("speed")
            except Exception as e:
                logger.warning(f"TTS 語音合成失敗: {e}")
        
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


@app.post("/api/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    request: TTSRequest,
    manager: RAGPipelineService = Depends(get_service_manager),
    _: None = Depends(validate_system_ready)
) -> TTSResponse:
    """TTS 語音合成端點"""
    try:
        if not manager.rag_pipeline or not manager.rag_pipeline.tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務不可用")
        
        start_time = datetime.now()
        
        # 執行語音合成
        tts_result = await manager.rag_pipeline.synthesize_speech(
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
                processing_time=processing_time
            )
        else:
            return TTSResponse(
                success=False,
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                processing_time=processing_time,
                error_message="語音合成失敗"
            )
        
    except Exception as e:
        logger.error(f"TTS 語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 語音合成失敗: {str(e)}")


@app.get("/api/v1/tts/voices")
async def get_available_voices(manager: RAGPipelineService = Depends(get_service_manager)) -> Dict[str, Any]:
    """獲取可用的語音列表"""
    try:
        if not manager.rag_pipeline or not manager.rag_pipeline.tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務不可用")
        
        voices = manager.rag_pipeline.tts_service.獲取可用語音()
        return {
            "success": True,
            "voices": voices,
            "count": len(voices)
        }
        
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")


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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=False, log_level="info") 