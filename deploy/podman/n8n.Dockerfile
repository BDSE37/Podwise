FROM python:3.10-slim

# === 安裝必要套件與 Node.js 20 ===
RUN apt update && apt install -y \
    curl gnupg ca-certificates \
    git ffmpeg chromium-driver chromium \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1 \
    build-essential libssl-dev libffi-dev && \
    # 安裝 Node.js v20.x
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt install -y nodejs && \
    npm install -g n8n && \
    apt clean

# === 安裝 Python 套件 ===
RUN pip install --upgrade pip && pip install \
    torch torchvision torchaudio \
    transformers \
    sentence-transformers \
    pymilvus pymongo \
    requests tqdm \
    yt-dlp beautifulsoup4 \
    fuzzywuzzy python-Levenshtein \
    selenium undetected-chromedriver

# === 預載 BGE-M3 模型（可選）===
RUN python3 -c "from transformers import AutoModel, AutoTokenizer; AutoTokenizer.from_pretrained('BAAI/bge-m3'); AutoModel.from_pretrained('BAAI/bge-m3')"

# === HuggingFace cache 設定（可搭配 Volume）===
ENV TRANSFORMERS_CACHE=/models/huggingface
ENV HF_HOME=/models/huggingface

# === Volume 掛載點（供 n8n 使用）===
VOLUME /home/node/.n8n

# === 開放 Port 並切換非 root 帳號執行 ===
EXPOSE 5678
RUN useradd -m -s /bin/bash n8nuser
USER n8nuser

CMD ["n8n"]
