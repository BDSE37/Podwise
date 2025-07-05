# ML Pipeline 服務 Dockerfile
# 機器學習管道，包含推薦系統與模型訓練
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（編譯器、curl、科學計算優化）
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

# 創建 ML 相關目錄
RUN mkdir -p /app/models/ml \
    /app/data/training \
    /app/data/validation \
    /app/data/testing \
    /app/cache \
    /app/logs \
    /app/experiments

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MODELS_DIR=/app/models/ml
ENV DATA_DIR=/app/data
ENV CACHE_DIR=/app/cache
ENV LOGS_DIR=/app/logs
ENV EXPERIMENTS_DIR=/app/experiments

# 暴露 API 服務埠（8004）
EXPOSE 8004

# 啟動指令
CMD ["python", "main.py"]
