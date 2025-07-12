#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 推薦服務
整合 MinIO 音檔搜尋、PostgreSQL 節目資訊和用戶反饋
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
import psycopg2.extras
from minio import Minio
from minio.error import S3Error
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 資料庫配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres.podwise.svc.cluster.local"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "podcast"),
    "user": os.getenv("POSTGRES_USER", "bdse37"),
    "password": os.getenv("POSTGRES_PASSWORD", "111111")
}

# MinIO 配置
MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "minio.podwise.svc.cluster.local:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    "secure": False
}

# 類別映射
CATEGORY_MAPPING = {
    "business": ["business", "財經", "職業", "房地產", "行銷", "投資", "理財"],
    "education": ["education", "教育", "學習", "科技", "知識", "技能"]
}

class RecommendationRequest(BaseModel):
    category: str
    user_id: Optional[str] = "default_user"
    limit: Optional[int] = 3

class UserFeedbackRequest(BaseModel):
    user_id: str
    episode_id: int
    action: str  # "like", "unlike", "play"
    category: str
    file_name: str
    bucket_category: str

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    category: str
    total_count: int
    user_id: str

class UserFeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None

class RecommendationService:
    """推薦服務核心類別"""
    
    def __init__(self):
        """初始化推薦服務"""
        self.db_conn = None
        self.minio_client = None
        self._init_connections()
        
    def _init_connections(self):
        """初始化資料庫和 MinIO 連接"""
        try:
            # 初始化 PostgreSQL 連接
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ PostgreSQL 連接成功")
            
            # 初始化 MinIO 連接
            self.minio_client = Minio(
                MINIO_CONFIG["endpoint"],
                access_key=MINIO_CONFIG["access_key"],
                secret_key=MINIO_CONFIG["secret_key"],
                secure=MINIO_CONFIG["secure"]
            )
            logger.info("✅ MinIO 連接成功")
            
        except Exception as e:
            logger.error(f"❌ 連接初始化失敗: {e}")
            raise
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        if not self.db_conn or self.db_conn.closed:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
        return self.db_conn
    
    def search_minio_audio_files(self, category: str, limit: int = 3) -> List[Dict[str, Any]]:
        """從 MinIO 搜尋音檔"""
        try:
            # 確定 bucket 名稱
            bucket_name = f"{category}_one_minutes"
            
            # 檢查 bucket 是否存在
            if not self.minio_client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} 不存在")
                return []
            
            # 列出 bucket 中的音檔
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            
            # 過濾 MP3 檔案
            mp3_files = [obj for obj in objects if obj.object_name.lower().endswith('.mp3')]
            
            # 限制數量
            mp3_files = mp3_files[:limit]
            
            results = []
            for obj in mp3_files:
                # 解析檔案名稱獲取 RSS 資訊
                file_info = self._parse_audio_filename(obj.object_name)
                
                # 生成預簽名 URL
                presigned_url = self.minio_client.presigned_get_object(
                    bucket_name, 
                    obj.object_name,
                    expires=3600  # 1小時有效
                )
                
                result = {
                    "file_name": obj.object_name,
                    "file_size": obj.size,
                    "last_modified": obj.last_modified.isoformat(),
                    "audio_url": presigned_url,
                    "bucket_name": bucket_name,
                    "category": category,
                    **file_info
                }
                results.append(result)
            
            logger.info(f"從 MinIO 找到 {len(results)} 個音檔")
            return results
            
        except Exception as e:
            logger.error(f"MinIO 搜尋失敗: {e}")
            return []
    
    def _parse_audio_filename(self, filename: str) -> Dict[str, Any]:
        """解析音檔檔案名稱，提取 RSS 資訊"""
        try:
            # 範例檔案名稱: RSS_262026947_podcast_1304_Millennials and business.mp3
            # 或者: 財經_1.mp3
            
            if filename.startswith('RSS_'):
                # 解析 RSS 格式
                parts = filename.replace('.mp3', '').split('_')
                if len(parts) >= 4:
                    rss_id = parts[1]
                    podcast_id = parts[3]
                    episode_title = '_'.join(parts[4:]) if len(parts) > 4 else "未知標題"
                    
                    return {
                        "rss_id": rss_id,
                        "podcast_id": podcast_id,
                        "episode_title": episode_title,
                        "file_type": "rss"
                    }
            else:
                # 解析簡單格式
                name_parts = filename.replace('.mp3', '').split('_')
                if len(name_parts) >= 2:
                    category = name_parts[0]
                    episode_num = name_parts[1]
                    
                    return {
                        "category": category,
                        "episode_num": episode_num,
                        "episode_title": f"{category}精選節目 {episode_num}",
                        "file_type": "simple"
                    }
            
            return {
                "episode_title": filename.replace('.mp3', ''),
                "file_type": "unknown"
            }
            
        except Exception as e:
            logger.error(f"解析檔案名稱失敗: {e}")
            return {
                "episode_title": filename.replace('.mp3', ''),
                "file_type": "error"
            }
    
    def get_podcast_info_from_db(self, rss_id: str = None, podcast_id: str = None) -> Dict[str, Any]:
        """從 PostgreSQL 獲取節目資訊"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                
                if rss_id:
                    # 根據 RSS ID 查詢
                    cursor.execute("""
                        SELECT p.podcast_id, p.name as podcast_name, p.description, p.author,
                               p.images_640, p.images_300, p.category, p.languages
                        FROM podcasts p
                        WHERE p.rss_link LIKE %s
                        LIMIT 1
                    """, (f"%{rss_id}%",))
                elif podcast_id:
                    # 根據 podcast_id 查詢
                    cursor.execute("""
                        SELECT p.podcast_id, p.name as podcast_name, p.description, p.author,
                               p.images_640, p.images_300, p.category, p.languages
                        FROM podcasts p
                        WHERE p.podcast_id = %s
                        LIMIT 1
                    """, (podcast_id,))
                else:
                    return {}
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return {}
                
        except Exception as e:
            logger.error(f"資料庫查詢失敗: {e}")
            return {}
    
    def get_episode_info_from_db(self, episode_title: str, podcast_id: str = None) -> Dict[str, Any]:
        """從 PostgreSQL 獲取集數資訊"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                
                if podcast_id:
                    # 根據 podcast_id 和標題查詢
                    cursor.execute("""
                        SELECT e.episode_id, e.episode_title, e.published_date, e.duration,
                               e.description, e.audio_url, e.languages
                        FROM episodes e
                        WHERE e.podcast_id = %s AND e.episode_title ILIKE %s
                        LIMIT 1
                    """, (podcast_id, f"%{episode_title}%"))
                else:
                    # 只根據標題查詢
                    cursor.execute("""
                        SELECT e.episode_id, e.episode_title, e.published_date, e.duration,
                               e.description, e.audio_url, e.languages, e.podcast_id
                        FROM episodes e
                        WHERE e.episode_title ILIKE %s
                        LIMIT 1
                    """, (f"%{episode_title}%",))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return {}
                
        except Exception as e:
            logger.error(f"集數查詢失敗: {e}")
            return {}
    
    def get_recommendations(self, category: str, user_id: str = "default_user", limit: int = 3) -> List[Dict[str, Any]]:
        """獲取推薦列表"""
        try:
            # 1. 從 MinIO 獲取音檔
            audio_files = self.search_minio_audio_files(category, limit)
            
            if not audio_files:
                logger.warning(f"沒有找到 {category} 類別的音檔")
                return self._get_fallback_recommendations(category, limit)
            
            recommendations = []
            
            for audio_file in audio_files:
                # 2. 嘗試從資料庫獲取節目資訊
                podcast_info = {}
                episode_info = {}
                
                if audio_file.get("file_type") == "rss":
                    # RSS 格式檔案
                    rss_id = audio_file.get("rss_id")
                    podcast_id = audio_file.get("podcast_id")
                    episode_title = audio_file.get("episode_title")
                    
                    if rss_id:
                        podcast_info = self.get_podcast_info_from_db(rss_id=rss_id)
                    elif podcast_id:
                        podcast_info = self.get_podcast_info_from_db(podcast_id=podcast_id)
                    
                    if episode_title:
                        episode_info = self.get_episode_info_from_db(episode_title, podcast_id)
                
                # 3. 合併資訊
                recommendation = {
                    "file_name": audio_file["file_name"],
                    "audio_url": audio_file["audio_url"],
                    "bucket_name": audio_file["bucket_name"],
                    "category": category,
                    "file_size": audio_file["file_size"],
                    "last_modified": audio_file["last_modified"],
                    
                    # 節目資訊
                    "podcast_name": podcast_info.get("podcast_name", f"{category}精選節目"),
                    "podcast_description": podcast_info.get("description", f"專業的{category}內容分享"),
                    "podcast_author": podcast_info.get("author", "專業團隊"),
                    "podcast_image": podcast_info.get("images_640") or podcast_info.get("images_300"),
                    
                    # 集數資訊
                    "episode_title": episode_info.get("episode_title", audio_file.get("episode_title", "精選內容")),
                    "episode_description": episode_info.get("description", f"精彩的{category}內容"),
                    "episode_duration": episode_info.get("duration", 60),
                    "episode_published_date": episode_info.get("published_date"),
                    "episode_id": episode_info.get("episode_id"),
                    
                    # 用戶反饋資訊
                    "user_feedback": self._get_user_feedback(user_id, episode_info.get("episode_id"))
                }
                
                recommendations.append(recommendation)
            
            logger.info(f"為用戶 {user_id} 生成 {len(recommendations)} 個 {category} 推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取推薦失敗: {e}")
            return self._get_fallback_recommendations(category, limit)
    
    def _get_fallback_recommendations(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """獲取備用推薦（當 MinIO 或資料庫無法訪問時）"""
        fallback_data = {
            "business": [
                {
                    "file_name": "財經_1.mp3",
                    "audio_url": "/audio/sample1.mp3",
                    "podcast_name": "股癌 Gooaye",
                    "episode_title": "投資理財精選",
                    "episode_description": "晦澀金融投資知識直白講，重要海內外時事輕鬆談；散戶也能找到樂趣。",
                    "podcast_image": "/images/股癌.png",
                    "category": "business"
                },
                {
                    "file_name": "財經_2.mp3",
                    "audio_url": "/audio/sample2.mp3",
                    "podcast_name": "財經早知道",
                    "episode_title": "市場分析報告",
                    "episode_description": "每日財經新聞精選，助您掌握市場動態。",
                    "podcast_image": "/images/財經早知道.png",
                    "category": "business"
                }
            ],
            "education": [
                {
                    "file_name": "教育_1.mp3",
                    "audio_url": "/audio/sample3.mp3",
                    "podcast_name": "矽谷輕鬆談",
                    "episode_title": "科技趨勢分享",
                    "episode_description": "Google 搜尋、AI 技術、科技趨勢都能輕鬆聽懂，專為中文使用者打造。",
                    "podcast_image": "/images/矽谷輕鬆談.png",
                    "category": "education"
                },
                {
                    "file_name": "教育_2.mp3",
                    "audio_url": "/audio/sample4.mp3",
                    "podcast_name": "天下學習",
                    "episode_title": "管理思維探索",
                    "episode_description": "訪談頂尖領導者，探索管理思維、教育創新與未來趨勢。",
                    "podcast_image": "/images/天下學習.png",
                    "category": "education"
                }
            ]
        }
        
        return fallback_data.get(category, fallback_data["business"])[:limit]
    
    def _get_user_feedback(self, user_id: str, episode_id: int) -> Dict[str, Any]:
        """獲取用戶對特定集數的反饋"""
        try:
            if not episode_id:
                return {"liked": False, "played": False, "rating": None}
            
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT like_count, dislike_count, preview_played, rating
                    FROM user_feedback
                    WHERE user_id = %s AND episode_id = %s
                """, (user_id, episode_id))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "liked": result["like_count"] > 0,
                        "disliked": result["dislike_count"] > 0,
                        "played": result["preview_played"] or False,
                        "rating": result["rating"]
                    }
                return {"liked": False, "played": False, "rating": None}
                
        except Exception as e:
            logger.error(f"獲取用戶反饋失敗: {e}")
            return {"liked": False, "played": False, "rating": None}
    
    def record_user_feedback(self, user_id: str, episode_id: int, action: str, 
                           category: str, file_name: str, bucket_category: str) -> bool:
        """記錄用戶反饋"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                
                # 檢查是否已有記錄
                cursor.execute("""
                    SELECT user_id, episode_id FROM user_feedback 
                    WHERE user_id = %s AND episode_id = %s
                """, (user_id, episode_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新現有記錄
                    if action == "like":
                        cursor.execute("""
                            UPDATE user_feedback 
                            SET like_count = like_count + 1, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND episode_id = %s
                        """, (user_id, episode_id))
                    elif action == "unlike":
                        cursor.execute("""
                            UPDATE user_feedback 
                            SET like_count = GREATEST(like_count - 1, 0), updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND episode_id = %s
                        """, (user_id, episode_id))
                    elif action == "play":
                        cursor.execute("""
                            UPDATE user_feedback 
                            SET preview_played = true, preview_played_at = CURRENT_TIMESTAMP, 
                                preview_play_count = preview_play_count + 1, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND episode_id = %s
                        """, (user_id, episode_id))
                else:
                    # 創建新記錄
                    cursor.execute("""
                        INSERT INTO user_feedback 
                        (user_id, episode_id, like_count, dislike_count, preview_played, 
                         preview_played_at, preview_play_count, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        user_id, episode_id,
                        1 if action == "like" else 0,
                        1 if action == "unlike" else 0,
                        True if action == "play" else False,
                        CURRENT_TIMESTAMP if action == "play" else None,
                        1 if action == "play" else 0
                    ))
                
                conn.commit()
                logger.info(f"用戶 {user_id} 對集數 {episode_id} 執行了 {action} 操作")
                return True
                
        except Exception as e:
            logger.error(f"記錄用戶反饋失敗: {e}")
            if conn:
                conn.rollback()
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶偏好"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT category, preference_score
                    FROM user_preferences
                    WHERE user_id = %s
                    ORDER BY preference_score DESC
                """, (user_id,))
                
                preferences = cursor.fetchall()
                return {row["category"]: row["preference_score"] for row in preferences}
                
        except Exception as e:
            logger.error(f"獲取用戶偏好失敗: {e}")
            return {}

# 創建 FastAPI 應用
app = FastAPI(title="Podwise 推薦服務", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建推薦服務實例
recommendation_service = RecommendationService()

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "recommendation"}

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """獲取推薦列表"""
    try:
        recommendations = recommendation_service.get_recommendations(
            category=request.category,
            user_id=request.user_id,
            limit=request.limit
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            category=request.category,
            total_count=len(recommendations),
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"獲取推薦失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback", response_model=UserFeedbackResponse)
async def record_feedback(request: UserFeedbackRequest):
    """記錄用戶反饋"""
    try:
        success = recommendation_service.record_user_feedback(
            user_id=request.user_id,
            episode_id=request.episode_id,
            action=request.action,
            category=request.category,
            file_name=request.file_name,
            bucket_category=request.bucket_category
        )
        
        if success:
            return UserFeedbackResponse(
                success=True,
                message=f"成功記錄 {request.action} 操作",
                feedback_id=f"{request.user_id}_{request.episode_id}"
            )
        else:
            raise HTTPException(status_code=500, detail="記錄反饋失敗")
            
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """獲取用戶偏好"""
    try:
        preferences = recommendation_service.get_user_preferences(user_id)
        return {"user_id": user_id, "preferences": preferences}
        
    except Exception as e:
        logger.error(f"獲取用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/minio/audio/{bucket_name}/{file_name}")
async def get_minio_audio_url(bucket_name: str, file_name: str):
    """獲取 MinIO 音檔的預簽名 URL"""
    try:
        presigned_url = recommendation_service.minio_client.presigned_get_object(
            bucket_name, file_name, expires=3600
        )
        return {"audio_url": presigned_url, "bucket_name": bucket_name, "file_name": file_name}
        
    except Exception as e:
        logger.error(f"獲取 MinIO URL 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 