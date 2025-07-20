# 統一 RAG 評估系統使用指南

## 📋 概述

統一 RAG 評估系統整合了 Podwise 專案的所有評估功能，提供完整的 RAG 系統評估解決方案。

## 🚀 主要功能

### 1. **多種評估方法**
- **Baseline 評估**: 無 RAG 的純 LLM 回答
- **Naive RAG 評估**: 基本的 RAG 系統評估
- **增強版評估**: Milvus 檢索 + 本地/OpenAI LLM 對比
- **Podwise 專用評估**: 整合 Podwise 向量資料庫

### 2. **多種檢索方式**
- **Milvus 向量搜尋**: 支援 IVF_FLAT 索引優化
- **Podwise 向量搜尋**: 整合 stage4_embedding_prep 資料
- **混合檢索**: 結合多種檢索方式

### 3. **多種 LLM 支援**
- **本地 LLM**: Qwen2.5-Taiwan-7B-Instruct
- **OpenAI LLM**: GPT-3.5-Turbo / GPT-4
- **模擬服務**: 快速測試和驗證

### 4. **完整評估指標**
- **信心度**: 評估系統對答案的信心程度
- **事實性**: 評估答案的事實準確性
- **相關性**: 評估答案與問題的相關程度
- **連貫性**: 評估答案的邏輯連貫性
- **推理時間**: 評估系統響應速度
- **Token 數**: 評估資源使用效率

## 🛠️ 安裝需求

```bash
# 基本依賴
pip install openai pandas numpy

# 向量資料庫
pip install pymilvus

# PDF 處理
pip install pymupdf

# 文本分割
pip install langchain-text-splitters tiktoken

# 環境變數管理
pip install python-dotenv

# 異步支援
pip install aiohttp asyncio-throttle

# 數據驗證
pip install pydantic
```

## 📖 使用範例

### 基本使用

```python
import asyncio
from unified_rag_evaluator import UnifiedRAGEvaluator

# 初始化評估器
evaluator = UnifiedRAGEvaluator(use_mock_services=True)

# 測試問題
questions = [
    "我想學習投資理財，有什麼推薦的 Podcast 嗎？",
    "通勤時間想聽一些輕鬆的內容",
    "有什麼關於創業的節目推薦嗎？"
]

# 執行評估
results = await evaluator.evaluate_batch(questions)

# 生成報告
report = evaluator.generate_comparison_report(
    results, 
    "evaluation_results.txt"
)

print(report)
```

### 使用執行腳本

```bash
# 設定環境變數
export OPENAI_API_KEY="your_api_key"

# 執行評估
chmod +x run_unified_evaluation.sh
./run_unified_evaluation.sh
```

### 選擇執行模式

1. **快速測試**: 使用模擬服務進行快速驗證
2. **完整評估**: 執行所有評估方法
3. **Podwise 專用評估**: 使用 Podwise 向量資料庫
4. **自定義評估**: 手動編寫評估邏輯

## ⚙️ 進階配置

### 自定義評估參數

```python
# 初始化時設定參數
evaluator = UnifiedRAGEvaluator(
    use_mock_services=False,  # 使用真實服務
)

# 自定義搜尋參數
search_results = await evaluator.milvus_search.search(
    query="您的問題",
    top_k=10,      # 返回結果數量
    nprobe=16      # 搜尋探針數量
)
```

### 整合 Podwise 組件

```python
# 確保以下模組可用
from config.integrated_config import get_config
from config.prompt_templates import get_prompt_template, format_prompt

# 初始化時會自動檢測並使用
evaluator = UnifiedRAGEvaluator()
```

### 自定義評估指標

```python
# 擴展評估器
class CustomRAGEvaluator(UnifiedRAGEvaluator):
    def _calculate_custom_metric(self, answer: str, question: str) -> float:
        """自定義評估指標"""
        # 實作您的評估邏輯
        return 0.5
```

## 📊 結果解讀

### 評估報告包含

1. **詳細對比結果**: 每個問題的本地 LLM vs OpenAI 對比
2. **統計摘要**: 平均指標和性能對比
3. **結論分析**: 系統優劣勢分析

### 分數說明

- **信心度 (0-1)**: 越高表示系統越有信心
- **事實性 (0-1)**: 越高表示答案越準確
- **相關性 (0-1)**: 越高表示答案越相關
- **連貫性 (0-1)**: 越高表示答案越連貫
- **速度比**: 本地 LLM 與 OpenAI 的速度對比
- **Token 比**: 本地 LLM 與 OpenAI 的 Token 使用對比

## 🔧 自定義和擴展

### 添加新的評估方法

```python
async def custom_evaluation(self, questions: List[str]) -> List[EvaluationResult]:
    """自定義評估方法"""
    results = []
    for question in questions:
        # 實作您的評估邏輯
        result = EvaluationResult(
            question=question,
            answer="自定義回答",
            confidence=0.8,
            factuality=0.7,
            relevance=0.9,
            coherence=0.8,
            inference_time=1.0,
            token_count=50,
            model_name="Custom",
            retrieval_method="Custom",
            sources=[]
        )
        results.append(result)
    return results
```

### 自定義問題生成

```python
def create_custom_dataset(self, content: str, num_questions: int) -> List[Dict[str, Any]]:
    """自定義問題生成邏輯"""
    # 實作您的問題生成邏輯
    pass
```

## 📁 輸出文件

評估結果會儲存在指定的輸出目錄中：

- `unified_rag_evaluation_report.txt`: 詳細對比報告
- `unified_rag_evaluation_report.csv`: CSV 格式結果
- `full_evaluation_report.txt`: 完整評估報告
- `podwise_evaluation_report.txt`: Podwise 專用評估報告

## 🚨 注意事項

1. **API 成本**: 評估過程會消耗 OpenAI API 額度
2. **執行時間**: 完整評估可能需要較長時間
3. **記憶體使用**: 大量文本處理可能消耗較多記憶體
4. **網路連接**: 需要穩定的網路連接來調用 API

## 🔍 故障排除

### 常見問題

1. **模組導入錯誤**: 確保所有依賴已正確安裝
2. **API 錯誤**: 檢查 OpenAI API Key 是否有效
3. **Milvus 連接失敗**: 檢查 Milvus 服務是否正常運行
4. **記憶體不足**: 減少評估資料集大小

### 調試模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 啟用詳細日誌
evaluator = UnifiedRAGEvaluator()
```

## 📈 性能優化

### 1. **並行評估**
```python
# 使用 asyncio 進行並行評估
results = await asyncio.gather(*[
    evaluator.evaluate_single_question(q) for q in questions
])
```

### 2. **結果快取**
```python
# 實作結果快取機制
import hashlib
cache_key = hashlib.md5(question.encode()).hexdigest()
```

### 3. **批量處理**
```python
# 批量處理問題以提高效率
batch_size = 10
for i in range(0, len(questions), batch_size):
    batch = questions[i:i+batch_size]
    results = await evaluator.evaluate_batch(batch)
```

## 🎯 最佳實踐

### 1. **評估資料集設計**
- 使用多樣化的問題類型
- 包含邊界情況和異常問題
- 確保問題與實際使用場景相符

### 2. **指標選擇**
- 根據應用場景選擇合適的評估指標
- 平衡準確性和效率
- 定期更新評估標準

### 3. **結果分析**
- 深入分析失敗案例
- 識別系統改進機會
- 追蹤性能趨勢

## 📞 支援

如有問題或建議，請參考：
- Podwise 專案文檔
- 統一評估器原始碼
- 評估結果報告

---

**版本**: 3.0.0  
**更新時間**: 2025-07-20  
**作者**: Podwise Team 