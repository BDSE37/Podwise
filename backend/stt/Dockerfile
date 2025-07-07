# STT 服務 Dockerfile
# 語音轉文字服務，支援多種音訊格式處理
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（音訊處理、編譯器、curl）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建音訊處理目錄
RUN mkdir -p /app/audio/input \
    /app/audio/output \
    /app/models/stt

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV AUDIO_INPUT_DIR=/app/audio/input
ENV AUDIO_OUTPUT_DIR=/app/audio/output

# 暴露 API 服務埠（8001）
EXPOSE 8001

# 啟動指令
CMD ["python", "main.py"] 