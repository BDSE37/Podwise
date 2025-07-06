# Podwise RAG 問答機器人提示詞系統

## 概述

Podwise RAG 問答機器人是一個基於三層 CrewAI 架構的智能 Podcast 推薦系統，整合了 text2vec-base-chinese 語意檢索和 TAG_info.csv 標籤比對功能，為用戶提供精準的 Podcast 推薦服務。

## 🏗️ 系統架構

### 三層 CrewAI 架構

```
┌─────────────────────────────────────────────────────────────┐
│                    用戶介面層                                │
├─────────────────────────────────────────────────────────────┤
│                    領導者層 (Leader)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   決策整合      │  │   跨類別處理    │  │   Web Search │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    專家層 (Experts)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   商業專家      │  │   教育專家      │  │   其他專家   │ │
│  │  (投資理財)     │  │  (自我成長)     │  │  (生活娛樂)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    工作層 (Workers)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   問題分類      │  │   語意檢索      │  │   標籤匹配   │ │
│  │  (Classifier)   │  │  (Semantic)     │  │  (Tag Match) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔍 語意檢索與標籤比對

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
- **SEMANTIC_CONFIG_PROMPT**: 模型配置說明
- **HYBRID_RETRIEVAL_PROMPT**: 混合檢索專家
- **TAG_ANALYSIS_PROMPT**: 標籤分析專家
- **SEMANTIC_SIMILARITY_PROMPT**: 語意相似度計算
- **RETRIEVAL_EVALUATION_PROMPT**: 檢索結果評估

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

## 🔧 配置管理

### 語意檢索配置

```python
from config.semantic_config import get_semantic_config

# 獲取配置管理器
config_manager = get_semantic_config()

# 模型配置
model_config = config_manager.get_model_config()
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
retrieval_config = config_manager.get_retrieval_config()
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
matches = config_manager.match_query_tags("我想學習投資理財")
# [
#     ("投資", 1.0, ["投資"]),
#     ("理財", 1.0, ["理財"]),
#     ("ETF", 0.8, ["ETF", "指數基金"])
# ]

# 標籤相似度計算
tag_similarity = config_manager.calculate_tag_similarity(
    query="投資理財",
    content="股票投資策略分享"
)

# 混合分數計算
hybrid_score = config_manager.calculate_hybrid_score(
    semantic_score=0.8,
    tag_score=0.6
)
```

## 📊 使用範例

### 基本使用流程

```python
from config.prompt_templates import get_prompt_template, format_prompt
from config.semantic_config import get_semantic_config

# 1. 問題分類
classifier_prompt = get_prompt_template("category_classifier")
formatted_classifier = format_prompt(
    classifier_prompt, 
    user_question="我想學習投資理財"
)

# 2. 語意檢索
retrieval_prompt = get_prompt_template("semantic_retrieval")
formatted_retrieval = format_prompt(
    retrieval_prompt,
    user_query="我想學習投資理財",
    category_result=category_result_json
)

# 3. 專家評估
expert_prompt = get_prompt_template("business_expert")
formatted_expert = format_prompt(
    expert_prompt,
    search_results=search_results_json,
    user_question="我想學習投資理財"
)

# 4. 領導者決策
leader_prompt = get_prompt_template("leader_decision")
formatted_leader = format_prompt(
    leader_prompt,
    expert_results=expert_results_json,
    user_question="我想學習投資理財"
)

# 5. 回答生成
answer_prompt = get_prompt_template("answer_generation")
formatted_answer = format_prompt(
    answer_prompt,
    user_question="我想學習投資理財",
    final_recommendations=recommendations_json,
    explanation="根據您的投資理財需求推薦"
)
```

### 語意檢索配置範例

```python
# 獲取配置管理器
config_manager = get_semantic_config()

# 顯示配置資訊
print("模型配置：", config_manager.get_model_config())
print("檢索配置：", config_manager.get_retrieval_config())
print("分類權重：", config_manager.get_category_weights())
print("標籤統計：", config_manager.get_tag_statistics())

# 測試標籤匹配
test_query = "我想學習投資理財，有什麼推薦的 Podcast 嗎？"
matches = config_manager.match_query_tags(test_query)
for tag, score, matched_words in matches:
    print(f"{tag}: {score:.2f} ({', '.join(matched_words)})")

# 測試混合分數
hybrid_score = config_manager.calculate_hybrid_score(0.8, 0.6)
print(f"混合分數: {hybrid_score:.3f}")
```

## 🚀 執行範例

```bash
# 執行完整範例
cd backend/rag_pipeline
python examples/prompt_usage_example.py
```

範例輸出：
```
🚀 Podwise RAG 問答機器人提示詞使用範例
整合 text2vec-base-chinese 語意檢索和 TAG_info.csv 標籤比對

============================================================
🔍 語意檢索和標籤比對功能展示
============================================================

📋 語意檢索配置：
  模型：text2vec-base-chinese
  路徑：shibing624/text2vec-base-chinese
  最大長度：512
  語意權重：0.7
  標籤權重：0.3
  信心度閾值：0.7

📊 標籤統計：
  總標籤數：1180
  商業：682 個標籤
  教育：498 個標籤
  其他：0 個標籤

🧪 標籤匹配測試：

1. 查詢：我想學習投資理財，有什麼推薦的 Podcast 嗎？
   匹配標籤：
     投資: 1.00 (投資)
     理財: 1.00 (理財)
     個人理財: 0.80 (理財)

2. 查詢：最近想了解 AI 技術發展趨勢
   匹配標籤：
     AI: 1.00 (AI)
     AI技術: 0.80 (AI, 技術)

📈 混合分數計算範例：
  高語意 + 中標籤: 語意=0.8, 標籤=0.6, 混合=0.740 ❌ 不通過
  中語意 + 高標籤: 語意=0.6, 標籤=0.8, 混合=0.660 ❌ 不通過
  高語意 + 高標籤: 語意=0.9, 標籤=0.9, 混合=0.900 ✅ 通過
  低語意 + 低標籤: 語意=0.4, 標籤=0.3, 混合=0.370 ❌ 不通過
```

## 📝 最佳實踐

### 1. 提示詞設計原則

- **明確性**: 每個提示詞都有明確的任務和輸出格式
- **一致性**: 使用統一的 JSON 格式和變數命名
- **可擴展性**: 支援跨類別和混合推薦
- **容錯性**: 包含信心度控制和備援機制

### 2. 語意檢索優化

- **模型選擇**: 使用 text2vec-base-chinese 進行中文語意理解
- **參數調優**: 根據實際需求調整權重和閾值
- **標籤匹配**: 充分利用 TAG_info.csv 的標籤體系
- **混合策略**: 結合語意和標籤的優勢

### 3. 系統整合建議

- **模組化設計**: 各層級職責明確，易於維護
- **配置管理**: 統一的配置管理機制
- **錯誤處理**: 完善的錯誤處理和備援機制
- **效能監控**: 監控檢索質量和用戶滿意度

## 🔧 技術細節

### 依賴套件

```python
# 核心依賴
import pandas as pd  # 標籤資料處理
import numpy as np   # 數值計算
from sentence_transformers import SentenceTransformer  # 語意模型

# 配置管理
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
```

### 檔案結構

```
backend/rag_pipeline/
├── config/
│   ├── prompt_templates.py      # 提示詞模板
│   ├── semantic_config.py       # 語意檢索配置
│   └── README_PROMPTS.md        # 說明文件
├── examples/
│   └── prompt_usage_example.py  # 使用範例
└── scripts/
    └── csv/
        └── TAG_info.csv         # 標籤資料
```

### 效能考量

- **模型載入**: 使用單例模式避免重複載入
- **標籤索引**: 預先建立標籤索引提升匹配速度
- **批次處理**: 支援批次檢索提升效能
- **快取機制**: 可選的快取機制減少重複計算

## 📈 未來擴展

### 1. 模型升級

- 支援更多語意模型（BGE-M3、E5-Large 等）
- 動態模型選擇機制
- 模型效能監控和自動調優

### 2. 標籤體系擴展

- 動態標籤更新機制
- 用戶自定義標籤
- 標籤權重學習

### 3. 檢索策略優化

- 多模態檢索（音頻、文字、標籤）
- 個性化檢索策略
- 實時檢索優化

### 4. 系統整合

- 與其他 RAG 系統整合
- 支援更多資料來源
- 分散式檢索架構

---

**版本**: 1.0.0  
**作者**: Podwise Team  
**更新日期**: 2024年1月 