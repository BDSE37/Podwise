# Podwise Backend

Podwise Backend 是一個模組化的微服務架構，整合了多個專業化的服務模組，嚴格遵循 OOP 原則和 Google Clean Code 規範。

## 模組結構

```
backend/
├── main.py                 # 統一入口點
├── api/                    # API 服務
│   ├── main.py            # API 服務入口
│   ├── app.py             # FastAPI 應用
│   └── requirements.txt   # API 依賴
├── config/                 # 配置管理
│   ├── main.py            # 配置服務入口
│   ├── config_service.py  # 配置服務
│   ├── db_config.py       # 資料庫配置
│   └── mongo_config.py    # MongoDB 配置
├── llm/                    # LLM 服務
│   ├── main.py            # LLM 服務入口
│   ├── llm_service.py     # LLM 服務
│   ├── core/              # LLM 核心組件
│   │   ├── base_llm.py    # 抽象基類
│   │   ├── qwen_llm.py    # Qwen 實作
│   │   └── ollama_llm.py  # Ollama 實作
│   └── requirements.txt   # LLM 依賴
├── ml_pipeline/            # ML Pipeline
│   ├── main.py            # ML Pipeline 入口
│   ├── core/              # 核心 ML 功能
│   ├── services/          # 服務層
│   ├── utils/             # 工具層
│   └── requirements.txt   # ML 依賴
├── rag_pipeline/           # RAG Pipeline
│   ├── main.py            # RAG Pipeline 入口
│   ├── app/               # CrewAI 應用
│   ├── core/              # 核心 RAG 功能
│   ├── utils/             # RAG 工具
│   └── requirements.txt   # RAG 依賴
├── stt/                    # 語音轉文字
│   ├── main.py            # STT 服務入口
│   └── requirements.txt   # STT 依賴
├── tts/                    # 文字轉語音
│   ├── main.py            # TTS 服務入口
│   └── requirements.txt   # TTS 依賴
├── utils/                  # 通用工具
│   ├── main.py            # 工具服務入口
│   ├── core_services.py   # 核心服務
│   ├── audio_search.py    # 音頻搜尋
│   └── common_utils.py    # 通用工具
└── vector_pipeline/        # 向量處理
    ├── main.py            # 向量處理入口
    └── requirements.txt   # 向量處理依賴
```

## 架構特點

### 模組化設計
- 每個模組獨立運行
- 清晰的職責分離
- 易於維護和擴展

### OOP 原則
- **封裝**：每個類別封裝相關的數據和方法
- **繼承**：使用抽象基類定義介面，具體實作繼承基類
- **多態性**：支援不同實作之間的替換
- **抽象**：使用 `ABC` 和 `@abstractmethod` 定義抽象介面

### Google Clean Code
- **清晰的命名規範**：類別和方法名稱具描述性
- **完整的文檔註釋**：每個模組都有詳細的 docstring
- **一致的代碼風格**：使用現代 Python 特性
- **單一職責原則**：每個類別都有明確的職責
- **依賴反轉**：依賴抽象而非具體實作

### 監控和測試
- Langfuse 整合
- 性能監控
- A/B 測試支援
- 完整的測試覆蓋

## 快速開始

### 1. 安裝依賴

```bash
# 安裝所有模組的依賴
cd backend
pip install -r requirements.txt

# 或安裝特定模組的依賴
cd rag_pipeline
pip install -r requirements.txt
```

### 2. 運行統一入口

```bash
# 運行整個 Backend 系統
python main.py
```

### 3. 運行特定模組

```bash
# 運行 RAG Pipeline
cd rag_pipeline
python main.py

# 運行 API 服務
cd api
python main.py

# 運行 ML Pipeline
cd ml_pipeline
python main.py
```

## 模組功能

### API 服務 (`api/`)
- 提供統一的 RESTful API 接口
- 整合所有後端服務
- 支援 FastAPI 框架

### 配置管理 (`config/`)
- 集中化配置管理
- 支援多環境配置
- 資料庫連接配置

### LLM 服務 (`llm/`)
- 大語言模型服務
- 支援多種 LLM 提供商（Qwen、Ollama）
- 模型管理和調用
- 抽象基類設計，易於擴展

### ML Pipeline (`ml_pipeline/`)
- 機器學習管道
- 推薦系統
- 模型訓練和推理
- 多種推薦策略（協同過濾、內容推薦、混合推薦）

### RAG Pipeline (`rag_pipeline/`)
- 檢索增強生成
- 三層 CrewAI 架構
- 智能 TAG 提取
- 向量搜尋
- Web Search 備援
- Langfuse 整合
- A/B 測試支援

### 語音轉文字 (`stt/`)
- 語音識別服務
- 支援多種音頻格式
- 即時轉錄功能

### 文字轉語音 (`tts/`)
- 語音合成服務
- 多種語音選項
- 自然語音輸出

### 通用工具 (`utils/`)
- 核心服務工具
- 音頻搜尋功能
- 通用工具函數
- 環境配置管理

### 向量處理 (`vector_pipeline/`)
- 向量化處理
- 嵌入模型管理
- 向量搜尋優化

## OOP 設計模式

### 1. 抽象工廠模式
```python
# LLM 服務使用抽象工廠模式
from llm.core import BaseLLM, QwenLLM, OllamaLLM

class LLMFactory:
    @staticmethod
    def create_llm(model_type: str, config: dict) -> BaseLLM:
        if model_type == "qwen":
            return QwenLLM(config)
        elif model_type == "ollama":
            return OllamaLLM(config)
```

### 2. 策略模式
```python
# 推薦系統使用策略模式
class Recommender:
    def __init__(self, strategy: str):
        self.strategy = self._get_strategy(strategy)
    
    def get_recommendations(self, user_id: int):
        return self.strategy.recommend(user_id)
```

### 3. 觀察者模式
```python
# 性能監控使用觀察者模式
class PerformanceMonitor:
    def __init__(self):
        self.observers = []
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.update(event)
```

## 代碼品質指標

### 模組化程度
- ✅ 19 個 `__init__.py` 檔案
- ✅ 每個模組都有明確的匯出介面
- ✅ 依賴關係清晰

### OOP 遵循度
- ✅ 使用抽象基類定義介面
- ✅ 繼承結構合理
- ✅ 封裝性良好
- ✅ 多態性支援

### Clean Code 遵循度
- ✅ 命名規範清晰
- ✅ 文檔註釋完整
- ✅ 代碼風格一致
- ✅ 職責分離明確

## 測試覆蓋

每個模組都包含：
- 單元測試
- 整合測試
- 性能測試
- 端到端測試

## 性能監控

- Langfuse 追蹤
- 性能指標收集
- A/B 測試支援
- 自動調優機制

## 重要注意事項

- 確保所有環境變數正確配置
- 定期檢查各服務的健康狀態
- 監控系統性能和回應時間
- 遵循 OOP 原則和 Clean Code 規範進行開發 