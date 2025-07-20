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
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import PodwiseRAGPipeline, get_rag_pipeline

# 導入工具
try:
    from core.enhanced_vector_search import RAGVectorSearch as UnifiedVectorSearch
except ImportError:
    print("無法導入 enhanced_vector_search，使用備用")
    UnifiedVectorSearch = None

try:
    from tools.web_search_tool import WebSearchExpert as WebSearchTool
except ImportError:
    print("無法導入 web_search_tool，使用備用")
    WebSearchTool = None

try:
    from tools.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult
except ImportError:
    print("無法導入 podcast_formatter，使用備用")
    PodcastFormatter = None
    FormattedPodcast = None
    PodcastRecommendationResult = None

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


# ==================== 應用程式管理器 ====================

class ApplicationManager:
    """應用程式管理器 - 專注於 Web API 功能"""
    
    def __init__(self) -> None:
        """初始化應用程式管理器"""
        self.config = get_config()
        self.app_config = AppConfig()
        
        # 核心 RAG Pipeline（使用 main.py 中的實現）
        self.rag_pipeline: Optional[PodwiseRAGPipeline] = None
        
        # Web API 專用組件
        self.vector_search_tool: Optional[Any] = None
        self.web_search_tool: Optional[Any] = None
        self.podcast_formatter: Optional[Any] = None
        
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
            from core.enhanced_vector_search import RAGSearchConfig
            search_config = RAGSearchConfig(
                top_k=vector_config.get('top_k', 8),
                confidence_threshold=vector_config.get('confidence_threshold', 0.7),
                max_execution_time=vector_config.get('max_execution_time', 25),
                enable_semantic_search=vector_config.get('enable_semantic_search', True),
                enable_tag_matching=vector_config.get('enable_tag_matching', True),
                enable_content_cleaning=vector_config.get('enable_content_cleaning', True),
                enable_recommendation_enhancement=vector_config.get('enable_recommendation_enhancement', True)
            )
            self.vector_search_tool = UnifiedVectorSearch(search_config)
            logger.info("✅ 統一向量搜尋工具初始化完成")
            
            # 初始化 Web 搜尋工具
            if WebSearchTool:
            self.web_search_tool = WebSearchTool()
                logger.info("✅ Web 搜尋工具初始化完成")
            
            # 初始化 Podcast 格式化工具
            if PodcastFormatter:
            self.podcast_formatter = PodcastFormatter()
            logger.info("✅ Podcast 格式化工具初始化完成")
            
            self._is_initialized = True
            logger.info("🎉 所有組件初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            raise
    
    async def cleanup(self) -> None:
        """清理資源"""
        try:
            if self.rag_pipeline:
                await self.rag_pipeline.cleanup()
            logger.info("✅ 資源清理完成")
        except Exception as e:
            logger.error(f"❌ 清理失敗: {e}")
    
    def is_ready(self) -> bool:
        """檢查是否準備就緒"""
        return self._is_initialized and self.rag_pipeline is not None


# ==================== 配置類別 ====================

@dataclass
class AppConfig:
    """應用程式配置"""
    host: str = "0.0.0.0"
    port: int = 8012
    debug: bool = False
    title: str = "Podwise RAG Pipeline API"
    version: str = "3.0.0"
    description: str = "Podwise RAG Pipeline REST API"


# ==================== FastAPI 應用程式 ====================

# 應用程式管理器實例
app_manager = ApplicationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    await app_manager.initialize()
    logger.info("🚀 應用程式啟動完成")
    
    yield
    
    # 關閉時清理
    await app_manager.cleanup()
    logger.info("🛑 應用程式關閉完成")


# 創建 FastAPI 應用程式
app = FastAPI(
    title=app_manager.app_config.title,
    version=app_manager.app_config.version,
    description=app_manager.app_config.description,
    debug=app_manager.app_config.debug,
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


# ==================== API 端點 ====================

@app.get("/", response_model=SystemInfoResponse)
async def root():
    """根端點 - 系統資訊"""
    return SystemInfoResponse(
        service="Podwise RAG Pipeline API",
        version=app_manager.app_config.version,
        status="running",
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康檢查端點"""
    is_healthy = app_manager.is_ready()
    return HealthCheckResponse(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.now().isoformat(),
        services={
            "rag_pipeline": "healthy" if app_manager.rag_pipeline else "unhealthy",
            "vector_search": "healthy" if app_manager.vector_search_tool else "unhealthy",
            "web_search": "healthy" if app_manager.web_search_tool else "unhealthy",
            "podcast_formatter": "healthy" if app_manager.podcast_formatter else "unhealthy"
        }
    )


@app.post("/api/v1/rag/query", response_model=UserQueryResponse)
async def process_query(request: UserQueryRequest):
    """處理用戶查詢"""
    try:
        if not app_manager.is_ready():
            raise HTTPException(status_code=503, detail="服務未準備就緒")
        
        # 處理查詢
        response = await app_manager.rag_pipeline.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        return UserQueryResponse(
            content=response.content,
            confidence=response.confidence,
            sources=response.sources,
            processing_time=response.processing_time,
            level_used=response.level_used,
            metadata=response.metadata,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理失敗: {str(e)}")


@app.post("/api/v1/user/validate", response_model=UserValidationResponse)
async def validate_user(request: UserValidationRequest):
    """驗證用戶"""
    try:
        if not app_manager.is_ready():
            raise HTTPException(status_code=503, detail="服務未準備就緒")
        
        # 驗證用戶（這裡可以添加實際的驗證邏輯）
        is_valid = True  # 暫時設為 True
        
        return UserValidationResponse(
            user_id=request.user_id,
            is_valid=is_valid,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"用戶驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")


@app.get("/api/v1/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    """獲取系統資訊"""
    return SystemInfoResponse(
        service="Podwise RAG Pipeline API",
        version=app_manager.app_config.version,
        status="running" if app_manager.is_ready() else "initializing",
        timestamp=datetime.now().isoformat(),
        metadata={
            "config": app_manager.config.get_system_config(),
            "components": {
                "rag_pipeline": "available" if app_manager.rag_pipeline else "unavailable",
                "vector_search": "available" if app_manager.vector_search_tool else "unavailable",
                "web_search": "available" if app_manager.web_search_tool else "unavailable",
                "podcast_formatter": "available" if app_manager.podcast_formatter else "unavailable"
            }
        }
    )


# ==================== 錯誤處理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局異常處理器"""
    logger.error(f"未處理的異常: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="服務內部錯誤",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# ==================== 主程式入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_crewai:app",
        host=app_manager.app_config.host,
        port=app_manager.app_config.port,
        reload=app_manager.app_config.debug,
        log_level="info"
    ) 