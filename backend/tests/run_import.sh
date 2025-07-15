#!/bin/bash

# Podwise 測試資料匯入腳本

echo "🚀 開始執行 Podwise 測試資料匯入..."

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝"
    exit 1
fi

# 檢查是否在正確的目錄
if [ ! -f "data_importer.py" ]; then
    echo "❌ 請在 testdata 目錄下執行此腳本"
    exit 1
fi

# 安裝依賴套件
echo "📦 安裝依賴套件..."
pip3 install -r requirements.txt

# 檢查資料庫連線
echo "🔍 檢查資料庫連線..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        database='podcast',
        user='bdse37',
        password='111111'
    )
    conn.close()
    print('✅ 資料庫連線正常')
except Exception as e:
    print(f'❌ 資料庫連線失敗: {e}')
    exit(1)
"

# 執行資料匯入
echo "📊 開始匯入資料..."
python3 data_importer.py --data-dir .

echo "✅ 資料匯入完成！" 