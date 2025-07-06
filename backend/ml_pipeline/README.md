# ML Pipeline - 播客推薦系統

## 概述

ML Pipeline 是一個基於機器學習的播客推薦系統，採用層級化架構設計，符合 Google Clean Code 原則。系統提供多種推薦算法，包括協同過濾、圖神經網路和混合推薦。

## 架構設計

### 目錄結構

```
ml_pipeline/
├── core/                    # 核心功能模組
│   ├── __init__.py         # 核心模組匯入介面
│   ├── podcast_recommender.py      # 基礎播客推薦器
│   ├── gnn_podcast_recommender.py  # GNN 推薦器
│   ├── hybrid_gnn_recommender.py   # 混合推薦器
│   ├── recommender.py              # 基礎推薦器
│   ├── recommender_data.py         # 數據管理
│   ├── recommender_evaluator.py    # 評估器
│   └── recommender_main.py         # 主控制器
├── services/               # 服務層
│   ├── __init__.py        # 服務層匯入介面
│   └── recommendation_service.py  # 推薦服務
├── utils/                  # 工具層
│   ├── __init__.py        # 工具層匯入介面
│   └── embedding_data_loader.py   # 數據載入器
├── config/                 # 配置管理
│   ├── __init__.py        # 配置匯入介面
│   └── recommender_config.py     # 推薦配置
├── tests/                  # 測試模組
│   ├── __init__.py        # 測試匯入介面
│   └── test_ml_pipeline.py       # 整合測試
├── main.py                 # FastAPI 主入口
├── requirements.txt        # 依賴套件
├── Dockerfile             # Docker 配置
└── README.md              # 說明文件
```

### 設計原則

1. **分層架構**: 核心、服務、工具、配置分離
2. **單一職責**: 每個模組專注於特定功能
3. **依賴注入**: 通過配置和參數傳遞依賴
4. **錯誤處理**: 統一的異常處理機制
5. **日誌記錄**: 完整的操作日誌
6. **型別註解**: 完整的型別提示

## 核心功能

### 1. 推薦算法

#### 基礎推薦器 (PodcastRecommender)
- 基於協同過濾的推薦
- 支援用戶-項目矩陣
- 可配置的相似度計算

#### GNN 推薦器 (GNNPodcastRecommender)
- 圖神經網路推薦
- 用戶-播客圖結構
- 節點嵌入學習

#### 混合推薦器 (HybridGNNRecommender)
- 多算法融合
- 動態權重調整
- 集成學習策略

### 2. 數據管理

#### 數據載入器 (EmbeddingDataLoader)
```python
from utils import EmbeddingDataLoader

# 初始化載入器
loader = EmbeddingDataLoader(connection_string)

# 載入轉錄數據
transcripts = loader.load_episode_transcripts(min_length=30)

# 載入元數據
metadata = loader.load_episode_metadata(episode_ids=[1, 2, 3])

# 獲取統計信息
stats = loader.get_transcript_statistics()
```

#### 數據管理器 (RecommenderData)
- PostgreSQL 數據連接
- 用戶行為數據管理
- 節目元數據查詢

### 3. 評估系統

#### 評估器 (RecommenderEvaluator)
- 準確率評估 (Precision, Recall)
- 多樣性評估
- 新穎性評估
- 用戶滿意度評估

## 服務層

### 推薦服務 (RecommendationService)

```python
from services import RecommendationService
from config import get_recommender_config

# 初始化服務
config = get_recommender_config()
service = RecommendationService(db_url, config)

# 獲取推薦
recommendations = await service.get_recommendations(
    user_id=1,
    top_k=10,
    category_filter="科技"
)

# 獲取相似節目
similar_episodes = await service.get_similar_episodes(
    episode_id=1,
    limit=5
)

# 評估推薦結果
metrics = await service.evaluate_recommendations(
    user_id=1,
    recommendations=recommendations
)
```

## API 端點

### 主要端點

- `GET /` - 服務狀態
- `GET /health` - 健康檢查
- `POST /recommendations` - 獲取推薦
- `POST /similar-episodes` - 獲取相似節目
- `POST /user-preferences` - 更新用戶偏好
- `POST /evaluate` - 評估推薦結果
- `GET /status` - 系統狀態
- `POST /batch-recommendations` - 批次推薦

### 使用範例

```bash
# 獲取推薦
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "top_k": 10,
    "category_filter": "科技"
  }'

# 獲取相似節目
curl -X POST "http://localhost:8000/similar-episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "episode_id": 1,
    "limit": 5
  }'
```

## 配置管理

### 配置結構

```yaml
base:
  algorithm: "collaborative_filtering"
  similarity_metric: "cosine"
  top_k: 10

gnn:
  hidden_dim: 64
  num_layers: 2
  dropout: 0.1

hybrid:
  weights:
    collaborative: 0.4
    gnn: 0.4
    content: 0.2

database_url: "postgresql://user:password@localhost:5432/podwise"
```

### 環境變數

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/podwise"
export LOG_LEVEL="INFO"
export MODEL_PATH="/path/to/models"
```

## 安裝與運行

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯環境變數
vim .env
```

### 3. 運行服務

```bash
# 開發模式
python main.py

# 生產模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Docker 運行

```bash
# 建構映像
docker build -t ml-pipeline .

# 運行容器
docker run -p 8000:8000 ml-pipeline
```

## 測試

### 運行測試

```bash
# 運行所有測試
python tests/test_ml_pipeline.py

# 運行特定測試
python -m pytest tests/ -v
```

### 測試覆蓋率

```bash
python -m pytest tests/ --cov=core --cov=services --cov=utils
```

## 監控與日誌

### 日誌配置

```python
import logging

# 設定日誌級別
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 監控指標

- 推薦準確率
- 回應時間
- 系統資源使用率
- 錯誤率

## 與其他模組整合

### 與 RAG Pipeline 整合

```python
from rag_pipeline.core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
from ml_pipeline.services import RecommendationService

# 初始化 RAG Pipeline
rag_pipeline = HierarchicalRAGPipeline()

# 初始化推薦服務
recommendation_service = RecommendationService(db_url, config)

# 結合 RAG 和推薦
async def hybrid_recommendation(query: str, user_id: int):
    # RAG 處理查詢
    rag_response = await rag_pipeline.process_query(query)
    
    # 推薦相關節目
    recommendations = await recommendation_service.get_recommendations(
        user_id=user_id,
        context={"rag_response": rag_response}
    )
    
    return {
        "rag_response": rag_response,
        "recommendations": recommendations
    }
```

### 與監控面板整合

```python
from monitoring.hierarchical_dashboard import HierarchicalRAGMonitor

# 在監控面板中添加推薦系統指標
class EnhancedMonitor(HierarchicalRAGMonitor):
    def get_recommendation_metrics(self):
        """獲取推薦系統指標"""
        return {
            'recommendation_accuracy': 0.85,
            'user_satisfaction': 0.87,
            'diversity_score': 0.78
        }
```

## 開發指南

### 代碼風格

- 遵循 Google Python Style Guide
- 使用型別註解
- 完整的文檔字串
- 單元測試覆蓋

### 新增功能

1. 在對應層級添加新模組
2. 更新 `__init__.py` 匯入介面
3. 添加單元測試
4. 更新文檔

### 錯誤處理

```python
try:
    result = await service.get_recommendations(user_id)
except Exception as e:
    logger.error(f"推薦生成失敗: {str(e)}")
    # 返回預設結果或錯誤回應
```

## 性能優化

### 快取策略

- Redis 快取熱門推薦
- 數據庫連接池
- 模型預載入

### 非同步處理

- 使用 asyncio 處理並發請求
- 背景任務處理
- 批次推薦優化

## 故障排除

### 常見問題

1. **資料庫連接失敗**
   - 檢查 DATABASE_URL 設定
   - 確認資料庫服務運行狀態

2. **模型載入失敗**
   - 檢查模型檔案路徑
   - 確認依賴套件版本

3. **推薦結果為空**
   - 檢查用戶數據是否存在
   - 確認推薦算法配置

### 日誌分析

```bash
# 查看錯誤日誌
grep "ERROR" logs/ml_pipeline.log

# 查看性能日誌
grep "processing_time" logs/ml_pipeline.log
```

## 版本歷史

- **v1.0.0**: 初始版本，基礎推薦功能
- **v1.1.0**: 添加 GNN 推薦器
- **v1.2.0**: 重構為層級化架構
- **v1.3.0**: 添加混合推薦和評估系統

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 授權

本專案採用 MIT 授權條款。 