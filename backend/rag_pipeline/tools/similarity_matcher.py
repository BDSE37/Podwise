#!/usr/bin/env python3
"""
Similarity Matcher

餘弦相似度計算工具，用於計算向量間的相似度並提供信心值

功能：
- 餘弦相似度計算
- 向量正規化
- 信心值評估
- 批量相似度計算

作者: Podwise Team
版本: 1.0.0
"""

import logging
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """相似度計算結果"""
    similarity: float
    confidence: float
    normalized: bool = True
    vector_dimensions: int = 0


class SimilarityMatcher:
    """餘弦相似度匹配器"""
    
    def __init__(self, normalize_vectors: bool = True):
        """
        初始化相似度匹配器
        
        Args:
            normalize_vectors: 是否自動正規化向量
        """
        self.normalize_vectors = normalize_vectors
        logger.info("SimilarityMatcher 初始化完成")
    
    def calculate_cosine_similarity(self, 
                                  vector1: List[float], 
                                  vector2: List[float]) -> SimilarityResult:
        """
        計算兩個向量的餘弦相似度
        
        Args:
            vector1: 第一個向量
            vector2: 第二個向量
            
        Returns:
            SimilarityResult: 相似度結果
        """
        try:
            # 轉換為 numpy 陣列
            v1 = np.array(vector1, dtype=np.float64)
            v2 = np.array(vector2, dtype=np.float64)
            
            # 檢查向量維度
            if v1.shape != v2.shape:
                raise ValueError(f"向量維度不匹配: {v1.shape} vs {v2.shape}")
            
            # 正規化向量（如果需要）
            if self.normalize_vectors:
                v1_norm = self._normalize_vector(v1)
                v2_norm = self._normalize_vector(v2)
            else:
                v1_norm = v1
                v2_norm = v2
            
            # 計算餘弦相似度
            dot_product = np.dot(v1_norm, v2_norm)
            norm1 = np.linalg.norm(v1_norm)
            norm2 = np.linalg.norm(v2_norm)
            
            if norm1 == 0 or norm2 == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm1 * norm2)
            
            # 確保相似度在 [-1, 1] 範圍內
            similarity = max(-1.0, min(1.0, similarity))
            
            # 計算信心值（將相似度映射到 [0, 1] 範圍）
            confidence = (similarity + 1.0) / 2.0
            
            return SimilarityResult(
                similarity=similarity,
                confidence=confidence,
                normalized=self.normalize_vectors,
                vector_dimensions=len(vector1)
            )
            
        except Exception as e:
            logger.error(f"餘弦相似度計算失敗: {e}")
            return SimilarityResult(
                similarity=0.0,
                confidence=0.0,
                normalized=self.normalize_vectors,
                vector_dimensions=0
            )
    
    def calculate_batch_similarity(self, 
                                 query_vector: List[float],
                                 target_vectors: List[List[float]]) -> List[SimilarityResult]:
        """
        批量計算相似度
        
        Args:
            query_vector: 查詢向量
            target_vectors: 目標向量列表
            
        Returns:
            List[SimilarityResult]: 相似度結果列表
        """
        results = []
        
        for i, target_vector in enumerate(target_vectors):
            try:
                result = self.calculate_cosine_similarity(query_vector, target_vector)
                results.append(result)
            except Exception as e:
                logger.error(f"批量相似度計算失敗 (索引 {i}): {e}")
                results.append(SimilarityResult(
                    similarity=0.0,
                    confidence=0.0,
                    normalized=self.normalize_vectors,
                    vector_dimensions=0
                ))
        
        return results
    
    def find_top_matches(self, 
                        query_vector: List[float],
                        target_vectors: List[List[float]],
                        top_k: int = 5,
                        confidence_threshold: float = 0.7) -> List[Tuple[int, SimilarityResult]]:
        """
        找出最相似的匹配項
        
        Args:
            query_vector: 查詢向量
            target_vectors: 目標向量列表
            top_k: 返回前 k 個結果
            confidence_threshold: 信心度閾值
            
        Returns:
            List[Tuple[int, SimilarityResult]]: (索引, 相似度結果) 列表
        """
        try:
            # 計算所有相似度
            similarities = self.calculate_batch_similarity(query_vector, target_vectors)
            
            # 篩選符合閾值的結果
            valid_results = []
            for i, result in enumerate(similarities):
                if result.confidence >= confidence_threshold:
                    valid_results.append((i, result))
            
            # 按相似度排序
            valid_results.sort(key=lambda x: x[1].similarity, reverse=True)
            
            # 返回前 k 個結果
            return valid_results[:top_k]
            
        except Exception as e:
            logger.error(f"查找最佳匹配失敗: {e}")
            return []
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        正規化向量
        
        Args:
            vector: 輸入向量
            
        Returns:
            np.ndarray: 正規化後的向量
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def calculate_euclidean_distance(self, 
                                   vector1: List[float], 
                                   vector2: List[float]) -> float:
        """
        計算歐幾里得距離（輔助功能）
        
        Args:
            vector1: 第一個向量
            vector2: 第二個向量
            
        Returns:
            float: 歐幾里得距離
        """
        try:
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            return np.linalg.norm(v1 - v2)
        except Exception as e:
            logger.error(f"歐幾里得距離計算失敗: {e}")
            return float('inf')
    
    def calculate_manhattan_distance(self, 
                                   vector1: List[float], 
                                   vector2: List[float]) -> float:
        """
        計算曼哈頓距離（輔助功能）
        
        Args:
            vector1: 第一個向量
            vector2: 第二個向量
            
        Returns:
            float: 曼哈頓距離
        """
        try:
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            return np.sum(np.abs(v1 - v2))
        except Exception as e:
            logger.error(f"曼哈頓距離計算失敗: {e}")
            return float('inf')
    
    def validate_vector(self, vector: List[float]) -> bool:
        """
        驗證向量格式
        
        Args:
            vector: 輸入向量
            
        Returns:
            bool: 是否有效
        """
        try:
            if not isinstance(vector, list):
                return False
            
            if len(vector) == 0:
                return False
            
            # 檢查是否所有元素都是數字
            for element in vector:
                if not isinstance(element, (int, float)):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_vector_statistics(self, vector: List[float]) -> Dict[str, float]:
        """
        獲取向量統計資訊
        
        Args:
            vector: 輸入向量
            
        Returns:
            Dict[str, float]: 統計資訊
        """
        try:
            v = np.array(vector)
            
            return {
                "dimensions": len(vector),
                "mean": float(np.mean(v)),
                "std": float(np.std(v)),
                "min": float(np.min(v)),
                "max": float(np.max(v)),
                "norm": float(np.linalg.norm(v))
            }
            
        except Exception as e:
            logger.error(f"向量統計計算失敗: {e}")
            return {}


# 全域實例
similarity_matcher = SimilarityMatcher()


def get_similarity_matcher() -> SimilarityMatcher:
    """獲取相似度匹配器實例"""
    return similarity_matcher


def test_similarity_matcher():
    """測試相似度匹配器"""
    matcher = get_similarity_matcher()
    
    # 測試向量
    vector1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    vector2 = [1.0, 2.0, 3.0, 4.0, 5.0]  # 完全相同
    vector3 = [5.0, 4.0, 3.0, 2.0, 1.0]  # 相反
    vector4 = [0.0, 0.0, 0.0, 0.0, 0.0]  # 零向量
    
    print("測試相似度匹配器")
    print("=" * 50)
    
    # 測試相同向量
    result1 = matcher.calculate_cosine_similarity(vector1, vector2)
    print(f"相同向量相似度: {result1.similarity:.4f}, 信心度: {result1.confidence:.4f}")
    
    # 測試相反向量
    result2 = matcher.calculate_cosine_similarity(vector1, vector3)
    print(f"相反向量相似度: {result2.similarity:.4f}, 信心度: {result2.confidence:.4f}")
    
    # 測試零向量
    result3 = matcher.calculate_cosine_similarity(vector1, vector4)
    print(f"零向量相似度: {result3.similarity:.4f}, 信心度: {result3.confidence:.4f}")
    
    # 測試批量計算
    target_vectors = [vector2, vector3, vector4]
    batch_results = matcher.calculate_batch_similarity(vector1, target_vectors)
    print(f"\n批量計算結果:")
    for i, result in enumerate(batch_results):
        print(f"  向量 {i+1}: 相似度={result.similarity:.4f}, 信心度={result.confidence:.4f}")
    
    # 測試最佳匹配
    top_matches = matcher.find_top_matches(vector1, target_vectors, top_k=2, confidence_threshold=0.5)
    print(f"\n最佳匹配 (top_k=2, threshold=0.5):")
    for idx, result in top_matches:
        print(f"  索引 {idx}: 相似度={result.similarity:.4f}, 信心度={result.confidence:.4f}")
    
    # 測試向量統計
    stats = matcher.get_vector_statistics(vector1)
    print(f"\n向量統計:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_similarity_matcher() 