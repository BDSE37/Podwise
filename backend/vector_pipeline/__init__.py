"""
Vector Pipeline 套件初始化
"""

from .config.settings import VectorPipelineConfig
from .config.milvus_config import get_milvus_config, get_collection_config, get_field_schemas

__all__ = [
    'VectorPipelineConfig',
    'get_milvus_config',
    'get_collection_config',
    'get_field_schemas'
]

__version__ = "3.2.0"
__author__ = "Podri Team"
__description__ = "Vector Pipeline - 重構版本，統一的向量化處理管道" 