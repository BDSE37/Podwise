#!/usr/bin/env python3
"""
Podwise Backend 主模組

整合所有 backend 子模組的統一入口點。

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackendManager:
    """Backend 管理器"""
    
    def __init__(self):
        """初始化 Backend 管理器"""
        self.modules = {}
        self.is_initialized = False
        logger.info("🚀 初始化 Podwise Backend 管理器...")
    
    async def initialize_modules(self) -> None:
        """初始化所有模組"""
        try:
            logger.info("📋 開始初始化所有 Backend 模組...")
            
            # 初始化各模組
            modules_to_init = [
                ("api", "API 服務"),
                ("config", "配置管理"),
                ("llm", "LLM 服務"),
                ("ml_pipeline", "ML Pipeline"),
                ("rag_pipeline", "RAG Pipeline"),
                ("stt", "語音轉文字"),
                ("tts", "文字轉語音"),
                ("utils", "通用工具"),
                ("vector_pipeline", "向量處理")
            ]
            
            for module_name, module_desc in modules_to_init:
                try:
                    logger.info(f"🔄 初始化 {module_desc}...")
                    # 這裡可以根據需要實際初始化各模組
                    self.modules[module_name] = {
                        "status": "initialized",
                        "description": module_desc,
                        "version": "1.0.0"
                    }
                    logger.info(f"✅ {module_desc} 初始化完成")
                except Exception as e:
                    logger.warning(f"⚠️ {module_desc} 初始化失敗: {e}")
                    self.modules[module_name] = {
                        "status": "failed",
                        "description": module_desc,
                        "error": str(e)
                    }
            
            self.is_initialized = True
            logger.info("✅ 所有 Backend 模組初始化完成")
            
        except Exception as e:
            logger.error(f"❌ Backend 管理器初始化失敗: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        if not self.is_initialized:
            return {
                "is_ready": False,
                "modules": {},
                "version": "1.0.0",
                "message": "系統尚未初始化"
            }
        
        return {
            "is_ready": True,
            "modules": self.modules,
            "version": "1.0.0",
            "message": "系統運行正常"
        }
    
    def get_module_status(self, module_name: str) -> Optional[Dict[str, Any]]:
        """獲取特定模組狀態"""
        return self.modules.get(module_name)
    
    async def run_module(self, module_name: str, *args, **kwargs) -> Any:
        """運行特定模組"""
        if not self.is_initialized:
            raise RuntimeError("Backend 管理器尚未初始化")
        
        if module_name not in self.modules:
            raise ValueError(f"模組 {module_name} 不存在")
        
        module_info = self.modules[module_name]
        if module_info["status"] != "initialized":
            raise RuntimeError(f"模組 {module_name} 狀態異常: {module_info['status']}")
        
        logger.info(f"🔄 運行模組: {module_name}")
        
        # 這裡可以根據模組名稱調用相應的功能
        if module_name == "rag_pipeline":
            return await self._run_rag_pipeline(*args, **kwargs)
        elif module_name == "ml_pipeline":
            return await self._run_ml_pipeline(*args, **kwargs)
        elif module_name == "api":
            return await self._run_api_server(*args, **kwargs)
        else:
            return {"message": f"模組 {module_name} 運行成功", "args": args, "kwargs": kwargs}
    
    async def _run_rag_pipeline(self, *args, **kwargs) -> Dict[str, Any]:
        """運行 RAG Pipeline"""
        return {
            "module": "rag_pipeline",
            "status": "running",
            "message": "RAG Pipeline 運行中"
        }
    
    async def _run_ml_pipeline(self, *args, **kwargs) -> Dict[str, Any]:
        """運行 ML Pipeline"""
        return {
            "module": "ml_pipeline",
            "status": "running",
            "message": "ML Pipeline 運行中"
        }
    
    async def _run_api_server(self, *args, **kwargs) -> Dict[str, Any]:
        """運行 API 服務器"""
        return {
            "module": "api",
            "status": "running",
            "message": "API 服務器運行中"
        }
    
    async def close(self) -> None:
        """關閉所有連接"""
        logger.info("🔒 關閉 Backend 管理器...")
        self.modules.clear()
        self.is_initialized = False
        logger.info("✅ Backend 管理器已關閉")


# 全域管理器實例
_backend_manager: Optional[BackendManager] = None


async def get_backend_manager() -> BackendManager:
    """獲取 Backend 管理器實例"""
    global _backend_manager
    
    if _backend_manager is None:
        _backend_manager = BackendManager()
        await _backend_manager.initialize_modules()
    
    return _backend_manager


async def close_backend_manager() -> None:
    """關閉 Backend 管理器"""
    global _backend_manager
    
    if _backend_manager:
        await _backend_manager.close()
        _backend_manager = None


def print_module_structure():
    """打印模組結構"""
    logger.info("📁 Podwise Backend 模組結構:")
    logger.info("├── api/          - API 服務")
    logger.info("├── config/       - 配置管理")
    logger.info("├── llm/          - LLM 服務")
    logger.info("├── ml_pipeline/  - ML Pipeline")
    logger.info("├── rag_pipeline/ - RAG Pipeline")
    logger.info("├── stt/          - 語音轉文字")
    logger.info("├── tts/          - 文字轉語音")
    logger.info("├── utils/        - 通用工具")
    logger.info("└── vector_pipeline/ - 向量處理")


async def main():
    """主函數"""
    try:
        # 顯示模組結構
        print_module_structure()
        
        # 初始化管理器
        manager = await get_backend_manager()
        
        # 顯示系統狀態
        status = manager.get_system_status()
        logger.info(f"系統狀態: {status}")
        
        # 測試各模組
        for module_name in manager.modules.keys():
            try:
                result = await manager.run_module(module_name, test=True)
                logger.info(f"✅ {module_name}: {result}")
            except Exception as e:
                logger.warning(f"⚠️ {module_name}: {e}")
        
        logger.info("✅ Podwise Backend 運行正常")
        
    except Exception as e:
        logger.error(f"❌ Podwise Backend 執行失敗: {e}")
        raise
    finally:
        # 關閉管理器
        await close_backend_manager()


if __name__ == "__main__":
    asyncio.run(main()) 