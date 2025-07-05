# 🎧 Podwise RAG Pipeline - 三層 CrewAI 架構

## 📋 架構總覽

本系統使用 CrewAI 設計模式實現一套智慧型 Podcast 推薦系統，支援語意檢索、分類專家協作、跨類別決策與語音回饋，實現高互動性、高可解釋性推薦流程。

### 🔄 用戶流程

```
(1) 用戶進入聊天頁面 → 詢問用戶輸入 ID
    │
    ├─ 有記錄的 ID ──→ 根據歷史記錄推薦
    │
    └─ 無記錄的 ID  or 錯誤ID ──→ 提供詢問範本

(2) 用戶輸入查詢
    │
    ▼
RAG 檢索專家
    │
    ├─ 語意向量化(檢查對應跟相似的標籤)
    ├─ 向量資料庫搜尋
    └─ 相關性排序
    │
    ▼
分類到對應類別專家

(3) 專家協作階段
類別專家接收檢索結果
    │
    ├─ 商業專家 ──→ 商業類推薦
    │
    └─ 教育專家 ──→ 教育類推薦
    │
    ▼
處理：
    ├─ 摘要生成專家 ──→ 生成節目摘要
    │
    ▼
    ├─ 商業專家 ──→ 商業類信心值評分(低於0.7 重新檢索)
    │
    └─ 教育專家 ──→ 教育類信心值評分(低於0.7 重新檢索)
    │
    ▼
結果整合到領導者

(4) 領導者接收專家建議
    │
    ├─ 評估專家提供的答案信心度
    └─ 生成最終推薦
    │
    ▼
檢查是否需要 TTS
    │
    ├─ 需要 ──→ TTS 專家生成語音
    │
    └─ 不需要 ──→ 直接返回文本結果
```

## 🧱 三層 CrewAI 架構

### 🔹 第一層：領導者層 (Leader Layer)
- **Podcast 推薦總監（Leader Crew）**
  - 協調整體推薦流程
  - 判斷請求是否為跨類別（Multi-tag）
  - 呼叫 RAG Expert 統一檢索
  - 將每筆節目分派至類別專家評估信心值
  - 根據排序規則產生最終推薦

### 🔹 第二層：類別專家層 (Category Expert Layer)

所有類別專家皆遵循相同流程與標準，針對特定主題範疇進行專業評估與信心值打分。

| 專家名稱 | 商業類別專家 | 教育類別專家 | 語意專家 |
|----------|-------------|-------------|----------|
| 🎯 職責 | 推薦商業類 Podcast | 推薦教育類 Podcast | 分析泛用語意與冷門主題 |
| 🧰 工具 | 商業知識庫、信心值標準 (>0.7) | 教育知識庫、信心值標準 (>0.7) | 語意標籤庫、分類相似度規則 |
| 📨 輸入 | 用戶偏好、類別向量檢索結果 | 用戶偏好、類別向量檢索結果 | 用戶輸入語意 |
| 📤 輸出 | 篩選信心值 > 0.7 的節目，依更新時間排序，若信心值相同 → 依 RSS ID 升冪排序 |

### 🔹 第三層：功能專家層 (Functional Expert Layer)

| 專家模組 | 職責說明 |
|----------|----------|
| 🔍 Keyword Mapper | 使用關聯詞庫分類用戶輸入為商業/教育/雙類別 |
| 🧠 RAG Expert | 進行語意檢索，回傳相關節目清單 |
| ✏️ Summary Gen | 提供節目摘要（可選） |
| 🗣️ TTS Expert | 提供語音播放回應，支援 Edge / Qwen2.5-TW 等模型 |
| 👤 User Manager | 管理用戶登入、偏好設定、訂閱紀錄等 |

## 🚀 快速開始

### 1. 環境準備

```bash
# 進入 RAG Pipeline 目錄
cd backend/rag_pipeline

# 安裝依賴
pip install -r requirements.txt
```

### 2. 使用 Podman 部署

```bash
# 執行部署腳本
chmod +x deploy/podman/rag-pipeline-crewai.sh
./deploy/podman/rag-pipeline-crewai.sh
```

### 3. 測試功能

```bash
# 執行測試腳本
python test_crewai.py
```

### 4. API 使用

#### 用戶驗證
```bash
curl -X POST http://localhost:8004/api/v1/validate-user \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "test_user"}'
```

#### 智能查詢
```bash
curl -X POST http://localhost:8004/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "query": "我想了解股票投資和理財規劃"
  }'
```

#### 查看聊天歷史
```bash
curl http://localhost:8004/api/v1/chat-history/test_user
```

## 🛠️ 核心組件

### Keyword Mapper
- **檔案**: `tools/keyword_mapper.py`
- **功能**: 使用關聯詞庫分類用戶輸入
- **支援類別**: 商業、教育、雙類別
- **信心值計算**: 基於關鍵詞匹配和密度

### KNN 推薦器
- **檔案**: `tools/knn_recommender.py`
- **算法**: K-Nearest Neighbors
- **相似度度量**: Cosine Similarity
- **支援過濾**: 類別過濾、信心值閾值

### 三層代理人架構
- **檔案**: `core/crew_agents.py`
- **架構**: Leader → Category Experts → Functional Experts
- **協調模式**: 層級式協調
- **決策機制**: 信心值評估和排序

## 📊 推薦算法

### KNN 推薦流程
1. **向量化**: 將用戶查詢轉換為向量表示
2. **相似度計算**: 使用 Cosine Similarity 計算與所有 Podcast 的相似度
3. **鄰居選擇**: 選擇 K 個最相似的 Podcast
4. **類別過濾**: 根據分類結果過濾相關類別
5. **排序**: 按相似度和更新時間排序
6. **返回**: 返回 Top-N 推薦結果

### 信心值評估
- **商業類別**: 基於財經關鍵詞匹配
- **教育類別**: 基於學習成長關鍵詞匹配
- **閾值**: 0.7（低於此值會觸發重新檢索）
- **排序規則**: 信心值 → 更新時間 → RSS ID

## 🔧 配置說明

### 環境變數
```bash
# 資料庫配置
MONGODB_URI=mongodb://worker3:27017/podwise
POSTGRES_HOST=worker3
POSTGRES_PORT=5432

# LLM 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:8b

# 向量搜尋配置
MILVUS_HOST=worker3
MILVUS_PORT=19530
```

### 配置檔案
- **主要配置**: `config/integrated_config.py`
- **RAG 配置**: `config/hierarchical_rag_config.yaml`
- **環境配置**: `env.local`

## 📈 監控與日誌

### 健康檢查
```bash
curl http://localhost:8004/health
```

### 系統資訊
```bash
curl http://localhost:8004/api/v1/system-info
```

### 容器監控
```bash
# 查看容器狀態
podman ps

# 查看日誌
podman logs -f podwise-rag-crewai

# 進入容器
podman exec -it podwise-rag-crewai bash
```

## 🧪 測試

### 單元測試
```bash
# 測試 Keyword Mapper
python -c "from tools.keyword_mapper import KeywordMapper; mapper = KeywordMapper(); print(mapper.categorize_query('我想了解股票投資'))"

# 測試 KNN 推薦器
python -c "from tools.knn_recommender import KNNRecommender; print('KNN 推薦器測試完成')"
```

### 整合測試
```bash
# 執行完整測試套件
python test_crewai.py
```

## 🔄 擴展開發

### 添加新的類別專家
1. 在 `core/crew_agents.py` 中創建新的專家類別
2. 在 `tools/keyword_mapper.py` 中添加對應關鍵詞
3. 更新配置檔案中的專家配置
4. 測試新專家的功能

### 自定義推薦算法
1. 繼承 `KNNRecommender` 類別
2. 實作自定義的相似度計算方法
3. 更新推薦邏輯
4. 整合到主應用程式

### 添加新的工具
1. 在 `tools/` 目錄下創建新工具
2. 更新 `tools/__init__.py` 的導入
3. 在主應用程式中整合新工具
4. 添加相應的測試

## 📝 注意事項

1. **依賴管理**: 確保所有 Python 依賴都已正確安裝
2. **資料庫連接**: 確保 MongoDB、PostgreSQL、Milvus 等服務正常運行
3. **向量模型**: 確保 BGE-M3 等嵌入模型已正確載入
4. **記憶體使用**: 監控容器記憶體使用情況，避免 OOM
5. **日誌管理**: 定期清理日誌檔案，避免磁碟空間不足

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 授權

本專案採用 MIT 授權條款。

## 📞 支援

如有問題或建議，請提交 Issue 或聯繫開發團隊。 