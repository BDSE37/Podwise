#!/usr/bin/env python3
"""
ML Pipeline 主入口
提供推薦系統的 FastAPI 服務
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 匯入 ML Pipeline 模組
from services import RecommendationService
from config import get_recommender_config

# Pydantic 模型
class RecommendationRequest(BaseModel):
    """推薦請求模型"""
    user_id: int = Field(..., description="用戶ID")
    top_k: int = Field(10, description="推薦數量", ge=1, le=50)
    category_filter: Optional[str] = Field(None, description="類別篩選")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文資訊")

class SimilarEpisodeRequest(BaseModel):
    """相似節目請求模型"""
    episode_id: int = Field(..., description="節目ID")
    limit: int = Field(10, description="返回數量", ge=1, le=20)

class UserPreferenceUpdate(BaseModel):
    """用戶偏好更新模型"""
    user_id: str = Field(..., description="用戶ID")
    podcast_id: str = Field(..., description="播客ID")
    rating: float = Field(..., description="評分", ge=0.0, le=5.0)
    listen_time: int = Field(0, description="收聽時間（秒）")

class RecommendationResponse(BaseModel):
    """推薦回應模型"""
    recommendations: List[Dict[str, Any]]
    total_count: int
    processing_time: float
    confidence: float

class SystemStatusResponse(BaseModel):
    """系統狀態回應模型"""
    status: str
    services: Dict[str, str]
    metrics: Dict[str, Any]

# 初始化 FastAPI 應用
app = FastAPI(
    title="ML Pipeline API",
    description="播客推薦系統 API",
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

# 全局變數
recommendation_service: Optional[RecommendationService] = None

@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global recommendation_service
    
    try:
        # 獲取配置
        config = get_recommender_config()
        db_url = os.getenv("DATABASE_URL", config["database"]["database_url"])
        
        if not db_url:
            logger.error("未設定資料庫連接 URL")
            return
        
        # 初始化推薦服務
        recommendation_service = RecommendationService(db_url, config)
        logger.info("ML Pipeline 服務啟動成功")
        
    except Exception as e:
        logger.error(f"服務啟動失敗: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    logger.info("ML Pipeline 服務關閉")

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "ML Pipeline API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    status = recommendation_service.get_system_status()
    return status

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    獲取推薦結果
    
    Args:
        request: 推薦請求
        
    Returns:
        推薦結果
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        import time
        start_time = time.time()
        
        recommendations = await recommendation_service.get_recommendations(
            user_id=request.user_id,
            top_k=request.top_k,
            category_filter=request.category_filter,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 計算信心值（基於結果數量）
        confidence = min(len(recommendations) / request.top_k, 1.0)
        
        return RecommendationResponse(
            recommendations=recommendations,
            total_count=len(recommendations),
            processing_time=processing_time,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"推薦生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推薦生成失敗: {str(e)}")

@app.post("/similar-episodes")
async def get_similar_episodes(request: SimilarEpisodeRequest):
    """
    獲取相似節目
    
    Args:
        request: 相似節目請求
        
    Returns:
        相似節目列表
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        similar_episodes = await recommendation_service.get_similar_episodes(
            episode_id=request.episode_id,
            limit=request.limit
        )
        
        return {
            "similar_episodes": similar_episodes,
            "total_count": len(similar_episodes),
            "episode_id": request.episode_id
        }
        
    except Exception as e:
        logger.error(f"相似節目查詢失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"相似節目查詢失敗: {str(e)}")

@app.post("/user-preferences")
async def update_user_preference(request: UserPreferenceUpdate):
    """
    更新用戶偏好
    
    Args:
        request: 用戶偏好更新請求
        
    Returns:
        更新結果
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        success = recommendation_service.update_user_preference(
            user_id=request.user_id,
            podcast_id=request.podcast_id,
            rating=request.rating,
            listen_time=request.listen_time
        )
        
        if success:
            return {"message": "用戶偏好更新成功", "user_id": request.user_id}
        else:
            raise HTTPException(status_code=500, detail="用戶偏好更新失敗")
            
    except Exception as e:
        logger.error(f"用戶偏好更新失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"用戶偏好更新失敗: {str(e)}")

@app.post("/evaluate")
async def evaluate_recommendations(
    user_id: int,
    recommendations: List[Dict[str, Any]]
):
    """
    評估推薦結果
    
    Args:
        user_id: 用戶ID
        recommendations: 推薦結果列表
        
    Returns:
        評估指標
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        metrics = await recommendation_service.evaluate_recommendations(
            user_id=user_id,
            recommendations=recommendations
        )
        
        return {
            "user_id": user_id,
            "metrics": metrics,
            "recommendations_count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"推薦評估失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推薦評估失敗: {str(e)}")

@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    獲取系統狀態
    
    Returns:
        系統狀態信息
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        status = recommendation_service.get_system_status()
        
        # 添加額外的系統指標
        import psutil
        metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        return SystemStatusResponse(
            status=status.get('status', 'unknown'),
            services={
                'recommendation_service': 'active',
                'database': 'connected' if status.get('data_source') == 'connected' else 'disconnected'
            },
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"狀態查詢失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"狀態查詢失敗: {str(e)}")

@app.post("/batch-recommendations")
async def batch_recommendations(
    requests: List[RecommendationRequest],
    background_tasks: BackgroundTasks
):
    """
    批次推薦處理
    
    Args:
        requests: 推薦請求列表
        background_tasks: 背景任務
        
    Returns:
        批次處理結果
    """
    if recommendation_service is None:
        raise HTTPException(status_code=503, detail="服務未初始化")
    
    try:
        results = []
        
        for request in requests:
            try:
                recommendations = await recommendation_service.get_recommendations(
                    user_id=request.user_id,
                    top_k=request.top_k,
                    category_filter=request.category_filter,
                    context=request.context
                )
                
                results.append({
                    "user_id": request.user_id,
                    "recommendations": recommendations,
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "user_id": request.user_id,
                    "recommendations": [],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "batch_results": results,
            "total_requests": len(requests),
            "successful_requests": len([r for r in results if r["status"] == "success"])
        }
        
    except Exception as e:
        logger.error(f"批次推薦處理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批次推薦處理失敗: {str(e)}")

if __name__ == "__main__":
    # 開發環境運行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 