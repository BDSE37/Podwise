# Podwise RAG Pipeline K8s 部署指南

## 🎯 概述

本指南說明如何在 Kubernetes 集群上部署 Podwise RAG Pipeline 服務，包含新的 LLM 備援機制。

## 📋 前置需求

- Kubernetes 集群
- kubectl 工具
- Docker 或 Podman
- 訪問容器註冊表的權限
- OpenAI API Key (可選，用於備援)

## 🚀 部署方式

### 方式一：使用 K8s 部署腳本 (推薦)

```bash
# 1. 進入部署目錄
cd deploy/k8s/rag-pipeline

# 2. 設置環境變數 (可選)
export OPENAI_API_KEY="your_openai_api_key_here"
export LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
export LANGFUSE_SECRET_KEY="your_langfuse_secret_key"

# 3. 執行部署腳本
chmod +x build-and-deploy-k8s.sh
./build-and-deploy-k8s.sh
```

### 方式二：使用 Worker2 部署腳本

```bash
# 1. 進入部署目錄
cd deploy/k8s/rag-pipeline

# 2. 設置環境變數 (可選)
export OPENAI_API_KEY="your_openai_api_key_here"

# 3. 執行部署腳本
chmod +x deploy-rag-on-worker2.sh
./deploy-rag-on-worker2.sh
```

### 方式三：手動部署

```bash
# 1. 創建命名空間
kubectl create namespace podwise

# 2. 創建 Secrets (可選)
kubectl create secret generic openai-secrets \
    --from-literal=OPENAI_API_KEY="your_openai_api_key" \
    --namespace=podwise

# 3. 部署服務
kubectl apply -f rag-pipeline-deployment.yaml

# 4. 檢查部署狀態
kubectl rollout status deployment/rag-pipeline-service -n podwise
```

## 🤖 LLM 備援機制

### 模型優先級順序

1. **Qwen2.5-Taiwan** (第一優先)
   - 台灣優化版本
   - 針對繁體中文優化
   - 模型名稱: `weiren119/Qwen2.5-Taiwan-8B-Instruct`

2. **Qwen3:8b** (第二優先)
   - 標準 Qwen3 模型
   - 主要備用模型
   - 模型名稱: `Qwen/Qwen2.5-8B-Instruct`

3. **OpenAI GPT-3.5** (備援)
   - 需要 OpenAI API Key
   - 當前面模型不可用時啟用
   - 模型名稱: `gpt-3.5-turbo`

4. **OpenAI GPT-4** (最後備援)
   - 最高品質備援
   - 成本較高
   - 模型名稱: `gpt-4`

### 配置 OpenAI 備援

1. **設置環境變數**:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

2. **創建 K8s Secret**:
   ```bash
   kubectl create secret generic openai-secrets \
       --from-literal=OPENAI_API_KEY="your_openai_api_key" \
       --namespace=podwise
   ```

3. **驗證配置**:
   ```bash
   curl http://worker2:30806/api/v1/llm-status
   ```

## ✅ 驗證部署

### 檢查服務狀態

```bash
# 檢查 Pod 狀態
kubectl get pods -n podwise -l app=rag-pipeline-service

# 檢查服務狀態
kubectl get svc -n podwise -l app=rag-pipeline-service

# 檢查節點分配
kubectl get pods -n podwise -l app=rag-pipeline-service -o wide
```

### 測試服務連線

```bash
# 獲取服務端點
NODE_PORT=$(kubectl get svc rag-pipeline-service -n podwise -o jsonpath='{.spec.ports[0].nodePort}')

# 測試健康檢查
curl http://worker2:$NODE_PORT/health

# 測試 LLM 狀態
curl http://worker2:$NODE_PORT/api/v1/llm-status

# 測試 API 文檔
curl http://worker2:$NODE_PORT/docs
```

### 測試 LLM 備援機制

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

## ⚙️ 配置說明

### 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `PYTHONPATH` | Python 路徑 | `/app` |
| `PYTHONUNBUFFERED` | Python 輸出緩衝 | `1` |
| `APP_ENV` | 應用環境 | `production` |
| `DEBUG` | 除錯模式 | `false` |
| `LOG_LEVEL` | 日誌等級 | `INFO` |
| `OLLAMA_HOST` | Ollama 服務地址 | `http://worker1:11434` |
| `OLLAMA_MODEL` | Ollama 模型名稱 | `qwen2.5:8b` |
| `OPENAI_API_KEY` | OpenAI API Key | (可選) |

### 資源限制

預設資源配置：

- **CPU**: 2-4 cores
- **記憶體**: 4-8 GiB
- **節點選擇器**: worker2

### 持久化存儲

服務使用以下 PVC：

- `rag-data-pvc`: 數據存儲
- `rag-models-pvc`: 模型存儲
- `rag-cache-pvc`: 快取存儲

## 🔧 故障排除

### 常見問題

1. **Pod 無法啟動**
   ```bash
   # 檢查 Pod 事件
   kubectl describe pod <pod-name> -n podwise
   
   # 查看 Pod 日誌
   kubectl logs <pod-name> -n podwise
   ```

2. **LLM 服務連線失敗**
   ```bash
   # 檢查 Ollama 服務
   curl http://worker1:11434/api/tags
   
   # 檢查模型可用性
   kubectl exec -it deployment/rag-pipeline-service -n podwise -- python3 -c "
   from backend.rag_pipeline.core.qwen3_llm_manager import get_qwen3_llm_manager
   manager = get_qwen3_llm_manager()
   print(f'可用模型: {manager.get_available_models()}')
   "
   ```

3. **OpenAI 備援不工作**
   ```bash
   # 檢查 OpenAI Secret
   kubectl get secret openai-secrets -n podwise -o yaml
   
   # 測試 OpenAI 配置
   kubectl exec -it deployment/rag-pipeline-service -n podwise -- python3 -c "
   from backend.rag_pipeline.config.integrated_config import get_config
   config = get_config()
   print(f'OpenAI 配置: {bool(config.api.openai_api_key)}')
   "
   ```

4. **CrewAI 模組缺失**
   ```bash
   # 檢查 CrewAI 安裝
   kubectl exec -it deployment/rag-pipeline-service -n podwise -- python3 -c "
   import crewai
   print(f'CrewAI 版本: {crewai.__version__}')
   "
   ```

### 日誌查看

```bash
# 查看實時日誌
kubectl logs -f deployment/rag-pipeline-service -n podwise

# 查看特定時間的日誌
kubectl logs deployment/rag-pipeline-service -n podwise --since=1h

# 查看錯誤日誌
kubectl logs deployment/rag-pipeline-service -n podwise | grep ERROR
```

## 🔄 維護操作

### 更新部署

```bash
# 更新映像
kubectl set image deployment/rag-pipeline-service rag-pipeline-service=192.168.32.38:5000/podwise-rag-pipeline:latest -n podwise

# 重啟部署
kubectl rollout restart deployment/rag-pipeline-service -n podwise

# 查看更新狀態
kubectl rollout status deployment/rag-pipeline-service -n podwise
```

### 擴展服務

```bash
# 擴展副本數
kubectl scale deployment/rag-pipeline-service --replicas=3 -n podwise

# 查看擴展狀態
kubectl get pods -n podwise -l app=rag-pipeline-service
```

### 備份和恢復

```bash
# 備份配置
kubectl get deployment rag-pipeline-service -n podwise -o yaml > backup.yaml

# 恢復配置
kubectl apply -f backup.yaml
```

## 📊 監控

### 健康檢查

```bash
# 自動健康檢查
kubectl get pods -n podwise -l app=rag-pipeline-service

# 手動健康檢查
curl http://worker2:30806/health
```

### 性能監控

```bash
# 查看資源使用情況
kubectl top pods -n podwise

# 查看節點資源
kubectl top nodes
```

### LLM 監控

```bash
# 查看 LLM 狀態
curl http://worker2:30806/api/v1/llm-status

# 查看模型指標
kubectl exec -it deployment/rag-pipeline-service -n podwise -- python3 -c "
from backend.rag_pipeline.core.qwen3_llm_manager import get_qwen3_llm_manager
manager = get_qwen3_llm_manager()
print(manager.get_metrics_summary())
"
```

## 🔒 安全注意事項

1. **API Key 保護**: 確保 OpenAI API Key 安全存儲
2. **網路安全**: 限制服務訪問權限
3. **資源限制**: 設置適當的資源限制防止資源濫用
4. **日誌管理**: 定期清理日誌檔案

## 🎯 成功指標

部署成功後應該看到：

- ✅ Pod 狀態為 `Running`
- ✅ 健康檢查端點回應正常
- ✅ API 查詢端點正常工作
- ✅ LLM 備援機制正常運作
- ✅ 台灣模型為第一優先
- ✅ OpenAI 備援配置正確 (如果設置)
- ✅ podri-chat 能成功發送查詢到 RAG Pipeline

## 🔄 重新部署

如果需要重新部署：

```bash
# 刪除現有 Pod
kubectl delete pod -n podwise -l app=rag-pipeline-service --force --grace-period=0

# 重新執行建置腳本
./build-and-deploy-k8s.sh
``` 