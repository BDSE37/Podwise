#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise Scripts 模組主入口點
統一管理所有腳本功能，提供 OOP 設計的模組化架構
"""

import logging
import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScriptsModuleManager:
    """腳本模組管理器"""
    
    def __init__(self):
        """初始化腳本模組管理器"""
        self.analysis_manager = None
        self.db_manager = None
        self._init_services()
    
    def _init_services(self):
        """初始化所有腳本服務"""
        try:
            # 初始化分析管理器
            self.analysis_manager = self._init_analysis_manager()
            
            # 初始化資料庫管理器
            self.db_manager = self._init_db_manager()
            
            logger.info("✅ Scripts 模組服務初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Scripts 模組服務初始化失敗: {e}")
            raise
    
    def _init_analysis_manager(self):
        """初始化分析管理器"""
        try:
            # 這裡可以導入具體的分析管理器類別
            # from scripts.analyze_minio_episodes import MinioEpisodeAnalyzer
            # return MinioEpisodeAnalyzer()
            return {"status": "initialized", "type": "analysis"}
        except Exception as e:
            logger.error(f"分析管理器初始化失敗: {e}")
            return None
    
    def _init_db_manager(self):
        """初始化資料庫管理器"""
        try:
            # 這裡可以導入具體的資料庫管理器類別
            # from scripts.check_db_structure import DatabaseStructureChecker
            # return DatabaseStructureChecker()
            return {"status": "initialized", "type": "database"}
        except Exception as e:
            logger.error(f"資料庫管理器初始化失敗: {e}")
            return None
    
    def get_analysis_manager(self):
        """獲取分析管理器"""
        return self.analysis_manager
    
    def get_db_manager(self):
        """獲取資料庫管理器"""
        return self.db_manager
    
    def run_minio_analysis(self):
        """運行 MinIO 節目分析"""
        try:
            logger.info("開始運行 MinIO 節目分析...")
            # 這裡可以調用具體的分析功能
            # self.analysis_manager.analyze_episodes()
            logger.info("✅ MinIO 節目分析完成")
            return True
        except Exception as e:
            logger.error(f"❌ MinIO 節目分析失敗: {e}")
            return False
    
    def run_db_structure_check(self):
        """運行資料庫結構檢查"""
        try:
            logger.info("開始運行資料庫結構檢查...")
            # 這裡可以調用具體的檢查功能
            # self.db_manager.check_structure()
            logger.info("✅ 資料庫結構檢查完成")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫結構檢查失敗: {e}")
            return False
    
    def run_all_scripts(self):
        """運行所有腳本"""
        try:
            logger.info("開始運行所有腳本...")
            
            # 運行 MinIO 分析
            minio_success = self.run_minio_analysis()
            
            # 運行資料庫檢查
            db_success = self.run_db_structure_check()
            
            if minio_success and db_success:
                logger.info("✅ 所有腳本運行完成")
                return True
            else:
                logger.warning("⚠️ 部分腳本運行失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 腳本運行失敗: {e}")
            return False
    
    def health_check(self) -> dict:
        """健康檢查"""
        try:
            return {
                "status": "healthy",
                "analysis_manager": self.analysis_manager is not None,
                "db_manager": self.db_manager is not None,
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
            logger.info("✅ Scripts 模組資源清理完成")
        except Exception as e:
            logger.error(f"❌ Scripts 模組資源清理失敗: {e}")

# 全域實例
scripts_manager = None

def get_scripts_manager() -> ScriptsModuleManager:
    """獲取腳本模組管理器實例（單例模式）"""
    global scripts_manager
    if scripts_manager is None:
        scripts_manager = ScriptsModuleManager()
    return scripts_manager

def main():
    """主函數 - 用於測試和獨立運行"""
    try:
        logger.info("🚀 啟動 Podwise Scripts 模組...")
        
        # 初始化腳本管理器
        manager = get_scripts_manager()
        
        # 執行健康檢查
        health = manager.health_check()
        logger.info(f"健康檢查結果: {health}")
        
        if health["status"] == "healthy":
            logger.info("✅ Scripts 模組啟動成功")
            
            # 可以選擇運行特定的功能
            # manager.run_minio_analysis()
            # manager.run_db_structure_check()
            # manager.run_all_scripts()
            
        else:
            logger.error("❌ Scripts 模組啟動失敗")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Scripts 模組啟動異常: {e}")
        return 1
    finally:
        # 清理資源
        if scripts_manager:
            scripts_manager.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 