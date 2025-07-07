# 使用 Python 3.10 作為基礎映像
FROM docker.io/library/python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建健康檢查端點
RUN echo 'import streamlit as st\n\
st.set_page_config(page_title="Podri Chat", page_icon="🦊")\n\
st.write("Podri Chat 服務正常運行")\n\
' > health_check.py

# 暴露端口
EXPOSE 8501

# 設定環境變數
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# 啟動命令
CMD ["streamlit", "run", "podri_chat.py", "--server.port=8501", "--server.address=0.0.0.0"] 