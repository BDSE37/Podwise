#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise Core 模組主入口點
統一管理核心服務，提供 OOP 設計的模組化架構
"""

import logging
import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.podwise_service_manager import PodwiseServiceManager
from core.service_manager import ServiceManager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoreModuleManager:
    """核心模組管理器"""
    
    def __init__(self):
        """初始化核心模組管理器"""
        self.podwise_service = None
        self.service_manager = None
        self._init_services()
    
    def _init_services(self):
        """初始化所有核心服務"""
        try:
            # 初始化 Podwise 服務管理器
            self.podwise_service = PodwiseServiceManager()
            logger.info("✅ Podwise 服務管理器初始化成功")
            
            # 初始化通用服務管理器
            self.service_manager = ServiceManager()
            logger.info("✅ 通用服務管理器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 核心服務初始化失敗: {e}")
            raise
    
    def get_podwise_service(self) -> PodwiseServiceManager:
        """獲取 Podwise 服務管理器"""
        return self.podwise_service
    
    def get_service_manager(self) -> ServiceManager:
        """獲取通用服務管理器"""
        return self.service_manager
    
    def health_check(self) -> dict:
        """健康檢查"""
        try:
            return {
                "status": "healthy",
                "podwise_service": self.podwise_service is not None,
                "service_manager": self.service_manager is not None,
                "timestamp": "2025-01-19T00:00:00Z"
            }
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-01-19T00:00:00Z"
            }
    
    def cleanup(self):
        """清理資源"""
        try:
            if self.podwise_service:
                self.podwise_service.close_connections()
            logger.info("✅ 核心模組資源清理完成")
        except Exception as e:
            logger.error(f"❌ 核心模組資源清理失敗: {e}")

# 全域實例
core_manager = None

def get_core_manager() -> CoreModuleManager:
    """獲取核心模組管理器實例（單例模式）"""
    global core_manager
    if core_manager is None:
        core_manager = CoreModuleManager()
    return core_manager

def main():
    """主函數 - 用於測試和獨立運行"""
    try:
        logger.info("🚀 啟動 Podwise Core 模組...")
        
        # 初始化核心管理器
        manager = get_core_manager()
        
        # 執行健康檢查
        health = manager.health_check()
        logger.info(f"健康檢查結果: {health}")
        
        if health["status"] == "healthy":
            logger.info("✅ Core 模組啟動成功")
        else:
            logger.error("❌ Core 模組啟動失敗")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Core 模組啟動異常: {e}")
        return 1
    finally:
        # 清理資源
        if core_manager:
            core_manager.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 