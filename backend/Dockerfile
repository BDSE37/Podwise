# 基礎 Python 3.10 映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt（如有）
COPY requirements.txt ./

# 安裝依賴（若無 requirements.txt 會忽略）
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# 複製所有程式碼
COPY . .

# 預設啟動指令（可依需求調整）
CMD ["python", "main.py"] 