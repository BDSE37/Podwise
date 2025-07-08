#!/usr/bin/env python3
"""
ML Pipeline 核心模組
提供推薦系統的核心功能
"""

# 整合推薦引擎
from .recommender import RecommenderEngine

__all__ = [
    'RecommenderEngine'
] 