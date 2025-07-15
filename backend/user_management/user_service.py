#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 用戶偏好服務
提供用戶管理、偏好收集、反饋記錄等功能
採用 OOP 設計原則
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, Any, Optional, List
from datetime import datetime
import random

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserPreferenceService:
    """用戶偏好服務類別"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """初始化用戶偏好服務"""
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        logger.info("用戶偏好服務初始化完成")
    
    def _connect(self) -> bool:
        """建立資料庫連接"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"]
            )
            self.cursor = self.connection.cursor()
            logger.info("資料庫連接建立成功")
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {str(e)}")
            return False
    
    def _close(self):
        """關閉資料庫連接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("資料庫連接已關閉")
            
        except Exception as e:
            logger.error(f"關閉連接失敗: {str(e)}")
    
    def health_check(self) -> bool:
        """健康檢查"""
        try:
            if not self._connect():
                return False
            
            # 測試查詢
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            
            self._close()
            return result is not None
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return False
    
    def generate_podwise_id(self) -> Dict[str, Any]:
        """生成新的 Podwise ID"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                return {"success": False, "error": "資料庫游標未初始化"}
            
            # 獲取當前最大的 Podwise ID 編號
            self.cursor.execute("""
                SELECT user_id FROM users 
                WHERE user_id LIKE 'Podwise%' 
                ORDER BY CAST(SUBSTRING(user_id FROM 8) AS INTEGER) DESC 
                LIMIT 1
            """)
            result = self.cursor.fetchone()
            
            if result:
                # 解析現有編號並加1
                last_id = result[0]
                if last_id.startswith('Podwise'):
                    try:
                        last_number = int(last_id[7:])  # 提取 Podwise 後面的數字
                        next_number = last_number + 1
                    except ValueError:
                        next_number = 1
                else:
                    next_number = 1
            else:
                next_number = 1
            
            # 生成新的 Podwise ID（格式：Podwise0001, Podwise0002, ...）
            user_id = f"Podwise{next_number:04d}"  # 4位數字，不足補0
            
            # 創建新用戶
            self.cursor.execute("""
                INSERT INTO users (user_id, is_active, created_at, updated_at)
                VALUES (%s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id
            """, (user_id,))
            
            result = self.cursor.fetchone()
            if not result:
                self._close()
                return {"success": False, "error": "無法創建新用戶"}
            
            self.connection.commit()
            self._close()
            
            logger.info(f"生成 Podwise ID: {user_id}")
            return {
                "success": True,
                "podwise_id": user_id,
                "user_id": user_id,
                "message": "Podwise ID 生成成功"
            }
            
        except Exception as e:
            logger.error(f"生成 Podwise ID 失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)}
    
    def check_user_exists(self, user_code: str) -> bool:
        """檢查用戶是否存在"""
        try:
            if not self._connect():
                return False
            
            if not self.cursor:
                logger.error("資料庫游標未初始化")
                return False
            
            # 檢查 Podwise ID 是否存在
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_code,))
            result = self.cursor.fetchone()
            
            self._close()
            return result is not None
            
        except Exception as e:
            logger.error(f"檢查用戶存在性失敗: {e}")
            self._close()
            return False
    
    def save_user_preferences(self, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """儲存用戶偏好"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                return {"success": False, "error": "資料庫游標未初始化"}
            
            user_code = preferences_data.get("user_code")
            main_category = preferences_data.get("main_category", "business")
            selected_tag = preferences_data.get("selected_tag", "")
            liked_episodes = preferences_data.get("liked_episodes", [])
            
            if not user_code:
                return {"success": False, "error": "缺少用戶代碼"}
            
            # 使用 Podwise ID 作為 user_id
            user_id = user_code
            
            # 檢查用戶是否存在，如果不存在則創建
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                # 創建新用戶
                self.cursor.execute("""
                    INSERT INTO users (user_id, is_active, created_at, updated_at)
                    VALUES (%s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING user_id
                """, (user_id,))
                result = self.cursor.fetchone()
                if not result:
                    self._close()
                    return {"success": False, "error": "無法創建新用戶"}
                
                logger.info(f"創建新用戶: {user_code}")
            
            # 儲存喜歡的節目到 user_feedback 表
            for episode in liked_episodes:
                episode_id = episode.get("episode_id", 1)
                # 使用 INSERT 而不是 ON CONFLICT，因為可能沒有唯一約束
                self.cursor.execute("""
                    INSERT INTO user_feedback (user_id, episode_id, like_count, heart_like, created_at, updated_at)
                    VALUES (%s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, episode_id, 1))
            
            self.connection.commit()
            self._close()
            
            return {"success": True, "message": "用戶偏好儲存成功", "user_code": user_code}
            
        except Exception as e:
            logger.error(f"儲存用戶偏好失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)}
    
    def record_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """記錄用戶反饋"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                return {"success": False, "error": "資料庫游標未初始化"}
            
            user_code = feedback_data.get("user_code")
            episode_id = feedback_data.get("episode_id", 1)
            action = feedback_data.get("action", "like")
            
            if not user_code:
                return {"success": False, "error": "缺少用戶代碼"}
            
            # 使用 Podwise ID 作為 user_id
            user_id = user_code
            
            # 檢查用戶是否存在，如果不存在則創建
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            
            if not result:
                # 創建新用戶
                self.cursor.execute("""
                    INSERT INTO users (user_id, is_active, created_at, updated_at)
                    VALUES (%s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING user_id
                """, (user_id,))
                result = self.cursor.fetchone()
                if not result:
                    self._close()
                    return {"success": False, "error": "無法創建新用戶"}
            
            # 處理 episode_id：如果是字串（如 RSS_xxx），轉換為數字
            try:
                if isinstance(episode_id, str) and episode_id.startswith('RSS_'):
                    # 提取數字部分
                    numeric_id = int(episode_id.split('_')[1])
                    episode_id = numeric_id
                else:
                    episode_id = int(episode_id)
            except (ValueError, IndexError):
                # 如果無法轉換，使用預設值
                episode_id = 1
            
            # 記錄反饋
            if action == "like":
                self.cursor.execute("""
                    INSERT INTO user_feedback (user_id, episode_id, like_count, heart_like, created_at, updated_at)
                    VALUES (%s, %s, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, episode_id))
            elif action == "dislike":
                self.cursor.execute("""
                    INSERT INTO user_feedback (user_id, episode_id, dislike_count, created_at, updated_at)
                    VALUES (%s, %s, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (user_id, episode_id))
            
            self.connection.commit()
            self._close()
            
            return {"success": True, "message": "反饋記錄成功"}
            
        except Exception as e:
            logger.error(f"記錄反饋失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)}
    
    def get_user_preferences(self, user_code: str) -> Dict[str, Any]:
        """獲取用戶偏好"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                logger.error("資料庫游標未初始化")
                return {"success": False, "error": "資料庫游標未初始化"}
            
            # 獲取用戶偏好
            self.cursor.execute("""
                SELECT up.category, up.preference_score, up.created_at
                FROM user_preferences up
                JOIN users u ON up.user_id = u.user_id
                WHERE u.user_code = %s
                ORDER BY up.preference_score DESC
            """, (user_code,))
            
            preferences = []
            for row in self.cursor.fetchall():
                preferences.append({
                    "category": row[0],
                    "preference_score": row[1],
                    "created_at": row[2].isoformat() if row[2] else None
                })
            
            # 獲取用戶反饋
            self.cursor.execute("""
                SELECT uf.episode_id, uf.like_count, uf.dislike_count, uf.created_at
                FROM user_feedback uf
                JOIN users u ON uf.user_id = u.user_id
                WHERE u.user_code = %s
                ORDER BY uf.created_at DESC
            """, (user_code,))
            
            feedback = []
            for row in self.cursor.fetchall():
                feedback.append({
                    "episode_id": row[0],
                    "like_count": row[1],
                    "dislike_count": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                })
            
            self._close()
            
            return {
                "success": True,
                "user_code": user_code,
                "preferences": preferences,
                "feedback": feedback
            }
            
        except Exception as e:
            logger.error(f"獲取用戶偏好失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)}
    
    def create_guest_user(self) -> Dict[str, Any]:
        """創建訪客用戶"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                logger.error("資料庫游標未初始化")
                return {"success": False, "error": "資料庫游標未初始化"}
            
            # 創建訪客用戶
            self.cursor.execute("""
                INSERT INTO users (is_active, created_at, updated_at)
                VALUES (true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING user_id, user_code
            """)
            
            result = self.cursor.fetchone()
            user_id = result[0]
            user_code = result[1]
            
            self.connection.commit()
            self._close()
            
            logger.info(f"創建訪客用戶: {user_code} (ID: {user_id})")
            return {
                "success": True,
                "user_code": user_code,
                "user_id": user_id,
                "message": "訪客用戶創建成功"
            }
            
        except Exception as e:
            logger.error(f"創建訪客用戶失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)}
    
    def update_user_preferences(self, user_code: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """更新用戶偏好"""
        try:
            if not self._connect():
                return {"success": False, "error": "資料庫連接失敗"}
            
            if not self.cursor:
                logger.error("資料庫游標未初始化")
                return {"success": False, "error": "資料庫游標未初始化"}
            
            # 獲取用戶ID
            self.cursor.execute("SELECT user_id FROM users WHERE user_code = %s", (user_code,))
            result = self.cursor.fetchone()
            
            if not result:
                return {"success": False, "error": "用戶不存在"}
            
            user_id = result[0]
            
            # 更新偏好
            for category, score in preferences.items():
                self.cursor.execute("""
                    INSERT INTO user_preferences (user_id, category, preference_score, created_at, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, category) 
                    DO UPDATE SET preference_score = EXCLUDED.preference_score, updated_at = CURRENT_TIMESTAMP
                """, (user_id, category, score))
            
            self.connection.commit()
            self._close()
            
            return {"success": True, "message": "用戶偏好更新成功"}
            
        except Exception as e:
            logger.error(f"更新用戶偏好失敗: {e}")
            self._close()
            return {"success": False, "error": str(e)} 