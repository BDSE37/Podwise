# LLM 統一服務 Dockerfile
# 使用 Python 3.10 精簡映像，適合 LLM 與向量服務
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴
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

# 創建模型目錄
RUN mkdir -p /app/models/Qwen2.5-Taiwan-7B-Instruct \
    /app/models/Qwen3-8B \
    /app/logs

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=http://ollama:11434
ENV LOG_LEVEL=INFO

# 暴露 API 服務埠
EXPOSE 8004

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 啟動指令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"] 