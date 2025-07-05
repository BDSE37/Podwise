#!/usr/bin/env python3
"""
增強型向量搜尋工具
整合職缺搜尋和一般向量搜尋功能，提供統一的搜尋介面
支援 Milvus 向量資料庫和智能查詢優化
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
import json
import numpy as np
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVectorSearchTool:
    """增強型向量搜尋工具類別"""
    
    def __init__(
        self,
        collection_name: str = "podcast_embeddings",
        host: str = "milvus",
        port: int = 19530,
        dimension: int = 1536,
        search_type: str = "general"  # "general" 或 "job"
    ):
        """
        初始化增強型向量搜尋工具
        
        Args:
            collection_name: 集合名稱
            host: Milvus 主機
            port: Milvus 端口
            dimension: 向量維度
            search_type: 搜尋類型 ("general" 或 "job")
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.dimension = dimension
        self.search_type = search_type
        self.collection = None
        
        # 連接到 Milvus
        self._connect_to_milvus()
        
        # 初始化 LLM（如果可用）
        self.llm = None
        try:
            self.llm = OpenAI(temperature=0.1)
            logger.info("LLM 初始化成功")
        except Exception as e:
            logger.warning(f"LLM 初始化失敗: {e}")
        
        # 載入職缺元數據（如果是職缺搜尋）
        self.metadata = {}
        if search_type == "job":
            self._load_job_metadata()
        
        # 設定查詢提示樣板
        self._setup_prompts()
        
        logger.info(f"增強型向量搜尋工具初始化完成: {host}:{port}, 類型: {search_type}")
    
    def _connect_to_milvus(self):
        """連接到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info("成功連接到 Milvus")
            
            # 檢查集合是否存在
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"載入集合: {self.collection_name}")
            else:
                logger.warning(f"集合不存在: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"連接到 Milvus 失敗: {str(e)}")
            raise
    
    def _load_job_metadata(self):
        """載入職缺元數據"""
        try:
            metadata_path = "../data_processing_system/data/processed/vector/jobs_metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"載入職缺元數據: {len(self.metadata)} 筆記錄")
            else:
                logger.warning(f"找不到職缺元數據檔案: {metadata_path}")
        except Exception as e:
            logger.error(f"載入職缺元數據時出錯: {e}")
    
    def _setup_prompts(self):
        """設定查詢提示樣板"""
        if self.search_type == "job":
            # 職缺搜尋提示
            self.query_prompt = PromptTemplate(
                input_variables=["query"],
                template="""
                將以下用戶查詢轉化為適合向量數據庫搜索的查詢文本:
                查詢: {query}
                
                轉換後的查詢:
                """
            )
            
            self.answer_prompt = PromptTemplate(
                input_variables=["query", "results"],
                template="""
                你是一位專業的職缺顧問，根據以下職缺資訊回答用戶的問題。
                
                用戶問題: {query}
                
                相關職缺資訊:
                {results}
                
                請基於這些職缺資訊，針對用戶問題提供詳細且專業的回答。
                使用繁體中文回覆，並確保回覆中客觀反映實際的職缺狀況。
                如有按件計酬等特殊薪資類型，請特別說明。
                """
            )
        else:
            # 一般搜尋提示
            self.query_prompt = PromptTemplate(
                input_variables=["query"],
                template="""
                將以下用戶查詢轉化為適合向量數據庫搜索的查詢文本:
                查詢: {query}
                
                轉換後的查詢:
                """
            )
            
            self.answer_prompt = PromptTemplate(
                input_variables=["query", "results"],
                template="""
                根據以下相關內容回答用戶的問題。
                
                用戶問題: {query}
                
                相關內容:
                {results}
                
                請基於這些內容，針對用戶問題提供準確且有用的回答。
                使用繁體中文回覆。
                """
            )
    
    def _get_embedding(self, query: str) -> List[float]:
        """獲取查詢文本的嵌入向量"""
        try:
            from langchain.embeddings import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings()
            return embeddings.embed_query(query)
        except Exception as e:
            logger.error(f"獲取嵌入向量失敗: {e}")
            # 返回零向量作為備用
            return [0.0] * self.dimension
    
    def _format_job_result(self, job_id: str, score: float) -> str:
        """格式化職缺搜尋結果"""
        if not self.metadata or job_id not in self.metadata:
            return f"職缺 ID: {job_id} (無詳細資訊)"
        
        job = self.metadata[job_id]
        
        # 格式化薪資顯示
        salary_display = ""
        if job.get("is_commission", False):
            salary_display = "按件計酬 (無底薪保障)"
        else:
            salary_type = job.get("salary_type", "月薪")
            salary_min = job.get("salary_min", 0)
            salary_max = job.get("salary_max", 0)
            if salary_min and salary_max:
                salary_display = f"{salary_type} {salary_min:,} - {salary_max:,} 元"
            elif salary_min:
                salary_display = f"{salary_type} {salary_min:,} 元以上"
            else:
                salary_display = "待遇面議"
        
        # 組織職缺資訊
        result = f"""
職缺標題: {job.get('job_title', '未提供')}
公司名稱: {job.get('company_name', '未提供')}
工作地點: {job.get('location', '未提供')}
薪資待遇: {salary_display}
類別: {job.get('primary_category', '')} / {job.get('job_category', '')}
相關度: {score:.2f}
"""
        
        # 添加技能要求 (如果有)
        skills = job.get('skills', [])
        if skills and len(skills) > 0:
            result += f"所需技能: {', '.join(skills)}\n"
        
        # 添加工作描述片段 (如果有)
        job_description = job.get('job_description', '')
        if job_description:
            # 截取前 100 個字符作為摘要
            result += f"工作描述: {job_description[:100]}...\n"
        
        return result
    
    def _format_general_result(self, hit) -> str:
        """格式化一般搜尋結果"""
        return f"""
內容: {hit.entity.get('content', '')[:200]}...
來源: {hit.entity.get('source', '')}
相關度: {hit.score:.2f}
"""
    
    def search_similar_content(
        self,
        query_vector: List[float],
        top_k: int = 5,
        search_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜尋相似內容
        
        Args:
            query_vector: 查詢向量
            top_k: 返回結果數量
            search_params: 搜尋參數
            
        Returns:
            List[Dict[str, Any]]: 搜尋結果
        """
        try:
            if self.collection is None:
                raise ValueError("集合未載入")
            
            # 預設搜尋參數
            if search_params is None:
                search_params = {
                    "metric_type": "COSINE",
                    "params": {"nprobe": 10}
                }
            
            # 設定輸出欄位
            if self.search_type == "job":
                output_fields = ["job_title", "company_name", "salary_min", "salary_type", "is_commission"]
            else:
                output_fields = ["content", "metadata", "source"]
            
            # 執行搜尋
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=output_fields
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    if self.search_type == "job":
                        result_text = self._format_job_result(hit.id, hit.score)
                    else:
                        result_text = self._format_general_result(hit)
                    
                    formatted_results.append({
                        "id": hit.id,
                        "score": hit.score,
                        "content": result_text,
                        "metadata": hit.entity.get("metadata", {}),
                        "source": hit.entity.get("source", "")
                    })
            
            logger.info(f"搜尋完成，找到 {len(formatted_results)} 個結果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {str(e)}")
            return []
    
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行智能搜尋
        
        Args:
            query: 查詢文本
            top_k: 返回結果數量
            filters: 過濾條件
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        try:
            # 優化查詢文本
            enhanced_query = query
            if self.llm:
                try:
                    enhanced_query = self.llm(self.query_prompt.format(query=query))
                    logger.info(f"優化後查詢文本: {enhanced_query}")
                except Exception as e:
                    logger.warning(f"查詢優化失敗，使用原始查詢: {e}")
            
            # 獲取查詢向量
            query_vector = self._get_embedding(enhanced_query)
            
            # 準備搜尋參數
            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64}
            }
            
            # 執行向量搜尋
            hits = self.search_similar_content(query_vector, top_k, search_params)
            
            # 生成摘要回答
            answer = query  # 預設使用原始查詢
            if self.llm and hits:
                try:
                    formatted_results = "\n".join([hit["content"] for hit in hits])
                    answer = self.llm(self.answer_prompt.format(
                        query=query,
                        results=formatted_results
                    ))
                except Exception as e:
                    logger.warning(f"生成回答失敗: {e}")
            
            return {
                "query": query,
                "answer": answer,
                "hits": hits,
                "enhanced_query": enhanced_query
            }
        
        except Exception as e:
            logger.error(f"搜尋時出錯: {e}")
            return {
                "query": query,
                "answer": f"搜尋處理過程中發生錯誤: {str(e)}",
                "hits": [],
                "enhanced_query": query
            }
    
    def insert_vectors(
        self,
        vectors: List[List[float]],
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        sources: List[str]
    ) -> bool:
        """
        插入向量資料
        
        Args:
            vectors: 向量列表
            contents: 內容列表
            metadatas: 元數據列表
            sources: 來源列表
            
        Returns:
            bool: 是否成功
        """
        try:
            if self.collection is None:
                raise ValueError("集合未載入")
            
            # 準備插入資料
            insert_data = [
                vectors,
                contents,
                metadatas,
                sources
            ]
            
            # 插入資料
            self.collection.insert(insert_data)
            self.collection.flush()
            
            logger.info(f"成功插入 {len(vectors)} 個向量")
            return True
            
        except Exception as e:
            logger.error(f"插入向量失敗: {str(e)}")
            return False
    
    def delete_vectors(self, ids: List[int]) -> bool:
        """
        刪除向量資料
        
        Args:
            ids: 要刪除的 ID 列表
            
        Returns:
            bool: 是否成功
        """
        try:
            if self.collection is None:
                raise ValueError("集合未載入")
            
            # 刪除資料
            self.collection.delete(f"id in {ids}")
            
            logger.info(f"成功刪除 {len(ids)} 個向量")
            return True
            
        except Exception as e:
            logger.error(f"刪除向量失敗: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        獲取集合統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        try:
            if self.collection is None:
                return {"error": "集合未載入"}
            
            stats = {
                "collection_name": self.collection_name,
                "num_entities": self.collection.num_entities,
                "dimension": self.dimension,
                "search_type": self.search_type
            }
            
            if self.search_type == "job":
                stats["job_metadata_count"] = len(self.metadata)
            
            return stats
            
        except Exception as e:
            logger.error(f"獲取集合統計失敗: {str(e)}")
            return {"error": f"獲取集合統計失敗: {str(e)}"}
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            Dict[str, Any]: 健康狀態
        """
        try:
            # 檢查 Milvus 連接
            connections.get_connection("default")
            
            # 檢查集合狀態
            collection_loaded = self.collection is not None
            
            return {
                "status": "healthy",
                "milvus_connected": True,
                "collection_loaded": collection_loaded,
                "search_type": self.search_type,
                "llm_available": self.llm is not None
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """關閉連接"""
        try:
            if self.collection:
                self.collection.release()
            connections.disconnect("default")
            logger.info("向量搜尋工具連接已關閉")
        except Exception as e:
            logger.error(f"關閉連接失敗: {str(e)}")

# 向後相容性別名
JobSearchRAG = EnhancedVectorSearchTool

# 示範使用方式
if __name__ == "__main__":
    # 職缺搜尋範例
    job_rag = EnhancedVectorSearchTool(search_type="job")
    
    job_queries = [
        "我想找一份台北市的前端開發工作，需要熟悉 React，月薪至少 5 萬",
        "有沒有在高雄的資深 Python 工程師職缺？",
        "有哪些按件計酬的工作機會？",
    ]
    
    for query in job_queries:
        print("\n" + "="*50)
        print(f"職缺查詢: {query}")
        result = job_rag.search(query, top_k=3)
        print(f"回答: {result['answer']}")
        print(f"找到 {len(result['hits'])} 個相關職缺")
    
    # 一般搜尋範例
    general_rag = EnhancedVectorSearchTool(search_type="general")
    
    general_queries = [
        "什麼是機器學習？",
        "如何學習 Python 程式設計？",
    ]
    
    for query in general_queries:
        print("\n" + "="*50)
        print(f"一般查詢: {query}")
        result = general_rag.search(query, top_k=3)
        print(f"回答: {result['answer']}")
        print(f"找到 {len(result['hits'])} 個相關內容")
    
    # 關閉連接
    job_rag.close()
    general_rag.close()
