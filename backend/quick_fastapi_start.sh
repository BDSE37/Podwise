#!/bin/bash

# Podwise FastAPI 反向代理快速啟動腳本
# 簡化版本，專注於 FastAPI 反向代理功能

echo "🚀 啟動 Podwise FastAPI 反向代理..."

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
    echo "📥 安裝依賴..."
    pip3 install -r requirements_unified_api.txt
fi

# 設定環境變數
export TTS_SERVICE_URL=${TTS_SERVICE_URL:-"http://localhost:8002"}
export STT_SERVICE_URL=${STT_SERVICE_URL:-"http://localhost:8003"}
export RAG_PIPELINE_URL=${RAG_PIPELINE_URL:-"http://localhost:8005"}
export ML_PIPELINE_URL=${ML_PIPELINE_URL:-"http://localhost:8004"}
export LLM_SERVICE_URL=${LLM_SERVICE_URL:-"http://localhost:8006"}

echo "🔧 服務配置:"
echo "  TTS: $TTS_SERVICE_URL"
echo "  STT: $STT_SERVICE_URL"
echo "  RAG Pipeline: $RAG_PIPELINE_URL"
echo "  ML Pipeline: $ML_PIPELINE_URL"
echo "  LLM: $LLM_SERVICE_URL"

# 檢查端口是否被佔用
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

# 檢查其他服務是否運行
echo "🔍 檢查其他服務狀態..."
services=(
    "8002:TTS"
    "8003:STT"
    "8004:ML Pipeline"
    "8005:RAG Pipeline"
    "8006:LLM"
)

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    if check_port $port; then
        echo "  ✅ $name (端口: $port) - 運行中"
    else
        echo "  ⚠️  $name (端口: $port) - 未運行 (可選)"
    fi
done

# 啟動服務
echo ""
echo "🌐 啟動 FastAPI 反向代理在 http://localhost:8008"
echo "📚 API 文檔: http://localhost:8008/docs"
echo "📖 ReDoc: http://localhost:8008/redoc"
echo "🔍 健康檢查: http://localhost:8008/health"
echo ""
echo "💡 提示:"
echo "  - 如果其他服務未運行，FastAPI 反向代理仍會啟動"
echo "  - 但相關功能可能無法使用"
echo "  - 可以稍後單獨啟動其他服務"
echo ""
echo "按 Ctrl+C 停止服務"
echo ""

# 啟動 FastAPI 反向代理
python3 unified_api_gateway.py 