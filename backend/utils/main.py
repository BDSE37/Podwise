#!/usr/bin/env python3
"""
Podwise Utils 主模組

提供通用工具服務入口點。

作者: Podwise Team
版本: 1.0.0
"""

import logging
import sys
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from core_services import CoreServices
from audio_search import AudioSearchService
from common_utils import CommonUtils
from env_config import EnvironmentConfig
from intelligent_audio_search import IntelligentAudioSearch

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UtilsManager:
    """工具管理器"""
    
    def __init__(self):
        """初始化工具管理器"""
        self.core_services = None
        self.audio_search = None
        self.common_utils = None
        self.env_config = None
        self.intelligent_audio_search = None
        logger.info("🚀 初始化工具管理器...")
    
    def initialize(self) -> None:
        """初始化所有工具服務"""
        try:
            # 初始化核心服務
            self.core_services = CoreServices()
            logger.info("✅ 核心服務初始化完成")
            
            # 初始化音頻搜尋服務
            self.audio_search = AudioSearchService()
            logger.info("✅ 音頻搜尋服務初始化完成")
            
            # 初始化通用工具
            self.common_utils = CommonUtils()
            logger.info("✅ 通用工具初始化完成")
            
            # 初始化環境配置
            self.env_config = EnvironmentConfig()
            logger.info("✅ 環境配置初始化完成")
            
            # 初始化智能音頻搜尋
            self.intelligent_audio_search = IntelligentAudioSearch()
            logger.info("✅ 智能音頻搜尋初始化完成")
            
            logger.info("✅ 工具管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 工具管理器初始化失敗: {e}")
            raise
    
    def get_system_status(self) -> dict:
        """獲取系統狀態"""
        return {
            "core_services": self.core_services is not None,
            "audio_search": self.audio_search is not None,
            "common_utils": self.common_utils is not None,
            "env_config": self.env_config is not None,
            "intelligent_audio_search": self.intelligent_audio_search is not None,
            "version": "1.0.0"
        }
    
    def test_services(self) -> dict:
        """測試所有服務"""
        results = {}
        
        if self.core_services:
            results["core_services"] = "可用"
        
        if self.audio_search:
            results["audio_search"] = "可用"
        
        if self.common_utils:
            results["common_utils"] = "可用"
        
        if self.env_config:
            results["env_config"] = "可用"
        
        if self.intelligent_audio_search:
            results["intelligent_audio_search"] = "可用"
        
        return results


def main():
    """主函數"""
    try:
        # 初始化工具管理器
        manager = UtilsManager()
        manager.initialize()
        
        # 顯示系統狀態
        status = manager.get_system_status()
        logger.info(f"系統狀態: {status}")
        
        # 測試服務
        test_results = manager.test_services()
        logger.info(f"服務測試結果: {test_results}")
        
        logger.info("✅ 工具模組運行正常")
        
    except Exception as e:
        logger.error(f"❌ 工具模組執行失敗: {e}")
        raise


if __name__ == "__main__":
    main() 