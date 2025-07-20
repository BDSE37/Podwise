#!/usr/bin/env python3
"""
LLM 配置檔案

配置本地 Hugging Face 模型設定

作者: Podwise Team
版本: 1.0.0
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HuggingFaceLLMConfig:
    """Hugging Face LLM 配置"""
    model_name: str = "gpt-3.5-turbo"
    model_id: str = "gpt-3.5-turbo"
    model_path: str = "/home/bai/Desktop/Podwise/backend/llm/models/Qwen2.5-Taiwan-7B-Instruct/models--benchang1110--Qwen2.5-Taiwan-7B-Instruct/snapshots/fbded9aca0a2d45a930dff9a7200143cd3f6b8f9"
    device: str = "cpu"  # 改為 CPU 以避免 CUDA 記憶體不足
    torch_dtype: str = "float32"  # CPU 使用 float32
    trust_remote_code: bool = True
    use_cache: bool = True
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    timeout: int = 30


@dataclass
class OllamaLLMConfig:
    """Ollama LLM 配置（備用）"""
    model_name: str = "gpt-3.5-turbo"
    model_id: str = "gpt-3.5-turbo"
    host: str = "localhost"
    port: int = 11434
    timeout: int = 30
    use_chat_format: bool = True
    keep_alive: str = "5m"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1


class LLMConfigManager:
    """LLM 配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.hf_config = HuggingFaceLLMConfig()
        self.ollama_config = OllamaLLMConfig()
        
        # 檢查模型路徑是否存在
        self._validate_model_paths()
    
    def _validate_model_paths(self):
        """驗證模型路徑"""
        if not os.path.exists(self.hf_config.model_path):
            print(f"⚠️ 警告: Hugging Face 模型路徑不存在: {self.hf_config.model_path}")
            # 嘗試找到替代路徑
            alternative_paths = [
                "/home/bai/Desktop/Podwise/backend/llm/models/Qwen3-8B/models--Qwen--Qwen3-8B/snapshots/9c925d64d72725edaf899c6cb9c377fd0709d9c5",
                "/home/bai/Desktop/Podwise/Qwen2.5-Taiwan-7B-Instruct",
                "/home/bai/Desktop/Podwise/Qwen3-8B"
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    print(f"✅ 找到替代模型路徑: {alt_path}")
                    self.hf_config.model_path = alt_path
                    if "Qwen3-8B" in alt_path:
                        self.hf_config.model_name = "Qwen3-8B"
                        self.hf_config.model_id = "qwen3-8b"
                    break
            else:
                print("❌ 無法找到有效的模型路徑")
    
    def get_huggingface_config(self) -> HuggingFaceLLMConfig:
        """獲取 Hugging Face 配置"""
        return self.hf_config
    
    def get_ollama_config(self) -> OllamaLLMConfig:
        """獲取 Ollama 配置"""
        return self.ollama_config
    
    def get_preferred_config(self) -> Dict[str, Any]:
        """獲取首選配置（優先使用 GPT-3.5）"""
        return {
            "provider": "openai",
            "config": self.ollama_config
        }


# 全域配置實例
llm_config_manager = LLMConfigManager()


def get_llm_config() -> Dict[str, Any]:
    """獲取 LLM 配置"""
    return llm_config_manager.get_preferred_config()


def get_huggingface_config() -> HuggingFaceLLMConfig:
    """獲取 Hugging Face 配置"""
    return llm_config_manager.get_huggingface_config()


def get_ollama_config() -> OllamaLLMConfig:
    """獲取 Ollama 配置"""
    return llm_config_manager.get_ollama_config() 