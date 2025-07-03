#!/bin/bash

# Podwise Frontend 啟動腳本
# 使用 FastAPI 作為反向代理

echo "🚀 啟動 Podwise Frontend 服務..."

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，請先安裝 Python3"
    exit 1
fi

# 檢查是否在虛擬環境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建議在虛擬環境中運行"
    echo "   可以使用: python3 -m venv venv && source venv/bin/activate"
fi

# 安裝依賴
echo "📦 安裝依賴..."
pip install -r requirements.txt

# 檢查 Streamlit 是否可用
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit 未安裝，Podri 聊天功能可能無法正常使用"
    echo "   可以使用: pip install streamlit"
fi

# 啟動 FastAPI 應用程式
echo "🌐 啟動 FastAPI 服務..."
echo "   首頁: http://localhost:8000"
echo "   Podri 聊天: http://localhost:8000/podri"
echo "   API 文檔: http://localhost:8000/docs"
echo "   健康檢查: http://localhost:8000/health"

python3 main.py 