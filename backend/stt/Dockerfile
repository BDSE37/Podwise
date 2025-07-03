# 使用 Python 3.10 作為基礎映像
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 暴露端口
EXPOSE 8001

# 啟動應用（使用端口 8001）
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8001", "--server.address", "0.0.0.0"] 