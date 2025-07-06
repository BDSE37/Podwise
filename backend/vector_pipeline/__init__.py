"""
Vector Pipeline 模組
提供完整的資料處理流程：MongoDB → 切分 → 標籤 → PostgreSQL → 向量化 → Milvus
"""

from .pipeline_orchestrator import PipelineOrchestrator, ProcessedChunk
from .core import (
    MongoDBProcessor, MongoDocument,
    PostgreSQLMapper, EpisodeMetadata,
    TextChunker, TextChunk,
    VectorProcessor,
    MilvusWriter
)

__all__ = [
    'PipelineOrchestrator',
    'ProcessedChunk',
    'MongoDBProcessor',
    'MongoDocument',
    'PostgreSQLMapper',
    'EpisodeMetadata',
    'TextChunker',
    'TextChunk',
    'VectorProcessor',
    'MilvusWriter'
]

__version__ = "2.0.0" 