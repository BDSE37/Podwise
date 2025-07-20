# Podwise Data Cleaning Pipeline

## 概述

Podwise Data Cleaning Pipeline 是數據清理和預處理服務模組，負責清理、標準化和驗證 Podcast 數據。採用 OOP 設計原則，提供統一的介面。

## 架構設計

### 核心組件

#### 1. 數據清理器 (Data Cleaner)
- **職責**：核心數據清理功能
- **實現**：`DataCleaner` 類別
- **功能**：
  - 文本清理和標準化
  - 數據格式驗證
  - 重複數據處理

#### 2. 清理策略管理器 (Cleaning Strategy Manager)
- **職責**：管理不同的清理策略
- **實現**：`CleaningStrategyManager` 類別
- **功能**：
  - 策略選擇和應用
  - 自定義清理規則
  - 策略效能評估

#### 3. 數據驗證器 (Data Validator)
- **職責**：數據品質驗證
- **實現**：`DataValidator` 類別
- **功能**：
  - 數據完整性檢查
  - 格式驗證
  - 異常檢測

#### 4. 批次處理器 (Batch Processor)
- **職責**：大規模數據批次處理
- **實現**：`BatchProcessor` 類別
- **功能**：
  - 分批處理控制
  - 進度追蹤
  - 錯誤處理

## 統一服務管理器

### DataCleaningManager 類別
- **職責**：整合所有數據清理功能，提供統一的 OOP 介面
- **主要方法**：
  - `clean_data()`: 數據清理
  - `validate_data()`: 數據驗證
  - `batch_process()`: 批次處理
  - `health_check()`: 健康檢查

### 清理流程
1. **數據載入**：從多個來源載入原始數據
2. **初步驗證**：檢查數據完整性和格式
3. **策略選擇**：選擇適當的清理策略
4. **數據清理**：執行清理和標準化
5. **品質驗證**：驗證清理結果品質
6. **結果輸出**：輸出清理後的數據

## 配置系統

### 清理配置
- **檔案**：`config/cleaning_config.py`
- **功能**：
  - 清理策略配置
  - 驗證規則設定
  - 批次處理參數

### 數據配置
- **檔案**：`config/data_config.py`
- **功能**：
  - 數據源配置
  - 格式定義
  - 品質標準

## 數據模型

### 核心數據類別
- `CleaningRequest`: 清理請求
- `CleaningResult`: 清理結果
- `DataQuality`: 數據品質指標
- `CleaningStrategy`: 清理策略

### 工廠函數
- `create_cleaning_request()`: 創建清理請求
- `create_cleaning_result()`: 創建清理結果
- `create_data_quality()`: 創建數據品質指標

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的數據清理功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的清理策略
- 可擴展的驗證規則

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的數據源

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有清理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合數據清理管理器
  - 清理服務控制
  - 健康檢查和統計

### 使用方式
```python
# 創建數據清理實例
from core.data_cleaning_manager import DataCleaningManager

manager = DataCleaningManager()

# 數據清理
result = await manager.clean_data(
    data_source="raw_podcast_data",
    strategy="standard_cleaning",
    output_format="cleaned"
)

# 數據驗證
validation_result = await manager.validate_data(
    data=cleaned_data,
    quality_threshold=0.8
)

# 批次處理
batch_result = await manager.batch_process(
    input_directory="raw_data",
    output_directory="cleaned_data",
    batch_size=1000
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證數據源連接
- 監控清理性能
- 檢查策略可用性

### 性能指標
- 清理速度
- 數據品質提升
- 錯誤率統計
- 處理效率

## 技術棧

- **框架**：FastAPI
- **數據處理**：Pandas, NumPy
- **文本處理**：NLTK, spaCy
- **數據庫**：PostgreSQL, MongoDB
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-data-cleaning .

# 運行容器
docker run -p 8007:8007 podwise-data-cleaning
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/clean` - 數據清理
- `POST /api/v1/validate` - 數據驗證
- `POST /api/v1/batch-clean` - 批次清理
- `GET /api/v1/statistics` - 統計資訊

## 架構優勢

1. **高品質**：確保數據品質和一致性
2. **可擴展性**：支援新的清理策略和數據源
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的品質指標
5. **一致性**：統一的數據模型和介面設計 