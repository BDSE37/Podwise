#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 用戶偏好服務主模組
整合用戶管理、偏好收集、反饋記錄等功能
採用 OOP 設計原則
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from backend.user_management.user_service import UserPreferenceService
from backend.utils.minio_milvus_utils import get_minio_client, get_tags_for_audio, get_podcast_name_from_db

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserServiceConfig:
    """用戶服務配置類別"""
    postgres_host: str = os.getenv("POSTGRES_HOST", "10.233.50.117")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "podcast")
    postgres_user: str = os.getenv("POSTGRES_USER", "bdse37")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "111111")
    
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "192.168.32.66:30090")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "bdse37")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "11111111")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    enable_logging: bool = True
    log_level: str = "INFO"


class UserPreferenceManager:
    """用戶偏好管理器 - 統一管理所有用戶相關功能"""
    
    def __init__(self, config: Optional[UserServiceConfig] = None):
        """初始化用戶偏好管理器"""
        self.config = config or UserServiceConfig()
        self.user_service = None
        self.minio_client = None
        
        # 預設 podcast 名稱快取（將從資料庫動態載入）
        self.podcast_name_cache = {}
        
        # 預設 episode_title 快取（將從資料庫動態載入）
        self.episode_title_cache = {}
        
        # 預設 TAGS 快取（將從資料庫動態載入）
        self.podcast_tags_cache = {}
        
        self._initialize_services()
        self._load_podcast_cache_from_db()
        logger.info("🚀 用戶偏好管理器初始化完成")
    
    def _initialize_services(self) -> None:
        """初始化所有服務"""
        try:
            # 初始化用戶服務
            db_config = {
                "host": self.config.postgres_host,
                "port": self.config.postgres_port,
                "database": self.config.postgres_db,
                "user": self.config.postgres_user,
                "password": self.config.postgres_password
            }
            
            self.user_service = UserPreferenceService(db_config)
            logger.info("✅ 用戶服務已初始化")
            
            # 初始化 MinIO 客戶端
            self.minio_client = get_minio_client()
            logger.info("✅ MinIO 客戶端已初始化")
            
        except Exception as e:
            logger.error(f"❌ 服務初始化失敗: {e}")
            raise
    
    def _load_podcast_cache_from_db(self) -> None:
        """從資料庫載入 podcast 快取"""
        try:
            if not self.user_service:
                logger.warning("用戶服務未初始化，無法載入 podcast 快取")
                return
            
            # 從資料庫獲取所有 podcast 資訊
            # 直接使用 psycopg2 連接資料庫
            import psycopg2
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            if not conn:
                logger.warning("無法連接資料庫，無法載入 podcast 快取")
                return
            
            with conn.cursor() as cursor:
                # 獲取 podcast 基本資訊（只載入 business 和 education 類別）
                cursor.execute("""
                    SELECT podcast_id, podcast_name, category 
                    FROM podcasts 
                    WHERE category IN ('商業', '自我成長')
                    ORDER BY category, podcast_id
                """)
                
                for row in cursor.fetchall():
                    podcast_id = str(row[0])
                    podcast_name = row[1]
                    category = row[2]
                    
                    # 儲存 podcast 名稱
                    self.podcast_name_cache[podcast_id] = podcast_name
                    
                    # 根據類別設定預設標籤（只處理 business 和 education）
                    if category == "商業":
                        self.podcast_tags_cache[podcast_id] = ["投資理財", "股票分析", "經濟分析", "財務規劃"]
                    elif category == "自我成長":
                        self.podcast_tags_cache[podcast_id] = ["個人成長", "心理學", "自我提升", "心靈成長"]
                    # 其他類別不處理，跳過
                
                # 獲取 episode 標題
                cursor.execute("""
                    SELECT DISTINCT podcast_id, episode_title 
                    FROM episodes 
                    ORDER BY podcast_id, episode_title
                """)
                
                for row in cursor.fetchall():
                    podcast_id = str(row[0])
                    episode_title = row[1]
                    
                    # 儲存第一個 episode 標題作為預設
                    if podcast_id not in self.episode_title_cache:
                        self.episode_title_cache[podcast_id] = episode_title
            
            logger.info(f"✅ 已從資料庫載入 {len(self.podcast_name_cache)} 個 podcast 資訊")
            
        except Exception as e:
            logger.error(f"❌ 載入 podcast 快取失敗: {e}")
    
    def get_category_tags(self, category: str) -> Dict[str, Any]:
        """根據類別獲取標籤"""
        try:
            # 根據類別選擇 bucket（只支援 business 和 education）
            if category == "business":
                bucket = "business-one-min-audio"
            elif category == "education":
                bucket = "education-one-min-audio"
            else:
                return {"success": False, "detail": f"不支援的類別: {category}，只支援 business 和 education"}
            
            if not self.minio_client:
                logger.error("MinIO 客戶端未初始化")
                return {"success": False, "detail": "MinIO 客戶端未初始化"}
            
            tag_set = set()
            objects = self.minio_client.list_objects(bucket, recursive=True)
            
            for obj in objects:
                if not obj.object_name or not obj.object_name.endswith(".mp3"):
                    continue
                
                # 解析檔案名稱：RSS_{podcast_id}_{episode_title}.mp3
                filename = obj.object_name
                if not filename.startswith("RSS_"):
                    continue
                
                # 移除 "RSS_" 前綴和 ".mp3" 後綴
                base_name = filename[4:-4]  # 移除 "RSS_" 和 ".mp3"
                
                # 找到第一個下劃線後的位置（podcast_id）
                first_underscore = base_name.find("_")
                if first_underscore == -1:
                    continue
                
                podcast_id = base_name[:first_underscore]
                
                # 從預設快取獲取標籤
                if podcast_id in self.podcast_tags_cache:
                    tag_set.update(self.podcast_tags_cache[podcast_id])
            
            # 過濾掉「一般」標籤，然後隨機選擇4個標籤
            import random
            tags = list(tag_set)
            # 移除「一般」標籤
            tags = [tag for tag in tags if tag != "一般"]
            # business 類別將「成長」轉為「經濟成長」
            if category == "business":
                tags = [tag if tag != "成長" else "經濟成長" for tag in tags]
            random.shuffle(tags)
            
            return {"success": True, "tags": tags[:4]}
            
        except Exception as e:
            logger.error(f"獲取類別標籤失敗: {e}")
            return {"success": False, "detail": f"獲取標籤失敗: {e}"}
    
    def get_one_minute_episodes(self, category: str, tag: str) -> Dict[str, Any]:
        """根據類別和標籤獲取一分鐘節目"""
        try:
            # 根據類別選擇 bucket（只支援 business 和 education）
            if category == "business":
                bucket = "business-one-min-audio"
            elif category == "education":
                bucket = "education-one-min-audio"
            else:
                return {"success": False, "detail": f"不支援的類別: {category}，只支援 business 和 education"}
            
            if not self.minio_client:
                logger.error("MinIO 客戶端未初始化")
                return self._get_default_episodes(category)
            
            # 不管標籤如何，都獲取該類別的所有節目
            all_results = []
            objects = self.minio_client.list_objects(bucket, recursive=True)
            
            for obj in objects:
                if not obj.object_name or not obj.object_name.endswith(".mp3"):
                    continue
                
                # 解析檔案名稱：RSS_{podcast_id}_{episode_title}.mp3
                filename = obj.object_name
                if not filename.startswith("RSS_"):
                    continue
                
                # 移除 "RSS_" 前綴和 ".mp3" 後綴
                base_name = filename[4:-4]  # 移除 "RSS_" 和 ".mp3"
                
                # 找到第一個下劃線後的位置（podcast_id）
                first_underscore = base_name.find("_")
                if first_underscore == -1:
                    continue
                
                podcast_id = base_name[:first_underscore]
                episode_title = base_name[first_underscore + 1:]
                
                if not podcast_id or not episode_title:
                    continue
                
                # 從預設快取獲取標籤，過濾掉「一般」
                default_tags = self.podcast_tags_cache.get(podcast_id, [])
                tags = [tag for tag in default_tags if tag != "一般"]
                # business 類別將「成長」轉為「經濟成長」
                if category == "business":
                    tags = [tag if tag != "成長" else "經濟成長" for tag in tags]
                
                # 構建音檔和圖片 URL
                audio_url = f"http://{self.config.minio_endpoint}/{bucket}/{obj.object_name}"
                # 根據實際圖片命名格式：RSS_{rss_id}_{size}.jpg
                # 使用 300px 尺寸，適合前端 80x80px 的顯示
                image_url = f"http://{self.config.minio_endpoint}/podcast-images/RSS_{podcast_id}_300.jpg"
                
                # 從預設快取獲取 podcast 名稱
                podcast_name = self.podcast_name_cache.get(podcast_id, f"Podcast_{podcast_id}")
                
                all_results.append({
                    "podcast_id": podcast_id,
                    "podcast_name": podcast_name,
                    "episode_title": episode_title,
                    "audio_url": audio_url,
                    "image_url": image_url,
                    "tags": tags,
                    "rss_id": f"RSS_{podcast_id}"
                })
            
            # 隨機選擇3個節目
            if all_results:
                import random
                random.shuffle(all_results)
                return {"success": True, "episodes": all_results[:3]}
            else:
                # 返回預設節目
                return self._get_default_episodes(category)
                
        except Exception as e:
            logger.error(f"獲取節目失敗: {e}")
            return self._get_default_episodes(category)
    
    def _get_default_episodes(self, category: str) -> Dict[str, Any]:
        """獲取預設節目（從資料庫動態獲取）"""
        try:
            minio_url = f"http://{self.config.minio_endpoint}"
            default_episodes = []
            
            # 根據類別選擇 bucket（只支援 business 和 education）
            if category == "business":
                bucket = "business-one-min-audio"
                db_category = "商業"
            elif category == "education":
                bucket = "education-one-min-audio"
                db_category = "自我成長"  # 使用自我成長類別作為教育類別
            else:
                return {"success": False, "detail": f"不支援的類別: {category}，只支援 business 和 education"}
            
            # 從資料庫獲取該類別的 podcast
            import psycopg2
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.podcast_id, p.podcast_name, e.episode_title
                    FROM podcasts p
                    LEFT JOIN episodes e ON p.podcast_id = e.podcast_id
                    WHERE p.category = %s
                    ORDER BY p.podcast_id, e.episode_title
                    LIMIT 3
                """, (db_category,))
                
                for row in cursor.fetchall():
                    podcast_id = str(row[0])
                    podcast_name = row[1]
                    episode_title = row[2] or "精選節目"
                    
                    # 檢查 MinIO 中是否有對應的圖片
                    image_url = f"{minio_url}/podcast-images/RSS_{podcast_id}_300.jpg"
                    
                    # 從快取獲取標籤，過濾掉「一般」
                    default_tags = self.podcast_tags_cache.get(podcast_id, ["知識分享", "學習", "成長"])
                    tags = [tag for tag in default_tags if tag != "一般"]
                    # business 類別將「成長」轉為「經濟成長」
                    if category == "business":
                        tags = [tag if tag != "成長" else "經濟成長" for tag in tags]
                    
                    default_episodes.append({
                        "podcast_id": podcast_id,
                        "podcast_name": podcast_name,
                        "episode_title": episode_title,
                        "audio_url": f"{minio_url}/{bucket}/RSS_{podcast_id}_{episode_title}.mp3",
                        "image_url": image_url,
                        "tags": tags,
                        "rss_id": f"RSS_{podcast_id}"
                    })
            
            conn.close()
            
            if not default_episodes:
                logger.warning(f"資料庫中沒有找到 {category} 類別的 podcast")
                return {"success": False, "detail": f"沒有找到 {category} 類別的節目"}
            
            return {"success": True, "episodes": default_episodes}
            
        except Exception as e:
            logger.error(f"獲取預設節目失敗: {e}")
            return {"success": False, "detail": f"獲取預設節目失敗: {e}"}
    
    def generate_podwise_id(self) -> Dict[str, Any]:
        """生成新的 Podwise ID"""
        try:
            if not self.user_service:
                return {"success": False, "error": "用戶服務未初始化"}
            return self.user_service.generate_podwise_id()
        except Exception as e:
            logger.error(f"生成 Podwise ID 失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def check_user_exists(self, user_code: str) -> bool:
        """檢查用戶是否存在"""
        try:
            if not self.user_service:
                logger.error("用戶服務未初始化")
                return False
            return self.user_service.check_user_exists(user_code)
        except Exception as e:
            logger.error(f"檢查用戶失敗: {e}")
            return False
    
    def save_user_preferences(self, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """儲存用戶偏好"""
        try:
            if not self.user_service:
                return {"success": False, "error": "用戶服務未初始化"}
            return self.user_service.save_user_preferences(preferences_data)
        except Exception as e:
            logger.error(f"儲存用戶偏好失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def record_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """記錄用戶反饋"""
        try:
            if not self.user_service:
                return {"success": False, "error": "用戶服務未初始化"}
            return self.user_service.record_feedback(feedback_data)
        except Exception as e:
            logger.error(f"記錄反饋失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def get_audio_presigned_url(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取音檔預簽名 URL"""
        try:
            rss_id = request_data.get('rss_id')
            episode_title = request_data.get('episode_title')
            category = request_data.get('category', 'business')
            
            if not rss_id or not episode_title:
                return {"success": False, "error": "缺少必要參數"}
            
            # 根據類別選擇 bucket（只支援 business 和 education）
            if category == "business":
                bucket = "business-one-min-audio"
            elif category == "education":
                bucket = "education-one-min-audio"
            else:
                return {"success": False, "error": f"不支援的類別: {category}，只支援 business 和 education"}
            
            # 構建物件鍵：RSS_{rss_id}_{episode_title}.mp3
            object_key = f"RSS_{rss_id}_{episode_title}.mp3"
            
            # 獲取直接 URL
            audio_url = f"http://{self.config.minio_endpoint}/{bucket}/{object_key}"
            
            return {
                "success": True,
                "audio_url": audio_url,
                "bucket": bucket,
                "object_key": object_key
            }
            
        except Exception as e:
            logger.error(f"獲取音檔 URL 失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查資料庫連接
            db_healthy = False
            if self.user_service:
                db_healthy = self.user_service.health_check()
            
            # 檢查 MinIO 連接
            minio_healthy = False
            if self.minio_client:
                try:
                    minio_healthy = self.minio_client.bucket_exists("business-one-min-audio")
                except Exception as e:
                    logger.error(f"MinIO 健康檢查失敗: {e}")
            
            return {
                "status": "healthy" if db_healthy and minio_healthy else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "minio": "connected" if minio_healthy else "disconnected",
                "service": "user_preference_manager"
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "user_preference_manager"
            }


# 全域實例
_user_manager = None


def get_user_manager(config: Optional[UserServiceConfig] = None) -> UserPreferenceManager:
    """獲取用戶管理器實例（單例模式）"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserPreferenceManager(config)
    return _user_manager


def initialize_user_manager(config: Optional[UserServiceConfig] = None) -> UserPreferenceManager:
    """初始化用戶管理器"""
    return get_user_manager(config)


# FastAPI 應用
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

app = FastAPI(
    title="PodWise 用戶偏好管理 API",
    description="PodWise Podcast 推薦系統用戶偏好管理服務",
    version="1.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求模型
class FeedbackRequest(BaseModel):
    user_code: str
    episode_id: str  # 可以是字串或數字
    podcast_name: str
    episode_title: str
    rss_id: str

class AudioRequest(BaseModel):
    rss_id: str
    episode_title: str
    category: str = "business"

# 全域用戶管理器實例
user_manager = None

@app.on_event("startup")
async def startup_event():
    """啟動時初始化用戶管理器"""
    global user_manager
    try:
        user_manager = initialize_user_manager()
        print("🚀 用戶偏好管理服務已啟動")
    except Exception as e:
        print(f"❌ 服務啟動失敗: {e}")
        raise

@app.get("/health")
async def health_check():
    """健康檢查"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    return user_manager.health_check()

@app.get("/api/category-tags/{category}")
async def get_category_tags(category: str):
    """獲取類別標籤"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    return user_manager.get_category_tags(category)

@app.get("/api/one-minutes-episodes")
async def get_one_minute_episodes(category: str, tag: str = ""):
    """獲取一分鐘節目"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    return user_manager.get_one_minute_episodes(category, tag)

@app.post("/api/feedback")
async def record_feedback(request: FeedbackRequest):
    """記錄用戶反饋"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    feedback_data = {
        "user_code": request.user_code,
        "episode_id": request.episode_id,
        "podcast_name": request.podcast_name,
        "episode_title": request.episode_title,
        "rss_id": request.rss_id
    }
    return user_manager.record_feedback(feedback_data)

@app.post("/api/audio/presigned-url")
async def get_audio_presigned_url(request: AudioRequest):
    """獲取音檔預簽名 URL"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    request_data = {
        "rss_id": request.rss_id,
        "episode_title": request.episode_title,
        "category": request.category
    }
    return user_manager.get_audio_presigned_url(request_data)

@app.post("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成新的 Podwise ID"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    return user_manager.generate_podwise_id()

@app.get("/api/user/check/{user_code}")
async def check_user_exists(user_code: str):
    """檢查用戶是否存在"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    exists = user_manager.check_user_exists(user_code)
    return {"exists": exists}

@app.post("/api/user/preferences")
async def save_user_preferences(request: dict):
    """儲存用戶偏好"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="服務未初始化")
    return user_manager.save_user_preferences(request)

if __name__ == "__main__":
    # 啟動 FastAPI 服務
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    ) 