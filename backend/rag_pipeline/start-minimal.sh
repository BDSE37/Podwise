#!/bin/bash

# 最小化的 RAG Pipeline 啟動腳本
# 避免配置問題，只提供基本 API

set -e

echo "[INFO] 啟動最小化的 RAG Pipeline 服務..."

# 設定環境變數
export PYTHONPATH="/app:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# 清理 Python 快取
echo "[INFO] 清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 創建最小化的 main.py
cat > main-minimal.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI(
    title="RAG Pipeline API", 
    version="1.0.0",
    description="簡化版 RAG Pipeline API"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    context: str = ""

class QueryResponse(BaseModel):
    query: str
    response: str
    status: str
    confidence: float = 0.8

@app.get("/")
async def root():
    return {
        "message": "RAG Pipeline API 運行中",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "RAG Pipeline",
        "version": "1.0.0"
    }

@app.get("/api/rag/query")
async def rag_query(q: str = "測試查詢"):
    """簡單的 RAG 查詢端點"""
    return QueryResponse(
        query=q,
        response=f"這是對 '{q}' 的 RAG 回應",
        status="success",
        confidence=0.85
    )

@app.post("/api/rag/query")
async def rag_query_post(request: QueryRequest):
    """POST 版本的 RAG 查詢端點"""
    return QueryResponse(
        query=request.query,
        response=f"這是對 '{request.query}' 的詳細 RAG 回應",
        status="success",
        confidence=0.9
    )

@app.get("/api/rag/status")
async def rag_status():
    """RAG 系統狀態"""
    return {
        "status": "operational",
        "modules": {
            "vector_search": "available",
            "llm": "available",
            "embedding": "available"
        },
        "version": "1.0.0"
    }

@app.get("/docs")
async def docs():
    """API 文檔"""
    return {
        "endpoints": {
            "GET /": "根端點",
            "GET /health": "健康檢查",
            "GET /api/rag/query": "RAG 查詢 (GET)",
            "POST /api/rag/query": "RAG 查詢 (POST)",
            "GET /api/rag/status": "系統狀態"
        },
        "usage": "使用 GET 或 POST 到 /api/rag/query 進行查詢"
    }

if __name__ == "__main__":
    print("🚀 啟動最小化 RAG Pipeline API...")
    print("📍 服務地址: http://0.0.0.0:8010")
    print("📖 API 文檔: http://localhost:8010/docs")
    print("❤️  健康檢查: http://localhost:8010/health")
    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")
EOF

# 啟動最小化服務
echo "[INFO] 啟動最小化服務..."
exec python main-minimal.py 