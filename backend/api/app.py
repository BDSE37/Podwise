#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise API Gateway
統一管理所有微服務的 API 端點
"""

import os
import logging
import httpx
import random
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# 導入 Utils 管理器和資料庫配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.main import get_utils_manager
from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG

# 初始化 Utils 管理器
utils_manager = get_utils_manager()
minio_episode_service = utils_manager.get_minio_episode()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(title="Podwise API Gateway", version="1.0.0")

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服務配置
SERVICE_CONFIGS = {
    "tts": {
        "url": os.getenv("TTS_SERVICE_URL", "http://localhost:8001"),
        "health_endpoint": "/health"
    },
    "stt": {
        "url": os.getenv("STT_SERVICE_URL", "http://localhost:8002"),
        "health_endpoint": "/health"
    },
    "rag_pipeline": {
        "url": os.getenv("RAG_PIPELINE_URL", "http://localhost:8003"),
        "health_endpoint": "/health"
    },
    "ml_pipeline": {
        "url": os.getenv("ML_PIPELINE_URL", "http://localhost:8004"),
        "health_endpoint": "/health"
    },
    "llm": {
        "url": os.getenv("LLM_SERVICE_URL", "http://localhost:8005"),
        "health_endpoint": "/health"
    }
}
# 靜態檔案服務
# 根據運行目錄調整路徑
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

images_dir = os.path.join(project_root, "frontend", "home", "images")
assets_dir = os.path.join(project_root, "frontend", "home", "assets")

app.mount("/images", StaticFiles(directory=images_dir), name="images")
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.mount("/", StaticFiles(directory=os.path.join(project_root, "frontend", "home"), html=True), name="home")

def get_minio_client():
    """獲取 MinIO 客戶端"""
    try:
        from minio import Minio
        return Minio(
            MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=MINIO_CONFIG["secure"]
        )
    except Exception as e:
        logger.error(f"MinIO 客戶端初始化失敗: {e}")
        return None

def get_user_preference_manager():
    """獲取用戶偏好管理器"""
    try:
        import sys
        import os
        
        # 添加 backend 目錄到 Python 路徑
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # 直接導入整合用戶服務
        from user_management.integrated_user_service import user_service
        return user_service
        
    except ImportError as e:
        logger.error(f"導入 user_management.integrated_user_service 失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"用戶偏好管理器初始化失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return None

# 健康檢查函數
async def check_service_health(service_name: str, service_url: str) -> Dict[str, Any]:
    """檢查服務健康狀態"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                return {
                    "service": service_name,
                    "status": "healthy",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "url": service_url,
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "service": service_name,
            "status": "unhealthy",
            "url": service_url,
            "error": str(e)
        }

def get_podcast_name_from_db(podcast_id):
    """從資料庫獲取 podcast 名稱"""
    try:
        import psycopg2
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM podcasts WHERE podcast_id = %s", (podcast_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else f"Podcast_{podcast_id}"
    except Exception as e:
        logger.error(f"獲取 podcast 名稱失敗: {e}")
        return f"Podcast_{podcast_id}"

# 根路徑 - 返回首頁
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回首頁"""
    try:
        index_path = os.path.join(project_root, "frontend", "home", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"讀取首頁失敗: {e}")
        return HTMLResponse(content="<h1>Podwise 首頁載入失敗</h1>", status_code=500)

# 健康檢查端點
@app.get("/health")
async def health_check():
    """API Gateway 健康檢查"""
    return {
        "service": "Podwise API Gateway",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# 獲取所有服務狀態
@app.get("/api/v1/services")
async def get_services():
    """獲取所有微服務的狀態"""
    service_statuses = []
    
    for service_name, config in SERVICE_CONFIGS.items():
        status = await check_service_health(service_name, config["url"])
        service_statuses.append(status)
    
    return {
        "gateway": "healthy",
        "services": service_statuses,
        "timestamp": datetime.now().isoformat()
    }

# 獲取所有配置
@app.get("/api/v1/configs")
async def get_all_configs():
    """獲取所有服務配置"""
    return {
        "service_configs": SERVICE_CONFIGS,
        "timestamp": datetime.now().isoformat()
    }

# STT 轉錄端點
@app.post("/api/v1/stt/transcribe")
async def transcribe_audio(audio_data: Dict[str, Any]):
    """音檔轉錄"""
    try:
        stt_url = SERVICE_CONFIGS["stt"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{stt_url}/transcribe", json=audio_data)
            return response.json()
    except Exception as e:
        logger.error(f"STT 服務調用失敗: {e}")
        raise HTTPException(status_code=500, detail=f"STT 服務錯誤: {str(e)}")

# TTS 合成端點
@app.post("/api/v1/tts/synthesize")
async def synthesize_speech(text_data: Dict[str, Any]):
    """文字轉語音"""
    try:
        tts_url = SERVICE_CONFIGS["tts"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{tts_url}/synthesize", json=text_data)
            return response.json()
    except Exception as e:
        logger.error(f"TTS 服務調用失敗: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 服務錯誤: {str(e)}")

# LLM 聊天端點
@app.post("/api/v1/llm/chat")
async def llm_chat(chat_data: Dict[str, Any]):
    """LLM 聊天"""
    try:
        llm_url = SERVICE_CONFIGS["llm"]["url"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{llm_url}/chat", json=chat_data)
            return response.json()
    except Exception as e:
        logger.error(f"LLM 服務調用失敗: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 服務錯誤: {str(e)}")

# RAG 查詢端點
@app.post("/api/v1/rag/query")
async def rag_query(query_data: Dict[str, Any]):
    """RAG 查詢"""
    try:
        rag_url = SERVICE_CONFIGS["rag_pipeline"]["url"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{rag_url}/api/v1/query", json=query_data)
            return response.json()
    except Exception as e:
        logger.error(f"RAG 服務調用失敗: {e}")
        raise HTTPException(status_code=500, detail=f"RAG 服務錯誤: {str(e)}")

# ML 推薦端點
@app.post("/api/v1/ml/recommend")
async def ml_recommend(recommend_data: Dict[str, Any]):
    """ML 推薦"""
    try:
        ml_url = SERVICE_CONFIGS["ml_pipeline"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{ml_url}/recommend", json=recommend_data)
            return response.json()
    except Exception as e:
        logger.error(f"ML 服務調用失敗: {e}")
        raise HTTPException(status_code=500, detail=f"ML 服務錯誤: {str(e)}")

# 資料庫初始化端點
@app.post("/api/v1/init/database")
async def init_database():
    """初始化資料庫"""
    try:
        # 這裡可以添加資料庫初始化邏輯
        return {"success": True, "message": "資料庫初始化完成"}
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        return {"success": False, "error": str(e)}

# 全域異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理"""
    logger.error(f"全域異常: {exc}")
    return {"success": False, "error": str(exc)}

# 類別標籤端點
@app.get("/api/category-tags/{category}")
async def get_category_tags(category: str):
    """根據類別獲取標籤（使用 MinIO 服務）"""
    try:
        # 使用 MinIO 服務獲取標籤
        tags = minio_episode_service.get_category_tags(category)
        
        return {
            "success": True,
            "tags": tags
        }
    except Exception as e:
        logger.error(f"獲取標籤失敗: {e}")
        # 如果 MinIO 服務失敗，提供預設標籤
        if category == "business":
            tags = ["投資理財", "股票分析", "經濟分析", "財務規劃", "企業管理", "領導力", "科技趨勢", "創新思維"]
        elif category == "education":
            tags = ["學習方法", "教育理念", "知識分享", "個人成長", "心理學", "自我提升", "心靈成長", "教育科技"]
        else:
            tags = ["一般", "知識", "學習", "分享"]
        
        return {"success": False, "tags": tags}

# 一分鐘節目推薦端點 - 整合 MinIO 服務
@app.get("/api/one-minutes-episodes")
async def get_one_minutes_episodes(category: str, tag: str = ""):
    """獲取一分鐘節目推薦（簡化版本，先使用預設資料）"""
    try:
        logger.info(f"開始獲取 {category} 類別的節目")
        
        # 暫時使用預設資料，避免 MinIO 服務超時
        if category == "business":
            episodes = [
                {
                    "podcast_name": "股癌 Gooaye",
                    "episode_title": "投資理財精選",
                    "episode_description": "晦澀金融投資知識直白講，重要海內外時事輕鬆談。",
                    "podcast_image": "images/股癌.png",
                    "audio_url": "audio/sample1.mp3",
                    "episode_id": 1,
                    "rss_id": "RSS_1531106786",
                    "tags": ["投資理財", "股票分析", "市場趨勢", "經濟分析"]
                },
                {
                    "podcast_name": "矽谷輕鬆談",
                    "episode_title": "AI 技術趨勢",
                    "episode_description": "Google 搜尋、AI 技術、科技趨勢都能輕鬆聽懂。",
                    "podcast_image": "images/矽谷輕鬆談.png",
                    "audio_url": "audio/sample2.mp3",
                    "episode_id": 2,
                    "rss_id": "RSS_1493189417",
                    "tags": ["科技趨勢", "人工智慧", "創新思維", "數位轉型"]
                },
                {
                    "podcast_name": "天下學習",
                    "episode_title": "管理思維分享",
                    "episode_description": "訪談頂尖領導者，探索管理思維、教育創新與未來趨勢。",
                    "podcast_image": "images/天下學習.png",
                    "audio_url": "audio/sample3.mp3",
                    "episode_id": 3,
                    "rss_id": "RSS_1590058994",
                    "tags": ["企業管理", "領導力", "學習方法", "個人成長"]
                }
            ]
        elif category == "education":
            episodes = [
                {
                    "podcast_name": "啟點文化一天聽一點",
                    "episode_title": "學習方法論",
                    "episode_description": "探討有效的學習方法和知識獲取技巧。",
                    "podcast_image": "images/知識就是力量.png",
                    "audio_url": "audio/sample4.mp3",
                    "episode_id": 4,
                    "rss_id": "RSS_1488718553",
                    "tags": ["學習方法", "教育理念", "知識分享", "個人成長"]
                },
                {
                    "podcast_name": "文森說書",
                    "episode_title": "未來教育趨勢",
                    "episode_description": "探討科技如何改變教育方式和學習體驗。",
                    "podcast_image": "images/科技新知.png",
                    "audio_url": "audio/sample5.mp3",
                    "episode_id": 5,
                    "rss_id": "RSS_1513786617",
                    "tags": ["教育科技", "未來趨勢", "創新教育", "數位學習"]
                },
                {
                    "podcast_name": "大人的Small Talk",
                    "episode_title": "自我提升指南",
                    "episode_description": "幫助你建立積極心態，實現個人成長目標。",
                    "podcast_image": "images/心靈成長.png",
                    "audio_url": "audio/sample6.mp3",
                    "episode_id": 6,
                    "rss_id": "RSS_1452688611",
                    "tags": ["個人成長", "心理學", "自我提升", "心靈成長"]
                }
            ]
        else:
            episodes = []
        
        # 如果有指定 tag，過濾節目
        if tag and episodes:
            filtered_episodes = []
            for episode in episodes:
                if episode.get("tags") and tag in episode["tags"]:
                    filtered_episodes.append(episode)
            episodes = filtered_episodes
            logger.info(f"根據 tag '{tag}' 過濾後剩餘 {len(episodes)} 個節目")
        
        logger.info(f"最終返回 {len(episodes)} 個節目")
        return {
            "success": True,
            "episodes": episodes
        }
    except Exception as e:
        logger.error(f"獲取節目失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return {"success": False, "detail": f"獲取節目失敗: {e}"}

@app.get("/api/user/check/{user_id}")
def check_user_exists(user_id: str):
    """檢查用戶是否存在於資料庫中"""
    try:
        manager = get_user_preference_manager()
        if manager is None:
            return {"success": False, "error": "用戶偏好管理器未初始化"}
        result = manager.check_user_exists(user_id)
        return {"success": True, "exists": result}
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/preferences")
def save_user_preferences(preferences_data: Dict[str, Any]):
    """儲存用戶偏好"""
    try:
        manager = get_user_preference_manager()
        if manager is None:
            return {"success": False, "error": "用戶偏好管理器未初始化"}
        
        # 從 preferences_data 中提取參數
        user_id = preferences_data.get("user_id")
        main_category = preferences_data.get("main_category")
        sub_category = preferences_data.get("sub_category")
        language = preferences_data.get("language")
        duration_preference = preferences_data.get("duration_preference")
        
        if not user_id or not main_category:
            return {"success": False, "error": "缺少必要參數 user_id 或 main_category"}
        
        return manager.save_user_preferences(
            user_id=str(user_id),
            main_category=str(main_category),
            sub_category=str(sub_category) if sub_category else None,
            language=str(language) if language else None,
            duration_preference=str(duration_preference) if duration_preference else None
        )
    except Exception as e:
        logger.error(f"儲存用戶偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/feedback")
def record_feedback(feedback_data: Dict[str, Any]):
    """記錄用戶反饋"""
    try:
        manager = get_user_preference_manager()
        if manager is None:
            return {"success": False, "error": "用戶偏好管理器未初始化"}
        
        # 從 feedback_data 中提取參數
        user_id = feedback_data.get("user_id")
        podcast_id = feedback_data.get("podcast_id")
        episode_title = feedback_data.get("episode_title")
        like_count = feedback_data.get("like_count", 0)
        preview_play_count = feedback_data.get("preview_play_count", 0)
        
        if not all([user_id, podcast_id, episode_title]):
            return {"success": False, "error": "缺少必要參數"}
        
        return manager.record_user_feedback(
            user_id=str(user_id),
            podcast_id=int(podcast_id) if podcast_id is not None else 0,
            episode_title=str(episode_title),
            like_count=int(like_count) if like_count is not None else 0,
            preview_play_count=int(preview_play_count) if preview_play_count is not None else 0
        )
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/generate-podwise-id")
def generate_podwise_id():
    """生成新的 Podwise ID"""
    try:
        manager = get_user_preference_manager()
        if manager is None:
            return {"success": False, "error": "用戶偏好管理器未初始化"}
        
        user_id = manager.generate_user_id()
        return {
            "success": True,
            "podwise_id": user_id,
            "message": "Podwise ID 生成成功"
        }
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/audio/presigned-url")
async def get_audio_presigned_url(request: Request):
    """獲取音檔的預簽名 URL (由 audio_stream_service 提供)"""
    try:
        data = await request.json()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("http://localhost:8006/api/audio/presigned-url", json=data)
            return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/random-audio")
def get_random_audio(request_data: Dict[str, Any]):
    """獲取隨機音檔"""
    try:
        category = request_data.get("category", "business")
        
        # 根據類別選擇 bucket
        if category == "business":
            bucket_name = "business-one-min-audio"
        elif category == "education":
            bucket_name = "education-one-min-audio"
        else:
            bucket_name = "business-one-min-audio"  # 預設使用商業類別
        
        # 獲取 MinIO 客戶端
        minio_client = get_minio_client()
        
        # 列出 bucket 中的所有音檔
        try:
            if minio_client is None:
                return {"success": False, "message": "MinIO 客戶端未初始化"}
                
            objects = list(minio_client.list_objects(bucket_name, recursive=True))
            audio_files = [obj.object_name for obj in objects if obj.object_name and obj.object_name.endswith('.mp3')]
            
            if not audio_files:
                return {"success": False, "message": f"在 {bucket_name} 中找不到音檔"}
            
            # 隨機選擇一個音檔
            random_audio_file = random.choice(audio_files)
            
            # 生成預簽名 URL (1小時有效期)
            from datetime import timedelta
            presigned_url = minio_client.presigned_get_object(
                bucket_name, random_audio_file, expires=timedelta(hours=1)
            )
            
            # 從檔案名提取資訊
            if random_audio_file:
                filename_parts = random_audio_file.replace('.mp3', '').split('_')
                if len(filename_parts) >= 4:
                    rss_id = filename_parts[2]
                    episode_title = '_'.join(filename_parts[3:])
                else:
                    rss_id = "unknown"
                    episode_title = random_audio_file
            else:
                rss_id = "unknown"
                episode_title = "unknown"
            
            return {
                "success": True, 
                "audio_url": presigned_url,
                "filename": random_audio_file,
                "rss_id": rss_id,
                "episode_title": episode_title,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"列出 MinIO 物件失敗: {str(e)}")
            return {"success": False, "message": f"無法訪問 {bucket_name}: {str(e)}"}
        
    except Exception as e:
        logger.error(f"獲取隨機音檔失敗: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/chat")
async def chat_with_podri(chat_data: Dict[str, Any]):
    """與 Podri 聊天端點"""
    try:
        message = chat_data.get("message", "")
        user_id = chat_data.get("user_id", "default_user")
        enable_tts = chat_data.get("enable_tts", True)
        voice = chat_data.get("voice", "podrina")
        speed = chat_data.get("speed", 1.0)
        
        if not message:
            raise HTTPException(status_code=400, detail="缺少訊息內容")
        
        # 整合 RAG Pipeline 功能
        try:
            # 調用 RAG Pipeline 服務
            rag_url = SERVICE_CONFIGS["rag_pipeline"]["url"]
            async with httpx.AsyncClient(timeout=60.0) as client:
                rag_response = await client.post(f"{rag_url}/api/v1/query", json={
                    "query": message,
                    "user_id": user_id,
                    "session_id": f"session_{user_id}_{int(datetime.now().timestamp())}",
                    "enable_tts": enable_tts,
                    "voice": voice,
                    "speed": speed,
                    "metadata": {
                        "source": "podri_chat",
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    response_text = rag_data.get("response", f"您好！我收到了您的訊息：「{message}」。我正在學習如何更好地回答您的問題。")
                    
                    # 如果 RAG 回應包含音頻數據，直接使用
                    if rag_data.get("audio_data"):
                        audio_data = rag_data.get("audio_data")
                else:
                    # RAG 服務失敗，使用備用回應
                    response_text = f"您好！我收到了您的訊息：「{message}」。我正在學習如何更好地回答您的問題。"
                    
        except Exception as e:
            logger.warning(f"RAG Pipeline 調用失敗: {e}")
            # 使用備用回應
            response_text = f"您好！我收到了您的訊息：「{message}」。我正在學習如何更好地回答您的問題。"
        
        # 如果啟用 TTS，生成語音
        audio_data = None
        if enable_tts:
            try:
                # 調用 TTS 服務
                tts_url = SERVICE_CONFIGS["tts"]["url"]
                async with httpx.AsyncClient(timeout=30.0) as client:
                    tts_response = await client.post(f"{tts_url}/synthesize", json={
                        "文字": response_text,
                        "語音": voice,
                        "語速": f"{speed*100}%",
                        "音量": "+0%",
                        "音調": "+0%"
                    })
                    
                    if tts_response.status_code == 200:
                        tts_result = tts_response.json()
                        if tts_result.get("成功"):
                            audio_data = tts_result.get("音訊檔案")
            except Exception as e:
                logger.warning(f"TTS 服務調用失敗: {e}")
        
        return {
            "success": True,
            "response": response_text,
            "audio_data": audio_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"聊天處理失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "抱歉，處理您的訊息時發生錯誤。"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008) 