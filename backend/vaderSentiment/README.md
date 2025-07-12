# Podcast 情感分析與綜合評分系統

## 📋 專案概述

本系統專門針對 20 個 Podcast 頻道進行情感文字分析與綜合評分，提供正向、負向、中性情感分類，並整合多項指標進行綜合評分。

## 🎯 主要功能

### 1. 情感分析
- 使用 VADER Sentiment 進行中文文本情感分析
- 支援正向、負向、中性情感分類
- 提供情感分數與信心度評估

### 2. 綜合評分系統
根據以下權重分配進行綜合評分（滿分 5 分）：

| 評分來源 | 權重 |
|---------|------|
| Apple podcast 星等 | 40% |
| Apple podcast 評論文字分析 | 35% |
| 使用者點擊率（問卷喜好度） | 15% |
| Apple podcast 評論數 | 10% |

### 3. 分析功能
- **情感分析**: 分析 Podcast 評論的情感傾向
- **排名分析**: 根據多項指標進行 Podcast 排名
- **評論分析**: 深入分析評論內容與關鍵字
- **綜合評分**: 整合所有指標的加權評分

## 🏗️ 系統架構

```
vaderSentiment/
├── src/                          # 核心模組
│   ├── core/                     # 核心功能
│   │   ├── sentiment_analyzer.py # 情感分析器
│   │   ├── podcast_ranking.py    # 排名分析器
│   │   ├── comment_analyzer.py   # 評論分析器
│   │   └── rating_system.py      # 綜合評分系統
│   └── utils/                    # 工具模組
│       ├── data_processor.py     # 資料處理器
│       └── report_generator.py   # 報告生成器
├── Podcast_info/                 # Podcast 資訊 (20個頻道)
├── comment_data/                 # 評論資料
├── main.py                       # 主程式
├── requirements.txt              # 依賴套件
└── README.md                     # 說明文件
```

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 執行分析

#### 完整分析（推薦）
```bash
python main.py --mode complete
```

#### 單一功能分析
```bash
# 情感分析
python main.py --mode sentiment

# 指定分類情感分析
python main.py --mode sentiment --category 商業
python main.py --mode sentiment --category 教育

# 排名分析
python main.py --mode ranking

# 評論分析
python main.py --mode comment

# 綜合評分分析
python main.py --mode rating

# 測試功能
python main.py --mode test
```

## 📊 輸出結果

### 1. 情感分析報告
- 各 Podcast 的情感分數
- 正向、負向、中性情感分佈
- 情感分析信心度

### 2. 綜合評分報告
- Podcast 綜合評分排行榜
- 各項指標詳細分數
- 按分類的評分分析

### 3. 評論分析報告
- 關鍵字分析
- 評論情感趨勢
- 使用者回饋統計

## 🔧 技術特色

### OOP 架構設計
- 模組化設計，易於維護與擴展
- 完整的型別提示
- 統一的錯誤處理機制

### 中文文本處理
- 支援中文分詞
- 情感詞彙自定義
- 語境感知分析

### 資料整合
- 整合 Apple Podcast 資料
- 結合使用者問卷回饋
- 多源資料驗證

## 📈 評分算法

### 加權計算公式
```
綜合評分 = (Apple星等 × 0.4) + (評論情感分數 × 0.35) + (使用者參與度 × 0.15) + (評論數標準化分數 × 0.1)
```

### 情感分數轉換
- VADER 情感分數範圍: (-1, 1)
- 轉換為評分範圍: (0, 5)
- 轉換公式: `(情感分數 + 1) × 2.5`

### 評論數標準化
- 基準: 1000 評論 = 滿分 5 分
- 標準化公式: `min(評論數 / 1000, 1) × 5`

## 🎯 支援的 Podcast 分類

### 商業類 (10個)
- 投資理財
- 商業管理
- 創業經營
- 職涯發展

### 教育類 (10個)
- 語言學習
- 知識分享
- 技能提升
- 個人成長

## 📝 使用範例

### Python API 使用
```python
from src.core.rating_system import RatingSystem

# 初始化評分系統
rating_system = RatingSystem()

# 生成評分報告
rating_system.save_rating_report("my_rating_report.csv")

# 獲取分類分析
category_analysis = rating_system.get_category_analysis()
```

### 自定義權重
```python
from src.core.rating_system import RatingSystem, RatingWeights

# 自定義權重
custom_weights = RatingWeights(
    apple_rating=0.35,
    comment_sentiment=0.40,
    user_engagement=0.15,
    comment_count=0.10
)

rating_system = RatingSystem(weights=custom_weights)
```

## 🔍 故障排除

### 常見問題

1. **模組導入錯誤**
   ```bash
   # 確保在正確目錄下執行
   cd backend/vaderSentiment
   python main.py --mode test
   ```

2. **中文分詞問題**
   - 檢查 jieba 套件是否正確安裝
   - 確認文本編碼為 UTF-8

3. **資料檔案缺失**
   - 確認 `Podcast_info/` 目錄包含 20 個 JSON 檔案
   - 確認 `comment_data/` 目錄包含評論資料

4. **評分計算異常**
   - 檢查 testdata 目錄中的使用者回饋資料
   - 確認 Apple Podcast 評分格式正確

### 日誌查看
```bash
# 查看詳細日誌
python main.py --mode complete 2>&1 | tee analysis.log
```

## 📊 效能優化

### 記憶體使用
- 分批處理大量評論資料
- 使用生成器減少記憶體佔用
- 及時釋放不需要的資料

### 處理速度
- 並行處理多個 Podcast
- 快取情感分析結果
- 優化檔案 I/O 操作

## 🤝 貢獻指南

### 開發環境設定
```bash
# 安裝開發依賴
pip install -r requirements.txt

# 程式碼格式化
black src/

# 程式碼檢查
flake8 src/

# 執行測試
pytest tests/
```

### 程式碼規範
- 遵循 PEP 8 程式碼風格
- 提供完整的型別提示
- 撰寫詳細的 docstring
- 添加適當的錯誤處理

## 📄 授權條款

本專案採用 MIT 授權條款，詳見 LICENSE 檔案。

## 📞 聯絡資訊

如有問題或建議，請透過以下方式聯絡：
- 專案 Issues: GitHub Issues
- 技術支援: 開發團隊

---

**版本**: 3.0.0  
**最後更新**: 2024年12月  
**維護者**: Podwise Team 