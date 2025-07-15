# Podwise 專案 Podman 部署指南

## 📋 概述

本指南專門針對使用 Podman 部署 Podwise 專案。Podman 是一個無守護進程的容器引擎，提供與 Docker 相容的 CLI 介面。

## 🚀 快速開始

### 1. 安裝 Podman

#### Ubuntu/Debian
```bash
# 安裝 Podman
sudo apt-get update
sudo apt-get install -y podman

# 安裝 Podman Compose
pip3 install podman-compose
```

#### CentOS/RHEL/Fedora
```bash
# 安裝 Podman
sudo yum install -y podman  # CentOS/RHEL
# 或
sudo dnf install -y podman  # Fedora

# 安裝 Podman Compose
pip3 install podman-compose
```

#### 其他發行版
```bash
# 使用官方安裝腳本
curl -L https://github.com/containers/podman/releases/latest/download/podman-installer.sh | bash
```

### 2. 啟動 Podman 服務

```bash
# 啟動 Podman 服務
sudo systemctl start podman

# 設置開機自啟
sudo systemctl enable podman

# 檢查服務狀態
sudo systemctl status podman
```

### 3. 配置 Podman

#### 設置用戶命名空間（可選）
```bash
# 編輯 /etc/subuid 和 /etc/subgid
sudo usermod --add-subuids 100000-165535 $USER
sudo usermod --add-subgids 100000-165535 $USER
```

#### 配置 Podman 鏡像倉庫
```bash
# 編輯 /etc/containers/registries.conf
sudo nano /etc/containers/registries.conf
```

### 4. 啟動 Podwise 專案

#### 使用自動化腳本（推薦）
```bash
# 啟動所有服務
./start-podwise-podman.sh

# 檢查服務狀態
./check-podwise.sh

# 停止所有服務
./stop-podwise-podman.sh
```

#### 手動啟動
```bash
# 1. 檢查環境變數文件
ls -la backend/.env

# 2. 如果沒有 .env 文件，複製範例文件
cp backend/env.example backend/.env

# 3. 編輯環境變數（如需要）
nano backend/.env

# 4. 啟動所有服務
podman-compose up -d --build

# 5. 查看服務狀態
podman-compose ps

# 6. 查看日誌
podman-compose logs -f [服務名]
```

## 📁 服務訪問地址

### 主要服務
- 🌐 **前端主頁面**: http://localhost:8080
- 💬 **Streamlit 聊天**: http://localhost:8501
- 🔊 **TTS 服務**: http://localhost:8003
- 🎤 **STT 服務**: http://localhost:8001
- 🤖 **LLM 服務**: http://localhost:8000
- 🔍 **RAG Pipeline**: http://localhost:8005
- 📊 **ML Pipeline**: http://localhost:8004
- 🌍 **Web Search**: http://localhost:8006

### 監控工具
- 📈 **Grafana**: http://192.168.32.38:30004
- 📊 **Prometheus**: http://192.168.32.38:30090
- 🐳 **Portainer**: http://192.168.32.38:30003
- 🔍 **Attu (Milvus)**: http://192.168.32.38:3101

## 🔧 Podman 常用命令

### 服務管理
```bash
# 啟動所有服務
podman-compose up -d

# 停止所有服務
podman-compose down

# 重啟特定服務
podman-compose restart [服務名]

# 查看服務狀態
podman-compose ps

# 查看服務日誌
podman-compose logs -f [服務名]
```

### 容器管理
```bash
# 查看所有容器
podman ps -a

# 進入容器
podman exec -it podwise_[服務名] bash

# 查看容器資源使用
podman stats

# 查看容器詳細信息
podman inspect [容器名]
```

### 映像管理
```bash
# 查看所有映像
podman images

# 建置映像
podman build -t [映像名] [路徑]

# 拉取映像
podman pull [映像名]

# 清理未使用的映像
podman image prune -f
```

### 網路管理
```bash
# 查看網路
podman network ls

# 創建網路
podman network create [網路名]

# 檢查網路連接
podman network inspect [網路名]
```

### 系統管理
```bash
# 查看系統使用情況
podman system df

# 清理所有未使用的資源
podman system prune -a

# 查看 Podman 信息
podman info
```

## 🔍 Podman 特定故障排除

### 常見問題

#### 1. 權限問題
```bash
# 檢查用戶權限
podman info

# 如果出現權限錯誤，設置用戶命名空間
sudo usermod --add-subuids 100000-165535 $USER
sudo usermod --add-subgids 100000-165535 $USER
```

#### 2. 網路問題
```bash
# 檢查 Podman 網路
podman network ls
podman network inspect podwise_podwise

# 重新創建網路
podman network rm podwise_podwise
podman-compose up -d
```

#### 3. 存儲問題
```bash
# 檢查存儲驅動
podman info --format "{{.Store.GraphDriverName}}"

# 清理存儲
podman system prune -a --volumes
```

#### 4. 鏡像拉取問題
```bash
# 檢查鏡像倉庫配置
cat /etc/containers/registries.conf

# 手動拉取鏡像
podman pull docker.io/library/postgres:15
```

### 日誌分析
```bash
# 查看所有服務的錯誤日誌
podman-compose logs | grep -i error

# 查看特定時間段的日誌
podman-compose logs --since="2024-01-01T00:00:00" [服務名]

# 實時監控日誌
podman-compose logs -f --tail=100 [服務名]
```

## 📊 Podman 監控和維護

### 健康檢查
```bash
# 執行健康檢查腳本
./check-podwise.sh

# 手動檢查服務健康狀態
curl -f http://localhost:8005/health
curl -f http://localhost:8003/health
```

### 資源監控
```bash
# 查看容器資源使用
podman stats

# 查看系統使用情況
podman system df

# 查看詳細統計
podman stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### 備份和恢復
```bash
# 備份 PostgreSQL 資料
podman exec podwise_postgresql pg_dump -U bdse37 podcast > backup.sql

# 恢復 PostgreSQL 資料
podman exec -i podwise_postgresql psql -U bdse37 podcast < backup.sql
```

### 更新服務
```bash
# 拉取最新代碼
git pull

# 重新建置並啟動服務
podman-compose up -d --build

# 清理舊映像
podman image prune -f
```

## 🛡️ Podman 安全注意事項

### 1. 用戶命名空間
```bash
# 啟用用戶命名空間以提高安全性
sudo usermod --add-subuids 100000-165535 $USER
sudo usermod --add-subgids 100000-165535 $USER
```

### 2. 鏡像安全
```bash
# 只使用可信的鏡像倉庫
# 定期更新基礎映像
podman pull --all-tags [映像名]
```

### 3. 網路安全
```bash
# 使用自定義網路隔離容器
podman network create podwise_isolated
```

### 4. 存儲安全
```bash
# 使用加密存儲（如果支援）
# 定期備份重要資料
```

## 🔄 Docker 到 Podman 遷移

### 1. 停止 Docker 服務
```bash
sudo systemctl stop docker
sudo systemctl disable docker
```

### 2. 遷移容器
```bash
# 導出 Docker 容器
docker export [容器ID] > container.tar

# 導入到 Podman
podman import container.tar [映像名]
```

### 3. 遷移映像
```bash
# 保存 Docker 映像
docker save [映像名] > image.tar

# 載入到 Podman
podman load < image.tar
```

## 📞 支援

如果遇到 Podman 相關問題，請：

1. 檢查本文件的故障排除部分
2. 查看 Podman 官方文檔：https://docs.podman.io/
3. 查看服務日誌：`podman-compose logs [服務名]`
4. 執行狀態檢查：`./check-podwise.sh`
5. 聯繫開發團隊

## 📝 Podman 優勢

1. **無守護進程**: 不需要運行守護進程，更安全
2. **用戶命名空間**: 支援無 root 權限運行
3. **OCI 相容**: 完全相容 Docker 映像格式
4. **系統整合**: 與 systemd 深度整合
5. **資源效率**: 更低的資源佔用

## 🔗 相關連結

- [Podman 官方文檔](https://docs.podman.io/)
- [Podman Compose 文檔](https://github.com/containers/podman-compose)
- [Podwise 專案文檔](./README-DEPLOYMENT.md) 