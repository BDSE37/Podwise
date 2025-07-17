#!/bin/bash

# Podwise 統一 API Gateway 啟動腳本

echo "🚀 啟動 Podwise 統一 API Gateway..."

# 檢查 Python 版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ 需要 Python 3.8 或更高版本，當前版本: $python_version"
    exit 1
fi

# 檢查必要目錄
FRONTEND_PATH="../frontend/home"
IMAGES_PATH="$FRONTEND_PATH/images"
ASSETS_PATH="$FRONTEND_PATH/assets"

if [ ! -d "$FRONTEND_PATH" ]; then
    echo "❌ 前端目錄不存在: $FRONTEND_PATH"
    exit 1
fi

if [ ! -d "$IMAGES_PATH" ]; then
    echo "❌ 圖片目錄不存在: $IMAGES_PATH"
    exit 1
fi

if [ ! -d "$ASSETS_PATH" ]; then
    echo "❌ 資源目錄不存在: $ASSETS_PATH"
    exit 1
fi

echo "✅ 目錄檢查通過"

# 檢查依賴
echo "📦 檢查依賴..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📥 安裝依賴..."
    pip3 install -r requirements_unified_api.txt
fi

# 設定環境變數
export TTS_SERVICE_URL=${TTS_SERVICE_URL:-"http://localhost:8001"}
export STT_SERVICE_URL=${STT_SERVICE_URL:-"http://localhost:8002"}
export RAG_PIPELINE_URL=${RAG_PIPELINE_URL:-"http://localhost:8003"}
export ML_PIPELINE_URL=${ML_PIPELINE_URL:-"http://localhost:8004"}
export LLM_SERVICE_URL=${LLM_SERVICE_URL:-"http://localhost:8005"}

echo "🔧 服務配置:"
echo "  TTS: $TTS_SERVICE_URL"
echo "  STT: $STT_SERVICE_URL"
echo "  RAG Pipeline: $RAG_PIPELINE_URL"
echo "  ML Pipeline: $ML_PIPELINE_URL"
echo "  LLM: $LLM_SERVICE_URL"

# 啟動服務
echo "🌐 啟動服務在 http://localhost:8008"
echo "📚 API 文檔: http://localhost:8008/docs"
echo "📖 ReDoc: http://localhost:8008/redoc"
echo ""
echo "按 Ctrl+C 停止服務"
echo ""

python3 unified_api_gateway.py 