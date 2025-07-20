#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 整合用戶管理服務
整合用戶註冊、偏好設定、反饋記錄和推薦功能
"""

import os
import json
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
from minio import Minio
from minio.error import S3Error
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import requests

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入統一配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG

# 使用統一配置
DB_CONFIG = POSTGRES_CONFIG

# 類別映射
CATEGORY_MAPPING = {
    "business": ["business", "投資理財", "股票分析", "經濟分析", "財務規劃", "投資", "理財"],
    "education": ["education", "教育", "學習", "科技", "知識", "技能"]
}

# 類別對應的 MinIO bucket
CATEGORY_BUCKETS = {
    "business": "business-one-min-audio",
    "education": "education-one-min-audio"
}

# Pydantic 模型
class CategoryRequest(BaseModel):
    category: str  # "business" 或 "education"
    tag: Optional[str] = None  # 可選的 TAG 參數

class UserFeedbackRequest(BaseModel):
    user_id: str
    episode_id: int
    podcast_name: str
    episode_title: str
    rss_id: str
    action: str  # "like", "unlike"
    category: str

class UserRegistrationRequest(BaseModel):
    user_id: str
    category: str
    selected_episodes: List[Dict[str, Any]]  # 包含 podcast_name, episode_title, rss_id

class UserPreferenceRequest(BaseModel):
    user_id: str
    main_category: str
    sub_category: Optional[str] = None
    language: Optional[str] = None
    duration_preference: Optional[str] = None

class IntegratedUserService:
    """整合用戶管理服務核心類別"""
    
    def __init__(self):
        """初始化服務"""
        self.db_conn = None
        self.minio_client = None
        self._init_connections()
        
    def _init_connections(self):
        """初始化資料庫和 MinIO 連接"""
        try:
            # 初始化 MinIO 連接
            self.minio_client = Minio(
                MINIO_CONFIG["endpoint"],
                access_key=MINIO_CONFIG["access_key"],
                secret_key=MINIO_CONFIG["secret_key"],
                secure=MINIO_CONFIG["secure"]
            )
            logger.info("✅ MinIO 連接成功")
            
            # 延遲初始化 PostgreSQL 連接，避免服務啟動失敗
            self.db_conn = None
            logger.info("✅ 服務初始化成功，資料庫連接將在需要時建立")
            
        except Exception as e:
            logger.error(f"❌ 連接初始化失敗: {e}")
            # 不拋出異常，讓服務繼續運行
            self.db_conn = None
            self.minio_client = None
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            if not self.db_conn or self.db_conn.closed:
                logger.info("嘗試連接 PostgreSQL...")
                self.db_conn = psycopg2.connect(**DB_CONFIG)
                logger.info("✅ PostgreSQL 連接成功")
            return self.db_conn
        except Exception as e:
            logger.error(f"❌ PostgreSQL 連接失敗: {e}")
            return None
    
    def generate_user_id(self) -> str:
        """生成新的 Podwise ID (user_id)"""
        try:
            conn = self.get_db_connection()
            if not conn:
                raise Exception("無法連接資料庫")
                
            cursor = conn.cursor()
            
            # 查找最大的 Podwise ID
            cursor.execute("""
                SELECT user_id FROM users 
                WHERE user_id LIKE 'Podwise%' 
                ORDER BY CAST(SUBSTRING(user_id FROM 8) AS INTEGER) DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            
            if result:
                # 提取數字部分並加1
                last_number = int(result[0][7:])  # 跳過 'Podwise' 前綴
                new_number = last_number + 1
            else:
                # 如果沒有現有的 Podwise ID，從 1 開始
                new_number = 1
            
            # 生成新的 Podwise ID
            new_user_id = f"Podwise{new_number:04d}"
            
            cursor.close()
            conn.close()
            
            logger.info(f"生成新的 Podwise ID: {new_user_id}")
            return new_user_id
            
        except Exception as e:
            logger.error(f"生成 Podwise ID 失敗: {e}")
            raise
    
    def check_user_exists(self, user_id: str) -> bool:
        """檢查用戶是否存在"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，假設用戶不存在")
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"檢查用戶存在失敗: {e}")
            return False
    
    def register_user(self, username: str, email: Optional[str] = None, 
                     given_name: Optional[str] = None, family_name: Optional[str] = None) -> Dict[str, Any]:
        """註冊新用戶"""
        try:
            conn = self.get_db_connection()
            if not conn:
                raise Exception("無法連接資料庫")
                
            cursor = conn.cursor()
            
            # 生成新的 Podwise ID
            user_id = self.generate_user_id()
            
            # 插入新用戶
            cursor.execute("""
                INSERT INTO users (user_id, username, email, given_name, family_name, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING user_id, username
            """, (user_id, username, email, given_name, family_name))
            
            result = cursor.fetchone()
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"用戶註冊成功: {user_id}")
            return {
                "user_id": result[0],
                "username": result[1]
            }
            
        except Exception as e:
            logger.error(f"用戶註冊失敗: {e}")
            raise
    
    def save_user_preferences(self, user_id: str, main_category: str, 
                            sub_category: Optional[str] = None, language: Optional[str] = None,
                            duration_preference: Optional[str] = None) -> Dict[str, Any]:
        """儲存用戶偏好設定"""
        try:
            conn = self.get_db_connection()
            if not conn:
                raise Exception("無法連接資料庫")
                
            cursor = conn.cursor()
            
            # 檢查用戶是否存在，如果不存在則創建
            if not self.check_user_exists(user_id):
                logger.info(f"創建新用戶: {user_id}")
                cursor.execute("""
                    INSERT INTO users (user_id, username, created_at, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, user_id))
            
            # 更新用戶偏好
            cursor.execute("""
                INSERT INTO users (user_id, username, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"用戶偏好儲存成功: {user_id}")
            return {
                "success": True,
                "message": "用戶偏好儲存成功",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"儲存用戶偏好失敗: {e}")
            raise
    
    def record_user_feedback(self, user_id: str, podcast_id: int, episode_title: str,
                           like_count: int = 0, preview_play_count: int = 0) -> Dict[str, Any]:
        """記錄用戶反饋"""
        try:
            conn = self.get_db_connection()
            if not conn:
                raise Exception("無法連接資料庫")
                
            cursor = conn.cursor()
            
            # 檢查用戶是否存在，如果不存在則創建
            if not self.check_user_exists(user_id):
                logger.info(f"創建新用戶: {user_id}")
                cursor.execute("""
                    INSERT INTO users (user_id, username, created_at, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, user_id))
            
            # 插入用戶反饋
            cursor.execute("""
                INSERT INTO user_feedback (user_id, podcast_id, episode_title, like_count, preview_play_count, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (user_id, podcast_id, episode_title, like_count, preview_play_count))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"用戶反饋記錄成功: {user_id}")
            return {
                "success": True,
                "message": "用戶反饋記錄成功",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"記錄用戶反饋失敗: {e}")
            raise
    
    def get_category_recommendations(self, category: str, tag: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """根據類別獲取推薦節目"""
        try:
            # 1. 從 MinIO 獲取音檔列表
            bucket_name = CATEGORY_BUCKETS.get(category)
            if not bucket_name:
                raise ValueError(f"不支援的類別: {category}")
            
            if not self.minio_client or not self.minio_client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} 不存在")
                return []
            
            # 列出 bucket 中的音檔
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            mp3_files = [obj for obj in objects if obj.object_name and obj.object_name.lower().endswith('.mp3')]
            
            # 隨機打亂音檔順序
            random.shuffle(mp3_files)
            
            recommendations = []
            used_episode_ids = set()  # 用於追蹤已使用的節目 ID
            used_rss_ids = set()      # 用於追蹤已使用的 RSS ID
            
            for obj in mp3_files:
                if len(recommendations) >= limit:
                    break
                    
                if not obj.object_name:
                    continue
                    
                # 解析檔案名稱獲取 RSS 資訊
                file_info = self._parse_audio_filename(obj.object_name)
                if not file_info:
                    continue
                
                # 檢查 RSS ID 是否已使用（避免同一個節目的不同集數）
                if file_info['rss_id'] in used_rss_ids:
                    continue
                
                # 從 PostgreSQL 獲取節目資訊
                episode_info = self._get_episode_info(file_info['rss_id'], file_info['episode_title'])
                if not episode_info:
                    continue
                
                # 檢查節目 ID 是否已使用（避免重複節目）
                if episode_info['episode_id'] in used_episode_ids:
                    continue
                
                # 生成預簽名 URL
                presigned_url = self.minio_client.presigned_get_object(
                    bucket_name, 
                    obj.object_name,
                    expires=timedelta(hours=1)  # 1小時有效
                )
                
                # 獲取節目圖片
                podcast_image = self._get_podcast_image(file_info['rss_id'])
                
                # 生成 TAG
                if tag:
                    random_tags = self._generate_tags_with_selected(category, tag)
                else:
                    random_tags = self._generate_random_tags(category)
                
                recommendation = {
                    "file_name": obj.object_name,
                    "audio_url": presigned_url,
                    "podcast_name": episode_info['podcast_name'],
                    "episode_title": episode_info['episode_title'],
                    "episode_description": episode_info.get('description', ''),
                    "podcast_image": podcast_image,
                    "category": category,
                    "episode_id": episode_info['episode_id'],
                    "rss_id": file_info['rss_id'],
                    "tags": random_tags,
                    "user_feedback": {
                        "liked": False,
                        "played": False,
                        "rating": None
                    }
                }
                
                # 添加到推薦列表並記錄已使用的 ID
                recommendations.append(recommendation)
                used_episode_ids.add(episode_info['episode_id'])
                used_rss_ids.add(file_info['rss_id'])
                
                logger.info(f"添加推薦: {episode_info['podcast_name']} - {episode_info['episode_title']} (RSS: {file_info['rss_id']})")
            
            logger.info(f"從類別 {category} 找到 {len(recommendations)} 個不重複推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取類別推薦失敗: {e}")
            return []
    
    def _parse_audio_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """解析音檔檔案名稱"""
        try:
            # 實際格式: Spotify_RSS_{rss_id}_{episode_title}.mp3 (使用底線分隔)
            pattern = r'Spotify_RSS_(\d+)_(.+)\.mp3'
            match = re.match(pattern, filename)
            
            if match:
                return {
                    'rss_id': match.group(1),
                    'episode_title': match.group(2)
                }
            return None
            
        except Exception as e:
            logger.error(f"解析檔案名稱失敗: {e}")
            return None
    
    def _get_episode_info(self, rss_id: str, episode_title: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取節目資訊"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，使用預設節目資訊")
                return self._get_default_episode_info(rss_id, episode_title)
                
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # 嘗試用 RSS ID 查找節目
                cursor.execute("""
                    SELECT p.name as podcast_name, e.episode_title, e.description, e.episode_id
                    FROM episodes e
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.rss_link LIKE %s
                    LIMIT 1
                """, (f"%{rss_id}%",))
                
                result = cursor.fetchone()
                if result:
                    logger.info(f"找到節目資訊: {result['podcast_name']} - {result['episode_title']}")
                    return {
                        'podcast_name': result['podcast_name'],
                        'episode_title': result['episode_title'],
                        'description': result['description'],
                        'episode_id': result['episode_id']
                    }
                
                # 如果沒有找到，使用預設資訊
                return self._get_default_episode_info(rss_id, episode_title)
                
        except Exception as e:
            logger.error(f"獲取節目資訊失敗: {e}")
            return self._get_default_episode_info(rss_id, episode_title)
    
    def _get_default_episode_info(self, rss_id: str, episode_title: str) -> Dict[str, Any]:
        """獲取預設節目資訊"""
        return {
            'episode_id': int(rss_id) if rss_id.isdigit() else hash(rss_id) % 100000,
            'episode_title': episode_title,
            'description': f'來自 RSS {rss_id} 的節目',
            'podcast_name': f'Podcast {rss_id}',
            'podcast_id': int(rss_id) if rss_id.isdigit() else hash(rss_id) % 10000
        }
    
    def _get_podcast_image(self, rss_id: str) -> str:
        """獲取節目圖片 URL"""
        try:
            # 檢查 MinIO 客戶端是否可用
            if not self.minio_client:
                logger.error("MinIO 客戶端未初始化")
                return "http://localhost:8080/images/default_podcast.png"
            
            # 直接使用公開 URL，因為已設置 bucket 為公開讀取
            object_name = f"RSS_{rss_id}.jpg"
            public_url = f"http://localhost:9000/podcast-images/{object_name}"
            
            # 測試 URL 是否有效
            response = requests.head(public_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"找到節目圖片: {object_name}")
                return public_url
            else:
                logger.warning(f"圖片 {object_name} 不存在或無法存取")
                return "http://localhost:8080/images/default_podcast.png"
                
        except Exception as e:
            logger.error(f"獲取節目圖片失敗: {e}")
            return "http://localhost:8080/images/default_podcast.png"
    
    def _generate_random_tags(self, category: str) -> List[str]:
        """生成隨機 TAG"""
        category_tags = {
            "business": [
                "投資理財", "股票分析", "房地產", "創業", "職場技能", 
                "商業策略", "市場趨勢", "經濟分析", "財務規劃", "企業管理",
                "行銷策略", "品牌建立", "客戶服務", "供應鏈", "風險管理"
            ],
            "education": [
                "學習方法", "教育理念", "知識分享", "個人成長", "心理學",
                "生活智慧", "人際關係", "自我提升", "思考方法", "人生哲學",
                "心靈成長", "價值觀", "生活態度", "自我反思", "成長思維"
            ]
        }
        
        available_tags = category_tags.get(category, ["一般", "知識", "學習", "分享"])
        
        if len(available_tags) >= 4:
            selected_tags = random.sample(available_tags, 4)
        else:
            selected_tags = []
            while len(selected_tags) < 4:
                selected_tags.extend(random.sample(available_tags, min(4 - len(selected_tags), len(available_tags))))
        
        logger.info(f"為類別 {category} 生成 TAG: {selected_tags}")
        return selected_tags
    
    def _generate_tags_with_selected(self, category: str, selected_tag: str) -> List[str]:
        """生成包含指定 TAG 的標籤列表"""
        category_tags = {
            "business": [
                "投資理財", "股票分析", "房地產", "創業", "職場技能", 
                "商業策略", "市場趨勢", "經濟分析", "財務規劃", "企業管理",
                "行銷策略", "品牌建立", "客戶服務", "供應鏈", "風險管理"
            ],
            "education": [
                "學習方法", "教育理念", "知識分享", "個人成長", "心理學",
                "生活智慧", "人際關係", "自我提升", "思考方法", "人生哲學",
                "心靈成長", "價值觀", "生活態度", "自我反思", "成長思維"
            ]
        }
        
        available_tags = category_tags.get(category, ["一般", "知識", "學習", "分享"])
        
        if selected_tag not in available_tags:
            available_tags.append(selected_tag)
        
        other_tags = [t for t in available_tags if t != selected_tag]
        
        if len(other_tags) >= 3:
            other_selected = random.sample(other_tags, 3)
        else:
            other_selected = other_tags
        
        final_tags = [selected_tag] + other_selected
        final_tags = final_tags[:4]
        
        logger.info(f"為類別 {category} 生成包含 {selected_tag} 的 TAG: {final_tags}")
        return final_tags

# 創建 FastAPI 應用
app = FastAPI(title="Podwise 整合用戶管理服務", version="2.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建整合用戶服務實例
user_service = IntegratedUserService()

@app.get("/")
async def root():
    """根路徑"""
    return {"message": "Podwise 整合用戶管理服務", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "integrated_user_service"}

@app.post("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成新的 Podwise ID"""
    try:
        podwise_id = user_service.generate_user_id()
        return {
            "success": True,
            "podwise_id": podwise_id,
            "message": "Podwise ID 生成成功"
        }
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/register")
async def register_user(request: UserRegistrationRequest):
    """註冊新用戶"""
    try:
        result = user_service.register_user(
            username=request.user_id,
            email=None,
            given_name=None,
            family_name=None
        )
        return result
    except Exception as e:
        logger.error(f"用戶註冊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/preferences")
async def save_user_preferences(request: UserPreferenceRequest):
    """儲存用戶偏好"""
    try:
        result = user_service.save_user_preferences(
            user_id=request.user_id,
            main_category=request.main_category,
            sub_category=request.sub_category,
            language=request.language,
            duration_preference=request.duration_preference
        )
        return result
    except Exception as e:
        logger.error(f"儲存用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def record_feedback(request: UserFeedbackRequest):
    """記錄用戶反饋"""
    try:
        result = user_service.record_user_feedback(
            user_id=request.user_id,
            podcast_id=0,  # 使用預設值
            episode_title=request.episode_title,
            like_count=1 if request.action == "like" else 0,
            preview_play_count=0
        )
        return result
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/check/{user_id}")
async def check_user_exists(user_id: str):
    """檢查用戶是否存在"""
    try:
        exists = user_service.check_user_exists(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "exists": exists
        }
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/category/recommendations")
async def get_category_recommendations(request: CategoryRequest):
    """根據類別獲取推薦節目"""
    try:
        recommendations = user_service.get_category_recommendations(
            category=request.category,
            tag=request.tag,
            limit=3
        )
        
        return {
            "success": True,
            "category": request.category,
            "tag": request.tag,
            "recommendations": recommendations,
            "total_count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"獲取類別推薦失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007) 