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

# 設置模板
templates = Jinja2Templates(directory=Path(__file__).parent)

# 後端 API 服務 URL - 修正端口為 8008 (API 閘道)
BACKEND_API_URL = "http://localhost:8008"
# RAG Pipeline API 服務 URL - 使用 API Gateway
RAG_API_URL = "http://localhost:8008"

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
        
        # 嘗試連接到後端 API Gateway
        try:
            backend_url = f"{BACKEND_API_URL}/api/v1/query"
            
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
    """生成本地回應（當後端不可用時）"""
    query = body.get("query", "")
    user_id = body.get("user_id", "Podwise0001")
    enable_tts = body.get("enable_tts", True)
    voice = body.get("voice", "podrina")
    
    # 生成智能回應
    response_text = generate_smart_response(query)
    
    # 如果啟用 TTS，嘗試調用 TTS 服務
    audio_data = None
    if enable_tts:
        try:
            # 直接調用 TTS 服務
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
        "timestamp": datetime.now().isoformat()
    }

def generate_smart_response(query: str) -> str:
    """生成智能回應"""
    query_lower = query.lower()
    
    if "商業" in query or "business" in query_lower:
        return f"根據您的查詢「{query}」，我為您推薦以下商業相關播客：\n\n1. **股癌** - 專業的股市分析與投資策略\n2. **查理的創業化合物** - 創業經驗分享與商業洞察\n3. **吳淡如人生實用商學院** - 實用的商業智慧與人生哲學\n\n這些節目都經過精心挑選，符合您對商業內容的興趣。您想深入了解哪個主題呢？"
    
    elif "教育" in query or "education" in query_lower:
        return f"針對您的教育相關查詢「{query}」，我推薦以下優質教育播客：\n\n1. **知識就是力量** - 深度學習與知識分享\n2. **科學人** - 科學知識與最新研究\n3. **歷史學堂** - 歷史故事與文化傳承\n\n這些節目能幫助您持續學習和成長。您對哪個領域特別感興趣？"
    
    elif "推薦" in query or "推薦" in query:
        return f"很高興您詢問「{query}」！基於您的偏好，我為您精選了以下播客：\n\n🎧 **熱門推薦**\n- 股癌：專業財經分析\n- 查理的創業化合物：創業實戰經驗\n- 吳淡如人生實用商學院：實用商業智慧\n\n🎯 **個性化推薦**\n- 根據您的收聽歷史\n- 考慮您的興趣偏好\n- 結合當前熱門話題\n\n您想從哪個開始聽起呢？"
    
    else:
        return f"您好！我收到了您的查詢：「{query}」。\n\n作為您的個人播客助手，我可以：\n\n✅ 推薦符合您興趣的播客節目\n✅ 提供商業、教育等各類內容\n✅ 根據您的偏好進行個性化推薦\n✅ 回答關於播客內容的問題\n\n請告訴我您想聽什麼類型的主題，我會為您找到最適合的內容！"

def generate_silent_audio() -> str:
    """生成靜音音頻數據（Base64 格式）"""
    # 這是一個非常短的 WAV 格式靜音音頻的 Base64 編碼
    # 實際應用中，這裡會是真正的 TTS 音頻數據
    return "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"

async def generate_tts_audio(text: str, voice: str) -> Optional[Dict[str, Any]]:
    """生成 TTS 音頻"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BACKEND_API_URL}/api/v1/tts/synthesize", json={
                "text": text,
                "voice": voice,
                "speed": "+0%"
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"TTS 服務回應錯誤: {response.status_code}")
                return None
                
    except Exception as e:
        logger.warning(f"TTS 服務調用失敗: {e}")
        return None

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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BACKEND_API_URL}/api/v1/tts/synthesize", json=body)
            return response.json()
    except Exception as e:
        logger.error(f"TTS 語音合成失敗: {e}")
        return {"error": str(e)}

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

# 移除模擬端點，讓代理中間件處理這些請求

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
    for prefix in PROXY_PREFIXES:
        if request.url.path.startswith(prefix):
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