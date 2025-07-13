#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 聊天歷史 MongoDB 服務
用於儲存和管理聊天記錄
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import os

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """聊天歷史服務類別"""
    
    def __init__(self, mongo_uri: Optional[str] = None, database_name: str = "podwise"):
        """
        初始化聊天歷史服務
        
        Args:
            mongo_uri: MongoDB 連接字串
            database_name: 資料庫名稱
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.chat_collection: Optional[Collection] = None
        self.user_collection: Optional[Collection] = None
        
        self._connect()
        self._create_indexes()
    
    def _connect(self):
        """連接到 MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            self.chat_collection = self.db["chat_history"]
            self.user_collection = self.db["user_profiles"]
            
            logger.info(f"✅ MongoDB 連接成功: {self.database_name}")
            
        except Exception as e:
            logger.error(f"❌ MongoDB 連接失敗: {str(e)}")
            raise
    
    def _create_indexes(self):
        """創建必要的索引"""
        try:
            # 聊天歷史索引
            self.chat_collection.create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ])
            
            self.chat_collection.create_index([
                ("session_id", 1),
                ("timestamp", -1)
            ])
            
            self.chat_collection.create_index([
                ("chat_mode", 1),
                ("timestamp", -1)
            ])
            
            # 用戶資料索引
            self.user_collection.create_index([
                ("user_id", 1)
            ], unique=True)
            
            logger.info("✅ MongoDB 索引創建完成")
            
        except Exception as e:
            logger.error(f"❌ 創建索引失敗: {str(e)}")
    
    def save_chat_message(self, 
                         user_id: str,
                         session_id: str,
                         role: str,
                         content: str,
                         chat_mode: str = "rag",
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        儲存聊天訊息
        
        Args:
            user_id: 用戶 ID
            session_id: 會話 ID
            role: 角色 (user/assistant)
            content: 訊息內容
            chat_mode: 聊天模式 (rag/multi_agent/hybrid)
            metadata: 額外資訊
            
        Returns:
            str: 訊息 ID
        """
        try:
            message_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "chat_mode": chat_mode,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            result = self.chat_collection.insert_one(message_doc)
            message_id = str(result.inserted_id)
            
            logger.info(f"✅ 聊天訊息已儲存: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ 儲存聊天訊息失敗: {str(e)}")
            raise
    
    def save_multi_agent_message(self,
                                user_id: str,
                                session_id: str,
                                role: str,
                                content: str,
                                agents_used: List[str],
                                confidence: float,
                                processing_time: float,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        儲存多代理聊天訊息
        
        Args:
            user_id: 用戶 ID
            session_id: 會話 ID
            role: 角色
            content: 訊息內容
            agents_used: 使用的代理列表
            confidence: 信心度
            processing_time: 處理時間
            metadata: 額外資訊
            
        Returns:
            str: 訊息 ID
        """
        try:
            message_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "chat_mode": "multi_agent",
                "timestamp": datetime.utcnow(),
                "agents_used": agents_used,
                "confidence": confidence,
                "processing_time": processing_time,
                "metadata": metadata or {}
            }
            
            result = self.chat_collection.insert_one(message_doc)
            message_id = str(result.inserted_id)
            
            logger.info(f"✅ 多代理訊息已儲存: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ 儲存多代理訊息失敗: {str(e)}")
            raise
    
    def get_chat_history(self, 
                        user_id: str, 
                        session_id: Optional[str] = None,
                        limit: int = 50,
                        offset: int = 0) -> List[Dict[str, Any]]:
        """
        獲取聊天歷史
        
        Args:
            user_id: 用戶 ID
            session_id: 會話 ID (可選)
            limit: 限制數量
            offset: 偏移量
            
        Returns:
            List[Dict]: 聊天歷史列表
        """
        try:
            query = {"user_id": user_id}
            if session_id:
                query["session_id"] = session_id
            
            cursor = self.chat_collection.find(
                query,
                sort=[("timestamp", -1)],
                limit=limit,
                skip=offset
            )
            
            history = []
            for doc in cursor:
                # 轉換 ObjectId 為字串
                doc["_id"] = str(doc["_id"])
                # 轉換時間戳記
                if "timestamp" in doc:
                    doc["timestamp"] = doc["timestamp"].isoformat()
                history.append(doc)
            
            logger.info(f"✅ 獲取聊天歷史: {len(history)} 條記錄")
            return history
            
        except Exception as e:
            logger.error(f"❌ 獲取聊天歷史失敗: {str(e)}")
            return []
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        獲取特定會話的歷史
        
        Args:
            session_id: 會話 ID
            
        Returns:
            List[Dict]: 會話歷史列表
        """
        try:
            cursor = self.chat_collection.find(
                {"session_id": session_id},
                sort=[("timestamp", 1)]  # 按時間正序排列
            )
            
            history = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                if "timestamp" in doc:
                    doc["timestamp"] = doc["timestamp"].isoformat()
                history.append(doc)
            
            logger.info(f"✅ 獲取會話歷史: {len(history)} 條記錄")
            return history
            
        except Exception as e:
            logger.error(f"❌ 獲取會話歷史失敗: {str(e)}")
            return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        獲取用戶的所有會話
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            List[Dict]: 會話列表
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$session_id",
                    "last_message": {"$last": "$$ROOT"},
                    "message_count": {"$sum": 1},
                    "first_message": {"$first": "$$ROOT"}
                }},
                {"$sort": {"last_message.timestamp": -1}}
            ]
            
            sessions = []
            for doc in self.chat_collection.aggregate(pipeline):
                session_info = {
                    "session_id": doc["_id"],
                    "message_count": doc["message_count"],
                    "last_message": doc["last_message"]["content"][:100] + "..." if len(doc["last_message"]["content"]) > 100 else doc["last_message"]["content"],
                    "last_timestamp": doc["last_message"]["timestamp"].isoformat(),
                    "first_timestamp": doc["first_message"]["timestamp"].isoformat(),
                    "chat_mode": doc["last_message"].get("chat_mode", "rag")
                }
                sessions.append(session_info)
            
            logger.info(f"✅ 獲取用戶會話: {len(sessions)} 個會話")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ 獲取用戶會話失敗: {str(e)}")
            return []
    
    def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        儲存用戶資料
        
        Args:
            user_id: 用戶 ID
            profile: 用戶資料
            
        Returns:
            bool: 是否成功
        """
        try:
            profile_doc = {
                "user_id": user_id,
                "profile": profile,
                "updated_at": datetime.utcnow()
            }
            
            self.user_collection.update_one(
                {"user_id": user_id},
                {"$set": profile_doc},
                upsert=True
            )
            
            logger.info(f"✅ 用戶資料已儲存: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 儲存用戶資料失敗: {str(e)}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取用戶資料
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            Optional[Dict]: 用戶資料
        """
        try:
            doc = self.user_collection.find_one({"user_id": user_id})
            if doc:
                return doc.get("profile", {})
            return None
            
        except Exception as e:
            logger.error(f"❌ 獲取用戶資料失敗: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        刪除會話
        
        Args:
            session_id: 會話 ID
            
        Returns:
            bool: 是否成功
        """
        try:
            result = self.chat_collection.delete_many({"session_id": session_id})
            logger.info(f"✅ 會話已刪除: {session_id}, 刪除 {result.deleted_count} 條記錄")
            return True
            
        except Exception as e:
            logger.error(f"❌ 刪除會話失敗: {str(e)}")
            return False
    
    def delete_user_history(self, user_id: str) -> bool:
        """
        刪除用戶所有聊天歷史
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            bool: 是否成功
        """
        try:
            result = self.chat_collection.delete_many({"user_id": user_id})
            logger.info(f"✅ 用戶歷史已刪除: {user_id}, 刪除 {result.deleted_count} 條記錄")
            return True
            
        except Exception as e:
            logger.error(f"❌ 刪除用戶歷史失敗: {str(e)}")
            return False
    
    def get_chat_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        獲取聊天統計資訊
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            Dict: 統計資訊
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_messages": {"$sum": 1},
                    "user_messages": {"$sum": {"$cond": [{"$eq": ["$role", "user"]}, 1, 0]}},
                    "assistant_messages": {"$sum": {"$cond": [{"$eq": ["$role", "assistant"]}, 1, 0]}},
                    "sessions": {"$addToSet": "$session_id"},
                    "chat_modes": {"$addToSet": "$chat_mode"}
                }}
            ]
            
            result = list(self.chat_collection.aggregate(pipeline))
            if result:
                stats = result[0]
                return {
                    "total_messages": stats["total_messages"],
                    "user_messages": stats["user_messages"],
                    "assistant_messages": stats["assistant_messages"],
                    "total_sessions": len(stats["sessions"]),
                    "chat_modes": list(stats["chat_modes"]),
                    "user_id": user_id
                }
            else:
                return {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0,
                    "total_sessions": 0,
                    "chat_modes": [],
                    "user_id": user_id
                }
                
        except Exception as e:
            logger.error(f"❌ 獲取聊天統計失敗: {str(e)}")
            return {}
    
    def close(self):
        """關閉資料庫連接"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB 連接已關閉")

# 全局實例
_chat_history_service = None

def get_chat_history_service() -> ChatHistoryService:
    """獲取聊天歷史服務實例"""
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service 