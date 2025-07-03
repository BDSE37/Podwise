#!/usr/bin/env python3
"""
LLM 服務類別
整合多種語言模型，提供統一的推理介面
支援 Qwen3、DeepSeek、Llama3 等模型
整合 Langfuse 追蹤功能
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

# 導入 Langfuse
from langfuse import Langfuse
from langfuse.model import CreateTrace

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """模型配置資料結構"""
    model_name: str
    model_id: str
    host: str
    port: int
    api_endpoint: str
    max_tokens: int = 2048
    temperature: float = 0.7
    priority: int = 1
    enabled: bool = True

@dataclass
class GenerationRequest:
    """生成請求資料結構"""
    prompt: str
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None  # Langfuse 追蹤 ID

@dataclass
class GenerationResponse:
    """生成回應資料結構"""
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None  # Langfuse 追蹤 ID

class LLMService(BaseService):
    """LLM 服務類別"""
    
    def __init__(self, config: ServiceConfig):
        """
        初始化 LLM 服務
        
        Args:
            config: 服務配置
        """
        super().__init__(config)
        
        # 初始化模型配置
        self.models: Dict[str, ModelConfig] = {}
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # 初始化 Langfuse
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "http://langfuse:3000")
        )
        
        # 載入模型配置
        self._load_model_configs()
        
        self.logger.info(f"LLM 服務初始化完成，可用模型: {list(self.models.keys())}")
        self.logger.info("Langfuse 追蹤功能已啟用")
    
    def _load_model_configs(self):
        """載入模型配置"""
        # Qwen3 模型配置
        self.models["qwen3"] = ModelConfig(
            model_name="Qwen3",
            model_id="qwen2.5:7b",
            host=os.getenv("QWEN3_HOST", "llm"),
            port=int(os.getenv("QWEN3_PORT", "8000")),
            api_endpoint="/v1/chat/completions",
            max_tokens=2048,
            temperature=0.7,
            priority=1
        )
        
        # DeepSeek 模型配置
        self.models["deepseek"] = ModelConfig(
            model_name="DeepSeek",
            model_id="deepseek-coder:6.7b",
            host=os.getenv("DEEPSEEK_HOST", "llm"),
            port=int(os.getenv("DEEPSEEK_PORT", "8000")),
            api_endpoint="/v1/chat/completions",
            max_tokens=2048,
            temperature=0.7,
            priority=2
        )
        
        # Llama3 模型配置
        self.models["llama3"] = ModelConfig(
            model_name="Llama3",
            model_id="llama3.2:3b",
            host=os.getenv("LLAMA3_HOST", "llm"),
            port=int(os.getenv("LLAMA3_PORT", "8000")),
            api_endpoint="/v1/chat/completions",
            max_tokens=2048,
            temperature=0.7,
            priority=3
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
            
            # 測試模型連接
            await self._test_model_connections()
            
            self.logger.info("LLM 服務初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM 服務初始化失敗: {str(e)}")
            return False
    
    async def _test_model_connections(self):
        """測試模型連接"""
        for model_name, model_config in self.models.items():
            if not model_config.enabled:
                continue
                
            try:
                # 簡單的連接測試
                url = f"http://{model_config.host}:{model_config.port}/health"
                async with self.http_session.get(url, timeout=5) as response:
                    if response.status == 200:
                        self.logger.info(f"模型 {model_name} 連接正常")
                    else:
                        self.logger.warning(f"模型 {model_name} 連接異常: {response.status}")
                        model_config.enabled = False
                        
            except Exception as e:
                self.logger.warning(f"模型 {model_name} 連接失敗: {str(e)}")
                model_config.enabled = False
    
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
                request = GenerationRequest(**request_data)
            elif isinstance(request_data, GenerationRequest):
                request = request_data
            else:
                raise ValueError("無效的請求格式")
            
            # 生成回應
            response = await self.generate_text(request)
            
            processing_time = time.time() - start_time
            
            return self._create_response(
                success=True,
                data=response,
                message="文本生成成功",
                processing_time=processing_time,
                metadata={
                    "model_used": response.model_used,
                    "trace_id": response.trace_id  # 包含追蹤 ID
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"處理請求失敗: {str(e)}")
            
            return self._create_response(
                success=False,
                data=None,
                message=f"處理失敗: {str(e)}",
                processing_time=processing_time
            )
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """
        生成文本
        
        Args:
            request: 生成請求
            
        Returns:
            GenerationResponse: 生成回應
        """
        start_time = time.time()
        
        # 選擇模型
        model_name = request.model_name or self._select_best_model()
        model_config = self.models.get(model_name)
        
        if not model_config or not model_config.enabled:
            raise ValueError(f"模型 {model_name} 不可用")
        
        # 創建或使用現有的 Langfuse 追蹤
        trace_id = request.trace_id
        if not trace_id:
            trace = self.langfuse.trace(
                name="llm_generation",
                metadata={
                    "user_id": request.user_id,
                    "model_name": model_name,
                    "model_id": model_config.model_id
                }
            )
            trace_id = trace.id
        
        try:
            # 記錄開始生成
            self.langfuse.span(
                trace_id=trace_id,
                name="llm_generation_start",
                input={
                    "prompt": request.prompt,
                    "model": model_name,
                    "temperature": request.temperature or model_config.temperature,
                    "max_tokens": request.max_tokens or model_config.max_tokens
                }
            )
            
            # 準備請求數據
            payload = self._prepare_payload(request, model_config)
            
            # 記錄模型選擇過程
            self.langfuse.span(
                trace_id=trace_id,
                name="model_selection",
                input={
                    "selected_model": model_name,
                    "model_priority": model_config.priority,
                    "available_models": [name for name, config in self.models.items() if config.enabled]
                }
            )
            
            # 發送請求
            url = f"http://{model_config.host}:{model_config.port}{model_config.api_endpoint}"
            headers = {"Content-Type": "application/json"}
            
            async with self.http_session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析回應
                    generated_text = data["choices"][0]["message"]["content"]
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    
                    processing_time = time.time() - start_time
                    
                    # 計算信心值
                    confidence = self._calculate_confidence(generated_text, tokens_used)
                    
                    # 記錄生成結果
                    self.langfuse.span(
                        trace_id=trace_id,
                        name="llm_generation_complete",
                        input={
                            "generated_text": generated_text,
                            "tokens_used": tokens_used,
                            "processing_time": processing_time,
                            "confidence": confidence
                        }
                    )
                    
                    # 完成追蹤
                    self.langfuse.trace(
                        id=trace_id,
                        status="success"
                    )
                    
                    return GenerationResponse(
                        text=generated_text,
                        model_used=model_name,
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        confidence=confidence,
                        metadata={
                            "model_id": model_config.model_id,
                            "temperature": model_config.temperature,
                            "max_tokens": model_config.max_tokens
                        },
                        trace_id=trace_id
                    )
                else:
                    error_text = await response.text()
                    
                    # 記錄錯誤
                    self.langfuse.span(
                        trace_id=trace_id,
                        name="llm_generation_error",
                        input={
                            "error": f"API 請求失敗: {response.status} - {error_text}",
                            "model": model_name
                        }
                    )
                    
                    # 完成追蹤（錯誤狀態）
                    self.langfuse.trace(
                        id=trace_id,
                        status="error"
                    )
                    
                    raise Exception(f"API 請求失敗: {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"模型 {model_name} 生成失敗: {str(e)}")
            
            # 記錄錯誤到 Langfuse
            if trace_id:
                self.langfuse.span(
                    trace_id=trace_id,
                    name="llm_generation_exception",
                    input={
                        "error": str(e),
                        "model": model_name
                    }
                )
                self.langfuse.trace(
                    id=trace_id,
                    status="error"
                )
            
            # 嘗試其他模型
            return await self._fallback_generation(request, model_name)
    
    def _prepare_payload(self, request: GenerationRequest, model_config: ModelConfig) -> Dict[str, Any]:
        """
        準備請求載荷
        
        Args:
            request: 生成請求
            model_config: 模型配置
            
        Returns:
            Dict: 請求載荷
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
        
        return {
            "model": model_config.model_id,
            "messages": messages,
            "max_tokens": request.max_tokens or model_config.max_tokens,
            "temperature": request.temperature or model_config.temperature,
            "stream": False
        }
    
    def _select_best_model(self) -> str:
        """
        選擇最佳模型
        
        Returns:
            str: 模型名稱
        """
        # 按優先級排序啟用的模型
        enabled_models = [
            (name, config) for name, config in self.models.items()
            if config.enabled
        ]
        
        if not enabled_models:
            raise ValueError("沒有可用的模型")
        
        # 按優先級排序
        enabled_models.sort(key=lambda x: x[1].priority)
        
        return enabled_models[0][0]
    
    async def _fallback_generation(self, request: GenerationRequest, failed_model: str) -> GenerationResponse:
        """
        備援生成
        
        Args:
            request: 生成請求
            failed_model: 失敗的模型
            
        Returns:
            GenerationResponse: 生成回應
        """
        # 記錄備援開始
        if request.trace_id:
            self.langfuse.span(
                trace_id=request.trace_id,
                name="fallback_generation_start",
                input={
                    "failed_model": failed_model,
                    "available_models": [name for name, config in self.models.items() if config.enabled and name != failed_model]
                }
            )
        
        # 嘗試其他啟用的模型
        for model_name, model_config in self.models.items():
            if model_name != failed_model and model_config.enabled:
                try:
                    self.logger.info(f"嘗試備援模型: {model_name}")
                    
                    # 記錄嘗試備援模型
                    if request.trace_id:
                        self.langfuse.span(
                            trace_id=request.trace_id,
                            name="fallback_model_attempt",
                            input={
                                "attempted_model": model_name,
                                "model_priority": model_config.priority
                            }
                        )
                    
                    # 創建新的請求，指定備援模型
                    fallback_request = GenerationRequest(
                        prompt=request.prompt,
                        model_name=model_name,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        system_prompt=request.system_prompt,
                        user_id=request.user_id,
                        metadata=request.metadata,
                        trace_id=request.trace_id  # 保持相同的追蹤 ID
                    )
                    
                    return await self.generate_text(fallback_request)
                    
                except Exception as e:
                    self.logger.warning(f"備援模型 {model_name} 也失敗: {str(e)}")
                    
                    # 記錄備援模型失敗
                    if request.trace_id:
                        self.langfuse.span(
                            trace_id=request.trace_id,
                            name="fallback_model_failed",
                            input={
                                "failed_model": model_name,
                                "error": str(e)
                            }
                        )
                    continue
        
        # 記錄所有模型都失敗
        if request.trace_id:
            self.langfuse.span(
                trace_id=request.trace_id,
                name="all_models_failed",
                input={
                    "failed_models": [name for name, config in self.models.items() if config.enabled]
                }
            )
            self.langfuse.trace(
                id=request.trace_id,
                status="error"
            )
        
        # 所有模型都失敗
        raise Exception("所有模型都無法使用")
    
    def _calculate_confidence(self, text: str, tokens_used: int) -> float:
        """
        計算信心值
        
        Args:
            text: 生成的文本
            tokens_used: 使用的 token 數量
            
        Returns:
            float: 信心值 (0.0-1.0)
        """
        # 基於文本長度和 token 使用量的簡單信心值計算
        if not text:
            return 0.0
        
        # 文本長度因子
        length_factor = min(1.0, len(text) / 100)
        
        # Token 效率因子
        efficiency_factor = min(1.0, tokens_used / len(text) if len(text) > 0 else 1.0)
        
        # 綜合信心值
        confidence = (length_factor + efficiency_factor) / 2
        
        return min(0.95, max(0.1, confidence))
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        獲取可用模型列表
        
        Returns:
            List: 可用模型列表
        """
        models_info = []
        
        for model_name, model_config in self.models.items():
            models_info.append({
                "name": model_name,
                "model_id": model_config.model_id,
                "enabled": model_config.enabled,
                "priority": model_config.priority,
                "host": model_config.host,
                "port": model_config.port
            })
        
        return models_info
    
    async def cleanup(self) -> bool:
        """
        清理資源
        
        Returns:
            bool: 清理是否成功
        """
        try:
            if self.http_session:
                await self.http_session.close()
            
            self.logger.info("LLM 服務資源清理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM 服務資源清理失敗: {str(e)}")
            return False

# 便捷函數
async def create_llm_service(host: str = "0.0.0.0", port: int = 8000) -> LLMService:
    """
    創建 LLM 服務實例
    
    Args:
        host: 服務主機
        port: 服務端口
        
    Returns:
        LLMService: LLM 服務實例
    """
    config = ServiceConfig(
        service_name="LLM Service",
        service_version="1.0.0",
        host=host,
        port=port,
        debug=os.getenv("DEBUG", "False").lower() == "true",
        timeout=int(os.getenv("LLM_TIMEOUT", "30"))
    )
    
    return LLMService(config) 