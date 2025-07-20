#!/usr/bin/env python3
"""
Podwise RAG Pipeline 統一服務

整合所有 RAG Pipeline 功能模組的統一 OOP 介面
提供完整的智能 Podcast 推薦和問答服務

作者: Podwise Team
版本: 4.0.0
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
import httpx
import re

# 設定路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(current_dir, '..'))

# 添加路徑到 Python 路徑
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# 確保 config 目錄在路徑中
config_dir = os.path.join(current_dir, 'config')
if config_dir not in sys.path:
    sys.path.insert(0, config_dir)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 載入環境變數
try:
    from dotenv import load_dotenv
    # 嘗試載入多個可能的 .env 檔案位置
    env_paths = [
        os.path.join(current_dir, '.env'),
        os.path.join(backend_root, '.env'),
        os.path.join(current_dir, '..', '.env'),
        os.path.join(current_dir, '..', '..', '.env')
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"✅ 已載入環境變數檔案: {env_path}")
            break
    else:
        logger.warning("⚠️ 未找到 .env 檔案，使用系統環境變數")
except ImportError:
    logger.warning("⚠️ python-dotenv 未安裝，使用系統環境變數")

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# 導入統一服務管理器
try:
    # 嘗試多種導入方式
    try:
        from core.unified_service_manager import UnifiedServiceManager, ServiceConfig
        from core.data_models import RAGResponse, UserQuery, AgentResponse
        SERVICE_MANAGER_AVAILABLE = True
        logger.info("✅ 統一服務管理器導入成功")
    except ImportError:
        # 如果相對導入失敗，嘗試絕對導入
        from rag_pipeline.core.unified_service_manager import UnifiedServiceManager, ServiceConfig
        from rag_pipeline.core.data_models import RAGResponse, UserQuery, AgentResponse
        SERVICE_MANAGER_AVAILABLE = True
        logger.info("✅ 統一服務管理器導入成功 (絕對路徑)")
except ImportError as e:
    logger.warning(f"統一服務管理器導入失敗: {e}")
    SERVICE_MANAGER_AVAILABLE = False
    UnifiedServiceManager = None
    ServiceConfig = None
    RAGResponse = None
    UserQuery = None
    AgentResponse = None

# ==================== API 模型定義 ====================

class UserQueryRequest(BaseModel):
    query: str = Field(..., description="用戶查詢內容")
    user_id: str = Field(default="Podwise0001", description="用戶ID (格式: PodwiseXXXX)")
    session_id: Optional[str] = Field(None, description="會話ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外元數據")
    enable_tts: bool = Field(default=True, description="是否啟用TTS")
    voice: str = Field(default="podrina", description="語音模型")
    speed: float = Field(default=1.0, description="語音速度")

class UserQueryResponse(BaseModel):
    user_id: str
    query: str
    response: str
    category: str
    confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning: str
    processing_time: float
    timestamp: str
    audio_data: Optional[str] = None
    voice_used: Optional[str] = None
    speed_used: Optional[float] = None
    tts_enabled: bool = True

class TTSRequest(BaseModel):
    text: str = Field(..., description="要合成的文字")
    voice: str = Field(default="podrina", description="語音模型")
    speed: float = Field(default=1.0, description="語音速度")

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    text: Optional[str] = None
    processing_time: float
    message: str = ""

class UserValidationRequest(BaseModel):
    user_id: str = Field(..., description="用戶ID (格式: PodwiseXXXX)")

class UserValidationResponse(BaseModel):
    user_id: str
    is_valid: bool
    has_history: bool
    preferred_category: Optional[str] = None
    message: str = ""

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str

class SystemInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    features: Dict[str, Any]
    config: Dict[str, Any]

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, bool]

# ==================== 統一服務管理器實例 ====================

@dataclass
class PodwiseRAGPipeline:
    """
    Podwise RAG Pipeline 統一服務類別
    
    整合所有 RAG Pipeline 功能模組，提供統一的 OOP 介面
    """
    
    def __init__(self, 
                 enable_monitoring: bool = True,
                 enable_semantic_retrieval: bool = True,
                 enable_chat_history: bool = True,
                 enable_apple_ranking: bool = True,
                 confidence_threshold: float = 0.7):
        """
        初始化 RAG Pipeline
        
        Args:
            enable_monitoring: 是否啟用監控
            enable_semantic_retrieval: 是否啟用語意檢索
            enable_chat_history: 是否啟用聊天歷史記錄
            enable_apple_ranking: 是否啟用 Apple Podcast 排名系統
            confidence_threshold: 信心度閾值
        """
        # 創建服務配置
        if SERVICE_MANAGER_AVAILABLE and ServiceConfig:
            service_config = ServiceConfig(
                enable_monitoring=enable_monitoring,
                enable_semantic_retrieval=enable_semantic_retrieval,
                enable_chat_history=enable_chat_history,
                enable_apple_ranking=enable_apple_ranking,
                confidence_threshold=confidence_threshold
            )
        else:
            service_config = None
        
        # 初始化統一服務管理器
        if SERVICE_MANAGER_AVAILABLE:
            self.service_manager = UnifiedServiceManager(service_config)
            logger.info("✅ 統一服務管理器初始化成功")
        else:
            self.service_manager = None
            logger.warning("⚠️ 統一服務管理器不可用")
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "Podwise0001",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據
            
        Returns:
            RAGResponse: 處理結果
        """
        if not self.service_manager:
            return RAGResponse(
                content="服務管理器不可用",
                confidence=0.0,
                sources=[],
                processing_time=0.0,
                level_used="error",
                metadata={"error": "Service manager not available"}
            )
        
        return await self.service_manager.process_query(query, user_id, session_id, metadata)
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """語音合成（改為 HTTP 請求 TTS 微服務）"""
        url = "http://localhost:8002/synthesize"
        payload = {"文字": text, "語音": voice, "語速": f"{int((speed-1)*100):+d}%"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("成功"):
                        import base64
                        return {
                            "success": True,
                            "audio_data": data.get("音訊檔案"),
                            "text": text,
                            "voice": voice,
                            "speed": speed,
                            "audio_size": len(base64.b64decode(data.get("音訊檔案", ""))) if data.get("音訊檔案") else 0
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("錯誤訊息", "TTS 服務回傳失敗"),
                            "text": text,
                            "voice": voice,
                            "speed": speed
                        }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}",
                        "text": text,
                        "voice": voice,
                        "speed": speed
                    }
        except Exception as e:
            import traceback
            err = f"TTS HTTP 請求異常: {str(e)}\n{traceback.format_exc()}"
            logger.error(err)
            return {
                "success": False,
                "error": err,
                "text": text,
                "voice": voice,
                "speed": speed
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self.service_manager:
            return {
                "status": "unhealthy",
                "error": "Service manager not available",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            health_status = await self.service_manager.health_check()
            return {
                "status": health_status.status,
                "timestamp": health_status.timestamp.isoformat(),
                "components": health_status.components,
                "version": health_status.version,
                "metadata": health_status.metadata
            }
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        if not self.service_manager:
            return {
                "name": "Podwise RAG Pipeline",
                "version": "4.0.0",
                "description": "服務管理器不可用",
                "features": {},
                "config": {}
            }
        
        return self.service_manager.get_system_info()

# ==================== FastAPI 應用程式 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    logger.info("🚀 Podwise RAG Pipeline 服務啟動中...")
    
    # 初始化全域服務管理器
    global rag_pipeline
    rag_pipeline = PodwiseRAGPipeline()
    
    logger.info("✅ Podwise RAG Pipeline 服務啟動完成")
    
    yield
    
    # 關閉時
    logger.info("🛑 Podwise RAG Pipeline 服務關閉中...")

# 創建 FastAPI 應用程式
app = FastAPI(
    title="Podwise RAG Pipeline API",
    description="智能 Podcast 推薦系統 API",
    version="4.0.0",
    lifespan=lifespan
)

# 全域服務管理器實例
rag_pipeline: Optional[PodwiseRAGPipeline] = None

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_rag_pipeline() -> PodwiseRAGPipeline:
    """獲取 RAG Pipeline 實例"""
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline 未初始化")
    return rag_pipeline

# ==================== API 端點 ====================

@app.get("/")
async def root() -> Dict[str, Any]:
    """根端點"""
    return {
        "message": "Podwise RAG Pipeline API",
        "version": "4.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)):
    """健康檢查端點"""
    return await pipeline.health_check()

@app.post("/api/v1/generate-user-id")
async def generate_user_id(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)):
    """生成用戶 ID"""
    import random
    user_id = f"Podwise{random.randint(1, 9999):04d}"
    return {
        "user_id": user_id,
        "message": "用戶 ID 生成成功",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/validate-user")
async def validate_user(
    request: UserValidationRequest,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
):
    """驗證用戶"""
    try:
        # 簡單的用戶 ID 格式驗證
        if not request.user_id.startswith("Podwise"):
            return UserValidationResponse(
                user_id=request.user_id,
                is_valid=False,
                has_history=False,
                message="用戶 ID 格式不正確，應以 'Podwise' 開頭"
            )
        
        # 這裡可以添加更詳細的用戶驗證邏輯
        return UserValidationResponse(
            user_id=request.user_id,
            is_valid=True,
            has_history=False,
            message="用戶驗證成功"
        )
        
    except Exception as e:
        logger.error(f"用戶驗證失敗: {e}")
        return UserValidationResponse(
            user_id=request.user_id,
            is_valid=False,
            has_history=False,
            message=f"用戶驗證失敗: {str(e)}"
        )

@app.post("/api/v1/query", response_model=UserQueryResponse)
async def process_query(
    request: UserQueryRequest,
    background_tasks: BackgroundTasks,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
) -> UserQueryResponse:
    """處理用戶查詢"""
    start_time = datetime.now()
    
    try:
        # 處理查詢
        rag_response = await pipeline.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        # 準備回應
        response = UserQueryResponse(
            user_id=request.user_id,
            query=request.query,
            response=rag_response.content,
            category=rag_response.metadata.get("category", "其他"),
            confidence=rag_response.confidence,
            recommendations=rag_response.metadata.get("recommendations", []),
            reasoning=rag_response.metadata.get("reasoning", ""),
            processing_time=rag_response.processing_time,
            timestamp=datetime.now().isoformat(),
            tts_enabled=request.enable_tts
        )
        
        # 如果需要 TTS，在背景任務中處理
        if request.enable_tts:
            background_tasks.add_task(
                process_tts_background,
                request.query,
                request.voice,
                request.speed,
                response
            )
        
        return response
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

async def process_tts_background(text: str, voice: str, speed: float, response: UserQueryResponse):
    """背景處理 TTS"""
    try:
        pipeline = get_rag_pipeline()
        tts_result = await pipeline.synthesize_speech(text, voice, speed)
        
        if tts_result and tts_result.get("success"):
            response.audio_data = tts_result.get("audio_data")
            response.voice_used = tts_result.get("voice")
            response.speed_used = tts_result.get("speed")
        
    except Exception as e:
        logger.error(f"TTS 背景處理失敗: {e}")

@app.post("/api/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    request: TTSRequest,
    pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)
) -> TTSResponse:
    """語音合成端點"""
    start_time = datetime.now()
    
    try:
        result = await pipeline.synthesize_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result and result.get("success"):
            return TTSResponse(
                success=True,
                audio_data=result.get("audio_data"),
                text=result.get("text"),
                voice=result.get("voice"),
                speed=result.get("speed"),
                processing_time=processing_time,
                message="語音合成成功"
            )
        else:
            return TTSResponse(
                success=False,
                text=result.get("text") if result else request.text,
                voice=result.get("voice") if result else request.voice,
                speed=result.get("speed") if result else request.speed,
                processing_time=processing_time,
                message=result.get("error", "語音合成失敗") if result else "語音合成失敗"
            )
            
    except Exception as e:
        logger.error(f"語音合成失敗: {e}")
        return TTSResponse(
            success=False,
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            processing_time=(datetime.now() - start_time).total_seconds(),
            message=f"語音合成失敗: {str(e)}"
        )

@app.get("/api/v1/tts/voices")
async def get_available_voices(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)) -> Dict[str, Any]:
    """獲取可用語音列表"""
    try:
        # 這裡可以從 TTS 服務獲取可用語音列表
        voices = [
            {"id": "podrina", "name": "Podrina", "language": "zh-TW"},
            {"id": "podri", "name": "Podri", "language": "zh-TW"},
            {"id": "xiaoxiao", "name": "Xiaoxiao", "language": "zh-CN"}
        ]
        
        return {
            "voices": voices,
            "total": len(voices),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")

@app.get("/api/v1/system-info", response_model=SystemInfoResponse)
async def get_system_info(pipeline: PodwiseRAGPipeline = Depends(get_rag_pipeline)) -> SystemInfoResponse:
    """獲取系統資訊"""
    try:
        system_info = pipeline.get_system_info()
        return SystemInfoResponse(
            name=system_info["name"],
            version=system_info["version"],
            description=system_info["description"],
            features=system_info["features"],
            config=system_info["config"]
        )
        
    except Exception as e:
        logger.error(f"獲取系統資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取系統資訊失敗: {str(e)}")

# ==================== 錯誤處理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """全域異常處理器"""
    logger.error(f"全域異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """HTTP 異常處理器"""
    logger.error(f"HTTP 異常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

# ==================== 主函數 ====================

async def main():
    """主函數"""
    import uvicorn
    
    logger.info("🚀 啟動 Podwise RAG Pipeline 服務...")
    
    # 啟動 FastAPI 服務
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    asyncio.run(main()) 