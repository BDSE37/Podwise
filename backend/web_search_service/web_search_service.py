#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search Service - FastAPI 應用程式

提供網路搜尋 API 端點，整合到 RAG Pipeline 的 fallback 機制中。

Author: Podwise Team
License: MIT
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加專案路徑
sys.path.append(os.path.dirname(__file__))

try:
    from rag_pipeline.tools.web_search_tool import WebSearchExpert, SearchRequest, SearchResponse
    from core.service_manager import WebSearchService
except ImportError as e:
    print(f"匯入錯誤: {e}")
    sys.exit(1)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用程式
app = FastAPI(
    title="Web Search Service",
    description="提供基於 OpenAI API 的智能網路搜尋服務",
    version="1.0.0"
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


# Pydantic 模型
class SearchRequestModel(BaseModel):
    """搜尋請求模型"""
    query: str = Field(..., description="搜尋查詢")
    max_results: int = Field(3, description="最大結果數量", ge=1, le=10)
    language: str = Field("zh-TW", description="搜尋語言")
    search_type: str = Field("web", description="搜尋類型")
    include_summary: bool = Field(True, description="是否包含摘要")


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


# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    global web_search_service
    
    try:
        logger.info("正在初始化 Web Search Service...")
        web_search_service = WebSearchService()
        
        # 初始化服務
        success = await web_search_service.initialize()
        if success:
            logger.info("Web Search Service 初始化成功")
        else:
            logger.error("Web Search Service 初始化失敗")
            
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
        "version": "1.0.0",
        "status": "running"
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
        
    except Exception as e:
        logger.error(f"搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@app.post("/search/simple")
async def simple_search(query: str, max_results: int = 3):
    """簡化的搜尋端點"""
    try:
        response = await search(SearchRequestModel(
            query=query,
            max_results=max_results
        ))
        return response
    except Exception as e:
        logger.error(f"簡化搜尋失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")


@app.get("/info")
async def get_service_info():
    """獲取服務資訊"""
    return {
        "service_name": "Web Search Service",
        "version": "1.0.0",
        "description": "基於 OpenAI API 的智能網路搜尋服務",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "simple_search": "/search/simple",
            "info": "/info"
        },
        "features": [
            "多語言搜尋支援",
            "智能摘要生成",
            "信心度評估",
            "OpenAI API 整合"
        ]
    }


# 錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理"""
    logger.error(f"全域異常: {exc}")
    return {
        "error": "內部伺服器錯誤",
        "detail": str(exc),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # 從環境變數獲取配置
    host = os.getenv("WEB_SEARCH_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_SEARCH_PORT", "8006"))
    reload = os.getenv("WEB_SEARCH_RELOAD", "false").lower() == "true"
    
    logger.info(f"啟動 Web Search Service 於 {host}:{port}")
    
    uvicorn.run(
        "web_search_service:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 