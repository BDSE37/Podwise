#!/usr/bin/env python3
"""
Database Configuration Manager

統一的資料庫配置管理系統，支援 .env 檔案讀取和多資料庫連接

作者: Podwise Team
版本: 1.0.0
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """資料庫配置數據類別"""
    # MongoDB 配置
    mongodb_uri: str
    mongodb_database: str
    mongodb_collection: str
    
    # PostgreSQL 配置
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    
    # Redis 配置
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: Optional[str]
    
    # Milvus 配置
    milvus_host: str
    milvus_port: int
    milvus_collection: str
    
    # 環境配置
    environment: str
    debug: bool
    log_level: str


class DatabaseConfigManager:
    """資料庫配置管理器"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            env_file_path: .env 檔案路徑，如果為 None 則自動尋找
        """
        self.env_file_path = env_file_path or self._find_env_file()
        self.config = self._load_config()
        
        logger.info(f"資料庫配置管理器初始化完成，環境: {self.config.environment}")
    
    def _find_env_file(self) -> str:
        """自動尋找 .env 檔案"""
        # 搜尋順序：env.local > .env > .env.example
        search_paths = [
            "env.local",
            ".env",
            ".env.example"
        ]
        
        # 從當前目錄開始向上搜尋
        current_dir = Path(__file__).parent.parent
        for search_path in search_paths:
            env_file = current_dir / search_path
            if env_file.exists():
                logger.info(f"找到環境檔案: {env_file}")
                return str(env_file)
        
        logger.warning("未找到環境檔案，使用預設配置")
        return ""
    
    def _load_config(self) -> DatabaseConfig:
        """載入配置"""
        # 載入 .env 檔案
        if self.env_file_path and os.path.exists(self.env_file_path):
            self._load_env_file()
        
        # 從環境變數讀取配置
        return DatabaseConfig(
            # MongoDB 配置
            mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017/podwise"),
            mongodb_database=os.getenv("MONGODB_DATABASE", "podwise"),
            mongodb_collection=os.getenv("MONGODB_COLLECTION", "conversations"),
            
            # PostgreSQL 配置
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "podwise"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "password"),
            
            # Redis 配置
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            
            # Milvus 配置
            milvus_host=os.getenv("MILVUS_HOST", "localhost"),
            milvus_port=int(os.getenv("MILVUS_PORT", "19530")),
            milvus_collection=os.getenv("MILVUS_COLLECTION", "podcast_chunks"),
            
            # 環境配置
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def _load_env_file(self) -> None:
        """載入 .env 檔案"""
        try:
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # 只設定未存在的環境變數
                        if key and value and key not in os.environ:
                            os.environ[key] = value
                            
            logger.info(f"成功載入環境檔案: {self.env_file_path}")
            
        except Exception as e:
            logger.error(f"載入環境檔案失敗: {e}")
    
    def get_mongodb_config(self) -> Dict[str, str]:
        """獲取 MongoDB 配置"""
        return {
            "uri": self.config.mongodb_uri,
            "database": self.config.mongodb_database,
            "collection": self.config.mongodb_collection
        }
    
    def get_postgres_config(self) -> Dict[str, Any]:
        """獲取 PostgreSQL 配置"""
        return {
            "host": self.config.postgres_host,
            "port": self.config.postgres_port,
            "database": self.config.postgres_db,
            "user": self.config.postgres_user,
            "password": self.config.postgres_password
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """獲取 Redis 配置"""
        config = {
            "host": self.config.redis_host,
            "port": self.config.redis_port,
            "db": self.config.redis_db
        }
        
        if self.config.redis_password:
            config["password"] = self.config.redis_password
        
        return config
    
    def get_milvus_config(self) -> Dict[str, Any]:
        """獲取 Milvus 配置"""
        return {
            "host": self.config.milvus_host,
            "port": self.config.milvus_port,
            "collection": self.config.milvus_collection
        }
    
    def get_environment_config(self) -> Dict[str, Any]:
        """獲取環境配置"""
        return {
            "environment": self.config.environment,
            "debug": self.config.debug,
            "log_level": self.config.log_level
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """驗證配置完整性"""
        validation_results = {
            "mongodb": bool(self.config.mongodb_uri and self.config.mongodb_database),
            "postgres": bool(
                self.config.postgres_host and 
                self.config.postgres_db and 
                self.config.postgres_user and 
                self.config.postgres_password
            ),
            "redis": bool(self.config.redis_host),
            "milvus": bool(self.config.milvus_host and self.config.milvus_collection),
            "environment": bool(self.config.environment)
        }
        
        return validation_results
    
    def get_connection_strings(self) -> Dict[str, str]:
        """獲取連接字串"""
        return {
            "mongodb": self.config.mongodb_uri,
            "postgres": f"postgresql://{self.config.postgres_user}:{self.config.postgres_password}@{self.config.postgres_host}:{self.config.postgres_port}/{self.config.postgres_db}",
            "redis": f"redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}",
            "milvus": f"{self.config.milvus_host}:{self.config.milvus_port}"
        }


# 全域配置管理器實例
database_config_manager = DatabaseConfigManager()


def get_database_config() -> DatabaseConfig:
    """獲取資料庫配置"""
    return database_config_manager.config


def get_database_config_manager() -> DatabaseConfigManager:
    """獲取資料庫配置管理器"""
    return database_config_manager


if __name__ == "__main__":
    # 測試配置載入
    config_manager = get_database_config_manager()
    
    print("資料庫配置測試")
    print("=" * 50)
    
    # 顯示配置
    config = config_manager.config
    print(f"環境: {config.environment}")
    print(f"除錯模式: {config.debug}")
    print(f"日誌等級: {config.log_level}")
    
    print(f"\nMongoDB:")
    print(f"  URI: {config.mongodb_uri}")
    print(f"  資料庫: {config.mongodb_database}")
    print(f"  集合: {config.mongodb_collection}")
    
    print(f"\nPostgreSQL:")
    print(f"  主機: {config.postgres_host}:{config.postgres_port}")
    print(f"  資料庫: {config.postgres_db}")
    print(f"  用戶: {config.postgres_user}")
    
    print(f"\nRedis:")
    print(f"  主機: {config.redis_host}:{config.redis_port}")
    print(f"  資料庫: {config.redis_db}")
    
    print(f"\nMilvus:")
    print(f"  主機: {config.milvus_host}:{config.milvus_port}")
    print(f"  集合: {config.milvus_collection}")
    
    # 驗證配置
    validation = config_manager.validate_config()
    print(f"\n配置驗證:")
    for component, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"  {component}: {status}")
    
    # 顯示連接字串
    connections = config_manager.get_connection_strings()
    print(f"\n連接字串:")
    for db_type, connection_string in connections.items():
        print(f"  {db_type}: {connection_string}") 