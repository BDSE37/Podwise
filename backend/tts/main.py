#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri TTS 服務主程式

提供基於 FastAPI 的 RESTful API 服務，支援四種台灣語音合成。

Author: Podri Team
License: MIT
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加 backend 路徑以引用共用工具
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.tts_service import TTSService
from utils.logging_config import get_logger

# 配置日誌
logger = get_logger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="PodWise Podri TTS 語音合成服務",
    description="提供高品質的 Podri TTS 語音合成功能，支援四種台灣語音",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建 TTS 服務實例
tts_service = None


class TTSRequest(BaseModel):
    """TTS 請求模型"""
    文字: str = Field(..., description="要合成的文字內容", min_length=1, max_length=1000)
    語音: Optional[str] = Field(default="podrina", description="語音 ID")
    語速: Optional[str] = Field(default="+0%", description="語速調整，格式如 +10%")
    音量: Optional[str] = Field(default="+0%", description="音量調整，格式如 +5%")
    音調: Optional[str] = Field(default="+0%", description="音調調整，格式如 +2%")


class TTSResponse(BaseModel):
    """TTS 回應模型"""
    成功: bool = Field(..., description="是否成功")
    音訊檔案: Optional[str] = Field(default=None, description="Base64 編碼的音訊檔案")
    錯誤訊息: Optional[str] = Field(default=None, description="錯誤訊息")
    處理時間: Optional[float] = Field(default=None, description="處理時間（秒）")


class VoiceInfo(BaseModel):
    """語音信息模型"""
    id: str = Field(..., description="語音 ID")
    name: str = Field(..., description="語音名稱")
    description: str = Field(..., description="語音描述")


class ServiceStatus(BaseModel):
    """服務狀態模型"""
    podri_tts: Dict[str, Any] = Field(..., description="Podri TTS 狀態")


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global tts_service
    try:
        tts_service = TTSService()
        logger.info("TTS 服務初始化成功")
    except Exception as e:
        logger.error(f"TTS 服務初始化失敗: {e}")
        raise


@app.get("/")
async def root():
    """根路徑 - 服務狀態檢查"""
    return {
        "服務名稱": "PodWise Edge TTS 語音合成服務",
        "狀態": "運行中",
        "版本": "1.0.0",
        "支援語音": ["podrina", "podrisa", "podrino", "podriso"]
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"狀態": "健康", "服務": "Edge TTS"}


@app.get("/voices", response_model=list[VoiceInfo])
async def get_available_voices():
    """獲取可用的語音選項"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        語音列表 = tts_service.get_available_voices()
        return [
            VoiceInfo(
                id=voice["id"],
                name=voice["name"],
                description=voice["description"]
            )
            for voice in 語音列表
        ]
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")


@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """語音合成端點"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        logger.info(f"收到語音合成請求: 文字='{request.文字[:50]}...', 語音='{request.語音}'")
        
        # 執行語音合成
        開始時間 = asyncio.get_event_loop().time()
        音訊數據 = await tts_service.synthesize_speech(
            text=request.文字,
            voice_id=request.語音,
            rate=request.語速,
            volume=request.音量,
            pitch=request.音調
        )
        結束時間 = asyncio.get_event_loop().time()
        處理時間 = 結束時間 - 開始時間
        
        if 音訊數據:
            # 轉換為 Base64
            import base64
            音訊檔案 = base64.b64encode(音訊數據).decode('utf-8')
            
            return TTSResponse(
                成功=True,
                音訊檔案=音訊檔案,
                處理時間=處理時間
            )
        else:
            return TTSResponse(
                成功=False,
                錯誤訊息="語音合成失敗",
                處理時間=處理時間
            )
            
    except ValueError as e:
        logger.error(f"請求參數錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")


@app.get("/voice/{voice_id}", response_model=VoiceInfo)
async def get_voice_info(voice_id: str):
    """獲取特定語音信息"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        語音信息 = tts_service.get_voice_info(voice_id)
        if not 語音信息:
            raise HTTPException(status_code=404, detail=f"語音 {voice_id} 不存在")
        
        return VoiceInfo(
            id=語音信息["id"],
            name=語音信息["name"],
            description=語音信息["description"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取語音信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音信息失敗: {str(e)}")


@app.get("/status", response_model=ServiceStatus)
async def get_service_status():
    """獲取服務狀態"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        狀態 = await tts_service.get_service_status()
        return ServiceStatus(podri_tts=狀態["podri_tts"])
    except Exception as e:
        logger.error(f"獲取服務狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取服務狀態失敗: {str(e)}")


@app.post("/synthesize-stream")
async def synthesize_speech_stream(request: TTSRequest):
    """串流語音合成端點（未來實現）"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        logger.info(f"收到串流語音合成請求: {request.文字[:50]}...")
        
        # 目前返回標準回應，未來可實現真正的串流
        音訊數據 = await tts_service.synthesize_speech(
            text=request.文字,
            voice_id=request.語音,
            rate=request.語速,
            volume=request.音量,
            pitch=request.音調
        )
        
        if 音訊數據:
            import base64
            return {
                "成功": True,
                "音訊檔案": base64.b64encode(音訊數據).decode('utf-8'),
                "訊息": "串流功能開發中，目前返回完整音訊"
            }
        else:
            return {
                "成功": False,
                "錯誤訊息": "語音合成失敗"
            }
        
    except Exception as e:
        logger.error(f"串流語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"串流語音合成失敗: {str(e)}")


def start_server():
    """啟動 TTS 服務"""
    logger.info("正在啟動 Podri TTS 語音合成服務...")
    
    # 配置 uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,  # TTS 服務端口
        log_level="info",
        access_log=True,
        reload=False  # 生產環境中應設為 False
    )

# 添加 API v1 端點以符合前端期望
@app.post("/api/v1/tts/synthesize")
async def api_v1_synthesize(request: TTSRequest):
    """API v1 語音合成端點"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        logger.info(f"收到 API v1 語音合成請求: 文字='{request.文字[:50]}...', 語音='{request.語音}'")
        
        # 執行語音合成
        開始時間 = asyncio.get_event_loop().time()
        音訊數據 = await tts_service.synthesize_speech(
            text=request.文字,
            voice_id=request.語音,
            rate=request.語速,
            volume=request.音量,
            pitch=request.音調
        )
        結束時間 = asyncio.get_event_loop().time()
        處理時間 = 結束時間 - 開始時間
        
        if 音訊數據:
            # 轉換為 Base64
            import base64
            音訊檔案 = base64.b64encode(音訊數據).decode('utf-8')
            
            return {
                "success": True,
                "audio_data": 音訊檔案,
                "voice": request.語音,
                "speed": request.語速,
                "text": request.文字,
                "processing_time": 處理時間
            }
        else:
            return {
                "success": False,
                "error": "語音合成失敗",
                "processing_time": 處理時間
            }
            
    except ValueError as e:
        logger.error(f"請求參數錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")

@app.get("/api/v1/tts/voices")
async def api_v1_voices():
    """API v1 語音列表端點"""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS 服務未初始化")
        
        語音列表 = tts_service.get_available_voices()
        return {
            "success": True,
            "voices": 語音列表,
            "count": len(語音列表)
        }
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")


if __name__ == "__main__":
    start_server()
