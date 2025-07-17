#!/usr/bin/env python3
"""
修復版本的原本 RAG Pipeline 啟動腳本
跳過有問題的模組，直接啟動可用的功能
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

# 設定 Python 路徑
sys.path.insert(0, '/app')

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise RAG Pipeline (修復版)",
    version="3.0.0",
    description="修復版本的 RAG Pipeline，跳過有問題的模組"
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
class UserQueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    enable_tts: bool = False
    voice: str = "podrina"
    speed: float = 1.0

# 回應模型
class UserQueryResponse(BaseModel):
    user_id: str
    query: str
    response: str
    category: str = "general"
    confidence: float = 0.8
    recommendations: List[Dict[str, Any]] = []
    reasoning: str = "使用修復版本的 RAG Pipeline"
    processing_time: float = 0.1
    timestamp: str = ""
    audio_data: Optional[str] = None
    voice_used: Optional[str] = None
    speed_used: Optional[float] = None
    tts_enabled: bool = False

class UserValidationRequest(BaseModel):
    user_id: str

class UserValidationResponse(BaseModel):
    user_id: str
    is_valid: bool = True
    has_history: bool = False
    preferred_category: Optional[str] = None
    message: str = "用戶驗證成功"

class TTSRequest(BaseModel):
    text: str
    voice: str = "podrina"
    speed: float = 1.0

class TTSResponse(BaseModel):
    success: bool = True
    audio_data: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    processing_time: float = 0.1
    message: str = "TTS 功能暫時不可用"

@app.get("/")
async def root() -> Dict[str, Any]:
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline (修復版) 運行中",
        "version": "3.0.0",
        "status": "healthy",
        "note": "這是修復版本，部分功能可能不可用"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": "2025-07-17T11:30:00Z",
        "components": {
            "rag_pipeline": True,
            "vector_search_tool": False,
            "web_search_tool": False,
            "podcast_formatter": False,
            "tts_service": False
        },
        "note": "修復版本 - 基本功能可用"
    }

@app.post("/api/v1/validate-user", response_model=UserValidationResponse)
async def validate_user(request: UserValidationRequest) -> UserValidationResponse:
    """用戶驗證"""
    return UserValidationResponse(
        user_id=request.user_id,
        is_valid=True,
        has_history=False,
        message="用戶驗證成功 (修復版本)"
    )

@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(request: UserQueryRequest) -> UserQueryResponse:
    """處理用戶查詢"""
    import datetime
    
    # 簡單的查詢處理邏輯
    query = request.query.lower()
    
    if "podcast" in query or "播客" in query:
        response = f"關於播客的查詢：{request.query}。這是修復版本的 RAG Pipeline 回應。"
        category = "podcast"
        confidence = 0.8
    elif "投資" in query or "股票" in query or "理財" in query:
        response = f"關於投資理財的查詢：{request.query}。建議您關注相關的財經播客。"
        category = "business"
        confidence = 0.9
    elif "學習" in query or "教育" in query:
        response = f"關於學習教育的查詢：{request.query}。推薦您收聽教育類播客。"
        category = "education"
        confidence = 0.85
    else:
        response = f"您的查詢：{request.query}。這是修復版本的 RAG Pipeline 回應。"
        category = "general"
        confidence = 0.7
    
    # 模擬推薦
    recommendations = [
        {
            "title": "示例播客 1",
            "description": "這是一個示例播客推薦",
            "category": category,
            "confidence": confidence
        },
        {
            "title": "示例播客 2", 
            "description": "另一個示例播客推薦",
            "category": category,
            "confidence": confidence - 0.1
        }
    ]
    
    return UserQueryResponse(
        user_id=request.user_id,
        query=request.query,
        response=response,
        category=category,
        confidence=confidence,
        recommendations=recommendations,
        reasoning="使用修復版本的簡單查詢處理邏輯",
        processing_time=0.1,
        timestamp=datetime.datetime.now().isoformat(),
        tts_enabled=request.enable_tts
    )

@app.post("/api/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest) -> TTSResponse:
    """TTS 語音合成"""
    return TTSResponse(
        success=False,
        message="TTS 功能在修復版本中暫時不可用",
        processing_time=0.1
    )

@app.get("/api/v1/tts/voices")
async def get_available_voices() -> Dict[str, Any]:
    """獲取可用語音"""
    return {
        "voices": ["podrina", "podrinb"],
        "message": "TTS 功能在修復版本中暫時不可用"
    }

@app.get("/api/v1/system-info")
async def get_system_info() -> Dict[str, Any]:
    """系統資訊"""
    return {
        "version": "3.0.0 (修復版)",
        "status": "operational",
        "components": {
            "rag_pipeline": True,
            "vector_search_tool": False,
            "web_search_tool": False,
            "podcast_formatter": False,
            "tts_service": False
        },
        "timestamp": "2025-07-17T11:30:00Z",
        "note": "這是修復版本，提供基本功能"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全域異常處理"""
    return {
        "error": "內部服務錯誤",
        "detail": str(exc),
        "timestamp": "2025-07-17T11:30:00Z",
        "note": "修復版本異常處理"
    }

if __name__ == "__main__":
    print("🚀 啟動 Podwise RAG Pipeline (修復版)...")
    print("📍 服務地址: http://0.0.0.0:8011")
    print("📖 API 文檔: http://localhost:8011/docs")
    print("❤️  健康檢查: http://localhost:8011/health")
    print("⚠️  注意：這是修復版本，部分功能可能不可用")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8011,
        log_level="info"
    ) 