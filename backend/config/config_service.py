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
import subprocess

# 導入現有配置模組
from mongo_config import MONGO_CONFIG, MONGO_URI, MONGO_INDEXES
from db_config import POSTGRES_CONFIG, MILVUS_CONFIG, MINIO_CONFIG, DB_CONFIG

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
            "Milvus 配置",
            "MinIO 配置"
        ],
        "features": [
            "配置查詢",
            "資料庫初始化"
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
        return {
            "host": MONGO_CONFIG["host"],
            "port": MONGO_CONFIG["port"],
            "database": MONGO_CONFIG["database"],
            "username": MONGO_CONFIG["username"],
            "collections": MONGO_CONFIG["collections"],
            "indexes": MONGO_INDEXES
        }
    except Exception as e:
        logger.error(f"獲取 MongoDB 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/postgres")
async def get_postgres_config():
    """獲取 PostgreSQL 配置"""
    try:
        return {
            "host": POSTGRES_CONFIG["host"],
            "port": POSTGRES_CONFIG["port"],
            "database": POSTGRES_CONFIG["database"],
            "user": POSTGRES_CONFIG["user"]
        }
    except Exception as e:
        logger.error(f"獲取 PostgreSQL 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/milvus")
async def get_milvus_config():
    """獲取 Milvus 配置"""
    try:
        return {
            "host": MILVUS_CONFIG["host"],
            "port": MILVUS_CONFIG["port"],
            "collection_name": MILVUS_CONFIG["collection_name"],
            "dim": MILVUS_CONFIG["dim"],
            "index_type": MILVUS_CONFIG["index_type"],
            "metric_type": MILVUS_CONFIG["metric_type"]
        }
    except Exception as e:
        logger.error(f"獲取 Milvus 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/minio")
async def get_minio_config():
    """獲取 MinIO 配置"""
    try:
        return {
            "endpoint": MINIO_CONFIG["endpoint"],
            "bucket_name": MINIO_CONFIG["bucket_name"],
            "secure": MINIO_CONFIG["secure"]
        }
    except Exception as e:
        logger.error(f"獲取 MinIO 配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.get("/api/v1/configs/all")
async def get_all_configs():
    """獲取所有配置"""
    try:
        return {
            "mongo": await get_mongo_config(),
            "postgres": await get_postgres_config(),
            "milvus": await get_milvus_config(),
            "minio": await get_minio_config()
        }
    except Exception as e:
        logger.error(f"獲取所有配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="配置獲取失敗")

@app.post("/api/v1/init/database")
async def init_database():
    """初始化資料庫"""
    try:
        # 執行資料庫初始化腳本
        init_script_path = Path(__file__).parent / "init-scripts" / "01-init.sql"
        if not init_script_path.exists():
            raise HTTPException(status_code=404, detail="初始化腳本不存在")
        
        # 使用 psql 執行 SQL 腳本
        cmd = [
            "psql",
            "-h", POSTGRES_CONFIG["host"],
            "-p", str(POSTGRES_CONFIG["port"]),
            "-U", POSTGRES_CONFIG["user"],
            "-d", POSTGRES_CONFIG["database"],
            "-f", str(init_script_path)
        ]
        
        # 設定環境變數
        env = os.environ.copy()
        env["PGPASSWORD"] = POSTGRES_CONFIG["password"]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘超時
        )
        
        if result.returncode != 0:
            logger.error(f"資料庫初始化失敗: {result.stderr}")
            raise HTTPException(
                status_code=500, 
                detail=f"資料庫初始化失敗: {result.stderr}"
            )
        
        logger.info("資料庫初始化成功")
        return {
            "status": "success",
            "message": "資料庫初始化完成",
            "output": result.stdout
        }
        
    except subprocess.TimeoutExpired:
        logger.error("資料庫初始化超時")
        raise HTTPException(status_code=500, detail="資料庫初始化超時")
    except Exception as e:
        logger.error(f"資料庫初始化時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"初始化錯誤: {str(e)}")

@app.get("/api/v1/init/status")
async def get_init_status():
    """獲取初始化狀態"""
    return {
        "init_scripts_available": [
            "00-wait-for-db.sh",
            "01-init.sql"
        ],
        "database_config": {
            "postgres": POSTGRES_CONFIG["database"],
            "mongo": MONGO_CONFIG["database"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "config_service:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    ) 