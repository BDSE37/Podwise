# TTS 服務 Dockerfile
# 文字轉語音服務，整合 GPT-SoVITS 與多種 TTS 模型
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（音訊處理、編譯器、curl、CUDA 支援）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建 TTS 相關目錄
RUN mkdir -p /app/models/tts \
    /app/audio/input \
    /app/audio/output \
    /app/GPT-SoVITS \
    /app/training_data \
    /app/raw \
    /app/logs \
    /app/cache \
    /app/GPT_weights \
    /app/SoVITS_weights

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV AUDIO_INPUT_DIR=/app/audio/input
ENV AUDIO_OUTPUT_DIR=/app/audio/output
ENV GPT_SOVITS_DIR=/app/GPT-SoVITS

# 暴露多個服務埠
EXPOSE 8002 8003 7860 7861 9880

# 啟動指令（支援多種 TTS 服務）
CMD ["python", "main.py"] 