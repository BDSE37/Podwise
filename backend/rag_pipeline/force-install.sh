#!/bin/bash

# 強制安裝所有 RAG Pipeline 套件
# 解決套件安裝問題

set -e

echo "[INFO] 開始強制安裝 RAG Pipeline 套件..."

# 停止可能運行的服務
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

# 清理 Python 快取
echo "[INFO] 清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 更新 pip
echo "[INFO] 更新 pip..."
pip install --upgrade pip

# 強制重新安裝核心套件
echo "[INFO] 強制安裝核心套件..."
pip install --force-reinstall --no-cache-dir fastapi uvicorn python-multipart

# 強制重新安裝資料處理套件
echo "[INFO] 強制安裝資料處理套件..."
pip install --force-reinstall --no-cache-dir pandas numpy scikit-learn

# 強制重新安裝向量搜尋套件
echo "[INFO] 強制安裝向量搜尋套件..."
pip install --force-reinstall --no-cache-dir pymilvus

# 強制重新安裝 NLP 套件
echo "[INFO] 強制安裝 NLP 套件..."
pip install --force-reinstall --no-cache-dir transformers torch sentence-transformers

# 強制重新安裝 CrewAI 套件
echo "[INFO] 強制安裝 CrewAI 套件..."
pip install --force-reinstall --no-cache-dir crewai langchain langchain-community

# 強制重新安裝資料庫套件
echo "[INFO] 強制安裝資料庫套件..."
pip install --force-reinstall --no-cache-dir psycopg2-binary sqlalchemy

# 強制重新安裝工具套件
echo "[INFO] 強制安裝工具套件..."
pip install --force-reinstall --no-cache-dir requests python-dotenv pydantic

# 強制重新安裝其他套件
echo "[INFO] 強制安裝其他套件..."
pip install --force-reinstall --no-cache-dir pyyaml tqdm click rich typer toml

# 驗證安裝
echo "[INFO] 驗證套件安裝..."
python -c "import pandas; print('✅ pandas 版本:', pandas.__version__)"
python -c "import numpy; print('✅ numpy 已安裝')"
python -c "import transformers; print('✅ transformers 已安裝')"
python -c "import crewai; print('✅ crewai 已安裝')"
python -c "import pymilvus; print('✅ pymilvus 已安裝')"
python -c "import yaml; print('✅ pyyaml 已安裝')"

echo "[SUCCESS] 所有套件強制安裝完成！"
echo "[INFO] 現在可以啟動 RAG Pipeline 服務："
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload" 