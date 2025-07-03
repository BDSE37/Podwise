"""
Podwise 配置服務
提供統一的配置管理和服務發現
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Dict, Any
import asyncio
import os
from pathlib import Path

# 導入現有配置模組
from mongo_config import MongoConfig
from db_config import DatabaseConfig
from stt_config import STTConfig

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Podwise Config Service",
    description="Podwise 配置管理服務",
    version="1.0.0"
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
        "message": "Podwise 配置服務運行中",
        "version": "1.0.0",
        "configs": [
            "MongoDB 配置",
            "PostgreSQL 配置", 
            "STT 配置"
        ]
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/v1/configs/mongo")
async def get_mongo_config():
    """獲取 MongoDB 配置"""
    try:
        mongo_config = MongoConfig()
        return {
            "host": mongo_config.host,
            "port": mongo_config.port,
            "database": mongo_config.database,
            "username": mongo_config.username
        }
    except Exception as e:
        logger.error(f"獲取 MongoDB 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/postgres")
async def get_postgres_config():
    """獲取 PostgreSQL 配置"""
    try:
        db_config = DatabaseConfig()
        return {
            "host": db_config.host,
            "port": db_config.port,
            "database": db_config.database,
            "username": db_config.username
        }
    except Exception as e:
        logger.error(f"獲取 PostgreSQL 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/stt")
async def get_stt_config():
    """獲取 STT 配置"""
    try:
        stt_config = STTConfig()
        return {
            "model_name": stt_config.model_name,
            "device": stt_config.device,
            "language": stt_config.language
        }
    except Exception as e:
        logger.error(f"獲取 STT 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/all")
async def get_all_configs():
    """獲取所有配置"""
    try:
        return {
            "mongo": await get_mongo_config(),
            "postgres": await get_postgres_config(),
            "stt": await get_stt_config()
        }
    except Exception as e:
        logger.error(f"獲取所有配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

if __name__ == "__main__":
    uvicorn.run(
        "config_service:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    ) 