#!/bin/bash

# 簡化的 RAG Pipeline 啟動腳本
# 跳過有問題的模組，只啟動基本功能

set -e

echo "[INFO] 啟動簡化的 RAG Pipeline 服務..."

# 設定環境變數
export PYTHONPATH="/app:$PYTHONPATH"
export PYTHONUNBUFFERED=1
export SKIP_PROBLEMATIC_MODULES=1

# 清理 Python 快取
echo "[INFO] 清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 創建簡化的 main.py
cat > main-simple.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="RAG Pipeline API", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RAG Pipeline API 運行中"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "RAG Pipeline"}

@app.get("/api/rag/query")
async def rag_query(q: str = "測試查詢"):
    return {
        "query": q,
        "response": "這是 RAG Pipeline 的測試回應",
        "status": "success"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
EOF

# 啟動簡化服務
echo "[INFO] 啟動簡化服務..."
exec python main-simple.py 