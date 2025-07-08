# RAG 評估系統

這個模組整合了 Notebook (`610_ihower_LLM_workshop_RAG_evaluation.ipynb`) 中的所有測試方法，並加入了信心值計算功能。

## 🎯 功能特色

### 整合的測試方法
- **Baseline 評估**：無 RAG 的直接問答
- **Naive RAG 評估**：使用向量搜尋的 RAG 問答
- **信心值計算**：使用 `confidence_controller.py` 計算每個回答的信心值
- **事實性評估**：自動評估回答的事實準確性

### 輸出格式
- **JSON 格式**：詳細的評估結果
- **CSV 格式**：便於分析的表格格式
- **Markdown 報告**：易讀的評估報告
- **統計摘要**：各方法的性能比較

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install openai pymupdf pandas numpy pydantic
```

### 2. 設定環境變數

```bash
export OPENAI_API_KEY="your-openai-api-key"
export PDF_PATH="path/to/your/document.pdf"  # 可選
```

### 3. 執行測試

```bash
# 測試系統功能
python test_rag_evaluation.py

# 執行完整評估
python run_rag_evaluation.py
```

## 📊 評估流程

### 1. 合成資料集創建
- 讀取 PDF 文件
- 使用 LLM 自動產生問題答案對
- 專注於投資和個人理財主題

### 2. 多方法評估
- **Baseline**：直接問答，無上下文
- **Naive RAG**：使用向量搜尋檢索相關內容後回答

### 3. 信心值計算
每個回答都會計算信心值，考慮：
- 問題與回答的相關性
- 回答的完整性
- 上下文的支持程度

### 4. 事實性評估
使用 LLM 評估回答的事實準確性：
- A: 子集且一致 (0.4分)
- B: 超集且一致 (0.6分)
- C: 完全一致 (1.0分)
- D: 事實衝突 (0.0分)
- E: 差異不影響正確性 (1.0分)

## 📁 輸出檔案

評估完成後會在 `evaluation_results/` 目錄產生：

```
evaluation_results/
├── evaluation_results_20241201_143022.json    # 詳細結果
├── evaluation_statistics_20241201_143022.json # 統計資訊
├── evaluation_results_20241201_143022.csv     # CSV 格式
└── evaluation_report.md                       # 評估報告
```

## 📈 結果分析

### 統計指標
- **平均信心值**：回答的可信度
- **平均事實性分數**：回答的準確性
- **標準差**：結果的一致性
- **範圍**：最佳和最差表現

### 比較分析
- Baseline vs Naive RAG 的性能比較
- 信心值與事實性分數的相關性
- 不同問題類型的表現差異

## 🔧 自定義配置

### 修改評估參數

```python
from evaluation.rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator(
    openai_api_key="your-key",
    model_name="gpt-4o-mini",  # 可更改模型
    output_dir="custom_results"  # 自定義輸出目錄
)
```

### 調整問題產生

```python
# 修改每頁產生的問題數量
eval_dataset = evaluator.create_synthetic_dataset(
    pdf_path="document.pdf",
    num_questions_per_page=3  # 預設為 2
)
```

## 🧪 測試功能

### 單元測試
```bash
python test_rag_evaluation.py
```

測試內容：
- 信心值控制器功能
- RAG 評估器初始化
- 合成資料集創建
- 單一評估執行

### 完整評估
```bash
python run_rag_evaluation.py
```

## 📋 使用範例

### 基本使用

```python
from evaluation.rag_evaluator import RAGEvaluator

# 初始化評估器
evaluator = RAGEvaluator(
    openai_api_key="your-key",
    model_name="gpt-4o-mini"
)

# 執行完整評估
results = evaluator.run_complete_evaluation("document.pdf")

# 查看結果
print(f"總評估數量: {results['total_evaluations']}")
print(f"統計資訊: {results['statistics']}")
```

### 自定義評估

```python
# 只執行 Baseline 評估
baseline_results = evaluator.baseline_evaluation(eval_dataset)

# 只執行 Naive RAG 評估
naive_rag_results = evaluator.naive_rag_evaluation(eval_dataset)

# 計算統計資訊
statistics = evaluator._calculate_statistics(baseline_results + naive_rag_results)
```

## 🔍 故障排除

### 常見問題

1. **OpenAI API Key 錯誤**
   ```
   解決方案：檢查環境變數設定
   export OPENAI_API_KEY="your-key"
   ```

2. **PDF 檔案讀取失敗**
   ```
   解決方案：安裝 PyMuPDF
   pip install pymupdf
   ```

3. **向量搜尋失敗**
   ```
   解決方案：檢查向量資料庫連接
   或使用內建測試模式
   ```

### 日誌查看

系統會輸出詳細的日誌資訊，包括：
- 評估進度
- 錯誤訊息
- 統計摘要

## 📚 相關文件

- [Notebook 原始檔案](../610_ihower_LLM_workshop_RAG_evaluation.ipynb)
- [信心值控制器](../core/confidence_controller.py)
- [向量搜尋工具](../tools/enhanced_vector_search.py)

## 🤝 貢獻

如需修改或擴展功能，請：
1. 修改 `rag_evaluator.py` 中的相關方法
2. 更新測試腳本
3. 更新此說明文件 