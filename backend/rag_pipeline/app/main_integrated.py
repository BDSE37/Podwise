#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主應用程式 - CrewAI + LangChain 多代理人機制
專注於商業和教育類別，優先使用 OpenAI 搜尋再使用 LLM
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 導入統一的 API 模型
from ..core.api_models import QueryRequest, QueryResponse

# 導入核心組件
from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
from core.unified_processor import UnifiedContentProcessor
from core.confidence_controller import ConfidenceController
from core.qwen3_llm_manager import Qwen3LLMManager
from core.chat_history_service import ChatHistoryService
from core.crew_agents import AgentManager

# 導入工具
from tools.enhanced_vector_search import EnhancedVectorSearchTool
from tools.deepseek_tool import DeepseekTool
from tools.qwen3_tool import Qwen3Tool

# 導入配置
from config.integrated_config import get_config

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise RAG Pipeline - CrewAI + LangChain 多代理人機制",
    description="專注於商業和教育類別的智能問答系統，整合 OpenAI 搜尋和 LLM 生成",
    version="2.1.0",
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

# 載入配置
config = get_config()

# 初始化核心組件
rag_pipeline = None
hierarchical_rag = None
content_processor = None
confidence_controller = None
qwen3_manager = None
chat_history_service = None
vector_search_tool = None
deepseek_tool = None
qwen3_tool = None
agent_manager = None

# 檢查 OpenAI 配置
OPENAI_AVAILABLE = config.is_openai_configured()

@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    global rag_pipeline, hierarchical_rag, content_processor, confidence_controller
    global qwen3_manager, chat_history_service, vector_search_tool, deepseek_tool, qwen3_tool, agent_manager
    
    try:
        logger.info("🚀 初始化 Podwise RAG Pipeline...")
        
        # 初始化分層 RAG Pipeline
        hierarchical_rag = HierarchicalRAGPipeline("config/hierarchical_rag_config.yaml")
        logger.info("✅ 分層 RAG Pipeline 初始化完成")
        
        # 初始化統一內容處理器
        content_processor = UnifiedContentProcessor()
        logger.info("✅ 統一內容處理器初始化完成")
        
        # 初始化信心度控制器
        confidence_controller = ConfidenceController()
        logger.info("✅ 信心度控制器初始化完成")
        
        # 初始化 Qwen3 LLM 管理器
        qwen3_manager = Qwen3LLMManager()
        logger.info("✅ Qwen3 LLM 管理器初始化完成")
        
        # 初始化聊天歷史服務
        chat_history_service = ChatHistoryService()
        logger.info("✅ 聊天歷史服務初始化完成")
        
        # 初始化工具
        vector_search_tool = EnhancedVectorSearchTool()
        deepseek_tool = DeepseekTool()
        qwen3_tool = Qwen3Tool()
        logger.info("✅ 工具初始化完成")
        
        # 初始化三層代理人架構
        agent_config = config.get_agent_config()
        agent_manager = AgentManager(agent_config)
        logger.info("✅ 三層代理人架構初始化完成")
        
        # 記錄系統狀態
        logger.info(f"✅ OpenAI 搜尋: {'可用' if OPENAI_AVAILABLE else '不可用'}")
        logger.info("✅ 所有核心組件初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {str(e)}")
        raise

@app.get("/")
async def root():
    """根端點"""
    services = [
        "CrewAI + LangChain 多代理人機制",
        "分層 RAG Pipeline",
        "統一內容處理器",
        "信心度控制器",
        "Qwen3 LLM 管理器",
        "聊天歷史服務",
        "增強向量搜尋",
        "DeepSeek 工具",
        "Qwen3 工具"
    ]
    
    if OPENAI_AVAILABLE:
        services.append("OpenAI 搜尋")
    
    return {
        "message": "Podwise RAG Pipeline - CrewAI + LangChain 多代理人機制運行中",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "openai_available": OPENAI_AVAILABLE,
        "supported_categories": ["商業", "教育"],
        "api_endpoints": {
            "rag_query": "/api/v1/query",
            "vector_search": "/api/v1/vector-search",
            "content_process": "/api/v1/process-content",
            "chat_history": "/api/v1/chat-history",
            "system_status": "/health",
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
            "hierarchical_rag": hierarchical_rag is not None,
            "content_processor": content_processor is not None,
            "confidence_controller": confidence_controller is not None,
            "qwen3_manager": qwen3_manager is not None,
            "chat_history_service": chat_history_service is not None,
            "vector_search_tool": vector_search_tool is not None,
            "deepseek_tool": deepseek_tool is not None,
            "qwen3_tool": qwen3_tool is not None,
            "agent_manager": agent_manager is not None,
            "openai_search": OPENAI_AVAILABLE
        }
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest, background_tasks: BackgroundTasks):
    """智能問答端點 - CrewAI + LangChain 多代理人機制"""
    try:
        if not hierarchical_rag:
            raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
        
        start_time = datetime.now()
        
        # 驗證類別過濾器
        if request.category_filter and request.category_filter not in ["商業", "教育"]:
            raise HTTPException(status_code=400, detail="類別過濾器只能是 '商業' 或 '教育'")
        
        # 執行分層 RAG 查詢
        result = await hierarchical_rag.process_query(request.query)
        
        # 計算處理時間
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 記錄查詢歷史
        if request.user_id:
            background_tasks.add_task(
                chat_history_service.add_query,
                user_id=request.user_id,
                session_id=request.session_id,
                query=request.query,
                response=result["response"],
                confidence=result["confidence"],
                sources=result["sources"]
            )
        
        return QueryResponse(
            query=request.query,
            response=result["response"],
            confidence=result["confidence"],
            sources=result["sources"],
            processing_time=processing_time,
            level_used=result["level_used"],
            category=result["category"],
            metadata=result["metadata"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.post("/api/v1/vector-search")
async def vector_search(query: str, top_k: int = 5, category_filter: Optional[str] = None):
    """向量搜尋端點"""
    try:
        if not vector_search_tool:
            raise HTTPException(status_code=503, detail="向量搜尋工具未初始化")
        
        results = await vector_search_tool.search(query, top_k, category_filter)
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"向量搜尋失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"向量搜尋失敗: {str(e)}")

@app.post("/api/v1/process-content")
async def process_content(content: str, metadata: Dict[str, Any] = None):
    """內容處理端點"""
    try:
        if not content_processor:
            raise HTTPException(status_code=503, detail="內容處理器未初始化")
        
        result = await content_processor.process(content, metadata)
        return {
            "content": content,
            "processed_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"內容處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"內容處理失敗: {str(e)}")

@app.get("/api/v1/chat-history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """取得聊天歷史端點"""
    try:
        if not chat_history_service:
            raise HTTPException(status_code=503, detail="聊天歷史服務未初始化")
        
        history = await chat_history_service.get_history(user_id, limit)
        return {
            "user_id": user_id,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"取得聊天歷史失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得聊天歷史失敗: {str(e)}")

@app.get("/api/v1/system-info")
async def get_system_info():
    """系統資訊端點"""
    return {
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "hierarchical_rag": hierarchical_rag is not None,
            "content_processor": content_processor is not None,
            "confidence_controller": confidence_controller is not None,
            "qwen3_manager": qwen3_manager is not None,
            "chat_history_service": chat_history_service is not None,
            "vector_search_tool": vector_search_tool is not None,
            "deepseek_tool": deepseek_tool is not None,
            "qwen3_tool": qwen3_tool is not None,
            "agent_manager": agent_manager is not None,
            "openai_search": OPENAI_AVAILABLE
        },
        "config": {
            "environment": config.environment,
            "debug": config.debug,
            "log_level": config.log_level
        }
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
    uvicorn.run(app, host="0.0.0.0", port=8004) 