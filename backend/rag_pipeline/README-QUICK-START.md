# RAG Pipeline 快速開始指南

## 前置需求

- Podman 已安裝
- 在 `backend/rag_pipeline` 目錄下執行

## 快速開始

### 1. 建構和啟動容器

```bash
# 在主機上執行
./build-and-run.sh
```

這會：
- 建構 Docker 映像
- 啟動容器（開發模式）
- 顯示服務資訊

### 2. 進入容器安裝套件

```bash
# 在主機上執行
./build-and-run.sh enter
```

在容器內執行：
```bash
# 在容器內執行
./install-rag-packages.sh
```

### 3. 啟動 RAG 服務

在容器內執行：
```bash
# 啟動服務
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

### 4. 測試連接

在主機上執行：
```bash
# 測試健康檢查
curl http://localhost:8010/health

# 測試 API 文檔
curl http://localhost:8010/docs
```

## 常用命令

### 在主機上執行

```bash
# 建構映像
./build-and-run.sh build

# 啟動開發模式
./build-and-run.sh run-dev

# 啟動生產模式
./build-and-run.sh run-prod

# 進入容器
./build-and-run.sh enter

# 安裝 RAG 套件（在容器內）
./build-and-run.sh install-rag-packages

# 查看日誌
./build-and-run.sh logs

# 查看狀態
./build-and-run.sh status

# 停止服務
./build-and-run.sh stop

# 清理
./build-and-run.sh cleanup
```

### 在容器內執行

```bash
# 安裝 RAG 套件
./install-rag-packages.sh

# 啟動 IPython
python -m ipython

# 執行測試
python -m pytest

# 格式化程式碼
black .

# 檢查程式碼風格
flake8 .

# 啟動服務
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

## 故障排除

### 端口被佔用
腳本會自動尋找可用端口，從 8010 開始

### 容器啟動失敗
```bash
# 查看容器日誌
podman logs rag-pipeline-container

# 重新建構
./build-and-run.sh cleanup
./build-and-run.sh build
```

### 套件安裝失敗
```bash
# 進入容器手動安裝
./build-and-run.sh enter
pip install <package-name>
```

## 環境變數

編輯 `env.local` 檔案設定資料庫連接：

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=podwise
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

## 前端連接

前端已配置為連接端口 8010，確保容器使用正確的端口映射。 