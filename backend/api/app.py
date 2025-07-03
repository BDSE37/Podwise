"""
Podwise API 主應用程式
整合所有後端服務的統一 API 介面
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any
import asyncio

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Podwise API",
    description="語音互動式 Podcast 推薦系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 設定 CORS
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
        "message": "Podwise API 服務運行中",
        "version": "1.0.0",
        "services": [
            "STT (語音轉文字)",
            "TTS (文字轉語音)", 
            "LLM (大語言模型)",
            "RAG (檢索增強生成)",
            "ML Pipeline (機器學習管道)"
        ]
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/v1/services")
async def get_services():
    """獲取所有服務狀態"""
    return {
        "stt": {"status": "running", "port": 8001},
        "tts": {"status": "running", "port": 8003},
        "llm": {"status": "running", "port": 8000},
        "rag_pipeline": {"status": "running", "port": 8005},
        "ml_pipeline": {"status": "running", "port": 8004}
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"全域異常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "內部伺服器錯誤", "detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    ) 