#!/usr/bin/env python3
"""
本地 Ollama LLM 服務類別
完全本地化的語言模型服務，使用 Ollama 作為後端
不依賴任何外部 API，支援多種本地模型
"""

import os
import logging
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

# 導入基礎服務
from ..core.base_service import BaseService, ServiceConfig, ServiceResponse

logger = logging.getLogger(__name__)

@dataclass
class OllamaModelConfig:
    """Ollama 模型配置資料結構"""
    model_name: str
    model_id: str
    host: str
    port: int
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    enabled: bool = True

@dataclass
class OllamaRequest:
    """Ollama 請求資料結構"""
    prompt: str
    model: str
    system: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False

@dataclass
class OllamaResponse:
    """Ollama 回應資料結構"""
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    done: bool = True

class OllamaService(BaseService):
    """本地 Ollama LLM 服務類別"""
    
    def __init__(self, config: ServiceConfig):
        """
        初始化 Ollama 服務
        
        Args:
            config: 服務配置
        """
        super().__init__(config)
        
        # 初始化模型配置
        self.models: Dict[str, OllamaModelConfig] = {}
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Ollama 配置
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        
        # 載入模型配置
        self._load_model_configs()
        
        self.logger.info(f"Ollama 服務初始化完成，可用模型: {list(self.models.keys())}")
        self.logger.info(f"Ollama 主機: {self.ollama_host}")
        self.logger.info(f"預設模型: {self.default_model}")
    
    def _load_model_configs(self):
        """載入 Ollama 模型配置"""
        # Qwen2.5 模型配置
        self.models["qwen2.5:7b"] = OllamaModelConfig(
            model_name="Qwen2.5-7B",
            model_id="qwen2.5:7b",
            host=self.ollama_host.replace("http://", "").replace("https://", "").split(":")[0],
            port=11434,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        # Llama3.2 模型配置
        self.models["llama3.2:3b"] = OllamaModelConfig(
            model_name="Llama3.2-3B",
            model_id="llama3.2:3b",
            host=self.ollama_host.replace("http://", "").replace("https://", "").split(":")[0],
            port=11434,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        # DeepSeek 模型配置
        self.models["deepseek-coder:6.7b"] = OllamaModelConfig(
            model_name="DeepSeek-Coder-6.7B",
            model_id="deepseek-coder:6.7b",
            host=self.ollama_host.replace("http://", "").replace("https://", "").split(":")[0],
            port=11434,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
        
        # 中文模型配置
        self.models["qwen2.5:7b-chinese"] = OllamaModelConfig(
            model_name="Qwen2.5-7B-Chinese",
            model_id="qwen2.5:7b",
            host=self.ollama_host.replace("http://", "").replace("https://", "").split(":")[0],
            port=11434,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
    
    async def initialize(self) -> bool:
        """
        初始化服務
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 創建 HTTP 會話
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # 測試 Ollama 連接
            await self._test_ollama_connection()
            
            # 檢查可用模型
            await self._check_available_models()
            
            self.logger.info("Ollama 服務初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Ollama 服務初始化失敗: {str(e)}")
            return False
    
    async def _test_ollama_connection(self):
        """測試 Ollama 連接"""
        try:
            url = f"{self.ollama_host}/api/tags"
            async with self.http_session.get(url, timeout=10) as response:
                if response.status == 200:
                    self.logger.info("Ollama 連接正常")
                else:
                    self.logger.warning(f"Ollama 連接異常: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Ollama 連接失敗: {str(e)}")
            raise
    
    async def _check_available_models(self):
        """檢查可用的 Ollama 模型"""
        try:
            url = f"{self.ollama_host}/api/tags"
            async with self.http_session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model["name"] for model in data.get("models", [])]
                    self.logger.info(f"可用的 Ollama 模型: {available_models}")
                    
                    # 更新模型狀態
                    for model_id, config in self.models.items():
                        if model_id in available_models:
                            config.enabled = True
                            self.logger.info(f"模型 {model_id} 可用")
                        else:
                            config.enabled = False
                            self.logger.warning(f"模型 {model_id} 不可用")
                            
        except Exception as e:
            self.logger.error(f"檢查可用模型失敗: {str(e)}")
    
    async def process_request(self, request_data: Any) -> ServiceResponse:
        """
        處理請求
        
        Args:
            request_data: 請求數據
            
        Returns:
            ServiceResponse: 服務回應
        """
        start_time = time.time()
        
        try:
            # 解析請求
            if isinstance(request_data, dict):
                request = OllamaRequest(**request_data)
            elif isinstance(request_data, OllamaRequest):
                request = request_data
            else:
                raise ValueError("無效的請求格式")
            
            # 生成回應
            response = await self.generate_text(request)
            
            processing_time = time.time() - start_time
            
            return self._create_response(
                success=True,
                data={
                    "text": response.text,
                    "model_used": response.model_used,
                    "tokens_used": response.tokens_used,
                    "processing_time": processing_time,
                    "done": response.done
                },
                message="文字生成成功"
            )
            
        except Exception as e:
            self.logger.error(f"處理請求失敗: {str(e)}")
            return self._create_response(
                success=False,
                error=str(e),
                message="文字生成失敗"
            )
    
    async def generate_text(self, request: OllamaRequest) -> OllamaResponse:
        """
        生成文字
        
        Args:
            request: Ollama 請求
            
        Returns:
            OllamaResponse: Ollama 回應
        """
        start_time = time.time()
        
        # 選擇模型
        model_id = request.model if request.model else self.default_model
        
        if model_id not in self.models:
            raise ValueError(f"不支援的模型: {model_id}")
        
        model_config = self.models[model_id]
        if not model_config.enabled:
            raise ValueError(f"模型 {model_id} 不可用")
        
        # 準備請求資料
        payload = {
            "model": model_id,
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {
                "num_predict": model_config.max_tokens,
                "temperature": model_config.temperature,
                "top_p": model_config.top_p,
                "top_k": model_config.top_k,
                "repeat_penalty": model_config.repeat_penalty
            }
        }
        
        if request.system:
            payload["system"] = request.system
        
        if request.options:
            payload["options"].update(request.options)
        
        # 發送請求到 Ollama
        url = f"{self.ollama_host}/api/generate"
        
        try:
            async with self.http_session.post(url, json=payload, timeout=60) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API 錯誤: {response.status}")
                
                data = await response.json()
                
                processing_time = time.time() - start_time
                
                return OllamaResponse(
                    text=data.get("response", ""),
                    model_used=model_id,
                    tokens_used=data.get("eval_count", 0),
                    processing_time=processing_time,
                    done=data.get("done", True)
                )
                
        except Exception as e:
            self.logger.error(f"生成文字失敗: {str(e)}")
            raise
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        獲取可用模型列表
        
        Returns:
            List[Dict[str, Any]]: 模型列表
        """
        try:
            url = f"{self.ollama_host}/api/tags"
            async with self.http_session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"獲取可用模型失敗: {str(e)}")
            return []
    
    async def pull_model(self, model_id: str) -> bool:
        """
        拉取模型
        
        Args:
            model_id: 模型 ID
            
        Returns:
            bool: 是否成功
        """
        try:
            url = f"{self.ollama_host}/api/pull"
            payload = {"name": model_id}
            
            async with self.http_session.post(url, json=payload, timeout=300) as response:
                if response.status == 200:
                    self.logger.info(f"模型 {model_id} 拉取成功")
                    return True
                else:
                    self.logger.error(f"模型 {model_id} 拉取失敗: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"拉取模型失敗: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 服務是否健康
        """
        try:
            url = f"{self.ollama_host}/api/tags"
            async with self.http_session.get(url, timeout=5) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {str(e)}")
            return False
    
    async def cleanup(self) -> bool:
        """
        清理資源
        
        Returns:
            bool: 清理是否成功
        """
        try:
            if self.http_session:
                await self.http_session.close()
            return True
            
        except Exception as e:
            self.logger.error(f"清理資源失敗: {str(e)}")
            return False

async def create_ollama_service(host: str = "0.0.0.0", port: int = 8004) -> OllamaService:
    """
    創建 Ollama 服務實例
    
    Args:
        host: 服務主機
        port: 服務端口
        
    Returns:
        OllamaService: Ollama 服務實例
    """
    config = ServiceConfig(
        name="ollama-service",
        host=host,
        port=port,
        timeout=60,
        max_workers=10
    )
    
    service = OllamaService(config)
    
    if await service.initialize():
        return service
    else:
        raise Exception("Ollama 服務初始化失敗")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        """主函數"""
        try:
            service = await create_ollama_service()
            await service.start()
            
        except KeyboardInterrupt:
            print("服務停止中...")
        except Exception as e:
            print(f"服務錯誤: {str(e)}")
    
    asyncio.run(main()) 