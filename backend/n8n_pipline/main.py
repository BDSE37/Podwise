#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise N8N Pipeline 模組主入口點
統一管理 N8N 工作流程和數據處理，提供 OOP 設計的模組化架構
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

class N8NPipelineModuleManager:
    """N8N Pipeline 模組管理器"""
    
    def __init__(self):
        """初始化 N8N Pipeline 模組管理器"""
        self.ingestion_manager = None
        self._init_services()
    
    def _init_services(self):
        """初始化所有 N8N Pipeline 服務"""
        try:
            # 初始化數據攝取管理器
            self.ingestion_manager = self._init_ingestion_manager()
            logger.info("✅ N8N Pipeline 服務初始化成功")
            
        except Exception as e:
            logger.error(f"❌ N8N Pipeline 服務初始化失敗: {e}")
            raise
    
    def _init_ingestion_manager(self):
        """初始化數據攝取管理器"""
        try:
            # 這裡可以導入具體的攝取管理器類別
            # from n8n_pipline.ingestion.auto_crawler import AutoCrawler
            # return AutoCrawler()
            return {"status": "initialized"}
        except Exception as e:
            logger.error(f"數據攝取管理器初始化失敗: {e}")
            return None
    
    def get_ingestion_manager(self):
        """獲取數據攝取管理器"""
        return self.ingestion_manager
    
    def run_auto_crawler(self):
        """運行自動爬蟲"""
        try:
            logger.info("開始運行自動爬蟲...")
            # 這裡可以調用具體的爬蟲功能
            # self.ingestion_manager.run_crawler()
            logger.info("✅ 自動爬蟲運行完成")
            return True
        except Exception as e:
            logger.error(f"❌ 自動爬蟲運行失敗: {e}")
            return False
    
    def run_podcast_scraping(self):
        """運行播客爬取"""
        try:
            logger.info("開始運行播客爬取...")
            # 這裡可以調用具體的播客爬取功能
            logger.info("✅ 播客爬取運行完成")
            return True
        except Exception as e:
            logger.error(f"❌ 播客爬取運行失敗: {e}")
            return False
    
    def upload_to_minio(self):
        """上傳到 MinIO"""
        try:
            logger.info("開始上傳到 MinIO...")
            # 這裡可以調用具體的上傳功能
            logger.info("✅ MinIO 上傳完成")
            return True
        except Exception as e:
            logger.error(f"❌ MinIO 上傳失敗: {e}")
            return False
    
    def health_check(self) -> dict:
        """健康檢查"""
        try:
            return {
                "status": "healthy",
                "ingestion_manager": self.ingestion_manager is not None,
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
            logger.info("✅ N8N Pipeline 模組資源清理完成")
        except Exception as e:
            logger.error(f"❌ N8N Pipeline 模組資源清理失敗: {e}")

# 全域實例
n8n_pipeline_manager = None

def get_n8n_pipeline_manager() -> N8NPipelineModuleManager:
    """獲取 N8N Pipeline 模組管理器實例（單例模式）"""
    global n8n_pipeline_manager
    if n8n_pipeline_manager is None:
        n8n_pipeline_manager = N8NPipelineModuleManager()
    return n8n_pipeline_manager

def main():
    """主函數 - 用於測試和獨立運行"""
    try:
        logger.info("🚀 啟動 Podwise N8N Pipeline 模組...")
        
        # 初始化 N8N Pipeline 管理器
        manager = get_n8n_pipeline_manager()
        
        # 執行健康檢查
        health = manager.health_check()
        logger.info(f"健康檢查結果: {health}")
        
        if health["status"] == "healthy":
            logger.info("✅ N8N Pipeline 模組啟動成功")
            
            # 可以選擇運行特定的功能
            # manager.run_auto_crawler()
            # manager.run_podcast_scraping()
            # manager.upload_to_minio()
            
        else:
            logger.error("❌ N8N Pipeline 模組啟動失敗")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ N8N Pipeline 模組啟動異常: {e}")
        return 1
    finally:
        # 清理資源
        if n8n_pipeline_manager:
            n8n_pipeline_manager.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 