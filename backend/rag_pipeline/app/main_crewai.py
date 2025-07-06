#!/usr/bin/env python3
"""
Podwise RAG Pipeline FastAPI 應用程式

此模組提供 REST API 介面，整合核心 RAG Pipeline 功能：
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

# 導入核心 RAG Pipeline
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import PodwiseRAGPipeline, get_rag_pipeline

# 導入工具
from tools.enhanced_vector_search import UnifiedVectorSearch
from tools.web_search_tool import WebSearchTool
from tools.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult

# 導入配置
from config.integrated_config import get_config

# 導入統一 API 模型
from core.api_models import (
    UserQueryRequest, UserQueryResponse, UserValidationRequest, UserValidationResponse,
    ErrorResponse, SystemInfoResponse, HealthCheckResponse
)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    """應用程式配置數據類別"""
    title: str = "Podwise RAG Pipeline - FastAPI 介面"
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


class ApplicationManager:
    """應用程式管理器 - 專注於 Web API 功能"""
    
    def __init__(self) -> None:
        """初始化應用程式管理器"""
        self.config = get_config()
        self.app_config = AppConfig()
        
        # 核心 RAG Pipeline（使用 main.py 中的實現）
        self.rag_pipeline: Optional[PodwiseRAGPipeline] = None
        
        # Web API 專用組件
        self.vector_search_tool: Optional[UnifiedVectorSearch] = None
        self.web_search_tool: Optional[WebSearchTool] = None
        self.podcast_formatter: Optional[PodcastFormatter] = None
        
        # 系統狀態
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """初始化所有核心組件"""
        try:
            logger.info("🚀 初始化 Podwise RAG Pipeline FastAPI...")
            
            # 初始化核心 RAG Pipeline
            self.rag_pipeline = get_rag_pipeline()
            logger.info("✅ 核心 RAG Pipeline 初始化完成")
            
            # 初始化統一向量搜尋工具
            vector_config = self.config.get_vector_search_config()
            self.vector_search_tool = UnifiedVectorSearch(vector_config)
            logger.info("✅ 統一向量搜尋工具初始化完成")
            
            # 初始化 Web Search 工具
            self.web_search_tool = WebSearchTool()
            if self.web_search_tool.is_configured():
                logger.info("✅ Web Search 工具初始化完成 (OpenAI 可用)")
            else:
                logger.warning("⚠️ Web Search 工具初始化完成 (OpenAI 未配置)")
            
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
        "message": "Podwise RAG Pipeline - FastAPI 介面運行中",
        "version": app_manager.app_config.version,
        "timestamp": datetime.now().isoformat(),
        "features": [
            "核心 RAG Pipeline 整合",
            "統一向量搜尋",
            "用戶 ID 管理",
            "REST API 介面"
        ],
        "supported_categories": ["商業", "教育"],
        "status": "running"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(manager: ApplicationManager = Depends(get_app_manager)) -> HealthCheckResponse:
    """健康檢查端點"""
    status = manager.get_system_status()
    
    # 獲取核心 RAG Pipeline 健康狀態
    rag_health = {}
    if manager.rag_pipeline:
        try:
            rag_health = await manager.rag_pipeline.health_check()
        except Exception as e:
            rag_health = {"status": "error", "error": str(e)}
    
    return HealthCheckResponse(
        status="healthy" if status.is_ready else "unhealthy",
        timestamp=status.timestamp,
        components=status.components,
        rag_pipeline_health=rag_health,
        web_search_available=manager.web_search_tool.is_configured() if manager.web_search_tool else False
    )


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
        
        # 檢查歷史記錄（簡化版本）
        has_history = False
        preferred_category = None
        
        message = "用戶驗證成功"
        
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


@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(
    request: UserQueryRequest,
    background_tasks: BackgroundTasks,
    manager: ApplicationManager = Depends(get_app_manager),
    _: None = Depends(validate_system_ready)
) -> UserQueryResponse:
    """
    處理用戶查詢
    
    此端點使用核心 RAG Pipeline 處理用戶查詢，並整合推薦功能。
    """
    start_time = datetime.now()
    
    try:
        user_id = request.user_id
        query = request.query
        session_id = request.session_id
        
        logger.info(f"處理用戶查詢: {user_id} - {query}")
        
        # 使用核心 RAG Pipeline 處理查詢
        if manager.rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG Pipeline 未初始化")
        
        # 使用核心 RAG Pipeline 處理
        rag_response = await manager.rag_pipeline.process_query(
            query=query,
            user_id=user_id
        )
        
        # 獲取推薦項目
        recommendations = await _get_recommendations(query, manager)
        
        # 計算處理時間
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 記錄歷史（背景任務）
        background_tasks.add_task(
            _log_query_history,
            user_id, session_id, query, rag_response.content, 
            rag_response.confidence
        )
        
        return UserQueryResponse(
            user_id=user_id,
            query=query,
            response=rag_response.content,
            category=rag_response.metadata.get("category", "其他"),
            confidence=rag_response.confidence,
            recommendations=recommendations,
            reasoning=f"使用 {rag_response.level_used} 層級處理",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")


async def _get_recommendations(query: str, manager: ApplicationManager) -> List[Dict[str, Any]]:
    """獲取推薦項目"""
    if manager.vector_search_tool is None:
        return []
    
    try:
        # 使用統一向量搜尋工具
        search_results = await manager.vector_search_tool.search(query, top_k=3)
        
        # 轉換為字典格式
        recommendations = []
        for result in search_results.get("combined_results", [])[:3]:
            recommendations.append({
                "id": result.get("id", ""),
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "category": result.get("category", ""),
                "tags": result.get("tags", []),
                "score": result.get("score", 0.0),
                "source": result.get("source", "")
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"獲取推薦失敗: {str(e)}")
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
        # 簡化的歷史記錄（實際應用中應使用資料庫）
        logger.info(f"記錄查詢歷史: {user_id} - {confidence}")
    except Exception as e:
        logger.error(f"記錄歷史失敗: {str(e)}")


@app.get("/api/v1/system-info", response_model=SystemInfoResponse)
async def get_system_info(manager: ApplicationManager = Depends(get_app_manager)) -> SystemInfoResponse:
    """獲取系統資訊"""
    status = manager.get_system_status()
    
    # 獲取向量搜尋統計
    vector_stats = {}
    if manager.vector_search_tool:
        vector_stats = manager.vector_search_tool.get_statistics()
    
    return SystemInfoResponse(
        version=status.version,
        timestamp=status.timestamp,
        environment=manager.config.environment,
        debug=manager.config.debug,
        components=status.components,
        features=[
            "核心 RAG Pipeline 整合",
            "統一向量搜尋",
            "用戶 ID 管理",
            "REST API 介面"
        ],
        configuration={
            "app_title": manager.app_config.title,
            "app_version": manager.app_config.version,
            "supported_categories": ["商業", "教育"]
        },
        statistics={
            "vector_search_stats": vector_stats
        }
    )


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