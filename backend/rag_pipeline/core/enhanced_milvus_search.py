#!/usr/bin/env python3
"""
增強版 Milvus 搜尋服務

整合 LLM 功能來增強 Milvus 檢索：
- LLM 查詢增強
- 智能標籤提取
- 結果重排序
- 多模態搜尋

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 導入 LLM 整合服務
from core.llm_integration import LLMIntegrationService, LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSearchConfig:
    """增強搜尋配置"""
    # Milvus 配置
    milvus_host: str = "worker3"
    milvus_port: int = 19530
    collection_name: str = "podwise_chunks"
    similarity_threshold: float = 0.7
    
    # LLM 配置
    llm_host: str = "localhost"
    llm_port: int = 8003
    enable_llm_enhancement: bool = True
    enable_query_rewrite: bool = True
    enable_tag_extraction: bool = True
    enable_result_rerank: bool = True
    
    # 搜尋配置
    top_k: int = 10
    max_expansions: int = 3
    rerank_threshold: float = 0.5


class EnhancedMilvusSearch:
    """增強版 Milvus 搜尋服務"""
    
    def __init__(self, config: Optional[EnhancedSearchConfig] = None):
        self.config = config or EnhancedSearchConfig()
        
        # 初始化 LLM 整合服務
        llm_config = LLMConfig(
            host=self.config.llm_host,
            port=self.config.llm_port
        )
        self.llm_service = LLMIntegrationService(llm_config)
        
        # 初始化 Milvus 連接
        self._init_milvus_connection()
        
        # 搜尋歷史
        self.search_history: List[Dict[str, Any]] = []
    
    def _init_milvus_connection(self):
        """初始化 Milvus 連接"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 連接到 Milvus
            connections.connect(
                alias="default",
                host=self.config.milvus_host,
                port=self.config.milvus_port
            )
            
            # 檢查集合是否存在
            if utility.has_collection(self.config.collection_name):
                self.collection = Collection(self.config.collection_name)
                logger.info(f"Milvus 集合 '{self.config.collection_name}' 連接成功")
            else:
                logger.warning(f"Milvus 集合 '{self.config.collection_name}' 不存在")
                self.collection = None
                
        except ImportError:
            logger.warning("pymilvus 未安裝，將使用模擬搜尋")
            self.collection = None
        except Exception as e:
            logger.error(f"Milvus 連接失敗: {e}")
            self.collection = None
    
    async def search(self, query: str, user_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """執行增強搜尋"""
        try:
            start_time = datetime.now()
            
            # 1. LLM 查詢增強
            enhanced_query = await self._enhance_query(query)
            
            # 2. 執行向量搜尋
            search_results = await self._vector_search(enhanced_query, **kwargs)
            
            # 3. LLM 結果重排序
            if self.config.enable_result_rerank and search_results:
                search_results = await self._rerank_results(query, search_results)
            
            # 4. 記錄搜尋歷史
            self._log_search_history(query, enhanced_query, search_results, start_time)
            
            return search_results
            
        except Exception as e:
            logger.error(f"增強搜尋失敗: {e}")
            return []
    
    async def _enhance_query(self, query: str) -> Dict[str, Any]:
        """增強查詢"""
        if not self.config.enable_llm_enhancement:
            return {
                "original_query": query,
                "rewritten_query": query,
                "tags": {},
                "expansions": [],
                "enhanced_at": datetime.now().isoformat()
            }
        
        try:
            # 檢查 LLM 服務是否可用
            if not await self.llm_service.health_check():
                logger.warning("LLM 服務不可用，跳過查詢增強")
                return {
                    "original_query": query,
                    "rewritten_query": query,
                    "tags": {},
                    "expansions": [],
                    "enhanced_at": datetime.now().isoformat()
                }
            
            # 執行查詢增強
            enhanced = await self.llm_service.enhance_query(query)
            logger.info(f"查詢增強完成: {enhanced['rewritten_query']}")
            return enhanced
            
        except Exception as e:
            logger.error(f"查詢增強失敗: {e}")
            return {
                "original_query": query,
                "rewritten_query": query,
                "tags": {},
                "expansions": [],
                "enhanced_at": datetime.now().isoformat()
            }
    
    async def _vector_search(self, enhanced_query: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """執行向量搜尋"""
        try:
            # 使用重寫後的查詢
            query_text = enhanced_query.get("rewritten_query", enhanced_query.get("original_query", ""))
            
            # 獲取查詢嵌入
            embedding = await self.llm_service.get_embedding(query_text)
            if not embedding:
                logger.warning("無法獲取查詢嵌入，使用原始查詢")
                return self._fallback_search(query_text)
            
            # 執行 Milvus 搜尋
            if self.collection:
                results = await self._milvus_search(embedding, **kwargs)
            else:
                results = self._fallback_search(query_text)
            
            # 添加標籤過濾
            if enhanced_query.get("tags"):
                results = self._filter_by_tags(results, enhanced_query["tags"])
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return self._fallback_search(enhanced_query.get("original_query", ""))
    
    async def _milvus_search(self, embedding: List[float], **kwargs) -> List[Dict[str, Any]]:
        """執行 Milvus 搜尋"""
        try:
            if self.collection is None:
                logger.warning("Milvus 集合未初始化，使用回退搜尋")
                return []
            
            from pymilvus import Collection
            
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
                limit=self.config.top_k,
                output_fields=["chunk_id", "chunk_text", "metadata", "tags"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    if hit.score >= self.config.similarity_threshold:
                        formatted_results.append({
                            "chunk_id": hit.entity.get("chunk_id"),
                            "content": hit.entity.get("chunk_text"),
                            "similarity_score": hit.score,
                            "metadata": hit.entity.get("metadata", {}),
                            "tags": hit.entity.get("tags", []),
                            "source": "milvus"
                        })
            
            return formatted_results
            
        except ImportError:
            logger.warning("pymilvus 未安裝，使用回退搜尋")
            return []
        except Exception as e:
            logger.error(f"Milvus 搜尋失敗: {e}")
            return []
    
    def _fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """回退搜尋（模擬結果）"""
        logger.info("使用回退搜尋")
        
        # 模擬搜尋結果
        mock_results = [
            {
                "chunk_id": "chunk_1",
                "content": "商業週刊 Podcast 內容：台灣最具影響力的商業媒體，提供最新的財經資訊和市場分析。",
                "similarity_score": 0.85,
                "metadata": {"source": "business_weekly", "title": "商業週刊"},
                "tags": ["商業", "財經", "台灣"],
                "source": "fallback"
            },
            {
                "chunk_id": "chunk_2", 
                "content": "財經 M 平方 Podcast 內容：專業的財經分析，深入解析全球經濟趨勢。",
                "similarity_score": 0.82,
                "metadata": {"source": "m_square", "title": "財經 M 平方"},
                "tags": ["財經", "分析", "全球"],
                "source": "fallback"
            }
        ]
        
        # 根據查詢關鍵詞過濾
        filtered_results = []
        query_lower = query.lower()
        
        for result in mock_results:
            content_lower = result["content"].lower()
            if any(keyword in content_lower for keyword in ["商業", "財經", "podcast", "分析"]):
                filtered_results.append(result)
        
        return filtered_results[:self.config.top_k]
    
    def _filter_by_tags(self, results: List[Dict[str, Any]], tags: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """根據標籤過濾結果"""
        if not tags:
            return results
        
        filtered_results = []
        all_tags = []
        for tag_list in tags.values():
            all_tags.extend(tag_list)
        
        for result in results:
            result_tags = result.get("tags", [])
            # 檢查是否有標籤匹配
            if any(tag in result_tags for tag in all_tags):
                filtered_results.append(result)
        
        return filtered_results if filtered_results else results
    
    async def _rerank_results(self, original_query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重新排序結果"""
        if not self.config.enable_result_rerank or not results:
            return results
        
        try:
            # 檢查 LLM 服務是否可用
            if not await self.llm_service.health_check():
                logger.warning("LLM 服務不可用，跳過結果重排序")
                return results
            
            # 執行重排序
            reranked = await self.llm_service.rerank_results(original_query, results)
            logger.info(f"結果重排序完成，共 {len(reranked)} 個結果")
            return reranked
            
        except Exception as e:
            logger.error(f"結果重排序失敗: {e}")
            return results
    
    def _log_search_history(self, original_query: str, enhanced_query: Dict[str, Any], 
                           results: List[Dict[str, Any]], start_time: datetime):
        """記錄搜尋歷史"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        history_entry = {
            "timestamp": start_time.isoformat(),
            "duration": duration,
            "original_query": original_query,
            "enhanced_query": enhanced_query,
            "results_count": len(results),
            "results": results[:3]  # 只記錄前3個結果
        }
        
        self.search_history.append(history_entry)
        
        # 保持歷史記錄在合理範圍內
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-50:]
    
    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取搜尋歷史"""
        return self.search_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取搜尋統計"""
        if not self.search_history:
            return {
                "total_searches": 0,
                "average_duration": 0,
                "most_common_queries": [],
                "llm_enhancement_rate": 0
            }
        
        total_searches = len(self.search_history)
        total_duration = sum(entry["duration"] for entry in self.search_history)
        average_duration = total_duration / total_searches
        
        # 統計最常見的查詢
        query_counts = {}
        for entry in self.search_history:
            query = entry["original_query"]
            query_counts[query] = query_counts.get(query, 0) + 1
        
        most_common_queries = sorted(
            query_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 計算 LLM 增強率
        enhanced_count = sum(
            1 for entry in self.search_history 
            if entry["enhanced_query"]["rewritten_query"] != entry["original_query"]
        )
        llm_enhancement_rate = enhanced_count / total_searches if total_searches > 0 else 0
        
        return {
            "total_searches": total_searches,
            "average_duration": average_duration,
            "most_common_queries": most_common_queries,
            "llm_enhancement_rate": llm_enhancement_rate
        }
    
    async def close(self):
        """關閉連接"""
        await self.llm_service.close()


# 創建全局實例
enhanced_search = EnhancedMilvusSearch() 