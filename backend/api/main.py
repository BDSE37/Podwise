"""
Podwise API 閘道服務
統一的 API 介面，整合所有後端服務
"""

import os
import httpx
import asyncio
import csv
import random
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入 CSV 資料
def load_episodes_data():
    """載入節目資料"""
    episodes_data = {"business": [], "education": []}
    
    try:
        # 載入商業節目
        business_file = "../analysis_output/business_episodes_analysis.csv"
        print(f"DEBUG: 檢查商業節目檔案路徑: {os.path.abspath(business_file)}")
        print(f"DEBUG: 檔案是否存在: {os.path.exists(business_file)}")
        
        if os.path.exists(business_file):
            with open(business_file, 'r', encoding='utf-8-sig') as f:  # 使用 utf-8-sig 處理 BOM
                reader = csv.DictReader(f)
                episodes_data["business"] = list(reader)
            print(f"DEBUG: 成功載入 {len(episodes_data['business'])} 個商業節目")
            if episodes_data["business"]:
                print(f"DEBUG: 第一個商業節目: {episodes_data['business'][0]}")
                print(f"DEBUG: podcast_id 欄位: {list(episodes_data['business'][0].keys())}")
        
        # 載入教育節目
        education_file = "../analysis_output/education_episodes_analysis.csv"
        print(f"DEBUG: 檢查教育節目檔案路徑: {os.path.abspath(education_file)}")
        print(f"DEBUG: 檔案是否存在: {os.path.exists(education_file)}")
        
        if os.path.exists(education_file):
            with open(education_file, 'r', encoding='utf-8-sig') as f:  # 使用 utf-8-sig 處理 BOM
                reader = csv.DictReader(f)
                episodes_data["education"] = list(reader)
            print(f"DEBUG: 成功載入 {len(episodes_data['education'])} 個教育節目")
            if episodes_data["education"]:
                print(f"DEBUG: 第一個教育節目: {episodes_data['education'][0]}")
        
    except Exception as e:
        print(f"DEBUG: 載入 CSV 資料失敗: {e}")
        logger.error(f"載入 CSV 資料失敗: {e}")
    
    return episodes_data

# 預定義的標籤
CATEGORY_TAGS = {
    "business": ["股票分析", "投資理財", "企業管理", "市場趨勢", "財務規劃", "創業故事", "經濟分析", "商業策略"],
    "education": ["學習方法", "知識分享", "技能提升", "學術研究", "語言學習", "職業發展", "個人成長", "教育趨勢"]
}

# 載入節目資料
EPISODES_DATA = load_episodes_data()

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise API Gateway",
    description="統一的 API 閘道，整合所有後端服務",
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

# 服務配置
SERVICE_CONFIG = {
    "stt": {
        "url": os.getenv("STT_SERVICE_URL", "http://localhost:8001"),
        "health_endpoint": "/health",
        "description": "語音轉文字服務"
    },
    "tts": {
        "url": os.getenv("TTS_SERVICE_URL", "http://localhost:8003"),
        "health_endpoint": "/health",
        "description": "文字轉語音服務"
    },
    "llm": {
        "url": os.getenv("LLM_SERVICE_URL", "http://localhost:8000"),
        "health_endpoint": "/health",
        "description": "大語言模型服務"
    },
    "rag": {
        "url": os.getenv("RAG_SERVICE_URL", "http://localhost:8012"),
        "health_endpoint": "/health",
        "description": "檢索增強生成服務 (CrewAI 三層架構)"
    },
    "ml": {
        "url": os.getenv("ML_SERVICE_URL", "http://localhost:8004"),
        "health_endpoint": "/health",
        "description": "機器學習推薦服務"
    },
    "config": {
        "url": os.getenv("CONFIG_SERVICE_URL", "http://localhost:8008"),
        "health_endpoint": "/health",
        "description": "配置管理服務"
    }
}

# 反向代理路由配置
PROXY_ROUTES = {
    "/api/rag": {
        "target": SERVICE_CONFIG["rag"]["url"],
        "strip_prefix": "/api/rag",
        "description": "RAG Pipeline 服務代理"
    },
    "/api/tts": {
        "target": SERVICE_CONFIG["tts"]["url"],
        "strip_prefix": "/api/tts",
        "description": "TTS 服務代理"
    },
    "/api/stt": {
        "target": SERVICE_CONFIG["stt"]["url"],
        "strip_prefix": "/api/stt",
        "description": "STT 服務代理"
    },
    "/api/llm": {
        "target": SERVICE_CONFIG["llm"]["url"],
        "strip_prefix": "/api/llm",
        "description": "LLM 服務代理"
    },
    "/api/ml": {
        "target": SERVICE_CONFIG["ml"]["url"],
        "strip_prefix": "/api/ml",
        "description": "ML 服務代理"
    }
}

# Pydantic 模型
class ServiceStatus(BaseModel):
    service: str
    status: str
    url: str
    description: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, ServiceStatus]
    timestamp: str

class ChatRequest(BaseModel):
    message: str = Field(..., description="用戶訊息")
    user_id: Optional[str] = Field(None, description="用戶 ID")

class ChatResponse(BaseModel):
    response: str
    service: str

class TranscribeRequest(BaseModel):
    audio_url: str = Field(..., description="音頻檔案 URL")
    language: Optional[str] = Field("zh-TW", description="語言代碼")

class TranscribeResponse(BaseModel):
    text: str
    confidence: Optional[float] = None

class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="要合成的文字")
    voice: Optional[str] = Field("zh-TW-HsiaoChenNeural", description="語音設定")

class SynthesizeResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    text: Optional[str] = None
    processing_time: Optional[float] = None
    message: str = ""

class RAGRequest(BaseModel):
    query: str = Field(..., description="查詢內容")
    user_id: Optional[str] = Field(None, description="用戶 ID")
    session_id: Optional[str] = Field(None, description="會話 ID")
    enable_tts: Optional[bool] = Field(True, description="是否啟用 TTS")
    voice: Optional[str] = Field("podrina", description="語音模型")
    speed: Optional[float] = Field(1.0, description="語音速度")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外元數據")

class RAGResponse(BaseModel):
    user_id: str
    query: str
    response: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: Optional[str] = None
    audio_data: Optional[str] = None
    voice_used: Optional[str] = None
    speed_used: Optional[float] = None
    tts_enabled: Optional[bool] = None

class RecommendRequest(BaseModel):
    user_id: str = Field(..., description="用戶 ID")
    context: Optional[str] = Field(None, description="上下文資訊")

class RecommendResponse(BaseModel):
    recommendations: list
    score: Optional[float] = None

# 工具函數
async def check_service_health(service_name: str, config: dict) -> ServiceStatus:
    """檢查服務健康狀態"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config['url']}{config['health_endpoint']}")
            if response.status_code == 200:
                return ServiceStatus(
                    service=service_name,
                    status="healthy",
                    url=config['url'],
                    description=config['description']
                )
            else:
                return ServiceStatus(
                    service=service_name,
                    status="unhealthy",
                    url=config['url'],
                    description=config['description'],
                    error=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ServiceStatus(
            service=service_name,
            status="unhealthy",
            url=config['url'],
            description=config['description'],
            error=str(e)
        )

async def forward_request(service_name: str, endpoint: str, data: dict, method: str = "POST") -> dict:
    """轉發請求到對應服務"""
    config = SERVICE_CONFIG.get(service_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(f"{config['url']}{endpoint}")
            else:
            response = await client.post(f"{config['url']}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Service {service_name} error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Service {service_name} connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

# API 端點
@app.get("/")
async def root():
    """根端點 - 顯示服務資訊"""
    return {
        "service": "Podwise API Gateway",
        "version": "1.0.0",
        "description": "統一的 API 閘道，整合所有後端服務",
        "endpoints": {
            "health": "/health",
            "services": "/api/v1/services",
            "configs": "/api/v1/configs",
            "stt": "/api/v1/stt/transcribe",
            "tts": "/api/v1/tts/synthesize",
            "llm": "/api/v1/llm/chat",
            "rag": "/api/v1/rag/query",
            "ml": "/api/v1/ml/recommend"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查 - 檢查所有服務狀態"""
    import datetime
    
    # 並行檢查所有服務
    tasks = [
        check_service_health(service_name, config)
        for service_name, config in SERVICE_CONFIG.items()
    ]
    
    service_statuses = await asyncio.gather(*tasks)
    services_dict = {status.service: status for status in service_statuses}
    
    # 判斷整體狀態
    overall_status = "healthy" if all(s.status == "healthy" for s in service_statuses) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        services=services_dict,
        timestamp=datetime.datetime.now().isoformat()
    )

@app.get("/api/v1/services")
async def get_services_status():
    """獲取所有服務狀態"""
    return await health_check()

@app.get("/api/v1/configs")
async def get_configs():
    """獲取所有服務配置"""
    return {
        "services": SERVICE_CONFIG,
        "environment": {
            "STT_SERVICE_URL": os.getenv("STT_SERVICE_URL"),
            "TTS_SERVICE_URL": os.getenv("TTS_SERVICE_URL"),
            "LLM_SERVICE_URL": os.getenv("LLM_SERVICE_URL"),
            "RAG_SERVICE_URL": os.getenv("RAG_SERVICE_URL"),
            "ML_SERVICE_URL": os.getenv("ML_SERVICE_URL"),
            "CONFIG_SERVICE_URL": os.getenv("CONFIG_SERVICE_URL")
        }
    }

@app.post("/api/v1/stt/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """語音轉文字"""
    data = {
        "audio_url": request.audio_url,
        "language": request.language
    }
    result = await forward_request("stt", "/transcribe", data)
    return TranscribeResponse(**result)

@app.get("/api/v1/tts/voices")
async def get_tts_voices():
    """獲取可用的語音列表"""
    try:
        logger.info("API Gateway: 開始獲取TTS語音列表")
        result = await forward_request("tts", "/api/v1/tts/voices", {}, method="GET")
        logger.info(f"API Gateway: TTS語音列表結果: {result}")
        return result
    except Exception as e:
        logger.error(f"獲取語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")

@app.post("/api/v1/tts/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """文字轉語音"""
    data = {
        "文字": request.text,
        "語音": request.voice
    }
    result = await forward_request("tts", "/synthesize", data)
    
    # 轉換 TTS 服務的回應格式
    return SynthesizeResponse(
        success=result.get("成功", False),
        audio_data=result.get("音訊檔案"),
        voice=request.voice,
        text=request.text,
        processing_time=result.get("處理時間"),
        message=result.get("錯誤訊息") or ""
    )

@app.post("/api/v1/llm/chat", response_model=ChatResponse)
async def llm_chat(request: ChatRequest):
    """LLM 聊天"""
    data = {
        "message": request.message,
        "user_id": request.user_id
    }
    result = await forward_request("llm", "/chat", data)
    return ChatResponse(**result)

@app.post("/api/v1/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """RAG 查詢"""
    data = {
        "query": request.query,
        "user_id": request.user_id,
        "session_id": request.session_id,
        "enable_tts": request.enable_tts,
        "voice": request.voice,
        "speed": request.speed,
        "metadata": request.metadata
    }
    result = await forward_request("rag", "/api/v1/query", data)
    return RAGResponse(**result)

@app.post("/api/v1/ml/recommend", response_model=RecommendResponse)
async def ml_recommend(request: RecommendRequest):
    """ML 推薦"""
    data = {
        "user_id": request.user_id,
        "context": request.context
    }
    result = await forward_request("ml", "/recommend", data)
    return RecommendResponse(**result)

@app.post("/api/v1/init/database")
async def init_database():
    """初始化資料庫"""
    try:
        result = await forward_request("config", "/init/database", {})
        return {"status": "success", "message": "Database initialized successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

# ==================== 前端專用端點 ====================

@app.get("/api/one-minutes-episodes")
async def get_one_minutes_episodes(category: str = "business", tag: str = ""):
    """不論 tag，隨機回傳 3 個不同 podcast_id 的節目"""
    try:
        print(f"DEBUG: 請求類別: {category}, 標籤: {tag}")
        print(f"DEBUG: EPISODES_DATA 鍵值: {list(EPISODES_DATA.keys())}")
        
        category_episodes = EPISODES_DATA.get(category, [])
        print(f"DEBUG: category_episodes 筆數: {len(category_episodes)}")
        
        if not category_episodes:
            print("DEBUG: 沒有找到該類別的節目資料")
            return {"success": True, "episodes": [], "category": category, "tag": tag}

        # 隨機打亂，取不同 podcast_id 的 3 個節目
        random.shuffle(category_episodes)
        selected_episodes = []
        used_podcast_ids = set()
        
        print(f"DEBUG: 開始處理 {len(category_episodes)} 個節目")
        
        for i, episode in enumerate(category_episodes):
            podcast_id = episode.get('podcast_id')
            print(f"DEBUG: 處理第 {i+1} 個節目, podcast_id: {podcast_id}")
            
            if podcast_id and podcast_id not in used_podcast_ids:
                # 隨機分配一個 tag（讓前端不會壞）
                episode_tags = [random.choice(CATEGORY_TAGS.get(category, []))]
                
                # 優先使用 CSV 中的 audio_url，如果沒有則構建新的 URL
                audio_url = episode.get('audio_url', '')
                if not audio_url:
                    podcast_id = episode.get('podcast_id', '')
                    episode_title = episode.get('episode_title', '')
                    
                    # 根據類別選擇正確的 bucket
                    bucket_map = {
                        "business": "business-one-min-audio",
                        "education": "education-one-min-audio"
                    }
                    bucket = bucket_map.get(category, "business-one-min-audio")
                    
                    # 構建音檔 URL
                    audio_url = f"http://192.168.32.66:30090/{bucket}/RSS_{podcast_id}_{episode_title}.mp3"
                else:
                    # 如果 CSV 中有 audio_url，但包含過期的預簽名參數，則移除預簽名參數
                    if '?' in audio_url:
                        audio_url = audio_url.split('?')[0]
                
                selected_episode = {
                    "episode_id": len(selected_episodes) + 1,
                    "rss_id": episode.get('rss_id', ''),
                    "podcast_name": episode.get('podcast_name', 'Unknown Podcast'),
                    "episode_title": episode.get('episode_title', 'Unknown Episode'),
                    "episode_description": f"關於 {tag or category} 的精選內容",
                    "image_url": episode.get('image_url', ''),  # 使用 image_url 欄位
                    "audio_url": audio_url,
                    "tags": episode_tags
                }
                selected_episodes.append(selected_episode)
                used_podcast_ids.add(podcast_id)
                print(f"DEBUG: 已選擇 {len(selected_episodes)} 個節目")
                
                if len(selected_episodes) >= 3:
                    break

        print(f"DEBUG: 最終選擇了 {len(selected_episodes)} 個節目")
        print(f"DEBUG: 回傳資料: {selected_episodes}")

        return {
            "success": True,
            "episodes": selected_episodes,
            "category": category,
            "tag": tag
        }
    except Exception as e:
        print(f"DEBUG: 發生錯誤: {e}")
        logger.error(f"獲取節目推薦失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category-tags/{category}")
async def get_category_tags(category: str):
    """獲取分類標籤（前端專用）"""
    try:
        # 使用預定義的標籤
        category_tags = CATEGORY_TAGS.get(category, [])
        
        # 隨機選擇 4 個標籤
        if len(category_tags) > 4:
            selected_tags = random.sample(category_tags, 4)
        else:
            selected_tags = category_tags
        
        logger.info(f"為 {category} 類別選擇標籤: {selected_tags}")
        
        return {
            "success": True,
            "tags": selected_tags,
            "category": category
        }
    except Exception as e:
        logger.error(f"獲取類別標籤失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成 Podwise ID（前端專用）"""
    try:
        import random
        import string
        
        # 生成隨機 ID，格式為 PodwiseXXXX
        random_suffix = ''.join(random.choices(string.digits, k=4))
        podwise_id = f"Podwise{random_suffix}"
        
        return {
            "success": True,
            "podwise_id": podwise_id,
            "user_id": podwise_id,  # 使用相同的 Podwise ID 作為 user_id
            "message": "Podwise ID 生成成功"
        }
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/check/{user_code}")
async def check_user_exists(user_code: str):
    """檢查用戶是否存在（前端專用）"""
    try:
        # 模擬用戶檢查
        exists = user_code.startswith("Podwise")
        
        return {
            "success": True,
            "exists": exists,
            "user_code": user_code
        }
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/preferences")
async def save_user_preferences(request: Request):
    """保存用戶偏好（前端專用）"""
    try:
        body = await request.json()
        
        return {
            "success": True,
            "message": "用戶偏好保存成功",
            "data": body
        }
    except Exception as e:
        logger.error(f"保存用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def record_feedback(request: Request):
    """記錄用戶反饋（前端專用）"""
    try:
        body = await request.json()
        
        return {
            "success": True,
            "message": "反饋記錄成功",
            "data": body
        }
    except Exception as e:
        logger.error(f"記錄反饋失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/step4/save-preferences")
async def save_step4_preferences(request: Request):
    """保存 Step4 用戶偏好和選中的節目（前端專用）"""
    try:
        body = await request.json()
        user_id = body.get("user_id")
        main_category = body.get("main_category", "business")
        selected_episodes = body.get("selected_episodes", [])
        
        # 檢查用戶是否存在，如果不存在則自動創建
        if not user_id or not user_id.startswith("Podwise"):
            # 自動生成新的 Podwise ID
            import random
            import string
            random_suffix = ''.join(random.choices(string.digits, k=4))
            user_id = f"Podwise{random_suffix}"
            logger.info(f"自動生成新用戶 ID: {user_id}")
        
        # 模擬保存用戶偏好
        logger.info(f"保存用戶偏好: {user_id}, 主類別: {main_category}, 選中節目數: {len(selected_episodes)}")
        
        return {
            "success": True,
            "message": "Step4 用戶偏好保存成功",
            "user_id": user_id,
            "main_category": main_category,
            "selected_episodes_count": len(selected_episodes),
            "data": body
        }
    except Exception as e:
        logger.error(f"保存 Step4 偏好失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audio/presigned-url")
async def get_audio_presigned_url(request: Request):
    """獲取音檔預簽名 URL（前端專用）"""
    try:
        body = await request.json()
        rss_id = body.get("rss_id", "123")
        episode_title = body.get("episode_title", "測試節目")
        category = body.get("category", "business")
        
        # 構建音檔 URL
        audio_url = f"http://192.168.32.66:30090/business-one-min-audio/Spotify_RSS_{rss_id}_{episode_title}.mp3"
        
        return {
            "success": True,
            "audio_url": audio_url,
            "bucket": "business-one-min-audio",
            "object_key": f"Spotify_RSS_{rss_id}_{episode_title}.mp3"
        }
    except Exception as e:
        logger.error(f"獲取音檔 URL 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 反向代理功能 ====================

async def proxy_request(request: Request, target_url: str, strip_prefix: str = ""):
    """通用反向代理函數"""
    try:
        # 構建目標 URL
        path = request.url.path
        if strip_prefix and path.startswith(strip_prefix):
            path = path[len(strip_prefix):]
        
        target_path = f"{target_url}{path}"
        if request.url.query:
            target_path += f"?{request.url.query}"
        
        logger.info(f"代理請求: {request.url.path} -> {target_path}")
        
        # 準備請求頭
        headers = dict(request.headers)
        # 移除可能導致問題的頭部
        headers.pop("host", None)
        headers.pop("Host", None)
        
        # 準備請求體
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except:
                body = None
        
        # 發送請求到目標服務
        async with httpx.AsyncClient(timeout=60.0) as client:
            if request.method == "GET":
                response = await client.get(target_path, headers=headers)
            elif request.method == "POST":
                response = await client.post(target_path, headers=headers, content=body)
            elif request.method == "PUT":
                response = await client.put(target_path, headers=headers, content=body)
            elif request.method == "DELETE":
                response = await client.delete(target_path, headers=headers)
            elif request.method == "PATCH":
                response = await client.patch(target_path, headers=headers, content=body)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # 返回響應
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                # 處理 SSE 流
                async def stream_response():
                    async for chunk in response.aiter_bytes():
                        yield chunk
                
                return StreamingResponse(
                    stream_response(),
                    media_type=response.headers.get("content-type"),
                    headers=dict(response.headers)
                )
            else:
                # 處理普通響應
                return JSONResponse(
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
    except httpx.HTTPStatusError as e:
        logger.error(f"代理請求失敗 (HTTP {e.response.status_code}): {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"代理請求失敗: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# 動態創建反向代理路由
for route_prefix, config in PROXY_ROUTES.items():
    @app.api_route(f"{route_prefix}{{path:path}}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_route(request: Request, path: str, route_config=config):
        """動態反向代理路由"""
        return await proxy_request(request, route_config["target"], route_config["strip_prefix"])

# 全域異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011) 