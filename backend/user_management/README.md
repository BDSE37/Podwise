# User Management 模組

本模組統一管理用戶註冊、登入、查詢等功能，支援 OOP 調用與 CLI 測試，符合 Google Clean Code 原則。

## 主要功能
- 用戶註冊
- 用戶登入
- 用戶查詢

## OOP 調用範例
```python
from main import UserManager

manager = UserManager()
# 註冊
result = manager.register('user1', 'password123', 'user1@example.com')
# 登入
result = manager.login('user1', 'password123')
# 查詢
result = manager.query_user('user_id')
```

## CLI 用法
```bash
# 註冊
python main.py register --username user1 --password password123 --email user1@example.com

# 登入
python main.py login --username user1 --password password123

# 查詢
python main.py query --user_id 123456
```

## 依賴
- user_service.py
- user_api.py

---
本模組可作為獨立服務或被其他模組以 OOP 方式調用。 