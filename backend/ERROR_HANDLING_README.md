# 錯誤處理功能說明

## 概述

本系統整合了完整的錯誤記錄和處理功能，專門處理向量化過程中的各種錯誤，並提供詳細的錯誤報告供事後分析。

## 功能特色

### 🔍 詳細錯誤記錄
- **Collection ID**: 記錄錯誤發生的 Collection
- **RSS ID**: 記錄錯誤的 RSS 來源
- **Title**: 記錄節目標題
- **Error Type**: 錯誤類型分類
- **Error Message**: 詳細錯誤訊息
- **Processing Stage**: 處理階段
- **Timestamp**: 錯誤發生時間
- **Retry Count**: 重試次數

### 📊 多種報告格式
- **JSON 格式**: 結構化資料，適合程式處理
- **CSV 格式**: 表格格式，適合 Excel 分析
- **摘要統計**: 錯誤類型、受影響 Collections 統計

### 🛠️ 錯誤類型分類
- `mongodb_error`: MongoDB 連接或查詢錯誤
- `text_processing_error`: 文本處理錯誤
- `vectorization_error`: 向量化錯誤
- `milvus_error`: Milvus 儲存錯誤
- `general_error`: 一般錯誤

### 📁 檔案結構
```
error_logs/
├── vectorization_errors_20241206_143022.json
├── vectorization_errors_20241206_143022.csv
└── ...
```

## 使用方式

### 1. 自動錯誤記錄

錯誤記錄功能已整合到管道處理中，會自動記錄所有錯誤：

```python
# 在處理過程中自動記錄錯誤
try:
    # 處理邏輯
    pass
except Exception as e:
    self.error_handler.handle_vectorization_error(
        collection_id=doc.collection_id,
        rss_id=doc.rss_id,
        title=doc.title,
        error=e,
        stage="vectorization"
    )
```

### 2. 查看錯誤報告

#### 列出所有錯誤報告
```bash
python view_error_report.py --list
```

#### 查看最新錯誤報告
```bash
python view_error_report.py
```

#### 查看指定錯誤報告
```bash
python view_error_report.py --view vectorization_errors_20241206_143022.json
```

#### 搜尋特定錯誤
```bash
python view_error_report.py --search "connection"
```

#### 匯出過濾後的錯誤
```bash
# 匯出特定 Collection 的錯誤
python view_error_report.py --export --collection "1500839292" --output filtered_errors.json

# 匯出特定錯誤類型
python view_error_report.py --export --error-type "vectorization" --output vector_errors.csv
```

### 3. 錯誤報告範例

#### JSON 格式
```json
{
  "summary": {
    "total_errors": 5,
    "generated_at": "2024-12-06T14:30:22",
    "error_types": {
      "vectorization_error": 3,
      "milvus_error": 2
    }
  },
  "errors": [
    {
      "collection_id": "1500839292",
      "rss_id": "rss_001",
      "title": "EP001_股癌",
      "error_type": "vectorization_error",
      "error_message": "Model loading failed",
      "processing_stage": "text_vectorization",
      "timestamp": "2024-12-06T14:30:22",
      "retry_count": 0
    }
  ]
}
```

#### CSV 格式
```csv
Collection ID,RSS ID,Title,Error Type,Error Message,Processing Stage,Timestamp,Retry Count
1500839292,rss_001,EP001_股癌,vectorization_error,Model loading failed,text_vectorization,2024-12-06T14:30:22,0
```

## 錯誤處理流程

### 1. 錯誤捕獲
- 在每個處理階段都加入 try-catch
- 使用專門的錯誤處理器記錄錯誤
- 保留原始錯誤資訊

### 2. 錯誤分類
- 根據錯誤發生位置分類
- 記錄處理階段資訊
- 提供錯誤上下文

### 3. 錯誤報告
- 自動生成 JSON 和 CSV 報告
- 提供錯誤摘要統計
- 支援錯誤搜尋和過濾

### 4. 事後處理
- 根據錯誤報告分析問題
- 針對性修復錯誤
- 重新處理失敗的項目

## 常見錯誤及處理

### MongoDB 錯誤
- **原因**: 連接失敗、查詢超時、資料格式錯誤
- **處理**: 檢查連接設定、網路狀態、資料完整性

### 文本處理錯誤
- **原因**: 編碼問題、特殊字符、記憶體不足
- **處理**: 清理文本、增加記憶體、處理編碼

### 向量化錯誤
- **原因**: 模型載入失敗、GPU 記憶體不足、文本過長
- **處理**: 檢查模型檔案、調整批次大小、分割長文本

### Milvus 錯誤
- **原因**: 連接失敗、索引問題、資料格式錯誤
- **處理**: 檢查 Milvus 服務、重建索引、驗證資料格式

## 最佳實踐

### 1. 定期檢查錯誤報告
```bash
# 每日檢查錯誤
python view_error_report.py --list
python view_error_report.py --view latest
```

### 2. 分析錯誤模式
```bash
# 分析特定 Collection 的錯誤
python view_error_report.py --export --collection "1500839292" --output collection_errors.json
```

### 3. 建立錯誤處理流程
1. 查看錯誤摘要
2. 分析錯誤類型分布
3. 針對性修復問題
4. 重新處理失敗項目
5. 驗證修復結果

### 4. 監控錯誤趨勢
- 定期匯出錯誤報告
- 分析錯誤發生頻率
- 識別系統性問題
- 優化處理流程

## 進階功能

### 自訂錯誤處理
```python
# 自訂錯誤處理邏輯
def custom_error_handler(self, error_type, error_message, context):
    # 自訂處理邏輯
    pass
```

### 錯誤重試機制
```python
# 實現重試邏輯
if error.retry_count < max_retries:
    # 重試處理
    pass
```

### 錯誤通知
```python
# 發送錯誤通知
def send_error_notification(self, error_summary):
    # 發送郵件或訊息通知
    pass
```

## 故障排除

### 1. 錯誤報告檔案損壞
```bash
# 檢查檔案完整性
python view_error_report.py --view filename.json
```

### 2. 錯誤記錄不完整
- 檢查日誌目錄權限
- 確認磁碟空間
- 驗證錯誤處理器初始化

### 3. 錯誤分類不正確
- 檢查錯誤處理器設定
- 驗證錯誤類型定義
- 更新錯誤分類邏輯

## 總結

錯誤處理功能提供了完整的錯誤追蹤和分析能力，幫助您：
- 快速識別問題
- 分析錯誤模式
- 針對性修復
- 改善系統穩定性

透過這些工具，您可以有效地管理和解決向量化過程中的各種錯誤。 