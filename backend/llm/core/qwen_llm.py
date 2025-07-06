#!/usr/bin/env python3
"""
Qwen LLM 實作

支援 Qwen2.5-7b-Taiwan 和 Qwen3:8b 模型。

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
class QwenModelConfig(LLMConfig):
    """Qwen 模型配置"""
    api_key: Optional[str] = None
    use_chat_format: bool = True
    trust_remote_code: bool = True


class QwenLLM(BaseLLM):
    """Qwen LLM 實作類別"""
    
    def __init__(self, config: QwenModelConfig):
        """
        初始化 Qwen LLM
        
        Args:
            config: Qwen 模型配置
        """
        super().__init__(config)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.api_base = f"http://{config.host}:{config.port}"
        
        # Qwen 特定配置
        self.use_chat_format = config.use_chat_format
        self.trust_remote_code = config.trust_remote_code
    
    async def initialize(self) -> bool:
        """
        初始化 Qwen LLM 服務
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info(f"初始化 Qwen LLM: {self.config.model_name}")
            
            # 創建 HTTP 會話
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            
            # 健康檢查
            if not await self.health_check():
                raise RuntimeError("Qwen LLM 健康檢查失敗")
            
            self.is_initialized = True
            self.logger.info(f"Qwen LLM {self.config.model_name} 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Qwen LLM 初始化失敗: {str(e)}")
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
            raise RuntimeError("Qwen LLM 尚未初始化")
        
        start_time = time.time()
        
        try:
            # 準備請求 payload
            payload = self._prepare_chat_payload(request)
            
            # 發送請求
            url = f"{self.api_base}{self.config.api_endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}" if self.config.api_key else ""
            }
            
            async with self.http_session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Qwen API 錯誤: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 解析回應
                return self._parse_response(result, time.time() - start_time)
                
        except Exception as e:
            self.logger.error(f"Qwen 文本生成失敗: {str(e)}")
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
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "repetition_penalty": request.repetition_penalty,
            "stream": False
        }
        
        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}
        
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
            choice = result["choices"][0]
            message = choice["message"]
            
            return GenerationResponse(
                text=message["content"],
                model_used=self.config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                processing_time=processing_time,
                confidence=self._calculate_confidence(message["content"]),
                finish_reason=choice.get("finish_reason", "stop"),
                metadata={
                    "model_id": self.config.model_id,
                    "api_version": "v1",
                    "response_format": "chat"
                }
            )
            
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"解析 Qwen 回應失敗: {str(e)}")
    
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
            raise RuntimeError("Qwen LLM 尚未初始化")
        
        try:
            # 使用 Qwen 的嵌入 API
            url = f"{self.api_base}/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}" if self.config.api_key else ""
            }
            
            payload = {
                "model": f"{self.config.model_id}-embedding",
                "input": texts
            }
            
            async with self.http_session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Qwen 嵌入 API 錯誤: {response.status} - {error_text}")
                
                result = await response.json()
                return [item["embedding"] for item in result["data"]]
                
        except Exception as e:
            self.logger.error(f"Qwen 嵌入獲取失敗: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 服務是否健康
        """
        try:
            url = f"{self.api_base}/health"
            async with self.http_session.get(url) as response:
                return response.status == 200
        except Exception as e:
            self.logger.warning(f"Qwen 健康檢查失敗: {str(e)}")
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
            context_length=8192,  # Qwen 預設上下文長度
            max_tokens=self.config.max_tokens,
            supported_features=["chat", "completion", "embedding"],
            metadata={
                "provider": "Qwen",
                "version": "2.5/3.0",
                "language": "zh-TW, en",
                "trust_remote_code": self.trust_remote_code
            }
        )
    
    async def cleanup(self) -> None:
        """清理資源"""
        await super().cleanup()
        
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
        
        self.logger.info(f"Qwen LLM {self.config.model_name} 資源已清理")


class QwenTaiwanLLM(QwenLLM):
    """Qwen2.5-7b-Taiwan 專用實作"""
    
    def __init__(self, config: QwenModelConfig):
        """
        初始化 Qwen Taiwan LLM
        
        Args:
            config: Qwen 模型配置
        """
        # 設定 Taiwan 特定配置
        config.model_name = "Qwen2.5-7b-Taiwan"
        config.model_id = "qwen2.5:7b-taiwan"
        config.metadata["region"] = "Taiwan"
        config.metadata["language_focus"] = "zh-TW"
        
        super().__init__(config)
    
    def _prepare_chat_payload(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        準備 Taiwan 版本的聊天 payload
        
        Args:
            request: 生成請求
            
        Returns:
            Dict[str, Any]: 請求 payload
        """
        payload = super()._prepare_chat_payload(request)
        
        # 添加 Taiwan 特定配置
        payload["metadata"] = {
            "region": "Taiwan",
            "language": "zh-TW",
            "model_variant": "taiwan"
        }
        
        return payload


class Qwen3LLM(QwenLLM):
    """Qwen3:8b 專用實作"""
    
    def __init__(self, config: QwenModelConfig):
        """
        初始化 Qwen3 LLM
        
        Args:
            config: Qwen 模型配置
        """
        # 設定 Qwen3 特定配置
        config.model_name = "Qwen3:8b"
        config.model_id = "qwen3:8b"
        config.metadata["version"] = "3.0"
        config.metadata["architecture"] = "transformer"
        
        super().__init__(config)
    
    async def get_model_info(self) -> ModelInfo:
        """
        獲取 Qwen3 模型資訊
        
        Returns:
            ModelInfo: 模型資訊
        """
        return ModelInfo(
            name=self.config.model_name,
            id=self.config.model_id,
            type="chat",
            context_length=32768,  # Qwen3 支援更長的上下文
            max_tokens=self.config.max_tokens,
            supported_features=["chat", "completion", "embedding", "function_calling"],
            metadata={
                "provider": "Qwen",
                "version": "3.0",
                "language": "multilingual",
                "architecture": "transformer",
                "context_length": 32768
            }
        ) 