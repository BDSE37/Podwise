"""
用戶管理 API 服務
提供用戶 ID 的 RESTful API 介面
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from user_service import UserService
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import POSTGRES_CONFIG

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="PodWise 用戶管理 API",
    description="提供用戶 ID 管理功能",
    version="1.0.0"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化用戶服務
user_service = UserService(POSTGRES_CONFIG)

# Pydantic 模型
class UserCreate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    user_id: str
    username: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    is_active: bool

class ActivityRecord(BaseModel):
    user_id: int
    activity_type: str
    activity_data: Optional[Dict[str, Any]] = None

# API 端點
@app.get("/")
async def root():
    """根端點"""
    return {"message": "PodWise 用戶管理 API", "version": "1.0.0"}

@app.get("/api/get-id")
async def get_user_id(user_id: str):
    """
    獲取用戶資訊
    
    Args:
        user_id: 用戶 ID (字符串，可能是 Podwise0001 格式)
        
    Returns:
        用戶資訊
    """
    try:
        # 嘗試將字符串轉換為整數
        try:
            user_id_int = int(user_id)
            user = user_service.get_user_by_id(user_id_int)
        except ValueError:
            # 如果不是數字，嘗試通過用戶名查找
            user = user_service.get_user_by_username(user_id)
        
        if user:
            return {"success": True, "user": user}
        else:
            return {"success": False, "message": "用戶不存在"}
    except Exception as e:
        logger.error(f"獲取用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/create-user")
async def create_user(user_data: UserCreate):
    """
    建立新用戶
    
    Args:
        user_data: 用戶資料
        
    Returns:
        建立的用戶資訊
    """
    try:
        user = user_service.create_user(
            username=user_data.username or None,
            email=user_data.email or None
        )
        if user:
            return {"success": True, "user": user}
        else:
            raise HTTPException(status_code=400, detail="建立用戶失敗")
    except Exception as e:
        logger.error(f"建立用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.put("/api/update-user/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate):
    """
    更新用戶資訊
    
    Args:
        user_id: 用戶 ID
        user_data: 更新的用戶資料
        
    Returns:
        更新後的用戶資訊
    """
    try:
        update_data = {}
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
            
        user = user_service.update_user(user_id, **update_data)
        if user:
            return {"success": True, "user": user}
        else:
            raise HTTPException(status_code=404, detail="用戶不存在")
    except Exception as e:
        logger.error(f"更新用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.delete("/api/delete-user/{user_id}")
async def delete_user(user_id: str):
    """
    刪除用戶
    
    Args:
        user_id: 用戶 ID
        
    Returns:
        刪除結果
    """
    try:
        success = user_service.delete_user(user_id)
        if success:
            return {"success": True, "message": "用戶刪除成功"}
        else:
            raise HTTPException(status_code=404, detail="用戶不存在")
    except Exception as e:
        logger.error(f"刪除用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/list-users")
async def list_users(limit: int = 100, offset: int = 0):
    """
    獲取用戶列表
    
    Args:
        limit: 限制數量
        offset: 偏移量
        
    Returns:
        用戶列表
    """
    try:
        users = user_service.list_users(limit=limit, offset=offset)
        return {"success": True, "users": users, "count": len(users)}
    except Exception as e:
        logger.error(f"獲取用戶列表失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/record-activity")
async def record_activity(activity: ActivityRecord):
    """
    記錄用戶活動
    
    Args:
        activity: 活動記錄資料
        
    Returns:
        記錄結果
    """
    try:
        user_service.record_activity(
            user_id=activity.user_id,
            activity_type=activity.activity_type,
            activity_data=activity.activity_data or {}
        )
        return {"success": True, "message": "活動記錄成功"}
    except Exception as e:
        logger.error(f"記錄活動失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/user-activities/{user_id}")
async def get_user_activities(user_id: int, limit: int = 50):
    """
    獲取用戶活動記錄
    
    Args:
        user_id: 用戶 ID (整數)
        limit: 限制數量
        
    Returns:
        活動記錄列表
    """
    try:
        activities = user_service.get_user_activities(user_id=user_id, limit=limit)
        return {"success": True, "activities": activities, "count": len(activities)}
    except Exception as e:
        logger.error(f"獲取活動記錄失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/recommend-programs")
async def recommend_programs(request: dict):
    """
    根據類別和標籤推薦節目
    
    Args:
        request: 包含 category, tags, limit 的請求
        
    Returns:
        推薦節目列表
    """
    try:
        category = request.get("category", "")
        tags = request.get("tags", [])
        limit = request.get("limit", 3)
        
        # 從資料庫獲取推薦節目
        programs = user_service.get_recommended_programs(category, tags, limit)
        return {"success": True, "programs": programs}
    except Exception as e:
        logger.error(f"獲取推薦節目失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")



@app.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 測試資料庫連接
        user_service._get_connection().close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {"status": "unhealthy", "database": "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 