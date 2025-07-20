#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise User Management 模組主入口點
統一管理用戶相關功能，提供 OOP 設計的模組化架構
"""

import logging
import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from user_management.integrated_user_service import IntegratedUserService

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserManagementModuleManager:
    """用戶管理模組管理器"""
    
    def __init__(self):
        """初始化用戶管理模組管理器"""
        self.user_service = None
        self._init_services()
    
    def _init_services(self):
        """初始化所有用戶管理服務"""
        try:
            # 初始化整合用戶服務
            self.user_service = IntegratedUserService()
            logger.info("✅ 整合用戶服務初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 用戶管理服務初始化失敗: {e}")
            raise
    
    def get_user_service(self) -> IntegratedUserService:
        """獲取整合用戶服務"""
        if self.user_service is None:
            raise RuntimeError("用戶服務未初始化")
        return self.user_service
    
    def health_check(self) -> dict:
        """健康檢查"""
        try:
            return {
                "status": "healthy",
                "user_service": self.user_service is not None,
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
            if self.user_service:
                # 清理用戶服務資源
                pass
            logger.info("✅ 用戶管理模組資源清理完成")
        except Exception as e:
            logger.error(f"❌ 用戶管理模組資源清理失敗: {e}")

# 全域實例
user_management_manager = None

def get_user_management_manager() -> UserManagementModuleManager:
    """獲取用戶管理模組管理器實例（單例模式）"""
    global user_management_manager
    if user_management_manager is None:
        user_management_manager = UserManagementModuleManager()
    return user_management_manager

def main():
    """主函數 - 用於測試和獨立運行"""
    try:
        logger.info("🚀 啟動 Podwise User Management 模組...")
        
        # 初始化用戶管理管理器
        manager = get_user_management_manager()
        
        # 執行健康檢查
        health = manager.health_check()
        logger.info(f"健康檢查結果: {health}")
        
        if health["status"] == "healthy":
            logger.info("✅ User Management 模組啟動成功")
        else:
            logger.error("❌ User Management 模組啟動失敗")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ User Management 模組啟動異常: {e}")
        return 1
    finally:
        # 清理資源
        if user_management_manager:
            user_management_manager.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 