#!/usr/bin/env python3
"""
KNN 推薦工具模組

此模組實現基於向量相似度的 K-Nearest Neighbors 推薦算法，
支援商業和教育類別的 Podcast 推薦，提供高精度的內容匹配。

主要功能：
- 基於向量相似度的 KNN 推薦
- 支援多種相似度度量方法
- 類別過濾和統計分析
- 推薦結果的詳細推理說明
- 性能監控和優化

作者: Podwise Team
版本: 2.0.0
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import json
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PodcastItem:
    """
    Podcast 項目數據類別
    
    此類別封裝了 Podcast 項目的完整資訊，包含基本屬性、
    向量表示和元數據。
    
    Attributes:
        rss_id: RSS 識別碼
        title: Podcast 標題
        description: 描述內容
        category: 類別 ("商業" 或 "教育")
        tags: 標籤列表
        vector: 向量表示
        updated_at: 更新時間
        confidence: 信心值
    """
    rss_id: str
    title: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    vector: Optional[np.ndarray] = None
    updated_at: Optional[str] = None
    confidence: float = 0.0
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")
        
        if self.category not in ["商業", "教育"]:
            raise ValueError("無效的類別值")


@dataclass(frozen=True)
class RecommendationResult:
    """
    推薦結果數據類別
    
    此類別封裝了 KNN 推薦的完整結果，包含推薦項目、
    相似度分數和處理元數據。
    
    Attributes:
        recommendations: 推薦的 Podcast 項目列表
        query_vector: 查詢向量
        similarity_scores: 相似度分數列表
        category: 推薦類別
        confidence: 整體信心值
        reasoning: 推薦推理說明
        processing_time: 處理時間
    """
    recommendations: List[PodcastItem]
    query_vector: np.ndarray
    similarity_scores: List[float] = field(default_factory=list)
    category: str = "混合"
    confidence: float = 0.0
    reasoning: str = ""
    processing_time: float = 0.0
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")
        
        if self.processing_time < 0:
            raise ValueError("處理時間不能為負數")


class SimilarityMetric(ABC):
    """相似度度量抽象基類"""
    
    @abstractmethod
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """計算兩個向量之間的相似度"""
        pass
    
    @abstractmethod
    def get_metric_name(self) -> str:
        """獲取度量方法名稱"""
        pass


class CosineSimilarity(SimilarityMetric):
    """餘弦相似度度量"""
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """計算餘弦相似度"""
        return float(cosine_similarity([vector1], [vector2])[0][0])
    
    def get_metric_name(self) -> str:
        return "cosine"


class EuclideanSimilarity(SimilarityMetric):
    """歐幾里得距離相似度度量"""
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """計算基於歐幾里得距離的相似度"""
        distance = np.linalg.norm(vector1 - vector2)
        return float(1.0 / (1.0 + distance))
    
    def get_metric_name(self) -> str:
        return "euclidean"


class ManhattanSimilarity(SimilarityMetric):
    """曼哈頓距離相似度度量"""
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """計算基於曼哈頓距離的相似度"""
        distance = np.sum(np.abs(vector1 - vector2))
        return float(1.0 / (1.0 + distance))
    
    def get_metric_name(self) -> str:
        return "manhattan"


class SimilarityMetricFactory:
    """相似度度量工廠類別"""
    
    _metrics = {
        "cosine": CosineSimilarity,
        "euclidean": EuclideanSimilarity,
        "manhattan": ManhattanSimilarity
    }
    
    @classmethod
    def create_metric(cls, metric_name: str) -> SimilarityMetric:
        """
        創建相似度度量實例
        
        Args:
            metric_name: 度量方法名稱
            
        Returns:
            SimilarityMetric 實例
            
        Raises:
            ValueError: 當度量方法名稱無效時
        """
        if metric_name not in cls._metrics:
            raise ValueError(f"不支援的度量方法: {metric_name}")
        
        return cls._metrics[metric_name]()


class RecommendationAnalyzer:
    """推薦分析器"""
    
    def __init__(self) -> None:
        """初始化推薦分析器"""
        pass
    
    def generate_reasoning(self, recommendations: List[PodcastItem], 
                          similarity_scores: List[float], 
                          category_filter: Optional[str],
                          k: int,
                          metric_name: str) -> str:
        """
        生成推薦推理說明
        
        Args:
            recommendations: 推薦項目列表
            similarity_scores: 相似度分數列表
            category_filter: 類別過濾器
            k: KNN 參數
            metric_name: 度量方法名稱
            
        Returns:
            推理說明文字
        """
        if not recommendations:
            return "沒有找到相關的 Podcast 推薦"
        
        category = category_filter or "混合類別"
        avg_similarity = np.mean(similarity_scores)
        
        # 統計類別分布
        category_counts = self._count_categories(recommendations)
        category_distribution = self._format_category_distribution(category_counts)
        
        reasoning = f"""
基於 KNN 算法 ({k}-近鄰, {metric_name}) 的 {category} 推薦結果：

📊 相似度統計：
- 平均相似度: {avg_similarity:.3f}
- 最高相似度: {max(similarity_scores):.3f}
- 最低相似度: {min(similarity_scores):.3f}

📂 類別分布: {category_distribution}

🎯 推薦理由: 根據向量相似度匹配，選擇最相關的 {len(recommendations)} 個 Podcast
        """.strip()
        
        return reasoning
    
    def _count_categories(self, recommendations: List[PodcastItem]) -> Dict[str, int]:
        """統計類別分布"""
        category_counts = {}
        for item in recommendations:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        return category_counts
    
    def _format_category_distribution(self, category_counts: Dict[str, int]) -> str:
        """格式化類別分布"""
        return ", ".join([f"{cat}: {count}個" for cat, count in category_counts.items()])


class KNNRecommender:
    """
    K-Nearest Neighbors 推薦器
    
    此類別實現基於向量相似度的 KNN 推薦算法，支援多種
    相似度度量方法和類別過濾功能。
    
    主要功能：
    - 基於向量相似度的 KNN 推薦
    - 支援多種相似度度量方法
    - 類別過濾和統計分析
    - 推薦結果的詳細推理說明
    - 性能監控和優化
    """
    
    def __init__(self, k: int = 5, metric: str = "cosine") -> None:
        """
        初始化 KNN 推薦器
        
        Args:
            k: 鄰居數量
            metric: 相似度度量方法 ("cosine", "euclidean", "manhattan")
            
        Raises:
            ValueError: 當參數無效時
        """
        if k <= 0:
            raise ValueError("k 必須大於 0")
        
        self.k = k
        self.metric = metric
        self.similarity_metric = SimilarityMetricFactory.create_metric(metric)
        
        # 初始化組件
        self.nn_model: Optional[NearestNeighbors] = None
        self.podcast_items: List[PodcastItem] = []
        self.vectors: List[np.ndarray] = []
        self.categories: List[str] = []
        self.recommendation_analyzer = RecommendationAnalyzer()
        
        # 初始化 KNN 模型
        self._initialize_model()
        
        logger.info(f"KNN 推薦器初始化完成 (k={k}, metric={metric})")
    
    def _initialize_model(self) -> None:
        """初始化 KNN 模型"""
        self.nn_model = NearestNeighbors(
            n_neighbors=self.k,
            metric=self.metric,
            algorithm='auto'
        )
    
    def add_podcast_items(self, items: List[PodcastItem]) -> None:
        """
        添加 Podcast 項目到推薦系統
        
        Args:
            items: Podcast 項目列表
            
        Raises:
            ValueError: 當項目列表為空或項目無效時
        """
        if not items:
            raise ValueError("項目列表不能為空")
        
        valid_items = []
        for item in items:
            if item.vector is not None:
                valid_items.append(item)
                self.podcast_items.append(item)
                self.vectors.append(item.vector)
                self.categories.append(item.category)
        
        # 重新訓練模型
        if self.vectors and self.nn_model is not None:
            vectors_array = np.array(self.vectors)
            self.nn_model.fit(vectors_array)
            logger.info(f"已添加 {len(valid_items)} 個有效 Podcast 項目，總計 {len(self.podcast_items)} 個")
    
    def recommend(self, query_vector: np.ndarray, 
                 category_filter: Optional[str] = None, 
                 top_k: int = 3) -> RecommendationResult:
        """
        執行 KNN 推薦
        
        Args:
            query_vector: 查詢向量
            category_filter: 類別過濾器 ("商業" 或 "教育")
            top_k: 返回推薦數量
            
        Returns:
            RecommendationResult: 推薦結果
            
        Raises:
            ValueError: 當參數無效時
        """
        if top_k <= 0:
            raise ValueError("top_k 必須大於 0")
        
        start_time = time.time()
        
        # 檢查是否有可用的項目
        if len(self.podcast_items) == 0:
            return self._create_empty_result(query_vector, category_filter, start_time)
        
        # 檢查模型是否已初始化
        if self.nn_model is None:
            return self._create_empty_result(query_vector, category_filter, start_time, 
                                           "KNN 模型未初始化")
        
        # 執行 KNN 搜尋
        distances, indices = self.nn_model.kneighbors([query_vector])
        
        # 獲取候選項目
        candidates = self._get_candidates(indices[0], distances[0], category_filter)
        
        # 排序並選擇 top_k
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:top_k]
        
        # 構建結果
        recommendations = [item for item, _ in top_candidates]
        similarity_scores = [score for _, score in top_candidates]
        
        # 計算整體信心值
        confidence = float(np.mean(similarity_scores)) if similarity_scores else 0.0
        
        # 生成推理說明
        reasoning = self.recommendation_analyzer.generate_reasoning(
            recommendations, similarity_scores, category_filter, self.k, self.metric
        )
        
        processing_time = time.time() - start_time
        
        return RecommendationResult(
            recommendations=recommendations,
            query_vector=query_vector,
            similarity_scores=similarity_scores,
            category=category_filter or "混合",
            confidence=confidence,
            reasoning=reasoning,
            processing_time=processing_time
        )
    
    def _create_empty_result(self, query_vector: np.ndarray, 
                           category_filter: Optional[str], 
                           start_time: float,
                           reason: str = "沒有可用的 Podcast 項目") -> RecommendationResult:
        """創建空結果"""
        return RecommendationResult(
            recommendations=[],
            query_vector=query_vector,
            similarity_scores=[],
            category=category_filter or "未知",
            confidence=0.0,
            reasoning=reason,
            processing_time=time.time() - start_time
        )
    
    def _get_candidates(self, indices: np.ndarray, distances: np.ndarray, 
                       category_filter: Optional[str]) -> List[Tuple[PodcastItem, float]]:
        """獲取候選項目"""
        candidates = []
        for i, idx in enumerate(indices):
            item = self.podcast_items[idx]
            similarity = 1 - distances[i]  # 轉換距離為相似度
            
            # 應用類別過濾
            if category_filter and item.category != category_filter:
                continue
            
            candidates.append((item, similarity))
        
        return candidates
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """
        獲取類別統計資訊
        
        Returns:
            類別統計字典
        """
        if not self.categories:
            return {"total": 0, "categories": {}}
        
        category_counts = {}
        for category in self.categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total": len(self.categories),
            "categories": category_counts,
            "model_ready": self.nn_model is not None and len(self.vectors) > 0
        }
    
    def filter_by_category(self, category: str) -> List[PodcastItem]:
        """
        按類別過濾 Podcast 項目
        
        Args:
            category: 類別名稱
            
        Returns:
            過濾後的項目列表
        """
        return [item for item in self.podcast_items if item.category == category]
    
    def get_similar_items(self, item_id: str, top_k: int = 5) -> List[Tuple[PodcastItem, float]]:
        """
        獲取相似項目
        
        Args:
            item_id: 項目 ID
            top_k: 返回數量
            
        Returns:
            相似項目和相似度的元組列表
        """
        # 找到目標項目
        target_item = None
        for item in self.podcast_items:
            if item.rss_id == item_id:
                target_item = item
                break
        
        if target_item is None or target_item.vector is None:
            return []
        
        # 計算與所有項目的相似度
        similarities = []
        for item in self.podcast_items:
            if item.rss_id != item_id and item.vector is not None:
                similarity = self.similarity_metric.calculate_similarity(
                    target_item.vector, item.vector
                )
                similarities.append((item, similarity))
        
        # 排序並返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def export_recommendations_to_json(self, result: RecommendationResult, 
                                     filepath: str) -> None:
        """
        匯出推薦結果到 JSON 檔案
        
        Args:
            result: 推薦結果
            filepath: 檔案路徑
        """
        data = {
            "recommendations": [
                {
                    "rss_id": item.rss_id,
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "tags": item.tags,
                    "confidence": item.confidence,
                    "updated_at": item.updated_at
                }
                for item in result.recommendations
            ],
            "metadata": {
                "query_vector_shape": result.query_vector.shape,
                "similarity_scores": result.similarity_scores,
                "category": result.category,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "export_timestamp": str(datetime.now()),
                "version": "2.0.0"
            },
            "reasoning": result.reasoning
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"推薦結果已匯出到: {filepath}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        self.podcast_items.clear()
        self.vectors.clear()
        self.categories.clear()
        self.nn_model = None
        logger.info("已清除所有數據")


def test_knn_recommender() -> None:
    """測試 KNN 推薦器功能"""
    # 創建測試數據
    test_items = [
        PodcastItem(
            rss_id="rss_001",
            title="股癌 EP310",
            description="台股投資分析與市場趨勢",
            category="商業",
            tags=["股票", "投資", "台股", "財經"],
            vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
            updated_at="2025-01-15",
            confidence=0.9
        ),
        PodcastItem(
            rss_id="rss_002",
            title="大人學 EP110",
            description="職涯發展與個人成長指南",
            category="教育",
            tags=["職涯", "成長", "技能", "學習"],
            vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
            updated_at="2025-01-14",
            confidence=0.85
        ),
        PodcastItem(
            rss_id="rss_003",
            title="財報狗 Podcast",
            description="財報分析與投資策略",
            category="商業",
            tags=["財報", "投資", "分析", "策略"],
            vector=np.array([0.9, 0.5, 0.8, 0.6, 0.9, 0.5, 0.8, 0.6]),
            updated_at="2025-01-13",
            confidence=0.88
        )
    ]
    
    # 初始化推薦器
    recommender = KNNRecommender(k=3, metric="cosine")
    recommender.add_podcast_items(test_items)
    
    # 測試查詢
    query_vector = np.array([0.7, 0.7, 0.8, 0.8, 0.7, 0.7, 0.8, 0.8])
    
    # 執行推薦
    result = recommender.recommend(query_vector, category_filter="商業", top_k=2)
    
    print("=== KNN 推薦器測試 ===")
    print(f"查詢向量: {query_vector}")
    print(f"推薦類別: {result.category}")
    print(f"信心值: {result.confidence:.3f}")
    print(f"處理時間: {result.processing_time:.3f} 秒")
    print(f"推薦項目數量: {len(result.recommendations)}")
    print(f"推理說明: {result.reasoning}")
    
    # 顯示推薦項目
    for i, item in enumerate(result.recommendations):
        print(f"\n推薦 {i+1}: {item.title}")
        print(f"  類別: {item.category}")
        print(f"  相似度: {result.similarity_scores[i]:.3f}")
        print(f"  描述: {item.description}")


if __name__ == "__main__":
    test_knn_recommender() 