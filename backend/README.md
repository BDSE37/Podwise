# Podwise Backend 系統

## 📋 概述

Podwise Backend 是一個基於微服務架構的播客推薦系統，採用 OOP 設計原則和 Google Clean Code 標準。系統由三個核心模組組成：統一工具模組 (Utils)、機器學習管道 (ML Pipeline) 和檢索增強生成管道 (RAG Pipeline)。

## 🏗️ 系統架構

```
Podwise Backend 系統架構
├── utils/                    # 統一工具模組
│   ├── 文本處理工具
│   ├── 向量搜尋引擎
│   ├── 環境配置管理
│   └── 共用服務組件
├── ml_pipeline/             # 機器學習管道
│   ├── 協同過濾推薦
│   ├── KNN 演算法
│   ├── 數據管理
│   └── 評估指標
└── rag_pipeline/            # 檢索增強生成管道
    ├── 三層 CrewAI 架構
    ├── 六層 RAG 處理
    ├── 智能代理人系統
    └── 層級化處理流程
```

## 🎯 核心模組

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

# OpenAI 配置
export OPENAI_API_KEY=your_api_key

# 服務配置
export RAG_URL=http://rag-pipeline-service:8004
export ML_URL=http://ml-pipeline-service:8004
```

### 啟動服務

```bash
# 啟動 ML Pipeline
cd ml_pipeline
python main.py

# 啟動 RAG Pipeline
cd rag_pipeline
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
- **Redis**: 快取服務
- **PostgreSQL**: 關係型數據庫

#### 機器學習
- **scikit-learn**: 協同過濾算法
- **numpy/pandas**: 數據處理
- **sentence-transformers**: 文本向量化
- **OpenAI**: LLM 服務

## 🧪 測試和評估

### 單元測試
```bash
# 測試所有模組
python -m pytest tests/

# 測試特定模組
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

## 📁 專案結構

```
backend/
├── utils/                          # 統一工具模組
│   ├── text_processing.py          # 文本處理工具
│   ├── vector_search.py            # 向量搜尋引擎
│   ├── env_config.py               # 環境配置
│   ├── common_utils.py             # 共用工具
│   └── README.md                   # 模組文檔
├── ml_pipeline/                    # 機器學習管道
│   ├── core/
│   │   ├── data_manager.py         # 數據管理
│   │   └── recommender.py          # 推薦引擎
│   ├── services/
│   │   └── api_service.py          # API 服務
│   ├── evaluation/
│   │   └── recommender_metrics.py  # 評估指標
│   └── README.md                   # 模組文檔
├── rag_pipeline/                   # 檢索增強生成管道
│   ├── core/
│   │   ├── integrated_core.py      # 統一核心
│   │   ├── crew_agents.py          # 代理人系統
│   │   ├── hierarchical_rag_pipeline.py  # 層級化 RAG
│   │   └── unified_vector_processor.py   # 統一向量處理
│   ├── tools/
│   │   └── enhanced_vector_search.py     # 增強向量搜尋
│   ├── config/
│   │   ├── agent_roles_config.py   # 代理人配置
│   │   └── hierarchical_rag_config.yaml  # RAG 配置
│   └── README.md                   # 模組文檔
├── requirements.txt                # 依賴清單
└── README.md                      # 主文檔
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
- **更新**: 2024年

---

**感謝使用 Podwise Backend 系統！**

如有任何問題或建議，請聯絡開發團隊或提交 Issue。 