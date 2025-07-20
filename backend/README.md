# Podwise Backend 系統

## 📋 概述

Podwise Backend 是一個基於微服務架構的播客推薦系統，採用 OOP 設計原則和 Google Clean Code 標準。系統由多個核心模組組成，每個模組都遵循統一的架構標準，確保高內聚、低耦合的設計。

## 🏗️ 系統架構

```
Podwise Backend 系統架構
├── core/                      # 核心服務管理
│   ├── PodwiseServiceManager  # Podwise 核心業務邏輯
│   └── ServiceManager         # 通用服務管理
├── user_management/           # 用戶管理模組
│   └── IntegratedUserService  # 整合用戶服務
├── utils/                     # 統一工具模組
│   ├── 文本處理工具
│   ├── 向量搜尋引擎
│   ├── 環境配置管理
│   └── 共用服務組件
├── ml_pipeline/              # 機器學習管道
│   ├── 協同過濾推薦
│   ├── KNN 演算法
│   ├── 數據管理
│   └── 評估指標
├── rag_pipeline/             # 檢索增強生成管道
│   ├── 三層 CrewAI 架構
│   ├── 六層 RAG 處理
│   ├── 智能代理人系統
│   └── 層級化處理流程
├── tts/                      # 文字轉語音服務
├── stt/                      # 語音轉文字服務
├── vector_pipeline/          # 向量處理管道
├── data_cleaning/            # 數據清理模組
├── llm/                      # 語言模型模組
├── vaderSentiment/           # 情感分析模組
├── config/                   # 配置管理模組
├── n8n_pipline/             # N8N 工作流程
├── scripts/                  # 系統維護腳本
└── api/                      # API 網關
```

## 🎯 核心模組

### 🏛️ Core 模組 - 核心服務管理
**位置**: `backend/core/`

統一管理所有核心服務，提供系統基礎功能：

- **PodwiseServiceManager**: Podwise 核心業務邏輯
- **ServiceManager**: 通用服務管理
- **健康檢查**: 系統狀態監控
- **資源管理**: 連接池和資源清理

```python
# 快速使用
from core.main import get_core_manager

manager = get_core_manager()
podwise_service = manager.get_podwise_service()
```

### 👥 User Management 模組 - 用戶管理
**位置**: `backend/user_management/`

處理用戶相關的所有功能：

- **用戶註冊**: 用戶 ID 生成和驗證
- **偏好管理**: 用戶偏好設置和保存
- **反饋記錄**: 用戶行為和反饋追蹤
- **上下文管理**: 用戶會話和上下文維護

```python
# 快速使用
from user_management.main import get_user_management_manager

manager = get_user_management_manager()
user_service = manager.get_user_service()
```

### 🛠️ Utils 模組 - 統一工具服務
**位置**: `backend/utils/`

提供所有後端模組共用的工具和服務：

- **文本處理**: 語義分塊、標籤提取、向量化
- **向量搜尋**: Milvus 整合、相似度計算
- **環境配置**: MongoDB、Milvus、服務配置
- **共用工具**: 日誌、認證、核心服務

```python
# 快速使用
from utils import create_text_processor, create_vector_search

processor = create_text_processor()
search = create_vector_search()
```

### 🤖 ML Pipeline - 機器學習推薦
**位置**: `backend/ml_pipeline/`

專門處理協同過濾推薦算法：

- **KNN 協同過濾**: 基於用戶行為的推薦
- **數據管理**: MongoDB 數據載入和預處理
- **評估指標**: Precision、Recall、NDCG
- **API 服務**: RESTful 推薦接口

```python
# 快速使用
from ml_pipeline.core.recommender import CollaborativeFilteringRecommender

recommender = CollaborativeFilteringRecommender()
recommendations = recommender.recommend(user_id, top_k=5)
```

### 🔍 RAG Pipeline - 檢索增強生成
**位置**: `backend/rag_pipeline/`

基於 CrewAI 的三層架構和六層 RAG 處理：

- **三層代理人架構**: 領導者層、類別專家層、功能專家層
- **六層 RAG 處理**: 查詢處理→混合搜尋→檢索增強→重新排序→上下文壓縮→混合式RAG
- **智能備援**: OpenAI Web 搜尋備援
- **統一向量處理**: 整合 ML Pipeline 和向量搜尋

```python
# 快速使用
from rag_pipeline.core.hierarchical_rag_pipeline import HierarchicalRAGPipeline

pipeline = HierarchicalRAGPipeline()
response = await pipeline.process_query(query, user_id)
```

### 🔊 TTS 模組 - 文字轉語音
**位置**: `backend/tts/`

提供高品質的文字轉語音服務：

- **多語音支援**: 多種語音和語言
- **音頻處理**: 音頻格式轉換和優化
- **快取機制**: 音頻快取和重複使用
- **API 服務**: RESTful TTS 接口

### 🎤 STT 模組 - 語音轉文字
**位置**: `backend/stt/`

提供高精度的語音識別服務：

- **多格式支援**: MP3、WAV、FLAC 等
- **多語言支援**: 中文、英文、日文等
- **並發處理**: 多音頻文件同時處理
- **錯誤處理**: 完善的錯誤恢復機制

### 🔄 Vector Pipeline - 向量處理
**位置**: `backend/vector_pipeline/`

處理文本向量化和嵌入：

- **文本分塊**: 智能文本分割
- **向量化**: 文本轉換為向量表示
- **嵌入存儲**: 向量數據存儲和管理
- **相似度計算**: 向量相似度匹配

### 🧹 Data Cleaning - 數據清理
**位置**: `backend/data_cleaning/`

提供數據清理和預處理功能：

- **數據驗證**: 數據格式和完整性檢查
- **重複移除**: 重複數據識別和清理
- **格式標準化**: 數據格式統一
- **質量評估**: 數據質量評估和報告

### 🧠 LLM 模組 - 語言模型
**位置**: `backend/llm/`

整合各種語言模型服務：

- **模型管理**: 多種 LLM 模型整合
- **推理服務**: 文本生成和推理
- **模型切換**: 動態模型選擇
- **性能優化**: 模型載入和推理優化

### 😊 VaderSentiment - 情感分析
**位置**: `backend/vaderSentiment/`

提供情感分析功能：

- **雙重分析**: 中文和 VADER 情感分析
- **批量處理**: 大量文本批量分析
- **統計報告**: 情感分布和統計
- **結果可視化**: 情感分析結果展示

### ⚙️ Config 模組 - 配置管理
**位置**: `backend/config/`

統一管理系統配置：

- **環境配置**: 開發、測試、生產環境
- **服務配置**: 各模組服務配置
- **資料庫配置**: 多種資料庫連接配置
- **配置驗證**: 配置完整性和有效性檢查

### 🔄 N8N Pipeline - 工作流程
**位置**: `backend/n8n_pipline/`

管理自動化工作流程：

- **數據攝取**: 自動爬蟲和數據收集
- **數據處理**: 數據清理和轉換
- **工作流程**: N8N 工作流程管理
- **監控告警**: 工作流程狀態監控

### 📜 Scripts 模組 - 系統腳本
**位置**: `backend/scripts/`

提供系統維護和數據分析腳本：

- **MinIO 分析**: 節目數據分析
- **資料庫檢查**: 資料庫結構檢查
- **系統維護**: 系統清理和維護
- **數據備份**: 數據備份和恢復

### 🌐 API 模組 - API 網關
**位置**: `backend/api/`

提供統一的 API 接口：

- **路由管理**: 請求路由和負載均衡
- **認證授權**: 用戶認證和權限控制
- **請求處理**: 請求驗證和處理
- **響應格式**: 統一響應格式

## 🏗️ 架構標準化原則

### 1. 統一結構要求

每個模組都包含：
- **main.py**: 主入口點，統一管理所有模組功能
- **README.md**: 架構說明文檔
- **__init__.py**: 模組初始化文件
- **requirements.txt**: 依賴庫列表（如需要）
- **Dockerfile**: 容器化配置（如需要）

### 2. OOP 設計原則

- **單一職責原則**: 每個類別只負責一個特定功能
- **開放封閉原則**: 對擴展開放，對修改封閉
- **依賴倒置原則**: 依賴抽象而非具體實現
- **模組化設計**: 每個模組獨立，可重用

### 3. 模組獨立性

- 每個模組可以獨立運行和測試
- 模組間通過標準接口通信
- 避免循環依賴
- 最小化模組間耦合

### 4. 統一接口設計

#### 模組管理器接口
```python
class ModuleManager:
    def __init__(self):
        """初始化模組管理器"""
        pass
    
    def health_check(self) -> dict:
        """健康檢查"""
        pass
    
    def cleanup(self):
        """清理資源"""
        pass
```

#### 服務接口
```python
class Service:
    def __init__(self):
        """初始化服務"""
        pass
    
    def start(self):
        """啟動服務"""
        pass
    
    def stop(self):
        """停止服務"""
        pass
    
    def status(self) -> dict:
        """獲取服務狀態"""
        pass
```

## 🚀 快速開始

### 環境設置

```bash
# 克隆專案
git clone https://github.com/your-org/podwise.git
cd podwise/backend

# 創建虛擬環境
python -m venv venv_podwise
source venv_podwise/bin/activate  # Linux/Mac
# 或 venv_podwise\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 環境變數配置

```bash
# MongoDB 配置
export MONGO_HOST=worker3
export MONGO_PORT=27017
export MONGO_DB=podwise

# Milvus 配置
export MILVUS_HOST=worker3
export MILVUS_PORT=19530

# PostgreSQL 配置
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=podwise
export POSTGRES_USER=podwise
export POSTGRES_PASSWORD=password

# MinIO 配置
export MINIO_ENDPOINT=192.168.32.66:30090
export MINIO_ACCESS_KEY=your_access_key
export MINIO_SECRET_KEY=your_secret_key

# OpenAI 配置
export OPENAI_API_KEY=your_api_key

# 服務配置
export RAG_URL=http://rag-pipeline-service:8004
export ML_URL=http://ml-pipeline-service:8004
```

### 啟動服務

```bash
# 啟動核心服務
cd core
python main.py

# 啟動用戶管理服務
cd user_management
python main.py

# 啟動 ML Pipeline
cd ml_pipeline
python main.py

# 啟動 RAG Pipeline
cd rag_pipeline
python main.py

# 啟動 TTS 服務
cd tts
python main.py

# 啟動 STT 服務
cd stt
python main.py
```

## 🔄 數據流程

### 1. 用戶查詢處理流程
```
用戶查詢 → RAG Pipeline → ML Pipeline → Utils → 回應生成
```

### 2. 推薦生成流程
```
查詢分析 → 向量搜尋 → 協同過濾 → 結果融合 → 最終推薦
```

### 3. 備援處理流程
```
RAG 檢索 → 信心度評估 → Web 搜尋 → OpenAI 處理 → 備援回應
```

### 4. 音頻處理流程
```
音頻輸入 → STT 轉錄 → 文本處理 → TTS 合成 → 音頻輸出
```

## 📊 系統特性

### 🎯 設計原則

#### OOP 原則遵循
- **單一職責**: 每個模組專注特定功能
- **開放封閉**: 易於擴展，無需修改現有代碼
- **依賴反轉**: 依賴抽象而非具體實現

#### Google Clean Code 標準
- **清晰命名**: 描述性的變數和函數名
- **函數簡潔**: 單一功能，適當參數
- **完整文檔**: docstring 和類型註解
- **錯誤處理**: 統一異常處理機制

### 🔧 技術棧

#### 核心技術
- **Python 3.8+**: 主要開發語言
- **FastAPI**: Web 框架
- **CrewAI**: 代理人協作框架
- **LangChain**: LLM 整合框架

#### 數據存儲
- **MongoDB**: 文檔存儲 (worker3:27017)
- **Milvus**: 向量數據庫 (worker3:19530)
- **PostgreSQL**: 關係型數據庫
- **Redis**: 快取服務
- **MinIO**: 物件存儲

#### 機器學習
- **scikit-learn**: 協同過濾算法
- **numpy/pandas**: 數據處理
- **sentence-transformers**: 文本向量化
- **OpenAI**: LLM 服務

#### 音頻處理
- **Edge TTS**: 文字轉語音
- **Whisper**: 語音轉文字
- **FFmpeg**: 音頻格式轉換

## 📁 專案結構

```
backend/
├── core/                          # 核心服務管理
│   ├── main.py                    # 主入口點
│   ├── podwise_service_manager.py # Podwise 服務管理器
│   ├── service_manager.py         # 通用服務管理器
│   ├── __init__.py                # 模組初始化
│   └── README.md                  # 架構說明
├── user_management/               # 用戶管理模組
│   ├── main.py                    # 主入口點
│   ├── integrated_user_service.py # 整合用戶服務
│   ├── __init__.py                # 模組初始化
│   └── README.md                  # 架構說明
├── utils/                         # 統一工具模組
│   ├── main.py                    # 主入口點
│   ├── text_processing.py         # 文本處理工具
│   ├── vector_search.py           # 向量搜尋引擎
│   ├── env_config.py              # 環境配置
│   ├── common_utils.py            # 共用工具
│   └── README.md                  # 模組文檔
├── ml_pipeline/                   # 機器學習管道
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   ├── data_manager.py        # 數據管理
│   │   └── recommender.py         # 推薦引擎
│   ├── services/
│   │   └── api_service.py         # API 服務
│   ├── evaluation/
│   │   └── recommender_metrics.py # 評估指標
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── rag_pipeline/                  # 檢索增強生成管道
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   ├── integrated_core.py     # 統一核心
│   │   ├── crew_agents.py         # 代理人系統
│   │   ├── hierarchical_rag_pipeline.py  # 層級化 RAG
│   │   └── unified_vector_processor.py   # 統一向量處理
│   ├── tools/
│   │   └── enhanced_vector_search.py     # 增強向量搜尋
│   ├── config/
│   │   ├── agent_roles_config.py  # 代理人配置
│   │   └── hierarchical_rag_config.yaml  # RAG 配置
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── tts/                           # 文字轉語音模組
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   └── tts_service.py         # TTS 服務
│   ├── config/
│   │   └── voice_config.py        # 語音配置
│   ├── providers/
│   │   └── edge_tts_provider.py   # Edge TTS 提供者
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── stt/                           # 語音轉文字模組
│   ├── main.py                    # 主入口點
│   ├── stt_service.py             # STT 服務
│   ├── config/
│   │   └── stt_config.py          # STT 配置
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── vector_pipeline/               # 向量處理管道
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   └── batch_processor.py     # 批次處理器
│   ├── services/
│   │   └── embedding_service.py   # 嵌入服務
│   ├── config/
│   │   └── config_manager.py      # 配置管理器
│   └── README.md                  # 模組文檔
├── data_cleaning/                 # 數據清理模組
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   ├── base_cleaner.py        # 基礎清理器
│   │   └── episode_cleaner.py     # 節目清理器
│   ├── services/
│   │   └── cleaner_orchestrator.py # 清理協調器
│   └── README.md                  # 模組文檔
├── llm/                           # 語言模型模組
│   ├── main.py                    # 主入口點
│   ├── core/
│   │   ├── base_llm.py            # 基礎 LLM
│   │   └── huggingface_llm.py     # HuggingFace LLM
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── vaderSentiment/                # 情感分析模組
│   ├── main.py                    # 主入口點
│   ├── src/
│   │   ├── core/
│   │   │   ├── comment_analyzer.py # 評論分析器
│   │   │   └── podcast_ranking.py  # 播客排名
│   │   └── utils/
│   │       ├── data_processor.py   # 數據處理器
│   │       └── report_generator.py # 報告生成器
│   └── README.md                  # 模組文檔
├── config/                        # 配置管理模組
│   ├── main.py                    # 主入口點
│   ├── config_service.py          # 配置服務
│   ├── db_config.py               # 資料庫配置
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── n8n_pipline/                   # N8N 工作流程
│   ├── main.py                    # 主入口點
│   ├── ingestion/                 # 數據攝取
│   │   ├── auto_crawler.py        # 自動爬蟲
│   │   ├── PodcastScrap_ALL_v1.py # 播客爬取
│   │   ├── Spotify_Scrapy.py      # Spotify 爬取
│   │   ├── DcardPodcastFinal.py   # Dcard 播客爬取
│   │   ├── upload_to_minio.py     # MinIO 上傳
│   │   └── download_images.py     # 圖片下載
│   ├── data_cleaning/             # 數據清理
│   └── README.md                  # 模組文檔
├── scripts/                       # 系統腳本
│   ├── main.py                    # 主入口點
│   ├── analyze_minio_episodes.py  # MinIO 節目分析
│   ├── check_db_structure.py      # 資料庫結構檢查
│   └── README.md                  # 模組文檔
├── api/                           # API 網關
│   ├── main.py                    # 主入口點
│   ├── Dockerfile                 # 容器化配置
│   └── README.md                  # 模組文檔
├── unified_api_gateway.py         # 統一 API 網關
├── main.py                        # 主入口點
├── requirements.txt               # 依賴清單
├── Dockerfile                     # 容器化配置
└── README.md                      # 主文檔
```

## 📊 數據目錄保護

### Data 目錄結構 (`data/`)

```
data/
├── stage1_chunking/             # 第一階段：文本分塊
├── stage3_tagging/              # 第三階段：標籤處理
└── stage4_embedding_prep/       # 第四階段：嵌入準備
```

**保護措施**:
- 所有原始數據已保存
- 數據處理流程不影響原始數據
- 每個階段都有獨立的輸出目錄
- 支持數據恢復和重新處理

## 🧪 測試和評估

### 單元測試
```bash
# 測試所有模組
python -m pytest tests/

# 測試特定模組
python -m pytest core/tests/
python -m pytest user_management/tests/
python -m pytest utils/tests/
python -m pytest ml_pipeline/tests/
python -m pytest rag_pipeline/tests/
```

### 整合測試
```bash
# 測試模組間整合
python -m pytest integration_tests/

# 測試 API 端點
python -m pytest api_tests/
```

### 效能測試
```bash
# 載入測試
python -m pytest performance_tests/

# 記憶體使用測試
python -m pytest memory_tests/
```

## 🚀 部署指南

### Docker 部署

```bash
# 構建所有服務
docker-compose build

# 啟動所有服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps
```

### Kubernetes 部署

```bash
# 部署到 Kubernetes
kubectl apply -f k8s/

# 檢查部署狀態
kubectl get pods -n podwise

# 查看服務日誌
kubectl logs -f deployment/rag-pipeline -n podwise
```

### 服務監控

```bash
# 健康檢查
curl http://localhost:8004/health

# 服務狀態
curl http://localhost:8004/status

# 推薦測試
curl -X POST http://localhost:8004/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "科技播客推薦", "user_id": "test"}'
```

## 🔍 故障排除

### 常見問題

1. **模組導入失敗**
   ```bash
   # 檢查 Python 路徑
   export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
   
   # 檢查虛擬環境
   which python
   pip list
   ```

2. **服務連接失敗**
   ```bash
   # 檢查 MongoDB
   mongo --host worker3:27017 --eval "db.runCommand('ping')"
   
   # 檢查 Milvus
   curl http://worker3:19530/health
   
   # 檢查 PostgreSQL
   psql -h localhost -U podwise -d podwise -c "SELECT 1;"
   
   # 檢查 Redis
   redis-cli -h worker3 ping
   ```

3. **記憶體不足**
   ```bash
   # 檢查記憶體使用
   free -h
   
   # 調整批次大小
   export BATCH_SIZE=100
   
   # 啟用記憶體監控
   export MEMORY_MONITOR=true
   ```

### 日誌分析

```bash
# 查看應用日誌
tail -f logs/application.log

# 查看錯誤日誌
tail -f logs/error.log

# 查看效能日誌
tail -f logs/performance.log
```

## 📈 效能優化

### 系統效能
- **並行處理**: 多執行緒和異步 I/O
- **快取策略**: Redis 多層快取
- **連接池**: 資料庫連接復用
- **批次處理**: 大量數據分批處理

### 推薦效能
- **模型快取**: 預訓練模型快取
- **結果快取**: 推薦結果快取
- **增量更新**: 增量模型更新
- **負載均衡**: 多實例負載分散

## 🔐 安全性

### 認證授權
- **API 金鑰**: OpenAI API 金鑰管理
- **用戶認證**: 用戶身份驗證
- **權限控制**: 基於角色的訪問控制

### 數據安全
- **數據加密**: 敏感數據加密存儲
- **傳輸加密**: HTTPS/TLS 傳輸
- **數據脫敏**: 個人信息脫敏處理

## 🤝 貢獻指南

### 開發流程
1. **Fork 專案** 並創建功能分支
2. **遵循代碼規範** (PEP 8, Google Style Guide)
3. **添加測試** 確保功能正確性
4. **更新文檔** 包括 README 和 docstring
5. **提交 Pull Request** 並描述變更內容

### 代碼規範
- **命名規範**: 使用描述性名稱
- **函數設計**: 保持函數簡潔
- **註釋文檔**: 完整的 docstring
- **錯誤處理**: 適當的異常處理
- **測試覆蓋**: 新功能需要測試

## 📊 監控指標

### 系統指標
- **CPU 使用率**: 處理器負載
- **記憶體使用率**: 記憶體佔用
- **磁碟 I/O**: 磁碟讀寫性能
- **網路流量**: 網路傳輸量

### 業務指標
- **推薦準確率**: 推薦結果準確性
- **響應時間**: API 響應延遲
- **用戶滿意度**: 用戶反饋評分
- **系統可用性**: 服務可用時間

## 📄 授權

MIT License

## 📞 聯絡資訊

- **專案**: Podwise Backend System
- **團隊**: Podwise Development Team
- **版本**: 2.0.0
- **更新**: 2025年

---

**感謝使用 Podwise Backend 系統！**

如有任何問題或建議，請聯絡開發團隊或提交 Issue。 
