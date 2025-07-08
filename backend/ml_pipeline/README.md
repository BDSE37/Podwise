# ML Pipeline - 播客推薦系統

## 功能概述

ML Pipeline 是一個基於機器學習的播客推薦系統，採用層級化架構設計，符合 Google Clean Code 原則。系統提供多種推薦算法，包括協同過濾、圖神經網路和混合推薦。

## 架構設計

### 核心功能

#### 1. 推薦算法

#### 基礎推薦器 (PodcastRecommender)
- 基於協同過濾的推薦
- **KNN 協同過濾**：使用 sklearn KNeighborsRegressor 進行評分預測
- **傳統協同過濾**：基於餘弦相似度的用戶相似度計算
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

#### 2. 數據管理

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

#### 3. 評估系統

#### 評估器 (RecommenderEvaluator)
- 準確率評估 (Precision, Recall)
- 多樣性評估
- 新穎性評估
- 用戶滿意度評估

## 使用方法

### KNN 協同過濾

```python
from core.podcast_recommender import PodcastRecommender

# 初始化 KNN 協同過濾推薦器
recommender = PodcastRecommender(
    podcast_data=podcast_df,
    user_history=user_history_df,
    use_knn=True,        # 啟用 KNN
    k_neighbors=5        # 設定 k 值
)

# 獲取推薦
recommendations = recommender.get_recommendations(
    user_id="user_123",
    top_k=10,
    category_filter="財經"
)
```

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

collaborative:
  use_knn: true           # 是否使用 KNN 協同過濾
  k_neighbors: 5          # KNN 的 k 值
  knn_weights: "distance" # KNN 權重方式 ('uniform', 'distance')
  knn_metric: "cosine"    # KNN 距離度量 ('cosine', 'euclidean', 'manhattan')
  rating_weight: 2.0      # 評分權重
  preview_weight: 1.0     # 預覽播放權重
  playtime_weight: 1.0    # 播放時間權重

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

### 2. 啟動服務
```bash
python main.py
```

### 3. Docker 部署
```bash
docker build -t ml-pipeline .
docker run -p 8004:8004 ml-pipeline
```

## 依賴項目

- fastapi
- uvicorn
- torch
- torch-geometric
- scikit-learn
- pandas
- numpy
- psycopg2-binary
- sqlalchemy

## 注意事項

- 確保 PostgreSQL 資料庫正在運行
- 大量數據處理時注意記憶體使用
- 模型訓練需要足夠的計算資源
- 定期更新推薦模型以保持準確性 