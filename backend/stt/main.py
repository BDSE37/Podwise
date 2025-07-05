"""
STT 服務主程式 (API 入口)
僅負責 API 路由，核心邏輯由 STTService 類別提供
"""

import os
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
from stt_service import STTService

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI
app = FastAPI(title="STT Service - Faster Whisper")

# 全域 STT 服務實例
stt_service: Optional[STTService] = None

class TranscriptionRequest(BaseModel):
    """轉錄請求模型"""
    language: str = "zh"

@app.on_event("startup")
async def startup_event():
    """服務啟動時載入模型"""
    global stt_service
    try:
        stt_service = STTService(
            model_name=os.getenv("WHISPER_MODEL", "medium"),
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "float32")
        )
        logger.info("✅ STTService 啟動完成")
    except Exception as e:
        logger.error(f"❌ STTService 啟動失敗: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """服務關閉時釋放資源"""
    global stt_service
    if stt_service:
        stt_service.close()
        logger.info("STTService 已釋放資源")

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy", 
        "service": "STT",
        "model": stt_service.model_name if stt_service else None,
        "model_loaded": stt_service is not None
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "zh"
):
    """轉錄音頻文件端點"""
    global stt_service
    if not stt_service:
        raise HTTPException(status_code=503, detail="STT 服務未啟動")
    try:
        # 檢查文件類型
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="只支援音頻文件")
        # 讀取文件內容
        audio_data = await file.read()
        # 調用 STTService 進行轉錄
        result = stt_service.transcribe(audio_data, language)
        return result
    except Exception as e:
        logger.error(f"轉錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """獲取可用模型資訊"""
    return {
        "current_model": stt_service.model_name if stt_service else None,
        "supported_languages": ["zh", "en", "ja", "ko", "th", "vi"],
        "model_size": "1.53GB",
        "device": stt_service.device if stt_service else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
