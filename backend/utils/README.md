# Podwise Utils

## 概述

Podwise Utils 是通用工具模組，提供各種輔助功能和服務。採用 OOP 設計原則，提供統一的工具介面。

## 架構設計

### 核心組件

#### 1. 批次處理器 (Batch Processor)
- **職責**：大規模數據批次處理
- **實現**：`BatchProcessor` 類別
- **功能**：
  - 分批處理控制
  - 進度追蹤
  - 錯誤處理和重試

#### 2. 音頻流服務 (Audio Stream Service)
- **職責**：音頻流處理和管理
- **實現**：`AudioStreamService` 類別
- **功能**：
  - 音頻流處理
  - 格式轉換
  - 流媒體支援

#### 3. MinIO 服務 (MinIO Service)
- **職責**：MinIO 物件存儲管理
- **實現**：`MinIOService` 類別
- **功能**：
  - 檔案上傳下載
  - 存儲桶管理
  - 物件生命週期管理

#### 4. 文本處理器 (Text Processor)
- **職責**：文本處理和轉換
- **實現**：`TextProcessor` 類別
- **功能**：
  - 文本清理
  - 格式轉換
  - 語言處理

## 統一服務管理器

### UtilsServiceManager 類別
- **職責**：整合所有工具功能，提供統一的 OOP 介面
- **主要方法**：
  - `batch_process()`: 批次處理
  - `process_audio()`: 音頻處理
  - `manage_storage()`: 存儲管理
  - `health_check()`: 健康檢查

### 工具使用流程
1. **需求分析**：分析具體需求
2. **工具選擇**：選擇適當的工具
3. **參數配置**：配置處理參數
4. **執行處理**：執行具體處理
5. **結果驗證**：驗證處理結果

## 配置系統

### 工具配置
- **檔案**：`config/utils_config.py`
- **功能**：
  - 工具參數配置
  - 處理策略設定
  - 性能優化參數

### 環境配置
- **檔案**：`env_config.py`
- **功能**：
  - 環境變數管理
  - 配置載入
  - 環境檢測

## 數據模型

### 核心數據類別
- `ProcessingRequest`: 處理請求
- `ProcessingResult`: 處理結果
- `BatchStatus`: 批次狀態
- `StorageConfig`: 存儲配置

### 工廠函數
- `create_processing_request()`: 創建處理請求
- `create_processing_result()`: 創建處理結果
- `create_batch_status()`: 創建批次狀態

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的工具功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的工具和處理方式
- 可擴展的處理策略

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的處理引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有工具都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合工具服務管理器
  - 工具服務控制
  - 健康檢查和統計

### 使用方式
```python
# 創建工具服務實例
from utils.utils_service_manager import UtilsServiceManager

manager = UtilsServiceManager()

# 批次處理
result = await manager.batch_process(
    data_source="input_data",
    processor="text_processor",
    batch_size=1000
)

# 音頻處理
audio_result = await manager.process_audio(
    audio_file="input.wav",
    format="mp3",
    quality="high"
)

# 存儲管理
storage_result = await manager.manage_storage(
    operation="upload",
    file_path="data.json",
    bucket="podwise-data"
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證工具可用性
- 監控處理性能
- 檢查存儲連接

### 性能指標
- 處理速度
- 資源使用效率
- 錯誤率統計
- 工具可用性

## 技術棧

- **框架**：FastAPI
- **數據處理**：Pandas, NumPy
- **音頻處理**：librosa, pydub
- **存儲**：MinIO, S3
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-utils .

# 運行容器
docker run -p 8010:8010 podwise-utils
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/batch-process` - 批次處理
- `POST /api/v1/process-audio` - 音頻處理
- `POST /api/v1/storage` - 存儲管理
- `GET /api/v1/statistics` - 統計資訊

## 架構優勢

1. **通用性**：提供各種通用工具功能
2. **可擴展性**：支援新的工具和處理方式
3. **可維護性**：清晰的模組化設計
4. **高效性**：優化的處理和存儲機制
5. **一致性**：統一的介面設計和錯誤處理