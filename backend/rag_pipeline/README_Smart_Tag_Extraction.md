# 智能 TAG 提取功能說明

## 概述

智能 TAG 提取功能是 Podwise RAG Pipeline 的進階組件，當查詢中的詞彙不在現有標籤表時，使用 Word2Vec + Transformer 進行智能標籤提取，提供更精準的語義理解和標籤映射。

## 核心功能

### 1. 智能 TAG 提取流程

```
用戶查詢
    ↓
基礎 TAG 提取（現有邏輯）
    ↓
檢查是否在現有標籤表
    ↓
缺失 TAG → 智能映射
    ↓
Word2Vec 語義相似度
    ↓
Transformer 語義理解
    ↓
模糊匹配（備援）
    ↓
組合最終結果
```

### 2. 多層次映射策略

#### 基礎 TAG 提取
- **大寫字母詞彙**: 提取如 "NVIDIA", "TSMC" 等
- **引號內容**: 提取如 "機器學習" 等
- **中文詞彙**: 提取 2 字以上的中文詞彙

#### Word2Vec 語義相似度
- 基於 Podcast 內容訓練的語義模型
- 計算詞彙間的語義相似度
- 相似度閾值: 0.7

#### Transformer 語義理解
- 使用 BERT/RoBERTa 等預訓練模型
- 結合上下文進行語義理解
- 支援中文語義分析

#### 模糊匹配（備援）
- 字符相似度計算
- 包含關係檢查
- 編輯距離算法

## 核心組件

### SmartTagExtractor 類別

```python
class SmartTagExtractor:
    def __init__(self, 
                 existing_tags_file: Optional[str] = None,
                 word2vec_model_path: Optional[str] = None,
                 transformer_model_name: str = "bert-base-chinese",
                 similarity_threshold: float = 0.7)
    
    def extract_smart_tags(self, query: str, context: str = "") -> SmartTagResult
    def extract_basic_tags(self, query: str) -> List[str]
    def find_missing_tags(self, extracted_tags: List[str]) -> List[str]
    def word2vec_similarity(self, query_tag: str, top_k: int = 5) -> List[Tuple[str, float]]
    def transformer_similarity(self, query_tag: str, context: str = "", top_k: int = 5) -> List[Tuple[str, float]]
    def smart_tag_mapping(self, missing_tags: List[str], context: str = "") -> List[TagMapping]
    def fuzzy_match(self, query_tag: str) -> List[str]
```

### 數據模型

#### TagMapping
```python
@dataclass
class TagMapping:
    original_tag: str        # 原始標籤
    mapped_tags: List[str]   # 映射後的標籤
    confidence: float        # 信心度
    method: str             # 映射方法 ("exact", "word2vec", "transformer", "fuzzy")
```

#### SmartTagResult
```python
@dataclass
class SmartTagResult:
    extracted_tags: List[str]      # 提取的標籤
    mapped_tags: List[TagMapping]  # 映射結果
    confidence: float              # 整體信心度
    processing_time: float         # 處理時間
    method_used: List[str]         # 使用的方法
```

## 使用方式

### 基本使用

```python
from tools.smart_tag_extractor import SmartTagExtractor

# 初始化提取器
extractor = SmartTagExtractor(
    existing_tags_file="tags.json",
    word2vec_model_path="models/word2vec_podcast.model",
    transformer_model_name="bert-base-chinese"
)

# 智能 TAG 提取
query = "我想了解 NVIDIA 和 TSMC 在 AI 晶片市場的競爭"
result = extractor.extract_smart_tags(query)

print(f"提取的 TAG: {result.extracted_tags}")
print(f"信心度: {result.confidence:.2f}")
print(f"使用的方法: {result.method_used}")
```

### 與 PodcastFormatter 整合

```python
from tools.podcast_formatter import PodcastFormatter

# 初始化格式化器（自動整合智能 TAG 提取）
formatter = PodcastFormatter(existing_tags_file="tags.json")

# 格式化 Podcast 推薦
result = formatter.format_podcast_recommendations(podcasts, query)
print(f"使用的 TAG: {result.tags_used}")
```

## 模型訓練

### Word2Vec 模型訓練

```python
from tools.train_word2vec_model import Word2VecTrainer

# 初始化訓練器
trainer = Word2VecTrainer(
    data_dir="../../../data/raw",
    model_save_path="models/word2vec_podcast.model",
    min_count=2,
    vector_size=100,
    window=5,
    workers=4
)

# 訓練模型
success = trainer.train_and_save()
```

### 訓練參數說明

- **min_count**: 最小詞頻（過濾低頻詞）
- **vector_size**: 向量維度（影響語義表達能力）
- **window**: 窗口大小（影響上下文範圍）
- **workers**: 工作進程數（影響訓練速度）

## 配置選項

### 相似度閾值

```python
# 調整相似度閾值
extractor = SmartTagExtractor(similarity_threshold=0.8)  # 更嚴格
extractor = SmartTagExtractor(similarity_threshold=0.6)  # 更寬鬆
```

### 模型選擇

```python
# 使用不同的 Transformer 模型
extractor = SmartTagExtractor(transformer_model_name="hfl/chinese-bert-wwm-ext")
extractor = SmartTagExtractor(transformer_model_name="bert-base-chinese")
```

### 標籤檔案格式

#### JSON 格式
```json
{
    "商業": ["股票", "投資", "理財", "財經"],
    "科技": ["AI", "人工智慧", "機器學習", "深度學習"],
    "教育": ["學習", "教育", "培訓", "課程"]
}
```

#### TXT 格式
```
股票
投資
理財
財經
AI
人工智慧
機器學習
深度學習
```

## 測試與驗證

### 運行測試

```bash
# 測試智能 TAG 提取功能
python test_smart_tag_extraction.py

# 測試 Word2Vec 模型訓練
python tools/train_word2vec_model.py
```

### 測試案例

```python
# 基礎 TAG 測試
"我想了解 NVIDIA 的投資機會" → ["NVIDIA", "投資"]

# 智能映射測試
"我想了解人工智慧的發展趨勢" → ["人工智慧", "AI", "發展"]

# 複雜查詢測試
"我想了解 NVIDIA 和 TSMC 在 AI 晶片市場的競爭" → ["NVIDIA", "TSMC", "AI", "晶片", "競爭"]
```

## 性能優化

### 模型快取

```python
# 啟用模型快取
extractor = SmartTagExtractor()
extractor._initialize_ml_models(word2vec_model_path, transformer_model_name)
```

### 批次處理

```python
# 批次處理多個查詢
queries = ["查詢1", "查詢2", "查詢3"]
results = [extractor.extract_smart_tags(query) for query in queries]
```

### 記憶體優化

```python
# 使用較小的向量維度
trainer = Word2VecTrainer(vector_size=50)  # 減少記憶體使用
```

## 錯誤處理

### 常見錯誤

1. **機器學習套件未安裝**
   ```
   解決方案: pip install gensim transformers torch jieba
   ```

2. **模型檔案不存在**
   ```
   解決方案: 先運行 train_word2vec_model.py 訓練模型
   ```

3. **記憶體不足**
   ```
   解決方案: 減少 vector_size 或使用較小的模型
   ```

### 降級策略

當機器學習組件不可用時，系統會自動降級到基礎 TAG 提取：

```python
if ML_AVAILABLE:
    # 使用智能提取
    result = extractor.extract_smart_tags(query)
else:
    # 降級到基礎提取
    tags = extractor.extract_basic_tags(query)
```

## 未來擴展

### 計劃功能

1. **多語言支援**: 支援英文、日文等其他語言
2. **動態標籤學習**: 根據用戶反饋動態更新標籤表
3. **語義聚類**: 自動聚類相似標籤
4. **個性化標籤**: 根據用戶偏好調整標籤權重

### 技術改進

1. **更先進的模型**: 使用最新的預訓練模型
2. **增量學習**: 支援模型的增量更新
3. **分散式訓練**: 支援大規模數據的分散式訓練
4. **模型壓縮**: 減少模型大小，提高推理速度

## 相關檔案

- `tools/smart_tag_extractor.py`: 智能 TAG 提取器
- `tools/train_word2vec_model.py`: Word2Vec 模型訓練
- `tools/podcast_formatter.py`: Podcast 格式化器（已整合）
- `test_smart_tag_extraction.py`: 測試腳本
- `README_Smart_Tag_Extraction.md`: 本說明文件

## 版本歷史

- **v1.0.0**: 初始版本，支援基礎 TAG 提取和智能映射
- 整合 Word2Vec 和 Transformer 模型
- 支援多種標籤檔案格式
- 提供完整的測試和驗證工具 