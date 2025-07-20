# Podwise RAG 評估系統使用指南

## 📋 概述

本 RAG 評估系統基於 ihower LLM workshop 的評估框架，專為 Podwise 專案設計，提供完整的 RAG 系統評估功能。

## 🚀 主要功能

### 1. **多種內容類型支援**
- **PDF 文件**: 自動提取和分塊 PDF 內容
- **純文本**: 直接處理文本內容
- **播客內容**: 整合 Podwise 資料庫的 episode 內容

### 2. **多種評估方法**
- **Baseline 評估**: 無 RAG 的純 LLM 回答
- **Naive RAG 評估**: 基本的 RAG 系統評估
- **Ragas 指標評估**: 專業的 RAG 評估指標

### 3. **評估指標**
- **事實性分數**: 評估答案的事實準確性
- **信心值**: 評估系統對答案的信心程度
- **上下文召回率**: 評估檢索內容的完整性
- **上下文精確度**: 評估檢索內容的相關性
- **忠實度**: 評估答案對上下文的忠實程度

## 🛠️ 安裝需求

```bash
# 基本依賴
pip install openai pandas numpy

# PDF 處理
pip install pymupdf

# 文本分割
pip install langchain-text-splitters tiktoken

# 環境變數管理
pip install python-dotenv

# 可選：Podwise 專案組件
# 如果您的專案有 confidence_controller 和 enhanced_vector_search
```

## 📖 使用範例

### 基本使用

```python
from rag_evaluator import RAGEvaluator
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化評估器
evaluator = RAGEvaluator(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4o-mini",
    output_dir="evaluation_results",
    use_podwise_components=True  # 如果 Podwise 組件可用
)

# 評估 PDF 文件
result = evaluator.run_complete_evaluation(
    content_source="path/to/document.pdf",
    content_type="pdf",
    evaluation_methods=["baseline", "naive_rag", "ragas"]
)

print(result['report'])
```

### 評估文本內容

```python
sample_text = """
您的文本內容...
"""

result = evaluator.run_complete_evaluation(
    content_source=sample_text,
    content_type="text",
    evaluation_methods=["baseline", "naive_rag"]
)
```

### 評估播客內容

```python
result = evaluator.run_complete_evaluation(
    content_source="episode_001",  # episode ID
    content_type="episode",
    evaluation_methods=["baseline", "naive_rag"]
)
```

## ⚙️ 進階配置

### 自定義評估參數

```python
# 創建評估資料集時自定義參數
eval_dataset = evaluator.create_synthetic_dataset(
    content_source="your_content",
    content_type="pdf",
    num_questions_per_chunk=3,  # 每個 chunk 產生 3 個問題
    chunk_size=1000,            # chunk 大小
    chunk_overlap=200           # chunk 重疊
)

# 單獨執行特定評估方法
baseline_results = evaluator.baseline_evaluation(eval_dataset)
naive_rag_results = evaluator.naive_rag_evaluation(eval_dataset)
ragas_results = evaluator.ragas_evaluation(eval_dataset)
```

### 整合 Podwise 組件

如果您有 Podwise 專案的組件，可以啟用進階功能：

```python
# 確保以下模組可用
from core.confidence_controller import ConfidenceController
from tools.enhanced_vector_search import EnhancedVectorSearch

# 初始化時啟用 Podwise 組件
evaluator = RAGEvaluator(
    openai_api_key=openai_api_key,
    use_podwise_components=True
)
```

## 📊 結果解讀

### 評估報告包含

1. **統計摘要**: 各方法的平均分數和標準差
2. **詳細結果**: 每個問題的評估結果
3. **比較分析**: 不同方法間的效能比較

### 分數說明

- **事實性分數 (0-1)**: 越高表示答案越準確
- **信心值 (0-1)**: 越高表示系統越有信心
- **上下文召回率 (0-1)**: 越高表示檢索越完整
- **上下文精確度 (0-1)**: 越高表示檢索越相關
- **忠實度 (0-1)**: 越高表示答案越忠實於上下文

## 🔧 自定義和擴展

### 添加新的評估方法

```python
def custom_evaluation(self, eval_dataset):
    """自定義評估方法"""
    results = []
    for item in eval_dataset:
        # 實作您的評估邏輯
        result = {
            "method": "Custom",
            "question": item["input"],
            "custom_score": your_calculation(),
            # ... 其他欄位
        }
        results.append(result)
    return results
```

### 自定義問題生成

```python
def custom_question_generation(self, content, content_type):
    """自定義問題生成邏輯"""
    # 實作您的問題生成邏輯
    pass
```

## 📁 輸出文件

評估結果會儲存在指定的輸出目錄中：

- `evaluation_results_YYYYMMDD_HHMMSS.json`: 詳細結果
- `evaluation_statistics_YYYYMMDD_HHMMSS.json`: 統計資訊
- `evaluation_results_YYYYMMDD_HHMMSS.csv`: CSV 格式結果

## 🚨 注意事項

1. **API 成本**: 評估過程會消耗 OpenAI API 額度
2. **執行時間**: 完整評估可能需要較長時間
3. **記憶體使用**: 大量文本處理可能消耗較多記憶體
4. **網路連接**: 需要穩定的網路連接來調用 OpenAI API

## 🔍 故障排除

### 常見問題

1. **模組導入錯誤**: 確保所有依賴已正確安裝
2. **API 錯誤**: 檢查 OpenAI API Key 是否有效
3. **記憶體不足**: 減少 chunk_size 或評估資料集大小
4. **網路超時**: 增加重試機制或檢查網路連接

### 調試模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 啟用詳細日誌
evaluator = RAGEvaluator(...)
```

## 📞 支援

如有問題或建議，請參考：
- Podwise 專案文檔
- ihower LLM workshop 原始筆記本
- OpenAI API 文檔 