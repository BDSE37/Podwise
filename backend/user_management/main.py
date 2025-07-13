#!/usr/bin/env python3
"""
User Management 主入口

統一包裝用戶註冊、登入、查詢功能，支援 OOP 調用、CLI 測試與 FastAPI 服務。
符合 Google Clean Code 原則。
"""

import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from user_service import UserService
from config.db_config import POSTGRES_CONFIG

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class UserManager:
    """用戶管理 OOP 入口"""
    def __init__(self):
        self.service = UserService(POSTGRES_CONFIG)

    def register(self, username: str, password: str, email: str) -> Dict:
        """用戶註冊"""
        return self.service.register_user(username, password, email)

    def login(self, username: str, password: str) -> Dict:
        """用戶登入"""
        return self.service.login_user(username, password)

    def query_user(self, user_id: str) -> Dict:
        """用戶查詢"""
        return self.service.get_user_by_id(user_id)

    def create_user(self, username: Optional[str] = None, email: Optional[str] = None) -> Dict:
        """創建用戶"""
        return self.service.create_user(username=username, email=email)

    def update_user(self, user_id: str, **kwargs) -> Dict:
        """更新用戶"""
        return self.service.update_user(user_id, **kwargs)

    def delete_user(self, user_id: str) -> bool:
        """刪除用戶"""
        return self.service.delete_user(user_id)

    def list_users(self, limit: int = 100, offset: int = 0) -> list:
        """獲取用戶列表"""
        return self.service.list_users(limit=limit, offset=offset)

    def record_activity(self, user_id: int, activity_type: str, activity_data: Optional[Dict] = None) -> bool:
        """記錄用戶活動"""
        return self.service.record_activity(user_id, activity_type, activity_data)

    def get_user_activities(self, user_id: int, limit: int = 50) -> list:
        """獲取用戶活動"""
        return self.service.get_user_activities(user_id, limit=limit)

# 創建 FastAPI 應用
app = FastAPI(
    title="PodWise 用戶管理 API",
    description="提供用戶 ID 管理功能",
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

# 初始化用戶服務
user_manager = UserManager()

# API 端點
@app.get("/")
async def root():
    """根端點"""
    return {"message": "PodWise 用戶管理 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "User Management",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/get-id")
async def get_user_id(user_id: str):
    """獲取用戶資訊"""
    try:
        # 嘗試將字符串轉換為整數
        try:
            user_id_int = int(user_id)
            user = user_manager.query_user(user_id_int)
        except ValueError:
            # 如果不是數字，嘗試通過用戶名查找
            user = user_manager.service.get_user_by_username(user_id)
        
        if user:
            return {"success": True, "user": user}
        else:
            return {"success": False, "message": "用戶不存在"}
    except Exception as e:
        logger.error(f"獲取用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/create-user")
async def create_user(user_data: UserCreate):
    """建立新用戶"""
    try:
        user = user_manager.create_user(
            username=user_data.username,
            email=user_data.email
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
    """更新用戶資訊"""
    try:
        update_data = {}
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
            
        user = user_manager.update_user(user_id, **update_data)
        if user:
            return {"success": True, "user": user}
        else:
            raise HTTPException(status_code=404, detail="用戶不存在")
    except Exception as e:
        logger.error(f"更新用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.delete("/api/delete-user/{user_id}")
async def delete_user(user_id: str):
    """刪除用戶"""
    try:
        success = user_manager.delete_user(user_id)
        if success:
            return {"success": True, "message": "用戶刪除成功"}
        else:
            raise HTTPException(status_code=404, detail="用戶不存在")
    except Exception as e:
        logger.error(f"刪除用戶失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/list-users")
async def list_users(limit: int = 100, offset: int = 0):
    """獲取用戶列表"""
    try:
        users = user_manager.list_users(limit=limit, offset=offset)
        return {"success": True, "users": users, "count": len(users)}
    except Exception as e:
        logger.error(f"獲取用戶列表失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/record-activity")
async def record_activity(activity: ActivityRecord):
    """記錄用戶活動"""
    try:
        success = user_manager.record_activity(
            activity.user_id,
            activity.activity_type,
            activity.activity_data
        )
        if success:
            return {"success": True, "message": "活動記錄成功"}
        else:
            raise HTTPException(status_code=400, detail="記錄活動失敗")
    except Exception as e:
        logger.error(f"記錄活動失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.get("/api/user-activities/{user_id}")
async def get_user_activities(user_id: int, limit: int = 50):
    """獲取用戶活動"""
    try:
        activities = user_manager.get_user_activities(user_id, limit=limit)
        return {"success": True, "activities": activities, "count": len(activities)}
    except Exception as e:
        logger.error(f"獲取用戶活動失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

@app.post("/api/recommend-programs")
async def recommend_programs(request: dict):
    """推薦節目（整合 ML Pipeline）"""
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="缺少用戶ID")
        
        # 這裡可以整合 ML Pipeline 的推薦功能
        # 暫時返回模擬數據
        recommendations = [
            {"title": "推薦節目1", "confidence": 0.8},
            {"title": "推薦節目2", "confidence": 0.7}
        ]
        
        return {"success": True, "recommendations": recommendations}
    except Exception as e:
        logger.error(f"推薦節目失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務錯誤")

def cli_main():
    """CLI 主函數"""
    parser = argparse.ArgumentParser(description="User Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 註冊
    reg_parser = subparsers.add_parser("register", help="註冊新用戶")
    reg_parser.add_argument("--username", required=True)
    reg_parser.add_argument("--password", required=True)
    reg_parser.add_argument("--email", required=True)

    # 登入
    login_parser = subparsers.add_parser("login", help="用戶登入")
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)

    # 查詢
    query_parser = subparsers.add_parser("query", help="查詢用戶")
    query_parser.add_argument("--user_id", required=True)

    # 創建用戶
    create_parser = subparsers.add_parser("create", help="創建用戶")
    create_parser.add_argument("--username")
    create_parser.add_argument("--email")

    # 列出用戶
    list_parser = subparsers.add_parser("list", help="列出用戶")
    list_parser.add_argument("--limit", type=int, default=100)
    list_parser.add_argument("--offset", type=int, default=0)

    args = parser.parse_args()
    manager = UserManager()

    if args.command == "register":
        result = manager.register(args.username, args.password, args.email)
        print(result)
    elif args.command == "login":
        result = manager.login(args.username, args.password)
        print(result)
    elif args.command == "query":
        result = manager.query_user(args.user_id)
        print(result)
    elif args.command == "create":
        result = manager.create_user(username=args.username, email=args.email)
        print(result)
    elif args.command == "list":
        result = manager.list_users(limit=args.limit, offset=args.offset)
        print(result)
    else:
        parser.print_help()

def api_main():
    """API 主函數"""
    uvicorn.run(app, host="0.0.0.0", port=8007)

if __name__ == "__main__":
    # 檢查是否要啟動 API 服務
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        api_main()
    else:
        cli_main() 