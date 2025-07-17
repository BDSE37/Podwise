#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 核心服務管理器
統一管理所有 Podwise 功能，符合 OOP 設計原則
重構：以 MinIO 音檔為主，針對 Step1、Step2、Step3 進行處理
使用 CSV 檔案快取音檔列表，提高效能
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
import pandas as pd
import os

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG
from minio.api import Minio
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

class PodwiseServiceManager:
    """Podwise 核心服務管理器"""
    
    def __init__(self):
        """初始化服務管理器"""
        self.minio_client = None
        self.db_connection = None
        self._init_connections()
        
        # 類別配置（修正為正確的 bucket 名稱）
        self.category_buckets = {
            "business": "business-one-min-audio",
            "education": "education-one-min-audio"
        }
        
        self.category_tags = {
            "business": [
                "投資理財", "股票分析", "經濟分析", "財務規劃", 
                "企業管理", "領導力", "市場趨勢", "創業", "商業策略"
            ],
            "education": [
                "學習方法", "教育理念", "知識分享", "個人成長", 
                "心理學", "自我提升", "技能發展", "創新思維", "數位轉型"
            ]
        }
        
        # CSV 快取檔案路徑
        self.csv_cache_dir = Path(backend_path) / "analysis_output"
        self.csv_cache_files = {
            "business": self.csv_cache_dir / "business_episodes_analysis.csv",
            "education": self.csv_cache_dir / "education_episodes_analysis.csv"
        }
        
        # 快取 MinIO 音檔資訊
        self._minio_episodes_cache = {}
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=24)  # 24小時快取（使用 CSV）
    
    def _init_connections(self):
        """初始化資料庫和 MinIO 連接"""
        try:
            # 初始化 MinIO 客戶端
            self.minio_client = Minio(
                MINIO_CONFIG["endpoint"],
                access_key=MINIO_CONFIG["access_key"],
                secret_key=MINIO_CONFIG["secret_key"],
                secure=MINIO_CONFIG["secure"]
            )
            logger.info("✅ MinIO 連接成功")
            
        except Exception as e:
            logger.error(f"❌ MinIO 連接失敗: {e}")
            self.minio_client = None
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            if not self.db_connection or self.db_connection.closed:
                self.db_connection = psycopg2.connect(**POSTGRES_CONFIG)
            return self.db_connection
        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {e}")
            return None
    
    def _load_episodes_from_csv(self, category: str) -> List[Dict]:
        """從 CSV 檔案載入音檔資訊"""
        try:
            csv_file = self.csv_cache_files.get(category)
            if not csv_file or not csv_file.exists():
                logger.warning(f"CSV 檔案不存在: {csv_file}")
                return []
            
            # 讀取 CSV 檔案
            df = pd.read_csv(csv_file)
            logger.info(f"從 CSV 載入 {category} 類別: {len(df)} 個音檔")
            
            # 轉換為字典列表
            episodes = []
            for _, row in df.iterrows():
                # 構建正確的音檔 URL，移除過期的預簽名參數
                podcast_id = str(row['podcast_id'])
                episode_title = str(row['episode_title'])
                category = str(row['category'])
                
                # 根據類別選擇正確的 bucket
                bucket_map = {
                    "business": "business-one-min-audio",
                    "education": "education-one-min-audio"
                }
                bucket = bucket_map.get(category, "business-one-min-audio")
                
                # 構建正確的音檔 URL 格式：RSS_{podcast_id}_{episode_title}.mp3
                audio_url = f"http://192.168.32.66:30090/{bucket}/RSS_{podcast_id}_{episode_title}.mp3"
                
                episode_info = {
                    "podcast_id": int(podcast_id),
                    "podcast_name": row['podcast_name'],
                    "episode_title": episode_title,
                    "audio_url": audio_url,  # 使用重新構建的 URL
                    "image_url": row['image_url'],
                    "minio_filename": row['minio_filename'],
                    "category": category,
                    "rss_id": row['rss_id']
                }
                episodes.append(episode_info)
            
            return episodes
            
        except Exception as e:
            logger.error(f"載入 CSV 檔案失敗: {e}")
            return []
    
    def _load_minio_episodes(self, force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """從 CSV 檔案載入所有音檔資訊，以音檔為主，確保 podcast_id 與 podcast_name 對應"""
        try:
            # 檢查快取是否有效
            if (not force_refresh and 
                self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < self._cache_duration):
                logger.info("使用快取的 CSV 音檔資訊")
                return self._minio_episodes_cache
            
            episodes_by_category = {"business": [], "education": []}
            
            # 從 CSV 檔案載入每個類別的音檔
            for category in self.category_buckets.keys():
                episodes = self._load_episodes_from_csv(category)
                episodes_by_category[category] = episodes
                logger.info(f"載入 {category} 類別: {len(episodes)} 個音檔")
            
            # 更新快取
            self._minio_episodes_cache = episodes_by_category
            self._cache_timestamp = datetime.now()
            
            logger.info(f"CSV 音檔載入完成：商業 {len(episodes_by_category['business'])} 個，教育 {len(episodes_by_category['education'])} 個")
            return episodes_by_category
            
        except Exception as e:
            logger.error(f"載入 CSV 音檔失敗: {e}")
            return {}
    
    def get_category_tags(self, category: str) -> List[str]:
        """獲取類別標籤（Step2）"""
        tags = self.category_tags.get(category, self.category_tags["business"])
        # 隨機選擇 4 個標籤
        return random.sample(tags, min(4, len(tags)))
    
    def get_episodes_by_tag(self, category: str, tag: str, limit: int = 3) -> List[Dict]:
        """根據標籤獲取節目（Step3）- 使用 CSV 快取，提高效能"""
        try:
            # 載入 CSV 音檔資訊
            minio_episodes = self._load_minio_episodes()
            category_episodes = minio_episodes.get(category, [])
            
            if not category_episodes:
                logger.warning(f"在 CSV 中找不到 {category} 類別的音檔，使用備用資料")
                return self._get_default_episodes(category, limit)
            
            # 如果有標籤，嘗試從資料庫匹配（僅在需要時連接資料庫）
            if tag:
                matched_episodes = self._match_episodes_with_tags_from_csv(category_episodes, tag, limit)
                if matched_episodes and len(matched_episodes) >= limit:
                    logger.info(f"標籤匹配成功，返回 {len(matched_episodes)} 個節目")
                    return matched_episodes
                elif matched_episodes:
                    logger.info(f"標籤匹配部分成功，返回 {len(matched_episodes)} 個節目，補充隨機節目")
                    # 補充隨機節目到指定數量
                    remaining = limit - len(matched_episodes)
                    available_episodes = [ep for ep in category_episodes if ep not in matched_episodes]
                    if available_episodes:
                        additional_episodes = random.sample(available_episodes, min(remaining, len(available_episodes)))
                        matched_episodes.extend(additional_episodes)
                    return matched_episodes
            
            # 如果沒有標籤匹配或標籤為空，返回隨機音檔
            logger.info(f"返回 {category} 類別的隨機音檔")
            random_episodes = random.sample(category_episodes, min(limit, len(category_episodes)))
            
            # 補充完整資訊（podcast_name 已在 CSV 中包含）
            for episode in random_episodes:
                # 確保有完整的 episode_id（用於 Step4 保存）
                episode['episode_id'] = self._get_episode_id(episode['podcast_id'], episode['episode_title'])
                
                logger.info(f"Step3 節目資訊: {episode['podcast_name']} - {episode['episode_title']}")
                logger.info(f"  音檔 URL: {episode['audio_url']}")
                logger.info(f"  圖片 URL: {episode['image_url']}")
                logger.info(f"  Episode ID: {episode['episode_id']}")
            
            return random_episodes
            
        except Exception as e:
            logger.error(f"獲取節目失敗: {e}")
            logger.info("使用備用資料作為最後方案")
            return self._get_default_episodes(category, limit)
    
    def _match_episodes_with_tags_from_csv(self, csv_episodes: List[Dict], tag: str, limit: int) -> List[Dict]:
        """將 CSV 音檔與資料庫標籤匹配（僅在需要時連接資料庫）"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接到資料庫，返回隨機音檔")
                return random.sample(csv_episodes, min(limit, len(csv_episodes)))
            
            # 提取所有 podcast_id 和 episode_title
            episode_keys = {(ep['podcast_id'], ep['episode_title']) for ep in csv_episodes}
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # 查詢有該標籤且存在於 CSV 中的節目
                cursor.execute("""
                    SELECT DISTINCT 
                        e.episode_id,
                        e.episode_title,
                        p.podcast_id,
                        COALESCE(p.podcast_name, 'Unknown Podcast') as podcast_name,
                        COALESCE(p.category, 'business') as category
                    FROM episodes e
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    JOIN episode_topics et ON e.episode_id = et.episode_id
                    WHERE et.topic_tag = %s
                    LIMIT %s
                """, (tag, limit * 2))  # 查詢更多以確保有足夠的匹配
                
                db_episodes = cursor.fetchall()
                logger.info(f"資料庫中找到 {len(db_episodes)} 個標籤匹配的節目")
                
                # 匹配 CSV 音檔
                matched_episodes = []
                for db_ep in db_episodes:
                    if (db_ep['podcast_id'], db_ep['episode_title']) in episode_keys:
                        # 找到對應的 CSV 音檔
                        for csv_ep in csv_episodes:
                            if (csv_ep['podcast_id'] == db_ep['podcast_id'] and 
                                csv_ep['episode_title'] == db_ep['episode_title']):
                                # 合併資料（podcast_name 已在 CSV 中包含）
                                matched_episode = csv_ep.copy()
                                # 驗證 podcast_name 是否正確
                                if csv_ep['podcast_name'] != db_ep['podcast_name']:
                                    logger.warning(f"Podcast 名稱不匹配: CSV={csv_ep['podcast_name']}, DB={db_ep['podcast_name']}")
                                matched_episodes.append(matched_episode)
                                break
                        
                        if len(matched_episodes) >= limit:
                            break
                
                logger.info(f"成功匹配 {len(matched_episodes)} 個節目")
                return matched_episodes
                
        except Exception as e:
            logger.error(f"匹配標籤失敗: {e}")
            return random.sample(csv_episodes, min(limit, len(csv_episodes)))
    
    def get_random_audio(self, category: str) -> Dict:
        """獲取隨機音檔（Step1）- 使用 CSV 快取"""
        try:
            # 載入 CSV 音檔資訊
            minio_episodes = self._load_minio_episodes()
            category_episodes = minio_episodes.get(category, [])
            
            if not category_episodes:
                return {"success": False, "message": f"在 {category} 類別中找不到音檔"}
            
            # 隨機選擇一個音檔
            random_episode = random.choice(category_episodes)
            
            return {
                "success": True,
                "audio_url": random_episode['audio_url'],
                "podcast_name": random_episode['podcast_name'],  # 使用已包含的 podcast_name
                "episode_title": random_episode['episode_title'],
                "rss_id": random_episode['rss_id'],
                "category": category
            }
            
        except Exception as e:
            logger.error(f"獲取隨機音檔失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def get_podcast_name(self, podcast_id: int) -> str:
        """從資料庫獲取 podcast 名稱"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return f"Podcast_{podcast_id}"
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT podcast_name FROM podcasts WHERE podcast_id = %s", 
                    (podcast_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else f"Podcast_{podcast_id}"
                
        except Exception as e:
            logger.error(f"獲取 podcast 名稱失敗: {e}")
            return f"Podcast_{podcast_id}"
    
    def generate_user_id(self) -> str:
        """生成新的用戶 ID"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return f"Podwise{random.randint(1000, 9999)}"
            
            with conn.cursor() as cursor:
                # 查找最大的用戶 ID
                cursor.execute("SELECT MAX(user_id) FROM users")
                result = cursor.fetchone()
                max_id = result[0] if result[0] else 0
                
                new_id = max_id + 1
                user_code = f"Podwise{new_id:04d}"
                
                # 插入新用戶
                cursor.execute("""
                    INSERT INTO users (user_id, user_identifier, user_type, is_active)
                    VALUES (%s, %s, 'guest', true)
                """, (new_id, user_code))
                
                conn.commit()
                return user_code
                
        except Exception as e:
            logger.error(f"生成用戶 ID 失敗: {e}")
            return f"Podwise{random.randint(1000, 9999)}"
    
    def check_user_exists(self, user_code: str) -> bool:
        """檢查用戶是否存在"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE user_id = %s", 
                    (user_code,)
                )
                result = cursor.fetchone()
                return bool(result)
                
        except Exception as e:
            logger.error(f"檢查用戶存在性失敗: {e}")
            return False
    
    def save_user_preferences(self, user_id: str, main_category: str, sub_category: str = "") -> Dict:
        """保存用戶偏好"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "資料庫連接失敗"}
            
            # 獲取用戶 ID
            user_db_id = self._get_user_db_id(user_id)
            if not user_db_id:
                return {"success": False, "error": "用戶不存在"}
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_preferences (user_id, category, preference_score)
                    VALUES (%s, %s, 0.8)
                    ON CONFLICT (user_id, category) 
                    DO UPDATE SET 
                        preference_score = 0.8,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_db_id, main_category))
                
                conn.commit()
                return {"success": True, "message": "偏好保存成功"}
                
        except Exception as e:
            logger.error(f"保存用戶偏好失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def record_user_feedback(self, user_id: str, episode_id: int, episode_title: str, 
                           like_count: int = 0, preview_play_count: int = 0) -> Dict:
        """記錄用戶反饋"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "資料庫連接失敗"}
            
            # 獲取用戶 ID
            user_db_id = self._get_user_db_id(user_id)
            if not user_db_id:
                return {"success": False, "error": "用戶不存在"}
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_feedback 
                    (user_id, episode_id, like_count, preview_play_count, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, episode_id) 
                    DO UPDATE SET 
                        like_count = user_feedback.like_count + %s,
                        preview_play_count = user_feedback.preview_play_count + %s,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_db_id, episode_id, like_count, preview_play_count, like_count, preview_play_count))
                
                conn.commit()
                return {"success": True, "message": "反饋記錄成功"}
                
        except Exception as e:
            logger.error(f"記錄用戶反饋失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_user_db_id(self, user_code: str) -> Optional[int]:
        """獲取用戶的資料庫 ID"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE user_id = %s", 
                    (user_code,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"獲取用戶資料庫 ID 失敗: {e}")
            return None
    
    def _get_episode_id(self, podcast_id: int, episode_title: str) -> int:
        """從資料庫獲取 episode_id"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return 0  # 如果無法連接資料庫，返回 0
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT episode_id FROM episodes 
                    WHERE podcast_id = %s AND episode_title = %s
                """, (podcast_id, episode_title))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"獲取 episode_id 失敗: {e}")
            return 0
    
    def save_step4_user_preferences(self, user_id: str, main_category: str, selected_episodes: List[Dict]) -> Dict:
        """保存 Step4 用戶偏好和選中的節目（用於 RAG Pipeline）"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "資料庫連接失敗"}
            
            # 獲取用戶的資料庫 ID
            user_db_id = self._get_user_db_id(user_id)
            if not user_db_id:
                return {"success": False, "error": "用戶不存在"}
            
            with conn.cursor() as cursor:
                # 1. 保存用戶偏好
                cursor.execute("""
                    INSERT INTO user_preferences (user_id, category, preference_score)
                    VALUES (%s, %s, 0.9)
                    ON CONFLICT (user_id, category) 
                    DO UPDATE SET 
                        preference_score = 0.9,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_db_id, main_category))
                
                # 2. 保存選中的節目到用戶偏好
                for episode in selected_episodes:
                    episode_id = episode.get('episode_id', 0)
                    if episode_id > 0:
                        cursor.execute("""
                            INSERT INTO user_feedback 
                            (user_id, episode_id, like_count, preview_play_count, created_at, updated_at)
                            VALUES (%s, %s, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (user_id, episode_id) 
                            DO UPDATE SET 
                                like_count = user_feedback.like_count + 1,
                                preview_play_count = user_feedback.preview_play_count + 1,
                                updated_at = CURRENT_TIMESTAMP
                        """, (user_db_id, episode_id))
                
                # 3. 保存用戶會話資訊（用於 RAG Pipeline）
                session_data = {
                    "user_id": user_id,
                    "main_category": main_category,
                    "selected_episodes": selected_episodes,
                    "timestamp": datetime.now().isoformat()
                }
                
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_data, created_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, (user_db_id, json.dumps(session_data)))
                
                conn.commit()
                
                logger.info(f"Step4 用戶偏好保存成功: {user_id}, 類別: {main_category}, 選中節目: {len(selected_episodes)} 個")
                
                return {
                    "success": True,
                    "message": "偏好保存成功",
                    "user_id": user_id,
                    "main_category": main_category,
                    "selected_episodes_count": len(selected_episodes)
                }
                
        except Exception as e:
            logger.error(f"保存 Step4 用戶偏好失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_context_for_rag(self, user_id: str) -> Dict:
        """獲取用戶上下文資訊（用於 RAG Pipeline）"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"user_id": user_id, "context": "無法連接資料庫"}
            
            user_db_id = self._get_user_db_id(user_id)
            if not user_db_id:
                return {"user_id": user_id, "context": "用戶不存在"}
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # 獲取用戶偏好
                cursor.execute("""
                    SELECT category, preference_score 
                    FROM user_preferences 
                    WHERE user_id = %s 
                    ORDER BY preference_score DESC
                """, (user_db_id,))
                preferences = cursor.fetchall()
                
                # 獲取最近的會話資訊
                cursor.execute("""
                    SELECT session_data 
                    FROM user_sessions 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (user_db_id,))
                session_result = cursor.fetchone()
                
                # 獲取用戶喜歡的節目
                cursor.execute("""
                    SELECT e.episode_title, p.podcast_name, p.category
                    FROM user_feedback uf
                    JOIN episodes e ON uf.episode_id = e.episode_id
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE uf.user_id = %s AND uf.like_count > 0
                    ORDER BY uf.updated_at DESC
                    LIMIT 5
                """, (user_db_id,))
                liked_episodes = cursor.fetchall()
                
                context = {
                    "user_id": user_id,
                    "preferences": [{"category": p['category'], "score": p['preference_score']} for p in preferences],
                    "recent_session": json.loads(session_result['session_data']) if session_result else None,
                    "liked_episodes": [{"title": ep['episode_title'], "podcast": ep['podcast_name'], "category": ep['category']} for ep in liked_episodes],
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"獲取用戶上下文: {user_id}, 偏好: {len(preferences)}, 喜歡節目: {len(liked_episodes)}")
                return context
                
        except Exception as e:
            logger.error(f"獲取用戶上下文失敗: {e}")
            return {"user_id": user_id, "context": f"獲取失敗: {str(e)}"}
    
    def close_connections(self):
        """關閉所有連接"""
        try:
            if self.db_connection and not self.db_connection.closed:
                self.db_connection.close()
                logger.info("資料庫連接已關閉")
        except Exception as e:
            logger.error(f"關閉資料庫連接失敗: {e}")

    def _get_default_episodes(self, category: str, limit: int = 3) -> List[Dict]:
        """獲取預設節目（當 CSV 中沒有音檔時）- 優先使用資料庫，最後才用寫死資料"""
        try:
            logger.info(f"CSV 中沒有音檔，嘗試從資料庫獲取節目，類別: {category}")
            
            # 優先從資料庫隨機獲取節目
            conn = self.get_db_connection()
            if not conn:
                logger.warning("無法連接資料庫，使用寫死資料")
                return self._get_fallback_episodes(category, limit)
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # 隨機查詢指定類別的節目
                cursor.execute("""
                    SELECT DISTINCT 
                        e.episode_id,
                        e.episode_title,
                        p.podcast_id,
                        COALESCE(p.podcast_name, 'Unknown Podcast') as podcast_name,
                        COALESCE(p.category, %s) as category,
                        RANDOM() as random_order
                    FROM episodes e
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE COALESCE(p.category, %s) = %s
                    ORDER BY random_order
                    LIMIT %s
                """, (category, category, category, limit))
                
                episodes = cursor.fetchall()
                logger.info(f"從資料庫隨機獲取到 {len(episodes)} 個節目")
                
                if episodes:
                    # 轉換為標準格式
                    result = []
                    for episode in episodes:
                        episode_info = {
                            "podcast_id": episode['podcast_id'],
                            "episode_title": episode['episode_title'],
                            "podcast_name": episode['podcast_name'],
                            "audio_url": "",  # 預設節目沒有音檔
                            "image_url": f"http://192.168.32.66:30090/podcast-images/RSS_{episode['podcast_id']}_300.jpg",
                            "rss_id": f"RSS_{episode['podcast_id']}",
                            "episode_id": episode['episode_id'],
                            "category": episode['category'],
                            "tags": self._get_random_tags_for_episode(episode['episode_id'])
                        }
                        result.append(episode_info)
                    
                    logger.info(f"成功從資料庫獲取 {len(result)} 個節目")
                    return result
                else:
                    logger.warning(f"資料庫中沒有 {category} 類別的節目，使用寫死資料")
                    return self._get_fallback_episodes(category, limit)
                    
        except Exception as e:
            logger.error(f"獲取資料庫節目失敗: {e}")
            logger.info("使用寫死資料作為最後備用方案")
            return self._get_fallback_episodes(category, limit)
    
    def _get_random_tags_for_episode(self, episode_id: int) -> List[str]:
        """為節目獲取隨機標籤"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return ["一般", "推薦", "精選"]
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT topic_tag FROM episode_topics 
                    WHERE episode_id = %s 
                    ORDER BY RANDOM() 
                    LIMIT 3
                """, (episode_id,))
                
                tags = [row[0] for row in cursor.fetchall()]
                return tags if tags else ["一般", "推薦", "精選"]
                
        except Exception as e:
            logger.error(f"獲取節目標籤失敗: {e}")
            return ["一般", "推薦", "精選"]
    
    def _get_fallback_episodes(self, category: str, limit: int = 3) -> List[Dict]:
        """獲取寫死的備用節目（當 CSV 和資料庫都無法連接時）"""
        logger.info(f"使用寫死備用節目，類別: {category}")
        
        if category == "business":
            fallback_episodes = [
                {
                    "podcast_id": 262026947,
                    "episode_title": "投資理財精選",
                    "podcast_name": "股癌 Gooaye",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_262026947_300.jpg",
                    "rss_id": "RSS_262026947",
                    "episode_id": 1,
                    "category": "business",
                    "tags": ["投資理財", "股票分析", "市場趨勢", "經濟分析"]
                },
                {
                    "podcast_id": 1493189417,
                    "episode_title": "AI 技術趨勢",
                    "podcast_name": "矽谷輕鬆談",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_1493189417_300.jpg",
                    "rss_id": "RSS_1493189417",
                    "episode_id": 2,
                    "category": "business",
                    "tags": ["科技趨勢", "人工智慧", "創新思維", "數位轉型"]
                },
                {
                    "podcast_id": 1590058994,
                    "episode_title": "管理思維分享",
                    "podcast_name": "天下學習",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_1590058994_300.jpg",
                    "rss_id": "RSS_1590058994",
                    "episode_id": 3,
                    "category": "business",
                    "tags": ["企業管理", "領導力", "學習方法", "個人成長"]
                }
            ]
        else:  # education
            fallback_episodes = [
                {
                    "podcast_id": 1533782597,
                    "episode_title": "學習方法論",
                    "podcast_name": "啟點文化一天聽一點",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_1533782597_300.jpg",
                    "rss_id": "RSS_1533782597",
                    "episode_id": 4,
                    "category": "education",
                    "tags": ["學習方法", "教育理念", "知識分享", "個人成長"]
                },
                {
                    "podcast_id": 1513786617,
                    "episode_title": "未來教育趨勢",
                    "podcast_name": "文森說書",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_1513786617_300.jpg",
                    "rss_id": "RSS_1513786617",
                    "episode_id": 5,
                    "category": "education",
                    "tags": ["教育科技", "未來趨勢", "創新教育", "數位學習"]
                },
                {
                    "podcast_id": 1452688611,
                    "episode_title": "自我提升指南",
                    "podcast_name": "大人的Small Talk",
                    "audio_url": "",
                    "image_url": "http://192.168.32.66:30090/podcast-images/RSS_1452688611_300.jpg",
                    "rss_id": "RSS_1452688611",
                    "episode_id": 6,
                    "category": "education",
                    "tags": ["個人成長", "心理學", "自我提升", "心靈成長"]
                }
            ]
        
        # 返回指定數量的備用節目
        return fallback_episodes[:limit]

# 創建全局實例
podwise_service = PodwiseServiceManager() 