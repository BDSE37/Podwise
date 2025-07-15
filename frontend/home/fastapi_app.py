from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

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

# 設置模板
templates = Jinja2Templates(directory=Path(__file__).parent)

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
            "recommendation_service": "http://localhost:8006",
            "feedback_service": "http://localhost:8007",
            "minio_service": "http://localhost:9000"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    ) 