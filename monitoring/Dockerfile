# 監控服務 Dockerfile
# 整合 Prometheus 與 Grafana 監控系統
FROM python:3.10-slim

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

# 創建監控相關目錄
RUN mkdir -p /app/config \
    /app/data \
    /app/logs \
    /app/dashboards

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/app/config
ENV DATA_DIR=/app/data
ENV LOGS_DIR=/app/logs
ENV DASHBOARDS_DIR=/app/dashboards

# 暴露監控服務埠（9090, 3000）
EXPOSE 9090 3000

# 啟動指令
CMD ["python", "main.py"] 