#!/usr/bin/env python3
"""
使用者驗證服務
提供使用者 ID 驗證、訪客模式管理、使用者偏好等功能
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, Optional, List, Tuple
import logging
import uuid
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

class UserAuthService:
    """使用者驗證服務類別"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化使用者驗證服務
        
        Args:
            db_config: 資料庫配置
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
        logger.info("使用者驗證服務初始化完成")
    
    def connect(self) -> bool:
        """建立資料庫連接"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                cursor_factory=RealDictCursor
            )
            self.cursor = self.connection.cursor()
            logger.info("資料庫連接建立成功")
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {str(e)}")
            return False
    
    def close(self):
        """關閉資料庫連接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("資料庫連接已關閉")
            
        except Exception as e:
            logger.error(f"關閉連接失敗: {str(e)}")
    
    def validate_user_id(self, user_identifier: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        驗證使用者 ID
        
        Args:
            user_identifier: 使用者識別碼
            
        Returns:
            (是否有效, 使用者資訊)
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            # 查詢使用者
            query = """
                SELECT user_id, user_identifier, email, given_name, family_name, 
                       username, user_type, is_active, locale, last_chat_at, 
                       total_chat_count, preferred_categories
                FROM users 
                WHERE user_identifier = %s AND is_active = true
            """
            
            self.cursor.execute(query, (user_identifier,))
            user = self.cursor.fetchone()
            
            if user:
                # 更新最後聊天時間
                self._update_last_chat_time(user['user_id'])
                return True, dict(user)
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"驗證使用者 ID 失敗: {str(e)}")
            return False, None
    
    def create_guest_user(self) -> Optional[Dict[str, Any]]:
        """
        建立訪客使用者
        
        Returns:
            訪客使用者資訊
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            # 生成訪客 ID
            guest_id = f"guest_{uuid.uuid4().hex[:8]}"
            
            # 插入訪客使用者
            query = """
                INSERT INTO users (user_identifier, user_type, is_active, locale, created_at)
                VALUES (%s, 'guest', true, 'zh-TW', CURRENT_TIMESTAMP)
                RETURNING user_id, user_identifier, user_type, locale, created_at
            """
            
            self.cursor.execute(query, (guest_id,))
            self.connection.commit()
            
            guest_user = self.cursor.fetchone()
            logger.info(f"建立訪客使用者: {guest_id}")
            
            return dict(guest_user)
            
        except Exception as e:
            logger.error(f"建立訪客使用者失敗: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_user_preferences(self, user_id: int) -> List[Dict[str, Any]]:
        """
        獲取使用者偏好
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            使用者偏好列表
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            query = """
                SELECT category, preference_score, created_at, updated_at
                FROM user_preferences 
                WHERE user_id = %s
                ORDER BY preference_score DESC
            """
            
            self.cursor.execute(query, (user_id,))
            preferences = self.cursor.fetchall()
            
            return [dict(pref) for pref in preferences]
            
        except Exception as e:
            logger.error(f"獲取使用者偏好失敗: {str(e)}")
            return []
    
    def update_user_preference(self, user_id: int, category: str, score: float) -> bool:
        """
        更新使用者偏好
        
        Args:
            user_id: 使用者 ID
            category: 類別
            score: 偏好分數 (0.0-1.0)
            
        Returns:
            是否更新成功
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            query = """
                INSERT INTO user_preferences (user_id, category, preference_score, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, category) 
                DO UPDATE SET 
                    preference_score = EXCLUDED.preference_score,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            self.cursor.execute(query, (user_id, category, score))
            self.connection.commit()
            
            logger.info(f"更新使用者 {user_id} 的 {category} 偏好為 {score}")
            return True
            
        except Exception as e:
            logger.error(f"更新使用者偏好失敗: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def log_chat_message(self, user_id: int, session_id: str, message_type: str, 
                        content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        記錄聊天訊息
        
        Args:
            user_id: 使用者 ID
            session_id: 會話 ID
            message_type: 訊息類型 ('user' 或 'bot')
            content: 訊息內容
            metadata: 額外資訊
            
        Returns:
            是否記錄成功
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            query = """
                INSERT INTO user_chat_history 
                (user_id, session_id, message_type, message_content, message_timestamp, metadata)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            """
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.cursor.execute(query, (user_id, session_id, message_type, content, metadata_json))
            self.connection.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"記錄聊天訊息失敗: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_user_chat_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取使用者聊天歷史
        
        Args:
            user_id: 使用者 ID
            limit: 返回數量限制
            
        Returns:
            聊天歷史列表
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            query = """
                SELECT session_id, message_type, message_content, message_timestamp, metadata
                FROM user_chat_history 
                WHERE user_id = %s
                ORDER BY message_timestamp DESC
                LIMIT %s
            """
            
            self.cursor.execute(query, (user_id, limit))
            history = self.cursor.fetchall()
            
            return [dict(record) for record in history]
            
        except Exception as e:
            logger.error(f"獲取聊天歷史失敗: {str(e)}")
            return []
    
    def update_user_behavior_stats(self, user_id: int, query_type: str, 
                                  response_time_ms: int = 0) -> bool:
        """
        更新使用者行為統計
        
        Args:
            user_id: 使用者 ID
            query_type: 查詢類型 ('rag', 'recommendation', 'voice')
            response_time_ms: 回應時間 (毫秒)
            
        Returns:
            是否更新成功
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            today = date.today()
            
            # 檢查今日統計是否存在
            check_query = """
                SELECT total_queries, rag_queries, recommendation_queries, voice_queries, avg_response_time_ms
                FROM user_behavior_stats 
                WHERE user_id = %s AND stat_date = %s
            """
            
            self.cursor.execute(check_query, (user_id, today))
            existing_stats = self.cursor.fetchone()
            
            if existing_stats:
                # 更新現有統計
                stats = dict(existing_stats)
                stats['total_queries'] += 1
                
                if query_type == 'rag':
                    stats['rag_queries'] += 1
                elif query_type == 'recommendation':
                    stats['recommendation_queries'] += 1
                elif query_type == 'voice':
                    stats['voice_queries'] += 1
                
                # 更新平均回應時間
                if stats['avg_response_time_ms'] > 0:
                    stats['avg_response_time_ms'] = (stats['avg_response_time_ms'] + response_time_ms) // 2
                else:
                    stats['avg_response_time_ms'] = response_time_ms
                
                update_query = """
                    UPDATE user_behavior_stats 
                    SET total_queries = %s, rag_queries = %s, recommendation_queries = %s, 
                        voice_queries = %s, avg_response_time_ms = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND stat_date = %s
                """
                
                self.cursor.execute(update_query, (
                    stats['total_queries'], stats['rag_queries'], 
                    stats['recommendation_queries'], stats['voice_queries'],
                    stats['avg_response_time_ms'], user_id, today
                ))
                
            else:
                # 建立新統計記錄
                insert_query = """
                    INSERT INTO user_behavior_stats 
                    (user_id, stat_date, total_queries, rag_queries, recommendation_queries, 
                     voice_queries, avg_response_time_ms, created_at, updated_at)
                    VALUES (%s, %s, 1, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                rag_count = 1 if query_type == 'rag' else 0
                rec_count = 1 if query_type == 'recommendation' else 0
                voice_count = 1 if query_type == 'voice' else 0
                
                self.cursor.execute(insert_query, (
                    user_id, today, rag_count, rec_count, voice_count, response_time_ms
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新使用者行為統計失敗: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _update_last_chat_time(self, user_id: int) -> bool:
        """更新使用者最後聊天時間"""
        try:
            query = """
                UPDATE users 
                SET last_chat_at = CURRENT_TIMESTAMP, 
                    total_chat_count = total_chat_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """
            
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新最後聊天時間失敗: {str(e)}")
            return False
    
    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        獲取使用者統計資訊
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            使用者統計資訊
        """
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            # 獲取基本資訊
            user_query = """
                SELECT user_identifier, user_type, total_chat_count, last_chat_at, preferred_categories
                FROM users 
                WHERE user_id = %s
            """
            
            self.cursor.execute(user_query, (user_id,))
            user_info = self.cursor.fetchone()
            
            if not user_info:
                return None
            
            # 獲取今日統計
            today = date.today()
            stats_query = """
                SELECT total_queries, rag_queries, recommendation_queries, voice_queries, avg_response_time_ms
                FROM user_behavior_stats 
                WHERE user_id = %s AND stat_date = %s
            """
            
            self.cursor.execute(stats_query, (user_id, today))
            today_stats = self.cursor.fetchone()
            
            # 獲取偏好
            preferences = self.get_user_preferences(user_id)
            
            return {
                "user_info": dict(user_info),
                "today_stats": dict(today_stats) if today_stats else {
                    "total_queries": 0,
                    "rag_queries": 0,
                    "recommendation_queries": 0,
                    "voice_queries": 0,
                    "avg_response_time_ms": 0
                },
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"獲取使用者統計失敗: {str(e)}")
            return None 