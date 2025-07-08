# Data Cleaning 模組

## 功能概述

Data Cleaning 模組提供完整的資料清理功能，專門處理 podcast 相關的文本資料，包括 MongoDB 文檔、PostgreSQL 資料和一般文本清理。

### 主要功能

- **MongoDB 文檔清理**: 專門處理 MongoDB 中的 podcast 文檔
- **股癌節目清理**: 針對股癌節目的特殊清理邏輯
- **長文本清理**: 處理長文本內容的清理
- **PostgreSQL 資料清理**: 清理和轉換 PostgreSQL 資料
- **批次處理**: 支援遞迴批次清理指定資料夾下所有檔案與子資料夾
- **多格式輸出**: 支援 JSON、CSV 等輸出格式

## 架構設計

### OOP 設計原則

- 所有清理器皆繼承自 `BaseCleaner`，符合物件導向設計，易於擴充與維護。
- 各清理器（如 `MongoCleaner`, `StockCancerCleaner`, `LongTextCleaner`, `EpisodeCleaner`, `PodcastCleaner`）皆封裝單一責任。
- `CleanerOrchestrator` 統一調度各清理器，實現高內聚、低耦合。
- 批次處理與遞迴掃描皆以函式封裝，符合 Google Clean Code 原則。

### 批次清理流程

```
指定資料夾 → 遞迴尋找所有支援檔案 → 自動選擇清理器 → 執行清理 → 驗證結果 → 輸出清理後資料
```

## 使用方法

### 1. 單一檔案清理

```python
from data_cleaning.services import CleanerOrchestrator
orchestrator = CleanerOrchestrator()
output_path = orchestrator.clean_file("input.json")
```

### 2. 批次清理指定資料夾（推薦）

```bash
# 將所有要清理的檔案放到 backend/data_cleaning/batch_input
python backend/data_cleaning/batch_clean_folder.py --input-folder backend/data_cleaning/batch_input
# 可加 --output-folder 指定輸出資料夾
```
- 支援遞迴處理 batch_input 及其所有子資料夾下的 .json/.csv/.txt 檔案
- 清理結果統一輸出到 ../../data/cleaned_data

### 3. 其他清理器用法

（略，保留原有各清理器的單一檔案與批次清理範例）

## 乾淨程式碼原則

- 所有清理器皆以單一職責原則（SRP）設計
- 無多餘全域變數，所有狀態皆以物件屬性封裝
- 批次處理、遞迴掃描、檔案過濾皆以獨立函式實作
- 變數命名清楚、無魔法數字、無重複程式碼
- 例外處理明確，錯誤訊息具體

## 不必要檔案清單

- 請刪除所有 .DS_Store、__pycache__、._*、暫存檔案等與主程式無關之檔案
- 保留 batch_clean_folder.py、batch_input/ 及所有核心清理模組

## 注意事項

- 請將所有要清理的資料放入 batch_input 或自訂資料夾
- 執行批次清理腳本即可自動遞迴處理所有檔案
- 清理結果會自動輸出到指定資料夾 