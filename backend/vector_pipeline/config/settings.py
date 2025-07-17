"""
Vector Pipeline Settings

Configuration settings for the vector pipeline system.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os


@dataclass
class MilvusConfig:
    """Milvus database configuration."""
    host: str = "192.168.32.86"
    port: str = "19530"
    collection_name: str = "podcast_chunks"
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    model: str = "bge-m3"
    dimension: int = 1024
    device: str = "cpu"
    batch_size: int = 32


@dataclass
class ChunkingConfig:
    """Text chunking configuration."""
    chunk_size: int = 512
    overlap: int = 50
    min_chunk_size: int = 100


@dataclass
class DatabaseConfig:
    """Database configuration."""
    postgresql_url: Optional[str] = None
    mongodb_url: Optional[str] = None


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/vector_pipeline.log"


class VectorPipelineConfig:
    """Main configuration class for the vector pipeline."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_dict: Optional configuration dictionary
        """
        if config_dict:
            self._load_from_dict(config_dict)
        else:
            self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration values."""
        self.milvus = MilvusConfig()
        self.embedding = EmbeddingConfig()
        self.chunking = ChunkingConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        
        # Load from environment variables if available
        self._load_from_env()
    
    def _load_from_dict(self, config_dict: Dict[str, Any]):
        """Load configuration from dictionary."""
        milvus_config = config_dict.get('milvus', {})
        self.milvus = MilvusConfig(**milvus_config)
        
        embedding_config = config_dict.get('embedding', {})
        self.embedding = EmbeddingConfig(**embedding_config)
        
        chunking_config = config_dict.get('chunking', {})
        self.chunking = ChunkingConfig(**chunking_config)
        
        database_config = config_dict.get('database', {})
        self.database = DatabaseConfig(**database_config)
        
        logging_config = config_dict.get('logging', {})
        self.logging = LoggingConfig(**logging_config)
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Milvus
        if os.getenv('MILVUS_HOST'):
            self.milvus.host = os.getenv('MILVUS_HOST')
        if os.getenv('MILVUS_PORT'):
            self.milvus.port = os.getenv('MILVUS_PORT')
        if os.getenv('MILVUS_COLLECTION'):
            self.milvus.collection_name = os.getenv('MILVUS_COLLECTION')
        
        # Embedding
        if os.getenv('EMBEDDING_MODEL'):
            self.embedding.model = os.getenv('EMBEDDING_MODEL')
        if os.getenv('EMBEDDING_DIMENSION'):
            self.embedding.dimension = int(os.getenv('EMBEDDING_DIMENSION'))
        
        # Database
        if os.getenv('POSTGRESQL_URL'):
            self.database.postgresql_url = os.getenv('POSTGRESQL_URL')
        if os.getenv('MONGODB_URL'):
            self.database.mongodb_url = os.getenv('MONGODB_URL')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'milvus': {
                'host': self.milvus.host,
                'port': self.milvus.port,
                'collection_name': self.milvus.collection_name,
                'username': self.milvus.username,
                'password': self.milvus.password
            },
            'embedding': {
                'model': self.embedding.model,
                'dimension': self.embedding.dimension,
                'device': self.embedding.device,
                'batch_size': self.embedding.batch_size
            },
            'chunking': {
                'chunk_size': self.chunking.chunk_size,
                'overlap': self.chunking.overlap,
                'min_chunk_size': self.chunking.min_chunk_size
            },
            'database': {
                'postgresql_url': self.database.postgresql_url,
                'mongodb_url': self.database.mongodb_url
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path
            }
        }
    
    def validate(self) -> bool:
        """Validate configuration values."""
        try:
            # Validate Milvus config
            assert self.milvus.host, "Milvus host is required"
            assert self.milvus.port, "Milvus port is required"
            assert self.milvus.collection_name, "Milvus collection name is required"
            
            # Validate Embedding config
            assert self.embedding.model, "Embedding model is required"
            assert self.embedding.dimension > 0, "Embedding dimension must be positive"
            assert self.embedding.batch_size > 0, "Batch size must be positive"
            
            # Validate Chunking config
            assert self.chunking.chunk_size > 0, "Chunk size must be positive"
            assert self.chunking.overlap >= 0, "Overlap must be non-negative"
            assert self.chunking.min_chunk_size > 0, "Min chunk size must be positive"
            
            return True
            
        except AssertionError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"VectorPipelineConfig(milvus={self.milvus.host}:{self.milvus.port}, embedding={self.embedding.model})" 