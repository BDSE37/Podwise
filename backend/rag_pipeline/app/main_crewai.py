#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主應用程式模組

此模組實現三層 CrewAI 架構的 FastAPI 應用程式，整合
Keyword Mapper、KNN 推薦器和用戶 ID 管理流程。

主要功能：
- 三層 CrewAI 代理人架構
- 用戶查詢處理和分類
- Podcast 推薦系統
- 聊天歷史管理
- 用戶 ID 驗證
- 向量搜尋整合

作者: Podwise Team
版本: 3.0.0
"""

import os
import logging
import asyncio
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# 導入核心組件
from core.crew_agents import AgentManager, UserQuery
from core.chat_history_service import ChatHistoryService
from core.qwen3_llm_manager import Qwen3LLMManager

# 導入工具
from tools.keyword_mapper import KeywordMapper, CategoryResult
from tools.knn_recommender import KNNRecommender, PodcastItem, RecommendationResult
from tools.enhanced_vector_search import EnhancedVectorSearchTool

# 導入配置
from config.integrated_config import get_config

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    """應用程式配置數據類別"""
    title: str = "Podwise RAG Pipeline - 三層 CrewAI 架構"
    description: str = "整合 Keyword Mapper、KNN 推薦器和用戶 ID 管理的智能 Podcast 推薦系統"
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


class ApplicationManager:
    """應用程式管理器"""
    
    def __init__(self) -> None:
        """初始化應用程式管理器"""
        self.config = get_config()
        self.app_config = AppConfig()
        
        # 核心組件
        self.agent_manager: Optional[AgentManager] = None
        self.keyword_mapper: Optional[KeywordMapper] = None
        self.knn_recommender: Optional[KNNRecommender] = None
        self.chat_history_service: Optional[ChatHistoryService] = None
        self.qwen3_manager: Optional[Qwen3LLMManager] = None
        self.vector_search_tool: Optional[EnhancedVectorSearchTool] = None
        
        # 系統狀態
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """初始化所有核心組件"""
        try:
            logger.info("🚀 初始化 Podwise RAG Pipeline - 三層 CrewAI 架構...")
            
            # 初始化 Keyword Mapper
            self.keyword_mapper = KeywordMapper()
            logger.info("✅ Keyword Mapper 初始化完成")
            
            # 初始化 KNN 推薦器
            self.knn_recommender = KNNRecommender(k=5, metric="cosine")
            logger.info("✅ KNN 推薦器初始化完成")
            
            # 初始化聊天歷史服務
            self.chat_history_service = ChatHistoryService()
            logger.info("✅ 聊天歷史服務初始化完成")
            
            # 初始化 Qwen3 LLM 管理器
            self.qwen3_manager = Qwen3LLMManager()
            logger.info("✅ Qwen3 LLM 管理器初始化完成")
            
            # 初始化向量搜尋工具
            self.vector_search_tool = EnhancedVectorSearchTool()
            logger.info("✅ 向量搜尋工具初始化完成")
            
            # 初始化三層代理人架構
            agent_config = self.config.get_agent_config()
            self.agent_manager = AgentManager(agent_config)
            logger.info("✅ 三層代理人架構初始化完成")
            
            # 載入示例 Podcast 數據
            await self._load_sample_podcast_data()
            
            self._is_initialized = True
            logger.info("✅ 所有核心組件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {str(e)}")
            raise
    
    async def _load_sample_podcast_data(self) -> None:
        """載入示例 Podcast 數據"""
        if self.knn_recommender is None:
            return
        
        sample_items = [
            PodcastItem(
                rss_id="rss_001",
                title="股癌 EP310",
                description="台股投資分析與市場趨勢",
                category="商業",
                tags=["股票", "投資", "台股", "財經"],
                vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
                updated_at="2025-01-15",
                confidence=0.9
            ),
            PodcastItem(
                rss_id="rss_002",
                title="大人學 EP110",
                description="職涯發展與個人成長指南",
                category="教育",
                tags=["職涯", "成長", "技能", "學習"],
                vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
                updated_at="2025-01-14",
                confidence=0.85
            ),
            PodcastItem(
                rss_id="rss_003",
                title="財報狗 Podcast",
                description="財報分析與投資策略",
                category="商業",
                tags=["財報", "投資", "分析", "策略"],
                vector=np.array([0.9, 0.5, 0.8, 0.6, 0.9, 0.5, 0.8, 0.6]),
                updated_at="2025-01-13",
                confidence=0.88
            ),
            PodcastItem(
                rss_id="rss_004",
                title="生涯決策學 EP52",
                description="人生規劃與決策思維",
                category="教育",
                tags=["生涯", "決策", "規劃", "思維"],
                vector=np.array([0.4, 0.7, 0.5, 0.8, 0.4, 0.7, 0.5, 0.8]),
                updated_at="2025-01-12",
                confidence=0.82
            )
        ]
        
        self.knn_recommender.add_podcast_items(sample_items)
        logger.info(f"✅ 已載入 {len(sample_items)} 個示例 Podcast 項目")
    
    def get_system_status(self) -> SystemStatus:
        """獲取系統狀態"""
        components = {
            "keyword_mapper": self.keyword_mapper is not None,
            "knn_recommender": self.knn_recommender is not None,
            "chat_history_service": self.chat_history_service is not None,
            "qwen3_manager": self.qwen3_manager is not None,
            "vector_search_tool": self.vector_search_tool is not None,
            "agent_manager": self.agent_manager is not None
        }
        
        return SystemStatus(
            is_ready=self._is_initialized,
            components=components,
            timestamp=datetime.now().isoformat(),
            version=self.app_config.version
        )
    
    def is_ready(self) -> bool:
        """檢查系統是否準備就緒"""
        return self._is_initialized


# 創建應用程式管理器實例
app_manager = ApplicationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理器"""
    # 啟動時初始化
    await app_manager.initialize()
    yield
    # 關閉時清理
    logger.info("應用程式關閉，清理資源...")


# 創建 FastAPI 應用
app = FastAPI(
    title=app_manager.app_config.title,
    description=app_manager.app_config.description,
    version=app_manager.app_config.version,
    docs_url=app_manager.app_config.docs_url,
    redoc_url=app_manager.app_config.redoc_url,
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


# API 模型定義
class UserQueryRequest(BaseModel):
    """用戶查詢請求模型"""
    user_id: str = Field(..., description="用戶 ID", min_length=1)
    query: str = Field(..., description="查詢內容", min_length=1)
    session_id: Optional[str] = Field(default=None, description="會話 ID")
    
    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()
    
    @validator('query')
    def validate_query(cls, v: str) -> str:
        """驗證查詢內容"""
        if not v.strip():
            raise ValueError("查詢內容不能為空")
        return v.strip()


class UserQueryResponse(BaseModel):
    """用戶查詢回應模型"""
    user_id: str
    query: str
    response: str
    category: str
    confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning: str
    processing_time: float
    timestamp: str


class UserValidationRequest(BaseModel):
    """用戶驗證請求模型"""
    user_id: str = Field(..., description="用戶 ID", min_length=1)
    
    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()


class UserValidationResponse(BaseModel):
    """用戶驗證回應模型"""
    user_id: str
    is_valid: bool
    has_history: bool
    preferred_category: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    error: str
    detail: str
    timestamp: str


# 依賴注入
def get_app_manager() -> ApplicationManager:
    """獲取應用程式管理器"""
    return app_manager


def validate_system_ready(manager: ApplicationManager = Depends(get_app_manager)) -> None:
    """驗證系統是否準備就緒"""
    if not manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="系統尚未準備就緒，請稍後再試"
        )


# API 端點
@app.get("/")
async def root() -> Dict[str, Any]:
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline - 三層 CrewAI 架構運行中",
        "version": app_manager.app_config.version,
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Keyword Mapper 分類",
            "KNN 推薦算法",
            "三層 CrewAI 架構",
            "用戶 ID 管理",
            "聊天歷史追蹤",
            "向量搜尋",
            "Qwen3 LLM 整合"
        ],
        "supported_categories": ["商業", "教育"],
        "status": "running"
    }


@app.get("/health")
async def health_check(manager: ApplicationManager = Depends(get_app_manager)) -> Dict[str, Any]:
    """健康檢查端點"""
    status = manager.get_system_status()
    return {
        "status": "healthy" if status.is_ready else "unhealthy",
        "timestamp": status.timestamp,
        "version": status.version,
        "components": status.components
    }


@app.post("/api/v1/validate-user", response_model=UserValidationResponse)
async def validate_user(
    request: UserValidationRequest,
    manager: ApplicationManager = Depends(get_app_manager),
    _: None = Depends(validate_system_ready)
) -> UserValidationResponse:
    """
    驗證用戶 ID
    
    此端點驗證用戶 ID 的有效性，並檢查是否有歷史記錄。
    """
    try:
        user_id = request.user_id
        
        # 基本驗證
        is_valid = len(user_id) >= 3 and user_id.isalnum()
        
        if not is_valid:
            return UserValidationResponse(
                user_id=user_id,
                is_valid=False,
                has_history=False,
                message="用戶 ID 格式無效，必須至少 3 個字符且只包含字母和數字"
            )
        
        # 檢查歷史記錄
        has_history = False
        preferred_category = None
        
        if manager.chat_history_service:
            history = manager.chat_history_service.get_chat_history(user_id, limit=10)
            has_history = len(history) > 0
            
            if has_history:
                preferred_category = _analyze_user_preference(history)
        
        message = "用戶驗證成功"
        if has_history:
            message += f"，發現 {len(history)} 條歷史記錄"
        
        return UserValidationResponse(
            user_id=user_id,
            is_valid=True,
            has_history=has_history,
            preferred_category=preferred_category,
            message=message
        )
        
    except Exception as e:
        logger.error(f"用戶驗證失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"用戶驗證失敗: {str(e)}")


def _analyze_user_preference(history: List[Dict[str, Any]]) -> Optional[str]:
    """分析用戶偏好"""
    if not history:
        return None
    
    category_counts = {}
    for record in history:
        category = record.get('category', '未知')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    if category_counts:
        return max(category_counts.items(), key=lambda x: x[1])[0]
    
    return None


@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(
    request: UserQueryRequest,
    background_tasks: BackgroundTasks,
    manager: ApplicationManager = Depends(get_app_manager),
    _: None = Depends(validate_system_ready)
) -> UserQueryResponse:
    """
    處理用戶查詢
    
    此端點處理用戶查詢，執行分類、推薦和回應生成。
    """
    start_time = datetime.now()
    
    try:
        user_id = request.user_id
        query = request.query
        session_id = request.session_id
        
        logger.info(f"處理用戶查詢: {user_id} - {query}")
        
        # 1. 使用 Keyword Mapper 分類查詢
        if manager.keyword_mapper is None:
            raise HTTPException(status_code=500, detail="Keyword Mapper 未初始化")
        
        category_result = manager.keyword_mapper.categorize_query(query)
        
        # 2. 獲取推薦
        recommendations = await _get_recommendations(query, category_result, manager)
        
        # 3. 生成回應
        response = await _generate_response(query, category_result, recommendations, manager)
        
        # 4. 計算處理時間
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 5. 記錄歷史（背景任務）
        background_tasks.add_task(
            _log_query_history,
            user_id, session_id, query, response, 
            category_result.category, category_result.confidence
        )
        
        return UserQueryResponse(
            user_id=user_id,
            query=query,
            response=response,
            category=category_result.category,
            confidence=category_result.confidence,
            recommendations=recommendations,
            reasoning=category_result.reasoning,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")


async def _get_recommendations(
    query: str, 
    category_result: CategoryResult,
    manager: ApplicationManager
) -> List[Dict[str, Any]]:
    """獲取推薦項目"""
    if manager.knn_recommender is None:
        return []
    
    try:
        # 生成查詢向量（簡化版本）
        query_vector = _generate_simple_vector(query)
        
        # 執行推薦
        recommendation_result = manager.knn_recommender.recommend(
            query_vector=query_vector,
            category_filter=category_result.category if category_result.category != "雙類別" else None,
            top_k=3
        )
        
        # 轉換為字典格式
        recommendations = []
        for item in recommendation_result.recommendations:
            recommendations.append({
                "rss_id": item.rss_id,
                "title": item.title,
                "description": item.description,
                "category": item.category,
                "tags": item.tags,
                "confidence": item.confidence,
                "updated_at": item.updated_at
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"獲取推薦失敗: {str(e)}")
        return []


def _generate_simple_vector(text: str) -> np.ndarray:
    """生成簡單的文本向量（用於測試）"""
    # 簡化的向量生成邏輯
    # 實際應用中應使用更複雜的嵌入模型
    words = text.lower().split()
    vector = np.zeros(8)
    
    # 簡單的關鍵詞權重
    business_keywords = ["股票", "投資", "理財", "財經", "市場", "經濟"]
    education_keywords = ["學習", "技能", "成長", "職涯", "發展", "教育"]
    
    for word in words:
        if word in business_keywords:
            vector[0:4] += 0.1
        if word in education_keywords:
            vector[4:8] += 0.1
    
    # 正規化
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector


async def _generate_response(
    query: str,
    category_result: CategoryResult,
    recommendations: List[Dict[str, Any]],
    manager: ApplicationManager
) -> str:
    """生成回應"""
    try:
        # 如果有 LLM 管理器，使用它生成回應
        if manager.qwen3_manager:
            # 這裡可以整合 LLM 生成邏輯
            pass
        
        # 否則使用簡單的回應生成
        return _generate_fallback_response(category_result, recommendations)
        
    except Exception as e:
        logger.error(f"生成回應失敗: {str(e)}")
        return _generate_fallback_response(category_result, recommendations)


def _generate_fallback_response(
    category_result: CategoryResult,
    recommendations: List[Dict[str, Any]]
) -> str:
    """生成備用回應"""
    category = category_result.category
    confidence = category_result.confidence
    
    if not recommendations:
        return f"根據您的查詢，我將其分類為 {category} 類別（信心值: {confidence:.2f}）。目前沒有找到相關的 Podcast 推薦。"
    
    response = f"""
根據您的查詢，我將其分類為 {category} 類別（信心值: {confidence:.2f}）。

以下是為您推薦的 Podcast：

"""
    
    for i, rec in enumerate(recommendations, 1):
        response += f"{i}. **{rec['title']}**\n"
        response += f"   - 類別: {rec['category']}\n"
        response += f"   - 描述: {rec['description']}\n"
        response += f"   - 標籤: {', '.join(rec['tags'])}\n\n"
    
    response += f"分類理由: {category_result.reasoning}"
    
    return response


async def _log_query_history(
    user_id: str,
    session_id: Optional[str],
    query: str,
    response: str,
    category: str,
    confidence: float
) -> None:
    """記錄查詢歷史"""
    try:
        if app_manager.chat_history_service:
            # 儲存用戶查詢
            app_manager.chat_history_service.save_chat_message(
                user_id=user_id,
                session_id=session_id or "default",
                role="user",
                content=query,
                chat_mode="rag",
                metadata={"category": category, "confidence": confidence}
            )
            
            # 儲存系統回應
            app_manager.chat_history_service.save_chat_message(
                user_id=user_id,
                session_id=session_id or "default",
                role="assistant",
                content=response,
                chat_mode="rag",
                metadata={"category": category, "confidence": confidence}
            )
    except Exception as e:
        logger.error(f"記錄歷史失敗: {str(e)}")


@app.get("/api/v1/chat-history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    manager: ApplicationManager = Depends(get_app_manager),
    _: None = Depends(validate_system_ready)
) -> List[Dict[str, Any]]:
    """獲取用戶聊天歷史"""
    try:
        if manager.chat_history_service is None:
            raise HTTPException(status_code=500, detail="聊天歷史服務未初始化")
        
        history = manager.chat_history_service.get_chat_history(user_id, limit=limit)
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取聊天歷史失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取聊天歷史失敗: {str(e)}")


@app.get("/api/v1/system-info")
async def get_system_info(manager: ApplicationManager = Depends(get_app_manager)) -> Dict[str, Any]:
    """獲取系統資訊"""
    status = manager.get_system_status()
    
    return {
        "system_status": {
            "is_ready": status.is_ready,
            "components": status.components,
            "timestamp": status.timestamp,
            "version": status.version
        },
        "configuration": {
            "app_title": manager.app_config.title,
            "app_version": manager.app_config.version,
            "supported_categories": ["商業", "教育"],
            "features": [
                "Keyword Mapper 分類",
                "KNN 推薦算法",
                "三層 CrewAI 架構",
                "用戶 ID 管理",
                "聊天歷史追蹤",
                "向量搜尋",
                "Qwen3 LLM 整合"
            ]
        },
        "statistics": {
            "total_podcast_items": len(manager.knn_recommender.podcast_items) if manager.knn_recommender else 0,
            "category_distribution": manager.knn_recommender.get_category_statistics() if manager.knn_recommender else {}
        }
    }


# 錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """全局異常處理器"""
    logger.error(f"未處理的異常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="系統內部錯誤，請稍後再試",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            detail=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 