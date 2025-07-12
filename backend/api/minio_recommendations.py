"""
MinIO 推薦 API 服務
用於從 MinIO 的 one_minutes_mp3 資料夾中獲取 RSS 音檔推薦
"""

import os
import json
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

app = FastAPI(title="MinIO Recommendations API", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制為特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MinIO 配置 - K8s 環境
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio.podwise.svc.cluster.local:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "podwise")

# 如果是在 K8s 外部訪問，使用 NodePort
if os.getenv("K8S_EXTERNAL_ACCESS", "false").lower() == "true":
    MINIO_ENDPOINT = os.getenv("MINIO_NODEPORT_ENDPOINT", "localhost:30090")

# 初始化 MinIO 客戶端
minio_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

class AudioRecommendation(BaseModel):
    """音頻推薦模型"""
    title: str
    description: str
    audio_url: str
    image_url: Optional[str] = None
    category: str
    duration: Optional[str] = None
    tags: List[str] = []

class RecommendationRequest(BaseModel):
    """推薦請求模型"""
    category: str
    limit: int = 3

class AudioUrlRequest(BaseModel):
    """音頻 URL 請求模型"""
    audio_path: str

# 類別關鍵字映射
CATEGORY_KEYWORDS = {
    "財經": ["financial", "investment", "stock", "economy", "money", "finance", "trading"],
    "職業": ["career", "job", "professional", "work", "employment", "business"],
    "房地產": ["realestate", "property", "housing", "investment", "real estate"],
    "行銷": ["marketing", "business", "advertising", "sales", "promotion"]
}

@app.get("/")
async def root():
    """根路徑"""
    return {"message": "MinIO Recommendations API", "version": "1.0.0"}

@app.get("/api/recommendations")
async def get_recommendations(
    category: str = Query(..., description="推薦類別"),
    source: str = Query("minio", description="數據來源"),
    folder: str = Query("one_minutes_mp3", description="MinIO 資料夾"),
    limit: int = Query(3, description="推薦數量限制")
):
    """
    根據類別獲取推薦音頻
    
    Args:
        category: 推薦類別（財經、職業、房地產、行銷）
        source: 數據來源（minio）
        folder: MinIO 資料夾名稱
        limit: 推薦數量限制
    
    Returns:
        推薦音頻列表
    """
    try:
        # 獲取 MinIO 中的音檔列表
        audio_files = await get_minio_audio_files(folder)
        
        # 根據類別過濾和排序
        recommendations = filter_recommendations_by_category(audio_files, category, limit)
        
        return {
            "success": True,
            "category": category,
            "recommendations": recommendations,
            "total": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取推薦失敗: {str(e)}")

@app.post("/api/minio/audio-url")
async def get_minio_audio_url(request: AudioUrlRequest):
    """
    獲取 MinIO 音檔的播放 URL
    
    Args:
        request: 包含音頻路徑的請求
    
    Returns:
        音頻播放 URL
    """
    try:
        # 生成 MinIO 預簽名 URL
        audio_url = generate_minio_presigned_url(request.audio_path)
        
        return {
            "success": True,
            "audioUrl": audio_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取音頻 URL 失敗: {str(e)}")

async def get_minio_audio_files(folder: str) -> List[Dict]:
    """
    從 MinIO 獲取指定資料夾中的音檔列表
    
    Args:
        folder: 資料夾名稱
    
    Returns:
        音檔信息列表
    """
    try:
        # 列出指定資料夾中的對象
        response = minio_client.list_objects_v2(
            Bucket=MINIO_BUCKET,
            Prefix=f"{folder}/"
        )
        
        audio_files = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith(('.mp3', '.wav', '.m4a')):
                # 解析文件名獲取信息
                file_info = parse_audio_filename(obj['Key'])
                if file_info:
                    audio_files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        **file_info
                    })
        
        return audio_files
        
    except ClientError as e:
        print(f"MinIO 錯誤: {e}")
        return []

def parse_audio_filename(key: str) -> Optional[Dict]:
    """
    解析音頻文件名獲取信息
    
    Args:
        key: MinIO 對象鍵
    
    Returns:
        解析後的文件信息
    """
    try:
        # 移除資料夾前綴
        filename = key.split('/')[-1]
        
        # 移除副檔名
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # 嘗試從文件名中提取信息
        # 假設格式為: category_title_episode.mp3
        parts = name_without_ext.split('_')
        
        if len(parts) >= 2:
            category = parts[0]
            title = '_'.join(parts[1:])
            
            return {
                "title": title,
                "category": category,
                "description": f"{category}相關內容",
                "tags": [category]
            }
        
        return {
            "title": name_without_ext,
            "category": "其他",
            "description": "音頻內容",
            "tags": []
        }
        
    except Exception as e:
        print(f"解析文件名失敗: {e}")
        return None

def filter_recommendations_by_category(
    audio_files: List[Dict], 
    category: str, 
    limit: int
) -> List[AudioRecommendation]:
    """
    根據類別過濾和排序推薦
    
    Args:
        audio_files: 音檔列表
        category: 目標類別
        limit: 限制數量
    
    Returns:
        過濾後的推薦列表
    """
    # 獲取類別關鍵字
    keywords = CATEGORY_KEYWORDS.get(category, [category])
    
    # 計算每個音檔的相關性分數
    scored_files = []
    for audio_file in audio_files:
        score = calculate_relevance_score(audio_file, keywords)
        scored_files.append((score, audio_file))
    
    # 按分數排序並取前 N 個
    scored_files.sort(key=lambda x: x[0], reverse=True)
    top_files = scored_files[:limit]
    
    # 轉換為推薦格式
    recommendations = []
    for score, audio_file in top_files:
        recommendation = AudioRecommendation(
            title=audio_file.get('title', '未知標題'),
            description=audio_file.get('description', ''),
            audio_url=f"minio://{audio_file['key']}",
            category=audio_file.get('category', category),
            tags=audio_file.get('tags', [])
        )
        recommendations.append(recommendation)
    
    return recommendations

def calculate_relevance_score(audio_file: Dict, keywords: List[str]) -> float:
    """
    計算音檔與關鍵字的相關性分數
    
    Args:
        audio_file: 音檔信息
        keywords: 關鍵字列表
    
    Returns:
        相關性分數 (0-1)
    """
    score = 0.0
    
    # 檢查標題中的關鍵字
    title = audio_file.get('title', '').lower()
    category = audio_file.get('category', '').lower()
    tags = [tag.lower() for tag in audio_file.get('tags', [])]
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # 標題匹配
        if keyword_lower in title:
            score += 0.4
        
        # 類別匹配
        if keyword_lower in category:
            score += 0.3
        
        # 標籤匹配
        if keyword_lower in tags:
            score += 0.2
    
    return min(score, 1.0)

def generate_minio_presigned_url(audio_path: str) -> str:
    """
    生成 MinIO 預簽名 URL
    
    Args:
        audio_path: 音頻路徑
    
    Returns:
        預簽名 URL
    """
    try:
        # 從路徑中提取對象鍵
        if audio_path.startswith('minio://'):
            key = audio_path.replace('minio://', '')
        else:
            key = audio_path
        
        # 生成預簽名 URL（有效期 1 小時）
        url = minio_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': MINIO_BUCKET, 'Key': key},
            ExpiresIn=3600
        )
        
        return url
        
    except Exception as e:
        print(f"生成預簽名 URL 失敗: {e}")
        return ""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 