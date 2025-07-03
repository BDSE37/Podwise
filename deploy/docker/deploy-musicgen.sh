#!/bin/bash

# MusicGen 服務部署腳本
# 整合 MusicGen 音樂生成功能到 Podri 聊天系統

set -e

echo "🎵 開始部署 MusicGen 音樂生成服務..."

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查是否有 GPU 支援
if command -v nvidia-smi &> /dev/null; then
    echo "✅ 檢測到 NVIDIA GPU"
    export CUDA_AVAILABLE=true
else
    echo "⚠️  未檢測到 NVIDIA GPU，將使用 CPU 模式"
    export CUDA_AVAILABLE=false
fi

# 建立必要的目錄
echo "📁 建立必要目錄..."
mkdir -p ../../backend/musicgen/cache
mkdir -p ../../backend/musicgen/output
mkdir -p ../../frontend/chat/data

# 設定環境變數
echo "🔧 設定環境變數..."
export OPENAI_API_KEY=${OPENAI_API_KEY:-}
export GOOGLE_SEARCH_API_KEY=${GOOGLE_SEARCH_API_KEY:-}
export GEMINI_API_KEY=${GEMINI_API_KEY:-}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# 建立 Docker 網路（如果不存在）
echo "🌐 建立 Docker 網路..."
docker network create podwise-network 2>/dev/null || echo "網路已存在"

# 停止現有服務
echo "🛑 停止現有服務..."
docker-compose -f docker-compose-musicgen.yml down 2>/dev/null || true

# 建立並啟動服務
echo "🚀 建立並啟動服務..."
if [ "$CUDA_AVAILABLE" = true ]; then
    echo "使用 GPU 模式部署"
    docker-compose -f docker-compose-musicgen.yml up -d --build
else
    echo "使用 CPU 模式部署"
    # 移除 GPU 相關配置
    sed '/driver: nvidia/,/capabilities: \[gpu\]/d' docker-compose-musicgen.yml > docker-compose-musicgen-cpu.yml
    docker-compose -f docker-compose-musicgen-cpu.yml up -d --build
fi

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose -f docker-compose-musicgen.yml ps

# 測試 MusicGen 服務
echo "🧪 測試 MusicGen 服務..."
if curl -f http://localhost:8005/health > /dev/null 2>&1; then
    echo "✅ MusicGen 服務運行正常"
else
    echo "❌ MusicGen 服務啟動失敗"
    docker-compose -f docker-compose-musicgen.yml logs musicgen
    exit 1
fi

# 測試聊天服務
echo "🧪 測試聊天服務..."
if curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ 聊天服務運行正常"
else
    echo "❌ 聊天服務啟動失敗"
    docker-compose -f docker-compose-musicgen.yml logs podri-chat
    exit 1
fi

echo ""
echo "🎉 MusicGen 服務部署完成！"
echo ""
echo "📋 服務資訊："
echo "  🎵 MusicGen 服務: http://localhost:8005"
echo "  💬 聊天介面: http://localhost:8501"
echo ""
echo "🔧 功能特色："
echo "  ✅ API Key 管理（OpenAI、Google、Gemini、Anthropic）"
echo "  ✅ 智能 API 選擇"
echo "  ✅ MusicGen 音樂生成"
echo "  ✅ 多種音樂風格和節奏"
echo ""
echo "📖 使用說明："
echo "  1. 開啟 http://localhost:8501"
echo "  2. 在側邊欄設定 API Keys"
echo "  3. 啟用音樂生成功能"
echo "  4. 選擇音樂風格和節奏"
echo "  5. 點擊生成背景音樂"
echo ""
echo "🛠️  管理命令："
echo "  查看日誌: docker-compose -f docker-compose-musicgen.yml logs -f"
echo "  停止服務: docker-compose -f docker-compose-musicgen.yml down"
echo "  重啟服務: docker-compose -f docker-compose-musicgen.yml restart"
echo "" 