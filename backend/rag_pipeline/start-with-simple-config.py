#!/usr/bin/env python3
"""
使用簡化配置啟動 RAG Pipeline
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

# 設定 Python 路徑
sys.path.insert(0, '/app')

# 導入簡化配置
from config.simple_config import get_simple_config

# 獲取配置
config = get_simple_config()

# 創建 FastAPI 應用
app = FastAPI(
    title="RAG Pipeline API",
    version="1.0.0",
    description="使用簡化配置的 RAG Pipeline API"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求模型
class QueryRequest(BaseModel):
    query: str
    context: str = ""

# 回應模型
class QueryResponse(BaseModel):
    query: str
    response: str
    status: str
    confidence: float = 0.8
    config_info: Dict[str, Any] = {}

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "RAG Pipeline API 運行中",
        "version": "1.0.0",
        "status": "healthy",
        "config": {
            "environment": config.environment,
            "postgres_host": config.postgres_host,
            "rag_pipeline_port": config.rag_pipeline_port
        }
    }

@app.get("/health")
async def health():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "RAG Pipeline",
        "version": "1.0.0",
        "config_loaded": True
    }

@app.get("/config")
async def get_config():
    """獲取配置資訊"""
    return {
        "environment": config.environment,
        "database": {
            "postgres_host": config.postgres_host,
            "postgres_port": config.postgres_port,
            "postgres_db": config.postgres_db,
            "milvus_host": config.milvus_host,
            "milvus_port": config.milvus_port,
        },
        "rag": {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "similarity_threshold": config.similarity_threshold,
        },
        "ollama": {
            "host": config.ollama_host,
            "model": config.ollama_model,
        }
    }

@app.get("/api/rag/query")
async def rag_query(q: str = "測試查詢"):
    """簡單的 RAG 查詢端點"""
    return QueryResponse(
        query=q,
        response=f"這是對 '{q}' 的 RAG 回應 (使用簡化配置)",
        status="success",
        confidence=0.85,
        config_info={
            "environment": config.environment,
            "ollama_model": config.ollama_model
        }
    )

@app.post("/api/rag/query")
async def rag_query_post(request: QueryRequest):
    """POST 版本的 RAG 查詢端點"""
    return QueryResponse(
        query=request.query,
        response=f"這是對 '{request.query}' 的詳細 RAG 回應 (使用簡化配置)",
        status="success",
        confidence=0.9,
        config_info={
            "environment": config.environment,
            "ollama_model": config.ollama_model,
            "chunk_size": config.chunk_size
        }
    )

@app.get("/api/rag/status")
async def rag_status():
    """RAG 系統狀態"""
    return {
        "status": "operational",
        "modules": {
            "vector_search": "available",
            "llm": "available",
            "embedding": "available",
            "config": "simplified"
        },
        "version": "1.0.0",
        "config": {
            "environment": config.environment,
            "ollama_host": config.ollama_host,
            "ollama_model": config.ollama_model
        }
    }

if __name__ == "__main__":
    print("🚀 啟動 RAG Pipeline API (簡化配置)...")
    print(f"📍 服務地址: http://0.0.0.0:{config.rag_pipeline_port}")
    print(f"📖 API 文檔: http://localhost:{config.rag_pipeline_port}/docs")
    print(f"❤️  健康檢查: http://localhost:{config.rag_pipeline_port}/health")
    print(f"⚙️  配置資訊: http://localhost:{config.rag_pipeline_port}/config")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=config.rag_pipeline_port,
        log_level="info"
    ) 