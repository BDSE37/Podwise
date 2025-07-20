# Podwise ML Pipeline

## 概述

Podwise ML Pipeline 是機器學習推薦系統模組，負責提供智能的 Podcast 推薦服務。採用協同過濾和內容基於推薦算法，結合深度學習技術，提供個性化的推薦體驗。

## 架構設計

### 核心組件

#### 1. 數據管理器 (Data Manager)
- **職責**：管理用戶行為數據和內容元數據
- **實現**：`DataManager` 類別
- **功能**：
  - 數據載入和預處理
  - 特徵工程
  - 數據驗證和清理

#### 2. 推薦引擎 (Recommender Engine)
- **職責**：核心推薦算法實現
- **實現**：`Recommender` 類別
- **功能**：
  - 協同過濾推薦
  - 內容基於推薦
  - 混合推薦策略

#### 3. 模型管理器 (Model Manager)
- **職責**：機器學習模型的管理和部署
- **實現**：`ModelManager` 類別
- **功能**：
  - 模型訓練和驗證
  - 模型版本管理
  - 模型性能監控

#### 4. 評估器 (Evaluator)
- **職責**：推薦系統性能評估
- **實現**：`RecommenderMetrics` 類別
- **功能**：
  - 準確率評估
  - 多樣性評估
  - A/B 測試支援

## 統一服務管理器

### MLPipelineManager 類別
- **職責**：整合所有 ML 功能，提供統一的 OOP 介面
- **主要方法**：
  - `get_recommendations()`: 獲取推薦
  - `train_model()`: 訓練模型
  - `evaluate_model()`: 評估模型
  - `health_check()`: 健康檢查

### 推薦流程
1. **用戶分析**：分析用戶歷史行為和偏好
2. **內容分析**：分析 Podcast 內容特徵
3. **相似度計算**：計算用戶-內容相似度
4. **推薦生成**：生成個性化推薦列表
5. **結果排序**：根據多個指標排序結果

## 配置系統

### ML 配置
- **檔案**：`config/recommender_config.py`
- **功能**：
  - 推薦算法參數
  - 模型配置
  - 評估指標設定

### 數據配置
- **檔案**：`config/data_config.py`
- **功能**：
  - 數據源配置
  - 特徵工程參數
  - 數據預處理設定

## 數據模型

### 核心數據類別
- `UserProfile`: 用戶檔案數據
- `ContentProfile`: 內容檔案數據
- `RecommendationResult`: 推薦結果
- `ModelMetrics`: 模型指標

### 工廠函數
- `create_user_profile()`: 創建用戶檔案
- `create_content_profile()`: 創建內容檔案
- `create_recommendation_result()`: 創建推薦結果

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的 ML 功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的推薦算法
- 可擴展的模型架構

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的推薦算法

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有推薦器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合 ML 管道管理器
  - 推薦服務控制
  - 健康檢查和模型資訊

### 使用方式
```python
# 創建 ML 管道實例
from core.ml_pipeline_manager import MLPipelineManager

pipeline = MLPipelineManager()

# 獲取推薦
recommendations = await pipeline.get_recommendations(
    user_id="Podwise0001",
    category="business",
    limit=10
)

# 訓練模型
training_result = await pipeline.train_model(
    model_type="collaborative_filtering",
    data_source="user_interactions"
)

# 評估模型
evaluation_result = await pipeline.evaluate_model(
    model_id="latest",
    test_data="validation_set"
)
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證模型可用性
- 監控推薦性能
- 檢查數據源連接

### 性能指標
- 推薦準確率
- 推薦多樣性
- 用戶滿意度
- 模型訓練時間

## 技術棧

- **框架**：FastAPI
- **ML 庫**：scikit-learn, TensorFlow
- **數據處理**：Pandas, NumPy
- **推薦算法**：協同過濾、內容基於、深度學習
- **數據庫**：PostgreSQL, Redis
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-ml-pipeline .

# 運行容器
docker run -p 8002:8002 podwise-ml-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/recommend` - 獲取推薦
- `POST /api/v1/train` - 訓練模型
- `POST /api/v1/evaluate` - 評估模型
- `GET /api/v1/models` - 模型資訊

## 架構優勢

1. **個性化**：基於用戶行為的個性化推薦
2. **可擴展性**：支援多種推薦算法
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的性能指標
5. **一致性**：統一的數據模型和介面設計