# Dockerfile for FastAPI app running app.py
FROM python:3.10-slim

# 安裝必要套件
RUN apt-get update && apt-get install -y build-essential

# 建立工作目錄
WORKDIR /app

# 複製專案檔案
COPY . /app

# 安裝 Python 依賴
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 啟動 FastAPI 應用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]