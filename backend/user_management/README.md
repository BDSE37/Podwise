# Podwise User Management 服務

## 概述

Podwise User Management 服務是一個統一的用戶管理系統，採用 OOP 架構設計，支援 CLI 和 FastAPI 兩種介面，提供完整的用戶註冊、登入、查詢和管理功能。

## 功能特色

### 🎯 核心功能
- **用戶註冊與登入** - 安全的用戶認證系統
- **用戶資訊管理** - 完整的 CRUD 操作
- **活動記錄** - 追蹤用戶行為和偏好
- **雙介面支援** - CLI 和 FastAPI API
- **OOP 架構** - 物件導向設計，易於擴展

### 📊 服務架構
- **UserManager** - 主要管理類別
- **UserService** - 核心業務邏輯
- **FastAPI 服務** - RESTful API 介面
- **CLI 工具** - 命令列介面

## 系統架構

### 目錄結構
```
user_management/
├── main.py                    # 統一主介面 (CLI + FastAPI)
├── user_service.py            # 核心業務邏輯
├── requirements.txt           # 依賴套件
└── README.md                  # 說明文件
```

### 類別架構
```
UserManager
├── UserService               # 核心服務
└── 管理方法
    ├── register()            # 用戶註冊
    ├── login()               # 用戶登入
    ├── query_user()          # 用戶查詢
    ├── create_user()         # 創建用戶
    ├── update_user()         # 更新用戶
    ├── delete_user()         # 刪除用戶
    ├── list_users()          # 列出用戶
    ├── record_activity()     # 記錄活動
    └── get_user_activities() # 獲取活動
```

## API 端點

### 健康檢查
```http
GET /health
```

回應：
```json
{
  "status": "healthy",
  "service": "User Management",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 獲取用戶資訊
```http
GET /api/get-id?user_id=123
```

回應：
```json
{
  "success": true,
  "user": {
    "user_id": "123",
    "username": "user123",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z",
    "is_active": true
  }
}
```

### 創建用戶
```http
POST /api/create-user
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com"
}
```

回應：
```json
{
  "success": true,
  "user": {
    "user_id": "124",
    "username": "newuser",
    "email": "newuser@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
}
```

### 更新用戶
```http
PUT /api/update-user/123
Content-Type: application/json

{
  "username": "updateduser",
  "email": "updated@example.com",
  "is_active": true
}
```

### 刪除用戶
```http
DELETE /api/delete-user/123
```

### 列出用戶
```http
GET /api/list-users?limit=10&offset=0
```

### 記錄活動
```http
POST /api/record-activity
Content-Type: application/json

{
  "user_id": 123,
  "activity_type": "podcast_listen",
  "activity_data": {
    "podcast_id": "podcast_001",
    "duration": 300
  }
}
```

### 獲取用戶活動
```http
GET /api/user-activities/123?limit=50
```

### 推薦節目
```http
POST /api/recommend-programs
Content-Type: application/json

{
  "user_id": 123
}
```

## CLI 使用

### 啟動 API 服務
```bash
python main.py api
```

### 用戶註冊
```bash
python main.py register --username user123 --password pass123 --email user@example.com
```

### 用戶登入
```bash
python main.py login --username user123 --password pass123
```

### 查詢用戶
```bash
python main.py query --user_id 123
```

### 創建用戶
```bash
python main.py create --username newuser --email newuser@example.com
```

### 列出用戶
```bash
python main.py list --limit 10 --offset 0
```

## 配置說明

### 環境變數
```bash
# 資料庫配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=podwise
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# 服務配置
USER_MANAGEMENT_PORT=8007
USER_MANAGEMENT_HOST=0.0.0.0
```

### 資料庫配置
```python
# 在 config/db_config.py 中
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DATABASE', 'podwise'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password')
}
```

## 使用範例

### Python 客戶端
```python
import httpx
import asyncio

async def test_user_management():
    async with httpx.AsyncClient() as client:
        # 健康檢查
        response = await client.get("http://localhost:8007/health")
        print("健康狀態:", response.json())
        
        # 創建用戶
        response = await client.post(
            "http://localhost:8007/api/create-user",
            json={
                "username": "testuser",
                "email": "test@example.com"
            }
        )
        print("創建用戶:", response.json())
        
        # 獲取用戶資訊
        response = await client.get("http://localhost:8007/api/get-id?user_id=123")
        print("用戶資訊:", response.json())

# 執行測試
asyncio.run(test_user_management())
```

### JavaScript 客戶端
```javascript
// 健康檢查
const healthResponse = await fetch('http://localhost:8007/health');
const healthData = await healthResponse.json();
console.log('健康狀態:', healthData);

// 創建用戶
const createResponse = await fetch('http://localhost:8007/api/create-user', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'testuser',
        email: 'test@example.com'
    })
});
const createData = await createResponse.json();
console.log('創建用戶:', createData);
```

## 啟動指南

### 1. 安裝依賴
```bash
cd backend/user_management
pip install -r requirements.txt
```

### 2. 配置資料庫
```bash
# 確保 PostgreSQL 已安裝並運行
# 創建資料庫
createdb podwise
```

### 3. 啟動服務

#### API 模式
```bash
python main.py api
```

#### CLI 模式
```bash
# 註冊用戶
python main.py register --username admin --password admin123 --email admin@example.com

# 查詢用戶
python main.py query --user_id 1
```

### 4. 驗證服務
```bash
# API 健康檢查
curl http://localhost:8007/health

# CLI 健康檢查
python main.py --help
```

## 整合測試

### 與 RAG Pipeline 整合
```python
# 在 RAG Pipeline 中使用用戶管理
import httpx

async def get_user_info(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8007/api/get-id?user_id={user_id}")
        return response.json()

async def record_user_activity(user_id: int, activity_type: str, data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8007/api/record-activity",
            json={
                "user_id": user_id,
                "activity_type": activity_type,
                "activity_data": data
            }
        )
        return response.json()
```

### 與 ML Pipeline 整合
```python
# 獲取用戶偏好進行推薦
async def get_user_recommendations(user_id: int):
    # 1. 獲取用戶資訊
    user_info = await get_user_info(str(user_id))
    
    # 2. 獲取用戶活動
    activities = await get_user_activities(user_id)
    
    # 3. 基於活動生成推薦
    recommendations = generate_recommendations(user_info, activities)
    
    return recommendations
```

## 故障排除

### 常見問題

1. **資料庫連接失敗**
   - 檢查 PostgreSQL 服務是否運行
   - 確認資料庫配置是否正確
   - 檢查網路連接

2. **API 服務無法啟動**
   - 檢查端口是否被佔用
   - 確認依賴套件是否安裝完整
   - 檢查環境變數配置

3. **用戶認證失敗**
   - 檢查用戶是否存在
   - 確認密碼是否正確
   - 檢查用戶狀態是否啟用

### 日誌檢查
```bash
# 查看服務日誌
tail -f logs/user_management.log

# 查看資料庫日誌
tail -f /var/log/postgresql/postgresql-*.log
```

## 效能優化

### 1. 資料庫優化
- 使用連接池
- 實作查詢快取
- 優化索引設計

### 2. API 優化
- 實作回應快取
- 支援分頁查詢
- 優化序列化

### 3. 安全性
- 實作 JWT 認證
- 密碼加密存儲
- 輸入驗證

## 未來規劃

1. **功能擴展**
   - 支援社交登入
   - 實作用戶權限管理
   - 支援多租戶

2. **效能提升**
   - 實作 Redis 快取
   - 支援水平擴展
   - 優化查詢效能

3. **監控與分析**
   - 用戶行為分析
   - 效能指標監控
   - 異常檢測

這個用戶管理服務確保了與其他 Podwise 模組的無縫整合，為整個系統提供完整的用戶管理功能。 