# API 服務 Dockerfile
# 主要 API 閘道，整合所有後端服務
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（編譯器、curl、API 服務優化）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建 API 相關目錄
RUN mkdir -p /app/logs \
    /app/cache \
    /app/config \
    /app/templates

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOGS_DIR=/app/logs
ENV CACHE_DIR=/app/cache
ENV CONFIG_DIR=/app/config

# 暴露 API 服務埠（8000）
EXPOSE 8000

# 啟動指令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 