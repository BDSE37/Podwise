#!/bin/bash

# Stage4 Embedding Prep 資料插入 Milvus 執行腳本

echo "=========================================="
echo "Stage4 Embedding Prep 資料插入 Milvus"
echo "=========================================="

# 設定環境變數
export MILVUS_HOST="192.168.32.86"
export MILVUS_PORT="19530"
export MILVUS_COLLECTION="podcast_chunks"

echo "Milvus 配置:"
echo "  Host: $MILVUS_HOST"
echo "  Port: $MILVUS_PORT"
echo "  Collection: $MILVUS_COLLECTION"
echo ""

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 找不到 python3"
    exit 1
fi

# 切換到腳本目錄
cd "$(dirname "$0")"

# 檢查必要檔案
if [ ! -f "scripts/insert_stage4_to_milvus.py" ]; then
    echo "錯誤: 找不到 insert_stage4_to_milvus.py 腳本"
    exit 1
fi

# 檢查 stage4 資料目錄
if [ ! -d "data/stage4_embedding_prep" ]; then
    echo "錯誤: 找不到 stage4_embedding_prep 資料目錄"
    exit 1
fi

echo "開始執行資料插入..."
echo "開始時間: $(date)"
echo ""

# 執行 Python 腳本
python3 scripts/insert_stage4_to_milvus.py

echo ""
echo "結束時間: $(date)"
echo "=========================================="
echo "執行完成！"
echo "請檢查 logs 目錄中的日誌檔案"
echo "==========================================" 