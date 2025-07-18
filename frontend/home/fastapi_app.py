from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn
from pathlib import Path
import httpx
import logging

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
            "api_gateway": "http://localhost:8006",
            "recommendation_service": "http://localhost:8006",
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
    """RAG Pipeline 查詢 - 代理到後端 API Gateway"""
    try:
        body = await request.json()
        logger.info(f"RAG 查詢請求: {body}")
        
        # 直接代理到後端 API Gateway 的 RAG 查詢端點
        backend_url = f"{BACKEND_API_URL}/api/v1/query"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(backend_url, json=body)
            logger.info(f"RAG 回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG 服務回應錯誤: {response.status_code}")
                return {"error": f"RAG service error: {response.status_code}"}
                
    except Exception as e:
        logger.error(f"RAG Pipeline 查詢失敗: {e}")
        return {"error": str(e)}

@app.post("/api/rag/validate-user")
async def rag_validate_user(request: Request):
    """RAG Pipeline 用戶驗證"""
    body = await request.json()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{RAG_API_URL}/api/v1/validate-user", json=body)
            return response.json()
        except Exception as e:
            logger.error(f"RAG Pipeline 用戶驗證失敗: {e}")
            return {"error": str(e)}

@app.get("/api/rag/tts/voices")
async def rag_tts_voices():
    """RAG Pipeline TTS 語音列表"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{RAG_API_URL}/api/v1/tts/voices")
            return response.json()
        except Exception as e:
            logger.error(f"RAG Pipeline TTS 語音列表失敗: {e}")
            return {"error": str(e)}

@app.post("/api/rag/tts/synthesize")
async def rag_tts_synthesize(request: Request):
    """RAG Pipeline TTS 語音合成"""
    body = await request.json()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{RAG_API_URL}/api/v1/tts/synthesize", json=body)
            return response.json()
        except Exception as e:
            logger.error(f"RAG Pipeline TTS 語音合成失敗: {e}")
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