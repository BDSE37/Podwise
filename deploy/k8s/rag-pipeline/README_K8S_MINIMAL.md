# Podwise RAG Pipeline K8s 最小化部署指南

## 概述

這個最小化部署方案讓您可以在 K8s 上快速部署 RAG Pipeline，然後進入容器手動安裝所需的套件。這種方式可以：

- 快速部署基本環境
- 避免長時間的映像構建
- 靈活控制套件安裝
- 便於調試和測試

## 檔案結構

```
deploy/k8s/rag-pipeline/
├── Dockerfile.k8s-minimal          # 最小化 Dockerfile
├── deploy-k8s-minimal.sh           # K8s 部署腳本
├── test-deployment.sh              # 部署測試腳本
└── README_K8S_MINIMAL.md           # 本說明文件
```

## 部署步驟

### 1. 執行部署腳本

```bash
# 基本部署
./deploy/k8s/rag-pipeline/deploy-k8s-minimal.sh

# 帶 OpenAI API Key 的部署
./deploy/k8s/rag-pipeline/deploy-k8s-minimal.sh -k "your_openai_api_key"

# 自動確認部署
./deploy/k8s/rag-pipeline/deploy-k8s-minimal.sh -k "your_openai_api_key" -y
```

### 2. 檢查部署狀態

```bash
# 測試部署
./deploy/k8s/rag-pipeline/test-deployment.sh

# 或手動檢查
kubectl get pods -n podwise -l app=rag-pipeline-service
kubectl get svc -n podwise -l app=rag-pipeline-service
```

### 3. 進入容器安裝套件

```bash
# 獲取 Pod 名稱
POD_NAME=$(kubectl get pods -n podwise -l app=rag-pipeline-service -o jsonpath='{.items[0].metadata.name}')

# 進入容器
kubectl exec -it $POD_NAME -n podwise -- bash
```

## 容器內操作

### 1. 檢查環境

```bash
# 檢查 Python 版本
python --version

# 檢查已安裝的套件
pip list

# 檢查 requirements.txt
cat requirements.txt
```

### 2. 安裝套件

```bash
# 安裝所有套件
pip install -r requirements.txt

# 或分組安裝（推薦）
# 核心套件
pip install fastapi uvicorn pydantic pydantic-settings

# 資料庫套件
pip install psycopg2-binary pymongo motor redis sqlalchemy

# AI/ML 套件
pip install numpy pandas scikit-learn torch transformers sentence-transformers

# LangChain 套件
pip install langchain langchain-core langchain-community langchain-openai

# 向量資料庫套件
pip install pymilvus faiss-cpu chromadb

# 其他套件
pip install python-dotenv aiofiles beautifulsoup4 tiktoken tqdm crewai
```

### 3. 啟動服務

```bash
# 啟動 FastAPI 服務
python -m uvicorn backend.rag_pipeline.app.main_crewai:app --host 0.0.0.0 --port 8004

# 或使用 nohup 在背景運行
nohup python -m uvicorn backend.rag_pipeline.app.main_crewai:app --host 0.0.0.0 --port 8004 > app.log 2>&1 &
```

### 4. 測試服務

```bash
# 測試健康檢查
curl http://localhost:8004/health

# 測試根端點
curl http://localhost:8004/

# 測試 API 文檔
curl http://localhost:8004/docs
```

## 服務端點

部署完成後，您可以通過以下端點訪問服務：

- **健康檢查**: `http://worker2:30806/health`
- **API 文檔**: `http://worker2:30806/docs`
- **根端點**: `http://worker2:30806/`

## 常用命令

### 查看日誌

```bash
# 查看 Pod 日誌
kubectl logs -f deployment/rag-pipeline-service -n podwise

# 查看特定 Pod 日誌
kubectl logs -f $POD_NAME -n podwise
```

### 重啟服務

```bash
# 重啟部署
kubectl rollout restart deployment/rag-pipeline-service -n podwise

# 等待重啟完成
kubectl rollout status deployment/rag-pipeline-service -n podwise
```

### 刪除部署

```bash
# 刪除部署
kubectl delete deployment rag-pipeline-service -n podwise
kubectl delete svc rag-pipeline-service -n podwise
```

## 故障排除

### 1. Pod 無法啟動

```bash
# 檢查 Pod 狀態
kubectl describe pod $POD_NAME -n podwise

# 檢查事件
kubectl get events -n podwise --sort-by='.lastTimestamp'
```

### 2. 套件安裝失敗

```bash
# 更新 pip
pip install --upgrade pip

# 安裝編譯工具
apt-get update && apt-get install -y build-essential

# 使用國內鏡像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 服務無法訪問

```bash
# 檢查服務狀態
kubectl get svc -n podwise

# 檢查端口映射
kubectl get svc rag-pipeline-service -n podwise -o yaml

# 測試內部連線
kubectl exec -it $POD_NAME -n podwise -- curl http://localhost:8004/health
```

## 注意事項

1. **資源限制**: 最小化部署使用較少的資源，適合測試和開發
2. **套件安裝**: 首次安裝套件可能需要較長時間，請耐心等待
3. **網路連線**: 確保容器可以訪問外部網路下載套件
4. **持久化**: 容器重啟後需要重新安裝套件，建議在生產環境中使用完整映像

## 下一步

完成最小化部署和套件安裝後，您可以：

1. 測試所有 API 端點
2. 配置外部服務（如資料庫、向量資料庫）
3. 調整應用程式配置
4. 部署到生產環境

如有問題，請查看日誌或聯繫開發團隊。 