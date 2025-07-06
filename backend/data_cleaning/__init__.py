#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PodWise Data Cleaning 模組

提供統一的資料清理功能，支援 MongoDB、PostgreSQL 等資料源。

Author: Podri Team
License: MIT
"""

# 核心清理器
from .core.base_cleaner import BaseCleaner
from .core.mongo_cleaner import MongoCleaner
from .core.stock_cancer_cleaner import StockCancerCleaner
from .core.longtext_cleaner import LongTextCleaner
from .core.episode_cleaner import EpisodeCleaner
from .core.podcast_cleaner import PodcastCleaner

# 服務層
from .services.cleaner_orchestrator import CleanerOrchestrator
from .services.cleanup_service import CleanupService

# 工具函數
from .utils.data_extractor import DataExtractor
from .utils.db_utils import DBUtils
from .utils.file_format_detector import FileFormatDetector

__version__ = "1.0.0"
__author__ = "Podri Team"

# 便捷的 import 介面
__all__ = [
    # 核心清理器
    "BaseCleaner",
    "MongoCleaner", 
    "StockCancerCleaner",
    "LongTextCleaner",
    "EpisodeCleaner",
    "PodcastCleaner",
    
    # 服務層
    "CleanerOrchestrator",
    "CleanupService",
    
    # 工具函數
    "DataExtractor",
    "DBUtils", 
    "FileFormatDetector"
] 