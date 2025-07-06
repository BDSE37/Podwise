# Podwise 管道測試說明

## 概述

本目錄包含多個測試腳本，用於測試切斷、貼標、轉向量的完整流程，特別針對表情符號和特殊字元的處理。

## 測試腳本說明

### 1. 快速測試 (`quick_test.py`)
- **用途**: 快速驗證基本功能
- **功能**: 測試文本清理、切分、向量化、標籤提取
- **執行**: `python quick_test.py`
- **適用**: 初次測試，驗證環境設置

### 2. 文本清理測試 (`test_text_cleaning.py`)
- **用途**: 專門測試文本清理功能
- **功能**: 
  - 表情符號處理
  - 特殊字符處理
  - Unicode 標準化
  - 標題標準化
  - 搜索變體生成
  - 性能測試
- **執行**: `python test_text_cleaning.py`
- **適用**: 驗證文本清理功能

### 3. 簡化管道測試 (`test_simple_pipeline.py`)
- **用途**: 測試完整流程（不依賴 PostgreSQL）
- **功能**:
  - MongoDB 資料讀取
  - 文本清理
  - 文本切分
  - 標籤提取
  - 向量化
  - Milvus 儲存
- **執行**: 
  - 樣本資料: `python test_simple_pipeline.py`
  - MongoDB資料: `python test_simple_pipeline.py --mongo`
- **適用**: 測試完整流程

### 4. 完整管道測試 (`test_chunk_tag_vector.py`)
- **用途**: 完整功能測試
- **功能**: 包含所有組件的詳細測試
- **執行**: `python test_chunk_tag_vector.py`
- **適用**: 深度測試

### 5. 執行腳本 (`run_pipeline_test.sh`)
- **用途**: 互動式測試選擇
- **功能**: 提供選單選擇不同測試
- **執行**: `./run_pipeline_test.sh`
- **適用**: 方便使用

## 測試流程

### 基本流程
1. **文本清理**: 移除表情符號，標準化特殊字符
2. **文本切分**: 將長文本切分成適當大小的塊
3. **標籤提取**: 從文本塊中提取相關標籤
4. **向量化**: 將文本和標籤轉換為向量
5. **儲存**: 將結果儲存到向量資料庫

### 文本清理功能
- **表情符號處理**: 將表情符號轉換為文字描述
- **特殊字符處理**: 處理註冊商標、版權符號等
- **Unicode 標準化**: 統一字符編碼
- **空白處理**: 移除多餘空白和換行
- **標題標準化**: 生成標準化標題用於搜索

## 環境要求

### 必要服務
- MongoDB (運行中)
- Milvus (運行中)
- Python 3.8+

### 必要套件
```bash
pip install pymongo pymilvus sentence-transformers
```

## 使用建議

### 初次測試
1. 先運行快速測試: `python quick_test.py`
2. 檢查文本清理功能: `python test_text_cleaning.py`
3. 測試完整流程: `python test_simple_pipeline.py`

### 生產環境測試
1. 使用 MongoDB 真實資料: `python test_simple_pipeline.py --mongo`
2. 運行完整測試: `python test_chunk_tag_vector.py`

### 問題診斷
- 檢查日誌文件
- 確認服務連接狀態
- 驗證資料格式

## 日誌文件

- `simple_pipeline_test.log`: 簡化管道測試日誌
- `test_chunk_tag_vector.log`: 完整管道測試日誌
- 控制台輸出: 即時測試結果

## 常見問題

### 1. 連接錯誤
- 確認 MongoDB 和 Milvus 服務運行中
- 檢查連接配置
- 驗證網路連接

### 2. 向量化失敗
- 確認 sentence-transformers 已安裝
- 檢查模型下載狀態
- 驗證記憶體使用量

### 3. 標籤提取問題
- 檢查 TAG_info.csv 文件
- 確認標籤處理器初始化
- 驗證關鍵字匹配邏輯

## 測試結果驗證

### 成功指標
- 文本清理: 表情符號被正確處理
- 文本切分: 生成適當大小的文本塊
- 標籤提取: 提取相關標籤
- 向量化: 生成正確維度的向量
- 儲存: 成功寫入 Milvus

### 性能指標
- 文本清理速度
- 向量化速度
- 儲存速度
- 記憶體使用量

## 後續步驟

1. **優化配置**: 根據測試結果調整參數
2. **擴展功能**: 添加更多標籤類別
3. **性能優化**: 改進處理速度
4. **整合測試**: 與其他系統整合 