#!/bin/bash
# 建立最小 RAG Pipeline 開發容器
# Author: Podwise AI 助理

# 先移除舊容器
podman stop rag-pipeline-minimal 2>/dev/null || true
podman rm rag-pipeline-minimal 2>/dev/null || true

# 啟動最小 Python 容器，掛載程式碼目錄
podman run -itd \
  --name rag-pipeline-minimal \
  --network host \
  -v /home/bai/Desktop/Podwise/backend/rag_pipeline:/app \
  -w /app \
  python:3.11-slim \
  bash

echo "✅ 最小容器已啟動，可用以下指令進入："
echo "podman exec -it rag-pipeline-minimal bash" 