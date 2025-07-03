#!/usr/bin/env python3
"""
Podwise RAG Pipeline 漸進式整合應用程式
逐步整合各種組件，確保系統穩定性
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List
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
    title="Podwise RAG Pipeline - 漸進式整合版",
    description="逐步整合各種組件的穩定版本",
    version="1.1.0",
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

# 初始化組件狀態
components_status = {
    "basic_query": True,
    "qwen3_tool": False,
    "deepseek_tool": False,
    "vector_search": False,
    "content_processor": False,
    "confidence_controller": False,
    "chat_history": False
}

def check_component_availability():
    """檢查組件可用性"""
    global components_status
    
    # 檢查 Qwen3 工具
    try:
        from tools.qwen3_tool import Qwen3Tool
        qwen3_tool = Qwen3Tool()
        components_status["qwen3_tool"] = qwen3_tool.is_available()
        logger.info(f"Qwen3 工具: {'可用' if components_status['qwen3_tool'] else '不可用'}")
    except Exception as e:
        logger.warning(f"Qwen3 工具檢查失敗: {e}")
    
    # 檢查 DeepSeek 工具
    try:
        from tools.deepseek_tool import DeepseekTool
        deepseek_tool = DeepseekTool()
        components_status["deepseek_tool"] = deepseek_tool.is_available()
        logger.info(f"DeepSeek 工具: {'可用' if components_status['deepseek_tool'] else '不可用'}")
    except Exception as e:
        logger.warning(f"DeepSeek 工具檢查失敗: {e}")
    
    # 檢查向量搜尋
    try:
        from tools.enhanced_vector_search import EnhancedVectorSearchTool
        vector_tool = EnhancedVectorSearchTool()
        components_status["vector_search"] = True
        logger.info("向量搜尋工具: 可用")
    except Exception as e:
        logger.warning(f"向量搜尋工具檢查失敗: {e}")
    
    # 檢查內容處理器
    try:
        from core.unified_processor import UnifiedContentProcessor
        components_status["content_processor"] = True
        logger.info("內容處理器: 可用")
    except Exception as e:
        logger.warning(f"內容處理器檢查失敗: {e}")
    
    # 檢查信心度控制器
    try:
        from core.confidence_controller import ConfidenceController
        components_status["confidence_controller"] = True
        logger.info("信心度控制器: 可用")
    except Exception as e:
        logger.warning(f"信心度控制器檢查失敗: {e}")

@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    logger.info("🚀 啟動 Podwise RAG Pipeline 漸進式整合版")
    check_component_availability()

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline - 漸進式整合版運行中",
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "components": components_status,
        "endpoints": {
            "health": "/health",
            "query": "/api/v1/query",
            "system_info": "/api/v1/system-info",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": components_status
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """漸進式查詢端點"""
    import time
    start_time = time.time()
    
    try:
        logger.info(f"收到查詢: {request.query}")
        components_used = ["basic_query"]
        
        # 基本回應邏輯
        if "你好" in request.query or "hello" in request.query.lower():
            response = "你好！我是 Podwise RAG Pipeline 的漸進式整合版本。"
        elif "商業" in request.query:
            response = "這是商業相關的查詢回應。"
        elif "教育" in request.query:
            response = "這是教育相關的查詢回應。"
        else:
            response = f"收到您的查詢：{request.query}。"
        
        # 如果啟用進階功能，嘗試使用更多組件
        if request.use_advanced_features:
            # 嘗試使用 Qwen3 工具
            if components_status["qwen3_tool"]:
                try:
                    from tools.qwen3_tool import Qwen3Tool
                    qwen3_tool = Qwen3Tool()
                    qwen3_result = await qwen3_tool.analyze_query(request.query)
                    if qwen3_result["success"]:
                        response += f"\n\n[Qwen3 分析] {qwen3_result['response']}"
                        components_used.append("qwen3_tool")
                except Exception as e:
                    logger.warning(f"Qwen3 工具使用失敗: {e}")
            
            # 嘗試使用 DeepSeek 工具
            if components_status["deepseek_tool"]:
                try:
                    from tools.deepseek_tool import DeepseekTool
                    deepseek_tool = DeepseekTool()
                    deepseek_result = await deepseek_tool.analyze_query(request.query)
                    if deepseek_result["success"]:
                        response += f"\n\n[DeepSeek 分析] {deepseek_result['response']}"
                        components_used.append("deepseek_tool")
                except Exception as e:
                    logger.warning(f"DeepSeek 工具使用失敗: {e}")
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            query=request.query,
            response=response,
            timestamp=datetime.now().isoformat(),
            status="success",
            components_used=components_used,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.get("/api/v1/system-info")
async def get_system_info():
    """系統資訊端點"""
    return {
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "development",
        "debug": True,
        "components": components_status,
        "features": [
            "漸進式查詢處理",
            "組件可用性檢查",
            "多工具整合",
            "健康檢查",
            "基本錯誤處理"
        ]
    }

@app.get("/api/v1/components/status")
async def get_components_status():
    """組件狀態端點"""
    return {
        "components": components_status,
        "available_count": sum(components_status.values()),
        "total_count": len(components_status),
        "timestamp": datetime.now().isoformat()
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
    uvicorn.run(app, host="0.0.0.0", port=8005) 