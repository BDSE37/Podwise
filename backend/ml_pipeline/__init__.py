#!/usr/bin/env python3
"""
ML Pipeline 主模組
提供推薦系統的完整功能
"""

# 核心功能
from .core import RecommenderEngine

# 服務層
from .services.api_service import RecommendationService

# 配置
from .config import get_recommender_config

__version__ = "1.0.0"
__author__ = "Podwise Team"

__all__ = [
    'RecommenderEngine',
    'RecommendationService',
    'get_recommender_config'
] 