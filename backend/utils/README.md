# Podwise 統一工具模組 (Utils)

## 📋 概述

Podwise 統一工具模組提供給所有後端模組使用的共用工具和服務，遵循 OOP 原則和 Google Clean Code 標準。

## 🎯 核心功能

### 📝 文本處理 (text_processing.py)
- **文本分塊**: 語義文本分塊器，支援自定義分塊大小和重疊
- **標籤處理**: 統一標籤提取器，支援 CSV 詞庫
- **嵌入向量**: 文本向量化處理
- **文本清理**: 標準化和清理文本內容

### 🔍 向量搜尋 (vector_search.py)
- **Milvus 整合**: 向量資料庫搜尋
- **相似度計算**: 餘弦相似度、歐幾里得距離、內積計算
- **統一搜尋介面**: 支援多種向量搜尋引擎
- **結果格式化**: 標準化搜尋結果

### 🛠️ 共用工具 (common_utils.py)
- **字典轉屬性**: DictToAttrRecursive 類別
- **路徑處理**: 路徑清理和驗證
- **文件操作**: 檔案大小格式化、副檔名提取
- **重試機制**: 自動重試裝飾器
- **去重功能**: 列表去重處理

### ⚙️ 環境配置 (env_config.py)
- **MongoDB 配置**: worker3 容器配置
- **Milvus 配置**: 向量資料庫配置
- **服務 URL**: 各微服務端點配置
- **配置驗證**: 配置完整性檢查

### 📊 日誌配置 (logging_config.py)
- **彩色日誌**: 使用 colorlog 的彩色輸出
- **統一格式**: 標準化日誌格式
- **多級別支援**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 🎵 音頻搜尋 (audio_search.py)
- **智能音檔搜尋**: 根據內容推薦相關音檔
- **商業播客**: 股癌、矽谷輕鬆談、科技早餐等
- **音樂風格**: 古典、流行、電子、爵士等
- **情感分析**: 愉悅、放鬆、激勵等氛圍音樂

### 🔐 用戶認證 (user_auth_service.py)
- **用戶驗證**: 用戶 ID 驗證和管理
- **訪客模式**: 訪客用戶創建和管理
- **聊天記錄**: 用戶聊天歷史保存
- **行為統計**: 用戶行為追蹤和分析

### 🏗️ 核心服務 (core_services.py)
- **基礎服務**: BaseService 抽象類別
- **服務管理**: ServiceManager 生命週期管理
- **模型服務**: ModelService ML 模型管理
- **健康檢查**: 服務狀態監控

### 🌐 Langfuse 整合 (langfuse_client.py)
- **追蹤監控**: LLM 調用追蹤
- **雲端服務**: Langfuse Cloud 整合
- **效能監控**: 模型效能分析

## 🚀 快速開始

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 基本使用

#### 文本處理
```python
from utils import create_text_processor, TextChunk

# 創建文本處理器
processor = create_text_processor(
    tag_csv_path="path/to/tags.csv",
    chunk_size=1000,
    overlap=200
)

# 處理文本
chunks = processor.process_text("您的文本內容")
for chunk in chunks:
    print(f"分塊 {chunk.chunk_index}: {chunk.chunk_text[:100]}...")
    print(f"標籤: {chunk.tags}")
```

#### 向量搜尋
```python
from utils import create_vector_search

# 創建向量搜尋
vector_search = create_vector_search(
    host="worker3",
    port=19530,
    collection_name="podwise_vectors"
)

# 執行搜尋
results = vector_search.search_by_text(
    query_text="科技播客推薦",
    embedding_model=your_model,
    top_k=5
)
```

#### 環境配置
```python
from utils import PodriConfig

# 載入配置
config = PodriConfig()
config.print_config_summary()

# 獲取 MongoDB 配置
mongo_config = config.get_mongodb_config()
print(f"MongoDB URI: {mongo_config['uri']}")
```

#### 日誌配置
```python
from utils import setup_logging, get_logger

# 設定日誌
setup_logging(level=logging.INFO)

# 獲取日誌記錄器
logger = get_logger(__name__)
logger.info("這是一條資訊日誌")
```

## 🔧 主要設定

### 環境變數
```bash
# MongoDB 配置
MONGO_HOST=worker3
MONGO_PORT=27017
MONGO_DB=podwise

# Milvus 配置
MILVUS_HOST=worker3
MILVUS_PORT=19530

# 服務配置
RAG_URL=http://rag-pipeline-service:8004
ML_URL=http://ml-pipeline-service:8004
TTS_URL=http://tts-service:8501
STT_URL=http://stt-service:8501

# OpenAI 配置（選用）
OPENAI_API_KEY=your_api_key

# Langfuse 配置
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
```

## 📁 檔案結構

```
utils/
├── __init__.py              # 模組導出介面
├── text_processing.py       # 文本處理工具
├── vector_search.py         # 向量搜尋工具
├── common_utils.py          # 共用工具函數
├── env_config.py           # 環境配置管理
├── logging_config.py       # 日誌配置
├── audio_search.py         # 音頻搜尋服務
├── user_auth_service.py    # 用戶認證服務
├── core_services.py        # 核心服務基類
├── langfuse_client.py      # Langfuse 整合
├── intelligent_audio_search.py  # 智能音頻搜尋
└── main.py                 # 主程式入口
```

## 🎯 設計原則

### OOP 原則
- **單一職責**: 每個類別專注單一功能
- **開放封閉**: 易於擴展，無需修改現有代碼
- **依賴反轉**: 依賴抽象而非具體實現

### Google Clean Code 標準
- **清晰命名**: 使用描述性的變數和函數名
- **函數簡潔**: 單一功能，適當參數數量
- **完整文檔**: docstring 和類型註解
- **錯誤處理**: 統一的異常處理機制

## 🧪 測試

```bash
# 運行主程式測試
python main.py

# 測試文本處理
python -c "from utils import create_text_processor; print('Text processing OK')"

# 測試向量搜尋
python -c "from utils import create_vector_search; print('Vector search OK')"
```