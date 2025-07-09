# Podwise RAG Pipeline

整合 Apple Podcast 排名系統的智能推薦引擎，提供統一的 OOP 介面。

## 功能特色

### 🎯 核心功能
- **Apple Podcast 優先推薦系統** - 基於評分、評論、使用者反饋的綜合評分
- **層級化 CrewAI 架構** - 三層代理協作處理複雜查詢
- **語意檢索** - text2vec-base-chinese + TAG_info.csv 混合檢索
- **提示詞模板系統** - 標準化的提示詞管理
- **聊天歷史記錄** - 完整的對話歷史追蹤
- **效能優化** - 多層級快取和並行處理

### 📊 Apple Podcast 排名系統
- **Apple Podcast 星等** (50%) - 官方評分權重最高
- **評論情感分析** (40%) - 使用 vaderSentiment 模組分析
- **使用者點擊率** (5%) - 用戶行為數據
- **Apple Podcast 評論數** (5%) - 熱度指標

## 系統架構

```
rag_pipeline/
├── main.py                    # 統一主介面
├── core/                      # 核心模組
│   ├── apple_podcast_ranking.py    # Apple Podcast 排名系統
│   ├── integrated_core.py          # 整合核心功能
│   ├── hierarchical_rag_pipeline.py # 層級化 RAG 架構
│   ├── crew_agents.py              # CrewAI 代理系統
│   ├── content_categorizer.py      # 內容分類器
│   ├── qwen_llm_manager.py         # LLM 管理器
│   └── chat_history_service.py     # 聊天歷史服務
├── config/                    # 配置模組
│   ├── integrated_config.py        # 統一配置
│   ├── prompt_templates.py         # 提示詞模板
│   └── agent_roles_config.py       # 代理角色配置
├── tools/                     # 工具模組
│   ├── enhanced_podcast_recommender.py # 增強推薦器
│   ├── enhanced_vector_search.py       # 向量搜尋
│   └── podcast_formatter.py           # Podcast 格式化
└── scripts/                   # 腳本模組
    ├── tag_processor.py             # 標籤處理器
    └── audio_transcription_pipeline.py # 音頻轉錄
```

## 快速開始

### 基本使用

```python
from backend.rag_pipeline import get_rag_pipeline

# 獲取 RAG Pipeline 實例
pipeline = get_rag_pipeline()

# 處理查詢
response = await pipeline.process_query(
    query="推薦一些投資理財的 Podcast",
    user_id="user123"
)

print(f"回應: {response.content}")
print(f"信心度: {response.confidence}")
```

### Apple Podcast 排名使用

```python
from backend.rag_pipeline import ApplePodcastRankingSystem

# 創建排名系統
ranking_system = ApplePodcastRankingSystem()

# 獲取增強推薦
enhanced_results = await pipeline.get_enhanced_recommendations(
    query="科技趨勢分析",
    user_id="user123"
)

print(f"推薦結果: {enhanced_results}")
```

### 健康檢查

```python
# 檢查系統健康狀態
health = await pipeline.health_check()
print(f"系統狀態: {health['status']}")

# 獲取系統資訊
info = pipeline.get_system_info()
print(f"版本: {info['version']}")
```

## 配置說明

### 環境變數

```bash
# LLM 配置
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# 資料庫配置
MONGODB_URI=mongodb://localhost:27017/podwise
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# 向量資料庫
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 監控配置
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
```

### 權重配置

```python
# Apple Podcast 排名權重
weights = {
    'apple_rating': 0.50,      # Apple Podcast 星等 (50%)
    'comment_sentiment': 0.40, # 評論情感分析 (40%)
    'click_rate': 0.05,        # 使用者點擊率 (5%)
    'review_count': 0.05       # Apple Podcast 評論數 (5%)
}
```

## 與 vaderSentiment 整合

RAG Pipeline 使用 vaderSentiment 模組進行評論情感分析：

```python
from backend.vaderSentiment import get_sentiment_analysis

# 獲取情感分析實例
sentiment_analyzer = get_sentiment_analysis()

# 分析評論情感
result = sentiment_analyzer.analyze_text(
    text="這個 Podcast 真的很棒！",
    analyzer_type="chinese"
)

print(f"情感標籤: {result.label}")
print(f"信心度: {result.confidence}")
```

## 效能優化

### 快取策略
- **LLM 回應快取** - 避免重複計算
- **向量搜尋快取** - 提升檢索速度
- **用戶偏好快取** - 個人化推薦

### 並行處理
- **多代理並行** - CrewAI 代理協作
- **向量搜尋並行** - 多來源同時檢索
- **批次處理** - 大量數據處理

## 監控與日誌

### 健康檢查
```python
health = await pipeline.health_check()
# 返回各組件狀態和配置資訊
```

### 系統資訊
```python
info = pipeline.get_system_info()
# 返回版本、功能列表、配置摘要
```

## 錯誤處理

系統提供完整的錯誤處理機制：

```python
try:
    response = await pipeline.process_query(query, user_id)
except Exception as e:
    # 自動記錄錯誤並返回友善訊息
    print(f"處理失敗: {e}")
```

## 開發指南

### 添加新的代理
1. 繼承 `BaseAgent` 類別
2. 實現 `process` 方法
3. 在 `AgentManager` 中註冊

### 擴展排名系統
1. 修改 `ApplePodcastRankingSystem` 權重
2. 添加新的評分維度
3. 更新計算邏輯

### 自定義提示詞
1. 在 `prompt_templates.py` 中添加模板
2. 使用 `format_prompt` 函數格式化
3. 在代理中使用

## 版本歷史

### v2.0.0 (當前版本)
- ✅ 整合 Apple Podcast 排名系統
- ✅ 統一 OOP 介面設計
- ✅ 符合 Google Clean Code 原則
- ✅ 完整的錯誤處理機制
- ✅ 與 vaderSentiment 模組整合

### v1.0.0
- ✅ 基礎 RAG Pipeline 功能
- ✅ CrewAI 代理架構
- ✅ 語意檢索系統

## 授權

本專案採用 MIT 授權條款。

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**Podwise Team** - 打造最智能的 Podcast 推薦系統 