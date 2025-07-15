#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search Service - 整合到 RAG Pipeline

提供網路搜尋服務，整合到 RAG Pipeline 的 fallback 機制中。
使用 rag_pipeline.tools.web_search_tool 中的 WebSearchExpert。

Author: Podwise Team
License: MIT
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from tools.web_search_tool import WebSearchExpert, SearchRequest, SearchResponse
except ImportError as e:
    print(f"匯入錯誤: {e}")
    sys.exit(1)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服務狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"


class HealthStatus:
    """健康狀態類別"""
    def __init__(self, status: ServiceStatus, service_name: str):
        self.status = status
        self.service_name = service_name
        self.last_check = datetime.now()
        self.details: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None


class WebSearchService:
    """網路搜尋服務類別"""
    
    def __init__(self):
        """初始化服務"""
        self.web_search_expert: Optional[WebSearchExpert] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """初始化服務"""
        try:
            logger.info("正在初始化 Web Search Service...")
            
            # 初始化 WebSearchExpert
            self.web_search_expert = WebSearchExpert()
            success = await self.web_search_expert.initialize()
            
            if success:
                self._initialized = True
                logger.info("Web Search Service 初始化成功")
                return True
            else:
                logger.error("Web Search Service 初始化失敗")
                return False
                
        except Exception as e:
            logger.error(f"Web Search Service 初始化失敗: {e}")
            return False
    
    async def search(self, query: str, max_results: int = 3, 
                    language: str = "zh-TW") -> SearchResponse:
        """
        執行網路搜尋
        
        Args:
            query: 搜尋查詢
            max_results: 最大結果數量
            language: 搜尋語言
            
        Returns:
            搜尋回應
        """
        if not self._initialized or not self.web_search_expert:
            raise HTTPException(status_code=503, detail="服務未初始化")
        
        try:
            # 建立搜尋請求
            request = SearchRequest(
                query=query,
                max_results=max_results,
                language=language
            )
            
            # 執行搜尋
            response = await self.web_search_expert.search(request)
            return response
            
        except Exception as e:
            logger.error(f"搜尋失敗: {e}")
            raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")
    
    async def health_check(self) -> HealthStatus:
        """健康檢查"""
        try:
            if not self._initialized or not self.web_search_expert:
                return HealthStatus(ServiceStatus.ERROR, "Web Search Service")
            
            # 執行健康檢查
            health_details = await self.web_search_expert.health_check()
            
            if health_details.get("status") == "healthy":
                return HealthStatus(ServiceStatus.HEALTHY, "Web Search Service")
            else:
                return HealthStatus(ServiceStatus.DEGRADED, "Web Search Service")
                
        except Exception as e:
            health_status = HealthStatus(ServiceStatus.ERROR, "Web Search Service")
            health_status.error_message = str(e)
            return health_status
    
    async def cleanup(self) -> bool:
        """清理資源"""
        try:
            if self.web_search_expert:
                await self.web_search_expert.cleanup()
            return True
        except Exception as e:
            logger.error(f"清理失敗: {e}")
            return False


# Pydantic 模型
class SearchRequestModel(BaseModel):
    """搜尋請求模型"""
    query: str = Field(..., description="搜尋查詢")
    max_results: int = Field(3, description="最大結果數量", ge=1, le=10)
    language: str = Field("zh-TW", description="搜尋語言")


class SearchResultModel(BaseModel):
    """搜尋結果模型"""
    title: str
    url: str
    snippet: str
    source: str
    confidence: float
    timestamp: str


class SearchResponseModel(BaseModel):
    """搜尋回應模型"""
    query: str
    results: List[SearchResultModel]
    summary: Optional[str] = None
    total_results: int
    processing_time: float
    confidence: float
    source: str


class HealthResponseModel(BaseModel):
    """健康檢查回應模型"""
    status: str
    service_name: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# 建立 FastAPI 應用程式
app = FastAPI(
    title="Web Search Service",
    description="提供基於 OpenAI API 的智能網路搜尋服務，整合到 RAG Pipeline",
    version="2.0.0"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全域服務實例
web_search_service: Optional[WebSearchService] = None


# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    global web_search_service
    
    try:
        web_search_service = WebSearchService()
        success = await web_search_service.initialize()
        
        if not success:
            logger.error("Web Search Service 啟動失敗")
            
    except Exception as e:
        logger.error(f"啟動事件失敗: {e}")


# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉事件"""
    global web_search_service
    
    try:
        if web_search_service:
            await web_search_service.cleanup()
            logger.info("Web Search Service 已清理")
    except Exception as e:
        logger.error(f"關閉事件失敗: {e}")


# API 端點
@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {
        "service": "Web Search Service",
        "version": "2.0.0",
        "status": "running",
        "integration": "RAG Pipeline"
    }


@app.get("/health", response_model=HealthResponseModel)
async def health_check():
    """健康檢查端點"""
    global web_search_service
    
    try:
        if not web_search_service:
            return HealthResponseModel(
                status="error",
                service_name="Web Search Service",
                timestamp=datetime.now().isoformat(),
                error_message="服務未初始化"
            )
        
        health = await web_search_service.health_check()
        
        return HealthResponseModel(
            status=health.status.value,
            service_name=health.service_name,
            timestamp=health.last_check.isoformat(),
            details=health.details,
            error_message=health.error_message
        )
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return HealthResponseModel(
            status="error",
            service_name="Web Search Service",
            timestamp=datetime.now().isoformat(),
            error_message=str(e)
        )


@app.post("/search", response_model=SearchResponseModel)
async def search(request: SearchRequestModel):
    """執行網路搜尋"""
    global web_search_service
    
    try:
        if not web_search_service:
            raise HTTPException(status_code=503, detail="Web Search Service 未初始化")
        
        # 執行搜尋
        response = await web_search_service.search(
            query=request.query,
            max_results=request.max_results,
            language=request.language
        )
        
        # 轉換結果格式
        results = []
        for result in response.results:
            results.append(SearchResultModel(
                title=result.title,
                url=result.url,
                snippet=result.snippet,
                source=result.source,
                confidence=result.confidence,
                timestamp=result.timestamp.isoformat()
            ))
        
        return SearchResponseModel(
            query=response.query,
            results=results,
            summary=response.summary,
            total_results=response.total_results,
            processing_time=response.processing_time,
            confidence=response.confidence,
            source=response.source
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@app.post("/search/simple")
async def simple_search(query: str, max_results: int = 3):
    """簡化搜尋端點"""
    global web_search_service
    
    try:
        if not web_search_service:
            raise HTTPException(status_code=503, detail="Web Search Service 未初始化")
        
        response = await web_search_service.search(query, max_results)
        return {
            "query": response.query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet
                }
                for r in response.results
            ],
            "summary": response.summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"簡化搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@app.get("/info")
async def get_service_info():
    """取得服務資訊"""
    return {
        "service": "Web Search Service",
        "version": "2.0.0",
        "description": "整合到 RAG Pipeline 的網路搜尋服務",
        "features": [
            "OpenAI API 整合",
            "多語言支援",
            "智能摘要生成",
            "信心度評估",
            "RAG Pipeline 整合"
        ],
        "endpoints": [
            "GET / - 服務狀態",
            "GET /health - 健康檢查",
            "POST /search - 完整搜尋",
            "POST /search/simple - 簡化搜尋",
            "GET /info - 服務資訊"
        ]
    }


# 全域異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"未處理的異常: {exc}")
    return {
        "error": "內部伺服器錯誤",
        "message": str(exc),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "web_search_service:app",
        host="0.0.0.0",
        port=8009,
        reload=True,
        log_level="info"
    ) 