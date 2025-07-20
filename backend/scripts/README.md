# Podwise Scripts

## 概述

Podwise Scripts 是腳本工具模組，提供各種管理和維護腳本。採用 OOP 設計原則，提供統一的腳本管理介面。

## 架構設計

### 核心組件

#### 1. 腳本管理器 (Script Manager)
- **職責**：核心腳本管理功能
- **實現**：`ScriptManager` 類別
- **功能**：
  - 腳本執行控制
  - 參數管理
  - 結果處理

#### 2. 數據庫分析器 (Database Analyzer)
- **職責**：數據庫結構和數據分析
- **實現**：`DatabaseAnalyzer` 類別
- **功能**：
  - 數據庫結構檢查
  - 數據完整性分析
  - 性能優化建議

#### 3. MinIO 分析器 (MinIO Analyzer)
- **職責**：MinIO 存儲分析
- **實現**：`MinIOAnalyzer` 類別
- **功能**：
  - 存儲桶分析
  - 檔案統計
  - 存儲優化

#### 4. 系統監控器 (System Monitor)
- **職責**：系統狀態監控
- **實現**：`SystemMonitor` 類別
- **功能**：
  - 系統資源監控
  - 服務狀態檢查
  - 性能指標收集

## 統一服務管理器

### ScriptsServiceManager 類別
- **職責**：整合所有腳本功能，提供統一的 OOP 介面
- **主要方法**：
  - `run_script()`: 執行腳本
  - `analyze_database()`: 數據庫分析
  - `analyze_storage()`: 存儲分析
  - `health_check()`: 健康檢查

### 腳本執行流程
1. **腳本選擇**：選擇要執行的腳本
2. **參數配置**：配置腳本參數
3. **執行腳本**：執行具體腳本
4. **結果處理**：處理執行結果
5. **報告生成**：生成執行報告

## 配置系統

### 腳本配置
- **檔案**：`config/scripts_config.py`
- **功能**：
  - 腳本參數配置
  - 執行策略設定
  - 輸出格式配置

### 分析配置
- **檔案**：`config/analysis_config.py`
- **功能**：
  - 分析參數設定
  - 閾值配置
  - 報告格式設定

## 數據模型

### 核心數據類別
- `ScriptRequest`: 腳本請求
- `ScriptResult`: 腳本結果
- `AnalysisReport`: 分析報告
- `SystemStatus`: 系統狀態

### 工廠函數
- `create_script_request()`: 創建腳本請求
- `create_script_result()`: 創建腳本結果
- `create_analysis_report()`: 創建分析報告

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的腳本功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的腳本和分析方式
- 可擴展的執行策略

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的執行環境

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有腳本都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合腳本服務管理器
  - 腳本執行控制
  - 健康檢查和報告

### 使用方式
```python
# 創建腳本服務實例
from scripts.scripts_service_manager import ScriptsServiceManager

manager = ScriptsServiceManager()

# 執行腳本
result = await manager.run_script(
    script_name="analyze_database",
    parameters={"table": "episodes"}
)

# 數據庫分析
analysis_result = await manager.analyze_database(
    database="podwise",
    tables=["episodes", "podcasts"]
)

# 存儲分析
storage_analysis = await manager.analyze_storage(
    bucket="podwise-data",
    analyze_files=True
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證腳本可用性
- 監控執行性能
- 檢查系統資源

### 性能指標
- 腳本執行時間
- 資源使用效率
- 錯誤率統計
- 分析準確性

## 技術棧

- **框架**：FastAPI
- **數據庫**：PostgreSQL, MongoDB
- **存儲**：MinIO, S3
- **監控**：psutil, prometheus
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-scripts .

# 運行容器
docker run -p 8011:8011 podwise-scripts
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/run-script` - 執行腳本
- `POST /api/v1/analyze-database` - 數據庫分析
- `POST /api/v1/analyze-storage` - 存儲分析
- `GET /api/v1/reports` - 獲取報告

## 架構優勢

1. **自動化**：提供各種自動化管理腳本
2. **可擴展性**：支援新的腳本和分析方式
3. **可維護性**：清晰的模組化設計
4. **監控性**：完整的系統監控和分析
5. **一致性**：統一的腳本執行和報告格式 