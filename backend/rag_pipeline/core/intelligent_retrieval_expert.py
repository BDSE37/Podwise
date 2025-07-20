#!/usr/bin/env python3
"""
智能檢索專家實作

按照 agent_roles_config.py 中 intelligent_retrieval_expert 的配置實作：
- semantic_analyzer 萃取意圖與關鍵詞
- query_rewriter 參考 TAG_info 改寫查詢
- text2vec_model 向量化查詢
- milvus_db 檢索 top-k=8
- tag_matcher 依標籤重疊度＋相似度重排
- 信心分數 <0.7 時回傳 NO_MATCH

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 導入配置
try:
    import sys
    import os
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)
    from agent_roles_config import get_agent_roles_manager
    from integrated_config import get_config
except ImportError as e:
    logger.warning(f"配置模組導入失敗: {e}")
    get_agent_roles_manager = None
    get_config = None

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """檢索結果數據類別"""
    content: str
    semantic_score: float
    tag_score: float
    hybrid_score: float
    matched_tags: List[str]
    confidence: float
    source: str


@dataclass
class IntelligentRetrievalResponse:
    """智能檢索回應數據類別"""
    query: str
    results: List[RetrievalResult]
    total_matches: int
    avg_confidence: float
    processing_time: float
    status: str  # "SUCCESS", "NO_MATCH", "ERROR"


class SemanticAnalyzer:
    """語意分析器 - 萃取意圖與關鍵詞"""
    
    def __init__(self):
        """初始化語意分析器"""
        self.config = get_config()
        
    async def analyze(self, query: str) -> Dict[str, Any]:
        """
        分析查詢語意
        
        Args:
            query: 用戶查詢
            
        Returns:
            語意分析結果
        """
        try:
            # 使用 LLM 進行語意分析
            from core.llm_integration import LLMIntegrationService, LLMConfig
            
            llm_config = LLMConfig(
                host=self.config.ollama_host,
                port=11434,
                model="qwen2.5:8b"
            )
            llm_service = LLMIntegrationService(llm_config)
            
            analysis_prompt = f"""
            請分析以下查詢的語意：
            查詢：{query}
            
            請提取：
            1. 主要意圖
            2. 關鍵詞（按重要性排序）
            3. 查詢類型（推薦、分析、比較、解釋等）
            4. 相關領域
            
            請以 JSON 格式返回：
            {{
                "intent": "主要意圖",
                "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
                "query_type": "查詢類型",
                "domain": "相關領域",
                "confidence": 0.85
            }}
            """
            
            response = await llm_service.generate_text(analysis_prompt)
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning("LLM 回應格式錯誤，使用預設分析")
            
            # 預設分析
            return {
                "intent": "資訊查詢",
                "keywords": query.split(),
                "query_type": "general",
                "domain": "general",
                "confidence": 0.7
            }
            
        except Exception as e:
            logger.error(f"語意分析失敗: {e}")
            return {
                "intent": "資訊查詢",
                "keywords": query.split(),
                "query_type": "general",
                "domain": "general",
                "confidence": 0.5
            }


class QueryRewriter:
    """查詢重寫器 - 參考 TAG_info 改寫查詢"""
    
    def __init__(self, tag_csv_path: str = "scripts/csv/TAG_info.csv"):
        """初始化查詢重寫器"""
        self.tag_csv_path = tag_csv_path
        self.tag_mappings = self._load_tag_mappings()
        
    def _load_tag_mappings(self) -> Dict[str, List[str]]:
        """載入標籤對應"""
        try:
            import pandas as pd
            if os.path.exists(self.tag_csv_path):
                df = pd.read_csv(self.tag_csv_path)
                mappings = {}
                for _, row in df.iterrows():
                    tag = row.get('tag', '')
                    synonyms = row.get('synonyms', '')
                    if tag and synonyms:
                        mappings[tag] = [s.strip() for s in synonyms.split(',') if s.strip()]
                return mappings
        except Exception as e:
            logger.warning(f"載入標籤對應失敗: {e}")
        
        return {}
    
    async def rewrite(self, query: str, semantic_analysis: Dict[str, Any]) -> str:
        """
        重寫查詢
        
        Args:
            query: 原始查詢
            semantic_analysis: 語意分析結果
            
        Returns:
            重寫後的查詢
        """
        try:
            keywords = semantic_analysis.get("keywords", [])
            
            # 根據 TAG_info 擴展關鍵詞
            expanded_keywords = []
            for keyword in keywords:
                expanded_keywords.append(keyword)
                # 查找同義詞
                for tag, synonyms in self.tag_mappings.items():
                    if keyword in synonyms or keyword == tag:
                        expanded_keywords.extend(synonyms[:2])  # 取前2個同義詞
            
            # 去重並限制數量
            expanded_keywords = list(set(expanded_keywords))[:5]
            
            # 重寫查詢
            if expanded_keywords:
                rewritten = f"{query} {' '.join(expanded_keywords[:3])}"
                return rewritten
            
            return query
            
        except Exception as e:
            logger.error(f"查詢重寫失敗: {e}")
            return query


class Text2VecModel:
    """文本向量化模型"""
    
    def __init__(self):
        """初始化文本向量化模型"""
        self.config = get_config()
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """載入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = self.config.models.text2vec_path
            self.model = SentenceTransformer(model_name)
            logger.info(f"文本向量化模型載入成功: {model_name}")
            
        except Exception as e:
            logger.error(f"文本向量化模型載入失敗: {e}")
            self.model = None
    
    async def encode(self, text: str) -> Optional[List[float]]:
        """
        向量化文本
        
        Args:
            text: 輸入文本
            
        Returns:
            向量表示
        """
        try:
            if self.model is None:
                logger.warning("文本向量化模型未載入")
                return None
            
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"文本向量化失敗: {e}")
            return None


class MilvusDB:
    """Milvus 資料庫連接"""
    
    def __init__(self):
        """初始化 Milvus 連接"""
        self.config = get_config()
        self.collection = None
        self._connect()
        
    def _connect(self):
        """連接到 Milvus"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 連接到 Milvus
            connections.connect(
                alias="default",
                host=self.config.database.milvus_host,
                port=self.config.database.milvus_port
            )
            
            # 檢查集合是否存在
            collection_name = self.config.database.milvus_collection
            if utility.has_collection(collection_name):
                self.collection = Collection(collection_name)
                logger.info(f"Milvus 集合 '{collection_name}' 連接成功")
            else:
                logger.warning(f"Milvus 集合 '{collection_name}' 不存在")
                
        except ImportError:
            logger.warning("pymilvus 未安裝")
        except Exception as e:
            logger.error(f"Milvus 連接失敗: {e}")
    
    async def search(self, embedding: List[float], top_k: int = 8) -> List[Dict[str, Any]]:
        """
        執行向量搜尋
        
        Args:
            embedding: 查詢向量
            top_k: 返回結果數量
            
        Returns:
            搜尋結果
        """
        try:
            if self.collection is None:
                logger.warning("Milvus 集合未初始化")
                return []
            
            # 載入集合
            self.collection.load()
            
            # 執行搜尋
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "tags", "podcast_name", "episode_title", "category"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    # 解析 tags 欄位（JSON 格式）
                    tags = []
                    try:
                        if hit.entity.get("tags"):
                            if isinstance(hit.entity.get("tags"), str):
                                tags = json.loads(hit.entity.get("tags"))
                            else:
                                tags = hit.entity.get("tags")
                    except:
                        tags = []
                    
                    formatted_results.append({
                        "chunk_id": hit.entity.get("chunk_id"),
                        "content": hit.entity.get("chunk_text"),
                        "similarity_score": hit.score,
                        "metadata": {
                            "podcast_name": hit.entity.get("podcast_name", ""),
                            "episode_title": hit.entity.get("episode_title", ""),
                            "category": hit.entity.get("category", ""),
                            "chunk_id": hit.entity.get("chunk_id", "")
                        },
                        "tags": tags,
                        "source": "milvus"
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Milvus 搜尋失敗: {e}")
            return []


class TagMatcher:
    """標籤匹配器 - 依標籤重疊度＋相似度重排"""
    
    def __init__(self, tag_csv_path: str = "scripts/csv/TAG_info.csv"):
        """初始化標籤匹配器"""
        self.tag_csv_path = tag_csv_path
        self.tag_mappings = self._load_tag_mappings()
        
    def _load_tag_mappings(self) -> Dict[str, List[str]]:
        """載入標籤對應"""
        try:
            import pandas as pd
            if os.path.exists(self.tag_csv_path):
                df = pd.read_csv(self.tag_csv_path)
                mappings = {}
                for _, row in df.iterrows():
                    tag = row.get('tag', '')
                    synonyms = row.get('synonyms', '')
                    if tag and synonyms:
                        mappings[tag] = [s.strip() for s in synonyms.split(',') if s.strip()]
                return mappings
        except Exception as e:
            logger.warning(f"載入標籤對應失敗: {e}")
        
        return {}
    
    def match_tags(self, query_keywords: List[str], content_tags: List[str]) -> float:
        """
        計算標籤匹配度
        
        Args:
            query_keywords: 查詢關鍵詞
            content_tags: 內容標籤
            
        Returns:
            匹配度分數
        """
        try:
            if not query_keywords or not content_tags:
                return 0.0
            
            # 計算直接匹配
            direct_matches = 0
            for keyword in query_keywords:
                if keyword in content_tags:
                    direct_matches += 1
            
            # 計算同義詞匹配
            synonym_matches = 0
            for keyword in query_keywords:
                for tag, synonyms in self.tag_mappings.items():
                    if keyword in synonyms and tag in content_tags:
                        synonym_matches += 1
                        break
            
            # 計算總匹配度
            total_matches = direct_matches + synonym_matches
            max_possible = len(query_keywords)
            
            if max_possible == 0:
                return 0.0
            
            return total_matches / max_possible
            
        except Exception as e:
            logger.error(f"標籤匹配失敗: {e}")
            return 0.0
    
    def rerank_results(self, 
                      results: List[Dict[str, Any]], 
                      query_keywords: List[str],
                      semantic_score_weight: float = 0.7,
                      tag_score_weight: float = 0.3) -> List[RetrievalResult]:
        """
        重排序結果
        
        Args:
            results: 原始搜尋結果
            query_keywords: 查詢關鍵詞
            semantic_score_weight: 語意分數權重
            tag_score_weight: 標籤分數權重
            
        Returns:
            重排序後的結果
        """
        try:
            reranked_results = []
            
            for result in results:
                # 計算標籤匹配度
                content_tags = result.get("tags", [])
                tag_score = self.match_tags(query_keywords, content_tags)
                
                # 獲取語意相似度
                semantic_score = result.get("similarity_score", 0.0)
                
                # 計算混合分數
                hybrid_score = (semantic_score * semantic_score_weight + 
                              tag_score * tag_score_weight)
                
                # 創建檢索結果
                retrieval_result = RetrievalResult(
                    content=result.get("content", ""),
                    semantic_score=semantic_score,
                    tag_score=tag_score,
                    hybrid_score=hybrid_score,
                    matched_tags=content_tags,
                    confidence=hybrid_score,
                    source=result.get("source", "unknown")
                )
                
                reranked_results.append(retrieval_result)
            
            # 按混合分數排序
            reranked_results.sort(key=lambda x: x.hybrid_score, reverse=True)
            
            return reranked_results[:3]  # 取前3條
            
        except Exception as e:
            logger.error(f"結果重排序失敗: {e}")
            return []


class IntelligentRetrievalExpert:
    """智能檢索專家 - 按照 agent_roles_config.py 配置實作"""
    
    def __init__(self):
        """初始化智能檢索專家"""
        # 載入角色配置
        self.role_config = get_agent_roles_manager().get_role("intelligent_retrieval_expert")
        
        # 初始化工具
        self.semantic_analyzer = SemanticAnalyzer()
        self.query_rewriter = QueryRewriter()
        self.text2vec_model = Text2VecModel()
        self.milvus_db = MilvusDB()
        self.tag_matcher = TagMatcher()
        
        # 設定參數
        self.max_execution_time = self.role_config.max_execution_time if self.role_config else 25
        self.confidence_threshold = self.role_config.confidence_threshold if self.role_config else 0.7
        
        logger.info("智能檢索專家初始化完成")
    
    async def process_query(self, query: str) -> IntelligentRetrievalResponse:
        """
        處理查詢 - 按照配置的五步驟流程
        
        Args:
            query: 用戶查詢
            
        Returns:
            檢索結果
        """
        start_time = time.time()
        
        try:
            # 步驟一：semantic_analyzer 萃取意圖與關鍵詞
            logger.info("步驟一：語意分析")
            semantic_analysis = await self.semantic_analyzer.analyze(query)
            query_keywords = semantic_analysis.get("keywords", [])
            
            # 步驟二：query_rewriter 參考 TAG_info 改寫查詢
            logger.info("步驟二：查詢重寫")
            rewritten_query = await self.query_rewriter.rewrite(query, semantic_analysis)
            
            # 步驟三：text2vec_model 向量化查詢，milvus_db 檢索 top-k=8
            logger.info("步驟三：向量搜尋")
            query_embedding = await self.text2vec_model.encode(rewritten_query)
            if not query_embedding:
                return IntelligentRetrievalResponse(
                    query=query,
                    results=[],
                    total_matches=0,
                    avg_confidence=0.0,
                    processing_time=time.time() - start_time,
                    status="ERROR"
                )
            
            search_results = await self.milvus_db.search(query_embedding, top_k=8)
            
            # 步驟四：tag_matcher 依標籤重疊度＋相似度重排，取前 3 條
            logger.info("步驟四：標籤匹配與重排序")
            reranked_results = self.tag_matcher.rerank_results(
                search_results, 
                query_keywords
            )
            
            # 步驟五：若平均信心 <0.7，輸出『NO_MATCH』，否則以 default_QA JSON 格式回覆
            logger.info("步驟五：信心度評估")
            avg_confidence = 0.0
            if reranked_results:
                avg_confidence = sum(r.confidence for r in reranked_results) / len(reranked_results)
            
            processing_time = time.time() - start_time
            
            if avg_confidence < self.confidence_threshold:
                return IntelligentRetrievalResponse(
                    query=query,
                    results=[],
                    total_matches=0,
                    avg_confidence=avg_confidence,
                    processing_time=processing_time,
                    status="NO_MATCH"
                )
            
            return IntelligentRetrievalResponse(
                query=query,
                results=reranked_results,
                total_matches=len(reranked_results),
                avg_confidence=avg_confidence,
                processing_time=processing_time,
                status="SUCCESS"
            )
            
        except Exception as e:
            logger.error(f"智能檢索失敗: {e}")
            return IntelligentRetrievalResponse(
                query=query,
                results=[],
                total_matches=0,
                avg_confidence=0.0,
                processing_time=time.time() - start_time,
                status="ERROR"
            )
    
    def format_response(self, response: IntelligentRetrievalResponse) -> str:
        """
        格式化回應為 default_QA JSON 格式
        
        Args:
            response: 檢索回應
            
        Returns:
            JSON 格式回應
        """
        try:
            if response.status == "NO_MATCH":
                return json.dumps({
                    "answer": "",
                    "confidence": 0.0,
                    "sources": [],
                    "status": "NO_MATCH"
                }, ensure_ascii=False, indent=2)
            
            if response.status == "ERROR":
                return json.dumps({
                    "answer": "",
                    "confidence": 0.0,
                    "sources": [],
                    "status": "ERROR"
                }, ensure_ascii=False, indent=2)
            
            # 生成答案
            answer_parts = []
            for i, result in enumerate(response.results, 1):
                answer_parts.append(f"{i}. {result.content[:100]}...")
            
            answer = "根據您的查詢，我找到了以下相關資訊：\n\n" + "\n\n".join(answer_parts)
            
            # 格式化為 JSON
            formatted_response = {
                "answer": answer,
                "confidence": response.avg_confidence,
                "sources": [
                    {
                        "content": result.content,
                        "confidence": result.confidence,
                        "matched_tags": result.matched_tags,
                        "source": result.source
                    }
                    for result in response.results
                ],
                "status": "SUCCESS",
                "processing_time": response.processing_time
            }
            
            return json.dumps(formatted_response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"回應格式化失敗: {e}")
            return json.dumps({
                "answer": "",
                "confidence": 0.0,
                "sources": [],
                "status": "ERROR"
            }, ensure_ascii=False, indent=2)


# 全域實例
intelligent_retrieval_expert = IntelligentRetrievalExpert()


def get_intelligent_retrieval_expert() -> IntelligentRetrievalExpert:
    """獲取智能檢索專家實例"""
    return intelligent_retrieval_expert


if __name__ == "__main__":
    # 測試智能檢索專家
    async def test_retrieval():
        expert = get_intelligent_retrieval_expert()
        
        # 測試查詢
        test_query = "推薦一些商業相關的 Podcast"
        
        print(f"測試查詢: {test_query}")
        print("=" * 50)
        
        # 執行檢索
        response = await expert.process_query(test_query)
        
        print(f"檢索狀態: {response.status}")
        print(f"平均信心度: {response.avg_confidence:.3f}")
        print(f"處理時間: {response.processing_time:.3f} 秒")
        print(f"結果數量: {response.total_matches}")
        
        if response.results:
            print("\n檢索結果:")
            for i, result in enumerate(response.results, 1):
                print(f"{i}. 內容: {result.content[:100]}...")
                print(f"   語意分數: {result.semantic_score:.3f}")
                print(f"   標籤分數: {result.tag_score:.3f}")
                print(f"   混合分數: {result.hybrid_score:.3f}")
                print(f"   匹配標籤: {result.matched_tags}")
                print()
        
        # 格式化回應
        formatted = expert.format_response(response)
        print("格式化回應:")
        print(formatted)
    
    # 執行測試
    asyncio.run(test_retrieval()) 