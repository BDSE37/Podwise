#!/bin/bash

# Backend 服務啟動腳本
# 啟動所有 backend 模組的 Podman 容器

echo🚀 開始啟動 Backend 服務..."

# 檢查是否已有容器在運行
echo📋 檢查現有容器狀態...podman ps

# 停止並移除舊容器（如果存在）
echo🧹 清理舊容器..."
podman stop podwise-api podwise-stt podwise-tts podwise-rag podwise-vector podwise-user 2>/dev/null || true
podman rm podwise-api podwise-stt podwise-tts podwise-rag podwise-vector podwise-user 2>/dev/null || true

# 構建映像（如果需要）
echo "🔨 構建 Docker 映像..."

# API Gateway
echo 構建 API Gateway 映像..."
cd backend/api
podman build -t podwise-api:latest .
cd ../..

# STT 服務
echo構建 STT 服務映像..."
cd backend/stt
podman build -t podwise-stt:latest .
cd ../..

# TTS 服務
echo構建 TTS 服務映像..."
cd backend/tts
podman build -t podwise-tts:latest .
cd ../..

# RAG Pipeline
echo構建 RAG Pipeline 映像...
cd backend/rag_pipeline
podman build -t podwise-rag:latest .
cd ../..

# ML Pipeline (如果還沒構建)
echo 構建 ML Pipeline 映像..."
cd backend/ml_pipeline
podman build -t podwise-ml:latest .
cd ../..

# LLM 服務 (如果還沒構建)
echo構建 LLM 服務映像..."
cd backend/llm
podman build -t podwise-llm:latest .
cd ../..

# 啟動容器
echo "🚀 啟動容器...
# API Gateway (端口 8005ho "啟動 API Gateway...
podman run -d --name podwise-api \
  -p 805:85
  -v $(pwd)/frontend/home:/app/frontend/home:ro \
  --network podman \
  podwise-api:latest

# STT 服務 (端口 801ho 啟動 STT 服務...
podman run -d --name podwise-stt \
  -p 801:81\
  -v $(pwd)/data:/app/data \
  --network podman \
  podwise-stt:latest

# TTS 服務 (端口 802ho 啟動 TTS 服務...
podman run -d --name podwise-tts \
  -p 802:82\
  -v $(pwd)/data:/app/data \
  --network podman \
  podwise-tts:latest

# RAG Pipeline (端口 8006o "啟動 RAG Pipeline...
podman run -d --name podwise-rag \
  -p 806:86\
  -v $(pwd)/data:/app/data \
  --network podman \
  -e OLLAMA_HOST=http://podwise-ollama:11434 \
  -e REDIS_HOST=podwise-redis \
  podwise-rag:latest

# Vector Pipeline (端口 87 - 如果沒有 Dockerfile，用 Python 直接運行
echo "啟動 Vector Pipeline..."
cd backend/vector_pipeline
podman run -d --name podwise-vector \
  -p 807:807\
  -v $(pwd):/app \
  -v $(pwd)/../data:/app/data \
  --network podman \
  -w /app \
  python:310slim \
  bash -c "pip install -r requirements.txt && python main.py
cd ../..
# User Management (端口 88啟動 User Management...
cd backend/user_management
podman run -d --name podwise-user \
  -p 808:808\
  -v $(pwd):/app \
  --network podman \
  -w /app \
  python:310slim \
  bash -c "pip install -r requirements.txt && python main.pycd ../..

# 等待服務啟動
echo "⏳ 等待服務啟動...sleep10
# 檢查服務狀態
echo 📊 檢查服務狀態..."
podman ps

# 檢查端口
echo🔍 檢查端口使用情況..."
netstat -tlnp | grep -E :(801802803804805607808)" || echo端口檢查完成

echo ✅ Backend 服務啟動完成！
echo echo📋 服務端口對應："
echo  - API Gateway: http://localhost:805
echo - STT 服務: http://localhost:801
echo - TTS 服務: http://localhost:8002o  - ML Pipeline: http://localhost:803
echo - LLM 服務: http://localhost:84   -RAG Pipeline: http://localhost:8006
echo  - Vector Pipeline: http://localhost:807 - User Management: http://localhost:88
echo - Ollama: http://localhost:11434
echo- Redis: localhost:6379" 