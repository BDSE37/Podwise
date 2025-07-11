"""
用戶管理服務
提供用戶 ID 的增刪改查功能
"""

import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import uuid

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserService:
    """用戶管理服務類別"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化用戶服務
        
        Args:
            db_config: 資料庫配置字典
        """
        self.db_config = db_config
    
    def _get_connection(self):
        """獲取資料庫連接"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def _generate_podwise_username(self) -> str:
        """
        自動生成 Podwise 格式的用戶名稱
        
        Returns:
            Podwise 格式的用戶名稱 (例如: Podwise0001)
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # 獲取最大的用戶 ID
                    cursor.execute("SELECT MAX(user_id) FROM users")
                    result = cursor.fetchone()
                    max_id = result[0] if result[0] else 0
                    
                    # 生成下一個用戶名稱
                    next_id = max_id + 1
                    return f"Podwise{next_id:04d}"
                    
        except Exception as e:
            logger.error(f"生成用戶名稱失敗: {e}")
            # 如果失敗，使用時間戳作為備用
            timestamp = int(datetime.now().timestamp())
            return f"Podwise{timestamp % 10000:04d}"
    
    def create_user(self, username: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """
        建立新用戶
        
        Args:
            username: 用戶名稱 (如果為 None，將自動生成 Podwise 格式)
            email: 電子郵件
            
        Returns:
            用戶資訊字典
        """
        try:
            # 如果沒有提供用戶名稱，自動生成
            if not username:
                username = self._generate_podwise_username()
            
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO users (username, email, created_at, updated_at, is_active)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE)
                        RETURNING *
                    """, (username, email))
                    
                    user = cursor.fetchone()
                    conn.commit()
                    
                    if user:
                        logger.info(f"用戶建立成功: {user['user_id']} - {user['username']}")
                        return dict(user)
                    return None
                    
        except Exception as e:
            logger.error(f"建立用戶失敗: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根據用戶 ID 獲取用戶資訊
        
        Args:
            user_id: 用戶 ID (整數)
            
        Returns:
            用戶資訊字典或 None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM users WHERE user_id = %s
                    """, (user_id,))
                    
                    user = cursor.fetchone()
                    return dict(user) if user else None
                    
        except Exception as e:
            logger.error(f"獲取用戶失敗: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根據用戶名稱獲取用戶資訊
        
        Args:
            username: 用戶名稱
            
        Returns:
            用戶資訊字典或 None
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM users WHERE username = %s
                    """, (username,))
                    
                    user = cursor.fetchone()
                    return dict(user) if user else None
                    
        except Exception as e:
            logger.error(f"獲取用戶失敗: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """
        更新用戶資訊
        
        Args:
            user_id: 用戶 ID (整數)
            **kwargs: 要更新的欄位
            
        Returns:
            更新後的用戶資訊
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # 動態建立更新語句
                    set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
                    values = list(kwargs.values()) + [user_id]
                    
                    cursor.execute(f"""
                        UPDATE users 
                        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        RETURNING *
                    """, values)
                    
                    user = cursor.fetchone()
                    conn.commit()
                    
                    if user:
                        logger.info(f"用戶更新成功: {user_id}")
                        return dict(user)
                    else:
                        logger.warning(f"用戶不存在: {user_id}")
                        return None
                        
        except Exception as e:
            logger.error(f"更新用戶失敗: {e}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """
        刪除用戶
        
        Args:
            user_id: 用戶 ID (整數)
            
        Returns:
            是否刪除成功
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM users WHERE user_id = %s
                    """, (user_id,))
                    
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        logger.info(f"用戶刪除成功: {user_id}")
                    else:
                        logger.warning(f"用戶不存在: {user_id}")
                    
                    return deleted
                    
        except Exception as e:
            logger.error(f"刪除用戶失敗: {e}")
            return False
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        獲取用戶列表
        
        Args:
            limit: 限制數量
            offset: 偏移量
            
        Returns:
            用戶列表
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM users 
                        ORDER BY created_at DESC 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    users = cursor.fetchall()
                    return [dict(user) for user in users]
                    
        except Exception as e:
            logger.error(f"獲取用戶列表失敗: {e}")
            return []
    
    def record_activity(self, user_id: int, activity_type: str, activity_data: Dict[str, Any] = None):
        """
        記錄用戶活動
        
        Args:
            user_id: 用戶 ID (整數)
            activity_type: 活動類型
            activity_data: 活動資料
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO user_feedback (user_id, feedback_type, feedback_content, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (user_id, activity_type, str(activity_data or {})))
                    
                    conn.commit()
                    logger.info(f"活動記錄成功: {user_id} - {activity_type}")
                    
        except Exception as e:
            logger.error(f"記錄活動失敗: {e}")
    
    def get_user_activities(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取用戶活動記錄
        
        Args:
            user_id: 用戶 ID (整數)
            limit: 限制數量
            
        Returns:
            活動記錄列表
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM user_feedback 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (user_id, limit))
                    
                    activities = cursor.fetchall()
                    return [dict(activity) for activity in activities]
                    
        except Exception as e:
            logger.error(f"獲取活動記錄失敗: {e}")
            return [] 