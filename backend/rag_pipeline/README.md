# Podwise RAG Pipeline 整合系統

## 系統概述

Podwise RAG Pipeline 是一個整合了多個模組的智能檢索與推薦系統，採用三層式 CrewAI agent 架構，提供完整的 Podcast 內容檢索、推薦和語音合成服務。

## 核心架構

### 三層式 CrewAI Agent 架構

根據 `agent_roles_config.py` 的配置，系統採用以下三層架構：

#### 第一層：領導者層 (Leader Layer)
- **chief_decision_orchestrator**: 決策統籌長
  - 整合多元專家觀點
  - 量化評估與清晰比較
  - 提供最契合用戶需求的行動建議

#### 第二層：類別專家層 (Category Expert Layer)
- **business_intelligence_expert**: 商業智慧專家
  - 專注商業/投資/創業內容推薦
  - 個人化學習建議
- **educational_growth_strategist**: 教育成長專家
  - 專注教育/學習方法/個人成長內容
  - 行為改變與反思思維

#### 第三層：功能專家層 (Functional Expert Layer)
- **intelligent_retrieval_expert**: 智能檢索專家 ⭐
  - 語意分析與向量檢索
  - 標籤匹配與查詢改寫
  - 25秒內完成完整檢索循環
- **content_summary_expert**: 內容摘要專家
  - 生成 ≤200 字中文摘要
  - 關鍵事實核對
- **tag_classification_expert**: TAG 分類專家
  - 關鍵詞映射與內容分類
  - 商業/教育/其他分類
- **tts_expert**: 語音合成專家
  - 自然流暢語音生成
  - 情感豐富表達
- **user_experience_expert**: 用戶體驗專家
  - 個人化用戶洞察報告
  - 行為分析與偏好建模

## 模組整合

### 1. Data Cleaning 整合

```python
# 在 enhanced_vector_search.py 中整合
from data_cleaning.core.episode_cleaner import EpisodeCleaner
from data_cleaning.core.base_cleaner import BaseCleaner
from data_cleaning.utils.data_extractor import DataExtractor

# 功能：
# - 內容清理與標準化
# - 數據品質檢查
# - 異常處理與修正
```

### 2. ML Pipeline 整合

```python
# 在 enhanced_vector_search.py 中整合
from ml_pipeline.core.recommender import Recommender
from ml_pipeline.core.data_manager import DataManager

# 功能：
# - 智能推薦系統
# - 用戶偏好建模
# - 內容相似度計算
```

### 3. TTS 整合

```python
# 在 main.py 中整合
from tts.core.tts_service import TTSService

# 功能：
# - 語音合成 (podrina, podrisa, podrino)
# - 語速調節 (0.5x - 1.5x)
# - 情感表達控制
```

### 4. LLM 整合

```python
# 支援多種 LLM 模型
from llm.core.ollama_llm import OllamaLLM
from llm.core.qwen_llm_manager import Qwen3LLMManager

# 支援模型：
# - qwen2.5-Taiwan
# - qwen3:8b
# - Ollama 本地模型
```

### 5. STT 整合

```python
# 語音轉文字服務
from stt.stt_service import STTService

# 功能：
# - 語音識別
# - 多語言支援
# - 實時轉錄
```

### 6. User Management 整合

```python
# 用戶管理服務
from user_management.user_service import UserService

# 功能：
# - 用戶註冊/登入
# - 個人化設定
# - 使用歷史記錄
```

## 智能檢索 Fallback 機制

### 三層式回覆機制

1. **RAG 向量搜尋** (信心度 ≥ 0.7) → 使用本地知識庫
2. **Web 搜尋 + OpenAI** (信心度 < 0.7) → 使用 OpenAI API 智能搜尋
3. **預設問答** (最後保障) → 使用預設回應

### 信心度閾值

- **intelligent_retrieval_expert**: 0.7 (低於此值回傳 NO_MATCH)
- **business_intelligence_expert**: 0.75
- **educational_growth_strategist**: 0.75
- **chief_decision_orchestrator**: 0.8

## API 端點

### 主要查詢端點

```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "用戶查詢內容",
  "user_id": "用戶ID",
  "session_id": "會話ID",
  "enable_tts": true,
  "voice": "podrina",
  "speed": 1.0,
  "metadata": {
    "source": "podri_chat",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 回應格式

```json
{
  "user_id": "用戶ID",
  "query": "用戶查詢",
  "response": "AI 回應內容",
  "category": "內容分類",
  "confidence": 0.85,
  "recommendations": [
    {
      "title": "推薦標題",
      "description": "推薦描述",
      "category": "分類",
      "confidence": 0.8,
      "source": "來源"
    }
  ],
  "reasoning": "推理過程",
  "processing_time": 2.5,
  "timestamp": "2024-01-01T00:00:00Z",
  "audio_data": "base64編碼的音頻數據",
  "voice_used": "podrina",
  "speed_used": 1.0,
  "tts_enabled": true
}
```

### TTS 專用端點

```http
POST /api/v1/tts/synthesize
Content-Type: application/json

{
  "text": "要合成的文本",
  "voice": "podrina",
  "speed": 1.0
}
```

## 前端整合 (podri.html)

### 主要功能

1. **智能對話界面**
   - 實時聊天對話
   - 載入狀態指示
   - 錯誤處理與重試

2. **語音控制**
   - TTS 開關控制
   - 語音模型選擇 (podrina/podrisa/podrino)
   - 語速調節 (0.5x - 1.5x)

3. **用戶體驗**
   - 響應式設計
   - 側邊欄控制面板
   - 歷史對話記錄

### 關鍵 JavaScript 函數

```javascript
// 發送訊息到 RAG Pipeline
async function sendMessage() {
    const response = await fetch('http://localhost:8005/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: message,
            user_id: window.currentUserId || 'default_user',
            session_id: generateSessionId(),
            enable_tts: ttsEnabled,
            voice: selectedVoice,
            speed: parseFloat(speed)
        })
    });
}

// 生成 TTS 語音
async function generateTTS(text, voice, speed) {
    const response = await fetch('http://localhost:8003/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            文字: text,
            語音: voice,
            語速: rateAdjustment,
            音量: "+0%",
            音調: "+0%"
        })
    });
}
```

## 系統流程

### 1. 查詢處理流程

```
用戶查詢 → 語意分析 → 查詢改寫 → 向量化 → Milvus 檢索 → 標籤匹配 → 內容清理 → 推薦增強 → TTS 合成 → 回應
```

### 2. 智能檢索專家流程

```
1. semantic_analyzer: 萃取意圖與關鍵詞
2. query_rewriter: 參考 TAG_info 改寫查詢
3. text2vec_model: 向量化查詢
4. milvus_db: 檢索 top-k=8
5. tag_matcher: 依標籤重疊度＋相似度重排
6. 信心分數 <0.7 時回傳 NO_MATCH
```

### 3. TTS 整合流程

```
文本回應 → TTS 服務 → 語音合成 → Base64 編碼 → 前端播放
```

## 配置說明

### 環境變數

```bash
# RAG Pipeline 配置
RAG_PIPELINE_PORT=8005
RAG_PIPELINE_HOST=0.0.0.0

# TTS 服務配置
TTS_SERVICE_PORT=8003
TTS_SERVICE_HOST=0.0.0.0

# LLM 服務配置
LLM_SERVICE_PORT=8004
LLM_SERVICE_HOST=0.0.0.0

# STT 服務配置
STT_SERVICE_PORT=8006
STT_SERVICE_HOST=0.0.0.0

# User Management 配置
USER_MANAGEMENT_PORT=8007
USER_MANAGEMENT_HOST=0.0.0.0

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 資料庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/podwise
```

## 啟動指南

### 1. 啟動 RAG Pipeline

```bash
cd backend/rag_pipeline
python main.py
```

### 2. 啟動 TTS 服務

```bash
cd backend/tts
python main.py
```

### 3. 啟動 LLM 服務

```bash
cd backend/llm
python main.py
```

### 4. 啟動 STT 服務

```bash
cd backend/stt
python main.py
```

### 5. 啟動 User Management 服務

```bash
cd backend/user_management
python main.py
```

### 6. 啟動前端

```bash
# 使用 nginx 或其他 Web 伺服器
# 或直接在瀏覽器中開啟 podri.html
```

### 7. 驗證整合

```bash
# 測試健康檢查
curl http://localhost:8005/health

# 測試查詢
curl -X POST http://localhost:8005/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "推薦投資理財的 podcast", "enable_tts": true}'
```

## 故障排除

### 常見問題

1. **TTS 服務無法連接**
   - 檢查 TTS 服務是否在 8003 端口運行
   - 確認 TTS 服務健康狀態

2. **檢索結果信心度不足**
   - 檢查 Milvus 服務狀態
   - 確認向量資料庫是否已載入資料

3. **前端無法播放語音**
   - 檢查瀏覽器控制台錯誤
   - 確認音頻格式支援

4. **LLM 服務無法連接**
   - 檢查 LLM 服務是否在 8004 端口運行
   - 確認 Ollama 或 Qwen 模型是否已載入

### 日誌檢查

```bash
# RAG Pipeline 日誌
tail -f backend/rag_pipeline/logs/rag_pipeline.log

# TTS 服務日誌
tail -f backend/tts/logs/tts_service.log

# LLM 服務日誌
tail -f backend/llm/logs/llm_service.log
```

## 技術架構圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   podri.html    │    │  RAG Pipeline   │    │   TTS Service   │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Milvus DB     │
                       │  (Vector DB)    │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Data Cleaning   │
                       │ ML Pipeline     │
                       │ LLM Service     │
                       │ STT Service     │
                       │ User Management │
                       └─────────────────┘
```

## 未來規劃

1. **效能優化**
   - 向量檢索快取機制
   - 並行處理優化
   - 記憶體使用優化

2. **功能增強**
   - 多語言支援
   - 更豐富的語音選項
   - 個人化推薦算法

3. **監控與分析**
   - 詳細的效能指標
   - 用戶行為分析
   - A/B 測試支援

這個整合系統確保了所有組件之間的協調運作，為用戶提供完整的智能 Podcast 推薦和語音互動體驗。
