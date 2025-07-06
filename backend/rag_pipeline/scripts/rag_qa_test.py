#!/usr/bin/env python3
"""
RAG 問答測試系統
整合音檔轉錄管線和前端問答系統
使用 PodWise 預設問題列表進行測試
"""

import os
import sys
import json
import logging
import asyncio
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
except ImportError:
    print("請安裝 pymongo: pip install pymongo")
    sys.exit(1)

try:
    from pymilvus import connections, Collection, utility
except ImportError:
    print("請安裝 pymilvus: pip install pymilvus")
    sys.exit(1)

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("請安裝 sentence-transformers: pip install sentence-transformers")
    sys.exit(1)

from audio_transcription_pipeline import AudioTranscriptionPipeline

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGQATestSystem:
    """RAG 問答測試系統"""
    
    def __init__(self, 
                 mongodb_uri: str = "mongodb://localhost:27017/",
                 mongodb_db: str = "podwise",
                 mongodb_collection: str = "podcast",
                 milvus_host: str = "localhost",
                 milvus_port: str = "19530",
                 embedding_model: str = "BAAI/bge-m3",
                 rag_service_url: str = "http://localhost:8004"):
        """
        初始化 RAG 問答測試系統
        
        Args:
            mongodb_uri: MongoDB 連接 URI
            mongodb_db: MongoDB 資料庫名稱
            mongodb_collection: MongoDB 集合名稱
            milvus_host: Milvus 主機
            milvus_port: Milvus 端口
            embedding_model: 嵌入模型名稱
            rag_service_url: RAG 服務 URL
        """
        self.mongodb_uri = mongodb_uri
        self.mongodb_db = mongodb_db
        self.mongodb_collection = mongodb_collection
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = embedding_model
        self.rag_service_url = rag_service_url
        
        # 初始化連接
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.milvus_connected = False
        
        # 初始化嵌入模型
        self.embedding_model_instance = None
        
        # 連接資料庫
        self.connect_databases()
        self.load_embedding_model()
        
        # 預設測試問題
        self.default_test_questions = [
            "什麼是人工智慧？",
            "如何提升工作效率？",
            "創業需要注意什麼？",
            "時間管理的方法有哪些？",
            "領導力的重要性是什麼？",
            "台灣半導體產業的發展如何？",
            "雲端運算有什麼優勢？",
            "區塊鏈技術有哪些應用？",
            "教育創新與學習有什麼關係？",
            "商業模式創新有哪些方式？",
            "如何進行投資理財？",
            "健康生活的重要性是什麼？",
            "科技對生活的影響有哪些？",
            "如何培養良好的學習習慣？",
            "企業管理的最佳實踐是什麼？"
        ]
    
    def connect_databases(self):
        """連接資料庫"""
        # 連接 MongoDB
        try:
            self.mongo_client = MongoClient(self.mongodb_uri)
            self.mongo_db = self.mongo_client[self.mongodb_db]
            self.mongo_collection = self.mongo_db[self.mongodb_collection]
            
            # 測試連接
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB 連接成功")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB 連接失敗: {e}")
            raise
        
        # 連接 Milvus
        try:
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            self.milvus_connected = True
            logger.info("✅ Milvus 連接成功")
            
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {e}")
            raise
    
    def load_embedding_model(self):
        """載入嵌入模型"""
        try:
            logger.info(f"🔧 載入嵌入模型: {self.embedding_model}")
            self.embedding_model_instance = SentenceTransformer(self.embedding_model)
            logger.info("✅ 嵌入模型載入成功")
            
        except Exception as e:
            logger.error(f"❌ 載入嵌入模型失敗: {e}")
            raise
    
    def load_test_questions(self, questions_file: str = "PodWise 預設問題列表.xlsx") -> List[str]:
        """
        載入測試問題
        
        Args:
            questions_file: 問題檔案路徑
            
        Returns:
            問題列表
        """
        questions = []
        
        try:
            # 嘗試讀取 Excel 檔案
            import pandas as pd
            
            file_path = Path(questions_file)
            if file_path.exists():
                df = pd.read_excel(file_path)
                logger.info(f"✅ 成功載入問題檔案: {questions_file}")
                
                # 根據實際欄位名稱調整
                if 'question' in df.columns:
                    questions = df['question'].dropna().tolist()
                elif '問題' in df.columns:
                    questions = df['問題'].dropna().tolist()
                elif 'content' in df.columns:
                    questions = df['content'].dropna().tolist()
                else:
                    # 如果沒有找到標準欄位，使用第一列
                    questions = df.iloc[:, 0].dropna().tolist()
                
                logger.info(f"📝 載入 {len(questions)} 個測試問題")
            else:
                logger.warning(f"⚠️ 問題檔案不存在: {questions_file}，使用預設問題")
                questions = self.default_test_questions
                
        except Exception as e:
            logger.warning(f"⚠️ 載入問題檔案失敗: {e}，使用預設問題")
            questions = self.default_test_questions
        
        return questions
    
    def search_similar_chunks(self, 
                            query_text: str, 
                            top_k: int = 5,
                            collection_name: str = "podcast_chunks") -> List[Dict]:
        """
        搜尋相似 chunks
        
        Args:
            query_text: 查詢文本
            top_k: 返回結果數量
            collection_name: 集合名稱
            
        Returns:
            相似 chunks 列表
        """
        if not self.milvus_connected:
            raise Exception("Milvus 未連接")
        
        collection = Collection(collection_name)
        collection.load()
        
        try:
            # 生成查詢向量
            query_embedding = self.embedding_model_instance.encode(
                query_text, 
                normalize_embeddings=True
            )
            
            # 搜尋參數
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # 執行搜尋
            results = collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "tags", "source_document_id", "chunk_index", "audio_file"]
            )
            
            # 格式化結果
            similar_chunks = []
            for hits in results:
                for hit in hits:
                    chunk_data = {
                        'chunk_id': hit.entity.get('chunk_id'),
                        'chunk_text': hit.entity.get('chunk_text'),
                        'tags': json.loads(hit.entity.get('tags', '[]')),
                        'source_document_id': hit.entity.get('source_document_id'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'audio_file': hit.entity.get('audio_file'),
                        'score': hit.score
                    }
                    similar_chunks.append(chunk_data)
            
            return similar_chunks
            
        finally:
            collection.release()
    
    async def send_rag_query(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """
        發送 RAG 查詢
        
        Args:
            query: 查詢文本
            user_id: 用戶 ID
            
        Returns:
            RAG 回應
        """
        try:
            # 準備請求資料
            payload = {
                "query": query,
                "user_id": user_id,
                "session_id": f"test_session_{int(datetime.now().timestamp())}",
                "category_filter": None,
                "use_advanced_features": True
            }
            
            # 發送請求
            response = requests.post(
                f"{self.rag_service_url}/api/v1/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "recommendations": data.get("recommendations", []),
                    "confidence": data.get("confidence", 0.0),
                    "source": "rag_service"
                }
            else:
                return {
                    "success": False,
                    "error": f"RAG 服務錯誤: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"RAG 查詢失敗: {str(e)}"
            }
    
    def generate_qa_prompt(self, question: str, context_chunks: List[Dict]) -> str:
        """
        生成問答提示詞
        
        Args:
            question: 問題
            context_chunks: 上下文 chunks
            
        Returns:
            提示詞
        """
        # 組合上下文
        context_text = ""
        for i, chunk in enumerate(context_chunks[:3]):  # 只使用前3個最相關的chunks
            context_text += f"上下文 {i+1}:\n{chunk['chunk_text']}\n\n"
        
        # 生成提示詞
        prompt = f"""
你是一個專業的 Podcast 內容分析助手。請根據以下上下文回答用戶的問題。

{context_text}

用戶問題: {question}

請提供：
1. 直接回答問題
2. 相關的 Podcast 推薦
3. 進一步的學習建議

回答要求：
- 使用繁體中文
- 回答要具體且有實用性
- 如果有相關的 Podcast 內容，請提及
- 保持專業且友善的語氣
"""
        
        return prompt
    
    def evaluate_response_quality(self, question: str, response: str, context_chunks: List[Dict]) -> Dict[str, Any]:
        """
        評估回應品質
        
        Args:
            question: 問題
            response: 回應
            context_chunks: 上下文 chunks
            
        Returns:
            評估結果
        """
        evaluation = {
            "relevance_score": 0.0,
            "completeness_score": 0.0,
            "clarity_score": 0.0,
            "context_usage_score": 0.0,
            "overall_score": 0.0,
            "feedback": []
        }
        
        try:
            # 1. 相關性評分 (基於問題關鍵字匹配)
            question_keywords = set(question.lower().split())
            response_keywords = set(response.lower().split())
            keyword_overlap = len(question_keywords.intersection(response_keywords))
            evaluation["relevance_score"] = min(keyword_overlap / max(len(question_keywords), 1), 1.0)
            
            # 2. 完整性評分 (基於回應長度和結構)
            response_length = len(response)
            if response_length > 100:
                evaluation["completeness_score"] = 0.8
            elif response_length > 50:
                evaluation["completeness_score"] = 0.6
            else:
                evaluation["completeness_score"] = 0.3
            
            # 3. 清晰度評分 (基於句子結構)
            sentences = response.split('。')
            if len(sentences) > 2:
                evaluation["clarity_score"] = 0.8
            elif len(sentences) > 1:
                evaluation["clarity_score"] = 0.6
            else:
                evaluation["clarity_score"] = 0.4
            
            # 4. 上下文使用評分
            if context_chunks:
                context_usage = any(
                    any(keyword in response.lower() for keyword in chunk.get('tags', []))
                    for chunk in context_chunks
                )
                evaluation["context_usage_score"] = 0.8 if context_usage else 0.3
            else:
                evaluation["context_usage_score"] = 0.0
            
            # 5. 整體評分
            evaluation["overall_score"] = (
                evaluation["relevance_score"] * 0.3 +
                evaluation["completeness_score"] * 0.25 +
                evaluation["clarity_score"] * 0.25 +
                evaluation["context_usage_score"] * 0.2
            )
            
            # 6. 反饋建議
            if evaluation["relevance_score"] < 0.5:
                evaluation["feedback"].append("回應與問題相關性較低")
            if evaluation["completeness_score"] < 0.5:
                evaluation["feedback"].append("回應內容不夠完整")
            if evaluation["clarity_score"] < 0.5:
                evaluation["feedback"].append("回應表達不夠清晰")
            if evaluation["context_usage_score"] < 0.5:
                evaluation["feedback"].append("未充分利用上下文資訊")
            
            if not evaluation["feedback"]:
                evaluation["feedback"].append("回應品質良好")
                
        except Exception as e:
            logger.error(f"評估回應品質失敗: {e}")
            evaluation["feedback"].append("評估過程發生錯誤")
        
        return evaluation
    
    def run_qa_test(self, questions: List[str] = None, max_questions: int = 10) -> Dict[str, Any]:
        """
        執行問答測試
        
        Args:
            questions: 測試問題列表
            max_questions: 最大測試問題數量
            
        Returns:
            測試結果
        """
        if not questions:
            questions = self.load_test_questions()
        
        # 限制問題數量
        if max_questions:
            questions = questions[:max_questions]
        
        logger.info(f"🧪 開始執行 RAG 問答測試，共 {len(questions)} 個問題")
        
        test_results = {
            "total_questions": len(questions),
            "successful_queries": 0,
            "failed_queries": 0,
            "average_confidence": 0.0,
            "average_quality_score": 0.0,
            "question_results": [],
            "performance_metrics": {
                "total_time": 0.0,
                "average_response_time": 0.0,
                "rag_service_availability": 0.0
            }
        }
        
        start_time = datetime.now()
        
        for i, question in enumerate(questions, 1):
            logger.info(f"🔍 測試問題 {i}/{len(questions)}: {question}")
            
            question_result = {
                "question": question,
                "question_index": i,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "response": "",
                "confidence": 0.0,
                "quality_evaluation": {},
                "context_chunks": [],
                "error": None,
                "response_time": 0.0
            }
            
            try:
                question_start_time = datetime.now()
                
                # 1. 向量搜尋相關 chunks
                context_chunks = self.search_similar_chunks(question, top_k=3)
                question_result["context_chunks"] = context_chunks
                
                # 2. 生成提示詞
                prompt = self.generate_qa_prompt(question, context_chunks)
                
                # 3. 發送 RAG 查詢
                rag_response = asyncio.run(self.send_rag_query(question))
                
                if rag_response["success"]:
                    question_result["success"] = True
                    question_result["response"] = rag_response["response"]
                    question_result["confidence"] = rag_response.get("confidence", 0.0)
                    
                    # 4. 評估回應品質
                    quality_evaluation = self.evaluate_response_quality(
                        question, rag_response["response"], context_chunks
                    )
                    question_result["quality_evaluation"] = quality_evaluation
                    
                    test_results["successful_queries"] += 1
                    test_results["average_confidence"] += rag_response.get("confidence", 0.0)
                    test_results["average_quality_score"] += quality_evaluation["overall_score"]
                    
                    logger.info(f"✅ 問題 {i} 測試成功，信心度: {rag_response.get('confidence', 0.0):.2f}")
                else:
                    question_result["error"] = rag_response.get("error", "未知錯誤")
                    test_results["failed_queries"] += 1
                    logger.error(f"❌ 問題 {i} 測試失敗: {rag_response.get('error', '未知錯誤')}")
                
                # 計算回應時間
                question_result["response_time"] = (datetime.now() - question_start_time).total_seconds()
                
            except Exception as e:
                question_result["error"] = str(e)
                test_results["failed_queries"] += 1
                logger.error(f"❌ 問題 {i} 測試異常: {e}")
            
            test_results["question_results"].append(question_result)
            
            # 避免過度負載
            time.sleep(1)
        
        # 計算統計資訊
        end_time = datetime.now()
        test_results["performance_metrics"]["total_time"] = (end_time - start_time).total_seconds()
        
        if test_results["successful_queries"] > 0:
            test_results["average_confidence"] /= test_results["successful_queries"]
            test_results["average_quality_score"] /= test_results["successful_queries"]
            test_results["performance_metrics"]["average_response_time"] = (
                test_results["performance_metrics"]["total_time"] / test_results["successful_queries"]
            )
        
        test_results["performance_metrics"]["rag_service_availability"] = (
            test_results["successful_queries"] / test_results["total_questions"]
        )
        
        return test_results
    
    def save_test_results(self, results: Dict[str, Any], output_file: str = "rag_qa_test_results.json"):
        """
        儲存測試結果
        
        Args:
            results: 測試結果
            output_file: 輸出檔案名稱
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 測試結果已儲存到: {output_file}")
        except Exception as e:
            logger.error(f"❌ 儲存測試結果失敗: {e}")
    
    def print_test_summary(self, results: Dict[str, Any]):
        """
        列印測試摘要
        
        Args:
            results: 測試結果
        """
        print("\n" + "="*60)
        print("🧪 RAG 問答測試摘要")
        print("="*60)
        
        print(f"📊 測試統計:")
        print(f"  總問題數: {results['total_questions']}")
        print(f"  成功查詢: {results['successful_queries']}")
        print(f"  失敗查詢: {results['failed_queries']}")
        print(f"  成功率: {results['successful_queries']/results['total_questions']*100:.1f}%")
        
        print(f"\n📈 品質指標:")
        print(f"  平均信心度: {results['average_confidence']:.3f}")
        print(f"  平均品質分數: {results['average_quality_score']:.3f}")
        
        print(f"\n⏱️ 效能指標:")
        print(f"  總測試時間: {results['performance_metrics']['total_time']:.1f} 秒")
        print(f"  平均回應時間: {results['performance_metrics']['average_response_time']:.1f} 秒")
        print(f"  RAG 服務可用性: {results['performance_metrics']['rag_service_availability']*100:.1f}%")
        
        print(f"\n🔍 詳細結果:")
        for i, result in enumerate(results['question_results'][:5]):  # 只顯示前5個
            status = "✅" if result['success'] else "❌"
            confidence = result.get('confidence', 0.0)
            quality_score = result.get('quality_evaluation', {}).get('overall_score', 0.0)
            print(f"  {status} 問題 {i+1}: 信心度={confidence:.3f}, 品質分數={quality_score:.3f}")
        
        if len(results['question_results']) > 5:
            print(f"  ... 還有 {len(results['question_results']) - 5} 個問題結果")
        
        print("="*60)
    
    def close_connections(self):
        """關閉連接"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB 連接已關閉")
        
        if self.milvus_connected:
            connections.disconnect("default")
            logger.info("Milvus 連接已關閉")

def main():
    """主函數"""
    # 初始化測試系統
    test_system = RAGQATestSystem(
        mongodb_uri="mongodb://localhost:27017/",
        mongodb_db="podwise",
        mongodb_collection="podcast",
        milvus_host="localhost",
        milvus_port="19530",
        embedding_model="BAAI/bge-m3",
        rag_service_url="http://localhost:8004"
    )
    
    try:
        # 執行問答測試
        print("🧪 開始 RAG 問答測試...")
        results = test_system.run_qa_test(max_questions=5)  # 先測試5個問題
        
        # 列印測試摘要
        test_system.print_test_summary(results)
        
        # 儲存測試結果
        test_system.save_test_results(results)
        
        # 顯示詳細結果
        print("\n📋 詳細測試結果:")
        for i, result in enumerate(results['question_results'], 1):
            print(f"\n問題 {i}: {result['question']}")
            if result['success']:
                print(f"回應: {result['response'][:200]}...")
                print(f"信心度: {result['confidence']:.3f}")
                print(f"品質分數: {result['quality_evaluation']['overall_score']:.3f}")
                if result['quality_evaluation']['feedback']:
                    print(f"反饋: {', '.join(result['quality_evaluation']['feedback'])}")
            else:
                print(f"錯誤: {result['error']}")
        
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
    
    finally:
        test_system.close_connections()

if __name__ == "__main__":
    main() 