#!/usr/bin/env python3
"""
統一向量搜尋工具模組

提供給所有模組使用的向量搜尋功能：
- Milvus 向量搜尋
- 向量相似度計算
- 搜尋結果格式化

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

from .common_utils import create_logger

logger = create_logger(__name__)


@dataclass
class VectorSearchResult:
    """向量搜尋結果數據類"""
    chunk_id: str
    chunk_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    tags: List[str]


class VectorSearchEngine(Protocol):
    """向量搜尋引擎協議"""
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[VectorSearchResult]:
        """向量搜尋"""
        ...
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        ...


class MilvusVectorSearch:
    """Milvus 向量搜尋實現"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 19530,
                 collection_name: str = "podcast_chunks"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self._connect()
    
    def _connect(self):
        """連接到 Milvus"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 連接到 Milvus
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            
            # 檢查集合是否存在
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"連接到 Milvus 集合: {self.collection_name}")
            else:
                logger.warning(f"Milvus 集合不存在: {self.collection_name}")
                
        except ImportError:
            logger.warning("pymilvus 未安裝，向量搜尋功能不可用")
            self.collection = None
        except Exception as e:
            logger.error(f"連接 Milvus 失敗: {e}")
            self.collection = None
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[VectorSearchResult]:
        """向量搜尋"""
        if not self.is_available():
            return []
        
        try:
            # 執行向量搜尋
            search_params = {
                "metric_type": "IP",  # 內積相似度
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_vector.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "episode_title", "podcast_name", "tags"]
            )
            
            # 格式化結果
            search_results = []
            for hit in results[0]:
                result = VectorSearchResult(
                    chunk_id=hit.entity.get("chunk_id", ""),
                    chunk_text=hit.entity.get("chunk_text", ""),
                    similarity_score=float(hit.score),
                    metadata={
                        "episode_title": hit.entity.get("episode_title", ""),
                        "podcast_name": hit.entity.get("podcast_name", ""),
                        "distance": float(hit.distance) if hasattr(hit, 'distance') else 0.0
                    },
                    tags=hit.entity.get("tags", [])
                )
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return []
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return self.collection is not None


class VectorSimilarityCalculator:
    """向量相似度計算器"""
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算餘弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            return float(dot_product / (norm_vec1 * norm_vec2))
        except Exception as e:
            logger.error(f"計算餘弦相似度失敗: {e}")
            return 0.0
    
    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算歐幾里得距離"""
        try:
            return float(np.linalg.norm(vec1 - vec2))
        except Exception as e:
            logger.error(f"計算歐幾里得距離失敗: {e}")
            return float('inf')
    
    @staticmethod
    def inner_product(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算內積"""
        try:
            return float(np.dot(vec1, vec2))
        except Exception as e:
            logger.error(f"計算內積失敗: {e}")
            return 0.0


class UnifiedVectorSearch:
    """統一向量搜尋服務"""
    
    def __init__(self, 
                 search_engine: Optional[VectorSearchEngine] = None,
                 similarity_threshold: float = 0.7):
        self.search_engine = search_engine or MilvusVectorSearch()
        self.similarity_threshold = similarity_threshold
        self.similarity_calculator = VectorSimilarityCalculator()
    
    def search_by_vector(self, 
                        query_vector: np.ndarray, 
                        top_k: int = 5,
                        filter_threshold: bool = True) -> List[VectorSearchResult]:
        """根據向量搜尋"""
        if not self.search_engine.is_available():
            logger.warning("向量搜尋引擎不可用")
            return []
        
        results = self.search_engine.search(query_vector, top_k)
        
        # 過濾低相似度結果
        if filter_threshold:
            results = [
                result for result in results 
                if result.similarity_score >= self.similarity_threshold
            ]
        
        return results
    
    def search_by_text(self, 
                      query_text: str, 
                      embedding_model,
                      top_k: int = 5) -> List[VectorSearchResult]:
        """根據文本搜尋"""
        try:
            # 將文本轉換為向量
            query_vector = embedding_model.encode([query_text])
            if query_vector is None or len(query_vector) == 0:
                return []
            
            return self.search_by_vector(query_vector[0], top_k)
            
        except Exception as e:
            logger.error(f"文本向量搜尋失敗: {e}")
            return []
    
    def batch_search(self, 
                    query_vectors: List[np.ndarray], 
                    top_k: int = 5) -> List[List[VectorSearchResult]]:
        """批次向量搜尋"""
        results = []
        for query_vector in query_vectors:
            search_results = self.search_by_vector(query_vector, top_k)
            results.append(search_results)
        return results
    
    def is_available(self) -> bool:
        """檢查搜尋服務是否可用"""
        return self.search_engine.is_available()


def create_vector_search(host: str = "localhost",
                        port: int = 19530,
                        collection_name: str = "podcast_chunks",
                        similarity_threshold: float = 0.7) -> UnifiedVectorSearch:
    """創建向量搜尋服務工廠函數"""
    search_engine = MilvusVectorSearch(
        host=host,
        port=port,
        collection_name=collection_name
    )
    
    return UnifiedVectorSearch(
        search_engine=search_engine,
        similarity_threshold=similarity_threshold
    )


# 導出主要類別和函數
__all__ = [
    'VectorSearchResult',
    'VectorSearchEngine',
    'MilvusVectorSearch',
    'VectorSimilarityCalculator',
    'UnifiedVectorSearch',
    'create_vector_search'
] 