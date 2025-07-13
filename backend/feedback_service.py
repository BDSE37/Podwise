#!/usr/bin/env python3
"""
Feedback Service - 處理用戶反饋和偏好儲存
符合 PostgreSQL 資料庫結構
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import uuid
from minio_episode_service import MinioEpisodeService

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL 資料庫配置
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'podcast'),
    'user': os.getenv('POSTGRES_USER', 'bdse37'),
    'password': os.getenv('POSTGRES_PASSWORD', '111111')
}

# 建立 FastAPI 應用
app = FastAPI(
    title="PodWise Feedback Service",
    description="處理用戶反饋和偏好儲存，符合 PostgreSQL 資料庫結構",
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

class DatabaseManager:
    """資料庫管理類別"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """連接到 PostgreSQL 資料庫"""
        try:
            self.connection = psycopg2.connect(**POSTGRES_CONFIG)
            logger.info("成功連接到 PostgreSQL 資料庫")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    def get_connection(self):
        """獲取資料庫連接"""
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection
    
    def close(self):
        """關閉資料庫連接"""
        if self.connection:
            self.connection.close()

# 全域資料庫管理器
db_manager = DatabaseManager()

# 記憶體儲存（用於 Podwise ID 生成）
podwise_ids = {}

# Pydantic 模型 - 符合 PostgreSQL 資料庫結構
class FeedbackRequest(BaseModel):
    user_id: int  # 對應 users.user_id (INTEGER)
    episode_id: int  # 對應 episodes.episode_id (INTEGER)
    action: str  # 'like' 或 'unlike'
    category: str  # 節目分類

class UserPreferencesRequest(BaseModel):
    user_code: str  # 使用 user_identifier 作為 Podwise ID
    main_category: str
    selected_tag: Optional[str] = None
    liked_episodes: List[Dict[str, Any]] = []

class PodwiseIDRequest(BaseModel):
    pass

# API 端點
@app.get("/")
async def root():
    """根端點"""
    return {"message": "PodWise Feedback Service", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """健康檢查"""
    try:
        # 測試資料庫連接
        conn = db_manager.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return {
            "status": "healthy",
            "service": "feedback-service",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "service": "feedback-service",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/feedback")
async def record_feedback(feedback: FeedbackRequest):
    """記錄用戶反饋到 PostgreSQL user_feedback 表格"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 檢查用戶和節目是否存在
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (feedback.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用戶不存在")
            
            cursor.execute("SELECT episode_id FROM episodes WHERE episode_id = %s", (feedback.episode_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="節目不存在")
            
            # 檢查是否已有反饋記錄
            cursor.execute("""
                SELECT user_id, episode_id, like_count, dislike_count 
                FROM user_feedback 
                WHERE user_id = %s AND episode_id = %s
            """, (feedback.user_id, feedback.episode_id))
            
            existing_feedback = cursor.fetchone()
            
            if existing_feedback:
                # 更新現有記錄
                if feedback.action == 'like':
                    like_count = (existing_feedback['like_count'] or 0) + 1
                    dislike_count = existing_feedback['dislike_count'] or 0
                else:  # unlike
                    like_count = max(0, (existing_feedback['like_count'] or 0) - 1)
                    dislike_count = existing_feedback['dislike_count'] or 0
                
                cursor.execute("""
                    UPDATE user_feedback 
                    SET like_count = %s, dislike_count = %s, updated_at = NOW()
                    WHERE user_id = %s AND episode_id = %s
                """, (like_count, dislike_count, feedback.user_id, feedback.episode_id))
                
            else:
                # 插入新記錄
                if feedback.action == 'like':
                    like_count = 1
                    dislike_count = 0
                else:  # unlike
                    like_count = 0
                    dislike_count = 1
                
                cursor.execute("""
                    INSERT INTO user_feedback (
                        user_id, episode_id, like_count, dislike_count, 
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (feedback.user_id, feedback.episode_id, like_count, dislike_count))
            
            conn.commit()
            
            # 獲取節目資訊用於日誌
            cursor.execute("""
                SELECT e.episode_title, p.name as podcast_name
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.episode_id = %s
            """, (feedback.episode_id,))
            
            episode_info = cursor.fetchone()
            podcast_name = episode_info['podcast_name'] if episode_info else "Unknown"
            episode_title = episode_info['episode_title'] if episode_info else "Unknown"
            
            logger.info(f"記錄反饋: {feedback.action} - {podcast_name} - {episode_title}")
            
            return {
                "success": True,
                "message": f"反饋記錄成功: {feedback.action}",
                "user_id": feedback.user_id,
                "episode_id": feedback.episode_id,
                "action": feedback.action,
                "podcast_name": podcast_name,
                "episode_title": episode_title
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/user/preferences")
async def save_user_preferences(preferences: UserPreferencesRequest):
    """儲存用戶偏好（Step1、Step2、Step3 資訊）到 user_feedback 表格"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor() as cursor:
            # 根據 user_code 查找用戶
            cursor.execute("SELECT user_id FROM users WHERE user_code = %s", (preferences.user_code,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="用戶不存在")
            
            user_id = result[0]
            
            # 儲存喜歡的節目（Step3）
            for episode in preferences.liked_episodes:
                episode_id = episode.get('episode_id')
                if episode_id:
                    cursor.execute("""
                        INSERT INTO user_feedback (user_id, episode_id, rating, bookmark, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id, episode_id) 
                        DO UPDATE SET 
                            rating = EXCLUDED.rating,
                            bookmark = EXCLUDED.bookmark,
                            updated_at = CURRENT_TIMESTAMP
                    """, (user_id, episode_id, 5, True))
            
            conn.commit()
            
            logger.info(f"儲存用戶偏好成功: {user_id} - {preferences.main_category} - {preferences.user_code}")
            
            return {
                "success": True,
                "message": "用戶偏好儲存成功",
                "user_code": preferences.user_code
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"儲存用戶偏好失敗: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成 Podwise ID（user_code 會自動生成）"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor() as cursor:
            # 創建新用戶，user_code 會自動生成為 'Podwise' + 4位數字
            cursor.execute("""
                INSERT INTO users (username, email, is_active, created_at, updated_at)
                VALUES (%s, %s, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING user_id, user_code
            """, (
                f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@podwise.com"
            ))
            
            result = cursor.fetchone()
            user_id = result[0]
            user_code = result[1]  # 這就是自動生成的 Podwise ID
            
            conn.commit()
            
            logger.info(f"生成 Podwise ID: {user_code} (user_id: {user_id})")
            
            return {
                "success": True,
                "podwise_id": user_code,
                "user_id": user_id,
                "message": "Podwise ID 生成成功"
            }
        
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/user/preferences/{user_id}")
async def get_user_preferences(user_id: int):
    """獲取用戶偏好"""
    try:
        # 檢查用戶是否存在
        conn = db_manager.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用戶不存在")
        
        # 從記憶體獲取偏好（實際應該從資料庫獲取）
        if 'user_preferences' in globals() and user_id in globals()['user_preferences']:
            return {
                "success": True,
                "preferences": globals()['user_preferences'][user_id]
            }
        else:
            return {
                "success": False,
                "message": "用戶偏好不存在"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/user/preferences/code/{user_code}")
async def get_user_preferences_by_code(user_code: str):
    """根據 user_code 獲取用戶偏好（Step3 資訊）"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 檢查用戶是否存在
            cursor.execute("SELECT user_id, user_code FROM users WHERE user_code = %s", (user_code,))
            user_result = cursor.fetchone()
            
            if not user_result:
                raise HTTPException(status_code=404, detail="用戶不存在")
            
            user_id = user_result['user_id']
            
            # 獲取用戶最近的反饋記錄（Step3 資訊）
            cursor.execute("""
                SELECT uf.episode_id, uf.rating, uf.bookmark, uf.preview_played,
                       e.episode_title, p.name as podcast_name, p.category
                FROM user_feedback uf
                JOIN episodes e ON uf.episode_id = e.episode_id
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE uf.user_id = %s
                ORDER BY uf.updated_at DESC
                LIMIT 10
            """, (user_id,))
            
            feedback_records = cursor.fetchall()
            
            # 整理 Step3 資訊
            step3_info = {
                "liked_episodes": [
                    {
                        "episode_id": record['episode_id'],
                        "episode_title": record['episode_title'],
                        "podcast_name": record['podcast_name'],
                        "category": record['category'],
                        "rating": record['rating'],
                        "bookmark": record['bookmark']
                    }
                    for record in feedback_records
                    if record['rating'] and record['rating'] > 3
                ]
            }
            
            return {
                "success": True,
                "user_code": user_code,
                "user_id": user_id,
                "step3": step3_info,
                "last_updated": feedback_records[0]['updated_at'] if feedback_records else None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/feedback/user/{user_id}")
async def get_user_feedback(user_id: int):
    """獲取用戶反饋記錄"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 檢查用戶是否存在
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用戶不存在")
            
            # 獲取用戶反饋記錄
            cursor.execute("""
                SELECT uf.*, e.episode_title, p.name as podcast_name
                FROM user_feedback uf
                JOIN episodes e ON uf.episode_id = e.episode_id
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE uf.user_id = %s
                ORDER BY uf.updated_at DESC
            """, (user_id,))
            
            feedback_records = cursor.fetchall()
            
            return {
                "success": True,
                "feedback_count": len(feedback_records),
                "feedback": [dict(record) for record in feedback_records]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶反饋失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/available-episodes")
async def get_available_episodes(category: str = "business"):
    """獲取可用的節目（來自 MinIO）"""
    try:
        minio_service = MinioEpisodeService()
        episodes = minio_service.get_episodes_by_category(category)
        
        logger.info(f"獲取到 {len(episodes)} 個可用節目")
        
        return {
            "success": True,
            "episodes": episodes,
            "count": len(episodes),
            "category": category
        }
        
    except Exception as e:
        logger.error(f"獲取可用節目失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/category-tags")
async def get_category_tags(category: str = "business"):
    """獲取指定類別的標籤"""
    try:
        minio_service = MinioEpisodeService()
        tags = minio_service.get_category_tags(category)
        
        logger.info(f"獲取到 {len(tags)} 個 {category} 類別標籤")
        
        return {
            "success": True,
            "tags": tags,
            "category": category
        }
        
    except Exception as e:
        logger.error(f"獲取類別標籤失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/stats")
async def get_service_stats():
    """獲取服務統計"""
    try:
        conn = db_manager.get_connection()
        
        with conn.cursor() as cursor:
            # 獲取反饋統計
            cursor.execute("SELECT COUNT(*) as total_feedback FROM user_feedback")
            total_feedback = cursor.fetchone()[0]
            
            # 獲取用戶統計
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()[0]
            
            # 獲取節目統計
            cursor.execute("SELECT COUNT(*) as total_episodes FROM episodes")
            total_episodes = cursor.fetchone()[0]
        
        return {
            "success": True,
            "stats": {
                "total_feedback": total_feedback,
                "total_users": total_users,
                "total_episodes": total_episodes,
                "total_podwise_ids": len(podwise_ids),
                "service_uptime": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取統計失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/one-minutes-episodes")
async def get_one_minutes_episodes(category: str = "business", tag: str = ""):
    """獲取一分鐘節目推薦（符合前端需求）"""
    try:
        minio_service = MinioEpisodeService()
        episodes = minio_service.get_episodes_by_category(category)
        
        # 如果有指定 tag，過濾包含該 tag 的節目
        if tag:
            filtered_episodes = []
            for episode in episodes:
                if 'tags' in episode and tag in episode['tags']:
                    filtered_episodes.append(episode)
            episodes = filtered_episodes
        
        # 去重：確保沒有重複的 episode_id 和 podcast_id
        unique_episodes = []
        used_episode_ids = set()
        used_podcast_ids = set()
        
        for episode in episodes:
            episode_id = episode.get('episode_id')
            podcast_id = episode.get('podcast_id')
            
            # 檢查是否已經使用過這個 episode_id 或 podcast_id
            if (episode_id and episode_id not in used_episode_ids and 
                podcast_id and podcast_id not in used_podcast_ids):
                unique_episodes.append(episode)
                used_episode_ids.add(episode_id)
                used_podcast_ids.add(podcast_id)
        
        episodes = unique_episodes
        
        # 隨機選擇最多 3 個不同頻道的節目
        import random
        if len(episodes) > 3:
            episodes = random.sample(episodes, 3)
        else:
            episodes = episodes[:3]
        
        # 格式化回應格式，符合前端期望
        formatted_episodes = []
        for episode in episodes:
            formatted_episode = {
                'episode_id': episode.get('episode_id', 1),
                'rss_id': str(episode.get('rss_id', '123')),
                'podcast_name': episode.get('podcast_name', 'Unknown Podcast'),
                'episode_title': episode.get('episode_title', 'Unknown Episode'),
                'episode_description': episode.get('episode_description', '節目描述'),
                'podcast_image': f"images/{episode.get('podcast_name', 'default')}.png",
                'audio_url': episode.get('audio_url', ''),
                'tags': episode.get('tags', [])
            }
            formatted_episodes.append(formatted_episode)
        
        logger.info(f"返回 {len(formatted_episodes)} 個 {category} 類別節目")
        
        return {
            "success": True,
            "episodes": formatted_episodes,
            "category": category,
            "tag": tag
        }
        
    except Exception as e:
        logger.error(f"獲取一分鐘節目失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "feedback_service:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    ) 