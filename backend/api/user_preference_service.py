#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 用戶偏好收集服務
整合 MinIO 音檔搜尋、PostgreSQL 資料庫操作和用戶反饋記錄
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
import requests # Added for testing MinIO presigned URLs

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 資料庫配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "192.168.32.38"),
    "port": int(os.getenv("POSTGRES_PORT", "32432")),
    "database": os.getenv("POSTGRES_DB", "podcast"),
    "user": os.getenv("POSTGRES_USER", "bdse37"),
    "password": os.getenv("POSTGRES_PASSWORD", "111111")
}

# MinIO 配置
MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "bdse37"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "11111111"),
    "secure": False
}

# 類別映射（與 MinIO business-one-min-audio 一致）
CATEGORY_MAPPING = {
    "business": ["business", "投資理財", "股票分析", "經濟分析", "財務規劃", "投資", "理財"],
    "education": ["education", "教育", "學習", "科技", "知識", "技能"]
}

# 類別對應的 MinIO bucket
CATEGORY_BUCKETS = {
    "business": "business-one-min-audio",
    "education": "education-one-min-audio"
}

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

class UserPreferenceService:
    """用戶偏好收集服務核心類別"""
    
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
                from datetime import timedelta
                presigned_url = self.minio_client.presigned_get_object(
                    bucket_name, 
                    obj.object_name,
                    expires=timedelta(hours=1)  # 1小時有效
                )
                
                # 獲取節目圖片
                podcast_image = self._get_podcast_image(file_info['rss_id'])
                
                # 生成 TAG（如果有指定 tag，則包含該 tag；否則隨機生成）
                if tag:
                    # 如果指定了 tag，確保包含該 tag，並添加其他相關 tag
                    random_tags = self._generate_tags_with_selected(category, tag)
                else:
                    # 隨機生成 TAG
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
                    "tags": random_tags,  # 添加隨機 TAG
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
                
                # 如果沒有找到，嘗試更寬鬆的查詢
                logger.warning(f"未找到 RSS ID {rss_id} 的節目，嘗試更寬鬆查詢")
                cursor.execute("""
                    SELECT p.name as podcast_name, e.episode_title, e.description, e.episode_id
                    FROM episodes e
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.rss_link LIKE %s OR p.rss_link LIKE %s
                    LIMIT 1
                """, (f"%{rss_id}%", f"%id{rss_id}%"))
                
                result = cursor.fetchone()
                if result:
                    logger.info(f"寬鬆查詢找到節目資訊: {result['podcast_name']} - {result['episode_title']}")
                    return {
                        'podcast_name': result['podcast_name'],
                        'episode_title': result['episode_title'],
                        'description': result['description'],
                        'episode_id': result['episode_id']
                    }
                
                result = cursor.fetchone()
                if result:
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
            # 圖片命名格式：RSS_{rss_id}_{size}.jpg
            sizes = ['300', '640', '64']
            
            for size in sizes:
                try:
                    object_name = f"RSS_{rss_id}_{size}.jpg"
                    # 使用公開 URL
                    public_url = f"http://localhost:9000/podcast-images/{object_name}"
                    
                    # 測試 URL 是否有效
                    response = requests.head(public_url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"找到節目圖片: {object_name}")
                        return public_url
                        
                except Exception as e:
                    logger.debug(f"圖片 {object_name} 不存在或無法存取: {e}")
                    continue
            
            logger.warning(f"找不到 RSS ID {rss_id} 的節目圖片，使用預設圖片")
            return "http://localhost:8080/images/default_podcast.png"
                
        except Exception as e:
            logger.error(f"獲取節目圖片失敗: {e}")
            return "http://localhost:8080/images/default_podcast.png"
    
    def _generate_random_tags(self, category: str) -> List[str]:
        """生成隨機 TAG（一分鐘視聽中顯示四個相關 TAG）"""
        # 根據類別定義相關 TAG
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
        
        # 獲取對應類別的 TAG 池
        available_tags = category_tags.get(category, ["一般", "知識", "學習", "分享"])
        
        # 隨機選擇 4 個 TAG
        if len(available_tags) >= 4:
            selected_tags = random.sample(available_tags, 4)
        else:
            # 如果 TAG 不夠，重複選擇直到有 4 個
            selected_tags = []
            while len(selected_tags) < 4:
                selected_tags.extend(random.sample(available_tags, min(4 - len(selected_tags), len(available_tags))))
        
        logger.info(f"為類別 {category} 生成 TAG: {selected_tags}")
        return selected_tags
    
    def _generate_tags_with_selected(self, category: str, selected_tag: str) -> List[str]:
        """生成包含指定 TAG 的標籤列表"""
        # 根據類別定義相關 TAG
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
        
        # 獲取對應類別的 TAG 池
        available_tags = category_tags.get(category, ["一般", "知識", "學習", "分享"])
        
        # 確保選中的 tag 在池中
        if selected_tag not in available_tags:
            available_tags.append(selected_tag)
        
        # 移除選中的 tag，避免重複
        other_tags = [t for t in available_tags if t != selected_tag]
        
        # 隨機選擇 3 個其他 tag
        if len(other_tags) >= 3:
            other_selected = random.sample(other_tags, 3)
        else:
            other_selected = other_tags
        
        # 組合：選中的 tag + 3 個其他 tag
        final_tags = [selected_tag] + other_selected
        
        # 確保最多 4 個 tag
        final_tags = final_tags[:4]
        
        logger.info(f"為類別 {category} 生成包含 {selected_tag} 的 TAG: {final_tags}")
        return final_tags
    
    def record_user_feedback(self, user_id: str, episode_id: int, podcast_name: str, 
                           episode_title: str, rss_id: str, action: str, category: str) -> bool:
        """記錄用戶反饋"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，跳過反饋記錄")
                return False
            
            # 首先檢查用戶是否存在，如果不存在則創建
            user_numeric_id = self._get_or_create_user(user_id)
            if not user_numeric_id:
                logger.error(f"無法創建或獲取用戶: {user_id}")
                return False
                
            with conn.cursor() as cursor:
                # 檢查是否已存在記錄
                cursor.execute("""
                    SELECT user_id FROM user_feedback 
                    WHERE user_id = %s AND episode_id = %s
                """, (user_numeric_id, episode_id))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # 更新現有記錄
                    if action == "like":
                        cursor.execute("""
                            UPDATE user_feedback 
                            SET like_count = COALESCE(like_count, 0) + 1,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND episode_id = %s
                        """, (user_numeric_id, episode_id))
                    elif action == "unlike":
                        cursor.execute("""
                            UPDATE user_feedback 
                            SET like_count = GREATEST(COALESCE(like_count, 0) - 1, 0),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND episode_id = %s
                        """, (user_numeric_id, episode_id))
                else:
                    # 創建新記錄
                    cursor.execute("""
                        INSERT INTO user_feedback (user_id, episode_id, like_count, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (user_numeric_id, episode_id, 1 if action == "like" else 0))
                
                conn.commit()
                logger.info(f"用戶反饋記錄成功: {user_id} {action} {podcast_name}")
                return True
                
        except Exception as e:
            logger.error(f"記錄用戶反饋失敗: {e}")
            return False
    
    def _get_or_create_user(self, user_code: str) -> Optional[int]:
        """獲取或創建用戶，返回數字 ID"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            with conn.cursor() as cursor:
                # 檢查用戶是否存在（通過 user_code）
                cursor.execute("SELECT user_id FROM users WHERE user_code = %s", (user_code,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                # 如果不存在，創建新用戶
                cursor.execute("""
                    INSERT INTO users (user_code, username, created_at, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING user_id
                """, (user_code, user_code))
                new_user_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"創建新用戶: {user_code} -> ID: {new_user_id}")
                return new_user_id
        except Exception as e:
            logger.error(f"獲取或創建用戶失敗: {e}")
            return None
    
    def check_user_exists(self, user_id: str) -> bool:
        """檢查用戶是否存在"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，假設用戶不存在")
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE user_code = %s", (user_id,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"檢查用戶存在失敗: {e}")
            return False
    
    def get_audio_stream_url(self, rss_id: str, episode_title: str, category: str) -> str:
        """獲取音檔串流 URL"""
        try:
            # 根據類別確定 bucket
            bucket_name = CATEGORY_BUCKETS.get(category, "business-one-minutes-mp3")
            
            # 檢查 MinIO 客戶端是否可用
            if not self.minio_client:
                logger.warning("MinIO 客戶端未初始化")
                return ""
            
            # 在 MinIO 中搜尋對應的音檔
            if not self.minio_client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} 不存在")
                return ""
            
            # 列出 bucket 中的音檔
            objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
            mp3_files = [obj for obj in objects if obj.object_name and obj.object_name.lower().endswith('.mp3')]
            
            # 搜尋包含 rss_id 和 episode_title 的音檔
            target_file = None
            for obj in mp3_files:
                if obj.object_name:
                    filename = obj.object_name.lower()
                    # 檢查是否包含 RSS ID（格式：Spotify_RSS_{rss_id}_{episode_title}.mp3）
                    if f"spotify_rss_{rss_id.lower()}_" in filename:
                        # 檢查是否包含部分標題關鍵字
                        title_words = episode_title.lower().split()
                        if any(word in filename for word in title_words if len(word) > 2):
                            target_file = obj
                            break
                        # 如果沒有找到完全匹配，使用第一個包含 RSS ID 的檔案
                        if not target_file:
                            target_file = obj
            
            if target_file and target_file.object_name:
                # 生成預簽名 URL（有效期 1 小時）
                try:
                    url = self.minio_client.presigned_get_object(
                        bucket_name, 
                        target_file.object_name, 
                        expires=timedelta(hours=1)
                    )
                    logger.info(f"找到音檔: {target_file.object_name}")
                    logger.info(f"生成的預簽名 URL: {url[:100]}...")
                    return url
                except Exception as e:
                    logger.error(f"生成預簽名 URL 失敗: {e}")
                    return ""
            else:
                logger.warning(f"未找到對應的音檔: rss_id={rss_id}, episode_title={episode_title}")
                return ""
                
        except Exception as e:
            logger.error(f"獲取音檔串流 URL 失敗: {e}")
            return ""
    
    def create_user_and_record_preferences(self, user_id: str, category: str, 
                                         selected_episodes: List[Dict[str, Any]]) -> bool:
        """創建用戶並記錄偏好"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，跳過用戶創建")
                return False
            # 先 mapping user_code → user_id (int)
            user_numeric_id = self._get_or_create_user(user_id)
            if not user_numeric_id:
                logger.error(f"無法創建或獲取用戶: {user_id}")
                return False
            with conn.cursor() as cursor:
                # 更新用戶偏好類別
                cursor.execute("""
                    UPDATE users SET preferred_category = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (category, user_numeric_id))
                # 記錄選中的節目
                for episode in selected_episodes:
                    cursor.execute("""
                        INSERT INTO user_preferences (user_id, episode_id, podcast_name, episode_title, rss_id, category, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_numeric_id, 
                        episode.get('episode_id', 0),
                        episode.get('podcast_name', ''),
                        episode.get('episode_title', ''),
                        episode.get('rss_id', ''),
                        category,
                        datetime.now()
                    ))
                conn.commit()
                logger.info(f"用戶 {user_id} (ID: {user_numeric_id}) 記錄了 {len(selected_episodes)} 個偏好")
                return True
        except Exception as e:
            logger.error(f"創建用戶失敗: {e}")
            return False

# 創建 FastAPI 應用
app = FastAPI(title="Podwise User Preference Service", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建服務實例
preference_service = UserPreferenceService()

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "user_preference_service"}

@app.post("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成新的 Podwise ID"""
    try:
        # 獲取下一個可用的 Podwise ID 編號
        conn = preference_service.get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="無法連接資料庫")
            
        with conn.cursor() as cursor:
            # 查詢現有的最大 Podwise ID 編號
            cursor.execute("""
                SELECT user_code FROM users 
                WHERE user_code LIKE 'Podwise%' 
                ORDER BY CAST(SUBSTRING(user_code FROM 8) AS INTEGER) DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result and result[0]:
                # 提取現有最大編號
                last_id = result[0]
                try:
                    last_number = int(last_id[7:])  # 從第8個字符開始提取數字
                    next_number = last_number + 1
                except (IndexError, ValueError):
                    # 如果解析失敗，從 1 開始
                    next_number = 1
            else:
                # 如果沒有現有的 Podwise ID，從 1 開始
                next_number = 1
            
            # 生成新的 Podwise ID
            podwise_id = f"Podwise{next_number:04d}"  # 格式：Podwise0001, Podwise0002, ...
            
            # 在資料庫中創建用戶
            user_numeric_id = preference_service._get_or_create_user(podwise_id)
            
            if user_numeric_id:
                logger.info(f"生成 Podwise ID: {podwise_id} -> 資料庫 ID: {user_numeric_id}")
                return {
                    "success": True,
                    "podwise_id": podwise_id,
                    "user_id": user_numeric_id,
                    "message": "Podwise ID 生成成功"
                }
            else:
                raise HTTPException(status_code=500, detail="無法在資料庫中創建用戶")
                
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/category/recommendations")
async def get_category_recommendations(request: CategoryRequest):
    """根據類別獲取推薦節目"""
    try:
        recommendations = preference_service.get_category_recommendations(
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

@app.post("/api/feedback")
async def record_feedback(request: UserFeedbackRequest):
    """記錄用戶反饋"""
    try:
        success = preference_service.record_user_feedback(
            user_id=request.user_id,
            episode_id=request.episode_id,
            podcast_name=request.podcast_name,
            episode_title=request.episode_title,
            rss_id=request.rss_id,
            action=request.action,
            category=request.category
        )
        
        if success:
            return {
                "success": True,
                "message": f"成功記錄 {request.action} 操作",
                "feedback_id": f"{request.user_id}_{request.episode_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="記錄反饋失敗")
            
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/check/{user_id}")
async def check_user_exists(user_id: str):
    """檢查用戶是否存在"""
    try:
        exists = preference_service.check_user_exists(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "exists": exists
        }
        
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/register")
async def register_user_and_preferences(request: UserRegistrationRequest):
    """註冊用戶並記錄偏好"""
    try:
        success = preference_service.create_user_and_record_preferences(
            user_id=request.user_id,
            category=request.category,
            selected_episodes=request.selected_episodes
        )
        
        if success:
            return {
                "success": True,
                "message": "成功註冊用戶並記錄偏好",
                "user_id": request.user_id
            }
        else:
            raise HTTPException(status_code=500, detail="註冊用戶失敗")
            
    except Exception as e:
        logger.error(f"註冊用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audio/stream")
async def get_audio_stream(request: dict):
    """獲取音檔串流 URL"""
    try:
        rss_id = request.get("rss_id", "")
        episode_title = request.get("episode_title", "")
        category = request.get("category", "business")
        
        if not rss_id or not episode_title:
            raise HTTPException(status_code=400, detail="缺少必要參數: rss_id 或 episode_title")
        
        audio_url = preference_service.get_audio_stream_url(rss_id, episode_title, category)
        
        return {
            "success": True,
            "audio_url": audio_url,
            "rss_id": rss_id,
            "episode_title": episode_title
        }
        
    except Exception as e:
        logger.error(f"獲取音檔串流失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 