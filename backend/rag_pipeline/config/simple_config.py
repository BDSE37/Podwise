#!/usr/bin/env python3
"""
簡化的 RAG Pipeline 配置
避免 Pydantic 的額外參數問題
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class SimpleConfig:
    """簡化的配置類別"""
    
    # 環境配置
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # 資料庫配置
    mongodb_uri: str = "mongodb://localhost:27017/podwise"
    mongodb_database: str = "podwise"
    mongodb_collection: str = "conversations"
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "podwise"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "podcast_chunks"
    
    # API 配置
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-ada-002"
    
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"
    
    google_api_key: str = ""
    google_genai_model: str = "gemini-pro"
    
    # RAG 配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # 服務配置
    rag_pipeline_host: str = "localhost"
    rag_pipeline_port: int = 8010
    
    # Ollama 配置
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:8b"
    
    def __post_init__(self):
        """從環境變數載入配置"""
        self._load_from_env()
    
    def _load_from_env(self):
        """從環境變數載入配置"""
        # 資料庫配置
        self.mongodb_uri = os.getenv("MONGODB_URI", self.mongodb_uri)
        self.postgres_host = os.getenv("POSTGRES_HOST", self.postgres_host)
        self.postgres_port = int(os.getenv("POSTGRES_PORT", str(self.postgres_port)))
        self.postgres_db = os.getenv("POSTGRES_DB", self.postgres_db)
        self.postgres_user = os.getenv("POSTGRES_USER", self.postgres_user)
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", self.postgres_password)
        
        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.redis_db = int(os.getenv("REDIS_DB", str(self.redis_db)))
        self.redis_password = os.getenv("REDIS_PASSWORD", self.redis_password)
        
        self.milvus_host = os.getenv("MILVUS_HOST", self.milvus_host)
        self.milvus_port = int(os.getenv("MILVUS_PORT", str(self.milvus_port)))
        self.milvus_collection = os.getenv("MILVUS_COLLECTION", self.milvus_collection)
        
        # API 配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        
        # 服務配置
        self.rag_pipeline_host = os.getenv("RAG_PIPELINE_HOST", self.rag_pipeline_host)
        self.rag_pipeline_port = int(os.getenv("RAG_PIPELINE_PORT", str(self.rag_pipeline_port)))
        
        # Ollama 配置
        self.ollama_host = os.getenv("OLLAMA_HOST", self.ollama_host)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "database": {
                "mongodb_uri": self.mongodb_uri,
                "postgres_host": self.postgres_host,
                "postgres_port": self.postgres_port,
                "postgres_db": self.postgres_db,
                "postgres_user": self.postgres_user,
                "postgres_password": self.postgres_password,
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "redis_db": self.redis_db,
                "milvus_host": self.milvus_host,
                "milvus_port": self.milvus_port,
                "milvus_collection": self.milvus_collection,
            },
            "api": {
                "openai_api_key": self.openai_api_key,
                "anthropic_api_key": self.anthropic_api_key,
                "google_api_key": self.google_api_key,
            },
            "rag": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "top_k": self.top_k,
                "similarity_threshold": self.similarity_threshold,
            },
            "ollama": {
                "host": self.ollama_host,
                "model": self.ollama_model,
            }
        }

def get_simple_config() -> SimpleConfig:
    """獲取簡化配置"""
    return SimpleConfig()

# 全域配置實例
config = get_simple_config() 