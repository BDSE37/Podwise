#!/usr/bin/env python3
"""
Podwise RAG Pipeline 簡化測試應用程式
用於測試基本功能
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 導入統一的 API 模型
from ..core.api_models import QueryRequest, QueryResponse

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise RAG Pipeline - 簡化測試版",
    description="用於測試基本功能的簡化版本",
    version="1.0.0",
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

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline - 簡化測試版運行中",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "endpoints": {
            "health": "/health",
            "query": "/api/v1/query",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "fastapi": True,
            "uvicorn": True,
            "pydantic": True
        }
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """簡化查詢端點"""
    try:
        logger.info(f"收到查詢: {request.query}")
        
        # 簡單的回應邏輯
        if "你好" in request.query or "hello" in request.query.lower():
            response = "你好！我是 Podwise RAG Pipeline 的簡化測試版本。"
        elif "商業" in request.query:
            response = "這是商業相關的查詢回應。在完整版本中，我會提供更詳細的商業分析。"
        elif "教育" in request.query:
            response = "這是教育相關的查詢回應。在完整版本中，我會提供更詳細的教育資訊。"
        else:
            response = f"收到您的查詢：{request.query}。這是簡化測試版本的回應。"
        
        return QueryResponse(
            query=request.query,
            response=response,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.get("/api/v1/system-info")
async def get_system_info():
    """系統資訊端點"""
    return {
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "development",
        "debug": True,
        "features": [
            "簡化查詢處理",
            "健康檢查",
            "基本錯誤處理"
        ]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"未處理的異常: {str(exc)}")
    return {
        "error": "內部伺服器錯誤",
        "detail": str(exc),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 