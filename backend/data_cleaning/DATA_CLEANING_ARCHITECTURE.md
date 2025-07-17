# Data Cleaning 模組架構文檔

## 📋 整理概述

本次整理遵循 OOP 設計原則，消除了重複功能，統一了對外接口，確保每個模組都可以以 OOP 形式被調用。

## 🗂️ 刪除的重複檔案

### 根目錄重複檔案
- `batch_clean_folder.py` - 功能整合到 `UnifiedCleaner.batch_clean_files()`
- `check_data_structure.py` - 功能整合到 `scripts/detailed_db_inspection.py`
- `quick_clean_emoji.py` - 功能整合到 `UnifiedCleaner.quick_clean_emoji_from_folder()`
- `check_exception_file.py` - 功能重複，已刪除

### Scripts 目錄重複檔案
- `batch_upload_to_postgres.py` - 保留 `safe_batch_upload.py`（最完整）
- `improved_safe_upload.py` - 功能重複，已刪除
- `robust_upload.py` - 功能重複，已刪除
- `safe_upload_with_structure.py` - 功能重複，已刪除
- `auto_sync_batch_input_to_db.py` - 功能重複，已刪除
- `check_and_fix_db_structure.py` - 保留 `detailed_db_inspection.py`（最完整）
- `check_mapping_and_duplicates.py` - 功能重複，已刪除
- `check_orphan_episodes.py` - 功能重複，已刪除
- `check_spotify_rss_mapping.py` - 功能重複，已刪除
- `check_table_structure.py` - 功能重複，已刪除
- `fixed_mapping_check.py` - 功能重複，已刪除
- `verify_upload_results.py` - 功能重複，已刪除
- `progress_monitor.py` - 功能重複，已刪除
- `orphan_episodes_report.txt` - 臨時檔案，已刪除

### Database 目錄重複檔案
- `batch_inserter.py` - 功能重複，已刪除

## 🏗️ 整理後的架構

### 目錄結構
```
data_cleaning/
├── __init__.py                    # 統一對外接口（工廠模式 + 管理器模式）
├── main.py                        # 命令列工具（統一入口點）
├── README.md                      # 模組文檔
├── DATA_CLEANING_ARCHITECTURE.md  # 架構文檔
├── core/                          # 核心清理器
│   ├── __init__.py               # 核心模組匯出
│   ├── base_cleaner.py           # 基底清理器（抽象類別）
│   ├── unified_cleaner.py        # 統一清理器（主要接口）
│   ├── mongo_cleaner.py          # MongoDB 清理器
│   ├── longtext_cleaner.py       # 長文本清理器
│   ├── episode_cleaner.py        # Episode 清理器
│   ├── podcast_cleaner.py        # Podcast 清理器
│   └── youtube_cleaner.py        # YouTube 清理器
├── services/                      # 服務層
│   ├── __init__.py               # 服務模組匯出
│   ├── cleaner_orchestrator.py   # 清理協調器
│   └── cleanup_service.py        # 清理服務
├── utils/                         # 工具類
│   ├── __init__.py               # 工具模組匯出
│   ├── data_extractor.py         # 資料提取器
│   ├── db_utils.py               # 資料庫工具
│   └── file_format_detector.py   # 檔案格式檢測器
├── config/                        # 配置管理
│   ├── __init__.py               # 配置模組匯出
│   └── config.py                 # 配置類別
├── database/                      # 資料庫操作
│   ├── __init__.py               # 資料庫模組匯出
│   └── postgresql_inserter.py    # PostgreSQL 插入器
├── scripts/                       # 實用腳本（保留最完整的）
│   ├── safe_batch_upload.py      # 安全批次上傳
│   └── detailed_db_inspection.py # 詳細資料庫檢查
└── stock_cancer/                  # 股癌特殊處理（例外）
    ├── __init__.py               # 股癌模組匯出
    ├── stock_cancer_cleaner.py   # 股癌清理器
    ├── clean_stock_cancer_exception.py # 股癌例外處理
    └── process_stock_cancer.py   # 股癌處理腳本
```

## 🎯 OOP 設計模式

### 1. 工廠模式 (Factory Pattern)
```python
from data_cleaning import DataCleaningFactory

factory = DataCleaningFactory()
cleaner = factory.create_cleaner('episode')
```

### 2. 策略模式 (Strategy Pattern)
```python
# 所有清理器實現相同的 BaseCleaner 介面
cleaners = {
    'episode': EpisodeCleaner,
    'podcast': PodcastCleaner,
    'mongo': MongoCleaner,
    'longtext': LongTextCleaner,
    'stock_cancer': StockCancerCleaner,
    'unified': UnifiedCleaner,
}
```

### 3. 協調器模式 (Orchestrator Pattern)
```python
from data_cleaning.services import CleanerOrchestrator

orchestrator = CleanerOrchestrator()
output_path = orchestrator.clean_file("input.json")
```

### 4. 模板方法模式 (Template Method Pattern)
```python
class BaseCleaner:
    def clean(self, data):
        # 定義清理流程
        pass
```

## 🔧 統一對外接口

### 1. 主要接口類別
- `UnifiedCleaner`: 統一清理器，整合所有功能
- `DataCleaningFactory`: 工廠類別，統一建立清理器
- `DataCleaningManager`: 管理器類別，提供高層級管理

### 2. 命令列接口
```bash
# 統一通過 main.py 提供所有功能
python backend/data_cleaning/main.py --help
```

### 3. 程式碼接口
```python
# 方式 1: 直接使用統一清理器
from data_cleaning import UnifiedCleaner
cleaner = UnifiedCleaner()

# 方式 2: 使用工廠模式
from data_cleaning import DataCleaningFactory
factory = DataCleaningFactory()
cleaner = factory.create_cleaner('episode')

# 方式 3: 使用管理器模式
from data_cleaning import DataCleaningManager
manager = DataCleaningManager()
```

## 📊 功能整合

### 1. 批次處理整合
- 原 `batch_clean_folder.py` → `UnifiedCleaner.batch_clean_files()`
- 原 `quick_clean_emoji.py` → `UnifiedCleaner.quick_clean_emoji_from_folder()`

### 2. 檢查功能整合
- 多個檢查腳本 → `scripts/detailed_db_inspection.py`（最完整）

### 3. 資料庫上傳整合
- 多個上傳腳本 → `scripts/safe_batch_upload.py`（最完整）

### 4. 配置管理整合
- 統一配置管理 → `config/config.py`

## 🎯 設計原則遵循

### 1. 單一職責原則 (SRP)
- 每個清理器只負責一種類型的資料清理
- 每個服務只負責特定的功能領域

### 2. 開放封閉原則 (OCP)
- 可以新增清理器而不修改現有程式碼
- 通過繼承 `BaseCleaner` 擴展功能

### 3. 里氏替換原則 (LSP)
- 所有清理器都可以替換 `BaseCleaner`
- 保持介面一致性

### 4. 介面隔離原則 (ISP)
- 每個介面都有明確的職責
- 避免不必要的依賴

### 5. 依賴倒置原則 (DIP)
- 依賴抽象而非具體實現
- 通過工廠模式解耦

## 🔄 使用流程

### 1. 基本使用
```python
from data_cleaning import UnifiedCleaner

cleaner = UnifiedCleaner()
cleaned_data = cleaner.clean(data)
```

### 2. 批次處理
```python
# 批次清理檔案
cleaned_files = cleaner.batch_clean_files(["file1.json", "file2.json"])

# 快速清理表情符號
stats = cleaner.quick_clean_emoji_from_folder("source", "target")
```

### 3. 命令列使用
```bash
# 批次清理
python main.py --batch-clean --input-folder input --output-folder output

# 快速清理表情符號
python main.py --quick-clean-emoji --source-dir source --target-dir target
```

## ✅ 整理成果

### 1. 消除重複
- 刪除了 15+ 個重複檔案
- 整合了相似功能
- 統一了程式碼風格

### 2. 統一接口
- 提供統一的 `main.py` 入口點
- 統一的 OOP 接口設計
- 一致的錯誤處理

### 3. 改善維護性
- 清晰的模組結構
- 完整的文檔說明
- 標準化的命名規範

### 4. 提升可擴展性
- 工廠模式支援新增清理器
- 模板方法模式支援擴展
- 配置驅動的設計

## 🚀 後續建議

### 1. 測試覆蓋
- 為每個清理器添加單元測試
- 添加整合測試
- 添加效能測試

### 2. 效能優化
- 批次處理支援並行
- 記憶體使用優化
- 快取機制

### 3. 監控日誌
- 統一的日誌格式
- 效能監控
- 錯誤追蹤

### 4. 文檔完善
- API 文檔
- 使用範例
- 故障排除指南 