#!/bin/bash

echo "🚀 啟動 Podwise RAG Pipeline (修復版)"
echo "=================================="

# 檢查是否在容器內
if [ -f /.dockerenv ]; then
    echo "📍 檢測到容器環境"
    cd /app/rag_pipeline
else
    echo "📍 檢測到主機環境"
    cd backend/rag_pipeline
fi

# 檢查 Python 環境
echo "🔍 檢查 Python 環境..."
python3 --version

# 檢查必要套件
echo "🔍 檢查必要套件..."
python3 -c "import fastapi, uvicorn, pydantic; print('✅ 基本套件可用')" 2>/dev/null || {
    echo "❌ 缺少基本套件，嘗試安裝..."
    pip3 install fastapi uvicorn pydantic
}

# 檢查修復版本檔案
if [ ! -f "start-fixed-original.py" ]; then
    echo "❌ 找不到修復版本檔案"
    exit 1
fi

echo "✅ 修復版本檔案存在"

# 設定環境變數
export PYTHONPATH="/app:/app/backend:$PYTHONPATH"

# 檢查端口
PORT=8010
echo "🔍 檢查端口 $PORT..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被佔用"
    # 尋找可用端口
    for p in 8011 8012 8013 8014 8015; do
        if ! lsof -Pi :$p -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT=$p
            echo "✅ 找到可用端口: $PORT"
            break
        fi
    done
else
    echo "✅ 端口 $PORT 可用"
fi

echo "🚀 啟動服務..."
echo "📍 服務地址: http://0.0.0.0:$PORT"
echo "📖 API 文檔: http://localhost:$PORT/docs"
echo "❤️  健康檢查: http://localhost:$PORT/health"

# 啟動服務
python3 start-fixed-original.py 