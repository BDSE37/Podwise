# 整合 TTS 服務 Dockerfile
# 包含 Edge TTS、GPT-SoVITS 和 Web UI 功能

# 使用 Python 基礎映像
FROM docker.io/python:3.9-slim

# 設定環境變數
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV version=v2Pro
ENV language=zh

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    portaudio19-dev \
    build-essential \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 安裝 CPU 版本的 PyTorch（避免 CUDA 依賴）
RUN pip3 install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    torchvision==0.15.2

# 安裝額外的 TTS 相關依賴
RUN pip3 install --no-cache-dir \
    edge-tts>=6.1.0 \
    transformers>=4.30.0 \
    accelerate>=0.20.3 \
    librosa>=0.10.0 \
    soundfile>=0.12.1 \
    numpy>=1.24.0 \
    scipy>=1.10.0 \
    matplotlib>=3.7.0 \
    tqdm>=4.65.0 \
    psutil>=5.9.0 \
    pyyaml>=6.0 \
    aiohttp>=3.8.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.22.0 \
    pydantic>=2.0.0 \
    gradio>=3.50.2

# 複製應用程式碼
COPY . .

# 創建必要目錄
RUN mkdir -p \
    /app/GPT-SoVITS/models \
    /app/GPT-SoVITS/pretrained_models \
    /app/GPT-SoVITS/text \
    /app/GPT-SoVITS/SoVITS_weights_v2Pro \
    /app/GPT-SoVITS/GPT_weights_v2Pro \
    /app/GPT-SoVITS/logs \
    /app/GPT-SoVITS/output \
    /app/GPT-SoVITS/TEMP \
    /app/GPT-SoVITS/raw \
    /app/models \
    /app/training_data \
    /app/logs \
    /app/output \
    /app/cache \
    /app/config

# 設定權限
RUN chmod +x main.py
RUN chmod +x GPT-SoVITS/webui.py

# 設定 Python 路徑
ENV PYTHONPATH=/app:/app/GPT-SoVITS

# 暴露服務埠
EXPOSE 8501 8002 8003 7860 9880 9874 9873 9872 9871

# 啟動指令 - 啟動 TTS API
CMD ["python3", "main.py"] 