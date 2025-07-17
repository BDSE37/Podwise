# Data Cleaning 模組

## 📋 概述

Data Cleaning 模組提供完整的資料清理功能，專門處理 podcast 相關的文本資料，包括 MongoDB 文檔、PostgreSQL 資料和一般文本清理。採用 OOP 設計原則，提供統一的對外接口。

## 🎯 功能特色

- **統一清理器**: 整合所有清理功能，提供統一的 OOP 介面
- **MongoDB 文檔清理**: 專門處理 MongoDB 中的 podcast 文檔
- **股癌節目清理**: 針對股癌節目的特殊清理邏輯（保留在 stock_cancer 資料夾）
- **長文本清理**: 處理長文本內容的清理
- **PostgreSQL 資料清理**: 清理和轉換 PostgreSQL 資料
- **批次處理**: 支援批次清理指定資料夾下所有檔案
- **多格式輸出**: 支援 JSON、CSV 等輸出格式
- **JSON 格式修正**: 自動修正 JSON 檔案格式
- **檔案名稱清理**: 清理檔案名稱中的特殊字元
- **快速表情符號清理**: 專門用於清理 comment_data 中的表情符號

## 🏗️ 架構設計

### OOP 設計原則

- 所有清理器皆繼承自 `BaseCleaner`，符合物件導向設計，易於擴充與維護
- 各清理器（如 `MongoCleaner`, `StockCancerCleaner`, `LongTextCleaner`, `EpisodeCleaner`, `PodcastCleaner`）皆封裝單一責任
- `CleanerOrchestrator` 統一調度各清理器，實現高內聚、低耦合
- `UnifiedCleaner` 提供統一的對外接口，整合所有清理功能
- 批次處理與遞迴掃描皆以函式封裝，符合 Google Clean Code 原則

### 模組結構

```
data_cleaning/
├── __init__.py              # 統一對外接口
├── main.py                  # 命令列工具
├── README.md               # 模組文檔
├── core/                   # 核心清理器
│   ├── base_cleaner.py     # 基底清理器
│   ├── unified_cleaner.py  # 統一清理器
│   ├── mongo_cleaner.py    # MongoDB 清理器
│   ├── longtext_cleaner.py # 長文本清理器
│   ├── episode_cleaner.py  # Episode 清理器
│   ├── podcast_cleaner.py  # Podcast 清理器
│   └── youtube_cleaner.py  # YouTube 清理器
├── services/               # 服務層
│   ├── cleaner_orchestrator.py # 清理協調器
│   └── cleanup_service.py      # 清理服務
├── utils/                  # 工具類
│   ├── data_extractor.py   # 資料提取器
│   ├── db_utils.py         # 資料庫工具
│   └── file_format_detector.py # 檔案格式檢測器
├── config/                 # 配置管理
│   └── config.py           # 配置類別
├── database/               # 資料庫操作
│   └── postgresql_inserter.py # PostgreSQL 插入器
├── scripts/                # 實用腳本
│   ├── safe_batch_upload.py    # 安全批次上傳
│   └── detailed_db_inspection.py # 詳細資料庫檢查
└── stock_cancer/           # 股癌特殊處理（例外）
    └── stock_cancer_cleaner.py # 股癌清理器
```

## 🚀 快速開始

### 1. 統一清理器（推薦）

```python
from data_cleaning import UnifiedCleaner

# 建立統一清理器
cleaner = UnifiedCleaner()

# 清理文本
cleaned_text = cleaner.clean_text("Hello 😊 World :)")

# 清理檔案
cleaned_file = cleaner.clean_file("input.json")

# 批次清理
cleaned_files = cleaner.batch_clean_files(["file1.json", "file2.json"])

# 修正 JSON 格式
fixed_count = cleaner.batch_fix_json_format("directory/")

# 快速清理表情符號
stats = cleaner.quick_clean_emoji_from_folder("comment_data", "cleaned_data")
```

### 2. 工廠模式

```python
from data_cleaning import DataCleaningFactory

# 建立工廠
factory = DataCleaningFactory()

# 建立特定清理器
episode_cleaner = factory.create_cleaner('episode')
podcast_cleaner = factory.create_cleaner('podcast')
stock_cleaner = factory.create_cleaner('stock_cancer')

# 清理資料
cleaned_episode = episode_cleaner.clean(episode_data)
cleaned_podcast = podcast_cleaner.clean(podcast_data)
cleaned_stock = stock_cleaner.clean(stock_data)
```

### 3. 管理器模式

```python
from data_cleaning import DataCleaningManager

# 建立管理器
manager = DataCleaningManager()

# 清理各種資料
cleaned_episode = manager.clean_episode_data(episode_data)
cleaned_podcast = manager.clean_podcast_data(podcast_data)
cleaned_stock = manager.clean_stock_cancer_data(stock_data)

# 批次處理
cleaned_files = manager.batch_clean_files(["file1.json", "file2.json"])
```

### 4. 命令列工具

```bash
# 列出所有清理器
python backend/data_cleaning/main.py --list-cleaners

# 測試清理器
python backend/data_cleaning/main.py --test-cleaners

# 清理單個檔案
python backend/data_cleaning/main.py --clean --input data.json --output cleaned_data.json

# 批次清理資料夾
python backend/data_cleaning/main.py --batch-clean --input-folder batch_input --output-folder cleaned_data

# 快速清理表情符號
python backend/data_cleaning/main.py --quick-clean-emoji --source-dir comment_data --target-dir cleaned_comment_data

# 處理股癌資料
python backend/data_cleaning/main.py --process-stock-cancer --input stock_cancer.json

# 處理股癌資料並匯入 PostgreSQL
python backend/data_cleaning/main.py --process-stock-cancer --input stock_cancer.json --import-postgresql

# 匯入 PostgreSQL
python backend/data_cleaning/main.py --import-postgresql --input cleaned_data.json

# 執行服務測試
python backend/data_cleaning/main.py --service-test local --sample-size 50
python backend/data_cleaning/main.py --service-test database --sample-size 50
python backend/data_cleaning/main.py --service-test full --sample-size 50
```

## 🎯 設計原則

### 乾淨程式碼原則
- 所有清理器皆以單一職責原則（SRP）設計
- 無多餘全域變數，所有狀態皆以物件屬性封裝
- 批次處理、遞迴掃描、檔案過濾皆以獨立函式實作
- 變數命名清楚、無魔法數字、無重複程式碼
- 例外處理明確，錯誤訊息具體

### OOP 設計模式
- **工廠模式**: `DataCleaningFactory` 統一建立清理器
- **策略模式**: 不同清理器實現相同介面
- **協調器模式**: `CleanerOrchestrator` 統一調度
- **單例模式**: 配置和服務管理器
- **模板方法模式**: `BaseCleaner` 定義清理流程

## 📁 檔案管理

### 批次處理流程

```
指定資料夾 → 自動選擇清理器 → 執行清理 → 驗證結果 → 輸出清理後資料
```

### 支援的檔案格式
- **輸入**: JSON, CSV, TXT
- **輸出**: JSON (預設), CSV (可配置)

### 檔案命名規則
- 清理後的檔案會自動重命名，移除特殊字元
- 支援自定義輸出目錄
- 保留原始檔案，生成新的清理檔案

## ⚠️ 注意事項

- 請將所有要清理的資料放入指定資料夾
- 執行批次清理腳本即可自動處理所有檔案
- 清理結果會自動輸出到指定資料夾 
- 請刪除所有 .DS_Store、__pycache__、._*、暫存檔案等與主程式無關之檔案
- 保留所有核心清理模組和 stock_cancer 特殊處理模組
- 所有功能都通過統一的 `main.py` 接口提供

## 🔧 配置管理

### 環境變數
- 資料庫連接配置
- 清理參數配置
- 輸出目錄配置

### 自定義配置
```python
config = {
    "enable_emoji_removal": True,
    "enable_html_removal": True,
    "enable_special_char_removal": True,
    "enable_json_format_fix": True,
    "enable_filename_cleaning": True,
    "preserve_urls": True,
    "max_filename_length": 100
}

cleaner = UnifiedCleaner(config)
```

## 📈 效能優化

- 批次處理支援並行處理
- 記憶體使用優化
- 錯誤處理和重試機制
- 進度監控和日誌記錄 