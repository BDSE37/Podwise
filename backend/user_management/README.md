# Podwise User Management

## 概述

Podwise User Management 是用戶管理服務模組，負責用戶註冊、認證、授權和個人化設定。採用 OOP 設計原則，提供統一的介面。

## 架構設計

### 核心組件

#### 1. 用戶管理器 (User Manager)
- **職責**：核心用戶管理功能
- **實現**：`UserManager` 類別
- **功能**：
  - 用戶註冊和登入
  - 用戶資料管理
  - 用戶狀態追蹤

#### 2. 認證管理器 (Authentication Manager)
- **職責**：用戶認證和授權
- **實現**：`AuthenticationManager` 類別
- **功能**：
  - JWT 認證
  - 權限驗證
  - 會話管理

#### 3. 個人化管理器 (Personalization Manager)
- **職責**：用戶個人化設定
- **實現**：`PersonalizationManager` 類別
- **功能**：
  - 偏好設定管理
  - 推薦歷史追蹤
  - 個人化內容

#### 4. 權限管理器 (Permission Manager)
- **職責**：權限和角色管理
- **實現**：`PermissionManager` 類別
- **功能**：
  - 角色定義
  - 權限分配
  - 存取控制

## 統一服務管理器

### UserManagementManager 類別
- **職責**：整合所有用戶管理功能，提供統一的 OOP 介面
- **主要方法**：
  - `register_user()`: 用戶註冊
  - `authenticate_user()`: 用戶認證
  - `update_profile()`: 更新用戶資料
  - `health_check()`: 健康檢查

### 用戶管理流程
1. **用戶註冊**：建立新用戶帳戶
2. **身份驗證**：驗證用戶身份
3. **權限分配**：分配適當權限
4. **個人化設定**：建立個人化偏好
5. **會話管理**：管理用戶會話

## 配置系統

### 用戶配置
- **檔案**：`config/user_config.py`
- **功能**：
  - 用戶資料配置
  - 認證設定
  - 權限配置

### 安全配置
- **檔案**：`config/security_config.py`
- **功能**：
  - 密碼政策
  - JWT 設定
  - 安全參數

## 數據模型

### 核心數據類別
- `User`: 用戶資料
- `UserProfile`: 用戶檔案
- `UserSession`: 用戶會話
- `UserPermission`: 用戶權限

### 工廠函數
- `create_user()`: 創建用戶
- `create_user_profile()`: 創建用戶檔案
- `create_user_session()`: 創建用戶會話

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的用戶管理功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的認證方式
- 可擴展的權限系統

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的資料庫

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
  - 整合用戶管理管理器
  - 用戶服務控制
  - 健康檢查和統計

### 使用方式
```python
# 創建用戶管理實例
from core.user_management_manager import UserManagementManager

manager = UserManagementManager()

# 用戶註冊
user = await manager.register_user(
    username="Podwise0001",
    email="user@example.com",
    password="secure_password"
)

# 用戶認證
auth_result = await manager.authenticate_user(
    username="Podwise0001",
    password="secure_password"
)

# 更新用戶資料
updated_profile = await manager.update_profile(
    user_id=user.id,
    preferences={"category": "business", "language": "zh-TW"}
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證資料庫連接
- 監控認證服務
- 檢查權限系統

### 性能指標
- 註冊成功率
- 認證速度
- 會話管理效率
- 錯誤率統計

## 技術棧

- **框架**：FastAPI
- **認證**：JWT, bcrypt
- **資料庫**：PostgreSQL, Redis
- **安全**：OAuth2, RBAC
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-user-management .

# 運行容器
docker run -p 8006:8006 podwise-user-management
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/register` - 用戶註冊
- `POST /api/v1/login` - 用戶登入
- `PUT /api/v1/profile` - 更新用戶資料
- `GET /api/v1/profile` - 獲取用戶資料
- `POST /api/v1/logout` - 用戶登出

## 架構優勢

1. **安全性**：完整的認證和授權機制
2. **可擴展性**：支援新的認證方式和權限模型
3. **可維護性**：清晰的模組化設計
4. **個人化**：支援用戶個人化設定
5. **一致性**：統一的數據模型和介面設計 