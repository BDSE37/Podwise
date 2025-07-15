# VADER Sentiment Analysis Module

## 概述

VADER (Valence Aware Dictionary and sEntiment Reasoner) 情感分析模組，專門用於播客內容的情感評分和分析。

## 功能特色

- **情感分析**：分析播客內容的情感傾向
- **排名分析**：評估播客在各平台的排名表現
- **評論分析**：分析用戶評論的情感分布
- **綜合評分**：結合多項指標的綜合評分系統
- **分類分析**：支援商業和教育類別的專門分析

## 模組結構

```
vaderSentiment/
├── main.py              # 主程式入口
├── test_rating.py       # 評分測試腳本
├── requirements.txt     # 依賴套件
├── README.md           # 說明文件
└── src/                # 核心程式碼
    ├── core/           # 核心分析類別
    │   ├── sentiment_analyzer.py
    │   ├── podcast_ranking.py
    │   ├── comment_analyzer.py
    │   └── rating_system.py
    └── utils/          # 工具類別
        ├── data_processor.py
        └── report_generator.py
```

## 使用方式

### 1. 情感分析
```bash
python main.py --mode sentiment
```

### 2. 分類情感分析
```bash
python main.py --mode sentiment --category 商業
python main.py --mode sentiment --category 教育
```

### 3. 排名分析
```bash
python main.py --mode ranking
```

### 4. 評論分析
```bash
python main.py --mode comment
```

### 5. 綜合評分分析
```bash
python main.py --mode rating
```

### 6. 完整分析流程
```bash
python main.py --mode complete
```

### 7. 測試功能
```bash
python main.py --mode test
```

## 整合計劃

### 階段一：保持現狀
- 維持現有的 OOP 架構
- 確保所有功能正常運作
- 完善錯誤處理和日誌記錄

### 階段二：整合到評分系統
- 整合到 `ml_pipeline` 模組
- 建立統一的評分 API
- 支援即時評分功能

### 階段三：擴展功能
- 支援更多情感分析模型
- 增加多語言支援
- 建立評分歷史追蹤

## 依賴套件

- vaderSentiment
- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn

## 開發狀態

- ✅ 核心功能完成
- ✅ OOP 架構完整
- ✅ 測試腳本可用
- 🔄 整合到主系統（計劃中）
- 🔄 即時評分功能（計劃中）

## 注意事項

1. 此模組將保留在 backend 目錄中
2. 後續將整合到播客評分系統
3. 支援情感分析用於內容品質評估
4. 可與 RAG Pipeline 結合進行內容分析

## 維護者

Podwise Team 