# ML Pipeline Dockerfile
# 使用 Python 3.10 精簡映像，適合機器學習與向量服務
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要系統依賴（如編譯器、curl）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建必要目錄（如模型、資料、日誌）
RUN mkdir -p /app/models \
    && mkdir -p /app/data \
    && mkdir -p /app/logs

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露 API 服務埠（8004）
EXPOSE 8004

# 啟動指令，執行主程式
CMD ["python", "app.py"]
