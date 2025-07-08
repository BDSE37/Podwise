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

## 🔧 配置管理

### 環境變數設置
```bash
# MongoDB 配置
export MONGO_HOST=worker3
export MONGO_PORT=27017
export MONGO_DB=podwise

# Redis 配置 (快取)
export REDIS_HOST=worker3
export REDIS_PORT=6379

# 服務配置
export ML_PIPELINE_PORT=8004
export ML_PIPELINE_HOST=0.0.0.0

# 推薦配置
export DEFAULT_TOP_K=10
export MIN_INTERACTIONS=5
export SIMILARITY_THRESHOLD=0.1
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

## 🔄 工作流程

### 1. 數據處理流程
```
原始數據 → 數據清洗 → 特徵工程 → 用戶-項目矩陣 → 模型訓練 → 推薦生成
```

### 2. 推薦流程
```
用戶請求 → 載入用戶歷史 → 計算相似度 → 生成推薦 → 結果排序 → 返回推薦
```

### 3. 評估流程
```
模型訓練 → 預測生成 → 指標計算 → 結果分析 → 模型優化
```

## 🎯 推薦算法

### 協同過濾 (Collaborative Filtering)
- **用戶基礎**: 基於用戶相似度的推薦
- **項目基礎**: 基於項目相似度的推薦
- **混合方法**: 結合用戶和項目的推薦

### 相似度計算
- **餘弦相似度**: 適用於稀疏數據
- **皮爾森相關係數**: 適用於評分數據
- **歐幾里得距離**: 適用於密集數據

### 冷啟動處理
- **新用戶**: 基於人口統計學的推薦
- **新項目**: 基於內容的推薦
- **混合策略**: 結合多種方法的推薦

## 🧪 測試和評估

### 單元測試
```bash
# 執行所有測試
python -m pytest tests/

# 測試推薦器
python -m pytest tests/test_recommender.py

# 測試數據管理
python -m pytest tests/test_data_manager.py
```

### 效能測試
```bash
# 推薦效能測試
python -m pytest tests/test_performance.py

# 記憶體使用測試
python -m pytest tests/test_memory.py
```

### 評估指標
```python
# 執行完整評估
python evaluation/recommender_metrics.py

# 計算所有指標
python -c "
from ml_pipeline.evaluation.recommender_metrics import RecommenderMetrics
metrics = RecommenderMetrics()
results = metrics.evaluate_all()
print(results)
"
```

## 📊 效能優化

### 記憶體優化
- **稀疏矩陣**: 使用 scipy.sparse 處理稀疏數據
- **批次處理**: 分批處理大量數據
- **記憶體映射**: 使用 mmap 處理大文件

### 計算優化
- **並行計算**: 使用 multiprocessing 並行處理
- **向量化**: 使用 numpy 向量化操作
- **快取機制**: Redis 快取推薦結果

### 算法優化
- **近似算法**: 使用 LSH 進行近似相似度計算
- **增量更新**: 支援增量模型更新
- **模型壓縮**: 壓縮模型大小以提高載入速度

## 🔍 故障排除

### 常見問題

1. **記憶體不足**
   ```bash
   # 檢查記憶體使用
   python -c "
   import psutil
   print(f'Memory usage: {psutil.virtual_memory().percent}%')
   "
   
   # 調整批次大小
   export BATCH_SIZE=1000
   ```

2. **MongoDB 連接失敗**
   ```bash
   # 檢查 MongoDB 服務
   mongo --host worker3:27017 --eval "db.runCommand('ping')"
   
   # 測試連接
   python -c "
   import pymongo
   client = pymongo.MongoClient('mongodb://worker3:27017/')
   print(client.server_info())
   "
   ```

3. **推薦結果為空**
   ```bash
   # 檢查數據量
   python -c "
   from ml_pipeline.core.data_manager import DataManager
   dm = DataManager()
   data = dm.load_user_interactions()
   print(f'Data size: {len(data)}')
   "
   
   # 檢查用戶互動數據
   python -c "
   from ml_pipeline.core.data_manager import DataManager
   dm = DataManager()
   user_stats = dm.get_user_stats()
   print(user_stats)
   "
   ```

## 🚀 部署指南

### Docker 部署
```bash
# 構建鏡像
docker build -t ml-pipeline .

# 運行容器
docker run -p 8004:8004 \
  -e MONGO_HOST=worker3 \
  -e MONGO_PORT=27017 \
  -e MONGO_DB=podwise \
  ml-pipeline
```

### Kubernetes 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-pipeline
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-pipeline
  template:
    metadata:
      labels:
        app: ml-pipeline
    spec:
      containers:
      - name: ml-pipeline
        image: ml-pipeline:latest
        ports:
        - containerPort: 8004
        env:
        - name: MONGO_HOST
          value: "worker3"
        - name: MONGO_PORT
          value: "27017"
        - name: MONGO_DB
          value: "podwise"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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
  -d '{"user_id": "test_user", "top_k": 5}'
```

## 📈 監控指標

### 系統指標
- **CPU 使用率**: 處理器使用情況
- **記憶體使用率**: 記憶體佔用情況
- **磁碟 I/O**: 磁碟讀寫速度
- **網路 I/O**: 網路傳輸速度

### 業務指標
- **推薦請求數**: 每秒推薦請求數量
- **推薦延遲**: 推薦響應時間
- **推薦準確率**: 推薦結果準確性
- **用戶滿意度**: 用戶反饋評分

### 監控設置
```python
# Prometheus 指標
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('ml_pipeline_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('ml_pipeline_request_duration_seconds', 'Request latency')
ACTIVE_USERS = Gauge('ml_pipeline_active_users', 'Active users')

# 使用示例
REQUEST_COUNT.inc()
REQUEST_LATENCY.observe(response_time)
ACTIVE_USERS.set(user_count)
```

## 🤝 貢獻指南

1. **代碼風格**: 遵循 PEP 8 和 Google Python Style Guide
2. **測試覆蓋**: 新功能需要添加相應測試
3. **文檔更新**: 更新相關文檔和註釋
4. **效能考慮**: 注意算法時間複雜度和空間複雜度
5. **向後兼容**: 保持 API 向後兼容性

## 📊 效能基準

### 推薦效能
- **單用戶推薦**: < 100ms
- **批次推薦**: < 5s (100 用戶)
- **模型訓練**: < 30min (100K 互動)
- **記憶體使用**: < 2GB (1M 用戶)

### 準確率指標
- **Precision@5**: > 0.15
- **Recall@5**: > 0.10
- **NDCG@5**: > 0.20
- **Coverage**: > 0.80

## 📄 授權

MIT License

---

**Podwise Team** | 版本: 1.0.0 