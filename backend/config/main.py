#!/usr/bin/env python3
"""
Podwise Config 主模組

提供統一的配置管理服務，整合所有配置功能：
- 配置服務管理
- 資料庫配置
- MongoDB 配置
- FastAPI Web 服務
- 配置驗證

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 2.0.0
"""

import logging
import sys
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from config_service import ConfigService
from db_config import DatabaseConfig
from mongo_config import MongoConfig

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ConfigStatus:
    """配置狀態數據類別"""
    config_service: bool
    db_config: bool
    mongo_config: bool
    version: str = "2.0.0"


class ConfigManager:
    """配置管理器 - 統一管理所有配置服務"""
    
    def __init__(self, enable_web_service: bool = True):
        """
        初始化配置管理器
        
        Args:
            enable_web_service: 是否啟用 Web 服務
        """
        self.enable_web_service = enable_web_service
        self.config_service: Optional[ConfigService] = None
        self.db_config: Optional[DatabaseConfig] = None
        self.mongo_config: Optional[MongoConfig] = None
        self.app: Optional[FastAPI] = None
        
        logger.info("🚀 初始化配置管理器...")
    
    def initialize(self) -> None:
        """初始化所有配置服務"""
        try:
            # 初始化配置服務
            self.config_service = ConfigService()
            logger.info("✅ 配置服務初始化完成")
            
            # 初始化資料庫配置
            self.db_config = DatabaseConfig()
            logger.info("✅ 資料庫配置初始化完成")
            
            # 初始化 MongoDB 配置
            self.mongo_config = MongoConfig()
            logger.info("✅ MongoDB 配置初始化完成")
            
            # 初始化 Web 服務（如果啟用）
            if self.enable_web_service:
                self._initialize_web_service()
            
            logger.info("✅ 配置管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 配置管理器初始化失敗: {e}")
            raise
    
    def _initialize_web_service(self) -> None:
        """初始化 Web 服務"""
        self.app = FastAPI(
            title="Podwise Config Service",
            description="Podwise 配置管理服務",
            version="2.0.0"
        )
        
        # 設定 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 註冊路由
        self._register_routes()
        logger.info("✅ Web 服務初始化完成")
    
    def _register_routes(self) -> None:
        """註冊 API 路由"""
        
        @self.app.get("/")
        async def root():
            """根端點"""
            return {
                "message": "Podwise 配置服務運行中",
                "version": "2.0.0",
                "configs": [
                    "MongoDB 配置",
                    "PostgreSQL 配置", 
                    "Milvus 配置",
                    "MinIO 配置"
                ],
                "features": [
                    "配置查詢",
                    "資料庫初始化",
                    "配置驗證"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康檢查端點"""
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "config_status": self.get_system_status()
            }
        
        @self.app.get("/api/v1/configs/all")
        async def get_all_configs():
            """獲取所有配置"""
            try:
                return {
                    "mongo": self._get_mongo_config(),
                    "postgres": self._get_postgres_config(),
                    "milvus": self._get_milvus_config(),
                    "minio": self._get_minio_config()
                }
            except Exception as e:
                logger.error(f"獲取所有配置失敗: {str(e)}")
                raise HTTPException(status_code=500, detail="配置獲取失敗")
        
        @self.app.get("/api/v1/configs/validate")
        async def validate_all_configs():
            """驗證所有配置"""
            try:
                validation_results = self.validate_configs()
                return {
                    "status": "success",
                    "validation_results": validation_results
                }
            except Exception as e:
                logger.error(f"配置驗證失敗: {str(e)}")
                raise HTTPException(status_code=500, detail="配置驗證失敗")
    
    def _get_mongo_config(self) -> Dict[str, Any]:
        """獲取 MongoDB 配置"""
        if not self.mongo_config:
            raise HTTPException(status_code=500, detail="MongoDB 配置未初始化")
        
        return {
            "host": self.mongo_config.host,
            "port": self.mongo_config.port,
            "database": self.mongo_config.database,
            "username": self.mongo_config.username,
            "collections": self.mongo_config.collections
        }
    
    def _get_postgres_config(self) -> Dict[str, Any]:
        """獲取 PostgreSQL 配置"""
        if not self.db_config:
            raise HTTPException(status_code=500, detail="資料庫配置未初始化")
        
        return {
            "host": self.db_config.host,
            "port": self.db_config.port,
            "database": self.db_config.database,
            "user": self.db_config.user
        }
    
    def _get_milvus_config(self) -> Dict[str, Any]:
        """獲取 Milvus 配置"""
        if not self.db_config:
            raise HTTPException(status_code=500, detail="資料庫配置未初始化")
        
        return {
            "host": self.db_config.milvus_host,
            "port": self.db_config.milvus_port,
            "collection_name": self.db_config.milvus_collection,
            "dim": self.db_config.milvus_dim,
            "index_type": self.db_config.milvus_index_type,
            "metric_type": self.db_config.milvus_metric_type
        }
    
    def _get_minio_config(self) -> Dict[str, Any]:
        """獲取 MinIO 配置"""
        if not self.db_config:
            raise HTTPException(status_code=500, detail="資料庫配置未初始化")
        
        return {
            "endpoint": self.db_config.minio_endpoint,
            "bucket_name": self.db_config.minio_bucket,
            "secure": self.db_config.minio_secure
        }
    
    def get_system_status(self) -> ConfigStatus:
        """獲取系統狀態"""
        return ConfigStatus(
            config_service=self.config_service is not None,
            db_config=self.db_config is not None,
            mongo_config=self.mongo_config is not None
        )
    
    def validate_configs(self) -> Dict[str, Any]:
        """驗證所有配置"""
        results = {}
        
        if self.config_service:
            results["config_service"] = self.config_service.validate_config()
        
        if self.db_config:
            results["db_config"] = self.db_config.validate_connection()
        
        if self.mongo_config:
            results["mongo_config"] = self.mongo_config.validate_connection()
        
        return results
    
    async def start_web_service(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """啟動 Web 服務"""
        if not self.app:
            raise RuntimeError("Web 服務未初始化")
        
        logger.info(f"🌐 啟動配置服務於 {host}:{port}")
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def main():
    """主函數"""
    try:
        # 初始化配置管理器
        manager = ConfigManager(enable_web_service=True)
        manager.initialize()
        
        # 顯示系統狀態
        status = manager.get_system_status()
        logger.info(f"系統狀態: {status}")
        
        # 驗證配置
        validation_results = manager.validate_configs()
        logger.info(f"配置驗證結果: {validation_results}")
        
        # 啟動 Web 服務
        asyncio.run(manager.start_web_service())
        
    except Exception as e:
        logger.error(f"❌ 配置模組執行失敗: {e}")
        raise


if __name__ == "__main__":
    main() 