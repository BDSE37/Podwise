#!/usr/bin/env python3
"""
Ollama LLM 實作

支援 Ollama 本地模型部署。

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_llm import BaseLLM, LLMConfig, GenerationRequest, GenerationResponse, ModelInfo


@dataclass
class OllamaConfig(LLMConfig):
    """Ollama 模型配置"""
    api_key: Optional[str] = None
    use_chat_format: bool = True
    keep_alive: str = "5m"


class OllamaLLM(BaseLLM):
    """Ollama LLM 實作類別"""
    
    def __init__(self, config: OllamaConfig):
        """
        初始化 Ollama LLM
        
        Args:
            config: Ollama 模型配置
        """
        super().__init__(config)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.api_base = f"http://{config.host}:{config.port}"
        
        # Ollama 特定配置
        self.use_chat_format = config.use_chat_format
        self.keep_alive = config.keep_alive
    
    async def initialize(self) -> bool:
        """
        初始化 Ollama LLM 服務
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info(f"初始化 Ollama LLM: {self.config.model_name}")
            
            # 創建 HTTP 會話
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            
            # 健康檢查
            if not await self.health_check():
                raise RuntimeError("Ollama LLM 健康檢查失敗")
            
            # 檢查模型是否可用
            if not await self._check_model_availability():
                raise RuntimeError(f"Ollama 模型 {self.config.model_id} 不可用")
            
            self.is_initialized = True
            self.logger.info(f"Ollama LLM {self.config.model_name} 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Ollama LLM 初始化失敗: {str(e)}")
            return False
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """
        生成文本
        
        Args:
            request: 生成請求
            
        Returns:
            GenerationResponse: 生成回應
        """
        if not self.is_initialized:
            raise RuntimeError("Ollama LLM 尚未初始化")
        
        start_time = time.time()
        
        try:
            # 準備請求 payload
            payload = self._prepare_chat_payload(request)
            
            # 發送請求
            url = f"{self.api_base}/api/chat"
            headers = {"Content-Type": "application/json"}
            
            async with self.http_session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama API 錯誤: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 解析回應
                return self._parse_response(result, time.time() - start_time)
                
        except Exception as e:
            self.logger.error(f"Ollama 文本生成失敗: {str(e)}")
            raise
    
    def _prepare_chat_payload(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        準備聊天格式的請求 payload
        
        Args:
            request: 生成請求
            
        Returns:
            Dict[str, Any]: 請求 payload
        """
        messages = []
        
        # 添加系統提示
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 添加用戶提示
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        payload = {
            "model": self.config.model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
                "repeat_penalty": request.repetition_penalty,
                "keep_alive": self.keep_alive
            }
        }
        
        # 移除 None 值
        payload["options"] = {k: v for k, v in payload["options"].items() if v is not None}
        
        return payload
    
    def _parse_response(self, result: Dict[str, Any], processing_time: float) -> GenerationResponse:
        """
        解析 API 回應
        
        Args:
            result: API 回應
            processing_time: 處理時間
            
        Returns:
            GenerationResponse: 生成回應
        """
        try:
            message = result["message"]
            
            return GenerationResponse(
                text=message["content"],
                model_used=self.config.model_name,
                tokens_used=result.get("eval_count", 0),
                processing_time=processing_time,
                confidence=self._calculate_confidence(message["content"]),
                finish_reason=result.get("done_reason", "stop"),
                metadata={
                    "model_id": self.config.model_id,
                    "api_version": "v1",
                    "response_format": "chat",
                    "provider": "ollama"
                }
            )
            
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"解析 Ollama 回應失敗: {str(e)}")
    
    def _calculate_confidence(self, text: str) -> float:
        """
        計算回應信心度
        
        Args:
            text: 生成文本
            
        Returns:
            float: 信心度分數 (0-1)
        """
        # 簡單的信心度計算邏輯
        if not text:
            return 0.0
        
        # 基於文本長度和內容的簡單評估
        length_score = min(len(text) / 100, 1.0)  # 長度分數
        content_score = 0.8  # 預設內容分數
        
        return (length_score + content_score) / 2
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        獲取文本嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not self.is_initialized:
            raise RuntimeError("Ollama LLM 尚未初始化")
        
        try:
            # 使用 Ollama 的嵌入 API
            url = f"{self.api_base}/api/embeddings"
            headers = {"Content-Type": "application/json"}
            
            embeddings = []
            
            for text in texts:
                payload = {
                    "model": self.config.model_id,
                    "prompt": text
                }
                
                async with self.http_session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama 嵌入 API 錯誤: {response.status} - {error_text}")
                    
                    result = await response.json()
                    embeddings.append(result["embedding"])
            
            return embeddings
                
        except Exception as e:
            self.logger.error(f"Ollama 嵌入獲取失敗: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 服務是否健康
        """
        try:
            url = f"{self.api_base}/api/tags"
            async with self.http_session.get(url) as response:
                return response.status == 200
        except Exception as e:
            self.logger.warning(f"Ollama 健康檢查失敗: {str(e)}")
            return False
    
    async def _check_model_availability(self) -> bool:
        """
        檢查模型是否可用
        
        Returns:
            bool: 模型是否可用
        """
        try:
            url = f"{self.api_base}/api/tags"
            async with self.http_session.get(url) as response:
                if response.status != 200:
                    return False
                
                result = await response.json()
                models = result.get("models", [])
                
                for model in models:
                    if model["name"] == self.config.model_id:
                        return True
                
                return False
                
        except Exception as e:
            self.logger.warning(f"檢查模型可用性失敗: {str(e)}")
            return False
    
    async def get_model_info(self) -> ModelInfo:
        """
        獲取模型資訊
        
        Returns:
            ModelInfo: 模型資訊
        """
        return ModelInfo(
            name=self.config.model_name,
            id=self.config.model_id,
            type="chat",
            context_length=4096,  # Ollama 預設上下文長度
            max_tokens=self.config.max_tokens,
            supported_features=["chat", "completion", "embedding"],
            metadata={
                "provider": "Ollama",
                "version": "latest",
                "language": "multilingual",
                "deployment": "local",
                "keep_alive": self.keep_alive
            }
        )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出可用模型
        
        Returns:
            List[Dict[str, Any]]: 模型列表
        """
        try:
            url = f"{self.api_base}/api/tags"
            async with self.http_session.get(url) as response:
                if response.status != 200:
                    return []
                
                result = await response.json()
                return result.get("models", [])
                
        except Exception as e:
            self.logger.error(f"獲取模型列表失敗: {str(e)}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        拉取模型
        
        Args:
            model_name: 模型名稱
            
        Returns:
            bool: 是否成功
        """
        try:
            url = f"{self.api_base}/api/pull"
            payload = {"name": model_name}
            headers = {"Content-Type": "application/json"}
            
            async with self.http_session.post(url, json=payload, headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"拉取模型失敗: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """清理資源"""
        await super().cleanup()
        
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
        
        self.logger.info(f"Ollama LLM {self.config.model_name} 資源已清理") 