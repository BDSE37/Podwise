# Podwise ML Pipeline 系統

## 📋 概述

Podwise ML Pipeline 是一個專門處理機器學習推薦的模組，主要負責協同過濾 (Collaborative Filtering) 的 KNN 推薦算法。系統遵循 OOP 原則和 Google Clean Code 標準，為 RAG Pipeline 提供精確的播客推薦服務。

## 🎯 核心功能

### 🤖 協同過濾推薦 (collaborative_filtering.py)
- **KNN 演算法**: 基於用戶行為的協同過濾推薦
- **相似度計算**: 餘弦相似度、皮爾森相關係數
- **冷啟動處理**: 新用戶和新項目的推薦策略
- **評分預測**: 用戶對未知項目的評分預測

### 📊 數據管理 (data_manager.py)
- **數據載入**: 從 MongoDB 載入用戶行為數據
- **數據預處理**: 清洗、標準化、特徵工程
- **數據分割**: 訓練集、測試集分割
- **數據更新**: 增量數據更新機制

### 🔧 推薦引擎 (recommender.py)
- **統一推薦介面**: 標準化推薦 API
- **多策略推薦**: 支援多種推薦算法
- **結果融合**: 多算法結果融合
- **效能優化**: 快取機制、並行處理

### 📈 評估指標 (recommender_metrics.py)
- **準確率評估**: Precision、Recall、F1-Score
- **排序評估**: NDCG、MAP、MRR
- **多樣性評估**: 推薦結果多樣性分析
- **覆蓋率評估**: 推薦覆蓋率統計

### 🌐 API 服務 (api_service.py)
- **RESTful API**: 標準化 HTTP 接口
- **批次推薦**: 批量用戶推薦處理
- **實時推薦**: 單用戶實時推薦
- **健康檢查**: 服務狀態監控

## 🚀 快速開始

### 環境設置
```bash
# 進入虛擬環境
source venv_podwise/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 基本使用

#### 1. 協同過濾推薦
```python
from ml_pipeline.core.recommender import CollaborativeFilteringRecommender

# 創建推薦器
recommender = CollaborativeFilteringRecommender(
    n_neighbors=10,
    similarity_metric='cosine'
)

# 訓練模型
recommender.fit(user_item_matrix)

# 獲取推薦
recommendations = recommender.recommend(
    user_id="user123",
    top_k=5
)

for item in recommendations:
    print(f"推薦: {item['title']} (評分: {item['score']:.2f})")
```

#### 2. 數據管理
```python
from ml_pipeline.core.data_manager import DataManager

# 創建數據管理器
data_manager = DataManager(
    mongo_uri="mongodb://worker3:27017/podwise"
)

# 載入數據
user_data = data_manager.load_user_interactions()
item_data = data_manager.load_item_features()

# 預處理數據
processed_data = data_manager.preprocess_data(user_data, item_data)

# 創建用戶-項目矩陣
user_item_matrix = data_manager.create_user_item_matrix(processed_data)
```

#### 3. API 服務
```python
from ml_pipeline.services.api_service import MLPipelineAPI

# 創建 API 服務
api = MLPipelineAPI()

# 啟動服務
api.run(host="0.0.0.0", port=8004)
```

#### 4. 評估指標
```python
from ml_pipeline.evaluation.recommender_metrics import RecommenderMetrics

# 創建評估器
metrics = RecommenderMetrics()

# 計算準確率
precision = metrics.calculate_precision(y_true, y_pred, k=5)
recall = metrics.calculate_recall(y_true, y_pred, k=5)
f1_score = metrics.calculate_f1_score(precision, recall)

print(f"Precision@5: {precision:.4f}")
print(f"Recall@5: {recall:.4f}")
print(f"F1-Score@5: {f1_score:.4f}")

# 計算 NDCG
ndcg = metrics.calculate_ndcg(y_true, y_pred, k=5)
print(f"NDCG@5: {ndcg:.4f}")
```

## 🔧 主要設定

### 環境變數設置
```bash
# MongoDB 配置
MONGO_HOST=worker3
MONGO_PORT=27017
MONGO_DB=podwise

# Redis 配置 (快取)
REDIS_HOST=worker3
REDIS_PORT=6379

# 服務配置
ML_PIPELINE_PORT=8004
ML_PIPELINE_HOST=0.0.0.0

# 推薦配置
DEFAULT_TOP_K=10
MIN_INTERACTIONS=5
SIMILARITY_THRESHOLD=0.1
```

### 配置檔案 (config/recommender_config.py)
```python
# 推薦器配置
RECOMMENDER_CONFIG = {
    'collaborative_filtering': {
        'n_neighbors': 10,
        'similarity_metric': 'cosine',
        'min_interactions': 5,
        'max_recommendations': 50
    },
    'data_processing': {
        'min_rating': 1.0,
        'max_rating': 5.0,
        'implicit_feedback': True,
        'normalize_ratings': True
    },
    'evaluation': {
        'test_size': 0.2,
        'random_state': 42,
        'cross_validation_folds': 5
    },
    'caching': {
        'enable_cache': True,
        'cache_ttl': 3600,  # 1 小時
        'max_cache_size': 10000
    }
}
```

## 📁 檔案結構

```
ml_pipeline/
├── __init__.py
├── main.py                     # 主程式入口
├── Dockerfile                  # Docker 容器配置
├── requirements.txt            # 依賴包清單
├── config/
│   ├── __init__.py
│   └── recommender_config.py   # 推薦器配置
├── core/
│   ├── __init__.py
│   ├── data_manager.py         # 數據管理
│   └── recommender.py          # 推薦引擎
├── services/
│   ├── __init__.py
│   └── api_service.py          # API 服務
└── evaluation/
    ├── __init__.py
    └── recommender_metrics.py  # 評估指標
``` 