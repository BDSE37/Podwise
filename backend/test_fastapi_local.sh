#!/bin/bash

# Podwise FastAPI 反向代理本地測試腳本
# 純粹的 Python + FastAPI 測試，不依賴任何外部服務

echo "🧪 本地 FastAPI 反向代理測試..."

# 檢查 Python 版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "✅ Python 版本: $python_version"

# 檢查必要目錄
FRONTEND_PATH="../frontend"
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
    echo "📥 安裝 FastAPI 依賴..."
    pip3 install fastapi uvicorn httpx jinja2 python-multipart
fi

# 設定測試環境變數 (指向不存在的服務，測試錯誤處理)
export TTS_SERVICE_URL="http://localhost:9999"
export STT_SERVICE_URL="http://localhost:9998"
export RAG_PIPELINE_URL="http://localhost:9997"
export ML_PIPELINE_URL="http://localhost:9996"
export LLM_SERVICE_URL="http://localhost:9995"

echo "🔧 測試配置 (故意指向不存在的服務):"
echo "  TTS: $TTS_SERVICE_URL"
echo "  STT: $STT_SERVICE_URL"
echo "  RAG Pipeline: $RAG_PIPELINE_URL"
echo "  ML Pipeline: $ML_PIPELINE_URL"
echo "  LLM: $LLM_SERVICE_URL"

# 檢查端口
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # 端口被佔用
        else
            return 1  # 端口可用
        fi
    else
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            return 0  # 端口被佔用
        else
            return 1  # 端口可用
        fi
    fi
}

# 檢查 8008 端口
if check_port 8008; then
    echo "❌ 端口 8008 已被佔用，請先停止其他服務"
    echo "可以使用以下命令檢查："
    echo "  lsof -i :8008"
    echo "  netstat -tlnp | grep :8008"
    exit 1
fi

echo "✅ 端口 8008 可用"

# 啟動測試服務
echo ""
echo "🚀 啟動 FastAPI 反向代理測試服務..."
echo "🌐 訪問地址: http://localhost:8008"
echo "📚 API 文檔: http://localhost:8008/docs"
echo "🔍 健康檢查: http://localhost:8008/health"
echo ""
echo "🧪 測試項目："
echo "  1. 前端頁面載入"
echo "  2. 靜態檔案服務"
echo "  3. API 端點響應"
echo "  4. 錯誤處理機制"
echo ""
echo "按 Ctrl+C 停止測試服務"
echo ""

# 啟動 FastAPI 服務
python3 unified_api_gateway.py 