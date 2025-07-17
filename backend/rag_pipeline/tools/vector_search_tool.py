#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Pipeline 向量搜尋工具

整合向量搜尋功能到 RAG Pipeline，提供：
- Milvus 向量搜尋
- 向量相似度計算
- 搜尋結果格式化
- 與 RAG Pipeline 的無縫整合

Author: Podwise Team
License: MIT
"""

import os
import sys
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 導入配置
try:
    from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG
except ImportError:
    POSTGRES_CONFIG = {}
    MINIO_CONFIG = {}

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """向量搜尋結果數據類"""
    chunk_id: str
    chunk_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    tags: List[str]
    episode_title: str = ""
    podcast_name: str = ""
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


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
                    tags=hit.entity.get("tags", []),
                    episode_title=hit.entity.get("episode_title", ""),
                    podcast_name=hit.entity.get("podcast_name", "")
                )
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return []
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return self.collection is not None


class VectorSearchTool:
    """RAG Pipeline 向量搜尋工具"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 19530,
                 collection_name: str = "podcast_chunks",
                 similarity_threshold: float = 0.7):
        """
        初始化向量搜尋工具
        
        Args:
            host: Milvus 主機
            port: Milvus 端口
            collection_name: 集合名稱
            similarity_threshold: 相似度閾值
        """
        self.search_engine = MilvusVectorSearch(host, port, collection_name)
        self.similarity_threshold = similarity_threshold
        self.similarity_calculator = VectorSimilarityCalculator()
        
        logger.info(f"向量搜尋工具初始化完成，閾值: {similarity_threshold}")
    
    def search_by_vector(self, 
                        query_vector: np.ndarray, 
                        top_k: int = 5,
                        filter_threshold: bool = True) -> List[VectorSearchResult]:
        """
        根據向量搜尋
        
        Args:
            query_vector: 查詢向量
            top_k: 返回結果數量
            filter_threshold: 是否過濾低相似度結果
            
        Returns:
            搜尋結果列表
        """
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
        
        logger.info(f"向量搜尋完成，找到 {len(results)} 個結果")
        return results
    
    def search_by_text(self, 
                      query_text: str, 
                      embedding_model,
                      top_k: int = 5) -> List[VectorSearchResult]:
        """
        根據文本搜尋
        
        Args:
            query_text: 查詢文本
            embedding_model: 嵌入模型
            top_k: 返回結果數量
            
        Returns:
            搜尋結果列表
        """
        try:
            # 將文本轉換為向量
            if hasattr(embedding_model, 'encode'):
                query_vector = embedding_model.encode([query_text])
            elif hasattr(embedding_model, 'get_embeddings'):
                query_vector = embedding_model.get_embeddings([query_text])
            else:
                logger.error("嵌入模型不支援 encode 或 get_embeddings 方法")
                return []
            
            if query_vector is None or len(query_vector) == 0:
                return []
            
            return self.search_by_vector(query_vector[0], top_k)
            
        except Exception as e:
            logger.error(f"文本向量搜尋失敗: {e}")
            return []
    
    def batch_search(self, 
                    query_vectors: List[np.ndarray], 
                    top_k: int = 5) -> List[List[VectorSearchResult]]:
        """
        批次向量搜尋
        
        Args:
            query_vectors: 查詢向量列表
            top_k: 返回結果數量
            
        Returns:
            搜尋結果列表的列表
        """
        results = []
        for i, query_vector in enumerate(query_vectors):
            search_results = self.search_by_vector(query_vector, top_k)
            results.append(search_results)
            logger.info(f"批次搜尋 {i+1}/{len(query_vectors)} 完成")
        return results
    
    def calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray, method: str = "cosine") -> float:
        """
        計算兩個向量的相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            method: 相似度計算方法 ("cosine", "euclidean", "inner_product")
            
        Returns:
            相似度分數
        """
        if method == "cosine":
            return self.similarity_calculator.cosine_similarity(vec1, vec2)
        elif method == "euclidean":
            return self.similarity_calculator.euclidean_distance(vec1, vec2)
        elif method == "inner_product":
            return self.similarity_calculator.inner_product(vec1, vec2)
        else:
            logger.warning(f"不支援的相似度計算方法: {method}")
            return 0.0
    
    def filter_results_by_similarity(self, 
                                   results: List[VectorSearchResult], 
                                   threshold: Optional[float] = None) -> List[VectorSearchResult]:
        """
        根據相似度過濾結果
        
        Args:
            results: 搜尋結果列表
            threshold: 相似度閾值，如果為 None 則使用預設閾值
            
        Returns:
            過濾後的結果列表
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        filtered_results = [
            result for result in results 
            if result.similarity_score >= threshold
        ]
        
        logger.info(f"過濾結果: {len(results)} -> {len(filtered_results)}")
        return filtered_results
    
    def get_search_statistics(self, results: List[VectorSearchResult]) -> Dict[str, Any]:
        """
        獲取搜尋統計資訊
        
        Args:
            results: 搜尋結果列表
            
        Returns:
            統計資訊字典
        """
        if not results:
            return {
                "total_results": 0,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "unique_podcasts": 0,
                "unique_episodes": 0
            }
        
        similarities = [r.similarity_score for r in results]
        podcasts = set(r.podcast_name for r in results if r.podcast_name)
        episodes = set(r.episode_title for r in results if r.episode_title)
        
        return {
            "total_results": len(results),
            "avg_similarity": float(np.mean(similarities)),
            "max_similarity": float(np.max(similarities)),
            "min_similarity": float(np.min(similarities)),
            "unique_podcasts": len(podcasts),
            "unique_episodes": len(episodes)
        }
    
    def is_available(self) -> bool:
        """檢查搜尋服務是否可用"""
        return self.search_engine.is_available()
    
    def get_health_status(self) -> Dict[str, Any]:
        """獲取健康狀態"""
        return {
            "service": "VectorSearchTool",
            "status": "healthy" if self.is_available() else "unhealthy",
            "milvus_connected": self.search_engine.is_available(),
            "collection_name": self.search_engine.collection_name,
            "similarity_threshold": self.similarity_threshold,
            "timestamp": datetime.now().isoformat()
        }


# 全域向量搜尋工具實例
_vector_search_tool: Optional[VectorSearchTool] = None


def get_vector_search_tool(host: str = "localhost",
                          port: int = 19530,
                          collection_name: str = "podcast_chunks",
                          similarity_threshold: float = 0.7) -> VectorSearchTool:
    """
    獲取向量搜尋工具實例
    
    Args:
        host: Milvus 主機
        port: Milvus 端口
        collection_name: 集合名稱
        similarity_threshold: 相似度閾值
        
    Returns:
        向量搜尋工具實例
    """
    global _vector_search_tool
    
    if _vector_search_tool is None:
        _vector_search_tool = VectorSearchTool(
            host=host,
            port=port,
            collection_name=collection_name,
            similarity_threshold=similarity_threshold
        )
    
    return _vector_search_tool


def search_by_vector(query_vector: np.ndarray, 
                    top_k: int = 5,
                    similarity_threshold: float = 0.7) -> List[VectorSearchResult]:
    """
    便捷的向量搜尋函數
    
    Args:
        query_vector: 查詢向量
        top_k: 返回結果數量
        similarity_threshold: 相似度閾值
        
    Returns:
        搜尋結果列表
    """
    tool = get_vector_search_tool(similarity_threshold=similarity_threshold)
    return tool.search_by_vector(query_vector, top_k)


def search_by_text(query_text: str,
                  embedding_model,
                  top_k: int = 5,
                  similarity_threshold: float = 0.7) -> List[VectorSearchResult]:
    """
    便捷的文本搜尋函數
    
    Args:
        query_text: 查詢文本
        embedding_model: 嵌入模型
        top_k: 返回結果數量
        similarity_threshold: 相似度閾值
        
    Returns:
        搜尋結果列表
    """
    tool = get_vector_search_tool(similarity_threshold=similarity_threshold)
    return tool.search_by_text(query_text, embedding_model, top_k)


# 測試函數
def test_vector_search():
    """測試向量搜尋功能"""
    try:
        tool = get_vector_search_tool()
        
        # 檢查服務狀態
        health = tool.get_health_status()
        print(f"健康狀態: {health}")
        
        if tool.is_available():
            print("向量搜尋服務可用")
        else:
            print("向量搜尋服務不可用")
            
    except Exception as e:
        print(f"測試失敗: {e}")


if __name__ == "__main__":
    test_vector_search() 