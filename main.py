#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主要入口點
直接使用現有的 core 模組
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Podwise RAG Pipeline",
    description="整合 CrewAI、LangChain、LLM 的 Podcast 推薦系統",
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

# 資料模型
class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str
    user_id: Optional[str] = None
    use_hierarchical: bool = False
    enable_langfuse: bool = True

class QueryResponse(BaseModel):
    """查詢回應模型"""
    query: str
    response: str
    confidence: float
    sources: List[str]
    processing_time: float
    model_used: str
    pipeline_type: str
    metadata: Dict[str, Any]
    timestamp: datetime

class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str
    services: Dict[str, str]
    timestamp: datetime

# 全域變數
rag_pipeline = None
rag_chat = None
rag_engine = None

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時初始化服務"""
    global rag_pipeline, rag_chat, rag_engine
    
    logger.info("正在初始化 RAG Pipeline 服務...")
    
    try:
        # 初始化 RAG Pipeline
        from backend.rag_pipeline.core.rag_pipeline_main import UnifiedRAGPipeline
        rag_pipeline = UnifiedRAGPipeline()
        logger.info("✅ RAG Pipeline 初始化成功")
    except Exception as e:
        logger.error(f"❌ RAG Pipeline 初始化失敗: {e}")
    
    try:
        # 初始化 RAG Chat
        from backend.rag_pipeline.core.podwise_rag_chat import get_rag_chat
        rag_chat = get_rag_chat()
        logger.info("✅ RAG Chat 初始化成功")
    except Exception as e:
        logger.error(f"❌ RAG Chat 初始化失敗: {e}")
    
    try:
        # 初始化 RAG Engine
        from backend.rag_pipeline.core.rag_engine import get_rag_engine
        rag_engine = get_rag_engine()
        logger.info("✅ RAG Engine 初始化成功")
    except Exception as e:
        logger.error(f"❌ RAG Engine 初始化失敗: {e}")
    
    logger.info("RAG Pipeline 服務初始化完成")

@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    services = {
        "rag_pipeline": "available" if rag_pipeline else "unavailable",
        "rag_chat": "available" if rag_chat else "unavailable",
        "rag_engine": "available" if rag_engine else "unavailable"
    }
    
    overall_status = "healthy" if all([rag_pipeline, rag_chat, rag_engine]) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.now()
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """處理查詢請求"""
    try:
        logger.info(f"收到查詢請求: {request.query}")
        
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
        
        # 使用現有的 RAG Pipeline 處理查詢
        from backend.rag_pipeline.core.rag_pipeline_main import QueryRequest as CoreQueryRequest
        
        core_request = CoreQueryRequest(
            query=request.query,
            user_id=request.user_id,
            use_hierarchical=request.use_hierarchical,
            enable_langfuse=request.enable_langfuse
        )
        
        core_response = await rag_pipeline.process_query(core_request)
        
        return QueryResponse(
            query=request.query,
            response=core_response.content,
            confidence=core_response.confidence,
            sources=core_response.sources,
            processing_time=core_response.processing_time,
            model_used=core_response.model_used,
            pipeline_type=core_response.pipeline_type,
            metadata=core_response.metadata,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ 查詢處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.post("/chat", response_model=QueryResponse)
async def process_chat(request: QueryRequest):
    """處理聊天請求"""
    try:
        logger.info(f"收到聊天請求: {request.query}")
        
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat 未初始化")
        
        # 使用現有的 RAG Chat 處理聊天
        result = await rag_chat.process_chat_message(
            message=request.query,
            user_id=request.user_id or "default",
            use_crew=True
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return QueryResponse(
            query=request.query,
            response=result["response"],
            confidence=result["confidence"],
            sources=result.get("sources", []),
            processing_time=result.get("processing_time", 0.0),
            model_used=result.get("used_llm", "unknown"),
            pipeline_type="rag_chat",
            metadata={
                "method": result["method"],
                "fallback_used": result.get("fallback_used", False)
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ 聊天處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"聊天處理失敗: {str(e)}")

@app.get("/search")
async def vector_search(query: str, top_k: int = 5):
    """向量搜索端點"""
    try:
        logger.info(f"收到向量搜索請求: {query}")
        
        if not rag_engine:
            raise HTTPException(status_code=503, detail="RAG Engine 未初始化")
        
        # 使用現有的 RAG Engine 進行向量搜索
        results = rag_engine.search(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 向量搜索失敗: {e}")
        raise HTTPException(status_code=500, detail=f"向量搜索失敗: {str(e)}")

@app.get("/stats")
async def get_stats():
    """獲取系統統計資訊"""
    try:
        if rag_pipeline:
            return rag_pipeline.get_stats()
        else:
            return {
                "status": "pipeline_unavailable",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"獲取統計資訊失敗: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/engine/health")
async def engine_health():
    """RAG Engine 健康檢查"""
    try:
        if not rag_engine:
            raise HTTPException(status_code=503, detail="RAG Engine 未初始化")
        
        return rag_engine.health_check()
        
    except Exception as e:
        logger.error(f"Engine 健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Engine 健康檢查失敗: {str(e)}")

@app.get("/chat/stats")
async def chat_stats():
    """RAG Chat 統計資訊"""
    try:
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat 未初始化")
        
        return rag_chat.get_stats()
        
    except Exception as e:
        logger.error(f"Chat 統計資訊獲取失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Chat 統計資訊獲取失敗: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    ) 