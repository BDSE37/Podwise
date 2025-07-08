# 🏗️ Podwise 三層 CrewAI 架構系統

## 📋 概述

本系統採用三層 CrewAI 架構設計，提供智能、高效的 Podcast 推薦服務。遵循 Google Clean Code 原則，採用 OOP 設計模式，確保代碼的可維護性和可擴展性。

## 🎯 架構設計

### 🏛️ 三層架構結構

```
┌─────────────────────────────────────────────────────────────┐
│                    第一層：領導者層                          │
│                   (Leader Layer)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              👑 Podri Leader                       │   │
│  │         智能協調領導者                               │   │
│  │    • 協調所有專家代理人                             │   │
│  │    • 整合專家意見                                   │   │
│  │    • 做出最佳決策                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↑
                    整合所有專家意見
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   第二層：類別專家層                         │
│                (Category Expert Layer)                     │
│  ┌─────────────────────┐    ┌─────────────────────────┐   │
│  │   🎓 商業智慧專家    │    │   📚 教育成長專家       │   │
│  │   Business Expert   │    │   Education Expert      │   │
│  │  • 投資理財建議      │    │  • 學習成長指導         │   │
│  │  • 創業指導          │    │  • 技能發展建議         │   │
│  │  • 商業分析          │    │  • 教育資源推薦         │   │
│  └─────────────────────┘    └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↑
                    基於功能專家的分析
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  第三層：功能專家層                          │
│               (Functional Expert Layer)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ 🔍 RAG專家  │ │ 📄 摘要專家  │ │ 🏷️ TAG      │         │
│  │ 語意檢索    │ │ 內容摘要    │ │ 分類專家    │         │
│  └─────────────┘ └─────────────┘ └─────────────┘         │
│  ┌─────────────┐ ┌─────────────┐                         │
│  │ 🎵 TTS專家  │ │ 👤 用戶專家  │                         │
│  │ 語音合成    │ │ 用戶管理    │                         │
│  └─────────────┘ └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 核心組件

#### 1. 配置管理 (`config/`)
- **`agent_roles_config.py`**: 定義所有代理人的角色、職責和配置
- **`integrated_config.py`**: 系統整合配置
- **`prompt_templates.py`**: 提示模板管理

#### 2. 核心引擎 (`core/`)
- **`base_agent.py`**: 基礎代理人抽象類別
- **`agent_manager.py`**: 代理人管理器
- **`crew_agents.py`**: 具體代理人實現
- **`hierarchical_rag_pipeline.py`**: 層級化 RAG Pipeline

#### 3. 工具和服務 (`tools/`)
- **`enhanced_vector_search.py`**: 統一向量搜尋
- **`web_search_tool.py`**: Web 搜尋工具
- **`podcast_formatter.py`**: Podcast 格式化工具

#### 4. Web API (`app/`)
- **`main_crewai.py`**: FastAPI 應用程式

## 🎭 代理人角色定義

### 第一層：領導者層

#### 👑 Podri Leader (智能協調領導者)
- **職責**: 協調所有專家代理人，整合意見，做出最佳決策
- **技能**: 決策制定、團隊協調、需求分析、質量控制
- **工具**: decision_framework, quality_assessor, priority_ranker

### 第二層：類別專家層

#### 🎓 商業智慧專家 (Business Expert)
- **職責**: 提供專業的商業、投資、創業相關建議
- **技能**: 投資分析、財務規劃、市場趨勢、風險評估
- **工具**: financial_analyzer, market_scanner, risk_calculator

#### 📚 教育成長專家 (Education Expert)
- **職責**: 推薦教育、學習、個人成長相關內容
- **技能**: 學習理論、教育心理學、職涯規劃、技能發展
- **工具**: learning_assessor, skill_mapper, growth_tracker

### 第三層：功能專家層

#### 🔍 智能檢索專家 (RAG Expert)
- **職責**: 執行高精度的語意檢索和向量搜尋
- **技能**: 語意理解、向量檢索、相似度計算、結果排序
- **工具**: text2vec_model, milvus_db, tag_matcher

#### 📄 內容摘要專家 (Summary Expert)
- **職責**: 生成精準、簡潔的內容摘要
- **技能**: 內容分析、關鍵詞提取、摘要生成、資訊整理
- **工具**: text_analyzer, keyword_extractor, summary_generator

#### 🏷️ TAG 分類專家 (Tag Classification Expert)
- **職責**: 使用 Excel 詞庫進行精準內容分類
- **技能**: 關鍵詞映射、語義分析、跨類別處理、分類優化
- **工具**: keyword_mapper, excel_word_bank, semantic_analyzer

#### 🎵 語音合成專家 (TTS Expert)
- **職責**: 生成自然、流暢的語音內容
- **技能**: 語音合成、韻律控制、情感表達、音頻處理
- **工具**: edge_tts, voice_cloner, audio_processor

#### 👤 用戶體驗專家 (User Manager)
- **職責**: 深入理解用戶需求，管理用戶資料
- **技能**: 用戶分析、行為追蹤、偏好識別、個性化推薦
- **工具**: user_profiler, behavior_tracker, preference_analyzer

## 🔍 語意檢索與標籤比對系統

### 混合檢索策略

系統採用混合檢索策略，結合語意相似度和標籤匹配度：

```
混合分數 = (語意分數 × 0.7) + (標籤分數 × 0.3)
```

#### 1. 語意檢索 (text2vec-base-chinese)

- **模型**: shibing624/text2vec-base-chinese
- **最大長度**: 512 tokens
- **池化策略**: mean
- **輸出維度**: 768
- **相似度計算**: 餘弦相似度

#### 2. 標籤匹配 (TAG_info.csv)

- **標籤來源**: TAG_info.csv 檔案
- **匹配策略**: 精確匹配 + 相關詞彙匹配
- **分類支援**: 商業、教育、其他
- **權重分配**: 精確匹配 1.0，相關詞彙 0.8

### 標籤匹配詳細規則

```python
# 精確匹配
if tag.lower() in query.lower():
    score += 1.0

# 相關詞彙匹配
for word in related_words:
    if word.lower() in query.lower():
        score += 0.8

# Jaccard 相似度
jaccard_similarity = len(intersection) / len(union)
```

## 📋 提示詞模板架構

### 1. 系統層級提示詞

- **SYSTEM_PROMPT**: 定義機器人角色和行為準則
- **CATEGORY_CLASSIFIER_PROMPT**: 問題分類專家

### 2. 檢索層級提示詞

- **SEMANTIC_RETRIEVAL_PROMPT**: 語意檢索專家
- **HYBRID_RETRIEVAL_PROMPT**: 混合檢索專家
- **TAG_ANALYSIS_PROMPT**: 標籤分析專家

### 3. 專家層級提示詞

- **BUSINESS_EXPERT_PROMPT**: 商業類節目專家
- **EDUCATION_EXPERT_PROMPT**: 教育類節目專家
- **OTHER_EXPERT_PROMPT**: 其他類節目專家

### 4. 領導者層級提示詞

- **LEADER_DECISION_PROMPT**: 決策整合專家
- **ANSWER_GENERATION_PROMPT**: 回答生成專家
- **WEB_SEARCH_PROMPT**: Web Search 備援專家

## 🎯 核心功能

### 1. 智能問題分類

支援跨類別問題識別：

```json
{
    "categories": [
        {
            "category": "商業",
            "confidence": 0.85,
            "keywords": ["投資", "理財"],
            "reasoning": "用戶明確提到投資理財"
        },
        {
            "category": "教育", 
            "confidence": 0.45,
            "keywords": ["學習"],
            "reasoning": "提到學習，但主要內容是投資理財"
        }
    ],
    "primary_category": "商業",
    "is_multi_category": false
}
```

### 2. 混合檢索策略

結合語意和標籤的檢索結果：

```json
{
    "query": "用戶查詢",
    "semantic_matches": [
        {
            "content": "檢索內容",
            "semantic_score": 0.85,
            "tag_score": 0.6,
            "hybrid_score": 0.775,
            "matched_tags": ["投資", "理財"],
            "confidence": 0.775
        }
    ],
    "tag_matches": [
        {
            "tag": "投資",
            "score": 0.8,
            "matched_words": ["投資"]
        }
    ]
}
```

### 3. 信心度控制機制

- **閾值**: 0.7（只有 >= 0.7 的結果才被推薦）
- **觸發條件**: 高信心度結果 < 1 時執行 Web Search
- **動態推薦**: 1-3 個節目（根據信心度）

### 4. 跨類別處理

- **多類別識別**: 自動識別涉及多個類別的問題
- **信心度排序**: 按各類別信心度排序
- **混合推薦**: 可能推薦單一或混合類別
- **智能引導**: 其他類別不足時引導至商業/教育類別

## 🔄 處理流程

### 1. 查詢處理流程

```
用戶查詢 → 第三層（功能專家層）→ 第二層（類別專家層）→ 第一層（領導者層）→ 最終結果
```

### 2. 詳細執行步驟

1. **第三層執行**（並行處理）
   - RAG 專家進行語意檢索
   - 摘要專家生成內容摘要
   - TAG 分類專家進行內容分類
   - TTS 專家準備語音合成
   - 用戶專家分析用戶偏好

2. **第二層執行**（根據分類選擇）
   - 根據查詢分類選擇對應專家
   - 商業專家處理商業相關查詢
   - 教育專家處理學習相關查詢

3. **第一層執行**（整合決策）
   - 領導者整合所有專家意見
   - 權衡不同觀點
   - 做出最終決策

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd backend/rag_pipeline
pip install -r requirements.txt
```

### 2. 基本使用

```python
from main import get_rag_pipeline

# 獲取 RAG Pipeline 實例
pipeline = get_rag_pipeline()

# 處理查詢
response = await pipeline.process_query(
    query="我想學習投資理財",
    user_id="user123"
)

print(f"回應: {response.content}")
print(f"信心度: {response.confidence}")
```

### 3. 進階使用

```python
from core.agent_manager import AgentManager
from core.base_agent import BaseAgent

# 創建管理器
manager = AgentManager()

# 註冊代理人類別
agent_classes = {
    "leader": YourLeaderAgent,
    "business_expert": YourBusinessExpert,
    "education_expert": YourEducationExpert,
    # ... 其他代理人
}
manager.register_agent_classes(agent_classes)

# 初始化所有代理人
manager.initialize_all_agents()

# 處理查詢
result = await manager.process_query_with_three_layer_architecture(
    query="推薦投資理財的 podcast",
    user_id="user123",
    category="商業"
)

print(f"結果: {result.content}")
print(f"信心值: {result.confidence}")
```

## 🔧 配置管理

### 語意檢索配置

```python
from config.integrated_config import get_config

# 獲取配置管理器
config = get_config()

# 模型配置
model_config = config.get_llm_config()
# {
#     "model_name": "text2vec-base-chinese",
#     "model_path": "shibing624/text2vec-base-chinese",
#     "max_length": 512,
#     "batch_size": 32,
#     "normalize_embeddings": True,
#     "pooling_strategy": "mean",
#     "device": "auto"
# }

# 檢索配置
retrieval_config = config.get_vector_search_config()
# {
#     "top_k": 10,
#     "similarity_threshold": 0.3,
#     "tag_weight_factor": 0.3,
#     "semantic_weight_factor": 0.7,
#     "max_tag_matches": 5
# }
```

### 標籤匹配功能

```python
# 標籤匹配
matches = config.match_query_tags("我想學習投資理財")
# [
#     ("投資", 1.0, ["投資"]),
#     ("理財", 1.0, ["理財"]),
#     ("ETF", 0.8, ["ETF", "指數基金"])
# ]

# 標籤相似度計算
tag_similarity = config.calculate_tag_similarity(
    query="投資理財",
    content="股票投資策略分享"
)

# 混合分數計算
hybrid_score = config.calculate_hybrid_score(
    semantic_score=0.8,
    tag_score=0.6
)
```

## 📊 效能監控

### 系統指標
- 總查詢數
- 成功查詢數
- 失敗查詢數
- 成功率
- 平均處理時間

### 代理人指標
- 調用次數
- 成功率
- 平均信心值
- 平均處理時間

### 監控方法

```python
# 獲取系統狀態
status = manager.get_system_status()
print(f"系統成功率: {status['system_metrics']['success_rate']:.2%}")

# 獲取代理人指標
for agent_name, agent_status in status['agents_status'].items():
    metrics = agent_status['metrics']
    print(f"{agent_name}: {metrics['success_rate']:.2%}")
```

## 🔧 自定義代理人

### 創建新代理人

```python
from core.base_agent import BaseAgent, AgentResponse

class CustomAgent(BaseAgent):
    """自定義代理人"""
    
    async def process(self, input_data: Any) -> AgentResponse:
        """實現具體的處理邏輯"""
        # 你的處理邏輯
        return AgentResponse(
            content="處理結果",
            confidence=0.8,
            reasoning="處理推理",
            metadata={"custom_data": "value"}
        )
```

### 註冊新代理人

```python
# 1. 在 agent_roles_config.py 中添加角色定義
# 2. 創建代理人類別
# 3. 註冊到管理器
manager.register_agent_classes({"custom_agent": CustomAgent})
```

## 🎯 最佳實踐

### 1. 代理人設計原則
- **單一職責**: 每個代理人只負責一個特定功能
- **高內聚低耦合**: 代理人內部邏輯緊密，代理人之間松耦合
- **可測試性**: 每個代理人都可以獨立測試
- **可擴展性**: 易於添加新的代理人和功能

### 2. 錯誤處理
- 使用 try-catch 包裝所有異步操作
- 提供有意義的錯誤信息
- 實現優雅的降級機制

### 3. 效能優化
- 同層級代理人並行執行
- 使用適當的超時設置
- 實現結果緩存機制

## 🔍 故障排除

### 常見問題

1. **代理人初始化失敗**
   - 檢查角色配置是否正確
   - 確認所有依賴已安裝

2. **處理超時**
   - 調整 `max_execution_time` 參數
   - 優化代理人處理邏輯

3. **信心值過低**
   - 檢查輸入數據質量
   - 調整信心值計算邏輯

### 調試技巧

```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 檢查代理人狀態
status = manager.get_system_status()
for agent_name, agent_status in status['agents_status'].items():
    print(f"{agent_name}: {agent_status['status']}")
```

## 📈 未來發展

### 計劃功能
- [ ] 動態代理人載入
- [ ] 分散式代理人部署
- [ ] 更智能的負載均衡
- [ ] 實時效能監控儀表板
- [ ] A/B 測試框架

### 擴展方向
- 支援更多領域專家
- 增加多語言支援
- 整合更多 AI 模型
- 提供 REST API 介面

## 🤝 貢獻指南

1. Fork 本專案
2. 創建功能分支
3. 提交變更
4. 創建 Pull Request

## 📄 授權

MIT License

## 📞 聯絡資訊

- 專案: Podwise
- 團隊: Podwise Team
- 版本: 3.0.0 