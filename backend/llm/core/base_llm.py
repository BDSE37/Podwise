#!/usr/bin/env python3
"""
基礎 LLM 抽象類別

定義所有 LLM 提供商的通用介面，確保一致的 API 設計。

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置資料結構"""
    model_name: str
    model_id: str
    host: str
    port: int
    api_endpoint: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    priority: int = 1
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """生成請求資料結構"""
    prompt: str
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repetition_penalty: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None


@dataclass
class GenerationResponse:
    """生成回應資料結構"""
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    confidence: float
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelInfo:
    """模型資訊資料結構"""
    name: str
    id: str
    type: str  # "chat", "completion", "embedding"
    context_length: int
    max_tokens: int
    supported_features: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLM(ABC):
    """基礎 LLM 抽象類別"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化基礎 LLM
        
        Args:
            config: LLM 配置
        """
        self.config = config
        self.is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 性能統計
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "avg_response_time": 0.0
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化 LLM 服務
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """
        生成文本
        
        Args:
            request: 生成請求
            
        Returns:
            GenerationResponse: 生成回應
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        獲取文本嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 服務是否健康
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> ModelInfo:
        """
        獲取模型資訊
        
        Returns:
            ModelInfo: 模型資訊
        """
        pass
    
    async def process_request(self, request: GenerationRequest) -> GenerationResponse:
        """
        處理生成請求（包含重試邏輯）
        
        Args:
            request: 生成請求
            
        Returns:
            GenerationResponse: 生成回應
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        for attempt in range(self.config.retry_attempts):
            try:
                # 更新請求參數
                request = self._prepare_request(request)
                
                # 生成文本
                response = await self.generate_text(request)
                
                # 更新統計
                processing_time = time.time() - start_time
                response.processing_time = processing_time
                response.timestamp = datetime.now()
                
                self.stats["successful_requests"] += 1
                self.stats["total_tokens"] += response.tokens_used
                self._update_avg_response_time(processing_time)
                
                self.logger.info(
                    f"生成成功 - 模型: {response.model_used}, "
                    f"處理時間: {processing_time:.3f}s, "
                    f"Token 數: {response.tokens_used}"
                )
                
                return response
                
            except Exception as e:
                self.logger.warning(
                    f"生成失敗 (嘗試 {attempt + 1}/{self.config.retry_attempts}): {str(e)}"
                )
                
                if attempt == self.config.retry_attempts - 1:
                    self.stats["failed_requests"] += 1
                    raise
                
                # 等待後重試
                await asyncio.sleep(2 ** attempt)
    
    def _prepare_request(self, request: GenerationRequest) -> GenerationRequest:
        """
        準備請求參數
        
        Args:
            request: 原始請求
            
        Returns:
            GenerationRequest: 準備好的請求
        """
        # 使用配置中的預設值
        if request.max_tokens is None:
            request.max_tokens = self.config.max_tokens
        if request.temperature is None:
            request.temperature = self.config.temperature
        if request.top_p is None:
            request.top_p = self.config.top_p
        if request.top_k is None:
            request.top_k = self.config.top_k
        if request.repetition_penalty is None:
            request.repetition_penalty = self.config.repetition_penalty
        
        return request
    
    def _update_avg_response_time(self, new_time: float) -> None:
        """
        更新平均回應時間
        
        Args:
            new_time: 新的回應時間
        """
        total_requests = self.stats["successful_requests"]
        current_avg = self.stats["avg_response_time"]
        
        if total_requests == 1:
            self.stats["avg_response_time"] = new_time
        else:
            self.stats["avg_response_time"] = (
                (current_avg * (total_requests - 1) + new_time) / total_requests
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        return {
            **self.stats,
            "model_name": self.config.model_name,
            "is_initialized": self.is_initialized,
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "enabled": self.config.enabled
            }
        }
    
    async def cleanup(self) -> None:
        """清理資源"""
        self.logger.info(f"清理 {self.config.model_name} 資源")
        self.is_initialized = False
    
    def __str__(self) -> str:
        """字串表示"""
        return f"{self.__class__.__name__}({self.config.model_name})"
    
    def __repr__(self) -> str:
        """詳細字串表示"""
        return (
            f"{self.__class__.__name__}("
            f"model_name='{self.config.model_name}', "
            f"host='{self.config.host}:{self.config.port}', "
            f"enabled={self.config.enabled}"
            f")"
        ) 