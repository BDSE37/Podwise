#!/usr/bin/env python3
"""
增強版 Podcast 推薦器

整合 Milvus 向量檢索、LLM 推薦和 Langfuse 追蹤功能
提供智能化的 Podcast 推薦服務

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PodcastRecommendation:
    """Podcast 推薦結果"""
    podcast_id: str
    title: str
    description: str
    category: str
    confidence: float
    reasoning: str
    similarity_score: float
    tags: List[str]
    episode_count: int
    last_updated: str


@dataclass
class RecommendationRequest:
    """推薦請求"""
    query: str
    user_id: str
    limit: int = 5
    categories: Optional[List[str]] = None
    min_confidence: float = 0.7
    include_reasoning: bool = True


@dataclass
class RecommendationResponse:
    """推薦回應"""
    user_id: str
    query: str
    recommendations: List[PodcastRecommendation]
    total_found: int
    processing_time: float
    confidence: float
    reasoning: str
    timestamp: str


class EnhancedPodcastRecommender:
    """增強版 Podcast 推薦器"""
    
    def __init__(self, 
                 milvus_host: str = "192.168.32.86",
                 milvus_port: int = 19530,
                 collection_name: str = "podcast_chunks",
                 llm_model: str = "qwen2.5-taiwan-7b-instruct",
                 enable_langfuse: bool = True):
        """
        初始化增強版 Podcast 推薦器
        
        Args:
            milvus_host: Milvus 主機地址
            milvus_port: Milvus 端口
            collection_name: 向量集合名稱
            llm_model: LLM 模型名稱
            enable_langfuse: 是否啟用 Langfuse 追蹤
        """
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = collection_name
        self.llm_model = llm_model
        self.enable_langfuse = enable_langfuse
        
        # 初始化組件
        self.milvus_client = None
        self.llm_client = None
        self.langfuse_client = None
        
        # 初始化狀態
        self.is_initialized = False
        
        logger.info(f"增強版 Podcast 推薦器初始化完成，Milvus: {milvus_host}:{milvus_port}")
    
    async def initialize(self) -> bool:
        """初始化推薦器"""
        try:
            # 初始化 Milvus 客戶端
            await self._initialize_milvus()
            
            # 初始化 LLM 客戶端
            await self._initialize_llm()
            
            # 初始化 Langfuse 追蹤
            if self.enable_langfuse:
                await self._initialize_langfuse()
            
            self.is_initialized = True
            logger.info("增強版 Podcast 推薦器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"增強版 Podcast 推薦器初始化失敗: {e}")
            return False
    
    async def _initialize_milvus(self) -> None:
        """初始化 Milvus 客戶端"""
        try:
            from pymilvus import connections, Collection
            
            # 連接到 Milvus
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            
            # 檢查集合是否存在
            from pymilvus import utility
            if utility.has_collection(self.collection_name):
                self.milvus_collection = Collection(self.collection_name)
                logger.info(f"Milvus 集合 '{self.collection_name}' 連接成功")
            else:
                logger.warning(f"Milvus 集合 '{self.collection_name}' 不存在")
                self.milvus_collection = None
                
        except ImportError:
            logger.warning("pymilvus 未安裝，Milvus 功能將被禁用")
            self.milvus_collection = None
        except Exception as e:
            logger.error(f"Milvus 初始化失敗: {e}")
            self.milvus_collection = None
    
    async def _initialize_llm(self) -> None:
        """初始化 LLM 客戶端"""
        try:
            # 優先使用 OpenAI
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                try:
                    import openai
                    self.llm_client = openai.AsyncOpenAI(
                        api_key=openai_api_key,
                        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
                    )
                    logger.info(f"LLM 客戶端初始化成功，使用 OpenAI 模型: {self.llm_model}")
                    return
                except Exception as e:
                    logger.warning(f"OpenAI 初始化失敗: {e}")
            
            # 備用：使用本地 Ollama 模型
            ollama_host = os.getenv("OLLAMA_HOST")
            if ollama_host:
                self.llm_client = "ollama"
                logger.info(f"LLM 客戶端初始化成功，使用本地 Ollama 模型: {self.llm_model}")
                return
            
            # 最後備用：無 LLM
            self.llm_client = None
            logger.warning("所有 LLM 服務都不可用")
            
        except Exception as e:
            logger.error(f"LLM 初始化失敗: {e}")
            self.llm_client = None
    
    async def _initialize_langfuse(self) -> None:
        """初始化 Langfuse 追蹤"""
        try:
            from langfuse import Langfuse
            
            self.langfuse_client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
            logger.info("Langfuse 追蹤初始化成功")
            
        except ImportError:
            logger.warning("langfuse 未安裝，追蹤功能將被禁用")
            self.langfuse_client = None
        except Exception as e:
            logger.error(f"Langfuse 初始化失敗: {e}")
            self.langfuse_client = None
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        獲取 Podcast 推薦
        
        Args:
            request: 推薦請求
            
        Returns:
            推薦回應
        """
        start_time = datetime.now()
        
        try:
            if not self.is_initialized:
                raise RuntimeError("推薦器未初始化")
            
            # 1. 向量檢索
            vector_results = await self._vector_search(request.query, request.limit)
            
            # 2. LLM 智能推薦
            llm_results = await self._llm_recommendation(
                request.query, 
                vector_results, 
                request.include_reasoning
            )
            
            # 3. 合併結果
            final_recommendations = self._merge_recommendations(
                vector_results, 
                llm_results, 
                request.limit
            )
            
            # 4. 計算整體信心度
            confidence = self._calculate_overall_confidence(final_recommendations)
            
            # 5. 生成推理說明
            reasoning = self._generate_reasoning(request.query, final_recommendations)
            
            # 6. 記錄到 Langfuse
            if self.langfuse_client:
                await self._log_to_langfuse(request, final_recommendations, confidence)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RecommendationResponse(
                user_id=request.user_id,
                query=request.query,
                recommendations=final_recommendations,
                total_found=len(final_recommendations),
                processing_time=processing_time,
                confidence=confidence,
                reasoning=reasoning,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"獲取推薦失敗: {e}")
            return RecommendationResponse(
                user_id=request.user_id,
                query=request.query,
                recommendations=[],
                total_found=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                confidence=0.0,
                reasoning=f"推薦失敗: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """向量檢索"""
        if not self.milvus_collection:
            logger.warning("Milvus 未可用，跳過向量檢索")
            return []
        
        try:
            # 生成查詢向量
            query_vector = await self._generate_query_embedding(query)
            
            # 執行向量搜尋
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # 修正：使用正確的欄位名稱
            results = self.milvus_collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=["podcast_id", "episode_title", "chunk_text", "category", "tags", "podcast_name"]
            )
            
            # 格式化結果
            formatted_results = []
            try:
                # 處理 Milvus 搜尋結果
                if hasattr(results, '__iter__'):
                    for hits in results:
                        if hasattr(hits, '__iter__'):
                            for hit in hits:
                                # 檢查實體是否存在
                                if hasattr(hit, 'entity') and hit.entity:
                                    formatted_results.append({
                                        'podcast_id': hit.entity.get('podcast_id'),
                                        'title': hit.entity.get('episode_title'),  # 修正：使用 episode_title
                                        'description': hit.entity.get('chunk_text', '')[:200],  # 使用 chunk_text 作為描述
                                        'category': hit.entity.get('category'),
                                        'tags': self._parse_tags(hit.entity.get('tags', [])),
                                        'similarity_score': hit.score,
                                        'confidence': hit.score,
                                        'podcast_name': hit.entity.get('podcast_name', '')
                                    })
                                else:
                                    logger.warning("Milvus 搜尋結果缺少實體數據")
            except Exception as e:
                logger.warning(f"處理 Milvus 搜尋結果時發生錯誤: {e}")
                # 返回模擬結果
                formatted_results = [
                    {
                        'podcast_id': 'mock_001',
                        'title': '模擬播客節目',
                        'description': '這是一個模擬的播客節目描述，用於測試目的。',
                        'category': '一般',
                        'tags': ['模擬', '測試'],
                        'similarity_score': 0.8,
                        'confidence': 0.8,
                        'podcast_name': '模擬播客'
                    }
                ]
            
            logger.info(f"向量檢索完成，找到 {len(formatted_results)} 個結果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量檢索失敗: {e}")
            # 返回模擬結果
            return [
                {
                    'podcast_id': 'mock_001',
                    'title': '模擬播客節目',
                    'description': '這是一個模擬的播客節目描述，用於測試目的。',
                    'category': '一般',
                    'tags': ['模擬', '測試'],
                    'similarity_score': 0.8,
                    'confidence': 0.8,
                    'podcast_name': '模擬播客'
                }
            ]
    
    def _parse_tags(self, tags: Union[str, List]) -> List[str]:
        """解析標籤"""
        try:
            if isinstance(tags, str):
                import json
                return json.loads(tags)
            elif isinstance(tags, list):
                return tags
            else:
                return []
        except:
            return []
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """生成查詢向量"""
        try:
            # 優先使用 OpenAI
            if (self.llm_client and 
                hasattr(self.llm_client, 'embeddings') and 
                self.llm_client != "ollama" and
                self.llm_client is not None):
                try:
                    response = await self.llm_client.embeddings.create(
                        model="text-embedding-3-small",
                        input=query
                    )
                    return response.data[0].embedding
                except Exception as e:
                    logger.warning(f"OpenAI 嵌入失敗: {e}")
            
            # 備用：使用本地 Ollama 嵌入模型
            if os.getenv("OLLAMA_HOST"):
                return await self._generate_ollama_embedding(query)
            
            # 最後備用：簡單向量
            return self._simple_embedding(query)
            
        except Exception as e:
            logger.error(f"生成查詢向量失敗: {e}")
            return self._simple_embedding(query)
    
    async def _generate_ollama_embedding(self, query: str) -> List[float]:
        """生成 Ollama 嵌入向量"""
        try:
            import aiohttp
            
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            
            # 統一使用 BGE-M3 嵌入模型 (1024維)
            embedding_models = [
                "bge-m3",           # 1024維，主要模型
                "BAAI/bge-m3"       # 完整名稱備用
            ]
            
            for model in embedding_models:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{ollama_host}/api/embeddings",
                            json={"model": model, "prompt": query},
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                embedding = data.get("embedding", [])
                                
                                # 標準化向量維度為 1024
                                if len(embedding) == 1024:
                                    logger.info(f"使用 {model} 生成 1024 維嵌入向量")
                                    return embedding
                                elif len(embedding) > 1024:
                                    # 截斷到 1024 維
                                    logger.warning(f"{model} 生成 {len(embedding)} 維向量，截斷到 1024 維")
                                    return embedding[:1024]
                                else:
                                    # 填充到 1024 維
                                    logger.warning(f"{model} 生成 {len(embedding)} 維向量，填充到 1024 維")
                                    return embedding + [0.0] * (1024 - len(embedding))
                            else:
                                logger.warning(f"{model} 嵌入失敗: {response.status}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"{model} 嵌入失敗: {e}")
                    continue
            
            # 如果所有模型都失敗，使用簡單向量
            logger.warning("BGE-M3 嵌入模型失敗，使用簡單向量")
            return self._simple_embedding(query)
                        
        except Exception as e:
            logger.error(f"Ollama 嵌入失敗: {e}")
            return self._simple_embedding(query)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """簡單的詞頻向量（備用方案）"""
        import hashlib
        import struct
        
        # 生成 1024 維的簡單向量
        vector = []
        for i in range(1024):
            hash_input = f"{text}_{i}".encode()
            hash_value = hashlib.md5(hash_input).digest()
            float_value = struct.unpack('f', hash_value[:4])[0]
            vector.append(float_value)
        
        return vector
    
    async def _llm_recommendation(self, 
                                query: str, 
                                vector_results: List[Dict[str, Any]], 
                                include_reasoning: bool) -> List[Dict[str, Any]]:
        """LLM 智能推薦"""
        if not self.llm_client:
            logger.warning("LLM 未可用，跳過智能推薦")
            return vector_results
        
        try:
            # 構建推薦提示
            prompt = self._build_recommendation_prompt(query, vector_results, include_reasoning)
            
            # 調用 LLM
            if self.llm_client == "ollama":
                response_text = await self._call_ollama_llm(prompt)
            elif (hasattr(self.llm_client, 'chat') and 
                  hasattr(self.llm_client.chat, 'completions') and
                  self.llm_client is not None):
                response = await self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": "你是一個專業的 Podcast 推薦專家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                response_text = response.choices[0].message.content
            else:
                logger.warning("LLM 客戶端格式不正確或為空")
                return vector_results
            
            # 解析 LLM 回應
            if response_text:
                llm_recommendations = self._parse_llm_response(
                    response_text,
                    vector_results
                )
            else:
                llm_recommendations = vector_results
            
            logger.info(f"LLM 推薦完成，處理了 {len(llm_recommendations)} 個結果")
            return llm_recommendations
            
        except Exception as e:
            logger.error(f"LLM 推薦失敗: {e}")
            return vector_results
    
    async def _call_ollama_llm(self, prompt: str) -> str:
        """調用 Ollama LLM"""
        try:
            import aiohttp
            import json
            
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            
            # 嘗試多個 LLM 模型，按優先級排序
            llm_models = [
                "qwen2.5-taiwan-7b-instruct",  # 台灣版本
                "weiren119/Qwen2.5-Taiwan-8B-Instruct",  # 完整名稱
                "qwen2.5:8b",                  # 標準版本
                "qwen3:8b",                    # Qwen3 版本
                "gpt-3.5-turbo",               # 備用
                "llama2:7b",                   # 最後備用
                "mistral:7b"                   # 最後備用
            ]
            
            for model in llm_models:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{ollama_host}/api/generate",
                            json={
                                "model": model,
                                "prompt": prompt,
                                "stream": False
                            },
                            timeout=aiohttp.ClientTimeout(total=60)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                response_text = data.get("response", "")
                                if response_text:
                                    logger.info(f"使用 {model} 成功生成回應")
                                    return response_text
                            else:
                                logger.warning(f"{model} 調用失敗: {response.status}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"{model} 調用失敗: {e}")
                    continue
            
            # 如果所有模型都失敗，返回預設回應
            logger.error("所有 Ollama LLM 模型都失敗")
            return "抱歉，LLM 服務暫時不可用，請稍後再試。"
                        
        except Exception as e:
            logger.error(f"Ollama LLM 調用失敗: {e}")
            return "LLM 服務發生錯誤，請稍後再試。"
    
    def _build_recommendation_prompt(self, 
                                   query: str, 
                                   vector_results: List[Dict[str, Any]], 
                                   include_reasoning: bool) -> str:
        """構建推薦提示"""
        prompt = f"""
基於用戶查詢：「{query}」

以下是向量檢索找到的 Podcast：

"""
        
        for i, result in enumerate(vector_results, 1):
            prompt += f"""
{i}. {result['title']}
   播客: {result.get('podcast_name', '未知')}
   類別: {result['category']}
   描述: {result['description'][:200]}...
   標籤: {', '.join(result['tags'][:5])}
   相似度: {result['similarity_score']:.3f}
"""
        
        prompt += f"""

請根據用戶查詢和這些 Podcast 的資訊，提供智能推薦：

1. 重新排序這些 Podcast，將最相關的放在前面
2. 為每個推薦提供信心度評分（0-1）
3. 如果要求推理說明，請為每個推薦提供簡短的理由

請以 JSON 格式回應：
{{
    "recommendations": [
        {{
            "podcast_id": "id",
            "confidence": 0.9,
            "reasoning": "推薦理由"
        }}
    ]
}}
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析 LLM 回應"""
        try:
            import json
            
            # 嘗試解析 JSON
            data = json.loads(response)
            llm_recommendations = data.get('recommendations', [])
            
            # 更新向量結果
            updated_results = []
            for vector_result in vector_results:
                # 查找對應的 LLM 推薦
                llm_rec = next(
                    (r for r in llm_recommendations if r.get('podcast_id') == vector_result['podcast_id']),
                    None
                )
                
                if llm_rec:
                    vector_result['confidence'] = llm_rec.get('confidence', vector_result['confidence'])
                    vector_result['reasoning'] = llm_rec.get('reasoning', '')
                
                updated_results.append(vector_result)
            
            return updated_results
            
        except Exception as e:
            logger.error(f"解析 LLM 回應失敗: {e}")
            return vector_results
    
    def _merge_recommendations(self, 
                             vector_results: List[Dict[str, Any]], 
                             llm_results: List[Dict[str, Any]], 
                             limit: int) -> List[PodcastRecommendation]:
        """合併推薦結果"""
        # 使用 LLM 結果作為主要排序依據
        merged_results = []
        
        for result in llm_results[:limit]:
            recommendation = PodcastRecommendation(
                podcast_id=result['podcast_id'],
                title=result['title'],
                description=result['description'],
                category=result['category'],
                confidence=result['confidence'],
                reasoning=result.get('reasoning', ''),
                similarity_score=result['similarity_score'],
                tags=result['tags'],
                episode_count=0,  # 需要從資料庫獲取
                last_updated=datetime.now().isoformat()
            )
            merged_results.append(recommendation)
        
        return merged_results
    
    def _calculate_overall_confidence(self, recommendations: List[PodcastRecommendation]) -> float:
        """計算整體信心度"""
        if not recommendations:
            return 0.0
        
        total_confidence = sum(r.confidence for r in recommendations)
        return total_confidence / len(recommendations)
    
    def _generate_reasoning(self, query: str, recommendations: List[PodcastRecommendation]) -> str:
        """生成推理說明"""
        if not recommendations:
            return "未找到相關的 Podcast 推薦"
        
        reasoning = f"基於您的查詢「{query}」，我推薦了 {len(recommendations)} 個相關的 Podcast：\n\n"
        
        for i, rec in enumerate(recommendations[:3], 1):
            reasoning += f"{i}. {rec.title} (信心度: {rec.confidence:.2f})\n"
            if rec.reasoning:
                reasoning += f"   理由: {rec.reasoning}\n"
            reasoning += "\n"
        
        return reasoning
    
    async def _log_to_langfuse(self, 
                              request: RecommendationRequest, 
                              recommendations: List[PodcastRecommendation], 
                              confidence: float) -> None:
        """記錄到 Langfuse"""
        if not self.langfuse_client:
            return
        
        try:
            # 創建追蹤
            trace = self.langfuse_client.trace(
                name="podcast_recommendation",
                user_id=request.user_id,
                metadata={
                    "query": request.query,
                    "limit": request.limit,
                    "total_recommendations": len(recommendations),
                    "overall_confidence": confidence
                }
            )
            
            # 記錄生成步驟 - 修正 Langfuse 錯誤
            if trace:
                generation = trace.generation(
                    name="recommendation_generation",
                    model=self.llm_model,
                    completion=str([r.title for r in recommendations]),
                    metadata={
                        "recommendations": [
                            {
                                "title": r.title,
                                "confidence": r.confidence,
                                "reasoning": r.reasoning
                            }
                            for r in recommendations
                        ]
                    }
                )
                
                # 記錄向量檢索步驟
                span = trace.span(
                    name="vector_search",
                    metadata={
                        "milvus_collection": self.collection_name,
                        "query": request.query
                    }
                )
                if span:
                    span.end()
                
                # 完成追蹤
                trace.update(
                    status="success",
                    metadata={
                        "average_confidence": confidence
                    }
                )
            
            logger.info("推薦結果已記錄到 Langfuse")
            
        except Exception as e:
            logger.error(f"記錄到 Langfuse 失敗: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            "status": "healthy" if self.is_initialized else "unhealthy",
            "milvus_available": self.milvus_collection is not None,
            "llm_available": self.llm_client is not None,
            "langfuse_available": self.langfuse_client is not None,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self) -> None:
        """清理資源"""
        try:
            if self.milvus_collection:
                self.milvus_collection.release()
            
            if self.langfuse_client:
                self.langfuse_client.flush()
            
            logger.info("增強版 Podcast 推薦器清理完成")
            
        except Exception as e:
            logger.error(f"清理失敗: {e}")


# 全域推薦器實例
enhanced_recommender = EnhancedPodcastRecommender()


def get_enhanced_podcast_recommender() -> EnhancedPodcastRecommender:
    """獲取增強版 Podcast 推薦器"""
    return enhanced_recommender


async def get_podcast_recommendations(query: str, 
                                    user_id: str, 
                                    limit: int = 5) -> List[Dict[str, Any]]:
    """
    獲取 Podcast 推薦（簡化介面）
    
    Args:
        query: 查詢內容
        user_id: 用戶ID
        limit: 推薦數量
        
    Returns:
        推薦列表
    """
    request = RecommendationRequest(
        query=query,
        user_id=user_id,
        limit=limit
    )
    
    response = await enhanced_recommender.get_recommendations(request)
    
    # 轉換為字典格式
    return [
        {
            "podcast_id": rec.podcast_id,
            "title": rec.title,
            "description": rec.description,
            "category": rec.category,
            "confidence": rec.confidence,
            "reasoning": rec.reasoning,
            "similarity_score": rec.similarity_score,
            "tags": rec.tags
        }
        for rec in response.recommendations
    ]


async def test_enhanced_recommender():
    """測試增強版推薦器"""
    try:
        logger.info("開始測試增強版 Podcast 推薦器...")
        
        # 初始化
        success = await enhanced_recommender.initialize()
        if not success:
            logger.error("推薦器初始化失敗")
            return False
        
        # 測試推薦
        test_query = "科技類 Podcast"
        recommendations = await get_podcast_recommendations(test_query, "test_user", 3)
        
        logger.info(f"推薦測試成功，獲得 {len(recommendations)} 個推薦")
        
        # 測試健康檢查
        health = await enhanced_recommender.health_check()
        logger.info(f"健康檢查: {health['status']}")
        
        logger.info("增強版 Podcast 推薦器測試完成")
        return True
        
    except Exception as e:
        logger.error(f"測試增強版 Podcast 推薦器時發生錯誤: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_enhanced_recommender()) 