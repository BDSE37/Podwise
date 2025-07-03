# MLOps 生產部署指南

## 🎯 概述

本文件提供從開發環境到生產環境的完整部署流程，解決容器內檔案持久化問題並確保順利部署。

## 🔧 解決檔案持久化問題

### 問題描述
在 `vsc` 開發模式下，如果沒有正確配置 volume 掛載，容器內的變更可能無法同步到主機，導致開發成果丟失。

### 解決方案
我們的模板已經配置了完整的 volume 掛載：

```yaml
volumes:
  # 🔑 關鍵：雙向同步整個專案目錄
  - ./:/app
  # 確保重要目錄可以持久化
  - ./data:/app/data
  - ./logs:/app/logs
  - ./models:/app/models
  - ./cache:/app/cache
  - ./notebooks:/app/notebooks
```

### 驗證檔案同步
```bash
# 在容器內建立測試檔案
echo "test" > /app/test.txt

# 在主機上檢查檔案是否存在
ls -la test.txt
```

## 🚀 完整部署流程

### 階段 1: 開發環境準備

#### 1.1 啟動開發環境
```bash
# 使用 VS Code Dev Container (推薦)
code .
# 選擇 "Reopen in Container"

# 或手動啟動
MODE=vsc docker-compose up -d
```

#### 1.2 開發和測試
```bash
# 進入容器
docker-compose exec mlops-app bash

# 開發你的模型和 API
# 所有變更會自動同步到主機
```

#### 1.3 驗證開發成果
```bash
# 檢查重要檔案
./scripts/validate_template.sh

# 健康檢查
python scripts/health_check.py

# 測試 API
curl http://localhost:8000/health
```

### 階段 2: 準備生產部署

#### 2.1 收集開發產出
```bash
# 自動收集所有必要檔案並建立部署包
./scripts/dev_to_prod.sh package
```

這會建立：
- `deployment_artifacts/` 目錄
- `mlops-deployment-YYYYMMDD_HHMMSS.tar.gz` 部署包
- 生產環境配置範本
- 部署檢查清單

#### 2.2 檢查部署包內容
```bash
# 查看部署包
tar -tzf mlops-deployment-*.tar.gz

# 檢查產出目錄
ls -la deployment_artifacts/*/
```

### 階段 3: 生產環境部署

#### 3.1 傳輸部署包
```bash
# 上傳到生產伺服器
scp mlops-deployment-*.tar.gz user@prod-server:/opt/mlops/

# 登入生產伺服器
ssh user@prod-server
cd /opt/mlops/
```

#### 3.2 解壓和配置
```bash
# 解壓部署包
tar -xzf mlops-deployment-*.tar.gz
cd mlops-deployment-*/

# 配置生產環境
cp .env.production .env
vi .env  # 更新生產配置
```

#### 3.3 關鍵生產配置項目
```bash
# .env 檔案中需要更新的項目：
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@db:5432/mlops
REDIS_URL=redis://redis:6379/0
MLFLOW_TRACKING_URI=http://mlflow:5000
REGISTRY=your-docker-registry.com
TAG=v1.0.0
```

#### 3.4 執行部署
```bash
# 設定權限
chmod +x scripts/*.sh

# 完整部署
./scripts/deploy.sh deploy
```

#### 3.5 驗證部署
```bash
# 檢查服務狀態
./scripts/deploy.sh status

# 健康檢查
curl http://localhost:8000/health

# 查看日誌
./scripts/deploy.sh logs
```

## 📊 生產環境管理

### 監控和日誌
```bash
# 查看服務狀態
docker-compose -f compose.yml -f compose.prod.yml ps

# 即時日誌
docker-compose -f compose.yml -f compose.prod.yml logs -f mlops-app

# Prometheus 指標
curl http://localhost:9090/metrics
```

### 備份和恢復
```bash
# 建立備份
./scripts/deploy.sh backup

# 查看備份
ls -la backups/
```

### 服務管理
```bash
# 重啟服務
docker-compose -f compose.yml -f compose.prod.yml restart mlops-app

# 更新服務
./scripts/deploy.sh build
./scripts/deploy.sh deploy

# 停止服務
./scripts/deploy.sh down
```

## 🔒 安全最佳實踐

### 環境變數管理
```bash
# 使用 Docker secrets (推薦)
echo "your-secret-key" | docker secret create secret_key -

# 或使用 .env 檔案 (確保不被版本控制)
echo ".env" >> .gitignore
```

### 網路安全
```bash
# 配置防火牆
ufw allow 22     # SSH
ufw allow 80     # HTTP
ufw allow 443    # HTTPS
ufw deny 8000    # 不直接暴露 API 端口
```

### SSL/TLS 配置
```bash
# 使用 Let's Encrypt 或企業憑證
# 配置 Nginx 反向代理
docker-compose --profile with-nginx up -d
```

## 🚨 故障排除

### 常見問題

#### 1. 檔案沒有同步
```bash
# 檢查 volume 掛載
docker inspect mlops-app | grep -A 10 "Mounts"

# 檢查檔案權限
ls -la /app/
chmod -R 755 /app/
```

#### 2. 服務啟動失敗
```bash
# 查看詳細日誌
docker-compose logs mlops-app

# 檢查埠口衝突
netstat -tulpn | grep :8000

# 重建容器
docker-compose build --no-cache mlops-app
```

#### 3. 資料庫連接問題
```bash
# 檢查資料庫服務
docker-compose ps postgres

# 測試連接
docker-compose exec mlops-app python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Database connection successful')
"
```

#### 4. 記憶體不足
```bash
# 檢查資源使用
docker stats

# 調整資源限制
# 編輯 compose.prod.yml 中的 deploy.resources
```

### 緊急恢復
```bash
# 快速回滾到上一版本
docker-compose -f compose.yml -f compose.prod.yml down
export TAG=previous-version
docker-compose -f compose.yml -f compose.prod.yml up -d

# 從備份恢復
cd backups/latest/
docker run --rm \
  -v mlops_prod-data:/data \
  -v "$(pwd)":/backup \
  alpine tar xzf /backup/data.tar.gz -C /data
```

## 📈 性能調優

### 資源配置
```yaml
# compose.prod.yml 中的建議配置
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### 快取策略
```bash
# 配置 Redis 快取
export REDIS_URL=redis://redis:6379/0

# 配置應用程式快取
# 在 config/services.env 中設定
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

## 📝 檢查清單

### 部署前檢查
- [ ] 所有測試通過
- [ ] 代碼已提交到版本控制
- [ ] 環境變數已配置
- [ ] 資料庫遷移已準備
- [ ] 備份策略已實施
- [ ] 監控已配置

### 部署後驗證
- [ ] 服務健康檢查通過
- [ ] API 端點可存取
- [ ] 日誌正常輸出
- [ ] 指標收集正常
- [ ] 資料庫連接正常
- [ ] 檔案持久化正常

## 🔄 持續部署

### CI/CD 整合
```yaml
# .github/workflows/deploy.yml 範例
name: Deploy to Production
on:
  push:
    tags: ['v*']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and Deploy
        run: |
          ./scripts/dev_to_prod.sh package
          # 部署到生產環境
```

### 藍綠部署
```bash
# 建立新版本
export TAG=v2.0.0
./scripts/deploy.sh build

# 部署到暫存環境測試
ENVIRONMENT=staging ./scripts/deploy.sh deploy

# 切換到生產環境
ENVIRONMENT=production ./scripts/deploy.sh deploy
```

這個完整的部署指南確保你可以安全、可靠地將開發環境中的成果部署到生產環境，同時避免檔案丟失問題。 