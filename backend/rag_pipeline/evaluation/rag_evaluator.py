#!/usr/bin/env python3
"""
RAG 評估系統
整合 Notebook 中的所有測試方法並加入信心值計算
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.confidence_controller import ConfidenceController
from tools.enhanced_vector_search import EnhancedVectorSearch

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEvaluator:
    """RAG 評估系統主類別"""
    
    def __init__(self, 
                 openai_api_key: str,
                 model_name: str = "gpt-4o-mini",
                 output_dir: str = "evaluation_results"):
        """
        初始化 RAG 評估系統
        
        Args:
            openai_api_key: OpenAI API Key
            model_name: 使用的模型名稱
            output_dir: 結果輸出目錄
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化信心值控制器
        self.confidence_controller = ConfidenceController()
        
        # 初始化向量搜尋
        self.vector_search = EnhancedVectorSearch()
        
        # 設定 OpenAI 客戶端
        self._setup_openai_client()
        
        # 評估結果存儲
        self.evaluation_results = []
        
    def _setup_openai_client(self):
        """設定 OpenAI 客戶端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI 客戶端初始化成功")
        except ImportError:
            logger.error("請安裝 openai 套件: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI 客戶端初始化失敗: {str(e)}")
            raise
    
    def create_synthetic_dataset(self, pdf_path: str, num_questions_per_page: int = 2) -> List[Dict[str, Any]]:
        """
        創建合成評估資料集
        
        Args:
            pdf_path: PDF 檔案路徑
            num_questions_per_page: 每頁產生的問題數量
            
        Returns:
            評估資料集
        """
        try:
            import fitz  # PyMuPDF
            from pydantic import Field, BaseModel
            from typing import List
            
            class QAPair(BaseModel):
                reference: str = Field(..., description="原始文本段落")
                question: str = Field(..., description="問題")
                answer: str = Field(..., description="答案")
            
            class QAPairs(BaseModel):
                pairs: List[QAPair] = Field(..., description="問題答案對列表")
            
            # 讀取 PDF
            pages = fitz.open(pdf_path)
            dataset = []
            
            for idx, page in enumerate(pages):
                context = page.get_text()
                if len(context.strip()) < 50:  # 跳過太短的頁面
                    continue
                    
                # 產生問題
                pairs = self._produce_questions(context, num_questions_per_page)
                
                for pair in pairs:
                    qa_data = pair.model_dump()
                    qa_data["page_index"] = idx
                    qa_data["file_name"] = Path(pdf_path).name
                    dataset.append(qa_data)
            
            # 轉換為評估格式
            eval_dataset = []
            for qa in dataset:
                eval_dataset.append({
                    "input": qa['question'],
                    "expected": qa['answer'],
                    "metadata": {
                        "reference": qa['reference'],
                        'page_index': qa['page_index'],
                        'file_name': qa['file_name']
                    },
                })
            
            logger.info(f"成功創建 {len(eval_dataset)} 筆評估資料")
            return eval_dataset
            
        except ImportError:
            logger.error("請安裝 PyMuPDF: pip install pymupdf")
            raise
        except Exception as e:
            logger.error(f"創建合成資料集失敗: {str(e)}")
            raise
    
    def _produce_questions(self, content: str, num_questions: int = 2) -> List[Any]:
        """產生問題答案對"""
        try:
            from pydantic import Field, BaseModel
            from typing import List
            
            class QAPair(BaseModel):
                reference: str = Field(..., description="原始文本段落")
                question: str = Field(..., description="問題")
                answer: str = Field(..., description="答案")
            
            class QAPairs(BaseModel):
                pairs: List[QAPair] = Field(..., description="問題答案對列表")
            
            prompt = f"""請從以下文本中產生 {num_questions} 個問題答案對，專注於投資和個人理財主題。

對於每個問題答案對，請提供一個問題、一個獨特的答案，並包含原始文本中確切的文本段落。

重要要求：
1. 專注於投資、財務規劃、財富管理、股市、退休規劃、稅務優化或其他個人理財相關主題
2. 所有問題和答案必須使用繁體中文（台灣）
3. 使用台灣金融業常用的術語和表達方式
4. 如果文本不包含金融相關資訊，提取最相關的方面，可應用於個人理財或投資決策
5. 對於每個問題答案對，包含原始文本中確切的文本段落

文本內容：{content}"""

            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=QAPairs
            )
            
            parsed_result = completion.choices[0].message.parsed
            return parsed_result.pairs
            
        except Exception as e:
            logger.error(f"產生問題失敗: {str(e)}")
            return []
    
    def baseline_evaluation(self, eval_dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Baseline 評估（無 RAG）
        
        Args:
            eval_dataset: 評估資料集
            
        Returns:
            評估結果列表
        """
        logger.info("開始 Baseline 評估...")
        results = []
        
        for i, item in enumerate(eval_dataset):
            try:
                # 直接回答問題
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": item["input"]}]
                )
                answer = response.choices[0].message.content
                
                # 計算信心值
                confidence = self.confidence_controller.calculate_confidence(
                    query=item["input"],
                    answer=answer,
                    context=""
                )
                
                # 計算事實性分數
                factuality_score = self._calculate_factuality(
                    expected=item["expected"],
                    actual=answer
                )
                
                result = {
                    "method": "Baseline",
                    "question": item["input"],
                    "expected_answer": item["expected"],
                    "actual_answer": answer,
                    "confidence": confidence,
                    "factuality_score": factuality_score,
                    "metadata": item.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result)
                logger.info(f"Baseline 評估進度: {i+1}/{len(eval_dataset)}")
                
            except Exception as e:
                logger.error(f"Baseline 評估失敗 (問題 {i+1}): {str(e)}")
                continue
        
        return results
    
    def naive_rag_evaluation(self, eval_dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Naive RAG 評估
        
        Args:
            eval_dataset: 評估資料集
            
        Returns:
            評估結果列表
        """
        logger.info("開始 Naive RAG 評估...")
        results = []
        
        for i, item in enumerate(eval_dataset):
            try:
                # 使用向量搜尋檢索相關內容
                search_results = self.vector_search.search(
                    query=item["input"],
                    top_k=5
                )
                
                # 構建上下文
                context = "\n".join([f"* {doc}" for doc in search_results])
                
                # 使用 RAG 回答問題
                prompt = f"""我將提供您一份文件，然後詢問您關於該文件的問題。請按照以下步驟回答：

<document>
{context}
</document>

問題：{item["input"]}

請用繁體中文（台灣）回答，並使用文件中的事實來回答問題。"""

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = response.choices[0].message.content
                
                # 計算信心值
                confidence = self.confidence_controller.calculate_confidence(
                    query=item["input"],
                    answer=answer,
                    context=context
                )
                
                # 計算事實性分數
                factuality_score = self._calculate_factuality(
                    expected=item["expected"],
                    actual=answer
                )
                
                result = {
                    "method": "Naive RAG",
                    "question": item["input"],
                    "expected_answer": item["expected"],
                    "actual_answer": answer,
                    "retrieved_context": context,
                    "confidence": confidence,
                    "factuality_score": factuality_score,
                    "metadata": item.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result)
                logger.info(f"Naive RAG 評估進度: {i+1}/{len(eval_dataset)}")
                
            except Exception as e:
                logger.error(f"Naive RAG 評估失敗 (問題 {i+1}): {str(e)}")
                continue
        
        return results
    
    def _calculate_factuality(self, expected: str, actual: str) -> float:
        """
        計算事實性分數
        
        Args:
            expected: 期望答案
            actual: 實際答案
            
        Returns:
            事實性分數 (0-1)
        """
        try:
            prompt = f"""請評估以下兩個答案之間的事實內容差異：

期望答案：{expected}
實際答案：{actual}

請根據以下標準評分：
- A: 實際答案是期望答案的子集，且完全一致 (0.4分)
- B: 實際答案是期望答案的超集，包含更多細節但一致 (0.6分)  
- C: 兩者完全一樣，所有細節一致 (1.0分)
- D: 兩者有事實上的衝突或矛盾 (0.0分)
- E: 雖然不完全一樣，但差異不影響事實正確性 (1.0分)

請只回傳分數 (0.0-1.0)："""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # 確保在 0-1 範圍內
            except ValueError:
                logger.warning(f"無法解析事實性分數: {score_text}")
                return 0.5  # 預設中等分數
                
        except Exception as e:
            logger.error(f"計算事實性分數失敗: {str(e)}")
            return 0.5
    
    def run_complete_evaluation(self, pdf_path: str) -> Dict[str, Any]:
        """
        執行完整評估
        
        Args:
            pdf_path: PDF 檔案路徑
            
        Returns:
            完整評估結果
        """
        logger.info("開始執行完整 RAG 評估...")
        
        # 1. 創建評估資料集
        eval_dataset = self.create_synthetic_dataset(pdf_path)
        
        # 2. 執行各種評估方法
        baseline_results = self.baseline_evaluation(eval_dataset)
        naive_rag_results = self.naive_rag_evaluation(eval_dataset)
        
        # 3. 整合所有結果
        all_results = baseline_results + naive_rag_results
        
        # 4. 計算統計資訊
        statistics = self._calculate_statistics(all_results)
        
        # 5. 儲存結果
        self._save_results(all_results, statistics)
        
        return {
            "results": all_results,
            "statistics": statistics,
            "total_evaluations": len(all_results)
        }
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算統計資訊"""
        if not results:
            return {}
        
        # 按方法分組
        methods = {}
        for result in results:
            method = result["method"]
            if method not in methods:
                methods[method] = []
            methods[method].append(result)
        
        statistics = {}
        for method, method_results in methods.items():
            confidences = [r["confidence"] for r in method_results]
            factuality_scores = [r["factuality_score"] for r in method_results]
            
            statistics[method] = {
                "count": len(method_results),
                "avg_confidence": np.mean(confidences),
                "avg_factuality": np.mean(factuality_scores),
                "confidence_std": np.std(confidences),
                "factuality_std": np.std(factuality_scores),
                "min_confidence": np.min(confidences),
                "max_confidence": np.max(confidences),
                "min_factuality": np.min(factuality_scores),
                "max_factuality": np.max(factuality_scores)
            }
        
        return statistics
    
    def _save_results(self, results: List[Dict[str, Any]], statistics: Dict[str, Any]):
        """儲存評估結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 儲存詳細結果
        results_file = self.output_dir / f"evaluation_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 儲存統計資訊
        stats_file = self.output_dir / f"evaluation_statistics_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        
        # 儲存 CSV 格式
        df = pd.DataFrame(results)
        csv_file = self.output_dir / f"evaluation_results_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        logger.info(f"評估結果已儲存至: {self.output_dir}")
        logger.info(f"- 詳細結果: {results_file}")
        logger.info(f"- 統計資訊: {stats_file}")
        logger.info(f"- CSV 格式: {csv_file}")
    
    def generate_report(self, results: List[Dict[str, Any]], statistics: Dict[str, Any]) -> str:
        """生成評估報告"""
        report = []
        report.append("# RAG 評估報告")
        report.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"總評估數量: {len(results)}")
        report.append("")
        
        # 統計摘要
        report.append("## 統計摘要")
        for method, stats in statistics.items():
            report.append(f"### {method}")
            report.append(f"- 評估數量: {stats['count']}")
            report.append(f"- 平均信心值: {stats['avg_confidence']:.3f} ± {stats['confidence_std']:.3f}")
            report.append(f"- 平均事實性分數: {stats['avg_factuality']:.3f} ± {stats['factuality_std']:.3f}")
            report.append(f"- 信心值範圍: {stats['min_confidence']:.3f} - {stats['max_confidence']:.3f}")
            report.append(f"- 事實性分數範圍: {stats['min_factuality']:.3f} - {stats['max_factuality']:.3f}")
            report.append("")
        
        # 詳細結果摘要
        report.append("## 詳細結果摘要")
        for i, result in enumerate(results[:10]):  # 只顯示前10筆
            report.append(f"### 評估 {i+1}: {result['method']}")
            report.append(f"- 問題: {result['question']}")
            report.append(f"- 信心值: {result['confidence']:.3f}")
            report.append(f"- 事實性分數: {result['factuality_score']:.3f}")
            report.append("")
        
        if len(results) > 10:
            report.append(f"... 還有 {len(results) - 10} 筆結果")
        
        return "\n".join(report) 