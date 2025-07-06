# Data Cleaning 模組

## 功能概述

Data Cleaning 模組提供完整的資料清理功能，專門處理 podcast 相關的文本資料，包括 MongoDB 文檔、PostgreSQL 資料和一般文本清理。

### 主要功能

- **MongoDB 文檔清理**: 專門處理 MongoDB 中的 podcast 文檔
- **股癌節目清理**: 針對股癌節目的特殊清理邏輯
- **長文本清理**: 處理長文本內容的清理
- **PostgreSQL 資料清理**: 清理和轉換 PostgreSQL 資料
- **批次處理**: 支援大量資料的批次清理
- **多格式輸出**: 支援 JSON、CSV 等輸出格式

## 架構設計

### 核心組件

- **BaseCleaner**: 清理器抽象基類
- **MongoCleaner**: MongoDB 文檔清理器
- **StockCancerCleaner**: 股癌節目專用清理器
- **LongTextCleaner**: 長文本清理器
- **EpisodeCleaner**: Episode 資料清理器
- **PodcastCleaner**: Podcast 資料清理器
- **CleanerOrchestrator**: 清理協調器
- **CleanupService**: 清理服務

### 清理流程

```
原始資料 → 格式檢測 → 選擇清理器 → 執行清理 → 驗證結果 → 輸出清理後資料
```

## 使用方法

### 1. 基本使用

```python
from data_cleaning.core import MongoCleaner, StockCancerCleaner

# MongoDB 清理器
mongo_cleaner = MongoCleaner()
cleaned_doc = mongo_cleaner.clean(mongo_document)

# 股癌節目清理器
stock_cancer_cleaner = StockCancerCleaner()
cleaned_data = stock_cancer_cleaner.clean(stock_cancer_data)
```

### 2. 清理協調器

```python
from data_cleaning.services import CleanerOrchestrator

# 初始化協調器
orchestrator = CleanerOrchestrator()

# 清理檔案
cleaned_file = orchestrator.clean_file("input.json")

# 批次清理
cleaned_files = orchestrator.batch_clean_files(["file1.json", "file2.json"])
```

### 3. 清理服務

```python
from data_cleaning.services import CleanupService
from data_cleaning.config import Config

# 初始化配置
config = Config()

# 初始化服務
service = CleanupService(config)

# 執行本地測試
result = service.run_local_test(sample_size=100)

# 執行完整清理測試
result = service.run_full_cleanup_test()
```

### 4. 命令列使用

```bash
# 列出所有清理器
python main.py --list-cleaners

# 測試清理器
python main.py --test-cleaners

# 清理資料
python main.py --clean-data input.json output.json

# 處理股癌資料
python main.py --process-stock-cancer input.json

# 匯入 PostgreSQL
python main.py --import-postgresql cleaned_data.json
```

## 清理器說明

### MongoCleaner

專門處理 MongoDB 文檔的清理器：

```python
from data_cleaning.core import MongoCleaner

cleaner = MongoCleaner()

# 清理單個文檔
cleaned_doc = cleaner.clean(mongo_document)

# 批次清理
cleaned_docs = cleaner.batch_clean_documents(documents)

# 清理整個 collection
result = cleaner.clean_collection_data(collection_data, "collection_name")
```

**清理功能**：
- 文本欄位清理
- 標題清理
- 檔案名稱清理
- 移除表情符號和特殊字元
- 標準化格式

### StockCancerCleaner

股癌節目專用清理器：

```python
from data_cleaning.core import StockCancerCleaner

cleaner = StockCancerCleaner()

# 清理股癌資料
cleaned_data = cleaner.clean(stock_cancer_data)

# 批次清理
cleaned_docs = cleaner.batch_clean_documents(documents)

# 清理整個 collection
result = cleaner.clean_stock_cancer_collection(collection_data)
```

**特殊處理**：
- 移除表情符號和 kaomoji
- 統一標題格式為 `EPxxx_股癌`
- 提取集數資訊
- 特殊字符處理
- 檔案名稱清理

### LongTextCleaner

長文本清理器：

```python
from data_cleaning.core import LongTextCleaner

cleaner = LongTextCleaner()

# 清理長文本
cleaned_text = cleaner.clean(long_text)
```

**清理功能**：
- 移除表情符號
- 移除 kaomoji
- 移除 HTML 標籤
- 移除特殊字元
- 標準化空白字元

## 配置選項

### 資料庫配置

```python
from data_cleaning.config import Config

config = Config()

# 獲取資料庫配置
db_config = config.get_db_config()

# 獲取測試配置
test_config = config.get_test_config()
```

### 測試配置

```python
# 測試資料設定
test_config = {
    "backup_file": "episodes_backup_20250706_163501.sql",
    "test_output_dir": "../../data/cleaned_data",
    "sample_size": 100
}
```

## 資料格式

### 輸入格式

支援多種輸入格式：

- **JSON**: MongoDB 文檔格式
- **CSV**: 表格資料格式
- **SQL**: PostgreSQL 備份檔案

### 輸出格式

- **JSON**: 清理後的文檔
- **CSV**: 表格格式輸出
- **SQL**: PostgreSQL 插入語句

## 錯誤處理

### 錯誤記錄

```python
# 清理器會自動記錄錯誤
cleaned_doc = cleaner.clean(doc)

if cleaned_doc.get('cleaning_status') == 'error':
    error_message = cleaned_doc.get('error_message')
    print(f"清理失敗: {error_message}")
```

### 批次處理錯誤

```python
# 批次處理時會跳過錯誤的文檔
cleaned_docs = cleaner.batch_clean_documents(documents)

# 統計結果
success_count = len([doc for doc in cleaned_docs if doc.get('cleaning_status') == 'completed'])
error_count = len(cleaned_docs) - success_count
```

## 效能優化

### 批次處理

```python
# 使用批次處理提高效能
cleaned_docs = cleaner.batch_clean_documents(documents, batch_size=100)
```

### 記憶體管理

```python
# 使用生成器處理大量資料
def process_large_file(file_path):
    for chunk in read_file_in_chunks(file_path):
        cleaned_chunk = cleaner.clean(chunk)
        yield cleaned_chunk
```

## 依賴項目

- pandas
- numpy
- pymongo
- psycopg2-binary
- sqlalchemy
- python-dotenv

## 注意事項

- 確保輸入資料格式正確
- 大量資料處理時建議使用批次處理
- 股癌節目清理器需要特定的資料格式
- 清理結果會自動驗證
- 錯誤會記錄在清理狀態中 