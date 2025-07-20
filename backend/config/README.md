# Podwise Configuration Service

## 概述

Podwise Configuration Service 是配置管理服務模組，負責統一管理所有後端服務的配置。採用 OOP 設計原則，提供統一的配置管理介面。

## 架構設計

### 核心組件

#### 1. 配置管理器 (Configuration Manager)
- **職責**：核心配置管理功能
- **實現**：`ConfigurationManager` 類別
- **功能**：
  - 配置載入和驗證
  - 動態配置更新
  - 配置版本管理

#### 2. 數據庫配置管理器 (Database Config Manager)
- **職責**：數據庫配置管理
- **實現**：`DatabaseConfigManager` 類別
- **功能**：
  - 數據庫連接配置
  - 連接池管理
  - 數據庫初始化

#### 3. 環境配置管理器 (Environment Config Manager)
- **職責**：環境變數管理
- **實現**：`EnvironmentConfigManager` 類別
- **功能**：
  - 環境變數載入
  - 配置驗證
  - 敏感資訊保護

#### 4. 服務配置管理器 (Service Config Manager)
- **職責**：服務配置管理
- **實現**：`ServiceConfigManager` 類別
- **功能**：
  - 服務端點配置
  - 服務參數設定
  - 服務依賴管理

## 統一服務管理器

### ConfigurationServiceManager 類別
- **職責**：整合所有配置管理功能，提供統一的 OOP 介面
- **主要方法**：
  - `load_config()`: 載入配置
  - `update_config()`: 更新配置
  - `validate_config()`: 驗證配置
  - `health_check()`: 健康檢查

### 配置管理流程
1. **配置載入**：從多個來源載入配置
2. **配置驗證**：驗證配置完整性和正確性
3. **配置合併**：合併不同來源的配置
4. **配置分發**：分發配置到各服務
5. **配置監控**：監控配置變更

## 配置系統

### 主要配置
- **檔案**：`config_service.py`
- **功能**：
  - 統一配置管理
  - 配置驗證規則
  - 配置更新機制

### 數據庫配置
- **檔案**：`db_config.py`
- **功能**：
  - 數據庫連接參數
  - 連接池設定
  - 初始化腳本

## 數據模型

### 核心數據類別
- `Configuration`: 配置數據
- `DatabaseConfig`: 數據庫配置
- `ServiceConfig`: 服務配置
- `EnvironmentConfig`: 環境配置

### 工廠函數
- `create_configuration()`: 創建配置
- `create_database_config()`: 創建數據庫配置
- `create_service_config()`: 創建服務配置

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的配置管理功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的配置來源
- 可擴展的驗證規則

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的配置來源

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有配置管理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合配置服務管理器
  - 配置管理控制
  - 健康檢查和配置資訊

### 使用方式
```python
# 創建配置服務實例
from config.configuration_service_manager import ConfigurationServiceManager

manager = ConfigurationServiceManager()

# 載入配置
config = await manager.load_config(
    config_type="database",
    environment="production"
)

# 更新配置
updated_config = await manager.update_config(
    config_key="database.host",
    new_value="new-db-host"
)

# 驗證配置
validation_result = await manager.validate_config(
    config=config
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證配置完整性
- 監控配置載入性能
- 檢查配置來源可用性

### 性能指標
- 配置載入時間
- 配置驗證速度
- 配置更新效率
- 錯誤率統計

## 技術棧

- **框架**：FastAPI
- **配置管理**：Pydantic, python-dotenv
- **數據庫**：PostgreSQL
- **驗證**：Cerberus, Marshmallow
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-config-service .

# 運行容器
docker run -p 8009:8009 podwise-config-service
```

## API 端點

- `GET /health` - 健康檢查
- `GET /api/v1/config` - 獲取配置
- `PUT /api/v1/config` - 更新配置
- `POST /api/v1/config/validate` - 驗證配置
- `GET /api/v1/config/status` - 配置狀態

## 架構優勢

1. **統一管理**：所有配置的統一管理介面
2. **可擴展性**：支援新的配置來源和驗證規則
3. **可維護性**：清晰的模組化設計
4. **安全性**：敏感資訊保護和驗證
5. **一致性**：統一的配置格式和介面設計 