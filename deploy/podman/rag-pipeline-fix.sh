#!/bin/bash
# RAG Pipeline 修復腳本
# 修復缺少的 crewai 依賴問題

set -e

echo "🔧 開始修復 RAG Pipeline..."

# 1. 檢查現有的容器
echo "📋 檢查現有容器..."
EXISTING_CONTAINER=$(podman ps -a --filter "name=rag-pipeline" --format "{{.Names}}")

if [ -n "$EXISTING_CONTAINER" ]; then
    echo "🗑️ 停止並刪除現有容器: $EXISTING_CONTAINER"
    podman stop $EXISTING_CONTAINER 2>/dev/null || true
    podman rm $EXISTING_CONTAINER 2>/dev/null || true
fi

# 2. 檢查現有映像檔
echo "🔍 檢查現有映像檔..."
EXISTING_IMAGE=$(podman images --filter "reference=podwise-rag-pipeline" --format "{{.Repository}}:{{.Tag}}")

if [ -n "$EXISTING_IMAGE" ]; then
    echo "📦 使用現有映像檔: $EXISTING_IMAGE"
    BASE_IMAGE=$EXISTING_IMAGE
else
    echo "📦 使用 registry 映像檔"
    BASE_IMAGE="192.168.32.38:5000/podwise-rag-pipeline:latest"
fi

# 3. 創建修復後的容器
echo "🔨 創建修復後的容器..."
podman run -d \
    --name rag-pipeline-fixed \
    --network host \
    -v /home/bai/Desktop/Podwise/backend/rag_pipeline:/app \
    -v /home/bai/Desktop/Podwise/data:/app/data \
    -e PYTHONPATH=/app \
    -e CUDA_VISIBLE_DEVICES=0 \
    -e OLLAMA_HOST=http://192.168.32.38:11434 \
    -e TTS_HOST=http://192.168.32.38:8002 \
    -e MILVUS_HOST=192.168.32.86 \
    -e MILVUS_PORT=19530 \
    $BASE_IMAGE \
    /bin/bash -c "
        echo '📦 安裝缺少的依賴...' &&
        pip install --no-cache-dir crewai>=0.11.0 &&
        echo '🚀 啟動 RAG Pipeline...' &&
        python -m uvicorn app.main_integrated:app --host 0.0.0.0 --port 8004
    "

# 4. 等待容器啟動
echo "⏳ 等待容器啟動..."
sleep 30

# 5. 檢查容器狀態
echo "📊 檢查容器狀態..."
podman ps | grep rag-pipeline

# 6. 檢查容器日誌
echo "📝 檢查容器日誌..."
podman logs rag-pipeline-fixed --tail=20

# 7. 測試健康檢查
echo "🏥 測試健康檢查..."
sleep 10
curl -f http://localhost:8004/health || echo "❌ 健康檢查失敗"

echo "✅ RAG Pipeline 修復完成！"
echo "📋 管理指令："
echo "查看日誌: podman logs rag-pipeline-fixed -f"
echo "停止容器: podman stop rag-pipeline-fixed"
echo "重啟容器: podman restart rag-pipeline-fixed" 