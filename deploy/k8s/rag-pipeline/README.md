# Podwise RAG Pipeline K8s 開發文件

## 📁 目錄結構

```
deploy/k8s/rag-pipeline/
├── README.md                           # 本文件
├── DEPLOYMENT_GUIDE.md                 # 詳細部署指南
├── quick-deploy.sh                     # 快速部署腳本
├── build-and-deploy-k8s.sh             # Docker K8s 構建部署腳本
├── build-and-deploy-podman.sh          # Podman K8s 構建部署腳本
├── deploy-rag-on-worker2.sh            # Worker2 部署腳本
├── deploy-single-node.sh               # 單節點部署腳本
├── test-rag-connection.sh              # 連接測試腳本
├── Dockerfile                          # Docker 映像檔
├── rag-pipeline-deployment.yaml        # K8s 部署配置
├── rag-pipeline-pvc.yaml               # 持久化存儲配置
├── rag-pipeline-single-node.yaml       # 單節點部署配置
├── rag-pipeline-pvc-single.yaml        # 單節點 PVC 配置
└── openai-secrets.yaml                 # OpenAI Secrets 配置
```

## 🚀 快速開始

### 1. 使用快速部署腳本 (推薦)

```bash
# 進入目錄
cd deploy/k8s/rag-pipeline

# 查看幫助
./quick-deploy.sh --help

# K8s 部署 (使用 Podman，包含 OpenAI 備援)
./quick-deploy.sh -m k8s -b podman -k "your_openai_api_key"

# K8s 部署 (使用 Docker)
./quick-deploy.sh -m k8s -b docker -k "your_openai_api_key"

# Worker2 部署
./quick-deploy.sh -m worker2 -k "your_openai_api_key"

# 同時部署到 K8s 和 Worker2 (使用 Podman)
./quick-deploy.sh -m both -b podman -k "your_openai_api_key" -y
```

### 2. 手動部署

```bash
# 設置環境變數
export OPENAI_API_KEY="your_openai_api_key"

# 執行 K8s 部署
./build-and-deploy-k8s.sh

# 或執行 Worker2 部署
./deploy-rag-on-worker2.sh
```

## 🤖 LLM 備援機制

### 模型優先級

1. **Qwen2.5-Taiwan** (第一優先)
   - 台灣優化版本
   - 針對繁體中文優化
   - 模型: `weiren119/Qwen2.5-Taiwan-8B-Instruct`

2. **Qwen3:8b** (第二優先)
   - 標準 Qwen3 模型
   - 主要備用模型
   - 模型: `Qwen/Qwen2.5-8B-Instruct`

3. **OpenAI GPT-3.5** (備援)
   - 需要 OpenAI API Key
   - 當前面模型不可用時啟用
   - 模型: `gpt-3.5-turbo`

4. **OpenAI GPT-4** (最後備援)
   - 最高品質備援
   - 成本較高
   - 模型: `gpt-4`

### 配置 OpenAI 備援

```bash
# 方法 1: 環境變數
export OPENAI_API_KEY="your_openai_api_key"

# 方法 2: K8s Secret
kubectl create secret generic openai-secrets \
    --from-literal=OPENAI_API_KEY="your_openai_api_key" \
    --namespace=podwise
```

## 📋 部署腳本說明

### quick-deploy.sh
- **功能**: 整合所有部署方式的快速部署腳本
- **特點**: 支援命令行參數、自動驗證、詳細日誌
- **用法**: `./quick-deploy.sh -m k8s -k "api_key"`

### build-and-deploy-k8s.sh
- **功能**: 使用 Docker 構建映像並部署到 K8s
- **特點**: 自動構建、推送、部署、驗證
- **包含**: Secrets 創建、健康檢查、服務測試

### build-and-deploy-podman.sh
- **功能**: 使用 Podman 構建映像並部署到 K8s
- **特點**: 自動構建、推送、部署、驗證、本地清理
- **包含**: Secrets 創建、健康檢查、服務測試、映像清理

### deploy-rag-on-worker2.sh
- **功能**: 在 worker2 節點上部署 RAG Pipeline
- **特點**: SSH 連接、依賴安裝、服務測試
- **包含**: 環境設置、LLM 測試、服務啟動

### deploy-single-node.sh
- **功能**: 單節點部署 (適用於開發環境)
- **特點**: 簡化配置、快速部署
- **包含**: 基本服務配置、本地測試

## ⚙️ 配置文件說明

### rag-pipeline-deployment.yaml
- **用途**: K8s 主要部署配置
- **包含**: Pod 配置、服務配置、資源限制
- **特點**: 支援 LLM 備援、健康檢查、節點選擇

### rag-pipeline-pvc.yaml
- **用途**: 持久化存儲配置
- **包含**: 數據存儲、模型存儲、快取存儲
- **特點**: 多層級存儲、備份支援

### openai-secrets.yaml
- **用途**: OpenAI API Key 安全存儲
- **包含**: Secret 配置、命名空間設置
- **特點**: 安全存儲、可選配置

## 🔧 測試和驗證

### 連接測試
```bash
# 執行連接測試
./test-rag-connection.sh

# 手動測試
curl http://worker2:30806/health
curl http://worker2:30806/api/v1/llm-status
```

### LLM 備援測試
```bash
# 進入 Pod 執行測試
kubectl exec -it deployment/rag-pipeline-service -n podwise -- python3 -c "
from backend.rag_pipeline.test_llm_fallback import LLMFallbackTest
import asyncio

async def test():
    test_suite = LLMFallbackTest()
    results = test_suite.run_all_tests()
    print(f'測試結果: {results[\"summary\"]}')

asyncio.run(test())
"
```

## 📊 監控和日誌

### 查看服務狀態
```bash
# Pod 狀態
kubectl get pods -n podwise -l app=rag-pipeline-service

# 服務狀態
kubectl get svc -n podwise -l app=rag-pipeline-service

# 日誌查看
kubectl logs -f deployment/rag-pipeline-service -n podwise
```

### 健康檢查
```bash
# 自動健康檢查
kubectl get pods -n podwise -l app=rag-pipeline-service

# 手動健康檢查
curl http://worker2:30806/health
```

## 🔄 維護操作

### 更新部署
```bash
# 更新映像
kubectl set image deployment/rag-pipeline-service rag-pipeline-service=192.168.32.38:5000/podwise-rag-pipeline:latest -n podwise

# 重啟部署
kubectl rollout restart deployment/rag-pipeline-service -n podwise
```

### 擴展服務
```bash
# 擴展副本數
kubectl scale deployment/rag-pipeline-service --replicas=3 -n podwise
```

### 故障排除
```bash
# 查看 Pod 事件
kubectl describe pod <pod-name> -n podwise

# 查看詳細日誌
kubectl logs <pod-name> -n podwise --previous

# 進入 Pod 除錯
kubectl exec -it <pod-name> -n podwise -- bash
```

## 🎯 成功指標

部署成功後應該看到：

- ✅ Pod 狀態為 `Running`
- ✅ 健康檢查端點回應正常
- ✅ API 查詢端點正常工作
- ✅ LLM 備援機制正常運作
- ✅ 台灣模型為第一優先
- ✅ OpenAI 備援配置正確 (如果設置)
- ✅ podri-chat 能成功發送查詢到 RAG Pipeline

## 📚 相關文檔

- [詳細部署指南](DEPLOYMENT_GUIDE.md) - 完整的部署說明
- [Podman 部署指南](PODMAN_DEPLOYMENT.md) - Podman 專用部署說明
- [CrewAI + LangChain 整合說明](../../../backend/rag_pipeline/README_CrewAI_LangChain_LLM.md) - 架構說明
- [LLM 備援測試](../../../backend/rag_pipeline/test_llm_fallback.py) - 測試腳本

## 🤝 貢獻

如需修改或擴展部署配置，請：

1. 更新對應的配置文件
2. 修改相關的部署腳本
3. 更新文檔說明
4. 測試部署流程
5. 提交 Pull Request

## 📞 支援

如遇到問題，請：

1. 查看 [故障排除指南](DEPLOYMENT_GUIDE.md#故障排除)
2. 檢查日誌檔案
3. 執行測試腳本
4. 聯繫開發團隊 