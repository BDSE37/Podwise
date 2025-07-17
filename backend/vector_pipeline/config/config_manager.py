"""
Configuration Manager

Manages configuration loading, validation, and updates for the vector pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .settings import VectorPipelineConfig


class ConfigManager:
    """Manages configuration for the vector pipeline system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or use defaults."""
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                self.config = VectorPipelineConfig(config_dict)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
                self.config = VectorPipelineConfig()
        else:
            self.config = VectorPipelineConfig()
        
        # Validate configuration
        try:
            self.config.validate()
        except ValueError as e:
            print(f"Warning: Configuration validation failed: {e}")
    
    def get_config(self) -> VectorPipelineConfig:
        """Get the current configuration."""
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary containing configuration updates
        """
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
            
        current_dict = self.config.to_dict()
        
        # Deep merge updates
        def deep_merge(base: Dict, update: Dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(current_dict, updates)
        
        # Create new config
        self.config = VectorPipelineConfig(current_dict)
        self.config.validate()
    
    def save_config(self, path: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            path: Path to save configuration file
        """
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No path specified for saving configuration")
        
        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
    
    def get_milvus_config(self) -> Dict[str, Any]:
        """Get Milvus configuration."""
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
        return {
            'host': self.config.milvus.host,
            'port': self.config.milvus.port,
            'collection_name': self.config.milvus.collection_name,
            'username': self.config.milvus.username,
            'password': self.config.milvus.password
        }
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration."""
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
        return {
            'model': self.config.embedding.model,
            'dimension': self.config.embedding.dimension,
            'device': self.config.embedding.device,
            'batch_size': self.config.embedding.batch_size
        }
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """Get chunking configuration."""
        return {
            'chunk_size': self.config.chunking.chunk_size,
            'overlap': self.config.chunking.overlap,
            'min_chunk_size': self.config.chunking.min_chunk_size
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'postgresql_url': self.config.database.postgresql_url,
            'mongodb_url': self.config.database.mongodb_url
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': self.config.logging.level,
            'format': self.config.logging.format,
            'file_path': self.config.logging.file_path
        } 