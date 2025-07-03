# LLM 服務 Dockerfile
# 使用 Python 3.10 精簡映像，適合 LLM 與向量服務
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（如編譯器、curl）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建模型目錄（如需外部模型）
RUN mkdir -p /app/models/external/qwen \
    /app/models/external/bge-m3 \
    /app/models/external/deepseek

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露 API 服務埠（8003）
EXPOSE 8003

# 啟動指令
CMD ["python", "main.py"] 