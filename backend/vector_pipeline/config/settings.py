"""
Vector Pipeline 統一配置
符合 Google Clean Code 原則
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VectorPipelineConfig:
    """Vector Pipeline 統一配置類別"""
    
    # 資料目錄配置
    data_dir: str = "data"
    stage1_dir: str = "data/stage1_chunking"
    stage3_dir: str = "data/stage3_tagging"
    stage4_dir: str = "data/stage4_embedding_prep"
    
    # 標籤配置
    tag_csv_path: str = "../utils/TAG_info.csv"
    max_tags_per_chunk: int = 3
    min_tags_per_chunk: int = 1
    
    # 向量化配置
    embedding_model: str = "BAAI/bge-m3"
    vector_dim: int = 1024
    batch_size: int = 100
    
    # Milvus 配置
    milvus_host: str = "192.168.32.86"
    milvus_port: str = "19530"
    collection_name: str = "podwise_chunks"
    
    # 日誌配置
    log_level: str = "INFO"
    log_file: str = "vector_pipeline.log"
    
    # 處理配置
    max_chunk_length: int = 1000
    min_chunk_length: int = 50
    chunk_overlap: int = 100
    
    def __post_init__(self):
        """初始化後處理"""
        # 確保目錄存在
        for dir_path in [self.data_dir, self.stage1_dir, self.stage3_dir, self.stage4_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'VectorPipelineConfig':
        """從環境變數創建配置"""
        return cls(
            data_dir=os.getenv('VECTOR_DATA_DIR', 'data'),
            tag_csv_path=os.getenv('TAG_CSV_PATH', '../utils/TAG_info.csv'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'BAAI/bge-m3'),
            milvus_host=os.getenv('MILVUS_HOST', '192.168.32.86'),
            milvus_port=os.getenv('MILVUS_PORT', '19530'),
            collection_name=os.getenv('MILVUS_COLLECTION', 'podwise_chunks'),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'data_dir': self.data_dir,
            'stage1_dir': self.stage1_dir,
            'stage3_dir': self.stage3_dir,
            'stage4_dir': self.stage4_dir,
            'tag_csv_path': self.tag_csv_path,
            'max_tags_per_chunk': self.max_tags_per_chunk,
            'min_tags_per_chunk': self.min_tags_per_chunk,
            'embedding_model': self.embedding_model,
            'vector_dim': self.vector_dim,
            'batch_size': self.batch_size,
            'milvus_host': self.milvus_host,
            'milvus_port': self.milvus_port,
            'collection_name': self.collection_name,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'max_chunk_length': self.max_chunk_length,
            'min_chunk_length': self.min_chunk_length,
            'chunk_overlap': self.chunk_overlap
        }


# 全域配置實例
config = VectorPipelineConfig.from_env() 