#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Cleaning Module - 資料清理模組

提供統一的資料清理介面，支援多種資料類型和清理策略。
符合 Google Clean Code 原則，採用 OOP 設計模式。

主要功能：
- 通用資料清理器
- 特殊資料清理器（如股癌資料）
- 批次處理
- 資料庫匯入
- 配置管理

使用範例：
    from data_cleaning import DataCleaningFactory
    
    # 建立清理器
    factory = DataCleaningFactory()
    cleaner = factory.create_cleaner('episode')
    
    # 清理資料
    cleaned_data = cleaner.clean(data)
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

# 核心模組
from .core.base_cleaner import BaseCleaner
from .core.episode_cleaner import EpisodeCleaner
from .core.podcast_cleaner import PodcastCleaner
from .core.youtube_cleaner import YouTubeCleaner
from .core.longtext_cleaner import LongTextCleaner
from .core.mongo_cleaner import MongoCleaner
from .core.unified_cleaner import UnifiedCleaner

# 特殊清理器
from .stock_cancer.stock_cancer_cleaner import StockCancerCleaner

# 服務層
from .services.cleaner_orchestrator import CleanerOrchestrator
from .services.cleanup_service import CleanupService

# 配置
from .config.config import Config, DatabaseConfig

# 工具
from .utils.data_extractor import DataExtractor
from .utils.db_utils import DBUtils
from .utils.file_format_detector import FileFormatDetector

# 資料庫匯入
from .database.postgresql_inserter import PostgreSQLInserter
from .database.batch_inserter import BatchPostgreSQLInserter

__version__ = "2.0.0"
__author__ = "Podwise Team"

# 支援的清理器類型
SUPPORTED_CLEANERS = {
    'episode': EpisodeCleaner,
    'podcast': PodcastCleaner,
    'youtube': YouTubeCleaner,
    'longtext': LongTextCleaner,
    'mongo': MongoCleaner,
    'stock_cancer': StockCancerCleaner,
    'unified': UnifiedCleaner,
}

class DataCleaningFactory:
    """資料清理器工廠類別
    
    提供統一的清理器建立介面，支援不同類型的資料清理需求。
    """
    
    def __init__(self, config: Optional[Config] = None):
        """初始化工廠
        
        Args:
            config: 配置物件，如果為 None 則使用預設配置
        """
        self.config = config or Config()
        self._cleaners = {}
    
    def create_cleaner(self, cleaner_type: str, **kwargs) -> BaseCleaner:
        """建立指定類型的清理器
        
        Args:
            cleaner_type: 清理器類型，支援的值見 SUPPORTED_CLEANERS
            **kwargs: 傳遞給清理器的額外參數
            
        Returns:
            對應類型的清理器實例
            
        Raises:
            ValueError: 當清理器類型不支援時
        """
        if cleaner_type not in SUPPORTED_CLEANERS:
            raise ValueError(f"不支援的清理器類型: {cleaner_type}。"
                           f"支援的類型: {list(SUPPORTED_CLEANERS.keys())}")
        
        # 如果已經建立過，直接返回快取實例
        if cleaner_type in self._cleaners:
            return self._cleaners[cleaner_type]
        
        # 建立新的清理器實例
        cleaner_class = SUPPORTED_CLEANERS[cleaner_type]
        cleaner = cleaner_class(**kwargs)
        
        # 快取實例
        self._cleaners[cleaner_type] = cleaner
        
        return cleaner
    
    def get_orchestrator(self) -> CleanerOrchestrator:
        """取得清理協調器
        
        Returns:
            清理協調器實例
        """
        return CleanerOrchestrator()
    
    def get_cleanup_service(self) -> CleanupService:
        """取得清理服務
        
        Returns:
            清理服務實例
        """
        return CleanupService(self.config)

class DataCleaningManager:
    """資料清理管理器
    
    提供高層級的資料清理管理功能，整合多個清理器和服務。
    """
    
    def __init__(self, config: Optional[Config] = None):
        """初始化管理器
        
        Args:
            config: 配置物件
        """
        self.config = config or Config()
        self.factory = DataCleaningFactory(config)
        self.orchestrator = self.factory.get_orchestrator()
        self.cleanup_service = self.factory.get_cleanup_service()
    
    def clean_episode_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理單個 episode 資料
        
        Args:
            data: 原始 episode 資料
            
        Returns:
            清理後的資料
        """
        cleaner = self.factory.create_cleaner('episode')
        return cleaner.clean(data)
    
    def clean_podcast_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理單個 podcast 資料
        
        Args:
            data: 原始 podcast 資料
            
        Returns:
            清理後的資料
        """
        cleaner = self.factory.create_cleaner('podcast')
        return cleaner.clean(data)
    
    def clean_stock_cancer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理股癌資料
        
        Args:
            data: 原始股癌資料
            
        Returns:
            清理後的資料
        """
        cleaner = self.factory.create_cleaner('stock_cancer')
        return cleaner.clean(data)
    
    def batch_clean_files(self, file_paths: List[str], 
                         output_dir: Optional[str] = None) -> List[str]:
        """批次清理檔案
        
        Args:
            file_paths: 檔案路徑列表
            output_dir: 輸出目錄，如果為 None 則使用預設目錄
            
        Returns:
            清理後的檔案路徑列表
        """
        return self.orchestrator.batch_clean_files(file_paths, output_dir)
    
    def clean_file(self, file_path: str, 
                   output_path: Optional[str] = None) -> str:
        """清理單個檔案
        
        Args:
            file_path: 輸入檔案路徑
            output_path: 輸出檔案路徑，如果為 None 則自動生成
            
        Returns:
            清理後的檔案路徑
        """
        return self.orchestrator.clean_file(file_path, output_path)

# 便利函數
def create_cleaner(cleaner_type: str, **kwargs) -> BaseCleaner:
    """建立清理器的便利函數
    
    Args:
        cleaner_type: 清理器類型
        **kwargs: 額外參數
        
    Returns:
        清理器實例
    """
    factory = DataCleaningFactory()
    return factory.create_cleaner(cleaner_type, **kwargs)

def clean_episode(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理 episode 資料的便利函數
    
    Args:
        data: 原始資料
        
    Returns:
        清理後的資料
    """
    cleaner = create_cleaner('episode')
    return cleaner.clean(data)

def clean_podcast(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理 podcast 資料的便利函數
    
    Args:
        data: 原始資料
        
    Returns:
        清理後的資料
    """
    cleaner = create_cleaner('podcast')
    return cleaner.clean(data)

def clean_stock_cancer(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理股癌資料的便利函數
    
    Args:
        data: 原始資料
        
    Returns:
        清理後的資料
    """
    cleaner = create_cleaner('stock_cancer')
    return cleaner.clean(data)

# 匯出主要類別和函數
__all__ = [
    # 核心類別
    'DataCleaningFactory',
    'DataCleaningManager',
    'BaseCleaner',
    'EpisodeCleaner',
    'PodcastCleaner',
    'YouTubeCleaner',
    'LongTextCleaner',
    'MongoCleaner',
    'StockCancerCleaner',
    
    # 服務類別
    'CleanerOrchestrator',
    'CleanupService',
    
    # 配置類別
    'Config',
    'DatabaseConfig',
    
    # 工具類別
    'DataExtractor',
    'DBUtils',
    'FileFormatDetector',
    
    # 資料庫類別
    'PostgreSQLInserter',
    'BatchPostgreSQLInserter',
    
    # 便利函數
    'create_cleaner',
    'clean_episode',
    'clean_podcast',
    'clean_stock_cancer',
    
    # 常數
    'SUPPORTED_CLEANERS',
] 