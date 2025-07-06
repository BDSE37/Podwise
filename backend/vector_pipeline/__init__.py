"""
Vector Pipeline 模組
提供完整的資料處理流程：MongoDB → 切分 → 標籤 → PostgreSQL → 向量化 → Milvus

重構後架構：
- PipelineOrchestrator: 主要協調器
- Core 模組: 核心功能組件
- 整合 data_cleaning 模組的清理功能
- 移除重複的處理器，統一使用 OOP 架構
"""

from .pipeline_orchestrator import PipelineOrchestrator, ProcessedChunk
from .core import (
    MongoDBProcessor, MongoDocument,
    PostgreSQLMapper, EpisodeMetadata,
    TextChunker, TextChunk,
    VectorProcessor,
    MilvusWriter
)

# 主要匯出 - 統一入口點
__all__ = [
    'PipelineOrchestrator',  # 主要協調器
    'ProcessedChunk',        # 處理結果資料類別
    # Core 組件
    'MongoDBProcessor',      # MongoDB 處理（整合 data_cleaning）
    'MongoDocument',         # MongoDB 文檔類別
    'PostgreSQLMapper',      # PostgreSQL 映射
    'EpisodeMetadata',       # Episode 元資料類別
    'TextChunker',           # 文本切分器
    'TextChunk',             # 文本塊類別
    'VectorProcessor',       # 向量處理器
    'MilvusWriter'           # Milvus 寫入器
]

__version__ = "3.1.0"  # 整合 data_cleaning 版本 