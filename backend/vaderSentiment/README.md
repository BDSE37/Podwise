# Podwise VADER Sentiment Analysis

## 概述

Podwise VADER Sentiment Analysis 是情感分析服務模組，使用 VADER 算法進行文本情感分析。採用 OOP 設計原則，提供統一的情感分析介面。

## 架構設計

### 核心組件

#### 1. 情感分析器 (Sentiment Analyzer)
- **職責**：核心情感分析功能
- **實現**：`SentimentAnalyzer` 類別
- **功能**：
  - 文本情感分析
  - 情感強度計算
  - 情感分類

#### 2. 文本預處理器 (Text Preprocessor)
- **職責**：文本預處理和清理
- **實現**：`TextPreprocessor` 類別
- **功能**：
  - 文本清理
  - 格式標準化
  - 語言檢測

#### 3. 情感分類器 (Sentiment Classifier)
- **職責**：情感分類和標籤
- **實現**：`SentimentClassifier` 類別
- **功能**：
  - 情感標籤分配
  - 置信度計算
  - 分類結果驗證

#### 4. 結果分析器 (Result Analyzer)
- **職責**：分析結果處理和統計
- **實現**：`ResultAnalyzer` 類別
- **功能**：
  - 結果統計
  - 趨勢分析
  - 報告生成

## 統一服務管理器

### VADERSentimentManager 類別
- **職責**：整合所有情感分析功能，提供統一的 OOP 介面
- **主要方法**：
  - `analyze_sentiment()`: 情感分析
  - `batch_analyze()`: 批次分析
  - `get_statistics()`: 獲取統計
  - `health_check()`: 健康檢查

### 分析流程
1. **文本輸入**：接收待分析文本
2. **預處理**：清理和標準化文本
3. **情感分析**：使用 VADER 算法分析
4. **結果分類**：分類和標籤結果
5. **結果輸出**：返回分析結果

## 配置系統

### 情感分析配置
- **檔案**：`config/sentiment_config.py`
- **功能**：
  - VADER 參數配置
  - 分類閾值設定
  - 語言支援配置

### 文本處理配置
- **檔案**：`config/text_config.py`
- **功能**：
  - 文本清理規則
  - 預處理參數
  - 格式標準化設定

## 數據模型

### 核心數據類別
- `SentimentRequest`: 情感分析請求
- `SentimentResult`: 情感分析結果
- `SentimentScore`: 情感分數
- `AnalysisReport`: 分析報告

### 工廠函數
- `create_sentiment_request()`: 創建分析請求
- `create_sentiment_result()`: 創建分析結果
- `create_sentiment_score()`: 創建情感分數

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的情感分析功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的情感分析算法
- 可擴展的分類策略

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的分析引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有分析器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合情感分析管理器
  - 分析服務控制
  - 健康檢查和統計

### 使用方式
```python
# 創建情感分析實例
from vader_sentiment.vader_sentiment_manager import VADERSentimentManager

manager = VADERSentimentManager()

# 單一文本分析
result = await manager.analyze_sentiment(
    text="這個播客節目非常有趣且富有啟發性！",
    language="zh-TW"
)

# 批次分析
batch_result = await manager.batch_analyze(
    texts=["文本1", "文本2", "文本3"],
    language="zh-TW"
)

# 獲取統計資訊
stats = manager.get_statistics()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證分析模型可用性
- 監控分析性能
- 檢查語言支援

### 性能指標
- 分析速度
- 準確率統計
- 處理效率
- 錯誤率監控

## 技術棧

- **框架**：FastAPI
- **情感分析**：VADER, NLTK
- **文本處理**：spaCy, NLTK
- **機器學習**：scikit-learn
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-vader-sentiment .

# 運行容器
docker run -p 8012:8012 podwise-vader-sentiment
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/analyze` - 情感分析
- `POST /api/v1/batch-analyze` - 批次分析
- `GET /api/v1/statistics` - 統計資訊
- `GET /api/v1/languages` - 支援語言

## 架構優勢

1. **高準確率**：使用成熟的 VADER 算法
2. **多語言支援**：支援多種語言分析
3. **可擴展性**：支援新的分析算法和語言
4. **可維護性**：清晰的模組化設計
5. **一致性**：統一的數據模型和介面設計 