#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS API 服務
提供 REST API 端點供其他服務呼叫
"""

import asyncio
import json
import base64
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入 TTS 管理器
try:
    from tts_manager import tts_manager
except ImportError:
    logger.error("無法導入 TTS 管理器")
    tts_manager = None

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise TTS API",
    description="整合語音合成 API 服務",
    version="1.0.0"
)

class SpeechRequest(BaseModel):
    """語音合成請求模型"""
    text: str
    method: str = "auto"
    voice: str = "zh-TW-HsiaoChenNeural"
    speed: float = 1.0
    emotion: str = "neutral"
    pitch: int = 0
    timbre: float = 0.5
    speaker_name: str = "Podri"
    language: str = "zh"

class GPTSoVITSRequest(BaseModel):
    """GPT-SoVITS 語音合成請求模型"""
    text: str
    voice_id: str = "podri"
    emotion: str = "neutral"
    pitch: int = 0
    speed: float = 1.0
    timbre: float = 0.5
    speaker_name: str = "Podri"
    language: str = "zh"

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "Podwise TTS API",
        "version": "1.0.0"
    }

@app.post("/generate_speech")
async def generate_speech(request: SpeechRequest):
    """生成語音端點"""
    try:
        if not tts_manager:
            raise HTTPException(status_code=500, detail="TTS 管理器未初始化")
        
        # 根據方法選擇合成方式
        if request.method == "gpt_sovits":
            audio_data = await tts_manager.synthesize_with_gpt_sovits(
                text=request.text,
                text_language=request.language,
                speed=request.speed
            )
        elif request.method == "edge_tts":
            # 將 speed 轉換為 rate 格式 (例如: 1.0 -> "+0%", 1.5 -> "+50%", 0.8 -> "-20%")
            rate_change = int((request.speed - 1) * 100)
            rate = f"{rate_change:+d}%" if rate_change != 0 else "+0%"
            
            audio_data = await tts_manager.synthesize_with_edge_tts(
                text=request.text,
                voice=request.voice,
                rate=rate
            )
        else:  # auto
            audio_data = await tts_manager.synthesize_speech(
                text=request.text,
                method="auto",
                voice=request.voice,
                speed=request.speed
            )
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=speech.wav"}
            )
        else:
            raise HTTPException(status_code=500, detail="語音合成失敗")
            
    except Exception as e:
        logger.error(f"語音合成錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音合成錯誤: {str(e)}")

@app.post("/generate_gpt_sovits")
async def generate_gpt_sovits_speech(request: GPTSoVITSRequest):
    """GPT-SoVITS 語音合成端點"""
    try:
        if not tts_manager:
            raise HTTPException(status_code=500, detail="TTS 管理器未初始化")
        
        audio_data = await tts_manager.synthesize_with_gpt_sovits(
            text=request.text,
            voice_id=request.voice_id,
            text_language=request.language,
            speed=request.speed
        )
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=gpt_sovits_speech.wav"}
            )
        else:
            raise HTTPException(status_code=500, detail="GPT-SoVITS 語音合成失敗")
            
    except Exception as e:
        logger.error(f"GPT-SoVITS 語音合成錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GPT-SoVITS 語音合成錯誤: {str(e)}")

@app.get("/voices")
async def get_voices():
    """獲取可用語音列表"""
    try:
        if not tts_manager:
            raise HTTPException(status_code=500, detail="TTS 管理器未初始化")
        
        voices = tts_manager.get_available_voices()
        return voices
        
    except Exception as e:
        logger.error(f"獲取語音列表錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表錯誤: {str(e)}")

@app.get("/status")
async def get_status():
    """獲取服務狀態"""
    try:
        if not tts_manager:
            raise HTTPException(status_code=500, detail="TTS 管理器未初始化")
        
        status = await tts_manager.get_service_status()
        return status
        
    except Exception as e:
        logger.error(f"獲取服務狀態錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取服務狀態錯誤: {str(e)}")

if __name__ == "__main__":
    # 啟動 API 服務
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    ) 