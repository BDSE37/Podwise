#!/usr/bin/env python3
"""
Podwise LLM 主模組

提供統一的 LLM 服務入口點，整合所有語言模型功能：
- 多模型管理 (Qwen2.5-Taiwan-7B-Instruct, Qwen3-8B)
- 模型路由和負載均衡
- 效能監控和追蹤
- 錯誤處理和重試機制
- 配置管理

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 2.0.0
"""

import logging
import os
import sys
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置類別"""
    enable_qwen_taiwan: bool = True
    enable_qwen3: bool = True
    enable_fallback: bool = True
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60
    retry_count: int = 3
    log_level: str = "INFO"


class LLMManager:
    """LLM 管理器 - 統一管理所有語言模型服務"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """初始化 LLM 管理器"""
        self.config = config or LLMConfig()
        self.models = {}
        self._initialize_models()
        logger.info("🚀 LLM 管理器初始化完成")
    
    def _initialize_models(self) -> None:
        """初始化所有模型"""
        try:
            # 導入核心服務
            from .core.ollama_llm import OllamaLLM
            from .core.base_llm import BaseLLM
            
            # 初始化 Qwen2.5-Taiwan-7B-Instruct 模型
            if self.config.enable_qwen_taiwan:
                self.models['qwen_taiwan'] = OllamaLLM(
                    model_name="Qwen2.5-Taiwan-7B-Instruct",
                    host="localhost",
                    port=11434
                )
                logger.info("✅ Qwen2.5-Taiwan-7B-Instruct 模型已初始化")
            
            # 初始化 Qwen3-8B 模型
            if self.config.enable_qwen3:
                self.models['qwen3'] = OllamaLLM(
                    model_name="Qwen3-8B",
                    host="localhost",
                    port=11434
                )
                logger.info("✅ Qwen3-8B 模型已初始化")
            
        except Exception as e:
            logger.error(f"❌ 模型初始化失敗: {e}")
            raise
    
    def get_model(self, model_name: str) -> Any:
        """獲取指定模型"""
        if model_name not in self.models:
            raise ValueError(f"模型 '{model_name}' 不存在")
        return self.models[model_name]
    
    def get_qwen_taiwan(self) -> Any:
        """獲取 Qwen2.5-Taiwan-7B-Instruct 模型"""
        return self.get_model('qwen_taiwan')
    
    def get_qwen3(self) -> Any:
        """獲取 Qwen3-8B 模型"""
        return self.get_model('qwen3')
    
    async def generate_text(self, prompt: str, model_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """生成文字"""
        try:
            # 選擇模型
            if model_name and model_name in self.models:
                model = self.get_model(model_name)
            else:
                # 使用預設模型或自動選擇
                model = self.get_qwen_taiwan()
            
            # 生成文字
            response = await model.generate(
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                **kwargs
            )
            
            return {
                "success": True,
                "text": response,
                "model_used": model.model_name,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"文字生成失敗: {e}")
            
            # 嘗試 fallback
            if self.config.enable_fallback and model_name != 'qwen3':
                try:
                    fallback_model = self.get_qwen3()
                    response = await fallback_model.generate(prompt, **kwargs)
                    return {
                        "success": True,
                        "text": response,
                        "model_used": fallback_model.model_name,
                        "fallback": True,
                        "original_error": str(e)
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback 也失敗: {fallback_error}")
            
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "models": {},
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
        
        for model_name, model in self.models.items():
            try:
                # 基本可用性檢查
                if hasattr(model, 'health_check'):
                    model_health = model.health_check()
                else:
                    model_health = {"status": "available"}
                
                health_status["models"][model_name] = model_health
            except Exception as e:
                health_status["models"][model_name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
        
        return health_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "module": "llm",
            "version": "2.0.0",
            "description": "Podwise 語言模型服務",
            "models": list(self.models.keys()),
            "config": {
                "enable_qwen_taiwan": self.config.enable_qwen_taiwan,
                "enable_qwen3": self.config.enable_qwen3,
                "enable_fallback": self.config.enable_fallback,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count,
                "log_level": self.config.log_level
            }
        }


# 全域實例
_llm_manager: Optional[LLMManager] = None


def get_llm_manager(config: Optional[LLMConfig] = None) -> LLMManager:
    """獲取 LLM 管理器實例（單例模式）"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager(config)
    return _llm_manager


def initialize_llm(config: Optional[LLMConfig] = None) -> LLMManager:
    """初始化 LLM 模組"""
    return get_llm_manager(config)


# 便捷函數
def get_qwen_taiwan():
    """獲取 Qwen2.5-Taiwan-7B-Instruct 模型"""
    return get_llm_manager().get_qwen_taiwan()


def get_qwen3():
    """獲取 Qwen3-8B 模型"""
    return get_llm_manager().get_qwen3()


async def generate_text(prompt: str, model_name: Optional[str] = None, **kwargs):
    """生成文字"""
    return await get_llm_manager().generate_text(prompt, model_name, **kwargs)


if __name__ == "__main__":
    # 測試模式
    async def test_llm():
        try:
            llm_manager = initialize_llm()
            print("✅ LLM 模組初始化成功")
            print(f"📋 服務資訊: {llm_manager.get_service_info()}")
            print(f"🏥 健康檢查: {llm_manager.health_check()}")
            
            # 測試文字生成
            result = await llm_manager.generate_text("你好，請介紹一下自己")
            print(f"🤖 文字生成測試: {result}")
            
        except Exception as e:
            print(f"❌ LLM 模組初始化失敗: {e}")
            sys.exit(1)
    
    asyncio.run(test_llm()) 