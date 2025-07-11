#!/usr/bin/env python3
"""
RAG Pipeline 向量搜尋工具

整合統一工具模組，提供 RAG 特定的向量搜尋功能：
- 使用統一的向量搜尋服務
- 整合 ML Pipeline 推薦系統
- 支援標籤過濾

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 添加路徑以便導入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from utils import (
        create_logger,
        create_vector_search,
        create_text_processor,
        VectorSearchResult,
        UnifiedVectorSearch,
        TextProcessor
    )
except ImportError:
    # 如果無法導入 utils，使用簡化版本
    logger = logging.getLogger(__name__)
    
    class VectorSearchResult:
        def __init__(self, chunk_id: str, chunk_text: str, similarity_score: float, metadata: Dict[str, Any] = None, tags: List[str] = None):
            self.chunk_id = chunk_id
            self.chunk_text = chunk_text
            self.similarity_score = similarity_score
            self.metadata = metadata or {}
            self.tags = tags or []
    
    class UnifiedVectorSearch:
        def __init__(self, host: str = "localhost", port: int = 19530, collection_name: str = "podcast_chunks", similarity_threshold: float = 0.7):
            self.host = host
            self.port = port
            self.collection_name = collection_name
            self.similarity_threshold = similarity_threshold
            self._is_available = True
        
        def is_available(self) -> bool:
            return self._is_available
        
        def search_by_text(self, query_text: str, embedding_model=None, top_k: int = 5) -> List[VectorSearchResult]:
            # 模擬搜尋結果
            return [
                VectorSearchResult(
                    chunk_id="chunk_1",
                    chunk_text="商業週刊 Podcast 內容",
                    similarity_score=0.85,
                    metadata={"source": "business_weekly"},
                    tags=["商業", "財經"]
                )
            ]
    
    class TextProcessor:
        def __init__(self, tag_csv_path: str = None):
            self.tag_csv_path = tag_csv_path
            self.tag_processor = None
            self.embedding_processor = None
    
    def create_logger(name: str):
        return logging.getLogger(name)
    
    def create_vector_search(host: str, port: int, collection_name: str, similarity_threshold: float):
        return UnifiedVectorSearch(host, port, collection_name, similarity_threshold)
    
    def create_text_processor(tag_csv_path: str = None):
        return TextProcessor(tag_csv_path)

# 導入統一數據模型
try:
    from core.integrated_core import SearchResult
except ImportError:
    # 如果無法導入，創建簡化版本
    class SearchResult:
        def __init__(self, chunk_id: str, content: str, similarity_score: float, source: str, metadata: Dict[str, Any] = None, tags_used: List[str] = None, confidence: float = 0.0, timestamp=None):
            self.chunk_id = chunk_id
            self.content = content
            self.similarity_score = similarity_score
            self.source = source
            self.metadata = metadata or {}
            self.tags_used = tags_used or []
            self.confidence = confidence
            self.timestamp = timestamp or datetime.now()

logger = create_logger(__name__)


@dataclass
class RAGSearchConfig:
    """RAG 搜尋配置"""
    top_k: int = 5
    similarity_threshold: float = 0.7
    use_milvus: bool = True
    use_ml_pipeline: bool = True
    use_tags: bool = True
    user_id: int = 1
    tag_csv_path: str = "scripts/csv/TAG_info.csv"


class RAGVectorSearch:
    """RAG 向量搜尋服務"""
    
    def __init__(self, config: Optional[RAGSearchConfig] = None):
        self.config = config or RAGSearchConfig()
        
        # 初始化統一向量搜尋服務
        self.vector_search = create_vector_search(
            host=os.getenv("MILVUS_HOST", "localhost"),
            port=int(os.getenv("MILVUS_PORT", "19530")),
            collection_name="podcast_chunks",
            similarity_threshold=self.config.similarity_threshold
        )
        
        # 初始化文本處理器
        self.text_processor = create_text_processor(
            tag_csv_path=self.config.tag_csv_path
        )
        
        # ML Pipeline 推薦系統
        self.ml_recommender = None
        if self.config.use_ml_pipeline:
            self._init_ml_recommender()
    
    def _init_ml_recommender(self):
        """初始化 ML Pipeline 推薦系統"""
        try:
            # 動態導入 ML Pipeline
            ml_pipeline_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "ml_pipeline"
            )
            sys.path.append(ml_pipeline_path)
            
            from services.api_service import RecommendationService
            from config.recommender_config import get_recommender_config
            
            config = get_recommender_config()
            self.ml_recommender = RecommendationService(config)
            logger.info("ML Pipeline 推薦系統初始化成功")
            
        except ImportError as e:
            logger.warning(f"無法載入 ML Pipeline: {e}")
            self.ml_recommender = None
        except Exception as e:
            logger.error(f"ML Pipeline 初始化失敗: {e}")
            self.ml_recommender = None
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """執行 RAG 向量搜尋"""
        try:
            # 1. 標籤提取和查詢預處理
            tags = []
            if self.text_processor and self.text_processor.tag_processor:
                tags = self.text_processor.tag_processor.extract_tags(query)
            logger.info(f"提取標籤: {tags}")
            
            # 2. 向量搜尋
            vector_results = []
            if self.config.use_milvus and self.vector_search.is_available():
                # 使用文本處理器的嵌入功能
                embedding_processor = self.text_processor.embedding_processor
                if embedding_processor and embedding_processor.model:
                    vector_results = self.vector_search.search_by_text(
                        query_text=query,
                        embedding_model=embedding_processor,
                        top_k=self.config.top_k
                    )
            
            # 3. ML Pipeline 推薦（如果可用）
            ml_results = []
            if self.ml_recommender and self.config.use_ml_pipeline:
                try:
                    ml_results = await self._get_ml_recommendations(
                        query=query,
                        user_id=self.config.user_id,
                        tags=tags
                    )
                except Exception as e:
                    logger.warning(f"ML Pipeline 推薦失敗: {e}")
            
            # 4. 結果整合和排序
            combined_results = self._combine_results(
                vector_results=vector_results,
                ml_results=ml_results,
                tags=tags
            )
            
            # 5. 轉換為 SearchResult 格式
            search_results = self._convert_to_search_results(combined_results)
            
            logger.info(f"搜尋完成，返回 {len(search_results)} 個結果")
            return search_results
            
        except Exception as e:
            logger.error(f"RAG 向量搜尋失敗: {e}")
            return []
    
    async def _get_ml_recommendations(self, 
                                    query: str, 
                                    user_id: int,
                                    tags: List[str]) -> List[Dict[str, Any]]:
        """獲取 ML Pipeline 推薦結果"""
        if not self.ml_recommender:
            return []
        
        try:
            # 構建推薦請求
            request_data = {
                "user_id": user_id,
                "query": query,
                "tags": tags,
                "top_k": self.config.top_k
            }
            
            # 調用 ML Pipeline 推薦服務
            recommendations = await self.ml_recommender.get_recommendations(request_data)
            
            return recommendations or []
            
        except Exception as e:
            logger.error(f"ML Pipeline 推薦請求失敗: {e}")
            return []
    
    def _combine_results(self, 
                        vector_results: List[VectorSearchResult],
                        ml_results: List[Dict[str, Any]],
                        tags: List[str]) -> List[Dict[str, Any]]:
        """整合向量搜尋和 ML 推薦結果"""
        combined = []
        
        # 處理向量搜尋結果
        for result in vector_results:
            combined.append({
                "chunk_id": result.chunk_id,
                "chunk_text": result.chunk_text,
                "similarity_score": result.similarity_score,
                "source": "vector_search",
                "metadata": result.metadata,
                "tags": result.tags,
                "relevance_score": result.similarity_score
            })
        
        # 處理 ML 推薦結果
        for result in ml_results:
            combined.append({
                "chunk_id": result.get("chunk_id", ""),
                "chunk_text": result.get("content", ""),
                "similarity_score": result.get("score", 0.0),
                "source": "ml_recommendation",
                "metadata": result.get("metadata", {}),
                "tags": result.get("tags", []),
                "relevance_score": result.get("score", 0.0)
            })
        
        # 按相關性分數排序
        combined.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # 去重（基於 chunk_id）
        seen_chunks = set()
        unique_results = []
        
        for result in combined:
            chunk_id = result["chunk_id"]
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_results.append(result)
        
        return unique_results[:self.config.top_k]
    
    def _convert_to_search_results(self, 
                                  combined_results: List[Dict[str, Any]]) -> List[SearchResult]:
        """轉換為 SearchResult 格式"""
        search_results = []
        
        for result in combined_results:
            search_result = SearchResult(
                chunk_id=result["chunk_id"],
                content=result["chunk_text"],
                similarity_score=result["similarity_score"],
                source=result["source"],
                metadata=result["metadata"],
                tags_used=result["tags"],
                confidence=result["relevance_score"],
                timestamp=datetime.now()
            )
            search_results.append(search_result)
        
        return search_results
    
    def get_tag_categories(self) -> List[str]:
        """獲取可用的標籤類別"""
        if not self.text_processor or not self.text_processor.tag_processor:
            return ["商業", "教育", "科技", "娛樂", "新聞"]
        
        categories = set()
        for tag_info in self.text_processor.tag_processor.tag_info_map.values():
            if tag_info.category:
                categories.add(tag_info.category)
        
        return list(categories)
    
    def is_configured(self) -> bool:
        """檢查是否正確配置"""
        return (
            self.vector_search.is_available() if self.config.use_milvus else True
        ) and (
            self.ml_recommender is not None if self.config.use_ml_pipeline else True
        )


# 工廠函數
def create_rag_vector_search(config: Optional[RAGSearchConfig] = None) -> RAGVectorSearch:
    """創建 RAG 向量搜尋服務"""
    return RAGVectorSearch(config)


# 導出主要類別
__all__ = [
    'RAGSearchConfig',
    'RAGVectorSearch',
    'create_rag_vector_search'
]
