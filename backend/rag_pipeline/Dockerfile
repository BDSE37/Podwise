# RAG Pipeline 完整環境 Dockerfile
# 使用 Podman build，包含完整開發環境
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝完整系統依賴和開發工具
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    zip \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 開發工具
RUN pip install --upgrade pip setuptools wheel

# 複製完整的 requirements.txt
COPY requirements-complete.txt requirements.txt

# 安裝所有 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Python 開發工具
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    pytest \
    pytest-cov \
    black \
    flake8 \
    isort \
    mypy \
    pre-commit

# 複製應用程式碼
COPY . .

# 複製環境變數檔案
COPY env.local .env

# 創建必要目錄
RUN mkdir -p /app/data/documents \
    /app/data/embeddings \
    /app/models/embeddings \
    /app/cache \
    /app/logs \
    /app/temp \
    /app/scripts \
    /app/tests

# 複製安裝腳本
COPY install-additional-packages.sh /app/
COPY install-rag-packages.sh /app/
RUN chmod +x /app/install-additional-packages.sh
RUN chmod +x /app/install-rag-packages.sh

# 複製啟動腳本
COPY start-simple.sh /app/
RUN chmod +x /app/start-simple.sh

# 創建便捷的開發腳本
RUN echo '#!/bin/bash\n\
echo "🔧 RAG Pipeline 開發環境"\n\
echo "可用命令:"\n\
echo "  pip install <package>  - 安裝 Python 套件"\n\
echo "  apt-get update && apt-get install <package>  - 安裝系統套件"\n\
echo "  python -m ipython  - 啟動 IPython"\n\
echo "  python -m pytest  - 執行測試"\n\
echo "  black .  - 格式化程式碼"\n\
echo "  flake8 .  - 檢查程式碼風格"\n\
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload  - 啟動服務"\n\
echo ""\n\
exec "$@"' > /app/dev-entrypoint.sh && chmod +x /app/dev-entrypoint.sh

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV CACHE_DIR=/app/cache
ENV LOGS_DIR=/app/logs
ENV TEMP_DIR=/app/temp
ENV DEBIAN_FRONTEND=noninteractive

# 暴露 API 服務埠
EXPOSE 8010

# 設定預設啟動指令
CMD ["/app/start-simple.sh"] 