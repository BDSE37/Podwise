"""
Vector Pipeline Configuration

Simple configuration management for the vector pipeline system.
"""

import os
from typing import Dict, Any


class VectorPipelineConfig:
    """Configuration class for the vector pipeline."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.milvus = {
            'host': os.getenv('MILVUS_HOST', '192.168.32.86'),
            'port': os.getenv('MILVUS_PORT', '19530'),
            'collection_name': os.getenv('MILVUS_COLLECTION', 'podcast_chunks'),
            'username': os.getenv('MILVUS_USERNAME'),
            'password': os.getenv('MILVUS_PASSWORD')
        }
        
        self.embedding = {
            'model': os.getenv('EMBEDDING_MODEL', 'bge-m3'),
            'dimension': int(os.getenv('EMBEDDING_DIMENSION', '1024')),
            'device': os.getenv('EMBEDDING_DEVICE', 'cpu'),
            'batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
        }
        
        self.chunking = {
            'chunk_size': int(os.getenv('CHUNK_SIZE', '512')),
            'overlap': int(os.getenv('CHUNK_OVERLAP', '50')),
            'min_chunk_size': int(os.getenv('MIN_CHUNK_SIZE', '100'))
        }
        
        self.database = {
            'postgresql_url': os.getenv('POSTGRESQL_URL'),
            'mongodb_url': os.getenv('MONGODB_URL')
        }
        
        self.logging = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': os.getenv('LOG_FILE', 'logs/vector_pipeline.log')
        }
    
    def get_milvus_config(self) -> Dict[str, Any]:
        """Get Milvus configuration."""
        return self.milvus
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration."""
        return self.embedding
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """Get chunking configuration."""
        return self.chunking
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.database
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.logging
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'milvus': self.milvus,
            'embedding': self.embedding,
            'chunking': self.chunking,
            'database': self.database,
            'logging': self.logging
        }


# Global configuration instance
config = VectorPipelineConfig() 