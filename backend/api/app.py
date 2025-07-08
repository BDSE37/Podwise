"""
Podwise API 主應用程式
整合所有後端服務的統一 API 介面
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any, Optional
import asyncio
import httpx
import os

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Podwise API",
    description="語音互動式 Podcast 推薦系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服務配置 (本地 pod)
SERVICE_CONFIGS = {
    "stt": {
        "url": os.getenv("STT_URL", "http://localhost:8004"),
        "port": int(os.getenv("STT_PORT", "8004"))
    },
    "tts": {
        "url": os.getenv("TTS_URL", "http://localhost:8003"),
        "port": int(os.getenv("TTS_PORT", "8003"))
    },
    "llm": {
        "url": os.getenv("LLM_URL", "http://localhost:8005"),
        "port": int(os.getenv("LLM_PORT", "8005"))
    },
    "rag_pipeline": {
        "url": os.getenv("RAG_URL", "http://localhost:8001"),
        "port": int(os.getenv("RAG_PORT", "8001"))
    },
    "ml_pipeline": {
        "url": os.getenv("ML_URL", "http://localhost:8002"),
        "port": int(os.getenv("ML_PORT", "8002"))
    },
    "config": {
        "url": os.getenv("CONFIG_SERVICE_URL", "http://localhost:8008"),
        "port": int(os.getenv("CONFIG_SERVICE_PORT", "8008"))
    }
}

async def check_service_health(service_name: str, service_url: str) -> Dict[str, Any]:
    """檢查服務健康狀態"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "unhealthy",
                    "url": service_url,
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "error",
            "url": service_url,
            "error": str(e)
        }

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Podwise API 服務運行中",
        "version": "1.0.0",
        "services": [
            "STT (語音轉文字)",
            "TTS (文字轉語音)", 
            "LLM (大語言模型)",
            "RAG (檢索增強生成)",
            "ML Pipeline (機器學習管道)",
            "Config (配置管理)"
        ],
        "endpoints": {
            "health": "/health",
            "services": "/api/v1/services",
            "configs": "/api/v1/configs",
            "stt": "/api/v1/stt",
            "tts": "/api/v1/tts",
            "llm": "/api/v1/llm",
            "rag": "/api/v1/rag",
            "ml": "/api/v1/ml"
        }
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "service": "podwise-api-gateway"
    }

@app.get("/api/v1/services")
async def get_services():
    """獲取所有服務狀態"""
    health_results = {}
    
    for service_name, config in SERVICE_CONFIGS.items():
        health_results[service_name] = await check_service_health(
            service_name, config["url"]
        )
    
    return {
        "services": health_results,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/v1/configs")
async def get_all_configs():
    """獲取所有配置"""
    try:
        config_url = SERVICE_CONFIGS["config"]["url"]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config_url}/api/v1/configs/all")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="配置服務不可用")
    except Exception as e:
        logger.error(f"獲取配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"配置獲取失敗: {str(e)}")

@app.post("/api/v1/stt/transcribe")
async def transcribe_audio(audio_data: Dict[str, Any]):
    """語音轉文字"""
    try:
        stt_url = SERVICE_CONFIGS["stt"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{stt_url}/transcribe", json=audio_data)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="STT 服務錯誤")
    except Exception as e:
        logger.error(f"語音轉文字失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音轉文字失敗: {str(e)}")

@app.post("/api/v1/tts/synthesize")
async def synthesize_speech(text_data: Dict[str, Any]):
    """文字轉語音"""
    try:
        tts_url = SERVICE_CONFIGS["tts"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{tts_url}/synthesize", json=text_data)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="TTS 服務錯誤")
    except Exception as e:
        logger.error(f"文字轉語音失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文字轉語音失敗: {str(e)}")

@app.post("/api/v1/llm/chat")
async def llm_chat(chat_data: Dict[str, Any]):
    """LLM 聊天"""
    try:
        llm_url = SERVICE_CONFIGS["llm"]["url"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{llm_url}/chat", json=chat_data)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="LLM 服務錯誤")
    except Exception as e:
        logger.error(f"LLM 聊天失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 聊天失敗: {str(e)}")

@app.post("/api/v1/rag/query")
async def rag_query(query_data: Dict[str, Any]):
    """RAG 查詢"""
    try:
        rag_url = SERVICE_CONFIGS["rag_pipeline"]["url"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{rag_url}/query", json=query_data)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="RAG 服務錯誤")
    except Exception as e:
        logger.error(f"RAG 查詢失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG 查詢失敗: {str(e)}")

@app.post("/api/v1/ml/recommend")
async def ml_recommend(recommend_data: Dict[str, Any]):
    """ML 推薦"""
    try:
        ml_url = SERVICE_CONFIGS["ml_pipeline"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{ml_url}/recommend", json=recommend_data)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="ML 服務錯誤")
    except Exception as e:
        logger.error(f"ML 推薦失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ML 推薦失敗: {str(e)}")

@app.post("/api/v1/init/database")
async def init_database():
    """初始化資料庫"""
    try:
        config_url = SERVICE_CONFIGS["config"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{config_url}/api/v1/init/database")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="資料庫初始化失敗")
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"資料庫初始化失敗: {str(e)}")

@app.post("/api/create_user")
async def create_user():
    """創建新用戶並返回 user_code"""
    try:
        import psycopg2
        import os
        
        # 從環境變數獲取資料庫配置，使用 K8s PostgreSQL IP 地址
        db_config = {
            "host": os.getenv("POSTGRES_HOST", "10.233.50.117"),  # 使用 K8s PostgreSQL IP
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "podcast"),
            "user": os.getenv("POSTGRES_USER", "bdse37"),
            "password": os.getenv("POSTGRES_PASSWORD", "111111")
        }
        
        # 連接到 PostgreSQL
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        
        cursor = conn.cursor()
        
        # 插入新用戶記錄，user_code 會自動生成
        insert_query = """
            INSERT INTO users (is_active) 
            VALUES (true)
            RETURNING user_code
        """
        
        cursor.execute(insert_query)
        conn.commit()
        
        # 獲取生成的 user_code
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=500, detail="無法獲取生成的用戶代碼")
        
        user_code = result[0]
        
        cursor.close()
        conn.close()
        
        return {"user_code": user_code}
            
    except ImportError as e:
        logger.error(f"導入 psycopg2 失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="資料庫驅動不可用")
    except Exception as e:
        logger.error(f"創建用戶失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建用戶失敗: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"全域異常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "內部伺服器錯誤", "detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    ) 