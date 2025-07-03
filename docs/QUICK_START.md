# MLOps 模板快速啟動指南

## 🚀 5 分鐘快速啟動

### 前置要求
- Docker & Docker Compose
- VS Code (可選但推薦)

### 1. 建立新專案
```bash
# 複製模板到新專案
cp -r mlops-template my-new-project
cd my-new-project

# 初始化 Git (可選)
git init
git add .
git commit -m "Initial commit from MLOps template"
```

### 2. 啟動開發環境

#### 選項 A: VS Code Dev Container (推薦)
```bash
# 開啟 VS Code
code .

# 按 Ctrl+Shift+P 開啟命令面板
# 選擇: "Dev Containers: Reopen in Container"
```

#### 選項 B: 手動 Docker Compose
```bash
# 開發模式 (預設)
docker-compose up

# 或指定模式
MODE=vsc docker-compose up -d
MODE=api docker-compose up        # API 模式
MODE=jupyterlab docker-compose up # Jupyter 模式

```

### 3. 驗證安裝
```bash
# 在容器內執行
python scripts/health_check.py

# 或使用驗證腳本
./scripts/validate_template.sh
```

### 4. 存取服務
- **API 文件**: http://localhost:8000/docs
- **Jupyter Lab**: http://localhost:8888
- **Prometheus**: http://localhost:9090

## 🛠️ 自訂配置

### 更新 Python 依賴
```bash
# 進入 requirements 目錄
cd requirements/

# 編輯 .in 檔案
vim base-requirements.in

# 更新依賴
./update_requirements.sh
```

### 環境變數配置
```bash
# 複製範例配置
cp config/python.env.example config/python.env
cp config/services.env.example config/services.env

# 編輯配置
vim config/services.env
```

## 📚 常用命令

### 開發工作流程
```bash
# 啟動開發環境
MODE=vsc docker-compose up -d

# 查看日誌
docker-compose logs -f mlops-app

# 進入容器
docker-compose exec mlops-app bash

# 停止服務
docker-compose down
```

### 測試和驗證
```bash
# 運行測試
python -m pytest tests/

# 健康檢查
curl http://localhost:8000/health

# 驗證模板
./scripts/validate_template.sh
```

## 🔧 故障排除

### 常見問題

1. **端口被占用**
   ```bash
   # 修改端口
   export API_PORT=8001
   export JUPYTER_PORT=8889
   docker-compose up
   ```

2. **依賴問題**
   ```bash
   # 重建容器
   docker-compose build --no-cache
   ```

3. **權限問題**
   ```bash
   # 修復腳本權限
   chmod +x scripts/*.sh
   chmod +x requirements/*.sh
   ```

## 🎯 下一步

1. **自訂 API**: 編輯 `api/main.py`
2. **添加模型**: 在 `src/models/` 中實現
3. **設置測試**: 在 `tests/` 中添加測試
4. **配置 MLflow**: 啟動實驗追蹤
5. **部署準備**: 設置生產環境配置

## 📖 進階指南

查看完整的 [README.md](README.md) 以獲得詳細的使用說明和最佳實踐。 



mlops-template/
├── 📁 .devcontainer/
│   └── devcontainer.json          # VS Code 開發容器配置
├── 📁 api/
│   ├── __init__.py
│   └── main.py                    # FastAPI 主應用程式
├── 📁 src/
│   ├── __init__.py
│   └── 📁 models/
│       ├── __init__.py
│       └── base.py                # 基礎模型類別
├── 📁 requirements/
│   ├── base-requirements.in       # 核心套件
│   ├── dev-requirements.in        # 開發工具
│   ├── api-requirements.in        # API 服務
│   ├── ml-requirements.in         # 機器學習
│   ├── requirements.txt           # 編譯後的依賴
│   └── update_requirements.sh     # 依賴更新腳本
├── 📁 config/
│   ├── python.env                 # Python 環境配置
│   └── services.env               # 服務配置
├── 📁 scripts/
│   ├── entrypoint.sh              # 多模式啟動腳本
│   ├── setup.sh                   # 環境初始化
│   ├── health_check.py            # 健康檢查
│   └── validate_template.sh       # 模板驗證
├── 📁 monitoring/
│   └── prometheus.yml             # Prometheus 配置
├── 📁 data/                       # 資料檔案
├── 📁 logs/                       # 日誌檔案
├── 📁 models/                     # 訓練模型
├── 📁 cache/                      # 快取檔案
├── 📁 notebooks/                  # Jupyter notebooks
├── 📁 tests/                      # 測試檔案
├── 📁 docs/                       # 文件
├── 🐳 Dockerfile                  # 容器建置檔案
├── 🐳 compose.yml                 # 服務編排配置
├── 📝 .dockerignore               # Docker 忽略檔案
├── 📖 README.md                   # 完整使用說明
└── 🚀 QUICK_START.md              # 快速啟動指南