#!/usr/bin/env python3
"""
Podwise API Gateway
統一管理所有微服務的反向代理
"""

import os
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise API Gateway",
    description="統一管理所有微服務的 API 網關",
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
SERVICES = {
    "stt": {
        "url": "http://localhost:8003",
        "name": "Speech-to-Text Service",
        "health_path": "/health"
    },
    "tts": {
        "url": "http://localhost:8002",
        "name": "Text-to-Speech Service",
        "health_path": "/health"
    },
    "ml": {
        "url": "http://localhost:8000",
        "name": "ML Pipeline Service",
        "health_path": "/health"
    },
    "rag": {
        "url": "http://localhost:8008",
        "name": "RAG Pipeline Service",
        "health_path": "/health"
    }
}

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Podwise API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": list(SERVICES.keys())
    }

@app.get("/health")
async def health_check():
    """健康檢查 - 檢查所有服務狀態"""
    health_status = {}
    
    for service_name, service_config in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_config['url']}{service_config['health_path']}")
                if response.status_code == 200:
                    health_status[service_name] = {
                        "status": "healthy",
                        "response": response.json()
                    }
                else:
                    health_status[service_name] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            health_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # 計算整體健康狀態
    healthy_services = sum(1 for status in health_status.values() if status["status"] == "healthy")
    total_services = len(SERVICES)
    
    return {
        "gateway_status": "healthy",
        "services": health_status,
        "summary": {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "health_percentage": (healthy_services / total_services) * 100 if total_services > 0 else 0
        }
    }

@app.get("/services")
async def list_services():
    """列出所有服務"""
    return {
        "services": {
            name: {
                "name": config["name"],
                "url": config["url"],
                "health_path": config["health_path"]
            }
            for name, config in SERVICES.items()
        }
    }

@app.api_route("/stt/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def stt_proxy(request: Request, path: str):
    """STT 服務代理"""
    return await proxy_request(request, "stt", path)

@app.api_route("/tts/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def tts_proxy(request: Request, path: str):
    """TTS 服務代理"""
    return await proxy_request(request, "tts", path)

@app.api_route("/ml/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ml_proxy(request: Request, path: str):
    """ML Pipeline 服務代理"""
    return await proxy_request(request, "ml", path)

@app.api_route("/rag/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def rag_proxy(request: Request, path: str):
    """RAG Pipeline 服務代理"""
    return await proxy_request(request, "rag", path)

async def proxy_request(request: Request, service_name: str, path: str):
    """代理請求到對應的服務"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_config = SERVICES[service_name]
    target_url = f"{service_config['url']}/{path}"
    
    try:
        # 讀取請求內容
        body = await request.body()
        headers = dict(request.headers)
        
        # 移除一些不需要轉發的標頭
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.RequestError as e:
        logger.error(f"Proxy request failed for {service_name}: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} is unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in proxy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "service": "api_gateway"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 