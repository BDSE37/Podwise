"""
Vector Pipeline 模組 - 重構版本
提供完整的資料處理流程：標籤處理 → 向量化 → 搜尋
符合 Google Clean Code 原則和 OOP 架構
"""

# 配置模組
from .config.settings import VectorPipelineConfig, config
from .config.milvus_config import MilvusConfig

# 核心模組
from .core.tag_processor import UnifiedTagProcessor
from .core.text_chunker import TextChunker, TextChunk
from .core.vector_processor import VectorProcessor
from .core.milvus_writer import MilvusWriter
from .core.error_logger import ErrorLogger

# 服務模組
from .services.tagging_service import TaggingService
from .services.embedding_service import EmbeddingService
from .services.search_service import SearchService

# 工具模組
from .utils.data_quality_checker import DataQualityChecker

# 腳本模組
from .scripts.batch_processor import BatchProcessor

# 主程式
from .main_refactored import VectorPipeline

# 主要匯出 - 統一入口點
__all__ = [
    # 配置
    'VectorPipelineConfig',
    'config',
    'MilvusConfig',
    
    # 核心組件
    'UnifiedTagProcessor',
    'TextChunker',
    'TextChunk',
    'VectorProcessor',
    'MilvusWriter',
    'ErrorLogger',
    
    # 服務層
    'TaggingService',
    'EmbeddingService',
    'SearchService',
    
    # 工具
    'DataQualityChecker',
    
    # 腳本
    'BatchProcessor',
    
    # 主程式
    'VectorPipeline'
]

__version__ = "3.2.0"
__author__ = "Podri Team"
__description__ = "Vector Pipeline - 重構版本，統一的向量化處理管道" 