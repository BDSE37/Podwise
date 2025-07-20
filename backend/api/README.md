# Podwise API Gateway

## 概述

Podwise API Gateway 是統一的 API 網關服務，負責路由、負載均衡、認證和監控所有後端服務。採用 OOP 設計原則，提供統一的介面。

## 架構設計

### 核心組件

#### 1. 路由管理器 (Route Manager)
- **職責**：API 路由和負載均衡
- **實現**：`RouteManager` 類別
- **功能**：
  - 請求路由
  - 負載均衡
  - 服務發現

#### 2. 認證管理器 (Authentication Manager)
- **職責**：用戶認證和授權
- **實現**：`AuthenticationManager` 類別
- **功能**：
  - JWT 認證
  - 權限驗證
  - 用戶管理

#### 3. 請求處理器 (Request Processor)
- **職責**：請求處理和轉發
- **實現**：`RequestProcessor` 類別
- **功能**：
  - 請求驗證
  - 參數轉換
  - 錯誤處理

#### 4. 監控管理器 (Monitoring Manager)
- **職責**：服務監控和日誌
- **實現**：`MonitoringManager` 類別
- **功能**：
  - 性能監控
  - 錯誤追蹤
  - 統計資訊

## 統一服務管理器

### APIGatewayManager 類別
- **職責**：整合所有 API 網關功能，提供統一的 OOP 介面
- **主要方法**：
  - `route_request()`: 路由請求
  - `authenticate_user()`: 用戶認證
  - `health_check()`: 健康檢查
  - `get_statistics()`: 獲取統計資訊

### 請求處理流程
1. **請求接收**：接收客戶端請求
2. **認證驗證**：驗證用戶身份和權限
3. **路由選擇**：選擇目標服務
4. **請求轉發**：轉發到目標服務
5. **回應處理**：處理和返回回應

## 配置系統

### 網關配置
- **檔案**：`config/gateway_config.py`
- **功能**：
  - 路由配置
  - 認證設定
  - 監控配置

### 服務配置
- **檔案**：`config/service_config.py`
- **功能**：
  - 服務端點配置
  - 負載均衡設定
  - 超時配置

## 數據模型

### 核心數據類別
- `APIRequest`: API 請求
- `APIResponse`: API 回應
- `UserSession`: 用戶會話
- `ServiceEndpoint`: 服務端點

### 工廠函數
- `create_api_request()`: 創建 API 請求
- `create_api_response()`: 創建 API 回應
- `create_user_session()`: 創建用戶會話

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的網關功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的路由規則
- 可擴展的認證機制

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的認證方式

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有處理器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供統一的 API 端點
  - 整合 API 網關管理器
  - 路由和負載均衡控制
  - 健康檢查和監控

### 使用方式
```python
# 創建 API 網關實例
from core.api_gateway_manager import APIGatewayManager

gateway = APIGatewayManager()

# 路由請求
response = await gateway.route_request(
    method="POST",
    path="/api/v1/query",
    headers=headers,
    body=request_body
)

# 用戶認證
auth_result = await gateway.authenticate_user(
    token="jwt_token",
    required_permissions=["read"]
)

# 獲取統計資訊
stats = gateway.get_statistics()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證服務連接
- 監控路由性能
- 檢查認證服務

### 性能指標
- 請求處理時間
- 錯誤率統計
- 服務可用性
- 負載均衡效果

## 技術棧

- **框架**：FastAPI
- **認證**：JWT, OAuth2
- **負載均衡**：Round Robin, Least Connections
- **監控**：Prometheus, Grafana
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-api-gateway .

# 運行容器
docker run -p 8000:8000 podwise-api-gateway
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/query` - 查詢路由
- `POST /api/v1/auth/login` - 用戶登入
- `GET /api/v1/statistics` - 統計資訊
- `GET /api/v1/services` - 服務狀態

## 架構優勢

1. **統一入口**：所有服務的統一入口點
2. **可擴展性**：支援新的服務和路由
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的監控和日誌
5. **安全性**：統一的認證和授權 