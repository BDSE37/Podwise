# Data Cleaning 模組

## 📋 概述

Data Cleaning 模組提供完整的資料清理功能，專門處理 podcast 相關的文本資料，包括 MongoDB 文檔、PostgreSQL 資料和一般文本清理。

## 🎯 功能特色

- **統一清理器**: 整合所有清理功能，提供統一的 OOP 介面
- **MongoDB 文檔清理**: 專門處理 MongoDB 中的 podcast 文檔
- **股癌節目清理**: 針對股癌節目的特殊清理邏輯
- **長文本清理**: 處理長文本內容的清理
- **PostgreSQL 資料清理**: 清理和轉換 PostgreSQL 資料
- **批次處理**: 支援遞迴批次清理指定資料夾下所有檔案與子資料夾
- **多格式輸出**: 支援 JSON、CSV 等輸出格式
- **JSON 格式修正**: 自動修正 JSON 檔案格式
- **檔案名稱清理**: 清理檔案名稱中的特殊字元

## 🏗️ 架構設計

### OOP 設計原則

- 所有清理器皆繼承自 `BaseCleaner`，符合物件導向設計，易於擴充與維護。
- 各清理器（如 `MongoCleaner`, `StockCancerCleaner`, `LongTextCleaner`, `EpisodeCleaner`, `PodcastCleaner`）皆封裝單一責任。
- `CleanerOrchestrator` 統一調度各清理器，實現高內聚、低耦合。
- 批次處理與遞迴掃描皆以函式封裝，符合 Google Clean Code 原則。

### 批次清理流程

```
指定資料夾 → 遞迴尋找所有支援檔案 → 自動選擇清理器 → 執行清理 → 驗證結果 → 輸出清理後資料
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
```

### 2. 單一檔案清理

```python
from data_cleaning.services import CleanerOrchestrator
orchestrator = CleanerOrchestrator()
output_path = orchestrator.clean_file("input.json")
```

### 3. 批次清理指定資料夾（推薦）

```bash
# 將所有要清理的檔案放到 backend/data_cleaning/batch_input
python backend/data_cleaning/batch_clean_folder.py --input-folder backend/data_cleaning/batch_input
# 可加 --output-folder 指定輸出資料夾
```

- 支援遞迴處理 batch_input 及其所有子資料夾下的 .json/.csv/.txt 檔案
- 清理結果統一輸出到 ../../data/cleaned_data

## 🎯 設計原則

### 乾淨程式碼原則
- 所有清理器皆以單一職責原則（SRP）設計
- 無多餘全域變數，所有狀態皆以物件屬性封裝
- 批次處理、遞迴掃描、檔案過濾皆以獨立函式實作
- 變數命名清楚、無魔法數字、無重複程式碼
- 例外處理明確，錯誤訊息具體

## ⚠️ 注意事項

- 請將所有要清理的資料放入 batch_input 或自訂資料夾
- 執行批次清理腳本即可自動遞迴處理所有檔案
- 清理結果會自動輸出到指定資料夾 
- 請刪除所有 .DS_Store、__pycache__、._*、暫存檔案等與主程式無關之檔案
- 保留 batch_clean_folder.py、batch_input/ 及所有核心清理模組 