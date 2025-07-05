"""
STT 服務主程式
使用 Faster Whisper Medium 模型提供語音轉文字功能
"""

import os
import logging
import tempfile
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio

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

# 全域 STT 模型
stt_model = None

class TranscriptionRequest(BaseModel):
    """轉錄請求模型"""
    language: str = "zh"

@app.on_event("startup")
async def startup_event():
    """服務啟動時載入模型"""
    global stt_model
    try:
        from faster_whisper import WhisperModel
        logger.info("正在載入 Faster Whisper Medium 模型...")
        stt_model = WhisperModel("medium", device="cpu", compute_type="float32")
        logger.info("✅ Faster Whisper Medium 模型載入成功")
    except Exception as e:
        logger.error(f"❌ 模型載入失敗: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy", 
        "service": "STT",
        "model": "faster-whisper-medium",
        "model_loaded": stt_model is not None
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "zh"
):
    """轉錄音頻文件端點"""
    global stt_model
    
    if not stt_model:
        raise HTTPException(status_code=503, detail="STT 模型未載入")
    
    try:
        # 檢查文件類型
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="只支援音頻文件")
        
        # 讀取文件內容
        audio_data = await file.read()
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # 使用 Faster Whisper 進行轉錄
            segments, info = stt_model.transcribe(
                temp_file_path,
                language=language,
                task="transcribe"
            )
            
            # 收集轉錄結果
            text_parts = []
            segments_list = []
            
            for segment in segments:
                text_parts.append(segment.text)
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": segment.words if hasattr(segment, 'words') else []
                })
            
            full_text = " ".join(text_parts).strip()
            
            result = {
                "text": full_text,
                "confidence": 0.95,  # Faster Whisper 不直接提供 confidence
                "language": info.language,
                "model_used": "faster-whisper-medium",
                "processing_time": info.duration if hasattr(info, 'duration') else 0,
                "segments": segments_list,
                "language_probability": info.language_probability if hasattr(info, 'language_probability') else 0
            }
            
            return result
            
        finally:
            # 清理臨時文件
            os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"轉錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """獲取可用模型資訊"""
    return {
        "current_model": "faster-whisper-medium",
        "supported_languages": ["zh", "en", "ja", "ko", "th", "vi"],
        "model_size": "1.53GB",
        "device": "cpu"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
