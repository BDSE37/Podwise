"""
搜尋服務
整合語意搜尋功能
符合 Google Clean Code 原則
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .embedding_service import EmbeddingService
from ..config.settings import config

logger = logging.getLogger(__name__)


class SearchService:
    """搜尋服務 - 整合語意搜尋功能"""
    
    def __init__(self, milvus_config: Optional[Dict[str, Any]] = None):
        """
        初始化搜尋服務
        
        Args:
            milvus_config: Milvus 配置
        """
        self.embedding_service = EmbeddingService(milvus_config)
        
    def search_similar_content(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋相似內容
        
        Args:
            query_text: 查詢文本
            top_k: 返回結果數量
            
        Returns:
            相似內容列表
        """
        try:
            results = self.embedding_service.search_similar_chunks(query_text, top_k)
            
            logger.info(f"搜尋完成: '{query_text}' -> {len(results)} 個結果")
            
            return results
            
        except Exception as e:
            logger.error(f"搜尋失敗: {e}")
            return []
    
    def batch_search(self, queries: List[str], top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        批次搜尋
        
        Args:
            queries: 查詢列表
            top_k: 每個查詢返回結果數量
            
        Returns:
            每個查詢的結果
        """
        results = {}
        
        logger.info(f"開始批次搜尋 {len(queries)} 個查詢")
        
        for query in queries:
            logger.info(f"搜尋: '{query}'")
            query_results = self.search_similar_content(query, top_k)
            results[query] = query_results
        
        return results
    
    def search_by_tags(self, tags: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根據標籤搜尋
        
        Args:
            tags: 標籤列表
            top_k: 返回結果數量
            
        Returns:
            符合標籤的內容列表
        """
        # 將標籤組合成查詢文本
        query_text = " ".join(tags)
        
        logger.info(f"根據標籤搜尋: {tags}")
        
        return self.search_similar_content(query_text, top_k)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        獲取集合統計資訊
        
        Returns:
            集合統計資訊
        """
        return self.embedding_service.get_collection_stats()
    
    def test_search_functionality(self) -> Dict[str, Any]:
        """
        測試搜尋功能
        
        Returns:
            測試結果
        """
        test_queries = [
            "投資理財",
            "股票市場", 
            "退休規劃",
            "職場發展",
            "健康生活"
        ]
        
        logger.info("開始搜尋功能測試")
        
        results = self.batch_search(test_queries, top_k=3)
        
        # 分析結果
        total_results = sum(len(r) for r in results.values())
        avg_results_per_query = total_results / len(test_queries) if test_queries else 0
        
        test_summary = {
            "test_queries": test_queries,
            "total_results": total_results,
            "avg_results_per_query": avg_results_per_query,
            "results": results
        }
        
        logger.info(f"搜尋功能測試完成: {total_results} 個總結果")
        
        return test_summary 