# RAG Pipeline Dockerfile
# 使用 Python 3.11 精簡映像，適合現代 AI 應用
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定 PYTHONPATH 環境變數
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 安裝必要系統依賴（如編譯器、curl）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt --timeout=600

# 複製應用程式碼
COPY . .

# 暴露 API 服務埠（8004）
EXPOSE 8004

# 設定環境變數（可依需求調整）
ENV OLLAMA_HOST=http://ollama:11434
ENV TTS_HOST=http://tts:8002
ENV MILVUS_HOST=192.168.32.86
ENV MILVUS_PORT=19530

# 啟動指令，使用 uvicorn 啟動 FastAPI 主程式
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"] 