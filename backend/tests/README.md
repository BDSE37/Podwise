# Podwise 測試資料匯入程式

這個程式用於將 testdata 目錄下的 CSV 檔案資料匯入到 PostgreSQL 資料庫中。

## 功能特色

- 🔄 **自動資料處理**: 自動處理 CSV 檔案中的日期格式和資料類型轉換
- 👤 **使用者管理**: 自動創建不存在的使用者記錄
- 📺 **節目集數管理**: 自動創建不存在的節目集數記錄
- 🔄 **重複資料處理**: 支援更新現有記錄或插入新記錄
- 📊 **批次處理**: 每 100 筆資料自動提交，提升效能
- 📝 **詳細日誌**: 完整的執行日誌記錄
- ⚙️ **彈性配置**: 支援命令列參數配置

## 檔案結構

```
testdata/
├── data_importer.py          # 主要匯入程式
├── requirements.txt          # Python 依賴套件
├── run_import.sh            # 執行腳本
├── README.md                # 說明文件
├── user_feedback.csv        # 使用者回饋資料
├── episode_likes.csv        # 節目集數按讚統計
├── episode_plays.csv        # 節目集數播放統計
├── user_episode_counts.csv  # 使用者節目集數統計
└── podcast_stats.py         # 統計資料生成腳本
```

## 資料庫表格對應

### user_feedback 表格
- `User_id` → `user_id` (自動創建使用者)
- `Episode_id` → `episode_id` (自動創建節目集數)
- `preview_played_at` → `preview_played_at`
- `like_count` → `like_count`
- `preview_play_count` → `preview_play_count`
- `created_at` → `created_at`

### episodes 表格
- 從 `episode_likes.csv` 和 `episode_plays.csv` 更新統計資訊

## 安裝與設定

### 1. 安裝依賴套件

```bash
pip3 install -r requirements.txt
```

### 2. 確認資料庫連線

確保 PostgreSQL 資料庫正在運行，並且可以使用以下連線資訊：
- 主機: localhost
- 埠號: 5432
- 資料庫: podcast
- 使用者: bdse37
- 密碼: 111111

### 3. 執行資料匯入

#### 方法一：使用執行腳本（推薦）

```bash
chmod +x run_import.sh
./run_import.sh
```

#### 方法二：直接執行 Python 程式

```bash
python3 data_importer.py --data-dir .
```

## 命令列參數

```bash
python3 data_importer.py [選項]

選項:
  --host HOST              資料庫主機 (預設: localhost)
  --port PORT              資料庫埠號 (預設: 5432)
  --database DATABASE      資料庫名稱 (預設: podcast)
  --username USERNAME      資料庫使用者名稱 (預設: bdse37)
  --password PASSWORD      資料庫密碼 (預設: 111111)
  --data-dir DATA_DIR      測試資料目錄路徑 (預設: .)
  --skip-user-feedback     跳過使用者回饋資料匯入
  --skip-episode-stats     跳過節目集數統計資料匯入
  --skip-user-counts       跳過使用者統計資料匯入
  -h, --help               顯示說明訊息
```

## 使用範例

### 匯入所有資料
```bash
python3 data_importer.py
```

### 只匯入使用者回饋資料
```bash
python3 data_importer.py --skip-episode-stats --skip-user-counts
```

### 使用自訂資料庫連線
```bash
python3 data_importer.py --host 192.168.1.100 --port 5433 --username myuser --password mypass
```

### 指定資料目錄
```bash
python3 data_importer.py --data-dir /path/to/testdata
```

## 日誌檔案

程式執行時會產生以下日誌檔案：
- `data_import.log`: 詳細的執行日誌
- 控制台輸出: 即時執行狀態

## 錯誤處理

程式包含完整的錯誤處理機制：
- 🔄 **自動回滾**: 發生錯誤時自動回滾交易
- 📝 **詳細錯誤訊息**: 記錄具體的錯誤原因
- ⏭️ **跳過錯誤記錄**: 單筆資料錯誤不影響整體匯入
- 📊 **統計報告**: 顯示成功和失敗的筆數

## 注意事項

1. **資料庫權限**: 確保資料庫使用者有足夠的 INSERT 和 UPDATE 權限
2. **磁碟空間**: 大量資料匯入時確保有足夠的磁碟空間
3. **記憶體使用**: 程式會分批處理資料，避免記憶體不足
4. **備份建議**: 匯入前建議先備份資料庫
5. **重複執行**: 程式支援重複執行，會更新現有記錄

## 故障排除

### 常見問題

1. **資料庫連線失敗**
   - 檢查 PostgreSQL 服務是否運行
   - 確認連線參數是否正確
   - 檢查防火牆設定

2. **權限錯誤**
   - 確認資料庫使用者權限
   - 檢查表格是否存在

3. **編碼問題**
   - 確保 CSV 檔案使用 UTF-8 編碼
   - 檢查資料庫字元集設定

4. **記憶體不足**
   - 減少批次大小
   - 分批執行不同類型的資料

## 開發者資訊

- **程式語言**: Python 3.7+
- **資料庫**: PostgreSQL 12+
- **主要套件**: pandas, psycopg2
- **架構模式**: OOP 物件導向程式設計
- **日誌系統**: Python logging 模組

## 授權

本程式為 Podwise 專案的一部分，遵循專案授權條款。 