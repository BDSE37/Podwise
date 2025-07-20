#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 統一 API Gateway
整合所有前端頁面功能和後端服務的完整反向代理

功能包括：
1. 靜態檔案服務 (index.html, podri.html)
2. 用戶管理 API
3. 音檔管理 API
4. RAG Pipeline 整合
5. TTS/STT 服務
6. 推薦系統
7. 反饋系統

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import httpx
import random
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

# 添加後端路徑
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# 導入後端模組
try:
    from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG
    from core.podwise_service_manager import podwise_service
    # 導入用戶管理服務（混合方案）
    from user_management.integrated_user_service import IntegratedUserService, UserRegistrationRequest, UserPreferenceRequest, CategoryRequest
except ImportError as e:
    print(f"警告: 無法導入某些後端模組: {e}")

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(title="Podwise Unified API Gateway")

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化用戶服務（內部使用 - 混合方案）
try:
    user_service = IntegratedUserService()
    logger.info("✅ 用戶管理服務初始化成功")
except Exception as e:
    logger.warning(f"⚠️ 用戶管理服務初始化失敗: {e}")
    user_service = None

# 路徑配置
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
IMAGES_PATH = FRONTEND_PATH / "images"
ASSETS_PATH = FRONTEND_PATH / "assets"

# 靜態檔案服務
app.mount("/images", StaticFiles(directory=str(IMAGES_PATH)), name="images")
app.mount("/assets", StaticFiles(directory=str(ASSETS_PATH)), name="assets")

# 添加 JavaScript 文件路由
@app.get("/migrate_localStorage.js")
async def migrate_local_storage_js():
    """返回 migrate_localStorage.js 文件"""
    try:
        js_path = Path(__file__).parent.parent / "frontend" / "migrate_localStorage.js"
        if js_path.exists():
            return FileResponse(js_path, media_type="application/javascript")
        else:
            return Response(status_code=404, content="File not found")
    except Exception as e:
        logger.error(f"讀取 migrate_localStorage.js 失敗: {e}")
        return Response(status_code=404, content="File not found")

# 添加 favicon 路由
@app.get("/favicon.ico")
async def favicon():
    """返回 favicon"""
    try:
        favicon_path = ASSETS_PATH / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        else:
            # 如果沒有 favicon 檔案，返回空的回應
            return Response(status_code=204)
    except Exception:
        return Response(status_code=204)

# 服務配置
SERVICE_CONFIGS = {
    "tts": {
        "url": os.getenv("TTS_SERVICE_URL", "http://localhost:8002"),
        "health_endpoint": "/health"
    },
    "stt": {
        "url": os.getenv("STT_SERVICE_URL", "http://localhost:8003"),
        "health_endpoint": "/health"
    },
    "rag": {
        "url": os.getenv("RAG_PIPELINE_URL", "http://localhost:8005"),
        "health_endpoint": "/health"
    },
    "rag_pipeline": {
        "url": os.getenv("RAG_PIPELINE_URL", "http://localhost:8005"),
        "health_endpoint": "/health"
    },
    "ml_pipeline": {
        "url": os.getenv("ML_PIPELINE_URL", "http://localhost:8004"),
        "health_endpoint": "/health"
    },
    "llm": {
        "url": os.getenv("LLM_SERVICE_URL", "http://localhost:8004"),
        "health_endpoint": "/health"
    }
}

# Pydantic 模型
class UserPreferences(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    main_category: str = Field(..., description="主類別")
    sub_category: str = Field("", description="子類別")

class FeedbackData(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    episode_id: Optional[str] = Field(None, description="節目 ID (可以是字串格式)")
    podcast_name: str = Field(..., description="播客名稱")
    episode_title: str = Field(..., description="節目標題")
    rss_id: str = Field(..., description="RSS ID")
    action: str = Field(..., description="操作類型")
    category: str = Field(..., description="類別")

class Step4UserPreferences(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    main_category: str = Field(..., description="主類別")
    selected_episodes: List[Dict[str, Any]] = Field(..., description="選中的節目列表")

class ChatRequest(BaseModel):
    query: str = Field(..., description="查詢內容")
    user_id: str = Field(..., description="用戶 ID")
    session_id: str = Field(..., description="會話 ID")
    enable_tts: bool = Field(True, description="是否啟用 TTS")
    voice: str = Field("podrina", description="語音模型")
    speed: float = Field(1.0, description="語速")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")

class TTSRequest(BaseModel):
    text: str = Field(..., description="要轉換的文字")
    voice: str = Field("podrina", description="語音模型")
    speed: str = Field("+0%", description="語速調整")

class AudioRequest(BaseModel):
    rss_id: str = Field(..., description="RSS ID")
    episode_title: str = Field(..., description="節目標題")
    category: str = Field("business", description="類別")

class RandomAudioRequest(BaseModel):
    category: str = Field("business", description="類別")

class AudioPlayRequest(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    podcast_id: int = Field(..., description="播客 ID")
    episode_title: str = Field(..., description="節目標題")

class HeartLikeRequest(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    podcast_id: int = Field(..., description="播客 ID")
    episode_title: str = Field(..., description="節目標題")

class UserFeedbackRequest(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    podcast_id: int = Field(..., description="播客 ID")
    episode_title: str = Field(..., description="節目標題")
    action: str = Field("preview", description="操作類型: preview, heart_like, both")
    category: str = Field("business", description="類別")

# 工具函數
def get_minio_client():
    """獲取 MinIO 客戶端"""
    try:
        from minio.api import Minio
        return Minio(
            MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=MINIO_CONFIG["secure"]
        )
    except Exception as e:
        logger.error(f"MinIO 客戶端初始化失敗: {e}")
        return None

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

def get_podcast_name_from_db(podcast_id: int) -> str:
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

# ==================== 頁面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回首頁"""
    try:
        index_path = FRONTEND_PATH / "index.html"
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"讀取首頁失敗: {e}")
        return HTMLResponse(content="<h1>Podwise 首頁載入失敗</h1>", status_code=500)

@app.get("/index.html", response_class=HTMLResponse)
async def index_page():
    """返回首頁 (index.html)"""
    try:
        index_path = FRONTEND_PATH / "index.html"
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"讀取首頁失敗: {e}")
        return HTMLResponse(content="<h1>Podwise 首頁載入失敗</h1>", status_code=500)

@app.get("/podri.html", response_class=HTMLResponse)
async def podri_page():
    """返回 Podri 聊天頁面"""
    try:
        podri_path = FRONTEND_PATH / "podri.html"
        with open(podri_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"讀取 Podri 頁面失敗: {e}")
        return HTMLResponse(content="<h1>Podri 頁面載入失敗</h1>", status_code=500)

# ==================== 靜態檔案服務 ====================

@app.get("/assets/{path:path}")
async def serve_assets(path: str):
    """服務前端資源檔案"""
    try:
        file_path = ASSETS_PATH / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="檔案不存在")
    except Exception as e:
        logger.error(f"服務資源檔案失敗: {e}")
        raise HTTPException(status_code=404, detail="檔案不存在")

@app.get("/images/{path:path}")
async def serve_images(path: str):
    """服務圖片檔案"""
    try:
        file_path = IMAGES_PATH / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="檔案不存在")
    except Exception as e:
        logger.error(f"服務圖片檔案失敗: {e}")
        raise HTTPException(status_code=404, detail="檔案不存在")

@app.get("/audio/{path:path}")
async def serve_audio(path: str, category: str = "business"):
    """服務音檔檔案 - 從 MinIO 獲取對應類別的試聽音檔"""
    try:
        # 檢查本地音檔是否為文字檔案
        audio_path = FRONTEND_PATH / "audio" / path
        if audio_path.exists() and audio_path.is_file():
            with open(audio_path, 'rb') as f:
                header = f.read(4)
                if not (header.startswith(b'ID3') or header.startswith(b'\xff\xfb') or header.startswith(b'RIFF')):
                    # 這是文字檔案，需要從 MinIO 獲取真實音檔
                    logger.info(f"本地音檔 {path} 是文字檔案，從 MinIO 獲取對應類別音檔")
                else:
                    # 這是真實音檔，直接返回
                    return FileResponse(audio_path, media_type="audio/mpeg")
        
        # 從 MinIO 獲取對應類別的試聽音檔
        try:
            minio_client = get_minio_client()
            if not minio_client:
                raise HTTPException(status_code=500, detail="MinIO 客戶端未初始化")
            
            # 根據類別選擇 bucket
            bucket_map = {
                "business": "business-one-minutes-audio",
                "education": "education-one-minutes-audio"
            }
            bucket_name = bucket_map.get(category, "business-one-minutes-audio")
            
            # 檢查 bucket 是否存在
            if not minio_client.bucket_exists(bucket_name):
                raise HTTPException(status_code=404, detail=f"Bucket {bucket_name} 不存在")
            
            # 列出 bucket 中的所有音檔
            objects = list(minio_client.list_objects(bucket_name, recursive=True))
            audio_files = [obj.object_name for obj in objects if obj.object_name and obj.object_name.endswith('.mp3')]
            
            if not audio_files:
                raise HTTPException(status_code=404, detail=f"在 {bucket_name} 中找不到音檔")
            
            # 根據請求的檔案名選擇對應的音檔
            filename = path.replace('.mp3', '')
            selected_audio_file = None
            
            if filename.startswith('sample'):
                # 對於 sample 檔案，選擇第一個可用的音檔
                selected_audio_file = audio_files[0]
                logger.info(f"為 sample 檔案選擇音檔: {selected_audio_file}")
            else:
                # 嘗試找到匹配的音檔
                for audio_file in audio_files:
                    if filename in audio_file or audio_file.replace('.mp3', '') == filename:
                        selected_audio_file = audio_file
                        break
                
                # 如果沒有找到匹配的，使用第一個音檔
                if not selected_audio_file:
                    selected_audio_file = audio_files[0]
                    logger.info(f"未找到匹配音檔，使用預設音檔: {selected_audio_file}")
            
            # 生成預簽名 URL
            presigned_url = minio_client.presigned_get_object(
                bucket_name, selected_audio_file, expires=timedelta(hours=1)
            )
            
            logger.info(f"成功獲取音檔: {bucket_name}/{selected_audio_file}")
            
            # 重定向到 MinIO 音檔
            return RedirectResponse(url=presigned_url)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"從 MinIO 獲取音檔失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取音檔失敗: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"服務音檔檔案失敗: {e}")
        raise HTTPException(status_code=404, detail="檔案不存在")

# ==================== 健康檢查 ====================

@app.get("/health")
async def health_check():
    """API Gateway 健康檢查"""
    return {
        "service": "Podwise 統一 API Gateway",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

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

# ==================== 用戶管理 API（混合方案） ====================

# 暴露路由（前端可呼叫）
@app.get("/api/user/check/{user_id}")
def check_user_exists(user_id: str):
    """檢查用戶是否存在"""
    try:
        if user_service:
            exists = user_service.check_user_exists(user_id)
        else:
            exists = podwise_service.check_user_exists(user_id)
        return {
            "success": True,
            "exists": exists,
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"檢查用戶存在性失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/register")
def register_user(request: UserRegistrationRequest):
    """用戶註冊（暴露路由）"""
    try:
        if not user_service:
            return {"success": False, "error": "用戶服務未初始化"}
        
        # 使用 user_service 進行註冊
        result = user_service.register_user(
            username=request.user_id,
            email=None,
            given_name=None,
            family_name=None
        )
        
        # 保存用戶偏好
        if request.selected_episodes:
            user_service.save_user_preferences(
                user_id=result["user_id"],
                main_category=request.category
            )
        
        return {
            "success": True,
            "user_id": result["user_id"],
            "message": "用戶註冊成功"
        }
    except Exception as e:
        logger.error(f"用戶註冊失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/preferences")
def save_user_preferences(request: UserPreferenceRequest):
    """保存用戶偏好（暴露路由）"""
    try:
        if not user_service:
            return {"success": False, "error": "用戶服務未初始化"}
        
        result = user_service.save_user_preferences(
            user_id=request.user_id,
            main_category=request.main_category,
            sub_category=request.sub_category,
            language=request.language,
            duration_preference=request.duration_preference
        )
        
        return result
    except Exception as e:
        logger.error(f"保存用戶偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/heart-like")
def record_user_heart_like(request: UserFeedbackRequest):
    """記錄愛心點擊"""
    try:
        result = podwise_service.record_heart_like(
            user_id=request.user_id,
            podcast_id=request.podcast_id,
            episode_title=request.episode_title
        )
        
        if result["success"]:
            logger.info(f"愛心點擊記錄成功: {request.user_id}, 音檔: RSS_{request.podcast_id}_{request.episode_title}.mp3")
            return {
                "success": True,
                "message": result["message"],
                "audio_filename": f"RSS_{request.podcast_id}_{request.episode_title}.mp3",
                "podcast_id": request.podcast_id,
                "episode_title": request.episode_title
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"記錄愛心點擊失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/feedback")
def record_user_feedback(request: UserFeedbackRequest):
    """記錄用戶反饋（包含 podcast_id 和 episode_title）"""
    try:
        result = podwise_service.record_user_feedback(
            user_id=request.user_id,
            podcast_id=request.podcast_id,
            episode_title=request.episode_title,
            action=request.action
        )
        
        if result["success"]:
            logger.info(f"用戶反饋記錄成功: {request.user_id}, 操作: {request.action}, 音檔: {result.get('audio_filename', 'N/A')}")
            return {
                "success": True,
                "message": result["message"],
                "audio_filename": result.get("audio_filename"),
                "podcast_id": request.podcast_id,
                "episode_title": request.episode_title
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"記錄用戶反饋失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/category/recommendations")
def get_category_recommendations(request: CategoryRequest):
    """獲取類別推薦（暴露路由）"""
    try:
        if not user_service:
            return {"success": False, "error": "用戶服務未初始化"}
        
        recommendations = user_service.get_category_recommendations(
            category=request.category,
            tag=request.tag,
            limit=3
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "category": request.category,
            "tag": request.tag
        }
    except Exception as e:
        logger.error(f"獲取類別推薦失敗: {e}")
        return {"success": False, "error": str(e)}

# 內部功能（不暴露路由，僅供 API Gateway 內部使用）
def _internal_user_validation(user_id: str) -> bool:
    """內部用戶驗證（僅供內部使用）"""
    try:
        if not user_service:
            return False
        return user_service.check_user_exists(user_id)
    except Exception as e:
        logger.error(f"內部用戶驗證失敗: {e}")
        return False

def _internal_get_user_preferences(user_id: str) -> Dict[str, Any]:
    """內部獲取用戶偏好（僅供內部使用）"""
    try:
        if not user_service:
            return {}
        # 這裡可以調用 user_service 的內部方法
        return {"user_id": user_id, "preferences": []}
    except Exception as e:
        logger.error(f"內部獲取用戶偏好失敗: {e}")
        return {}

@app.post("/api/user/preferences-legacy")
def save_user_preferences_legacy(preferences: UserPreferences):
    """保存用戶偏好（舊版 API）"""
    try:
        result = podwise_service.save_user_preferences(
            user_id=preferences.user_id,
            main_category=preferences.main_category,
            sub_category=preferences.sub_category
        )
        
        return result
    except Exception as e:
        logger.error(f"保存用戶偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/generate-podwise-id")
def generate_podwise_id():
    """生成新的 Podwise ID"""
    try:
        user_id = podwise_service.generate_user_id()
        return {
            "success": True,
            "podwise_id": user_id,
            "user_id": user_id,
            "message": "Podwise ID 生成成功"
        }
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== 反饋系統 API ====================

@app.post("/api/feedback")
def record_feedback(feedback: FeedbackData):
    """記錄用戶反饋（支援舊格式和新格式）"""
    try:
        # 從 RSS ID 提取 podcast_id
        podcast_id = 0
        if feedback.rss_id and feedback.rss_id.startswith("RSS_"):
            try:
                podcast_id = int(feedback.rss_id.split("_")[1])
            except (ValueError, IndexError):
                podcast_id = 0
        
        # 使用新的 record_user_feedback 函數
        result = podwise_service.record_user_feedback(
            user_id=feedback.user_id,
            podcast_id=podcast_id,
            episode_title=feedback.episode_title,
            action="heart_like" if feedback.action == "like" else "preview"
        )
        
        if result["success"]:
            logger.info(f"反饋記錄成功: {feedback.user_id}, 操作: {feedback.action}, 音檔: {result.get('audio_filename', 'N/A')}")
            return {
                "success": True,
                "message": result["message"],
                "audio_filename": result.get("audio_filename"),
                "podcast_id": podcast_id,
                "episode_title": feedback.episode_title
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/step4/save-preferences")
def save_step4_preferences(preferences: Step4UserPreferences):
    """保存 Step4 用戶偏好和選中的節目"""
    try:
        # 檢查用戶是否存在，如果不存在則自動創建
        if not podwise_service.check_user_exists(preferences.user_id):
            logger.info(f"用戶 {preferences.user_id} 不存在，自動創建新用戶")
            # 自動創建用戶（如果用戶 ID 格式正確）
            if preferences.user_id.startswith("Podwise"):
                try:
                    # 嘗試從現有用戶 ID 創建新用戶
                    new_user_id = podwise_service.generate_user_id()
                    logger.info(f"自動創建新用戶: {new_user_id}")
                    # 使用新創建的用戶 ID
                    preferences.user_id = new_user_id
                except Exception as create_error:
                    logger.error(f"自動創建用戶失敗: {create_error}")
                    return {"success": False, "error": "無法創建用戶，請重新生成用戶 ID"}
            else:
                return {"success": False, "error": "用戶不存在，請先創建用戶 ID"}
        
        result = podwise_service.save_step4_user_preferences(
            preferences.user_id,
            preferences.main_category,
            preferences.selected_episodes
        )
        return result
    except Exception as e:
        logger.error(f"保存 Step4 偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/user/context/{user_id}")
def get_user_context(user_id: str):
    """獲取用戶上下文資訊（用於 RAG Pipeline）"""
    try:
        context = podwise_service.get_user_context_for_rag(user_id)
        return {
            "success": True,
            "context": context
        }
    except Exception as e:
        logger.error(f"獲取用戶上下文失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== 音檔管理 API ====================

@app.post("/api/audio/presigned-url")
async def get_audio_presigned_url(request: AudioRequest):
    """獲取音檔的預簽名 URL"""
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return {"success": False, "error": "MinIO 客戶端未初始化"}
        
        # 根據類別選擇 bucket
        bucket_map = {
            "business": "business-one-min-audio",
            "education": "education-one-min-audio"
        }
        bucket_name = bucket_map.get(request.category, "business-one-min-audio")
        
        # 使用標準格式：RSS_{rss_id}_{episode_title}.mp3
        filename = f"RSS_{request.rss_id}_{request.episode_title}.mp3"
        
        # 檢查檔案是否存在
        try:
            minio_client.stat_object(bucket_name, filename)
        except Exception as e:
            logger.warning(f"音檔 {filename} 不存在: {e}")
            return {"success": False, "error": "找不到對應的音檔"}
        
        # 生成預簽名 URL
        presigned_url = minio_client.presigned_get_object(
            bucket_name, filename, expires=timedelta(hours=1)
        )
        
        return {
            "success": True,
            "audio_url": presigned_url,
            "filename": filename,
            "bucket": bucket_name
        }
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/random-audio")
def get_random_audio(request: RandomAudioRequest):
    """獲取隨機音檔"""
    try:
        return podwise_service.get_random_audio(request.category)
    except Exception as e:
        logger.error(f"獲取隨機音檔失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== 音檔播放和愛心點擊 API ====================

@app.post("/api/audio/play")
def record_audio_play(request: AudioPlayRequest):
    """記錄音檔播放"""
    try:
        result = podwise_service.record_audio_play(
            user_id=request.user_id,
            podcast_id=request.podcast_id,
            episode_title=request.episode_title
        )
        
        if result["success"]:
            logger.info(f"音檔播放記錄成功: {request.user_id}, 音檔: RSS_{request.podcast_id}_{request.episode_title}.mp3")
            return {
                "success": True,
                "message": result["message"],
                "audio_filename": f"RSS_{request.podcast_id}_{request.episode_title}.mp3",
                "podcast_id": request.podcast_id,
                "episode_title": request.episode_title
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"記錄音檔播放失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/audio/heart-like")
def record_heart_like(request: HeartLikeRequest):
    """記錄愛心點擊"""
    try:
        result = podwise_service.record_heart_like(
            user_id=request.user_id,
            podcast_id=request.podcast_id,
            episode_title=request.episode_title
        )
        
        if result["success"]:
            logger.info(f"愛心點擊記錄成功: {request.user_id}, 音檔: RSS_{request.podcast_id}_{request.episode_title}.mp3")
            return {
                "success": True,
                "message": result["message"],
                "audio_filename": f"RSS_{request.podcast_id}_{request.episode_title}.mp3",
                "podcast_id": request.podcast_id,
                "episode_title": request.episode_title
            }
        else:
            return result
            
    except Exception as e:
        logger.error(f"記錄愛心點擊失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== 推薦系統 API ====================

@app.get("/api/category-tags/{category}")
async def get_category_tags(category: str):
    """獲取類別標籤"""
    try:
        tags = podwise_service.get_category_tags(category)
        
        return {
            "success": True,
            "category": category,
            "tags": tags
        }
    except Exception as e:
        logger.error(f"獲取類別標籤失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/one-minutes-episodes")
async def get_one_minutes_episodes(category: str, tag: str = ""):
    """獲取一分鐘節目推薦"""
    try:
        episodes = podwise_service.get_episodes_by_tag(category, tag, limit=3)
        
        return {
            "success": True,
            "episodes": episodes,
            "category": category,
            "tag": tag
        }
    except Exception as e:
        logger.error(f"獲取節目推薦失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== 代理路由 ====================



# ==================== RAG Pipeline API ====================

@app.post("/api/v1/rag/query")
async def rag_query_alias(request: ChatRequest):
    """RAG Pipeline 查詢別名端點"""
    return await rag_query(request)

@app.post("/api/v1/query")
async def rag_query(request: ChatRequest):
    """RAG Pipeline 查詢（整合用戶上下文）"""
    try:
        # 獲取用戶上下文
        user_context = podwise_service.get_user_context_for_rag(request.user_id)
        
        # 調用 RAG Pipeline 服務
        rag_url = SERVICE_CONFIGS["rag_pipeline"]["url"]
        
        # 準備查詢資料，包含用戶上下文
        query_data = {
            "query": request.query,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "enable_tts": request.enable_tts,
            "voice": request.voice,
            "speed": request.speed,
            "metadata": {
                **request.metadata,
                "user_context": user_context,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{rag_url}/api/v1/query", json=query_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                # 備用回應，包含用戶上下文
                context_info = ""
                if user_context.get("preferences"):
                    categories = [p["category"] for p in user_context["preferences"]]
                    context_info = f"根據您對 {', '.join(categories)} 類別的偏好，"
                
                if user_context.get("liked_episodes"):
                    recent_episode = user_context["liked_episodes"][0]
                    context_info += f"考慮到您最近喜歡的節目「{recent_episode['title']}」，"
                
                return {
                    "success": True,
                    "response": f"{context_info}您好！我收到了您的訊息：「{request.query}」。我正在學習如何更好地回答您的問題。",
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "user_context": user_context,
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"RAG Pipeline 查詢失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "抱歉，處理您的查詢時發生錯誤。"
        }

# ==================== TTS API ====================

@app.post("/api/v1/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """TTS 語音合成"""
    try:
        # 調用 TTS 服務
        tts_url = SERVICE_CONFIGS["tts"]["url"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{tts_url}/api/v1/tts/synthesize", json={
                "文字": request.text,
                "語音": request.voice,
                "語速": request.speed
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"TTS 服務錯誤: {response.status_code}, 回應: {response.text}")
                return {
                    "success": False,
                    "error": f"TTS 服務錯誤: {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"TTS 合成失敗: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ==================== STT API ====================

@app.post("/api/v1/stt/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """STT 語音轉文字"""
    try:
        # 調用 STT 服務
        stt_url = SERVICE_CONFIGS["stt"]["url"]
        
        # 準備檔案數據
        files = {"file": (file.filename, file.file, file.content_type)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{stt_url}/transcribe", files=files)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"STT 服務錯誤: {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"STT 轉錄失敗: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ==================== 全局異常處理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理器"""
    logger.error(f"全局異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "內部服務器錯誤"
        }
    )

# ==================== 通用代理路由 ====================
# 注意：這個通用代理路由在所有特定端點之後定義，以避免路由衝突

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_service(service: str, path: str, request: Request):
    """
    通用代理路由，將 /api/{service}/{path} 轉發到對應微服務
    支援所有 HTTP method
    """
    # 服務對應表
    SERVICE_MAP = {
        "tts": "http://localhost:8002",  # TTS 服務端口
        "rag": "http://localhost:8005",  # RAG Pipeline 端口
        "rag_pipeline": "http://localhost:8005",  # RAG Pipeline 端口
        "ml": "http://localhost:8004",
        "llm": "http://localhost:8004",  # LLM 服務端口
        "stt": "http://localhost:8003",  # STT 服務端口
    }
    
    # 特殊路由處理
    if service == "rag" and path == "query":
        path = "api/v1/query"  # 修正 RAG Pipeline 的查詢端點
    
    if service not in SERVICE_MAP:
        return JSONResponse(
            status_code=404,
            content={"error": f"Service '{service}' not found"}
        )
    
    target_url = f"{SERVICE_MAP[service]}/{path}"
    
    # 準備 headers，移除 host 以避免衝突
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # 取得 body
    body = await request.body()
    
    # 轉發請求
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=60.0
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=502,
                content={"error": f"Upstream error: {e}"}
            )
    
    # 回傳對應服務的 response
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp.headers
    )

# ==================== 啟動腳本 ====================

if __name__ == "__main__":
    # 檢查必要的目錄是否存在
    if not FRONTEND_PATH.exists():
        logger.error(f"前端目錄不存在: {FRONTEND_PATH}")
        sys.exit(1)
    
    if not IMAGES_PATH.exists():
        logger.error(f"圖片目錄不存在: {IMAGES_PATH}")
        sys.exit(1)
    
    if not ASSETS_PATH.exists():
        logger.error(f"資源目錄不存在: {ASSETS_PATH}")
        sys.exit(1)
    
    logger.info("🚀 啟動 Podwise 統一 API Gateway...")
    logger.info(f"前端路徑: {FRONTEND_PATH}")
    logger.info(f"圖片路徑: {IMAGES_PATH}")
    logger.info(f"資源路徑: {ASSETS_PATH}")
    
    # 啟動服務
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        reload=False,
        log_level="info"
    ) 