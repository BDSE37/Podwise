#!/usr/bin/env python3
"""
Podwise Utils 主模組

提供統一的工具服務入口點，整合所有共用工具功能：
- 文本處理工具
- 向量搜尋引擎
- 環境配置管理
- 用戶認證服務
- 音檔搜尋工具
- 日誌配置

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 2.0.0
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UtilsConfig:
    """Utils 配置類別"""
    enable_text_processing: bool = True
    enable_vector_search: bool = True
    enable_audio_search: bool = True
    enable_user_auth: bool = True
    enable_minio_utils: bool = True
    log_level: str = "INFO"


class UtilsManager:
    """Utils 管理器 - 統一管理所有工具服務"""
    
    def __init__(self, config: Optional[UtilsConfig] = None):
        """初始化 Utils 管理器"""
        self.config = config or UtilsConfig()
        self.services = {}
        self._initialize_services()
        logger.info("🚀 Utils 管理器初始化完成")
    
    def _initialize_services(self) -> None:
        """初始化所有服務"""
        try:
            # 導入核心服務
            from .core_services import BaseService, ServiceConfig, ServiceResponse
            from .text_processing import TextProcessor, create_text_processor
            from .vector_search import VectorSearchEngine, create_vector_search
            from .audio_search import AudioSearchEngine
            from .user_auth_service import UserAuthService
            from .minio_milvus_utils import get_minio_client, get_podcast_name_from_db
            from .env_config import PodriConfig
            from .logging_config import setup_logging
            
            # 設定日誌
            setup_logging(level=self.config.log_level)
            
            # 初始化服務
            if self.config.enable_text_processing:
                self.services['text_processor'] = create_text_processor()
                logger.info("✅ 文本處理服務已初始化")
            
            if self.config.enable_vector_search:
                self.services['vector_search'] = create_vector_search()
                logger.info("✅ 向量搜尋服務已初始化")
            
            if self.config.enable_audio_search:
                self.services['audio_search'] = AudioSearchEngine()
                logger.info("✅ 音檔搜尋服務已初始化")
            
            if self.config.enable_user_auth:
                self.services['user_auth'] = UserAuthService()
                logger.info("✅ 用戶認證服務已初始化")
            
            if self.config.enable_minio_utils:
                self.services['minio_client'] = get_minio_client()
                logger.info("✅ MinIO 客戶端已初始化")
            
            # 環境配置
            self.services['config'] = PodriConfig()
            logger.info("✅ 環境配置已載入")
            
        except Exception as e:
            logger.error(f"❌ 服務初始化失敗: {e}")
            raise
    
    def get_service(self, service_name: str) -> Any:
        """獲取指定服務"""
        if service_name not in self.services:
            raise ValueError(f"服務 '{service_name}' 不存在")
        return self.services[service_name]
    
    def get_text_processor(self) -> Any:
        """獲取文本處理器"""
        return self.get_service('text_processor')
    
    def get_vector_search(self) -> Any:
        """獲取向量搜尋引擎"""
        return self.get_service('vector_search')
    
    def get_audio_search(self) -> Any:
        """獲取音檔搜尋引擎"""
        return self.get_service('audio_search')
    
    def get_user_auth(self) -> Any:
        """獲取用戶認證服務"""
        return self.get_service('user_auth')
    
    def get_minio_client(self) -> Any:
        """獲取 MinIO 客戶端"""
        return self.get_service('minio_client')
    
    def get_config(self) -> Any:
        """獲取環境配置"""
        return self.get_service('config')
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
        
        for service_name, service in self.services.items():
            try:
                # 基本可用性檢查
                if hasattr(service, 'health_check'):
                    service_health = service.health_check()
                else:
                    service_health = {"status": "available"}
                
                health_status["services"][service_name] = service_health
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
        
        return health_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "module": "utils",
            "version": "2.0.0",
            "description": "Podwise 統一工具模組",
            "services": list(self.services.keys()),
            "config": {
                "enable_text_processing": self.config.enable_text_processing,
                "enable_vector_search": self.config.enable_vector_search,
                "enable_audio_search": self.config.enable_audio_search,
                "enable_user_auth": self.config.enable_user_auth,
                "enable_minio_utils": self.config.enable_minio_utils,
                "log_level": self.config.log_level
            }
        }


# 全域實例
_utils_manager: Optional[UtilsManager] = None


def get_utils_manager(config: Optional[UtilsConfig] = None) -> UtilsManager:
    """獲取 Utils 管理器實例（單例模式）"""
    global _utils_manager
    if _utils_manager is None:
        _utils_manager = UtilsManager(config)
    return _utils_manager


def initialize_utils(config: Optional[UtilsConfig] = None) -> UtilsManager:
    """初始化 Utils 模組"""
    return get_utils_manager(config)


# 便捷函數
def get_text_processor():
    """獲取文本處理器"""
    return get_utils_manager().get_text_processor()


def get_vector_search():
    """獲取向量搜尋引擎"""
    return get_utils_manager().get_vector_search()


def get_audio_search():
    """獲取音檔搜尋引擎"""
    return get_utils_manager().get_audio_search()


def get_user_auth():
    """獲取用戶認證服務"""
    return get_utils_manager().get_user_auth()


def get_minio_client():
    """獲取 MinIO 客戶端"""
    return get_utils_manager().get_minio_client()


def get_config():
    """獲取環境配置"""
    return get_utils_manager().get_config()


if __name__ == "__main__":
    # 測試模式
    try:
        utils_manager = initialize_utils()
        print("✅ Utils 模組初始化成功")
        print(f"📋 服務資訊: {utils_manager.get_service_info()}")
        print(f"🏥 健康檢查: {utils_manager.health_check()}")
    except Exception as e:
        print(f"❌ Utils 模組初始化失敗: {e}")
        sys.exit(1) 