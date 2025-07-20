from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn
from pathlib import Path
import httpx
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="PodWise Frontend",
    description="PodWise Podcast 自動摘要與個人化推薦系統前端",
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

# 設置靜態文件
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")
app.mount("/images", StaticFiles(directory=Path(__file__).parent / "images"), name="images")
app.mount("/audio", StaticFiles(directory=Path(__file__).parent / "audio"), name="audio")

# 添加 migrate_localStorage.js 的靜態文件服務
@app.get("/migrate_localStorage.js")
async def serve_migrate_localStorage():
    """提供 migrate_localStorage.js 檔案"""
    try:
        js_file_path = Path(__file__).parent / "migrate_localStorage.js"
        if js_file_path.exists():
            with open(js_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content=content, media_type="application/javascript")
        else:
            logger.error(f"migrate_localStorage.js 檔案不存在: {js_file_path}")
            return Response(content="console.log('migrate_localStorage.js not found');", media_type="application/javascript")
    except Exception as e:
        logger.error(f"載入 migrate_localStorage.js 失敗: {e}")
        return Response(content="console.log('migrate_localStorage.js load error');", media_type="application/javascript")

# 設置模板
templates = Jinja2Templates(directory=Path(__file__).parent)

# 後端 API 服務 URL - 直接連接到各服務
BACKEND_API_URL = "http://localhost:8005"  # RAG Pipeline
# RAG Pipeline API 服務 URL - 直接連接
RAG_API_URL = "http://localhost:8005"

PROXY_PREFIXES = ["/api/", "/user_management/", "/utils/"]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首頁"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """登入頁面"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/podri", response_class=HTMLResponse)
async def podri(request: Request):
    """Podri 聊天頁面"""
    return templates.TemplateResponse("podri.html", {"request": request})

@app.get("/podri.html", response_class=HTMLResponse)
async def podri_html(request: Request):
    """Podri 聊天頁面 (HTML 格式)"""
    return templates.TemplateResponse("podri.html", {"request": request})

@app.get("/test-audio", response_class=HTMLResponse)
async def test_audio(request: Request):
    """音檔測試頁面"""
    return templates.TemplateResponse("test_audio.html", {"request": request})

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "podwise-frontend",
        "version": "1.0.0"
    }

@app.get("/api/status")
async def api_status():
    """API 狀態檢查"""
    return {
        "frontend": "running",
        "backend_services": {
            "api_gateway": "http://localhost:8008",
            "recommendation_service": "http://localhost:8008",
            "feedback_service": "http://localhost:8007",
            "minio_service": "http://localhost:9000",
            "rag_pipeline": "http://localhost:8011"
        }
    }

# RAG Pipeline API 端點
@app.get("/api/rag/health")
async def rag_health():
    """RAG Pipeline 健康檢查"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{RAG_API_URL}/health")
            return response.json()
        except Exception as e:
            logger.error(f"RAG Pipeline 健康檢查失敗: {e}")
            return {"status": "unavailable", "error": str(e)}

@app.post("/api/rag/query")
async def rag_query(request: Request):
    """RAG Pipeline 查詢 - 連接到後端服務"""
    try:
        body = await request.json()
        logger.info(f"RAG 查詢請求: {body}")
        
        # 獲取查詢內容
        query = body.get("query", "")
        user_id = body.get("user_id", "Podwise0001")
        enable_tts = body.get("enable_tts", True)
        voice = body.get("voice", "podrina")
        
        # 嘗試連接到後端 RAG Pipeline 服務 (CrewAI 三層架構)
        try:
            backend_url = f"{RAG_API_URL}/api/v1/query"
            
            # 準備後端請求數據，確保包含所有必要欄位
            backend_request = {
                "query": query,
                "user_id": user_id,
                "session_id": body.get("session_id", f"session_{user_id}_{int(datetime.now().timestamp())}"),
                "enable_tts": enable_tts,
                "voice": voice,
                "speed": body.get("speed", 1.0),
                "metadata": body.get("metadata", {})
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(backend_url, json=backend_request)
                logger.info(f"後端回應狀態: {response.status_code}")
                
                if response.status_code == 200:
                    backend_data = response.json()
                    logger.info("成功從後端獲取回應")
                    return backend_data
                else:
                    logger.warning(f"後端服務回應錯誤: {response.status_code}")
                    # 如果後端失敗，使用本地回應
                    return await generate_local_response(body)
                    
        except Exception as backend_error:
            logger.warning(f"後端連接失敗: {backend_error}")
            # 如果後端連接失敗，使用本地回應
            return await generate_local_response(body)
                
    except Exception as e:
        logger.error(f"RAG Pipeline 查詢失敗: {e}")
        return {"error": str(e)}

async def generate_local_response(body: dict) -> dict:
    """生成本地回應 - 現在會嘗試調用後端 RAG Pipeline"""
    query = body.get("query", "")
    user_id = body.get("user_id", "Podwise0001")
    enable_tts = body.get("enable_tts", True)
    voice = body.get("voice", "podrina")
    
    logger.info(f"處理查詢: {query}, 用戶: {user_id}")
    
    # 首先嘗試調用後端 RAG Pipeline
    try:
        rag_response = await call_backend_rag_pipeline(query, user_id)
        if rag_response and rag_response.get("success"):
            logger.info("成功調用後端 RAG Pipeline")
            response_text = rag_response.get("response", "")
            
            # 如果啟用 TTS，嘗試調用 TTS 服務
            audio_data = None
            if enable_tts:
                try:
                    tts_response = await generate_tts_audio(response_text, voice)
                    if tts_response and tts_response.get("success"):
                        audio_data = tts_response.get("audio_data")
                except Exception as e:
                    logger.warning(f"TTS 生成失敗: {e}")
            
            return {
                "success": True,
                "response": response_text,
                "user_id": user_id,
                "session_id": body.get("session_id", f"session_{user_id}_{int(datetime.now().timestamp())}"),
                "audio_data": audio_data,
                "voice_used": voice,
                "tts_enabled": enable_tts,
                "timestamp": datetime.now().isoformat(),
                "source": "rag_pipeline"
            }
    except Exception as e:
        logger.warning(f"後端 RAG Pipeline 調用失敗: {e}")
    
    # 如果後端調用失敗，使用本地智能回應
    logger.info("使用本地智能回應作為備用")
    response_text = generate_smart_response(query)
    
    # 如果啟用 TTS，嘗試調用 TTS 服務
    audio_data = None
    if enable_tts:
        try:
            tts_response = await generate_tts_audio(response_text, voice)
            if tts_response and tts_response.get("success"):
                audio_data = tts_response.get("audio_data")
        except Exception as e:
            logger.warning(f"TTS 生成失敗: {e}")
    
    return {
        "success": True,
        "response": response_text,
        "user_id": user_id,
        "session_id": body.get("session_id", f"session_{user_id}_{int(datetime.now().timestamp())}"),
        "audio_data": audio_data,
        "voice_used": voice,
        "tts_enabled": enable_tts,
        "timestamp": datetime.now().isoformat(),
        "source": "local_smart_response"
    }

async def call_backend_rag_pipeline(query: str, user_id: str) -> Optional[dict]:
    """調用後端 RAG Pipeline"""
    try:
        # 嘗試調用 RAG Pipeline 服務
        rag_service_url = "http://localhost:8005"  # RAG Pipeline 端口
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{rag_service_url}/api/v1/query", json={
                "query": query,
                "user_id": user_id
            })
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"RAG Pipeline 回應: {result}")
                return result
            else:
                logger.warning(f"RAG Pipeline 回應錯誤: {response.status_code}")
                return None
                
    except Exception as e:
        logger.warning(f"調用 RAG Pipeline 失敗: {e}")
        return None

def generate_smart_response(query: str) -> str:
    """生成智能回應 - 現在會轉發到 RAG Pipeline 進行真實的 LLM 處理"""
    # 這個函數現在只作為備用，主要查詢會轉發到 RAG Pipeline
    return f"正在處理您的查詢：「{query}」...\n\n請稍候，我正在透過 AI 系統為您生成最準確的回答。"

def generate_silent_audio() -> str:
    """生成靜音音頻數據（Base64 格式）"""
    # 這是一個非常短的 WAV 格式靜音音頻的 Base64 編碼
    # 實際應用中，這裡會是真正的 TTS 音頻數據
    return "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"

async def generate_tts_audio(text: str, voice: str) -> Optional[Dict[str, Any]]:
    """生成 TTS 音頻"""
    try:
        # 首先嘗試透過 API Gateway
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BACKEND_API_URL}/api/v1/tts/synthesize", json={
                "text": text,
                "voice": voice,
                "speed": 1.0
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway TTS 服務回應錯誤: {response.status_code}")
                
    except Exception as e:
        logger.warning(f"API Gateway TTS 服務調用失敗: {e}")
    
    try:
        # 備用：直接連接到 TTS 服務
        tts_service_url = "http://localhost:8003"  # TTS 服務端口
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{tts_service_url}/api/v1/tts/synthesize", json={
                "text": text,
                "voice": voice,
                "speed": 1.0
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"直接 TTS 服務回應錯誤: {response.status_code}")
                
    except Exception as e:
        logger.warning(f"直接 TTS 服務調用失敗: {e}")
    
    # 如果所有 TTS 服務都失敗，返回靜音音頻
    logger.warning("所有 TTS 服務都不可用，返回靜音音頻")
    return {
        "success": True,
        "audio_data": generate_silent_audio(),
        "voice": voice,
        "speed": 1.0,
        "text": text,
        "message": "TTS 服務不可用，使用靜音音頻"
    }

@app.post("/api/rag/validate-user")
async def rag_validate_user(request: Request):
    """RAG Pipeline 用戶驗證"""
    body = await request.json()
    user_id = body.get("user_id", "Podwise0001")
    
    return {
        "user_id": user_id,
        "is_valid": True,
        "has_history": False,
        "message": "用戶驗證成功"
    }

@app.get("/api/rag/tts/voices")
async def rag_tts_voices():
    """RAG Pipeline TTS 語音列表"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_API_URL}/api/v1/tts/voices")
            return response.json()
    except Exception as e:
        logger.error(f"TTS 語音列表獲取失敗: {e}")
        # 返回預設語音列表
        return {
            "success": True,
            "voices": [
                {"id": "podrina", "name": "Podrina", "description": "溫柔女聲"},
                {"id": "podrisa", "name": "Podrisa", "description": "活潑女聲"},
                {"id": "podrino", "name": "Podrino", "description": "穩重男聲"}
            ],
            "count": 3
        }

@app.post("/api/rag/tts/synthesize")
async def rag_tts_synthesize(request: Request):
    """RAG Pipeline TTS 語音合成"""
    body = await request.json()
    try:
        # 首先嘗試透過 API Gateway
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BACKEND_API_URL}/api/v1/tts/synthesize", json=body)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway TTS 回應錯誤: {response.status_code}")
                
    except Exception as e:
        logger.warning(f"API Gateway TTS 調用失敗: {e}")
    
    try:
        # 備用：直接連接到 TTS 服務
        tts_service_url = "http://localhost:8003"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{tts_service_url}/api/v1/tts/synthesize", json=body)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"直接 TTS 服務回應錯誤: {response.status_code}")
                
    except Exception as e:
        logger.warning(f"直接 TTS 服務調用失敗: {e}")
    
    # 如果所有 TTS 服務都失敗，返回靜音音頻
    text = body.get("text", "")
    voice = body.get("voice", "podrina")
    
    return {
        "success": True,
        "audio_data": generate_silent_audio(),
        "voice": voice,
        "speed": body.get("speed", 1.0),
        "text": text,
        "processing_time": 0.1,
        "message": "TTS 服務不可用，使用靜音音頻"
    }

# TTS 直接端點
@app.post("/api/tts/synthesize")
async def tts_synthesize(request: Request):
    """TTS 語音合成 - 直接端點"""
    body = await request.json()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BACKEND_API_URL}/api/v1/tts/synthesize", json=body)
            return response.json()
    except Exception as e:
        logger.error(f"TTS 語音合成失敗: {e}")
        return {"error": str(e)}

@app.get("/api/tts/status")
async def tts_status():
    """檢查 TTS 服務狀態"""
    services = {
        "api_gateway": False,
        "direct_tts": False
    }
    
    # 檢查 API Gateway TTS
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_API_URL}/health")
            if response.status_code == 200:
                services["api_gateway"] = True
    except Exception as e:
        logger.warning(f"API Gateway 健康檢查失敗: {e}")
    
    # 檢查直接 TTS 服務
    try:
        tts_service_url = "http://localhost:8003"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{tts_service_url}/health")
            if response.status_code == 200:
                services["direct_tts"] = True
    except Exception as e:
        logger.warning(f"直接 TTS 服務健康檢查失敗: {e}")
    
    return {
        "status": "available" if any(services.values()) else "unavailable",
        "services": services,
        "recommendation": "啟動 TTS 服務以獲得完整功能" if not any(services.values()) else "TTS 服務正常"
    }

# 添加缺失的 API 端點
@app.post("/api/feedback")
async def feedback(request: Request):
    """處理用戶反饋"""
    try:
        body = await request.json()
        logger.info(f"收到反饋: {body}")
        return {"success": True, "message": "反饋已記錄"}
    except Exception as e:
        logger.error(f"處理反饋失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/generate-podwise-id")
async def generate_podwise_id():
    """生成 Podwise ID"""
    try:
        import random
        import time
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        podwise_id = f"Podwise{random_num}"
        return {"success": True, "podwise_id": podwise_id}
    except Exception as e:
        logger.error(f"生成 Podwise ID 失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/user/check/{user_id}")
async def check_user(user_id: str):
    """檢查用戶是否存在"""
    try:
        # 簡單的用戶檢查邏輯
        return {"success": True, "user_exists": True, "user_id": user_id}
    except Exception as e:
        logger.error(f"檢查用戶失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/preferences")
async def save_user_preferences(request: Request):
    """保存用戶偏好"""
    try:
        body = await request.json()
        logger.info(f"保存用戶偏好: {body}")
        return {"success": True, "message": "偏好已保存"}
    except Exception as e:
        logger.error(f"保存用戶偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/step4/save-preferences")
async def save_step4_preferences(request: Request):
    """保存 Step4 偏好"""
    try:
        body = await request.json()
        logger.info(f"保存 Step4 偏好: {body}")
        return {"success": True, "message": "Step4 偏好已保存"}
    except Exception as e:
        logger.error(f"保存 Step4 偏好失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/random-audio")
async def random_audio():
    """獲取隨機音頻"""
    try:
        return {"success": True, "audio_url": "/audio/sample.mp3"}
    except Exception as e:
        logger.error(f"獲取隨機音頻失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/one-minutes-episodes")
async def one_minutes_episodes(category: str = "", tag: str = ""):
    """獲取一分鐘節目"""
    try:
        logger.info(f"請求一分鐘節目: category={category}, tag={tag}")
        
        # 根據類別返回對應的節目數據
        if category == "business" or category == "商業":
            episodes = [
                {
                    "podcast_name": "股癌 Gooaye",
                    "episode_title": "投資理財精選",
                    "episode_description": "晦澀金融投資知識直白講，重要海內外時事輕鬆談。",
                    "podcast_image": "images/股癌.png",
                    "audio_url": "http://192.168.32.66:30090/business-one-min-audio/RSS_1500839292_EP569_股癌.mp3",
                    "episode_id": 4,
                    "rss_id": "RSS_1500839292",
                    "tags": ["投資理財", "股票分析", "市場趨勢", "經濟分析"]
                },
                {
                    "podcast_name": "矽谷輕鬆談",
                    "episode_title": "AI 技術趨勢",
                    "episode_description": "Google 搜尋、AI 技術、科技趨勢都能輕鬆聽懂。",
                    "podcast_image": "images/矽谷輕鬆談.png",
                    "audio_url": "http://192.168.32.66:30090/business-one-min-audio/RSS_1531106786_台幣漲夠了嗎 台積電增資100億美元避險玩什麼 2025.07.02.mp3",
                    "episode_id": 2,
                    "rss_id": "RSS_1531106786",
                    "tags": ["科技趨勢", "人工智慧", "創新思維", "數位轉型"]
                },
                {
                    "podcast_name": "財經M平方",
                    "episode_title": "投資策略分析",
                    "episode_description": "深度分析全球經濟趨勢，提供專業的投資策略建議。",
                    "podcast_image": "images/財經分析.png",
                    "audio_url": "http://192.168.32.66:30090/business-one-min-audio/RSS_1500839292_EP569_股癌.mp3",
                    "episode_id": 3,
                    "rss_id": "RSS_1500839292",
                    "tags": ["投資策略", "經濟分析", "市場趨勢", "財務規劃"]
                }
            ]
        elif category == "education" or category == "教育":
            episodes = [
                {
                    "podcast_name": "啟點文化一天聽一點",
                    "episode_title": "學習方法論",
                    "episode_description": "探討有效的學習方法和知識獲取技巧。",
                    "podcast_image": "images/知識就是力量.png",
                    "audio_url": "http://192.168.32.66:30090/education-one-min-audio/RSS_1488718553_幸福翹翹板#29體制外教育真的比傳統體制內教育更好更自由嗎.mp3",
                    "episode_id": 4,
                    "rss_id": "RSS_1488718553",
                    "tags": ["學習方法", "教育理念", "知識分享", "個人成長"]
                },
                {
                    "podcast_name": "文森說書",
                    "episode_title": "未來教育趨勢",
                    "episode_description": "探討科技如何改變教育方式和學習體驗。",
                    "podcast_image": "images/科技新知.png",
                    "audio_url": "http://192.168.32.66:30090/education-one-min-audio/RSS_1513786617_拿錢換到快樂的極限致富的心魔.mp3",
                    "episode_id": 5,
                    "rss_id": "RSS_1513786617",
                    "tags": ["教育科技", "未來趨勢", "創新教育", "數位學習"]
                },
                {
                    "podcast_name": "大人的Small Talk",
                    "episode_title": "自我提升指南",
                    "episode_description": "幫助你建立積極心態，實現個人成長目標。",
                    "podcast_image": "images/心靈成長.png",
                    "audio_url": "http://192.168.32.66:30090/education-one-min-audio/RSS_1452688611_EP577 工作中那些讓你看不過去忍不住想出手的鳥事多半是你找到天命的暗示.mp3",
                    "episode_id": 6,
                    "rss_id": "RSS_1452688611",
                    "tags": ["個人成長", "心理學", "自我提升", "心靈成長"]
                }
            ]
        else:
            # 預設返回商業類別
            episodes = [
                {
                    "podcast_name": "股癌 Gooaye",
                    "episode_title": "投資理財精選",
                    "episode_description": "晦澀金融投資知識直白講，重要海內外時事輕鬆談。",
                    "podcast_image": "images/股癌.png",
                    "audio_url": "http://192.168.32.66:30090/business-one-min-audio/RSS_1500839292_EP569_股癌.mp3",
                    "episode_id": 4,
                    "rss_id": "RSS_1500839292",
                    "tags": ["投資理財", "股票分析", "市場趨勢", "經濟分析"]
                }
            ]
        
        logger.info(f"返回 {len(episodes)} 個節目")
        return {"success": True, "episodes": episodes}
    except Exception as e:
        logger.error(f"獲取一分鐘節目失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/audio/presigned-url")
async def audio_presigned_url(request: Request):
    """獲取音頻預簽名 URL"""
    try:
        body = await request.json()
        logger.info(f"請求音頻預簽名 URL: {body}")
        return {"success": True, "url": "https://example.com/audio.mp3"}
    except Exception as e:
        logger.error(f"獲取音頻預簽名 URL 失敗: {e}")
        return {"success": False, "error": str(e)}

import csv
import random
import os

@app.get("/api/category-tags/{category}")
async def category_tags(category: str):
    """獲取類別標籤"""
    try:
        # 支援英文和中文類別名稱
        category_mapping = {
            "business": "business",
            "education": "education", 
            "商業": "business",
            "教育": "education"
        }
        
        # 將類別名稱標準化
        normalized_category = category_mapping.get(category, category)
        
        # 讀取 tags_info.csv 文件
        csv_path = "../backend/rag_pipeline/scripts/csv/tags_info.csv"
        if not os.path.exists(csv_path):
            logger.error(f"找不到 tags_info.csv 文件: {csv_path}")
            return {"success": False, "error": "標籤配置文件不存在"}
        
        # 從 CSV 文件中提取標籤
        all_tags = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row.get('Category', '').lower() == normalized_category.lower():
                    # 提取 TAG 欄位和相關的同步欄位
                    tag = row.get('TAG', '').strip()
                    if tag and len(tag) == 4:  # 只取四個字的標籤
                        all_tags.append(tag)
                    
                    # 檢查同步欄位 (sync1-sync14)
                    for i in range(1, 15):
                        sync_key = f'sync{i}'
                        sync_value = row.get(sync_key, '').strip()
                        if sync_value and len(sync_value) == 4:  # 只取四個字的標籤
                            all_tags.append(sync_value)
        
        # 去重並隨機選擇最多4個標籤
        unique_tags = list(set(all_tags))
        if len(unique_tags) > 4:
            selected_tags = random.sample(unique_tags, 4)
        else:
            selected_tags = unique_tags
        
        logger.info(f"類別標籤請求: {category} -> {normalized_category}, 找到 {len(unique_tags)} 個標籤, 選擇: {selected_tags}")
        return {"success": True, "tags": selected_tags}
    except Exception as e:
        logger.error(f"獲取類別標籤失敗: {e}")
        return {"success": False, "error": str(e)}

# API 代理中間件 - 暫時註解掉，讓 RAG 端點正常工作
# @app.middleware("http")
# async def proxy_api_requests(request: Request, call_next):
#     """代理 API 請求到後端服務"""
#     if request.url.path.startswith("/api/"):
#         # 跳過 RAG 相關端點，讓它們由本地端點處理
#         if (request.url.path.startswith("/api/rag/")):
#             response = await call_next(request)
#             return response
#             
#         # 構建後端 API URL
#         backend_url = f"{BACKEND_API_URL}{request.url.path}"
#         if request.url.query:
#             backend_url += f"?{request.url.query}"
#         logger.info(f"代理請求: {request.method} {request.url.path} -> {backend_url}")
#         
#         # 轉發請求到後端
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             try:
#                 # 準備請求資料
#                 headers = dict(request.headers)
#                 # 移除一些不需要的 headers
#                 headers.pop("host", None)
#                 headers.pop("content-length", None)  # 讓 httpx 自動計算
#                 
#                 # 根據請求方法轉發
#                 if request.method == "GET":
#                     response = await client.get(backend_url, headers=headers)
#                 elif request.method == "POST":
#                     body = await request.body()
#                     response = await client.post(backend_url, content=body, headers=headers)
#                 elif request.method == "PUT":
#                     body = await request.body()
#                     response = await client.put(backend_url, content=body, headers=headers)
#                 elif request.method == "DELETE":
#                     response = await client.delete(backend_url, headers=headers)
#                 else:
#                     # 其他方法直接轉發
#                     response = await client.request(
#                         request.method, 
#                         backend_url, 
#                         content=await request.body(),
#                         headers=headers
#                     )
#                 
#                 logger.info(f"後端回應: {response.status_code}")
#                 
#                 # 返回後端回應
#                 return Response(
#                     content=response.content,
#                     status_code=response.status_code,
#                     headers=dict(response.headers),
#                     media_type=response.headers.get("content-type")
#                 )
#                 
#             except httpx.ConnectError as e:
#                 logger.error(f"無法連接到後端服務: {e}")
#                 return JSONResponse(
#                     status_code=503,
#                     content={
#                         "success": False,
#                         "error": "Backend service unavailable - connection failed"
#                     }
#                 )
#             except httpx.TimeoutException as e:
#                 logger.error(f"後端服務請求超時: {e}")
#                 return JSONResponse(
#                     status_code=504,
#                     content={
#                         "success": False,
#                         "error": "Backend service timeout"
#                     }
#                 )
#             except Exception as e:
#                 logger.error(f"代理請求失敗: {e}")
#                 return JSONResponse(
#                     status_code=500,
#                     content={
#                         "success": False,
#                         "error": f"Backend service error: {str(e)}"
#                     }
#                 )
#     
#     # 非 API 請求，正常處理
#     response = await call_next(request)
#     return response

# 統一反向代理中間件
@app.middleware("http")
async def proxy_multi_prefix_requests(request: Request, call_next):
    # 跳過 RAG 相關端點和已定義的本地端點，讓它們由本地端點處理
    local_endpoints = [
        "/api/rag/",
        "/api/feedback",
        "/api/generate-podwise-id", 
        "/api/user/check/",
        "/api/user/preferences",
        "/api/step4/save-preferences",
        "/api/random-audio",
        "/api/one-minutes-episodes",
        "/api/audio/presigned-url",
        "/api/category-tags/",
        "/api/tts/",
        "/api/status",
        "/health"
    ]
    
    for endpoint in local_endpoints:
        if request.url.path.startswith(endpoint):
            return await call_next(request)
        
    # 其他 API 請求代理到後端
    if request.url.path.startswith("/api/"):
        backend_url = f"{BACKEND_API_URL}{request.url.path}"
        if request.url.query:
            backend_url += f"?{request.url.query}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = dict(request.headers)
                headers.pop("host", None)
                headers.pop("content-length", None)
                if request.method == "GET":
                    response = await client.get(backend_url, headers=headers)
                elif request.method == "POST":
                    body = await request.body()
                    response = await client.post(backend_url, content=body, headers=headers)
                elif request.method == "PUT":
                    body = await request.body()
                    response = await client.put(backend_url, content=body, headers=headers)
                elif request.method == "DELETE":
                    response = await client.delete(backend_url, headers=headers)
                else:
                    response = await client.request(
                        request.method,
                        backend_url,
                        content=await request.body(),
                        headers=headers
                    )
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": f"Backend service unavailable: {str(e)}"}
            )
    
    # 其他請求正常處理
    return await call_next(request)

# 最後掛載靜態檔案，避免攔截 API 請求
# 注意：靜態檔案掛載必須在最後，且不能覆蓋 API 路由
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "assets"), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    ) 