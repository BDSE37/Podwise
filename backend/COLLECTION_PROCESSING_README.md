# 播客資料處理管線說明文件

## 概述

這個管線用於處理 MongoDB collection 中的播客長文本資料，包含以下功能：

1. **文本清理**：移除表情符號和特殊字元
2. **文本切分**：將長文本切分為適當大小的 chunks
3. **智能標籤**：基於 TAG_info.csv 進行標籤匹配，如果沒有匹配則使用智能標籤系統
4. **向量化**：生成文本嵌入向量
5. **資料儲存**：將處理後的資料儲存到 Milvus 向量資料庫
6. **錯誤處理**：完整的錯誤記錄和處理機制
7. **標題更新**：批次更新節目標題為指定格式

## 檔案結構

```
backend/
├── process_collections.py          # 主要處理腳本
├── test_collection_processing.py   # 測試腳本
├── run_collection_processing.sh    # 執行腳本
├── collection_processing_config.json # 配置檔案
├── TAG_info.csv                   # 標籤定義檔案
├── vector_pipeline/
│   └── error_logger.py            # 錯誤記錄器
└── rag_pipeline/
    └── utils/
        └── tag_processor.py       # 標籤處理器
```

## 功能特色

### 1. 文本清理 (TextCleaner)

- **表情符號移除**：使用 emoji 套件移除所有表情符號
- **特殊字元清理**：移除顏文字和特殊字元，保留中文、英文、數字和基本標點
- **空白處理**：移除多餘的空白字元
- **標題清理**：專門的標題清理功能

### 2. 智能標籤系統

- **多層次標籤提取**：
  1. 基於 TAG_info.csv 的標籤匹配
  2. 智能關鍵字匹配
  3. 備援標籤系統
- **標籤驗證**：確保標籤品質和相關性
- **數量限制**：最多 3 個標籤

### 3. 錯誤處理機制

- **詳細錯誤記錄**：記錄錯誤的 collection、rssID、title 和錯誤原因
- **錯誤分類**：不同類型的錯誤分類處理
- **錯誤報告**：生成詳細的錯誤報告
- **繼續處理**：錯誤不影響其他文件的處理

### 4. 批次處理

- **進度追蹤**：實時顯示處理進度
- **批次大小控制**：可配置的批次大小
- **記憶體優化**：避免記憶體溢出

## 安裝需求

### Python 套件

```bash
pip install pymongo psycopg2-binary sentence-transformers pymilvus emoji pandas numpy
```

### 系統需求

- Python 3.8+
- MongoDB
- PostgreSQL
- Milvus

## 配置說明

### 1. 資料庫配置 (collection_processing_config.json)

```json
{
    "mongo_config": {
        "host": "localhost",
        "port": 27017,
        "database": "podwise",
        "username": "",
        "password": ""
    },
    "postgres_config": {
        "host": "localhost",
        "port": 5432,
        "database": "podwise",
        "user": "postgres",
        "password": "postgres"
    },
    "milvus_config": {
        "host": "localhost",
        "port": 19530
    }
}
```

### 2. 處理參數

```json
{
    "processing_config": {
        "tag_csv_path": "TAG_info.csv",
        "embedding_model": "BAAI/bge-m3",
        "max_chunk_size": 1024,
        "batch_size": 100,
        "text_field": "content"
    }
}
```

### 3. Collection 配置

```json
{
    "collections": ["1500839292"],
    "title_update_config": {
        "pattern": "EPXXX_股癌",
        "backup_original": true
    }
}
```

## 使用方法

### 1. 快速開始

```bash
# 執行完整處理
./run_collection_processing.sh

# 或直接執行 Python 腳本
python3 process_collections.py
```

### 2. 測試功能

```bash
# 執行測試
python3 test_collection_processing.py
```

### 3. 查看錯誤報告

```bash
# 查看錯誤報告
python3 view_error_report.py
```

## 處理流程

### 1. 初始化階段

1. 載入配置檔案
2. 建立資料庫連接
3. 初始化嵌入模型
4. 載入標籤處理器

### 2. 資料處理階段

對於每個 collection：

1. **標題更新**：更新節目標題為指定格式
2. **文件讀取**：從 MongoDB 讀取文件
3. **文本清理**：移除表情符號和特殊字元
4. **文本切分**：將長文本切分為 chunks
5. **標籤提取**：為每個 chunk 提取標籤
6. **向量化**：生成文本嵌入向量
7. **資料儲存**：儲存到 Milvus

### 3. 錯誤處理

- 記錄所有錯誤到 error_report.json
- 繼續處理其他文件
- 提供詳細的錯誤資訊

## 輸出結果

### 1. 處理統計

```
Collection 1500839292: 處理 95/100 文件, 成功率 95.00%, 錯誤 5 個, 總 chunks 285 個
```

### 2. 錯誤報告

錯誤報告包含：
- collection 名稱
- rssID
- 標題
- 錯誤類型
- 錯誤訊息
- 額外資訊

### 3. 日誌檔案

- `collection_processing.log`：詳細處理日誌
- `error_report.json`：錯誤報告

## 標籤系統說明

### 1. TAG_info.csv 格式

```csv
主要類別,子類別,標籤,權重
科技,AI,AI,人工智慧,機器學習,深度學習,1.0
商業,投資,投資,理財,股票,基金,1.0
```

### 2. 標籤提取策略

1. **第一階段**：使用 TagProcessor 進行精確匹配
2. **第二階段**：智能關鍵字匹配
3. **第三階段**：備援標籤系統

### 3. 標籤驗證

- 長度限制：最多 20 字元
- 內容驗證：移除特殊字元
- 相關性檢查：確保標籤與文本相關

## 效能優化

### 1. 批次處理

- 可配置的批次大小
- 記憶體使用優化
- 進度追蹤

### 2. 並行處理

- 支援多個 collection 並行處理
- 資料庫連接池
- 向量化批次處理

### 3. 錯誤恢復

- 自動重試機制
- 錯誤隔離
- 部分成功處理

## 故障排除

### 1. 常見問題

**Q: 連接資料庫失敗**
A: 檢查配置檔案中的連接參數

**Q: 標籤提取失敗**
A: 檢查 TAG_info.csv 檔案格式

**Q: 向量化失敗**
A: 檢查嵌入模型是否正確載入

### 2. 日誌分析

查看 `collection_processing.log` 檔案：
- INFO 級別：正常處理資訊
- WARNING 級別：警告資訊
- ERROR 級別：錯誤資訊

### 3. 錯誤報告分析

使用 `view_error_report.py` 查看詳細錯誤資訊：
- 錯誤類型統計
- 受影響的 collections
- 錯誤原因分析

## 擴展功能

### 1. 自定義標籤

修改 `TAG_info.csv` 檔案添加新的標籤類別

### 2. 自定義清理規則

修改 `TextCleaner` 類別添加自定義清理規則

### 3. 自定義嵌入模型

修改配置檔案中的 `embedding_model` 參數

## 聯絡支援

如有問題，請查看：
1. 日誌檔案
2. 錯誤報告
3. 測試腳本輸出

## 版本資訊

- 版本：1.0.0
- 更新日期：2024-01-XX
- 支援的 Python 版本：3.8+ 