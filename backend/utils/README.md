# Podwise Utils 模組

## 概述
Podwise Utils 提供統一的工具模組，包含各種功能性服務和工具類別。所有服務都可以通過 `main.py` 統一調用和管理。

## 新增服務模組

### 音檔流服務 (audio_stream_service.py)
- **功能**: 提供 MinIO 音檔的直接 URL 和流式播放
- **主要類別**: `AudioStreamService`
- **調用方式**: `get_audio_stream()`
- **端口**: 8006

### 反饋服務 (feedback_service.py)
- **功能**: 處理用戶反饋和偏好儲存，符合 PostgreSQL 資料庫結構
- **主要類別**: `DatabaseManager`, `FeedbackRequest`, `UserPreferencesRequest`
- **調用方式**: `get_feedback_service()`
- **端口**: 8007

### MinIO 節目服務 (minio_episode_service.py)
- **功能**: 獲取 business-one-minutes 和 education-one-minutes 資料夾中的可用節目
- **主要類別**: `MinioEpisodeService`
- **調用方式**: `get_minio_episode()`
- **支援格式**: Spotify_RSS_{rss_id}_{episode_title}.mp3, RSS_{rss_id}_{episode_title}.mp3

## 原有工具模組

### 文本處理 (text_processing.py)
- **功能**: 文本分塊、標籤提取、語義分析
- **主要類別**: `TextChunker`, `TagExtractor`, `UnifiedTagProcessor`
- **調用方式**: `get_text_processor()`

### 向量搜尋 (vector_search.py)
- **功能**: 向量相似度計算、Milvus 整合
- **主要類別**: `VectorSearchEngine`, `MilvusVectorSearch`
- **調用方式**: `get_vector_search()`

### 共用工具 (common_utils.py)
- **功能**: 通用工具函數、路徑處理、錯誤處理
- **主要類別**: `DictToAttrRecursive`, 各種工具函數

### 環境配置 (env_config.py)
- **功能**: 環境變數管理、配置載入
- **主要類別**: `PodriConfig`
- **調用方式**: `get_config()`

### 日誌配置 (logging_config.py)
- **功能**: 統一日誌配置、日誌格式化
- **主要函數**: `setup_logging`

## 使用方式

### 統一初始化
```python
from backend.utils.main import initialize_utils, UtilsConfig

# 基本初始化
utils_manager = initialize_utils()

# 自定義配置初始化
config = UtilsConfig(
    enable_audio_stream=True,
    enable_feedback_service=True,
    enable_minio_episode=True,
    log_level="INFO"
)
utils_manager = initialize_utils(config)
```

### 獲取服務
```python
# 獲取音檔流服務
audio_stream = utils_manager.get_audio_stream()

# 獲取反饋服務
feedback_service = utils_manager.get_feedback_service()

# 獲取 MinIO 節目服務
minio_episode = utils_manager.get_minio_episode()

# 獲取其他服務
text_processor = utils_manager.get_text_processor()
vector_search = utils_manager.get_vector_search()
```

### 便捷函數調用
```python
from backend.utils.main import (
    get_audio_stream,
    get_feedback_service,
    get_minio_episode,
    get_text_processor,
    get_vector_search
)

# 直接獲取服務
audio_stream = get_audio_stream()
feedback_service = get_feedback_service()
minio_episode = get_minio_episode()
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

## 專案結構
```
backend/utils/
├── main.py                      # 統一服務管理器
├── audio_stream_service.py      # 音檔流服務
├── feedback_service.py          # 反饋服務
├── minio_episode_service.py     # MinIO 節目服務
├── text_processing.py           # 文本處理工具
├── vector_search.py             # 向量搜尋工具
├── common_utils.py              # 共用工具
├── env_config.py                # 環境配置
├── logging_config.py            # 日誌配置
└── __init__.py                  # 模組初始化
```

## 配置選項

### UtilsConfig 配置類別
```python
@dataclass
class UtilsConfig:
    enable_text_processing: bool = True      # 啟用文本處理
    enable_vector_search: bool = True        # 啟用向量搜尋
    enable_audio_search: bool = True         # 啟用音檔搜尋
    enable_user_auth: bool = True            # 啟用用戶認證
    enable_minio_utils: bool = True          # 啟用 MinIO 工具
    enable_audio_stream: bool = True         # 啟用音檔流服務
    enable_feedback_service: bool = True     # 啟用反饋服務
    enable_minio_episode: bool = True        # 啟用 MinIO 節目服務
    log_level: str = "INFO"                  # 日誌等級
```

## 開發規範
- 遵循 OOP 原則和 Google Clean Code 標準
- 所有服務模組都應該有完整的錯誤處理
- 使用統一的日誌配置
- 提供清晰的 API 文檔和類型提示
- 通過 main.py 統一管理所有服務