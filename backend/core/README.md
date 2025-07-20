# Podwise Core Services

## 概述

Podwise Core Services 是核心服務管理模組，負責協調和管理所有後端服務。採用 OOP 設計原則，提供統一的服務管理介面。

## 架構設計

### 核心組件

#### 1. 服務管理器 (Service Manager)
- **職責**：核心服務管理功能
- **實現**：`ServiceManager` 類別
- **功能**：
  - 服務生命週期管理
  - 服務狀態監控
  - 服務間通訊協調

#### 2. Podwise 服務管理器 (Podwise Service Manager)
- **職責**：Podwise 特定服務管理
- **實現**：`PodwiseServiceManager` 類別
- **功能**：
  - 整合所有 Podwise 服務
  - 統一服務介面
  - 服務配置管理

#### 3. 健康檢查管理器 (Health Check Manager)
- **職責**：服務健康狀態監控
- **實現**：`HealthCheckManager` 類別
- **功能**：
  - 服務可用性檢查
  - 性能指標監控
  - 異常檢測和警報

#### 4. 配置管理器 (Configuration Manager)
- **職責**：服務配置管理
- **實現**：`ConfigurationManager` 類別
- **功能**：
  - 配置載入和驗證
  - 動態配置更新
  - 環境變數管理

## 統一服務管理器

### CoreServiceManager 類別
- **職責**：整合所有核心服務功能，提供統一的 OOP 介面
- **主要方法**：
  - `start_services()`: 啟動所有服務
  - `stop_services()`: 停止所有服務
  - `health_check()`: 健康檢查
  - `get_service_status()`: 獲取服務狀態

### 服務管理流程
1. **服務初始化**：載入配置和初始化服務
2. **服務啟動**：按順序啟動所有服務
3. **狀態監控**：持續監控服務狀態
4. **異常處理**：處理服務異常和故障
5. **服務關閉**：優雅關閉所有服務

## 配置系統

### 核心配置
- **檔案**：`config/core_config.py`
- **功能**：
  - 服務配置
  - 監控設定
  - 日誌配置

### 服務配置
- **檔案**：`config/service_config.py`
- **功能**：
  - 各服務端點配置
  - 連接參數設定
  - 超時配置

## 數據模型

### 核心數據類別
- `ServiceStatus`: 服務狀態
- `HealthCheck`: 健康檢查結果
- `ServiceConfig`: 服務配置
- `ServiceMetrics`: 服務指標

### 工廠函數
- `create_service_status()`: 創建服務狀態
- `create_health_check()`: 創建健康檢查
- `create_service_config()`: 創建服務配置

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的服務管理功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的服務類型
- 可擴展的監控機制

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的服務類型

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有管理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合核心服務管理器
  - 服務管理控制
  - 健康檢查和監控

### 使用方式
```python
# 創建核心服務實例
from core.core_service_manager import CoreServiceManager

manager = CoreServiceManager()

# 啟動所有服務
await manager.start_services()

# 健康檢查
health_status = await manager.health_check()

# 獲取服務狀態
service_status = manager.get_service_status()

# 停止所有服務
await manager.stop_services()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有服務狀態
- 驗證服務連接
- 監控服務性能
- 檢查資源使用

### 性能指標
- 服務啟動時間
- 服務可用性
- 響應時間統計
- 錯誤率監控

## 技術棧

- **框架**：FastAPI
- **服務管理**：asyncio, multiprocessing
- **監控**：Prometheus, Grafana
- **配置管理**：Pydantic, python-dotenv
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-core-services .

# 運行容器
docker run -p 8008:8008 podwise-core-services
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/services/start` - 啟動服務
- `POST /api/v1/services/stop` - 停止服務
- `GET /api/v1/services/status` - 服務狀態
- `GET /api/v1/metrics` - 性能指標

## 架構優勢

1. **統一管理**：所有服務的統一管理介面
2. **可擴展性**：支援新的服務和監控方式
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的監控和警報系統
5. **可靠性**：穩定的服務生命週期管理 