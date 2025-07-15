#!/bin/bash

# Podwise 四步驟功能演示啟動腳本

echo "🚀 啟動 Podwise 四步驟功能演示"
echo "=================================="

# 檢查 Python 環境
echo "📋 檢查 Python 環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，請先安裝 Python3"
    exit 1
fi

# 檢查必要的 Python 套件
echo "📦 檢查必要的 Python 套件..."
required_packages=("fastapi" "uvicorn" "psycopg2-binary" "minio" "requests")
for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        echo "⚠️  缺少套件: $package"
        echo "   請執行: pip install $package"
    fi
done

# 檢查環境變數
echo "🔧 檢查環境變數..."
if [ -z "$POSTGRES_HOST" ]; then
    export POSTGRES_HOST="192.168.32.56"
    echo "   設定 POSTGRES_HOST=$POSTGRES_HOST"
fi

if [ -z "$MINIO_ENDPOINT" ]; then
    export MINIO_ENDPOINT="192.168.32.66:30090"
    echo "   設定 MINIO_ENDPOINT=$MINIO_ENDPOINT"
fi

# 啟動後端 API 服務
echo "🔌 啟動後端 API 服務..."
cd backend/api

# 檢查是否已有服務在運行
if lsof -Pi :8008 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 8008 已被佔用，請先停止現有服務"
    echo "   可以使用以下命令停止:"
    echo "   pkill -f 'python.*app.py'"
    exit 1
fi

# 啟動服務
echo "   啟動 API 服務在端口 8008..."
python3 app.py &
API_PID=$!

# 等待服務啟動
echo "⏳ 等待 API 服務啟動..."
sleep 5

# 檢查服務是否成功啟動
if curl -s http://localhost:8008/health > /dev/null; then
    echo "✅ API 服務啟動成功"
else
    echo "❌ API 服務啟動失敗"
    kill $API_PID 2>/dev/null
    exit 1
fi

# 測試 API 端點
echo "🧪 測試 API 端點..."
cd ../..
if [ -f "backend/test_api_endpoints.py" ]; then
    python3 backend/test_api_endpoints.py
    if [ $? -eq 0 ]; then
        echo "✅ API 端點測試通過"
    else
        echo "⚠️  API 端點測試有問題，但服務仍在運行"
    fi
else
    echo "⚠️  找不到測試腳本，跳過 API 測試"
fi

# 顯示訪問信息
echo ""
echo "🎉 Podwise 四步驟功能已啟動！"
echo "=================================="
echo "📱 前端頁面: http://localhost:8080/home/index.html"
echo "🔌 API 文檔: http://localhost:8008/docs"
echo "🔌 API 健康檢查: http://localhost:8008/health"
echo ""
echo "📋 功能說明:"
echo "   Step 1: 選擇類別（商業/教育）"
echo "   Step 2: 獲取標籤（從 MinIO 隨機獲取 4 個標籤）"
echo "   Step 3: 節目推薦（根據標籤顯示 3 個節目）"
echo "   Step 4: 用戶註冊（輸入或生成 Podwise ID）"
echo ""
echo "🛑 停止服務: Ctrl+C 或執行 pkill -f 'python.*app.py'"
echo ""

# 等待用戶中斷
trap 'echo ""; echo "🛑 正在停止服務..."; kill $API_PID 2>/dev/null; echo "✅ 服務已停止"; exit 0' INT

# 保持腳本運行
wait $API_PID 