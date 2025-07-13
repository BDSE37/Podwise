#!/bin/bash

# Podwise TTS 整合功能啟動腳本
# 作者: Podwise Team
# 版本: 1.0.0

echo "🚀 啟動 Podwise TTS 整合功能..."
echo "=================================="

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，請先安裝 Python3"
    exit 1
fi

# 檢查必要目錄
if [ ! -d "backend/rag_pipeline" ]; then
    echo "❌ 找不到 backend/rag_pipeline 目錄"
    exit 1
fi

if [ ! -d "backend/tts" ]; then
    echo "❌ 找不到 backend/tts 目錄"
    exit 1
fi

# 設置環境變數
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
export RAG_PIPELINE_PORT=8005
export TTS_SERVICE_PORT=8003
export FRONTEND_PORT=8080

echo "📋 環境配置："
echo "   RAG Pipeline 端口: $RAG_PIPELINE_PORT"
echo "   TTS Service 端口: $TTS_SERVICE_PORT"
echo "   前端服務端口: $FRONTEND_PORT"
echo ""

# 檢查服務是否已在運行
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  $service_name 已在端口 $port 運行"
        return 0
    else
        return 1
    fi
}

# 啟動 TTS 服務
start_tts_service() {
    echo "🎵 啟動 TTS 服務..."
    
    if check_port $TTS_SERVICE_PORT "TTS Service"; then
        echo "   TTS 服務已在運行"
    else
        cd backend/tts
        echo "   啟動 TTS 服務在端口 $TTS_SERVICE_PORT..."
        python3 main.py &
        TTS_PID=$!
        echo "   TTS 服務已啟動 (PID: $TTS_PID)"
        cd ../..
        
        # 等待服務啟動
        sleep 3
    fi
}

# 啟動 RAG Pipeline 服務
start_rag_pipeline() {
    echo "🧠 啟動 RAG Pipeline 服務..."
    
    if check_port $RAG_PIPELINE_PORT "RAG Pipeline"; then
        echo "   RAG Pipeline 已在運行"
    else
        cd backend/rag_pipeline
        echo "   啟動 RAG Pipeline 在端口 $RAG_PIPELINE_PORT..."
        python3 main.py &
        RAG_PID=$!
        echo "   RAG Pipeline 已啟動 (PID: $RAG_PID)"
        cd ../..
        
        # 等待服務啟動
        sleep 5
    fi
}

# 啟動前端服務
start_frontend() {
    echo "🌐 啟動前端服務..."
    
    if check_port $FRONTEND_PORT "Frontend"; then
        echo "   前端服務已在運行"
    else
        cd frontend/home
        echo "   啟動前端服務在端口 $FRONTEND_PORT..."
        python3 fastapi_app.py &
        FRONTEND_PID=$!
        echo "   前端服務已啟動 (PID: $FRONTEND_PID)"
        cd ../..
        
        # 等待服務啟動
        sleep 2
    fi
}

# 健康檢查
health_check() {
    echo ""
    echo "🏥 執行健康檢查..."
    
    # 檢查 TTS 服務
    if curl -s http://localhost:$TTS_SERVICE_PORT/health > /dev/null 2>&1; then
        echo "✅ TTS 服務健康檢查通過"
    else
        echo "❌ TTS 服務健康檢查失敗"
    fi
    
    # 檢查 RAG Pipeline 服務
    if curl -s http://localhost:$RAG_PIPELINE_PORT/health > /dev/null 2>&1; then
        echo "✅ RAG Pipeline 服務健康檢查通過"
    else
        echo "❌ RAG Pipeline 服務健康檢查失敗"
    fi
    
    # 檢查前端服務
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo "✅ 前端服務健康檢查通過"
    else
        echo "❌ 前端服務健康檢查失敗"
    fi
}

# 顯示服務狀態
show_status() {
    echo ""
    echo "📊 服務狀態："
    echo "   TTS Service:      http://localhost:$TTS_SERVICE_PORT"
    echo "   RAG Pipeline:     http://localhost:$RAG_PIPELINE_PORT"
    echo "   Frontend:         http://localhost:$FRONTEND_PORT"
    echo "   Podri Chat:       http://localhost:$FRONTEND_PORT/podri.html"
    echo ""
    echo "📚 API 文檔："
    echo "   TTS API:          http://localhost:$TTS_SERVICE_PORT/docs"
    echo "   RAG Pipeline API: http://localhost:$RAG_PIPELINE_PORT/docs"
    echo ""
    echo "🎯 快速測試："
    echo "   curl -X GET http://localhost:$RAG_PIPELINE_PORT/api/v1/tts/voices"
    echo ""
}

# 清理函數
cleanup() {
    echo ""
    echo "🛑 正在停止服務..."
    
    if [ ! -z "$TTS_PID" ]; then
        kill $TTS_PID 2>/dev/null
        echo "   已停止 TTS 服務"
    fi
    
    if [ ! -z "$RAG_PID" ]; then
        kill $RAG_PID 2>/dev/null
        echo "   已停止 RAG Pipeline 服務"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   已停止前端服務"
    fi
    
    echo "✅ 所有服務已停止"
}

# 設置信號處理
trap cleanup SIGINT SIGTERM

# 主執行流程
main() {
    # 啟動所有服務
    start_tts_service
    start_rag_pipeline
    start_frontend
    
    # 健康檢查
    health_check
    
    # 顯示狀態
    show_status
    
    echo "🎉 Podwise TTS 整合功能啟動完成！"
    echo "   按 Ctrl+C 停止所有服務"
    echo ""
    
    # 保持腳本運行
    while true; do
        sleep 10
    done
}

# 檢查參數
case "${1:-}" in
    "stop")
        cleanup
        exit 0
        ;;
    "status")
        show_status
        exit 0
        ;;
    "test")
        echo "🧪 運行 TTS 整合測試..."
        cd backend/rag_pipeline
        python3 test_tts_integration.py
        cd ../..
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "使用方法: $0 [命令]"
        echo ""
        echo "命令："
        echo "  start   啟動所有服務 (預設)"
        echo "  stop    停止所有服務"
        echo "  status  顯示服務狀態"
        echo "  test    運行 TTS 整合測試"
        echo "  help    顯示此幫助訊息"
        echo ""
        echo "範例："
        echo "  $0 start    # 啟動所有服務"
        echo "  $0 test     # 運行測試"
        echo "  $0 status   # 檢查狀態"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "   使用 '$0 help' 查看可用命令"
        exit 1
        ;;
esac 