# Podwise RAG Pipeline

整合 Apple Podcast 排名系統和 MCP (Model Context Protocol) 的智能推薦引擎，提供統一的 OOP 介面。

## 功能特色

### 🎯 核心功能
- **Apple Podcast 優先推薦系統** - 基於評分、評論、使用者反饋的綜合評分
- **MCP (Model Context Protocol) 整合** - 動態工具調用和外部資源整合
- **層級化 CrewAI 架構** - 三層代理協作處理複雜查詢
- **Langfuse Cloud 追蹤** - 全流程可視化監控

### 📊 Apple Podcast 排名權重
- **Apple Podcast 星等** (50%) - 官方評分權重最高
- **評論情感分析** (40%) - 使用 vaderSentiment 模組分析
- **使用者點擊率** (5%) - 用戶行為數據
- **Apple Podcast 評論數** (5%) - 熱度指標

## 系統架構

### 目錄結構

```
rag_pipeline/
├── main.py                    # 統一主介面
├── core/                      # 核心模組
│   ├── integrated_core.py          # 統一數據結構、查詢處理、信心值控制
│   ├── mcp_integration.py          # MCP 工具/資源註冊、調用、快取
│   ├── enhanced_podcast_recommender.py # MCP 增強推薦器
│   ├── apple_podcast_ranking.py    # Apple Podcast 排名系統
│   ├── langfuse_tracking.py        # Langfuse Cloud 追蹤工具
│   ├── agent_manager.py            # 代理管理器
│   └── api_models.py               # API 模型定義
├── config/                    # 配置模組
│   ├── mcp_config.yaml            # MCP 配置檔案
│   ├── integrated_config.py        # 統一配置
│   └── prompt_templates.py         # 提示詞模板
├── tools/                     # 工具模組
│   ├── enhanced_vector_search.py   # 基礎向量搜尋工具
│   └── podcast_formatter.py        # Podcast 格式化工具
└── scripts/                   # 腳本模組
    └── tag_processor.py            # 標籤處理器
```

### 四層架構

```
[API 層 (app/)]
      │
      ▼
[主流程層 (integrated_core.py)]
      │
      ▼
[推薦器層 (enhanced_podcast_recommender.py)]
      │
      ▼
[工具層 (mcp_integration.py)]
```

#### 層級職責
- **API 層**：HTTP 入口，請求分發與回應格式化
- **主流程層**：統一數據結構、查詢處理、信心值計算、代理抽象
- **推薦器層**：Podcast 推薦邏輯，整合 MCP 工具進行多維度評分
- **工具層**：外部工具/資源的註冊、調用與快取管理

## 快速開始

### 基本使用

```python
from rag_pipeline.core import get_query_processor, get_mcp_enhanced_recommender

# 查詢處理
processor = get_query_processor()
response = await processor.process_query(user_query)

# MCP 增強推薦
recommender = get_mcp_enhanced_recommender()
results = await recommender.get_enhanced_recommendations(
    query="科技創新",
    use_mcp_tools=True
)
```

### MCP 工具使用

```python
from rag_pipeline.core import get_mcp_integration

mcp = get_mcp_integration()

# 情感分析
result = await mcp.call_tool("analyze_sentiment", {
    "text": "這個 Podcast 很棒！",
    "analyzer_type": "chinese"
})

# Apple Podcast 排名
result = await mcp.call_tool("get_apple_podcast_ranking", {
    "rss_id": "podcast_001",
    "include_details": True
})
```

## 主要設定

### 環境變數

```bash
# 資料庫配置
MONGODB_URI=mongodb://localhost:27017/podwise
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MILVUS_HOST=localhost
MILVUS_PORT=19530

# MCP 配置
MCP_ENABLED=true
MCP_CONFIG_PATH=config/mcp_config.yaml
MCP_TOOLS_ENABLED=true
MCP_RESOURCES_ENABLED=true

# Langfuse Cloud 追蹤
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
```

### MCP 配置檔案 (`config/mcp_config.yaml`)

```yaml
mcp:
  enabled: true
  tools:
    enabled: true
    builtin_tools:
      analyze_sentiment:
        enabled: true
        default_analyzer: "chinese"
      get_apple_podcast_ranking:
        enabled: true
        include_metadata: true
      vector_search:
        enabled: true
        default_top_k: 5
        default_similarity_threshold: 0.7
  resources:
    enabled: true
    max_cache_size: 100
    cache_ttl: 7200
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

# MCP 增強權重
mcp_weights = {
    'apple_rating': 0.25,
    'user_click_rate': 0.20,
    'comment_sentiment': 0.20,
    'comment_count': 0.15,
    'mcp_enhancement': 0.20
}
```

## 內建 MCP 工具

| 工具名稱 | 功能 | 參數 |
|---------|------|------|
| `analyze_sentiment` | 情感分析 | `text`, `analyzer_type` |
| `get_apple_podcast_ranking` | Apple Podcast 排名 | `rss_id`, `include_details` |
| `classify_content` | 內容分類 | `content`, `categories` |
| `vector_search` | 向量搜尋 | `query`, `top_k`, `similarity_threshold` |
| `search_podcasts` | Podcast 搜尋 | `query`, `category`, `limit` |

## 擴展指南

### 添加新的 MCP 工具
1. 在 `mcp_integration.py` 中定義工具處理函數
2. 使用 `register_tool` 註冊工具
3. 更新配置檔案

### 添加新的推薦算法
1. 繼承基礎推薦器類別
2. 實現推薦邏輯
3. 整合到 MCP 增強推薦器

## 監控與追蹤

### Langfuse Cloud 追蹤
- 自動追蹤查詢處理、工具調用、推薦結果
- 記錄信心值、處理時間、異常資訊
- 支援自定義追蹤事件

### 健康檢查
```python
# 系統健康檢查
health = await processor.health_check()
mcp_health = await mcp.health_check()
```

## 版本歷史

### v2.1.0 (當前版本)
- ✅ 整合 MCP (Model Context Protocol)
- ✅ Langfuse Cloud 追蹤
- ✅ 統一 OOP 介面設計
- ✅ 四層架構設計

---

**Podwise Team** - 打造最智能的 Podcast 推薦系統
