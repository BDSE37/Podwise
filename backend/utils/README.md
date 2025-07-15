# Podwise Utils 模組

## 📋 概述

Podwise Utils 是後端系統的統一工具模組，提供所有子模組共用的工具和服務。採用 OOP 設計原則和 Google Clean Code 標準，確保程式碼的可維護性和可重用性。

## 🏗️ 模組架構

```
utils/
├── main.py                 # 統一入口點
├── __init__.py            # 模組初始化
├── README.md              # 模組說明
├── core_services.py       # 核心服務基礎類別
├── text_processing.py     # 文本處理工具
├── vector_search.py       # 向量搜尋引擎
├── audio_search.py        # 音檔搜尋工具
├── user_auth_service.py   # 用戶認證服務
├── minio_milvus_utils.py  # MinIO 和 Milvus 工具
├── env_config.py          # 環境配置管理
├── logging_config.py      # 日誌配置
└── common_utils.py        # 通用工具函數
```

## 🎯 核心功能

### 1. **文本處理工具** (`text_processing.py`)
- **語義分塊**: 基於語義的文本分塊處理
- **標籤提取**: 智能標籤提取和分類
- **文本標準化**: 文本清理和標準化處理
- **向量化**: 文本向量化處理

```python
from utils import get_text_processor

processor = get_text_processor()
chunks = processor.process_text("您的文本內容")
```

### 2. **向量搜尋引擎** (`vector_search.py`)
- **Milvus 整合**: 向量資料庫操作
- **相似度計算**: 向量相似度計算
- **搜尋優化**: 高效向量搜尋
- **結果排序**: 智能結果排序

```python
from utils import get_vector_search

search_engine = get_vector_search()
results = search_engine.search("查詢向量", top_k=10)
```

### 3. **音檔搜尋工具** (`audio_search.py`)
- **音檔索引**: 音檔元資料索引
- **內容搜尋**: 基於內容的音檔搜尋
- **標籤匹配**: 音檔標籤匹配
- **結果過濾**: 智能結果過濾

```python
from utils import get_audio_search

audio_search = get_audio_search()
results = audio_search.search_by_content("搜尋關鍵字")
```

### 4. **用戶認證服務** (`user_auth_service.py`)
- **用戶管理**: 用戶註冊、登入、驗證
- **權限控制**: 基於角色的權限控制
- **會話管理**: 用戶會話管理
- **安全驗證**: 安全認證機制

```python
from utils import get_user_auth

auth_service = get_user_auth()
user = auth_service.authenticate_user("user_id", "password")
```

### 5. **MinIO 和 Milvus 工具** (`minio_milvus_utils.py`)
- **MinIO 操作**: 物件儲存操作
- **Milvus 連接**: 向量資料庫連接
- **資料同步**: 資料同步工具
- **URL 生成**: 預簽名 URL 生成

```python
from utils import get_minio_client

minio_client = get_minio_client()
objects = minio_client.list_objects("bucket_name")
```

## 🚀 快速開始

### 初始化 Utils 模組

```python
from utils import initialize_utils, UtilsConfig

# 基本初始化
utils_manager = initialize_utils()

# 自定義配置初始化
config = UtilsConfig(
    enable_text_processing=True,
    enable_vector_search=True,
    enable_audio_search=True,
    enable_user_auth=True,
    enable_minio_utils=True,
    log_level="INFO"
)
utils_manager = initialize_utils(config)
```

### 使用服務

```python
# 獲取文本處理器
text_processor = utils_manager.get_text_processor()

# 獲取向量搜尋引擎
vector_search = utils_manager.get_vector_search()

# 獲取音檔搜尋工具
audio_search = utils_manager.get_audio_search()

# 獲取用戶認證服務
user_auth = utils_manager.get_user_auth()

# 獲取 MinIO 客戶端
minio_client = utils_manager.get_minio_client()

# 獲取環境配置
config = utils_manager.get_config()
```

### 健康檢查

```python
# 檢查所有服務健康狀態
health_status = utils_manager.health_check()
print(f"健康狀態: {health_status}")

# 獲取服務資訊
service_info = utils_manager.get_service_info()
print(f"服務資訊: {service_info}")
```

## 🔧 配置選項

### UtilsConfig 配置類別

```python
@dataclass
class UtilsConfig:
    enable_text_processing: bool = True      # 啟用文本處理
    enable_vector_search: bool = True        # 啟用向量搜尋
    enable_audio_search: bool = True         # 啟用音檔搜尋
    enable_user_auth: bool = True            # 啟用用戶認證
    enable_minio_utils: bool = True          # 啟用 MinIO 工具
    log_level: str = "INFO"                  # 日誌等級
```

## 📊 服務狀態

### 健康檢查回應格式

```json
{
    "status": "healthy",
    "services": {
        "text_processor": {"status": "available"},
        "vector_search": {"status": "available"},
        "audio_search": {"status": "available"},
        "user_auth": {"status": "available"},
        "minio_client": {"status": "available"},
        "config": {"status": "available"}
    },
    "timestamp": "2024-01-01T00:00:00"
}
```

## 🛠️ 開發指南

### 添加新服務

1. **創建服務類別**:
```python
class NewService:
    def __init__(self):
        self.name = "new_service"
    
    def health_check(self):
        return {"status": "available"}
```

2. **在 UtilsManager 中註冊**:
```python
def _initialize_services(self):
    # ... 其他服務初始化
    self.services['new_service'] = NewService()
```

3. **添加便捷方法**:
```python
def get_new_service(self):
    return self.get_service('new_service')
```

### 錯誤處理

所有服務都包含完整的錯誤處理機制：

```python
try:
    service = utils_manager.get_service('service_name')
    result = service.perform_operation()
except ValueError as e:
    logger.error(f"服務不存在: {e}")
except Exception as e:
    logger.error(f"操作失敗: {e}")
```

## 📝 版本資訊

- **版本**: 2.0.0
- **作者**: Podwise Team
- **更新日期**: 2024-01-01
- **相容性**: Python 3.8+

## 🔗 相關模組

- **API 模組**: 使用 Utils 提供 REST API 服務
- **RAG Pipeline**: 使用 Utils 進行文本處理和向量搜尋
- **ML Pipeline**: 使用 Utils 進行資料處理和模型管理
- **STT/TTS**: 使用 Utils 進行音檔處理

## 📞 支援

如有問題或建議，請聯繫 Podwise Team 或查看相關文件。