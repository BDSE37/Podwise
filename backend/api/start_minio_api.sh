#!/bin/bash

# 啟動 MinIO 推薦 API 服務
echo "啟動 MinIO 推薦 API 服務..."

# 安裝依賴
pip install -r requirements_minio.txt

# 設置環境變數
export MINIO_ENDPOINT=${MINIO_ENDPOINT:-"localhost:9000"}
export MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-"minioadmin"}
export MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-"minioadmin"}
export MINIO_BUCKET=${MINIO_BUCKET:-"podwise"}

# 啟動服務
python minio_recommendations.py 