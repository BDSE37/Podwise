#!/bin/bash

# Podwise API 閘道服務啟動腳本

echo "🚀 啟動 Podwise API 閘道服務..."

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "📦 創建虛擬環境..."
    python3 -m venv .venv
fi

# 啟動虛擬環境
echo "🔧 啟動虛擬環境..."
source .venv/bin/activate

# 安裝依賴
echo "📥 安裝依賴套件..."
pip install -r requirements.txt

# 設定環境變數
export STT_SERVICE_URL=${STT_SERVICE_URL:-"http://localhost:8001"}
export TTS_SERVICE_URL=${TTS_SERVICE_URL:-"http://localhost:8003"}
export LLM_SERVICE_URL=${LLM_SERVICE_URL:-"http://localhost:8000"}
export RAG_SERVICE_URL=${RAG_SERVICE_URL:-"http://localhost:8011"}
export ML_SERVICE_URL=${ML_SERVICE_URL:-"http://localhost:8004"}
export CONFIG_SERVICE_URL=${CONFIG_SERVICE_URL:-"http://localhost:8008"}

echo "🌐 服務配置:"
echo "  STT: $STT_SERVICE_URL"
echo "  TTS: $TTS_SERVICE_URL"
echo "  LLM: $LLM_SERVICE_URL"
echo "  RAG: $RAG_SERVICE_URL"
echo "  ML: $ML_SERVICE_URL"
echo "  Config: $CONFIG_SERVICE_URL"

# 啟動服務
echo "🎯 啟動 API 閘道服務 (端口 8006)..."
echo "📖 API 文檔: http://localhost:8006/docs"
echo "🔍 健康檢查: http://localhost:8006/health"

uvicorn main:app --host 0.0.0.0 --port 8006 --reload 