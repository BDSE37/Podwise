#!/bin/bash

# PodWise 服務狀態檢查腳本

echo "📊 PodWise 服務狀態檢查"
echo "=========================="

# 檢查後端服務
echo "🔧 後端服務 (8007):"
if curl -s http://localhost:8007/api/health > /dev/null; then
    echo "  ✅ 運行中"
    BACKEND_STATUS=$(curl -s http://localhost:8007/api/health | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "  📋 狀態: $BACKEND_STATUS"
else
    echo "  ❌ 已停止"
fi

echo ""

echo "🎵 音檔流服務 (8006):"
if curl -s http://localhost:8006/health > /dev/null; then
    echo "  ✅ 運行中"
    AUDIO_STATUS=$(curl -s http://localhost:8006/health | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "  📋 狀態: $AUDIO_STATUS"
else
    echo "  ❌ 已停止"
fi

echo ""

# 檢查前端服務
echo "🎨 前端服務 (8080):"
if curl -s http://localhost:8080/health > /dev/null; then
    echo "  ✅ 運行中"
    FRONTEND_STATUS=$(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo "unknown")
    echo "  📋 狀態: $FRONTEND_STATUS"
else
    echo "  ❌ 已停止"
fi

echo ""

# 檢查進程
echo "🔍 進程檢查:"
BACKEND_PID=$(pgrep -f feedback_service.py)
AUDIO_PID=$(pgrep -f audio_stream_service.py)
FRONTEND_PID=$(pgrep -f fastapi_app.py)

if [ ! -z "$BACKEND_PID" ]; then
    echo "  🔧 後端進程 PID: $BACKEND_PID"
else
    echo "  🔧 後端進程: 未找到"
fi

if [ ! -z "$AUDIO_PID" ]; then
    echo "  🎵 音檔流進程 PID: $AUDIO_PID"
else
    echo "  🎵 音檔流進程: 未找到"
fi

if [ ! -z "$FRONTEND_PID" ]; then
    echo "  🎨 前端進程 PID: $FRONTEND_PID"
else
    echo "  🎨 前端進程: 未找到"
fi

echo ""

# 檢查端口
echo "🌐 端口檢查:"
if netstat -tlnp 2>/dev/null | grep ":8007 " > /dev/null; then
    echo "  ✅ 8007 端口: 監聽中"
else
    echo "  ❌ 8007 端口: 未監聽"
fi

if netstat -tlnp 2>/dev/null | grep ":8006 " > /dev/null; then
    echo "  ✅ 8006 端口: 監聽中"
else
    echo "  ❌ 8006 端口: 未監聽"
fi

if netstat -tlnp 2>/dev/null | grep ":8080 " > /dev/null; then
    echo "  ✅ 8080 端口: 監聽中"
else
    echo "  ❌ 8080 端口: 未監聽"
fi

echo ""
echo "🔗 訪問地址:"
echo "  前端網站: http://localhost:8080"
echo "  後端 API: http://localhost:8007"
echo ""
echo "📝 管理命令:"
echo "  啟動服務: ./start_services.sh"
echo "  停止服務: ./stop_services.sh"
echo "  檢查狀態: ./check_status.sh" 