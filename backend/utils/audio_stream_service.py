#!/usr/bin/env python3
"""
音檔流服務
提供 MinIO 音檔的直接 URL 和流式播放
"""

import os
import json
import logging
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import tempfile

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PodWise Audio Stream Service", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有方法
    allow_headers=["*"],  # 允許所有標頭
)

class AudioStreamService:
    def __init__(self):
        self.minio_alias = "minio"
        self.minio_host = "192.168.32.66:30090"  # K8s MinIO 服務地址
        self.minio_access_key = "bdse37"
        self.minio_secret_key = "11111111"
    
    def get_direct_url(self, bucket: str, object_key: str) -> str:
        """
        獲取 MinIO 物件的直接 URL
        """
        return f"http://{self.minio_host}/{bucket}/{object_key}"
    
    def get_presigned_url(self, bucket: str, object_key: str, expires: int = 3600) -> Optional[str]:
        """
        獲取 MinIO 物件的預簽名 URL（備用方法）
        """
        try:
            # 使用 mc 命令生成預簽名 URL
            cmd = [
                'mc', 'share', 'download', 
                f'{self.minio_alias}/{bucket}/{object_key}',
                '--expire', f'{expires}s'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析 mc share 輸出，獲取預簽名 URL
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.startswith('Share:'):
                    # 提取 Share URL
                    url = line.replace('Share:', '').strip()
                    return url
            
            logger.warning(f"無法從 mc share 輸出中解析 URL: {result.stdout}")
            # 如果預簽名 URL 失敗，返回直接 URL
            return self.get_direct_url(bucket, object_key)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"生成預簽名 URL 失敗: {e}")
            # 返回直接 URL 作為備用
            return self.get_direct_url(bucket, object_key)
        except Exception as e:
            logger.error(f"獲取預簽名 URL 時發生錯誤: {e}")
            # 返回直接 URL 作為備用
            return self.get_direct_url(bucket, object_key)
    
    def stream_audio(self, bucket: str, object_key: str) -> Optional[StreamingResponse]:
        """
        直接流式播放 MinIO 音檔
        """
        try:
            # 使用 mc cat 命令直接讀取音檔內容
            cmd = [
                'mc', 'cat', 
                f'{self.minio_alias}/{bucket}/{object_key}'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            def generate():
                try:
                    while True:
                        chunk = process.stdout.read(8192) if process.stdout else b''  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
                finally:
                    process.terminate()
                    process.wait()
            
            return StreamingResponse(
                generate(),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename={object_key}",
                    "Accept-Ranges": "bytes"
                }
            )
            
        except Exception as e:
            logger.error(f"流式播放音檔失敗: {e}")
            return None

# 創建服務實例
audio_service = AudioStreamService()

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "audio-stream-service",
        "version": "1.0.0"
    }

@app.post("/api/audio/presigned-url")
async def get_audio_presigned_url(request: Dict):
    """
    獲取音檔的預簽名 URL
    """
    try:
        rss_id = request.get('rss_id')
        episode_title = request.get('episode_title')
        category = request.get('category', 'business')
        
        if not rss_id or not episode_title:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        # 根據類別選擇資料夾
        folder_map = {
            "business": "business-one-min-audio",
            "education": "education-one-min-audio"
        }
        bucket = folder_map.get(category, "business-one-min-audio")
        
        # 構建物件鍵
        object_key = f"RSS_{rss_id}_{episode_title}.mp3"
        
        # 獲取直接 URL（更穩定）
        audio_url = audio_service.get_direct_url(bucket, object_key)
        
        return {
            "success": True,
            "audio_url": audio_url,
            "bucket": bucket,
            "object_key": object_key
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/audio/stream")
async def stream_audio_post(request: Dict):
    """
    POST 方式獲取音檔 URL
    """
    try:
        rss_id = request.get('rss_id')
        episode_title = request.get('episode_title')
        category = request.get('category', 'business')
        
        if not rss_id or not episode_title:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        # 根據類別選擇資料夾
        folder_map = {
            "business": "business-one-min-audio",
            "education": "education-one-min-audio"
        }
        bucket = folder_map.get(category, "business-one-min-audio")
        
        # 構建物件鍵
        object_key = f"RSS_{rss_id}_{episode_title}.mp3"
        
        # 獲取直接 URL
        audio_url = audio_service.get_direct_url(bucket, object_key)
        
        return {
            "success": True,
            "audio_url": audio_url,
            "bucket": bucket,
            "object_key": object_key
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009) 