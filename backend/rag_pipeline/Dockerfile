# RAG Pipeline 服務 Dockerfile
# 檢索增強生成系統，整合向量檢索與 LLM
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（編譯器、curl、向量運算優化）
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

# 創建 RAG 相關目錄
RUN mkdir -p /app/data/documents \
    /app/data/embeddings \
    /app/models/embeddings \
    /app/cache \
    /app/logs

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV CACHE_DIR=/app/cache
ENV LOGS_DIR=/app/logs

# 暴露 API 服務埠（8004）
EXPOSE 8004

# 啟動指令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"] 