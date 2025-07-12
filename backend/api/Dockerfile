FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY recommendation_service.py .

# 暴露端口
EXPOSE 8005

# 啟動命令
CMD ["python", "-m", "uvicorn", "recommendation_service:app", "--host", "0.0.0.0", "--port", "8005"] 