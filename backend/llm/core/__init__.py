#!/usr/bin/env python3
"""
LLM Core 模組

提供 LLM 服務的核心組件和抽象類別。

作者: Podwise Team
版本: 1.0.0
"""

from .base_llm import (
    BaseLLM,
    LLMConfig,
    GenerationRequest,
    GenerationResponse,
    ModelInfo
)

from .qwen_llm import (
    QwenLLM,
    QwenModelConfig,
    QwenTaiwanLLM,
    Qwen3LLM
)

from .ollama_llm import (
    OllamaLLM,
    OllamaConfig
)

__version__ = "1.0.0"
__author__ = "Podwise Team"

__all__ = [
    # 基礎類別
    "BaseLLM",
    "LLMConfig",
    "GenerationRequest",
    "GenerationResponse",
    "ModelInfo",
    
    # Qwen 實作
    "QwenLLM",
    "QwenModelConfig",
    "QwenTaiwanLLM",
    "Qwen3LLM",
    
    # Ollama 實作
    "OllamaLLM",
    "OllamaConfig"
] 