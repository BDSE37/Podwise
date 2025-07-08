#!/usr/bin/env python3
"""
Podwise 統一工具模組

提供給所有模組使用的共用工具：
- 文本處理 (text_processing)
- 向量搜尋 (vector_search)
- 共用工具 (common_utils)
- 環境配置 (env_config)
- 日誌配置 (logging_config)

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 1.0.0
"""

# 導入共用工具
from .common_utils import (
    DictToAttrRecursive,
    clean_path,
    normalize_text,
    safe_get,
    ensure_directory,
    validate_file_path,
    get_file_extension,
    format_file_size,
    create_logger,
    retry_on_failure,
    is_empty,
    remove_duplicates
)

# 導入文本處理工具
from .text_processing import (
    TextChunk,
    TagInfo,
    TextChunker,
    TagExtractor,
    BaseTextChunker,
    SemanticTextChunker,
    UnifiedTagProcessor,
    TextProcessor,
    EmbeddingProcessor,
    create_text_processor
)

# 導入向量搜尋工具
from .vector_search import (
    VectorSearchResult,
    VectorSearchEngine,
    MilvusVectorSearch,
    VectorSimilarityCalculator,
    UnifiedVectorSearch,
    create_vector_search
)

# 導入環境配置
from .env_config import PodriConfig

# 導入日誌配置
from .logging_config import setup_logging

# 版本資訊
__version__ = "1.0.0"
__author__ = "Podwise Team"
__description__ = "Podwise 統一工具模組"

# 導出所有公開介面
__all__ = [
    # 共用工具
    'DictToAttrRecursive',
    'clean_path',
    'normalize_text',
    'safe_get',
    'ensure_directory',
    'validate_file_path',
    'get_file_extension',
    'format_file_size',
    'create_logger',
    'retry_on_failure',
    'is_empty',
    'remove_duplicates',
    
    # 文本處理
    'TextChunk',
    'TagInfo',
    'TextChunker',
    'TagExtractor',
    'BaseTextChunker',
    'SemanticTextChunker',
    'UnifiedTagProcessor',
    'TextProcessor',
    'EmbeddingProcessor',
    'create_text_processor',
    
    # 向量搜尋
    'VectorSearchResult',
    'VectorSearchEngine',
    'MilvusVectorSearch',
    'VectorSimilarityCalculator',
    'UnifiedVectorSearch',
    'create_vector_search',
    
    # 環境配置
    'PodriConfig',
    
    # 日誌配置
    'setup_logging'
] 