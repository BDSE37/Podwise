"""
Podwise API 主應用程式
整合所有後端服務的統一 API 介面
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any, Optional
import asyncio
import httpx
import os
from fastapi import FastAPI
from backend.utils.minio_milvus_utils import get_minio_client, get_tags_for_audio, MINIO_URL
import random
import psycopg2

# 導入新的用戶偏好服務
from backend.user_management.main import get_user_manager, UserServiceConfig

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

# 初始化用戶偏好管理器
user_manager = None

def get_user_preference_manager():
    """獲取用戶偏好管理器實例"""
    global user_manager
    if user_manager is None:
        config = UserServiceConfig()
        user_manager = get_user_manager(config)
    return user_manager

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

# PostgreSQL 連線設定
PG_HOST = "postgres.podwise.svc.cluster.local"
PG_PORT = 5432
PG_DB = "podcast"
PG_USER = "bdse37"
PG_PASSWORD = "111111"

def get_podcast_name_from_db(podcast_id):
    try:
        conn = psycopg2.connect(
            dbname=PG_DB, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT
        )
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM podcasts WHERE podcast_id = %s", (int(podcast_id),))
            row = cur.fetchone()
            return row[0] if row else str(podcast_id)
    except Exception as e:
        print(f"PostgreSQL 查詢失敗: {e}")
        return str(podcast_id)
    finally:
        if 'conn' in locals():
            conn.close()

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

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"全域異常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "內部伺服器錯誤", "detail": str(exc)}
    )

@app.get("/api/category-tags")
def get_category_tags(category: str):
    """根據類別獲取標籤"""
    try:
        manager = get_user_preference_manager()
        return manager.get_category_tags(category)
    except Exception as e:
        logger.error(f"獲取類別標籤失敗: {e}")
        return {"success": False, "detail": f"獲取標籤失敗: {e}"}

@app.get("/api/one-minutes-episodes")
def get_one_minutes_episodes(category: str, tag: str):
    """獲取一分鐘節目推薦"""
    try:
        manager = get_user_preference_manager()
        return manager.get_one_minute_episodes(category, tag)
    except Exception as e:
        logger.error(f"獲取節目失敗: {e}")
        return {"success": False, "detail": f"獲取節目失敗: {e}"}

@app.get("/api/user/check/{user_code}")
def check_user_exists(user_code: str):
    """檢查用戶是否存在於資料庫中"""
    try:
        manager = get_user_preference_manager()
        result = manager.check_user_exists(user_code)
        return {"success": True, "exists": result}
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/preferences")
def save_user_preferences(preferences_data: Dict[str, Any]):
    """儲存用戶偏好"""
    try:
        manager = get_user_preference_manager()
        return manager.save_user_preferences(preferences_data)
    except Exception as e:
        logger.error(f"儲存用戶偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/feedback")
def record_feedback(feedback_data: Dict[str, Any]):
    """記錄用戶反饋"""
    try:
        manager = get_user_preference_manager()
        return manager.record_feedback(feedback_data)
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/generate-podwise-id")
def generate_podwise_id():
    """生成新的 Podwise ID"""
    try:
        manager = get_user_preference_manager()
        return manager.generate_podwise_id()
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/audio/presigned-url")
def get_audio_presigned_url(request_data: Dict[str, Any]):
    """獲取音檔的預簽名 URL"""
    try:
        manager = get_user_preference_manager()
        return manager.get_audio_presigned_url(request_data)
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    ) 