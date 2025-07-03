"""
TTS 語音合成服務主程式
基於 FastAPI 提供 RESTful API 服務
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging

from tts_service import TTSService
from utils.logging_config import get_logger

# 配置日誌
logger = get_logger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="PodWise TTS 語音合成服務",
    description="提供高品質的語音合成功能，支援多種語音選項",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建 TTS 服務實例
tts_service = TTSService()


class TTSRequest(BaseModel):
    """TTS 請求模型"""
    文字: str
    語音: Optional[str] = "podri"
    語速: Optional[float] = 1.0
    音調: Optional[float] = 1.0
    音量: Optional[float] = 1.0


class TTSResponse(BaseModel):
    """TTS 回應模型"""
    成功: bool
    音訊檔案: Optional[str] = None
    錯誤訊息: Optional[str] = None
    處理時間: Optional[float] = None


@app.get("/")
async def 根路徑():
    """根路徑 - 服務狀態檢查"""
    return {
        "服務名稱": "PodWise TTS 語音合成服務",
        "狀態": "運行中",
        "版本": "1.0.0"
    }


@app.get("/health")
async def 健康檢查():
    """健康檢查端點"""
    return {"狀態": "健康", "服務": "TTS"}


@app.get("/voices")
async def 獲取可用語音():
    """獲取可用的語音選項"""
    try:
        語音列表 = tts_service.獲取可用語音()
        return {
            "成功": True,
            "語音列表": 語音列表
        }
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")


@app.post("/synthesize", response_model=TTSResponse)
async def 語音合成(request: TTSRequest):
    """語音合成端點"""
    try:
        logger.info(f"收到語音合成請求: 文字='{request.文字[:50]}...', 語音='{request.語音}', 語速={request.語速}, 音調={request.音調}, 音量={request.音量}")
        logger.info(f"詳細語音參數: 語音ID='{request.語音}', 語音類型='{tts_service._get_voice_type(request.語音 or 'podri')}'")
        
        # 執行語音合成
        開始時間 = asyncio.get_event_loop().time()
        結果 = await tts_service.語音合成(
            text=request.文字,
            語音=request.語音 or "podri",
            語速=request.語速 or 1.0,
            音調=request.音調 or 1.0,
            音量=request.音量 or 1.0
        )
        結束時間 = asyncio.get_event_loop().time()
        處理時間 = 結束時間 - 開始時間
        
        if 結果["成功"]:
            return TTSResponse(
                成功=True,
                音訊檔案=結果["音訊檔案"],
                處理時間=處理時間
            )
        else:
            return TTSResponse(
                成功=False,
                錯誤訊息=結果["錯誤訊息"],
                處理時間=處理時間
            )
            
    except Exception as e:
        logger.error(f"語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")


@app.post("/synthesize-stream")
async def 串流語音合成(request: TTSRequest):
    """串流語音合成端點"""
    try:
        logger.info(f"收到串流語音合成請求: {request.文字[:50]}...")
        
        # 這裡應該實現串流回應
        # 目前返回標準回應
        結果 = await tts_service.語音合成(
            text=request.文字,
            語音=request.語音 or "podri",
            語速=request.語速 or 1.0,
            音調=request.音調 or 1.0,
            音量=request.音量 or 1.0
        )
        
        return 結果
        
    except Exception as e:
        logger.error(f"串流語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"串流語音合成失敗: {str(e)}")


@app.get("/config")
async def 獲取配置():
    """獲取 TTS 配置"""
    try:
        配置 = tts_service.獲取配置()
        return {
            "成功": True,
            "配置": 配置
        }
    except Exception as e:
        logger.error(f"獲取配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")


@app.post("/config")
async def 更新配置(配置: Dict[str, Any]):
    """更新 TTS 配置"""
    try:
        結果 = tts_service.更新配置(配置)
        return {
            "成功": 結果,
            "訊息": "配置更新成功" if 結果 else "配置更新失敗"
        }
    except Exception as e:
        logger.error(f"更新配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")


def 啟動服務():
    """啟動 TTS 服務"""
    logger.info("正在啟動 TTS 語音合成服務...")
    
    # 配置 uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8501,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    啟動服務()
