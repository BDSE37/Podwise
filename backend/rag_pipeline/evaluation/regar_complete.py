"""
完整的 RAG 評估腳本
基於 610_ihower_LLM_workshop_RAG_evaluation.ipynb 的完整功能
包含：
1. 合成數據生成 (Synthetic Data Generation)
2. Baseline 評估 (No RAG)
3. Naive RAG 評估
4. Ragas 指標評估
5. Braintrust 風格的評估
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 導入必要的庫
try:
    from pymilvus import connections, Collection
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    from pydantic import Field, BaseModel
    import tiktoken
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    print(f"缺少依賴庫: {e}")
    print("請安裝: pip install pymilvus sentence-transformers transformers pydantic tiktoken langchain-text-splitters")
    sys.exit(1)

# 配置
CSV_PATH = "../../rag_pipeline/scripts/csv/default_QA_standard.csv"
LLM_NAME = "../../../Qwen2.5-Taiwan-7B-Instruct"
MILVUS_HOST = "192.168.32.86"
MILVUS_PORT = "19530"
COLLECTION_NAME = "podcast_chunks"
EMBEDDING_MODEL = "BAAI/bge-m3"

# 創建輸出目錄
OUTPUT_DIR = "runs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Pydantic 模型定義
class QAPair(BaseModel):
    reference: str = Field(..., description="The exact text segment from the original context that this Q&A is based on")
    question: str = Field(description="A single question about the content")
    answer: str = Field(..., description="Answer")

class QAPairs(BaseModel):
    pairs: List[QAPair] = Field(..., description="List of question/answer pairs")

class QueryResult(BaseModel):
    relevant_quotes: List[str]
    answer: str
    following_questions: List[str]

class RAGEvaluator:
    def __init__(self):
        self.embedder = None
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.collection = None
        self.text_splitter = None
        self.tokenizer_encoding = None
        
    def setup_components(self):
        """初始化所有組件"""
        print("=== 初始化組件 ===")
        
        # 1. 連接 Milvus
        print("連接 Milvus...")
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, alias="default")
        self.collection = Collection(COLLECTION_NAME)
        self.collection.load(partition_names=["_default"])
        print(f"Milvus 連接成功，集合: {self.collection.name}")
        
        # 2. 初始化 Embedding 模型
        print("載入 Embedding 模型...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        print("Embedding 模型載入成功")
        
        # 3. 初始化 LLM
        print("載入 LLM 模型...")
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_NAME, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            LLM_NAME, trust_remote_code=True, device_map="auto"
        )
        self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer,
                                 max_new_tokens=512, temperature=0.1, do_sample=False)
        print("LLM 模型載入成功")
        
        # 4. 初始化文本分割器
        print("初始化文本分割器...")
        try:
            self.tokenizer_encoding = tiktoken.get_encoding("cl100k_base")
        except ValueError:
            try:
                self.tokenizer_encoding = tiktoken.get_encoding("r50k_base")
            except ValueError:
                print("警告: 無法載入 tiktoken 編碼，使用簡單字符計數")
                self.tokenizer_encoding = None
        
        if self.tokenizer_encoding:
            length_function = lambda text: len(self.tokenizer_encoding.encode(text))
        else:
            length_function = lambda text: len(text)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            length_function=length_function,
            chunk_size=800, chunk_overlap=200,
            separators=["\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""]
        )
        print("文本分割器初始化成功")
        
        print("=== 所有組件初始化完成 ===")
    
    def get_embeddings(self, text: str) -> List[float]:
        """獲取文本的 embedding"""
        return self.embedder.encode(text, normalize_embeddings=True).tolist()
    
    def generate_synthetic_data(self, content: str) -> List[QAPair]:
        """生成合成數據 - 基於 notebook 的 produce_questions 函數"""
        prompt = f"""請從以下文本生成2個問答對，專注於投資和個人理財主題。
對於每個問答對，提供一個問題、一個獨特的答案，並包含原始上下文中此問答基於的確切文本段落。

重要要求：
1. 僅專注於投資、財務規劃、財富管理、股票市場、退休規劃、稅務優化或其他個人理財相關主題。
2. 所有問題和答案必須使用繁體中文（台灣）。
3. 使用台灣金融業常用的術語和表達方式。
4. 如果上下文不包含金融相關信息，提取最相關的方面，可應用於個人理財或投資決策。
5. 對於每個問答對，包含原始上下文中包含用於問答的信息的確切文本。這應該從輸入上下文中逐字複製。

上下文: {content}

請以繁體中文回答，格式如下：
問題1: [問題]
答案1: [答案]
參考文本1: [確切文本段落]

問題2: [問題]
答案2: [答案]
參考文本2: [確切文本段落]
"""
        
        try:
            result = self.generator(prompt, max_new_tokens=1024)
            generated_text = result[0]['generated_text'][len(prompt):]
            
            # 解析生成的文本
            pairs = []
            lines = generated_text.split('\n')
            current_question = ""
            current_answer = ""
            current_reference = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('問題'):
                    if current_question and current_answer and current_reference:
                        pairs.append(QAPair(
                            question=current_question,
                            answer=current_answer,
                            reference=current_reference
                        ))
                    current_question = line.split(':', 1)[1].strip() if ':' in line else line
                elif line.startswith('答案'):
                    current_answer = line.split(':', 1)[1].strip() if ':' in line else line
                elif line.startswith('參考文本'):
                    current_reference = line.split(':', 1)[1].strip() if ':' in line else line
            
            # 添加最後一對
            if current_question and current_answer and current_reference:
                pairs.append(QAPair(
                    question=current_question,
                    answer=current_answer,
                    reference=current_reference
                ))
            
            return pairs[:2]  # 只返回前2對
            
        except Exception as e:
            print(f"生成合成數據時出錯: {e}")
            return []
    
    def baseline_qa(self, question: str) -> str:
        """Baseline: 無 RAG 的純 LLM 回答 - 基於 notebook 的 simple_qa 函數"""
        prompt = f"請回答以下問題：{question}"
        try:
            result = self.generator(prompt, max_new_tokens=256)
            return result[0]['generated_text'][len(prompt):].strip()
        except Exception as e:
            print(f"Baseline QA 出錯: {e}")
            return "無法生成回答"
    
    def naive_rag_qa(self, question: str) -> str:
        """Naive RAG: 基本的 RAG 系統 - 基於 notebook 的 ask_with_rag 函數"""
        try:
            # 檢索相關文檔
            results = self.collection.query(
                expr="",
                data=[self.get_embeddings(question)],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"nprobe": 10}},
                limit=10,
                output_fields=["chunk_text", "episode_title", "podcast_name", "category"]
            )
            
            documents = [hit.get('chunk_text') for hit in results[0]]
            context = '\n'.join(f'* {doc}' for doc in documents)
            
            # 生成回答 - 使用 notebook 中的 prompt
            prompt = f"""我將提供您一個文檔，然後詢問您有關它的問題。請按照以下步驟回答：

<document>
{context}
</document>

問題: {question}

請用繁體中文回答，格式如下：

1. 首先，識別文檔中最相關的引用來幫助回答問題並列出它們。每個引用應該相對較短。
   如果沒有相關引用，請寫"沒有相關引用"。

2. 然後，使用這些引用中的事實回答問題，不要在您的答案中直接引用內容。

3. 最後，根據原始問題和文檔內容提供3個相關的後續問題，以幫助進一步探索主題。

如果文檔不包含足夠的信息來回答問題，請在答案字段中說明這一點，但仍提供任何相關引用（如果有的話）和可能的後續問題。
"""
            
            result = self.generator(prompt, max_new_tokens=512)
            return result[0]['generated_text'][len(prompt):].strip()
            
        except Exception as e:
            print(f"Naive RAG QA 出錯: {e}")
            return "無法生成回答"
    
    def fetch_top_k_relevant_sections(self, question: str) -> List[str]:
        """檢索相關文檔段落 - 基於 notebook 的 fetch_top_k_relevant_sections 函數"""
        try:
            results = self.collection.query(
                expr="",
                data=[self.get_embeddings(question)],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"nprobe": 10}},
                limit=10,
                output_fields=["chunk_text", "episode_title", "podcast_name", "category"]
            )
            return [hit.get('chunk_text') for hit in results[0]]
        except Exception as e:
            print(f"檢索文檔出錯: {e}")
            return []
    
    def generate_answer_from_docs(self, question: str, retrieved_content: List[str]) -> Dict[str, Any]:
        """從檢索的文檔生成回答 - 基於 notebook 的 generate_answer_from_docs 函數"""
        try:
            context = '\n'.join(f'* {doc}' for doc in retrieved_content)
            
            # 使用 notebook 中的 prompt
            prompt = f"""我將提供您一個文檔，然後詢問您有關它的問題。請按照以下步驟回答：

<document>
{context}
</document>

問題: {question}

請用繁體中文回答，格式如下：

1. 首先，識別文檔中最相關的引用來幫助回答問題並列出它們。每個引用應該相對較短。
   如果沒有相關引用，請寫"沒有相關引用"。

2. 然後，使用這些引用中的事實回答問題，不要在您的答案中直接引用內容。

3. 最後，根據原始問題和文檔內容提供3個相關的後續問題，以幫助進一步探索主題。

如果文檔不包含足夠的信息來回答問題，請在答案字段中說明這一點，但仍提供任何相關引用（如果有的話）和可能的後續問題。
"""
            
            result = self.generator(prompt, max_new_tokens=512)
            answer = result[0]['generated_text'][len(prompt):].strip()
            
            return {
                "answer": answer,
                "relevant_quotes": [],  # 簡化處理
                "following_questions": []  # 簡化處理
            }
            
        except Exception as e:
            print(f"從文檔生成回答出錯: {e}")
            return {
                "answer": "無法生成回答",
                "relevant_quotes": [],
                "following_questions": []
            }
    
    def generate_answer_e2e(self, question: str) -> Dict[str, Any]:
        """端到端生成回答（用於 Ragas 評估）- 基於 notebook 的 generate_answer_e2e 函數"""
        retrieved_content = self.fetch_top_k_relevant_sections(question)
        result = self.generate_answer_from_docs(question, retrieved_content)
        return {
            "answer": result["answer"],
            "retrieved_docs": retrieved_content
        }
    
    # Ragas 風格的評估指標
    def evaluate_context_recall(self, answer: str, retrieved_docs: List[str], expected: str) -> float:
        """評估上下文召回率 - 基於 Ragas ContextRecall"""
        try:
            if not retrieved_docs:
                return 0.0
            
            # 計算檢索的文檔與期望答案的相關性
            expected_embedding = self.get_embeddings(expected)
            expected_embedding = np.array(expected_embedding)
            
            total_similarity = 0.0
            for doc in retrieved_docs:
                doc_embedding = self.get_embeddings(doc)
                doc_embedding = np.array(doc_embedding)
                
                similarity = np.dot(expected_embedding, doc_embedding) / (
                    np.linalg.norm(expected_embedding) * np.linalg.norm(doc_embedding)
                )
                total_similarity += similarity
            
            return float(total_similarity / len(retrieved_docs))
        except Exception as e:
            print(f"計算上下文召回率出錯: {e}")
            return 0.0
    
    def evaluate_context_precision(self, answer: str, retrieved_docs: List[str], question: str) -> float:
        """評估上下文精確度 - 基於 Ragas ContextPrecision"""
        try:
            if not retrieved_docs:
                return 0.0
            
            # 計算檢索的文檔與問題的相關性
            question_embedding = self.get_embeddings(question)
            question_embedding = np.array(question_embedding)
            
            total_similarity = 0.0
            for doc in retrieved_docs:
                doc_embedding = self.get_embeddings(doc)
                doc_embedding = np.array(doc_embedding)
                
                similarity = np.dot(question_embedding, doc_embedding) / (
                    np.linalg.norm(question_embedding) * np.linalg.norm(doc_embedding)
                )
                total_similarity += similarity
            
            return float(total_similarity / len(retrieved_docs))
        except Exception as e:
            print(f"計算上下文精確度出錯: {e}")
            return 0.0
    
    def evaluate_faithfulness(self, answer: str, retrieved_docs: List[str]) -> float:
        """評估忠實度 - 基於 Ragas Faithfulness"""
        try:
            if not retrieved_docs:
                return 0.0
            
            # 計算答案與檢索文檔的一致性
            answer_embedding = self.get_embeddings(answer)
            answer_embedding = np.array(answer_embedding)
            
            total_similarity = 0.0
            for doc in retrieved_docs:
                doc_embedding = self.get_embeddings(doc)
                doc_embedding = np.array(doc_embedding)
                
                similarity = np.dot(answer_embedding, doc_embedding) / (
                    np.linalg.norm(answer_embedding) * np.linalg.norm(doc_embedding)
                )
                total_similarity += similarity
            
            return float(total_similarity / len(retrieved_docs))
        except Exception as e:
            print(f"計算忠實度出錯: {e}")
            return 0.0
    
    def evaluate_answer_correctness(self, answer: str, expected: str) -> float:
        """評估答案正確性 - 基於 Ragas AnswerCorrectness"""
        try:
            # 計算答案與期望答案的語義相似度
            answer_embedding = self.get_embeddings(answer)
            expected_embedding = self.get_embeddings(expected)
            
            answer_embedding = np.array(answer_embedding)
            expected_embedding = np.array(expected_embedding)
            
            similarity = np.dot(answer_embedding, expected_embedding) / (
                np.linalg.norm(answer_embedding) * np.linalg.norm(expected_embedding)
            )
            return float(similarity)
        except Exception as e:
            print(f"計算答案正確性出錯: {e}")
            return 0.0
    
    # 額外的評估指標
    def evaluate_answer_length(self, answer: str) -> Dict[str, float]:
        """評估答案長度"""
        words = len(answer.split())
        chars = len(answer)
        return {
            "word_count": words,
            "char_count": chars,
            "avg_word_length": chars / words if words > 0 else 0
        }
    
    def evaluate_semantic_similarity(self, answer: str, expected: str) -> float:
        """評估語義相似度"""
        try:
            answer_embedding = self.get_embeddings(answer)
            expected_embedding = self.get_embeddings(expected)
            
            answer_embedding = np.array(answer_embedding)
            expected_embedding = np.array(expected_embedding)
            
            similarity = np.dot(answer_embedding, expected_embedding) / (
                np.linalg.norm(answer_embedding) * np.linalg.norm(expected_embedding)
            )
            return float(similarity)
        except Exception as e:
            print(f"計算語義相似度出錯: {e}")
            return 0.0
    
    def run_complete_evaluation(self):
        """運行完整評估 - 包含所有 notebook 中的評估方法"""
        print("=== 開始完整 RAG 評估 ===")
        
        # 讀取 QA 數據
        try:
            qa_df = pd.read_csv(CSV_PATH)
            print(f"讀取 QA 數據成功，共 {len(qa_df)} 行")
        except Exception as e:
            print(f"讀取 CSV 失敗: {e}")
            return
        
        # 準備評估數據
        eval_data = []
        for _, row in qa_df.iterrows():
            eval_data.append({
                "question": row['question'],
                "expected": row['answer'],
                "category": row.get('category', ''),
                "tag": row.get('tag', ''),
                "user": row.get('user', ''),
                "advice": row.get('advice', '')
            })
        
        print(f"準備評估數據，共 {len(eval_data)} 個問題")
        
        # 運行評估
        results = {
            "baseline": [],
            "naive_rag": [],
            "ragas_style": [],
            "synthetic_data": [],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(eval_data),
                "model": LLM_NAME,
                "embedding_model": EMBEDDING_MODEL,
                "evaluation_methods": ["Baseline", "Naive RAG", "Ragas Style", "Synthetic Data"]
            }
        }
        
        for i, data in enumerate(eval_data):
            print(f"處理問題 {i+1}/{len(eval_data)}: {data['question'][:50]}...")
            
            # 1. Baseline 評估 (No RAG)
            baseline_answer = self.baseline_qa(data['question'])
            baseline_metrics = self.evaluate_answer_length(baseline_answer)
            baseline_similarity = self.evaluate_semantic_similarity(baseline_answer, data['expected'])
            
            results["baseline"].append({
                "question": data['question'],
                "expected": data['expected'],
                "answer": baseline_answer,
                "metrics": baseline_metrics,
                "semantic_similarity": baseline_similarity,
                "category": data['category'],
                "tag": data['tag']
            })
            
            # 2. Naive RAG 評估
            naive_answer = self.naive_rag_qa(data['question'])
            naive_metrics = self.evaluate_answer_length(naive_answer)
            naive_similarity = self.evaluate_semantic_similarity(naive_answer, data['expected'])
            
            results["naive_rag"].append({
                "question": data['question'],
                "expected": data['expected'],
                "answer": naive_answer,
                "metrics": naive_metrics,
                "semantic_similarity": naive_similarity,
                "category": data['category'],
                "tag": data['tag']
            })
            
            # 3. Ragas 風格評估
            ragas_result = self.generate_answer_e2e(data['question'])
            ragas_metrics = self.evaluate_answer_length(ragas_result["answer"])
            ragas_similarity = self.evaluate_semantic_similarity(ragas_result["answer"], data['expected'])
            context_recall = self.evaluate_context_recall(ragas_result["answer"], ragas_result["retrieved_docs"], data['expected'])
            context_precision = self.evaluate_context_precision(ragas_result["answer"], ragas_result["retrieved_docs"], data['question'])
            faithfulness = self.evaluate_faithfulness(ragas_result["answer"], ragas_result["retrieved_docs"])
            answer_correctness = self.evaluate_answer_correctness(ragas_result["answer"], data['expected'])
            
            results["ragas_style"].append({
                "question": data['question'],
                "expected": data['expected'],
                "answer": ragas_result["answer"],
                "retrieved_docs": ragas_result["retrieved_docs"],
                "metrics": ragas_metrics,
                "semantic_similarity": ragas_similarity,
                "context_recall": context_recall,
                "context_precision": context_precision,
                "faithfulness": faithfulness,
                "answer_correctness": answer_correctness,
                "category": data['category'],
                "tag": data['tag']
            })
            
            # 4. 合成數據生成（可選）
            if i < 5:  # 只對前5個問題生成合成數據
                try:
                    synthetic_pairs = self.generate_synthetic_data(data['question'])
                    for pair in synthetic_pairs:
                        results["synthetic_data"].append({
                            "original_question": data['question'],
                            "synthetic_question": pair.question,
                            "synthetic_answer": pair.answer,
                            "reference": pair.reference,
                            "category": data['category'],
                            "tag": data['tag']
                        })
                except Exception as e:
                    print(f"生成合成數據出錯: {e}")
        
        # 計算統計結果
        self.calculate_comprehensive_statistics(results)
        
        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"complete_rag_evaluation_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 完整評估完成 ===")
        print(f"結果已保存到: {output_file}")
        
        # 打印詳細摘要
        self.print_comprehensive_summary(results)
    
    def calculate_comprehensive_statistics(self, results: Dict[str, Any]):
        """計算綜合統計結果"""
        for method in ["baseline", "naive_rag", "ragas_style"]:
            if method not in results:
                continue
            
            data = results[method]
            
            # 基本指標
            avg_similarity = np.mean([item.get('semantic_similarity', 0) for item in data])
            avg_word_count = np.mean([item.get('metrics', {}).get('word_count', 0) for item in data])
            avg_char_count = np.mean([item.get('metrics', {}).get('char_count', 0) for item in data])
            
            stats = {
                "avg_semantic_similarity": avg_similarity,
                "avg_word_count": avg_word_count,
                "avg_char_count": avg_char_count,
                "total_questions": len(data)
            }
            
            # Ragas 風格評估的額外指標
            if method == "ragas_style":
                avg_context_recall = np.mean([item.get('context_recall', 0) for item in data])
                avg_context_precision = np.mean([item.get('context_precision', 0) for item in data])
                avg_faithfulness = np.mean([item.get('faithfulness', 0) for item in data])
                avg_answer_correctness = np.mean([item.get('answer_correctness', 0) for item in data])
                
                stats.update({
                    "avg_context_recall": avg_context_recall,
                    "avg_context_precision": avg_context_precision,
                    "avg_faithfulness": avg_faithfulness,
                    "avg_answer_correctness": avg_answer_correctness
                })
            
            results[f"{method}_stats"] = stats
        
        # 合成數據統計
        if "synthetic_data" in results:
            results["synthetic_data_stats"] = {
                "total_synthetic_pairs": len(results["synthetic_data"])
            }
    
    def print_comprehensive_summary(self, results: Dict[str, Any]):
        """打印綜合評估摘要"""
        print("\n" + "="*80)
        print("完整 RAG 評估結果摘要")
        print("="*80)
        
        for method in ["baseline", "naive_rag", "ragas_style"]:
            if f"{method}_stats" not in results:
                continue
            
            stats = results[f"{method}_stats"]
            print(f"\n{method.upper()} 評估結果:")
            print(f"  問題數量: {stats['total_questions']}")
            print(f"  平均語義相似度: {stats['avg_semantic_similarity']:.4f}")
            print(f"  平均字數: {stats['avg_word_count']:.1f}")
            print(f"  平均字符數: {stats['avg_char_count']:.1f}")
            
            if method == "ragas_style":
                print(f"  平均上下文召回率: {stats['avg_context_recall']:.4f}")
                print(f"  平均上下文精確度: {stats['avg_context_precision']:.4f}")
                print(f"  平均忠實度: {stats['avg_faithfulness']:.4f}")
                print(f"  平均答案正確性: {stats['avg_answer_correctness']:.4f}")
        
        # 合成數據摘要
        if "synthetic_data_stats" in results:
            print(f"\n合成數據生成結果:")
            print(f"  生成問答對數量: {results['synthetic_data_stats']['total_synthetic_pairs']}")
        
        print("\n" + "="*80)

def main():
    """主函數"""
    print("=== 完整 RAG 評估系統啟動 ===")
    
    # 創建評估器
    evaluator = RAGEvaluator()
    
    try:
        # 初始化組件
        evaluator.setup_components()
        
        # 運行完整評估
        evaluator.run_complete_evaluation()
        
    except Exception as e:
        print(f"評估過程中出錯: {e}")
        traceback.print_exc()
    
    print("=== 完整評估系統結束 ===")

if __name__ == "__main__":
    main() 