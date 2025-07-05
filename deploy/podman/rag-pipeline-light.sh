#!/bin/bash
# 輕量級 RAG Pipeline 部署腳本
# 避免安裝 PyTorch，使用 CPU 版本

set -e

echo "🚀 開始輕量級 RAG Pipeline 部署..."

# 1. 清理現有容器
echo "🗑️ 清理現有容器..."
podman stop rag-pipeline-light 2>/dev/null || true
podman rm rag-pipeline-light 2>/dev/null || true

# 2. 創建新的容器
echo "🔨 創建新的輕量級 RAG Pipeline 容器..."
podman run -d \
    --name rag-pipeline-light \
    --network host \
    -v /home/bai/Desktop/Podwise/backend/rag_pipeline:/app \
    -v /home/bai/Desktop/Podwise/data:/app/data \
    -e PYTHONPATH=/app \
    -e CUDA_VISIBLE_DEVICES="" \
    -e OLLAMA_HOST=http://192.168.32.38:11434 \
    -e TTS_HOST=http://192.168.32.38:8002 \
    -e MILVUS_HOST=192.168.32.86 \
    -e MILVUS_PORT=19530 \
    python:3.11-slim \
    /bin/bash -c "
        echo '📦 安裝系統依賴...' &&
        apt-get update && apt-get install -y gcc g++ curl &&
        echo '📦 安裝 Python 依賴...' &&
        pip install --no-cache-dir --upgrade pip &&
        pip install --no-cache-dir fastapi uvicorn pydantic &&
        pip install --no-cache-dir langchain langchain-community langchain-openai &&
        pip install --no-cache-dir sentence-transformers faiss-cpu pymilvus &&
        pip install --no-cache-dir crewai>=0.11.0 &&
        pip install --no-cache-dir httpx requests python-multipart &&
        pip install --no-cache-dir psycopg2-binary pymongo redis sqlalchemy &&
        pip install --no-cache-dir numpy pandas scikit-learn &&
        pip install --no-cache-dir nltk jieba opencc-python-reimplemented &&
        pip install --no-cache-dir prometheus-client langfuse python-dotenv &&
        pip install --no-cache-dir aiofiles beautifulsoup4 tiktoken tqdm &&
        pip install --no-cache-dir supabase asyncio-mqtt huggingface_hub &&
        echo '🚀 啟動 RAG Pipeline...' &&
        cd /app &&
        python -m uvicorn app.main_integrated:app --host 0.0.0.0 --port 8004
    "

# 3. 等待容器啟動
echo "⏳ 等待容器啟動..."
sleep 60

# 4. 檢查容器狀態
echo "📊 檢查容器狀態..."
podman ps | grep rag-pipeline

# 5. 檢查容器日誌
echo "📝 檢查容器日誌..."
podman logs rag-pipeline-light | tail -20

# 6. 測試健康檢查
echo "🏥 測試健康檢查..."
sleep 30
curl -f http://localhost:8004/health || echo "❌ 健康檢查失敗，請檢查日誌"

echo "✅ 輕量級 RAG Pipeline 部署完成！"
echo "📋 管理指令："
echo "查看日誌: podman logs rag-pipeline-light -f"
echo "停止容器: podman stop rag-pipeline-light"
echo "重啟容器: podman restart rag-pipeline-light"
echo "進入容器: podman exec -it rag-pipeline-light bash" 