# 繁體中文情感分析引擎

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OOP](https://img.shields.io/badge/Architecture-OOP-orange.svg)](https://en.wikipedia.org/wiki/Object-oriented_programming)

## 📋 概述

這是一個專為繁體中文設計的情感分析引擎，基於 **NLTK** 和自定義中文情感詞典，採用 **OOP 架構** 和 **Google Clean Code 原則** 開發。專案整合了 [繁體中文 NLP 從 word2vec 到情感分析](https://studentcodebank.wordpress.com/2019/02/22/%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-nlp-%E5%BE%9Eword2vec%E5%88%B0-%E6%83%85%E6%84%9F%E5%88%86%E6%9E%90/) 的完整邏輯，提供高準確度的中文情感分析服務。

## 🎯 功能特色

- **繁體中文優化**: 專門針對台灣繁體中文語境設計
- **多維度分析**: 提供 Compound、正面、負面、中性分數
- **智能文本處理**: 使用 jieba 分詞 + 停用詞過濾
- **批次處理**: 支援大量 JSON 檔案批次分析
- **OOP 架構**: 符合 Google Clean Code 原則
- **可擴展性**: 模組化設計，易於維護和擴展

## 🏗️ 系統架構

```
vaderSentiment/
├── core/                          # 核心模組
│   ├── __init__.py               # 模組初始化
│   ├── text_preprocessor.py      # 文本預處理器
│   ├── lexicon_manager.py        # 詞典管理器
│   ├── sentiment_analyzer.py     # 情感分析器
│   └── data_processor.py         # 資料處理器
├── scripts/                       # 工具腳本
│   ├── fix_json_format.py        # JSON 格式修正
│   ├── clean_filenames.py        # 檔名清理
│   ├── convert_to_json.py        # 格式轉換
│   ├── convert_to_traditional.py # 簡繁轉換
│   └── filename_rename_table.csv # 檔名對照表
├── comment_data/                  # 原始資料
│   └── *.json                    # JSON 檔案
├── main.py                       # 主程式入口
├── apple_podcast_analyzer.py     # Apple Podcast 分析器
├── sentiment_analysis_engine.py  # 舊版分析引擎（保留）
├── vader_lexicon.txt             # 英文情感詞典
├── vader_lexicon2.txt            # 擴展詞典（簡體中文）
├── emoji_utf8_lexicon.txt        # 表情符號詞典
└── README.md                     # 專案說明
```

## 🧠 情感分析邏輯

### A. 文本預處理 (TextPreprocessor)

```python
# 1. 文本清理
text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)  # 保留中文、英文、數字
text = re.sub(r'\s+', ' ', text).strip()            # 移除多餘空格

# 2. 中文分詞
tokens = jieba.lcut(text)                           # jieba 分詞
tokens = [token for token in tokens if token not in stop_words and len(token) > 1]

# 3. 停用詞過濾
stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', ...}
```

### B. 中文情感詞典 (LexiconManager)

#### 1. 正面詞彙 (120+ 個)
```python
positive_words = {
    '好', '棒', '讚', '優秀', '完美', '喜歡', '愛', '開心', '快樂', '高興', 
    '興奮', '滿意', '成功', '厲害', '強大', '美好', '精彩', '有趣', '好玩',
    '舒適', '方便', '快速', '便宜', '划算', '值得', '推薦', '支持', '鼓勵',
    '幫助', '溫暖', '友善', '親切', '專業', '認真', '負責', '誠實', '可靠',
    '穩定', '安全', '健康', '新鮮', '美味', '漂亮', '帥氣', '可愛', '聰明',
    '智慧', '創意', '創新', '進步', '發展', '成長', '學習', '提升', '改善',
    '解決', '完成', '實現', '夢想', '希望', '未來', '機會', '成功', '勝利',
    '冠軍', '第一', '最好', '最棒', '最讚', '超棒', '超讚', '無敵', '完美',
    '理想', '優質', '高品質', '頂級', '一流', '傑出', '卓越', '非凡', '出色',
    '優雅', '精緻', '細緻', '用心', '貼心', '周到', '細心', '耐心', '恆心',
    '決心', '信心', '勇氣', '堅強', '勇敢', '樂觀', '積極', '正面', '陽光',
    '活力', '能量', '動力', '熱情', '激情', '熱愛', '熱衷', '專注', '投入',
    '專心', '專注', '專一', '專精', '精通', '熟練'
}
```

#### 2. 負面詞彙 (150+ 個) - 已清理重複
```python
negative_words = {
    # 基礎負面情感詞彙
    '壞', '糟', '爛', '差', '討厭', '恨', '生氣', '憤怒', '傷心', '難過',
    '痛苦', '失望', '失敗', '無聊', '煩', '累', '疲憊', '困難', '麻煩',
    '複雜', '昂貴', '貴', '浪費', '不值得', '不推薦', '反對', '批評',
    '抱怨', '指責', '冷漠', '無情', '不友善', '不專業', '不認真', '不負責',
    '不誠實', '不可靠', '不穩定', '不安全', '不健康', '不新鮮', '難吃',
    '醜', '難看', '笨', '愚蠢', '無創意', '退步', '退縮', '停滯',
    '問題', '障礙', '挫折', '絕望', '無望', '失去', '錯過', '輸',
    '單調', '枯燥', '乏味', '沉悶', '壓抑', '沉重', '折磨', '煎熬',
    '恐懼', '害怕', '驚恐', '恐慌',
    
    # 品質相關負面詞彙
    '不公平', '不正義', '不舒服', '髒', '亂', '邪惡', '說謊', 
    '膽小', '軟弱', '悲觀', '消極', '被動', '依賴', '不平等', '專制', 
    '戰爭', '分裂', '守舊', '吵', '危險', '傳統', '保守', '限制', '競爭',
    
    # 否定詞組合（避免重複）
    '不喜歡', '不愛', '不開心', '不高興', '不快樂', '不滿意', '不成功',
    '不厲害', '不強大', '不美好', '不精彩', '不有趣', '不好玩', '不舒適',
    '不方便', '不快速', '不便宜', '不划算', '不支持', '不鼓勵', '不幫助',
    '不溫暖', '不親切', '不美味', '不漂亮', '不帥氣', '不可愛', '不聰明',
    '不智慧', '不能', '不需要', '不想要', '不知道', '擔心', '不累', '不餓', '不渴'
}
```

#### 3. 程度詞 (50+ 個)
```python
intensifiers = {
    '非常': 2.0, '很': 1.5, '特別': 1.8, '極其': 2.0, '十分': 1.8,
    '相當': 1.3, '比較': 1.2, '有點': 0.8, '稍微': 0.6, '一點': 0.5,
    '超級': 2.5, '無敵': 2.5, '超': 1.8, '太': 1.5, '真': 1.3,
    '確實': 1.2, '真的': 1.3, '實在': 1.2, '簡直': 1.5, '完全': 1.8,
    '絕對': 2.0, '根本': 1.5, '從來': 1.3, '從來沒有': 1.5, '從來不': 1.5,
    # 從停用詞中移出的程度詞
    '熱': 1.2, '冷': 1.2, '暖': 1.1, '涼': 1.1, '亮': 1.1, '暗': 1.2,
    '安靜': 1.1, '吵': 1.3, '整齊': 1.1, '亂': 1.3, '簡單': 1.1, '複雜': 1.3,
    '容易': 1.1, '困難': 1.3, '便宜': 1.1, '貴': 1.3, '免費': 1.1, '付費': 1.2,
    '公開': 1.1, '私人': 1.1, '正式': 1.1, '非正式': 1.1, '重要': 1.2,
    '不重要': 1.2, '緊急': 1.3, '不緊急': 1.1, '危險': 1.5, '安全': 1.1
}
```

#### 4. 否定詞 (80+ 個)
```python
negations = {
    '不', '沒', '無', '別', '莫', '勿', '未', '非', '否', '不是',
    '沒有', '無關', '無所謂', '不在乎', '不關心', '不喜歡', '不愛',
    '不開心', '不快樂', '不高興', '不滿意', '不成功', '不厲害',
    '不強大', '不美好', '不精彩', '不有趣', '不好玩', '不舒適',
    '不方便', '不快速', '不便宜', '不划算', '不值得', '不推薦',
    '不支持', '不鼓勵', '不幫助', '不溫暖', '不友善', '不親切',
    '不專業', '不認真', '不負責', '不誠實', '不可靠', '不穩定',
    '不安全', '不健康', '不新鮮', '不美味', '不漂亮', '不帥氣',
    '不可愛', '不聰明', '不智慧', '不創意', '不創新', '不退步',
    '不退縮', '不停滯', '沒問題', '沒困難', '沒障礙', '沒失敗',
    '沒挫折', '沒絕望', '沒無望', '沒過去', '沒失去', '沒錯過',
    '沒失敗', '沒輸', '沒最後', '沒最差', '沒最糟', '沒最爛'
}
```

### C. 情感分數計算邏輯

#### 1. 詞彙匹配與權重計算
```python
def _calculate_sentiment_scores(self, tokens: List[str]) -> Dict[str, float]:
    positive_score = 0.0
    negative_score = 0.0
    
    positive_words = self.lexicon.get_positive_words()
    negative_words = self.lexicon.get_negative_words()
    intensifiers = self.lexicon.get_intensifiers()
    negations = self.lexicon.get_negations()
    
    for i, token in enumerate(tokens):
        # 檢查程度詞
        intensity = 1.0
        if token in intensifiers:
            intensity = intensifiers[token]
        
        # 檢查否定詞
        negation_factor = 1.0
        if i > 0 and tokens[i-1] in negations:
            negation_factor = -1.0
        
        # 計算分數
        if token in positive_words:
            positive_score += intensity * negation_factor
        elif token in negative_words:
            negative_score += intensity * negation_factor
    
    return {
        'positive': positive_score,
        'negative': negative_score
    }
```

## 🚀 快速開始

### 基本使用

```python
from vaderSentiment import get_sentiment_analysis

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

## 🎯 設計原則

### OOP 設計原則
- **單一職責原則 (SRP)**: 每個類別專責特定功能
- **開放封閉原則 (OCP)**: 可擴展新的分析器
- **依賴反轉原則 (DIP)**: 高層模組依賴抽象介面
- **介面隔離原則 (ISP)**: 明確的職責分工
- **里氏替換原則 (LSP)**: 子類別可替換父類別

## 🛠️ 依賴項目

- nltk
- jieba
- pandas
- numpy
- scikit-learn 