"""
STT 服務主程式
提供語音轉文字功能的 FastAPI 介面
"""

import os
import logging
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
app = FastAPI(title="STT Service")

class TranscriptionRequest(BaseModel):
    """轉錄請求模型"""
    language: str = "zh-TW"
    model_size: str = "base"

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "STT"}

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "zh-TW",
    model_size: str = "base"
):
    """轉錄音頻文件端點"""
    try:
        # 檢查文件類型
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="只支援音頻文件")
        
        # 讀取文件內容
        audio_data = await file.read()
        
        # 這裡應該調用 STT 服務進行轉錄
        # 暫時返回模擬結果
        result = {
            "text": "這是模擬的轉錄結果",
            "confidence": 0.95,
            "language": language,
            "model_used": f"whisper-{model_size}",
            "processing_time": 1.5
        }
        
        return result

    except Exception as e:
        logger.error(f"轉錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
