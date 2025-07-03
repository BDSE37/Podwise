#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise Frontend FastAPI 應用程式
提供前端頁面服務和路由重定向功能
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import os
import subprocess
import asyncio
from typing import Optional

# 創建 FastAPI 應用程式
app = FastAPI(
    title="Podwise Frontend",
    description="Podwise 智慧播客平台前端服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 設定路徑
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR

# 設定模板和靜態檔案
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class PodriService:
    """Podri 聊天服務管理類別"""
    
    def __init__(self):
        self.chat_dir = BASE_DIR.parent / "chat"
        self.podri_chat_path = self.chat_dir / "podri_chat.py"
        self.streamlit_process: Optional[subprocess.Popen] = None
        self.streamlit_port = 8501
    
    def is_podri_available(self) -> bool:
        """檢查 Podri 聊天應用程式是否可用"""
        return self.podri_chat_path.exists()
    
    async def start_streamlit(self) -> bool:
        """啟動 Streamlit 應用程式"""
        if not self.is_podri_available():
            return False
        
        try:
            # 檢查是否已經在運行
            if self.streamlit_process and self.streamlit_process.poll() is None:
                return True
            
            # 啟動 Streamlit 應用程式
            cmd = [
                "streamlit", "run", 
                str(self.podri_chat_path),
                "--server.port", str(self.streamlit_port),
                "--server.address", "0.0.0.0",
                "--server.headless", "true"
            ]
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                cwd=str(self.chat_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服務啟動
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            print(f"啟動 Streamlit 失敗: {e}")
            return False
    
    def get_streamlit_url(self) -> str:
        """獲取 Streamlit 應用程式 URL"""
        return f"http://localhost:{self.streamlit_port}"


# 創建 Podri 服務實例
podri_service = PodriService()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首頁路由"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"載入首頁失敗: {str(e)}")


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """登入頁面路由"""
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"載入登入頁面失敗: {str(e)}")


@app.get("/podri")
async def podri():
    """
    Podri 聊天應用程式路由
    自動啟動並重定向到 Streamlit 應用程式
    """
    if not podri_service.is_podri_available():
        raise HTTPException(
            status_code=404, 
            detail="Podri 聊天應用程式未找到，請確認 chat/podri_chat.py 檔案存在"
        )
    
    # 嘗試啟動 Streamlit 應用程式
    success = await podri_service.start_streamlit()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="無法啟動 Podri 聊天應用程式，請檢查 Streamlit 是否已安裝"
        )
    
    # 重定向到 Streamlit 應用程式
    streamlit_url = podri_service.get_streamlit_url()
    return RedirectResponse(url=streamlit_url, status_code=302)


@app.get("/podri/status")
async def podri_status():
    """檢查 Podri 服務狀態"""
    return {
        "available": podri_service.is_podri_available(),
        "running": podri_service.streamlit_process is not None and 
                  podri_service.streamlit_process.poll() is None,
        "url": podri_service.get_streamlit_url() if podri_service.is_podri_available() else None
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "Podwise Frontend",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    print("🚀 啟動 Podwise Frontend FastAPI 應用程式...")
    print(f"📁 工作目錄: {BASE_DIR}")
    print(f"📁 模板目錄: {TEMPLATES_DIR}")
    print(f"📁 靜態檔案目錄: {STATIC_DIR}")
    print(f"🤖 Podri 聊天應用程式: {podri_service.podri_chat_path}")
    print(f"✅ Podri 可用: {podri_service.is_podri_available()}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 