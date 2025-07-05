# Podwise RAG Pipeline Podman 部署指南

## 🎯 概述

本指南專門說明如何使用 Podman 部署 Podwise RAG Pipeline 服務到 Kubernetes 集群。

## 📋 前置需求

- Kubernetes 集群
- kubectl 工具
- Podman (推薦 4.0+)
- 訪問容器註冊表的權限
- OpenAI API Key (可選，用於備援)

## 🚀 快速部署

### 使用快速部署腳本 (推薦)

```bash
# 進入部署目錄
cd deploy/k8s/rag-pipeline

# 查看幫助
./quick-deploy.sh --help

# Podman K8s 部署 (包含 OpenAI 備援)
./quick-deploy.sh -m k8s -b podman -k "your_openai_api_key"

# 自動確認部署
./quick-deploy.sh -m k8s -b podman -k "your_openai_api_key" -y
```

### 使用專用 Podman 腳本

```bash
# 設置環境變數
export OPENAI_API_KEY="your_openai_api_key"

# 執行 Podman 部署
chmod +x build-and-deploy-podman.sh
./build-and-deploy-podman.sh
```

## 🔧 Podman 特有功能

### 1. 本地映像清理
Podman 部署腳本會自動清理本地構建的映像，節省磁碟空間：

```bash
# 自動清理本地映像
podman rmi 192.168.32.38:5000/podwise-rag-pipeline:latest

# 清理未使用的映像
podman image prune -f
```

### 2. 無需 root 權限
Podman 可以在非 root 模式下運行，提高安全性：

```bash
# 檢查 Podman 模式
podman info | grep "rootless"

# 以非 root 用戶運行
podman build -t myimage .
```

### 3. 更好的隔離
Podman 提供更好的容器隔離，每個容器都有獨立的命名空間。

## 📋 部署腳本比較

| 功能 | Docker 腳本 | Podman 腳本 |
|------|-------------|-------------|
| 構建工具 | Docker | Podman |
| 本地清理 | ❌ | ✅ |
| 非 root 支援 | ❌ | ✅ |
| 隔離性 | 一般 | 更好 |
| 安全性 | 一般 | 更高 |

## ⚙️ 配置說明

### 環境變數

```bash
# 必需變數
export OPENAI_API_KEY="your_openai_api_key"

# 可選變數
export LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
export LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
export IMAGE_TAG="latest"
export NAMESPACE="podwise"
```

### Podman 配置

```bash
# 檢查 Podman 配置
podman info

# 配置註冊表
podman login 192.168.32.38:5000

# 檢查可用映像
podman images
```

## 🔍 故障排除

### 常見 Podman 問題

1. **權限問題**
   ```bash
   # 檢查用戶權限
   podman unshare id
   
   # 重新配置用戶命名空間
   podman system migrate
   ```

2. **註冊表連接問題**
   ```bash
   # 測試註冊表連接
   podman login 192.168.32.38:5000
   
   # 檢查網路連接
   podman network ls
   ```

3. **映像構建失敗**
   ```bash
   # 查看詳細錯誤
   podman build --log-level=debug -t test .
   
   # 清理緩存
   podman system prune -a
   ```

### 日誌查看

```bash
# 查看 Podman 日誌
journalctl --user -u podman

# 查看構建日誌
podman build -t test . 2>&1 | tee build.log

# 查看容器日誌
podman logs <container_id>
```

## 🔄 維護操作

### 更新部署

```bash
# 使用 Podman 重新構建
./build-and-deploy-podman.sh

# 或使用快速部署腳本
./quick-deploy.sh -m k8s -b podman -k "your_openai_api_key" -y
```

### 清理資源

```bash
# 清理本地映像
podman image prune -a

# 清理容器
podman container prune

# 清理系統
podman system prune -a
```

### 備份和恢復

```bash
# 備份映像
podman save -o rag-pipeline.tar 192.168.32.38:5000/podwise-rag-pipeline:latest

# 恢復映像
podman load -i rag-pipeline.tar
```

## 📊 監控

### Podman 監控

```bash
# 查看系統狀態
podman system df

# 查看運行中的容器
podman ps

# 查看映像使用情況
podman images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### K8s 監控

```bash
# 查看 Pod 狀態
kubectl get pods -n podwise -l app=rag-pipeline-service

# 查看服務狀態
kubectl get svc -n podwise -l app=rag-pipeline-service

# 查看日誌
kubectl logs -f deployment/rag-pipeline-service -n podwise
```

## 🎯 成功指標

Podman 部署成功後應該看到：

- ✅ Podman 映像構建成功
- ✅ 映像推送成功
- ✅ K8s Pod 狀態為 `Running`
- ✅ 健康檢查端點回應正常
- ✅ 本地映像清理完成
- ✅ LLM 備援機制正常運作

## 🔒 安全最佳實踐

1. **使用非 root 模式**
   ```bash
   # 確保以非 root 用戶運行
   podman unshare id
   ```

2. **定期更新 Podman**
   ```bash
   # 更新 Podman
   sudo dnf update podman  # RHEL/CentOS
   sudo apt update && sudo apt upgrade podman  # Ubuntu/Debian
   ```

3. **掃描映像安全**
   ```bash
   # 掃描映像漏洞
   podman scan 192.168.32.38:5000/podwise-rag-pipeline:latest
   ```

4. **限制資源使用**
   ```bash
   # 構建時限制資源
   podman build --memory=2g --cpus=2 -t test .
   ```

## 📚 相關文檔

- [Podman 官方文檔](https://docs.podman.io/)
- [Podman vs Docker 比較](https://podman.io/whatis.html)
- [K8s 部署指南](DEPLOYMENT_GUIDE.md)
- [快速部署腳本](quick-deploy.sh)

## 🤝 支援

如遇到 Podman 相關問題，請：

1. 查看 [Podman 故障排除指南](https://docs.podman.io/en/latest/markdown/podman-system.1.html)
2. 檢查 Podman 日誌
3. 執行 `podman system info` 收集系統信息
4. 聯繫開發團隊 