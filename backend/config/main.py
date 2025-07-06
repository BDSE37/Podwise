#!/usr/bin/env python3
"""
Podwise Config 主模組

提供配置管理服務入口點。

作者: Podwise Team
版本: 1.0.0
"""

import logging
import sys
from pathlib import Path

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


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_service = None
        self.db_config = None
        self.mongo_config = None
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
            
            logger.info("✅ 配置管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 配置管理器初始化失敗: {e}")
            raise
    
    def get_system_status(self) -> dict:
        """獲取系統狀態"""
        return {
            "config_service": self.config_service is not None,
            "db_config": self.db_config is not None,
            "mongo_config": self.mongo_config is not None,
            "version": "1.0.0"
        }
    
    def validate_configs(self) -> dict:
        """驗證所有配置"""
        results = {}
        
        if self.config_service:
            results["config_service"] = self.config_service.validate_config()
        
        if self.db_config:
            results["db_config"] = self.db_config.validate_connection()
        
        if self.mongo_config:
            results["mongo_config"] = self.mongo_config.validate_connection()
        
        return results


def main():
    """主函數"""
    try:
        # 初始化配置管理器
        manager = ConfigManager()
        manager.initialize()
        
        # 顯示系統狀態
        status = manager.get_system_status()
        logger.info(f"系統狀態: {status}")
        
        # 驗證配置
        validation_results = manager.validate_configs()
        logger.info(f"配置驗證結果: {validation_results}")
        
        logger.info("✅ 配置模組運行正常")
        
    except Exception as e:
        logger.error(f"❌ 配置模組執行失敗: {e}")
        raise


if __name__ == "__main__":
    main() 