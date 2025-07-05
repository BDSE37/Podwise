# Podwise RAG Pipeline Dockerfile for K8s
# 支援 CrewAI + LangChain + LLM 備援機制

FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY backend/rag_pipeline/requirements.txt ./requirements.txt

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        pydantic==2.5.0 \
        pydantic-settings==2.1.0 \
        numpy==1.24.3 \
        scikit-learn==1.3.2 \
        pymongo==4.6.0 \
        python-multipart==0.0.6 \
        aiofiles==23.2.1 \
        python-dotenv==1.0.0 \
        langchain==0.1.0 \
        langchain-openai==0.0.5 \
        crewai==0.28.0

# 複製應用程式代碼
COPY backend/rag_pipeline ./backend/rag_pipeline
COPY backend/config ./backend/config
COPY backend/core ./backend/core
COPY backend/utils ./backend/utils

# 創建必要的目錄
RUN mkdir -p /app/data /app/models /app/cache /app/logs

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV DEBUG=false
ENV LOG_LEVEL=INFO

# 暴露端口
EXPOSE 8004

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 啟動命令
CMD ["python", "-m", "uvicorn", "backend.rag_pipeline.app.main_crewai:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "1"] 