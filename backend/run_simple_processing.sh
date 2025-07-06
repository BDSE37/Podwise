#!/bin/bash

# MongoDB Collection 處理執行腳本
# 處理長文本切分、標籤貼標和向量化

set -e

echo "=========================================="
echo "MongoDB Collection 處理管線"
echo "=========================================="

# 檢查 Python 環境
echo "檢查 Python 環境..."
python3 --version

# 檢查必要套件
echo "檢查必要套件..."
python3 -c "
import pymongo
import psycopg2
import sentence_transformers
import pymilvus
import pandas
import numpy
print('所有必要套件已安裝')
"

# 設定環境變數
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 建立日誌目錄
mkdir -p logs

# 執行處理
echo "開始執行 collection 處理..."
python3 process_collections_simple.py

echo "=========================================="
echo "處理完成！"
echo "=========================================="

# 顯示錯誤報告
if [ -f "error_report.json" ]; then
    echo "錯誤報告摘要："
    python3 -c "
import json
with open('error_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'總錯誤數: {len(data)}')
if data:
    collections = set(item['collection_name'] for item in data)
    print(f'受影響的 collections: {collections}')
    error_types = set(item['error_type'] for item in data)
    print(f'錯誤類型: {error_types}')
"
fi

echo "詳細日誌請查看: collection_processing.log"
echo "錯誤報告請查看: error_report.json" 