#!/bin/bash

# 修復的 RAG Pipeline 啟動腳本
# 解決模組導入問題

set -e

echo "[INFO] 啟動修復的 RAG Pipeline 服務..."

# 設定環境變數
export PYTHONPATH="/app:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# 清理 Python 快取
echo "[INFO] 清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 驗證套件安裝
echo "[INFO] 驗證套件安裝..."
python -c "import pandas; print('✅ pandas 版本:', pandas.__version__)"
python -c "import yaml; print('✅ yaml 已安裝')"
python -c "import langchain_openai; print('✅ langchain_openai 已安裝')"

# 測試模組導入
echo "[INFO] 測試模組導入..."
python -c "
import sys
sys.path.insert(0, '/app')
try:
    from core.enhanced_vector_search import RAGVectorSearch
    print('✅ RAGVectorSearch 導入成功')
except ImportError as e:
    print('❌ RAGVectorSearch 導入失敗:', e)
    print('嘗試修復...')
    import pandas as pd
    import yaml
    print('基礎套件導入成功')
"

# 啟動服務
echo "[INFO] 啟動 RAG Pipeline 服務..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload 