#!/usr/bin/env python3
"""
ML Pipeline 主模組
提供推薦系統的完整功能
"""

# 核心功能
from .core import (
    PodcastRecommender,
    GNNPodcastRecommender,
    HybridGNNRecommender,
    Recommender,
    RecommenderData,
    RecommenderEvaluator,
    RecommenderSystem
)

# 服務層
from .services import RecommendationService

# 工具層
from .utils import EmbeddingDataLoader

# 配置
from .config import get_recommender_config

__version__ = "1.0.0"
__author__ = "Podwise Team"

__all__ = [
    # 核心類別
    'PodcastRecommender',
    'GNNPodcastRecommender',
    'HybridGNNRecommender',
    'Recommender',
    'RecommenderData',
    'RecommenderEvaluator',
    'RecommenderSystem',
    
    # 服務類別
    'RecommendationService',
    
    # 工具類別
    'EmbeddingDataLoader',
    
    # 配置函數
    'get_recommender_config'
] 