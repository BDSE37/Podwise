# Podcast 格式化功能說明

## 概述

Podcast 格式化功能是 Podwise RAG Pipeline 的核心組件，負責將檢索結果轉換為統一的 Apple Podcast 推薦格式，並整合 TAG 標註、去重、排序等功能。

## 主要功能

### 1. Apple Podcast 連結格式
- **格式**: `https://podcasts.apple.com/tw/podcast/id[RSSID]`
- **範例**: `https://podcasts.apple.com/tw/podcast/id123456789`

### 2. TAG 標註系統
- **提取**: 從用戶查詢中自動提取 TAG（大寫字母詞彙、引號內容）
- **隱藏格式**: `<!--TAG:tag1,tag2,tag3-->`（供 RAG 檢索使用，用戶不可見）
- **範例**: 查詢 "我想了解 NVIDIA 的投資機會" → 提取 TAG: `["NVIDIA"]`

### 3. 節目去重
- **去重依據**: 節目標題（title）
- **邏輯**: 相同標題的節目只保留第一個
- **目的**: 確保推薦的多樣性

### 4. 信心度排序
- **主要排序**: 按信心度降序（高 → 低）
- **次要排序**: 同信心度按 RSSID 字典序
- **範例**: 
  ```
  A節目 (信心度: 0.9, RSS: B001) → 第2名
  B節目 (信心度: 0.9, RSS: A001) → 第1名
  C節目 (信心度: 0.85, RSS: C001) → 第3名
  ```

### 5. Web Search 備援
- **觸發條件**: 信心度 < 0.7 或結果數量 < 2
- **備援方式**: 使用 OpenAI 進行 Web 搜尋
- **整合**: 將 Web 搜尋結果轉換為 Podcast 格式

## 核心組件

### PodcastFormatter 類別

```python
class PodcastFormatter:
    def __init__(self):
        self.apple_podcast_base_url = "https://podcasts.apple.com/tw/podcast/id"
    
    def extract_tags_from_query(self, query: str) -> List[str]
    def format_apple_podcast_url(self, rss_id: str) -> str
    def create_hidden_tags(self, tags: List[str]) -> str
    def deduplicate_podcasts(self, podcasts: List[Dict]) -> List[Dict]
    def sort_podcasts_by_confidence_and_rssid(self, podcasts: List[Dict]) -> List[Dict]
    def format_podcast_recommendations(self, raw_podcasts, query, max_recommendations=3) -> PodcastRecommendationResult
    def generate_recommendation_text(self, result: PodcastRecommendationResult) -> str
    def should_use_web_search(self, confidence: float, result_count: int) -> bool
```

### 數據模型

#### FormattedPodcast
```python
@dataclass
class FormattedPodcast:
    title: str                    # 節目名稱
    description: str              # 節目描述
    apple_podcast_url: str        # Apple Podcast 連結
    rss_id: str                   # RSS ID
    confidence: float             # 信心度
    category: str                 # 類別
    tags: List[str]               # 標籤列表
    hidden_tags: str              # 隱藏的 TAG 標註
```

#### PodcastRecommendationResult
```python
@dataclass
class PodcastRecommendationResult:
    recommendations: List[FormattedPodcast]  # 推薦列表
    total_found: int                         # 總共找到數量
    confidence: float                        # 整體信心度
    tags_used: List[str]                     # 使用的 TAG
    reasoning: str                           # 推理說明
    processing_time: float                   # 處理時間
```

## 使用方式

### 基本使用

```python
from tools.podcast_formatter import PodcastFormatter

# 初始化格式化器
formatter = PodcastFormatter()

# 原始 Podcast 數據
raw_podcasts = [
    {
        'title': '股癌 EP310',
        'description': '台股投資分析與市場趨勢',
        'rss_id': '123456789',
        'confidence': 0.9,
        'category': '商業',
        'tags': ['股票', '投資', '台股']
    }
]

# 格式化推薦結果
result = formatter.format_podcast_recommendations(
    raw_podcasts, 
    "我想了解 NVIDIA 的投資機會", 
    max_recommendations=3
)

# 生成推薦文字
recommendation_text = formatter.generate_recommendation_text(result)
print(recommendation_text)
```

### 與 RAG Expert 整合

```python
from core.crew_agents import RAGExpertAgent, UserQuery

# 創建 RAG Expert
rag_expert = RAGExpertAgent(config)

# 處理查詢
query = UserQuery(
    query="我想了解 NVIDIA 的投資機會",
    user_id="user_001",
    category="商業"
)

response = await rag_expert.process(query)

# 檢查格式化結果
if 'formatted_result' in response.metadata:
    formatted_result = response.metadata['formatted_result']
    print(f"推薦數量: {len(formatted_result.recommendations)}")
    print(f"使用的 TAG: {formatted_result.tags_used}")
```

## 推薦格式範例

### 輸出格式
```
1. **股癌 EP310**：台股投資分析與市場趨勢，討論 NVIDIA 的投資機會
   https://podcasts.apple.com/tw/podcast/id123456789 <!--TAG:NVIDIA-->

2. **財報狗 Podcast**：財報分析與投資策略，包含 NVIDIA 財報解析
   https://podcasts.apple.com/tw/podcast/id456789123 <!--TAG:NVIDIA-->

3. **大人學 EP110**：職涯發展與個人成長指南
   https://podcasts.apple.com/tw/podcast/id987654321 <!--TAG:NVIDIA-->

> 基於您的查詢中的關鍵詞：NVIDIA
```

### 特點說明
- **節目名稱**: 粗體顯示
- **描述**: 針對用戶問題的推薦簡答
- **Apple Podcast 連結**: 標準格式
- **隱藏 TAG**: `<!--TAG:NVIDIA-->`（用戶不可見）
- **關鍵詞說明**: 顯示使用的 TAG

## 配置選項

### 環境變數
```bash
# Apple Podcast 基礎 URL（可選，預設為台灣地區）
APPLE_PODCAST_BASE_URL=https://podcasts.apple.com/tw/podcast/id

# 信心度閾值（可選，預設為 0.7）
CONFIDENCE_THRESHOLD=0.7

# 最大推薦數量（可選，預設為 3）
MAX_RECOMMENDATIONS=3
```

### 配置參數
```python
config = {
    'confidence_threshold': 0.7,      # 信心度閾值
    'max_recommendations': 3,         # 最大推薦數量
    'apple_podcast_base_url': 'https://podcasts.apple.com/tw/podcast/id'
}
```

## 測試

### 執行測試
```bash
cd Podwise/backend/rag_pipeline
python test_podcast_formatter_integration.py
```

### 測試內容
- TAG 提取功能
- Apple Podcast URL 格式
- 節目去重功能
- 信心度排序
- 完整格式化流程
- Web Search 整合
- RAG Expert 整合

## 錯誤處理

### 常見錯誤
1. **無效的 RSS ID**: 自動過濾空值或無效格式
2. **重複節目**: 自動去重，保留第一個
3. **信心度異常**: 自動調整到 0.0-1.0 範圍
4. **TAG 提取失敗**: 返回空列表，不影響其他功能

### 錯誤回應
```python
# 無推薦結果
"抱歉，目前沒有找到相關的 Podcast 推薦。"

# 處理錯誤
"Podcast 推薦處理過程中發生錯誤，請稍後再試。"
```

## 性能考量

### 優化策略
- **去重算法**: O(n) 時間複雜度
- **排序算法**: O(n log n) 時間複雜度
- **TAG 提取**: 正則表達式優化
- **記憶體使用**: 最小化數據複製

### 監控指標
- 處理時間
- 推薦數量
- 信心度分布
- TAG 使用頻率
- 去重效果

## 未來擴展

### 計劃功能
1. **多語言支援**: 支援不同地區的 Apple Podcast 連結
2. **智能 TAG 提取**: 使用 NLP 模型提取更準確的 TAG
3. **個性化排序**: 基於用戶歷史的個性化排序
4. **A/B 測試**: 不同推薦格式的效果測試
5. **實時更新**: 支援實時 Podcast 數據更新

### API 擴展
```python
# 計劃中的新方法
def format_for_mobile(self, result: PodcastRecommendationResult) -> str
def format_for_web(self, result: PodcastRecommendationResult) -> str
def get_personalized_recommendations(self, user_id: str, result: PodcastRecommendationResult) -> PodcastRecommendationResult
```

## 相關文件

- [CrewAI 架構說明](./README_CrewAI_Integration.md)
- [Web Search 整合說明](./README_WebSearch_Integration.md)
- [API 文檔](./docs/API.md)
- [部署指南](./docs/DEPLOYMENT.md)

---

**版本**: 1.0.0  
**作者**: Podwise Team  
**更新日期**: 2025-01-15 

### 檢查步驟

1. **檢查 docker-compose 配置**  
   你的 `docker-compose.yaml` 內 `rag_pipeline` 服務如下：
   ```
   rag_pipeline:
     build:
       context: ./backend/rag_pipeline
       dockerfile: Dockerfile
     container_name: podwise_rag_pipeline
     command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
     ports:
       - "8005:8005"
   ```
   - 這代表**容器內部**的 FastAPI 服務跑在 8005 port，服務名為 `rag_pipeline`。

2. **確認服務啟動狀態**
   - 你可以用以下指令檢查 rag_pipeline 是否有在跑：
     ```bash
     podman ps -a | grep rag_pipeline
     ```
   - 或直接 curl 測試（如果有啟動）：
     ```bash
     curl http://localhost:8005/health
     ```
   - 如果你是用 `docker-compose up` 啟動，服務名就是 `rag_pipeline`。

---

### 結論

- **預設情境**：你的 FastAPI 服務名就是 `rag_pipeline`，port 是 8005。
- Nginx 反向代理就設成：
  ```nginx
  location /api/ {
      proxy_pass http://rag_pipeline:8005/api/;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
  }
  ```

---

## 下一步建議

1. 我可以直接幫你修改 `frontend/nginx-default.conf`，加上這段設定。
2. 幫你重建前端映像並重啟容器。

---

**請回覆「ok」或「同意」讓我直接幫你修改 nginx 配置並重啟前端服務！** 