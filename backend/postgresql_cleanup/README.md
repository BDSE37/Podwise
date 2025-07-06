# PostgreSQL Meta Data Cleanup

此模組提供清理 PostgreSQL 資料庫中 meta_data 相關資料的功能。
專為 Kubernetes 環境設計，支援 podwise namespace 和 podcast 資料庫。

## 功能特色

- 🔄 **批次清理**: 支援大批量資料的批次處理
- 📊 **統計報告**: 提供詳細的清理統計資訊
- 🛡️ **安全模式**: 支援試運行模式，避免意外刪除
- ⚙️ **靈活配置**: 可透過環境變數或命令列參數自訂配置
- 📝 **完整日誌**: 記錄所有清理操作的詳細日誌
- ☸️ **K8s 原生**: 專為 Kubernetes 環境優化
- 🧹 **測試資料清理**: 專門清理測試和臨時資料
- 🎵 **Episodes 處理**: 清理表情符號並對應到資料庫欄位

## 安裝

```bash
cd backend/postgresql_cleanup
pip install -r requirements.txt
```

## 本機清理測試資料

### 快速開始

```bash
# 檢查資料庫狀態
./quick_cleanup.sh --check

# 試運行清理 (不會實際刪除)
./quick_cleanup.sh --dry-run

# 執行實際清理
./quick_cleanup.sh --cleanup
```

### 詳細清理選項

```bash
# 使用 Python 腳本進行更精細的控制
python local_cleanup.py --help

# 試運行模式
python local_cleanup.py --dry-run --verbose

# 清理指定表格
python local_cleanup.py --table podcast_metadata --verbose

# 清理所有表格並輸出結果
python local_cleanup.py --verbose --output cleanup_results.json
```

## 環境變數配置

建立 `.env` 檔案並設定以下變數：

```env
# 資料庫連線配置 (已針對您的環境預設)
POSTGRES_HOST=postgresql-service
POSTGRES_PORT=5432
POSTGRES_DB=podcast
POSTGRES_USER=bdse37
POSTGRES_PASSWORD=111111

# Kubernetes 配置
K8S_NAMESPACE=podwise
POSTGRES_SERVICE_NAME=postgresql-service

# 清理配置
CLEANUP_BATCH_SIZE=1000
CLEANUP_MAX_RETRIES=3
CLEANUP_TIMEOUT=300
CLEANUP_DRY_RUN=false

# 清理條件
CLEANUP_MAX_AGE_DAYS=90
CLEANUP_STATUS_FILTER=completed,failed
CLEANUP_SIZE_LIMIT_MB=1000

# Kubernetes 特定配置
K8S_JOB_TIMEOUT=3600
K8S_RETRY_INTERVAL=30
```

## 使用方法

### 本機執行

```bash
# 清理所有目標表格
python -m postgresql_cleanup.main

# 清理指定表格
python -m postgresql_cleanup.main --table podcast_metadata

# 試運行模式
python -m postgresql_cleanup.main --dry-run
```

### Kubernetes 部署

```bash
# 部署到 Kubernetes
kubectl apply -f k8s_deployment.yaml

# 檢查部署狀態
kubectl get cronjobs -n podwise
kubectl get pods -n podwise -l app=postgresql-cleanup

# 手動觸發清理任務
kubectl create job --from=cronjob/postgresql-cleanup-cronjob manual-cleanup -n podwise

# 查看日誌
kubectl logs -n podwise -l app=postgresql-cleanup
```

### 進階用法

```bash
# 清理 30 天前的資料
python -m postgresql_cleanup.main --days 30

# 清理特定狀態的資料
python -m postgresql_cleanup.main --status failed,expired

# 詳細輸出
python -m postgresql_cleanup.main --verbose

# 將結果輸出到檔案
python -m postgresql_cleanup.main --output cleanup_results.json
```

### 組合使用

```bash
# 清理 podcast_metadata 表格中 60 天前且狀態為 failed 的資料
python -m postgresql_cleanup.main \
    --table podcast_metadata \
    --days 60 \
    --status failed \
    --verbose \
    --output results.json
```

## 清理策略

### 1. 本機測試資料清理
- **激進清理**: 清理包含測試關鍵字的記錄
- **關鍵字過濾**: test, testing, demo, sample, temp, temporary, draft
- **時間過濾**: 清理 1 天前的資料
- **狀態過濾**: 清理測試狀態的記錄

### 2. 生產環境清理
- **根據年齡**: 刪除超過指定天數的舊記錄
- **根據狀態**: 刪除特定狀態的記錄
- **表格優化**: 執行 `VACUUM ANALYZE` 操作

### 3. 表格優化
- 執行 `VACUUM ANALYZE` 操作
- 回收已刪除記錄佔用的空間
- 更新表格統計資訊

## 目標表格

預設會清理以下表格：

- `podcast_metadata` - 播客元資料
- `episode_metadata` - 集數元資料
- `transcript_metadata` - 轉錄元資料
- `embedding_metadata` - 嵌入向量元資料
- `processing_metadata` - 處理元資料

## 輸出格式

清理完成後會顯示詳細的統計資訊：

```
============================================================
本機 PostgreSQL 測試資料清理結果摘要
============================================================

表格: podcast_metadata
  - 根據年齡刪除: 150 筆
  - 根據狀態刪除: 25 筆
  - 總刪除數量: 175 筆
  - 初始大小: 45.67 MB
  - 最終大小: 42.15 MB
  - 節省空間: 3.52 MB

總計:
  - 總刪除記錄: 175 筆
  - 總節省空間: 3.52 MB
============================================================
```

## Episodes 資料處理

### 功能概述

Episodes 處理功能專門處理播客集數資料，包括：

- 🧹 **表情符號清理**: 移除標題和描述中的表情符號
- 🏷️ **HTML 標籤清理**: 移除 HTML 標籤和推廣文字
- 📅 **日期解析**: 解析並標準化發布日期
- 🔢 **集數提取**: 從標題中提取集數資訊
- 🗄️ **資料庫對應**: 將處理後的資料對應到 PostgreSQL 欄位

### 支援的頻道

- **商業頻道** (business): 頻道 ID 1304
- **教育頻道** (evucation): 頻道 ID 1321

### 快速開始

```bash
# 處理所有頻道，僅輸出檔案
./process_episodes.sh

# 處理商業頻道並插入資料庫
./process_episodes.sh -c business -d

# 處理教育頻道
./process_episodes.sh -c evucation

# 顯示統計資訊
./process_episodes.sh -s
```

### 詳細使用

```bash
# 使用 Python 腳本進行更精細的控制
python episode_processor.py --help

# 處理指定頻道
python episode_processor.py --channel business --output-dir processed_episodes

# 處理所有頻道並插入資料庫
python episode_processor.py --episodes-dir episodes --insert-db --verbose

# 僅處理並輸出檔案
python episode_processor.py --episodes-dir episodes --output-dir processed_episodes
```

### 測試功能

```bash
# 執行測試腳本
python test_episode_processing.py
```

### 資料庫表格結構

處理後的資料會插入到 `episode_metadata` 表格：

```sql
CREATE TABLE episode_metadata (
    id SERIAL PRIMARY KEY,
    episode_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    audio_url TEXT,
    published_date VARCHAR(100),
    published_timestamp TIMESTAMP,
    published_year INTEGER,
    published_month INTEGER,
    published_day INTEGER,
    channel_id VARCHAR(50) NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    episode_number VARCHAR(20),
    processed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 清理功能

- **表情符號清理**: 移除所有 Unicode 表情符號
- **HTML 標籤清理**: 移除 `<p>`, `<br />`, `<a>` 等標籤
- **推廣文字清理**: 移除 IG 連結、留言連結、Powered by 等文字
- **特殊字符清理**: 保留中文、英文、數字和基本標點符號
- **空白清理**: 清理多餘的空白和換行

### 輸出格式

處理完成後會產生以下檔案：

```
processed_episodes/
├── business_processed.json      # 商業頻道處理結果
├── evucation_processed.json     # 教育頻道處理結果
└── all_episodes_processed.json  # 所有頻道合併結果
```

### 統計資訊

處理完成後會顯示統計資訊：

```
=== 處理結果統計 ===
商業頻道: 5 筆
教育頻道: 20 筆
總計: 25 筆
```

## 工作流程

### 本機開發階段
1. **檢查資料庫狀態**: `./quick_cleanup.sh --check`
2. **試運行清理**: `./quick_cleanup.sh --dry-run`
3. **執行實際清理**: `./quick_cleanup.sh --cleanup`
4. **驗證清理結果**: 檢查清理報告
5. **準備上傳**: 確認資料庫已清理乾淨

### Kubernetes 部署階段
1. **建立 Docker 映像**: `./deploy.sh -b`
2. **部署到 K8s**: `./deploy.sh -d`
3. **驗證部署**: 檢查 CronJob 狀態
4. **監控執行**: 查看日誌和統計

## Kubernetes 部署說明

### 部署組件

1. **Namespace**: `podwise`
2. **ServiceAccount**: `postgresql-cleanup-sa`
3. **ConfigMap**: `postgresql-cleanup-config`
4. **Secret**: `postgresql-cleanup-secret`
5. **CronJob**: `postgresql-cleanup-cronjob`

### 排程設定

- **預設排程**: 每天凌晨 2 點執行
- **並發控制**: 禁止並發執行
- **歷史記錄**: 保留最近 3 次成功/失敗記錄

### 資源限制

- **記憶體請求**: 256Mi
- **CPU 請求**: 100m
- **記憶體限制**: 512Mi
- **CPU 限制**: 500m

## 安全注意事項

1. **備份資料**: 執行清理前請務必備份重要資料
2. **試運行**: 首次使用建議先執行 `--dry-run` 模式
3. **權限檢查**: 確保資料庫使用者有適當的刪除權限
4. **監控日誌**: 定期檢查清理日誌檔案
5. **K8s 安全**: 使用最小權限原則的 ServiceAccount

## 錯誤處理

常見錯誤及解決方案：

- **連線失敗**: 檢查 PostgreSQL Service 名稱和 namespace
- **權限不足**: 確認資料庫使用者 `bdse37` 權限
- **表格不存在**: 檢查表格名稱是否正確
- **鎖定衝突**: 避免在業務高峰期執行清理
- **K8s 問題**: 檢查 Pod 狀態和日誌

## 監控與維護

### 檢查 CronJob 狀態

```bash
kubectl get cronjobs -n podwise
kubectl describe cronjob postgresql-cleanup-cronjob -n podwise
```

### 查看執行歷史

```bash
kubectl get jobs -n podwise -l app=postgresql-cleanup
kubectl logs job/manual-cleanup-xxxxx -n podwise
```

### 更新配置

```bash
# 更新 ConfigMap
kubectl patch configmap postgresql-cleanup-config -n podwise --patch-file config-patch.yaml

# 重新部署 CronJob
kubectl rollout restart cronjob/postgresql-cleanup-cronjob -n podwise
```

## 開發

### 專案結構

```
postgresql_cleanup/
├── __init__.py              # 模組初始化
├── config.py               # 配置管理
├── cleanup_service.py      # 核心清理服務
├── main.py                # 主執行腳本
├── local_cleanup.py       # 本機清理腳本
├── requirements.txt       # 依賴套件
├── k8s_deployment.yaml   # Kubernetes 部署配置
├── Dockerfile            # Docker 映像建置檔案
├── deploy.sh             # 自動化部署腳本
├── quick_cleanup.sh      # 快速清理腳本
├── test_cleanup.py       # 單元測試
└── README.md             # 說明文件
```

### 擴展功能

如需新增清理功能，可以：

1. 在 `cleanup_service.py` 中新增方法
2. 在 `config.py` 中新增配置選項
3. 在 `main.py` 中新增命令列參數
4. 更新 `k8s_deployment.yaml` 中的環境變數

## 授權

此專案遵循 MIT 授權條款。 