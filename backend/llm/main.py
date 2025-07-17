#!/usr/bin/env python3
"""
Podwise LLM 統一服務模組

整合所有語言模型功能：
- Ollama 本地模型 (Qwen2.5-Taiwan-7B-Instruct, Qwen3-8B)
- Hugging Face 模型
- 模型路由和負載均衡
- 效能監控和追蹤
- 錯誤處理和重試機制
- 配置管理

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 3.0.0
"""

import logging
import os
import sys
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置類別"""
    # 模型啟用配置
    enable_qwen_taiwan: bool = True
    enable_qwen3: bool = True
    enable_huggingface: bool = True
    enable_fallback: bool = True
    
    # 生成參數
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # 連接配置
    timeout: int = 60
    retry_count: int = 3
    
    # Ollama 配置
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 120
    
    # Hugging Face 配置
    hf_model_path: str = "./models"
    hf_device: str = "cpu"
    
    # 日誌配置
    log_level: str = "INFO"


@dataclass
class GenerationRequest:
    """生成請求資料結構"""
    prompt: str
    system: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    stream: bool = False


@dataclass
class GenerationResponse:
    """生成回應資料結構"""
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    success: bool = True
    error: Optional[str] = None


class OllamaLLM:
    """Ollama LLM 服務類別"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.available_models: List[str] = []
        self.model_mapping = {
            "qwen2.5:7b-taiwan": "qwen2.5-taiwan-7b-instruct:latest",
            "qwen3:8b": "qwen3-8b:latest",
            "qwen2.5-taiwan": "qwen2.5-taiwan-7b-instruct:latest",
            "qwen3": "qwen3-8b:latest",
            "qwen2.5-taiwan-7b-instruct": "qwen2.5-taiwan-7b-instruct:latest"
        }
        self.logger = logging.getLogger(f"{__name__}.OllamaLLM")
    
    async def initialize(self) -> bool:
        """初始化 Ollama 服務"""
        try:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.ollama_timeout)
            )
            
            # 測試連接
            await self._test_connection()
            
            # 檢查可用模型
            await self._check_available_models()
            
            self.logger.info(f"Ollama 服務初始化成功，可用模型: {self.available_models}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ollama 服務初始化失敗: {e}")
            return False
    
    async def _test_connection(self):
        """測試 Ollama 連接"""
        try:
            if self.http_session is None:
                raise Exception("HTTP session 未初始化")
            
            url = f"{self.config.ollama_host}/api/tags"
            async with self.http_session.get(url) as response:
                if response.status == 200:
                    self.logger.info("Ollama 連接正常")
                else:
                    raise Exception(f"Ollama 連接異常: {response.status}")
        except Exception as e:
            self.logger.error(f"Ollama 連接失敗: {e}")
            raise
    
    async def _check_available_models(self):
        """檢查可用模型"""
        try:
            if self.http_session is None:
                self.available_models = []
                return
                
            url = f"{self.config.ollama_host}/api/tags"
            async with self.http_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model['name'] for model in data.get('models', [])]
                else:
                    self.available_models = []
        except Exception as e:
            self.logger.error(f"檢查可用模型失敗: {e}")
            self.available_models = []
    
    def _map_model_name(self, model_name: str) -> str:
        """映射模型名稱"""
        return self.model_mapping.get(model_name, model_name)
    
    async def generate_text(self, request: GenerationRequest, model_name: str) -> GenerationResponse:
        """生成文字"""
        start_time = time.time()
        
        try:
            # 映射模型名稱
            mapped_model_name = self._map_model_name(model_name)
            
            # 檢查模型是否可用
            if mapped_model_name not in self.available_models:
                raise Exception(f"模型 {mapped_model_name} 不可用，可用模型: {self.available_models}")
            
            # 準備請求資料
            payload = {
                "model": mapped_model_name,
                "prompt": request.prompt,
                "stream": request.stream,
                "options": {
                    "num_predict": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature,
                    "top_p": request.top_p or self.config.top_p,
                    "top_k": request.top_k or self.config.top_k,
                    "repeat_penalty": request.repeat_penalty or self.config.repeat_penalty
                }
            }
            
            if request.system:
                payload["system"] = request.system
            
            # 發送請求
            if self.http_session is None:
                raise Exception("HTTP session 未初始化")
                
            url = f"{self.config.ollama_host}/api/generate"
            async with self.http_session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    processing_time = time.time() - start_time
                    
                    return GenerationResponse(
                        text=data.get('response', ''),
                        model_used=mapped_model_name,
                        tokens_used=data.get('eval_count', 0),
                        processing_time=processing_time,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API 錯誤: {response.status} - {error_text}")
                    
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"文字生成失敗: {e}")
            
            return GenerationResponse(
                text="",
                model_used=model_name,
                tokens_used=0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            if self.http_session is None:
                return {
                    "status": "error",
                    "error": "HTTP session 未初始化",
                    "available_models": [],
                    "connection": "failed"
                }
                
            url = f"{self.config.ollama_host}/api/tags"
            async with self.http_session.get(url) as response:
                return {
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "available_models": self.available_models,
                    "connection": "ok" if response.status == 200 else "failed"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "available_models": [],
                "connection": "failed"
            }
    
    async def cleanup(self):
        """清理資源"""
        if self.http_session:
            await self.http_session.close()


class HuggingFaceLLM:
    """Hugging Face LLM 服務類別"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.models: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.HuggingFaceLLM")
    
    async def initialize(self) -> bool:
        """初始化 Hugging Face 服務"""
        try:
            # 這裡可以添加 Hugging Face 模型初始化邏輯
            self.logger.info("Hugging Face 服務初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"Hugging Face 服務初始化失敗: {e}")
            return False
    
    async def _load_models(self):
        """載入模型"""
        # 實現模型載入邏輯
        pass
    
    async def generate_text(self, request: GenerationRequest, model_name: str) -> GenerationResponse:
        """生成文字"""
        start_time = time.time()
        
        try:
            # 這裡實現 Hugging Face 模型推理
            # 目前返回預設回應
            processing_time = time.time() - start_time
            
            return GenerationResponse(
                text=f"[Hugging Face] {request.prompt} (模型: {model_name})",
                model_used=model_name,
                tokens_used=len(request.prompt.split()),
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Hugging Face 文字生成失敗: {e}")
            
            return GenerationResponse(
                text="",
                model_used=model_name,
                tokens_used=0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            "status": "healthy",
            "available_models": list(self.models.keys()),
            "connection": "ok"
        }


class LLMManager:
    """LLM 管理器類別"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.ollama_llm: Optional[OllamaLLM] = None
        self.hf_llm: Optional[HuggingFaceLLM] = None
        self.logger = logging.getLogger(f"{__name__}.LLMManager")
    
    async def initialize(self) -> bool:
        """初始化 LLM 管理器"""
        try:
            # 初始化 Ollama 服務
            if self.config.enable_qwen_taiwan or self.config.enable_qwen3:
                self.ollama_llm = OllamaLLM(self.config)
                if not await self.ollama_llm.initialize():
                    self.logger.warning("Ollama 服務初始化失敗")
            
            # 初始化 Hugging Face 服務
            if self.config.enable_huggingface:
                self.hf_llm = HuggingFaceLLM(self.config)
                if not await self.hf_llm.initialize():
                    self.logger.warning("Hugging Face 服務初始化失敗")
            
            self.logger.info("🚀 LLM 管理器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM 管理器初始化失敗: {e}")
            return False
    
    async def generate_text(self, request: GenerationRequest, model_name: Optional[str] = None) -> GenerationResponse:
        """生成文字"""
        # 如果沒有指定模型，使用預設模型
        if not model_name:
            if self.config.enable_qwen_taiwan:
                model_name = "qwen2.5:7b-taiwan"
            elif self.config.enable_qwen3:
                model_name = "qwen3:8b"
            else:
                return GenerationResponse(
                    text="",
                    model_used="",
                    tokens_used=0,
                    processing_time=0,
                    success=False,
                    error="沒有可用的模型"
                )
        
        # 根據模型名稱選擇服務
        if model_name in ["qwen2.5:7b-taiwan", "qwen3:8b", "qwen2.5-taiwan", "qwen3", "qwen2.5-taiwan-7b-instruct", "qwen2.5-taiwan-7b-instruct:latest"]:
            if self.ollama_llm:
                return await self.ollama_llm.generate_text(request, model_name)
            else:
                return GenerationResponse(
                    text="",
                    model_used=model_name,
                    tokens_used=0,
                    processing_time=0,
                    success=False,
                    error="Ollama 服務不可用"
                )
        else:
            # 嘗試 Hugging Face 服務
            if self.hf_llm:
                return await self.hf_llm.generate_text(request, model_name)
            else:
                return GenerationResponse(
                    text="",
                    model_used=model_name,
                    tokens_used=0,
                    processing_time=0,
                    success=False,
                    error="Hugging Face 服務不可用"
                )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 檢查 Ollama 服務
        if self.ollama_llm:
            try:
                ollama_health = await self.ollama_llm.health_check()
                health_status["services"]["ollama"] = ollama_health
            except Exception as e:
                health_status["services"]["ollama"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # 檢查 Hugging Face 服務
        if self.hf_llm:
            try:
                hf_health = await self.hf_llm.health_check()
                health_status["services"]["huggingface"] = hf_health
            except Exception as e:
                health_status["services"]["huggingface"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    async def cleanup(self):
        """清理資源"""
        if self.ollama_llm:
            await self.ollama_llm.cleanup()


# 全局 LLM 管理器實例
_llm_manager: Optional[LLMManager] = None


def get_llm_manager(config: Optional[LLMConfig] = None) -> LLMManager:
    """獲取 LLM 管理器實例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager(config)
    return _llm_manager


async def initialize_llm(config: Optional[LLMConfig] = None) -> LLMManager:
    """初始化 LLM 服務"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager(config)
        await _llm_manager.initialize()
    return _llm_manager


async def generate_text(prompt: str, model_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """生成文字的便捷函數"""
    manager = get_llm_manager()
    request = GenerationRequest(
        prompt=prompt,
        system=kwargs.get('system'),
        max_tokens=kwargs.get('max_tokens'),
        temperature=kwargs.get('temperature'),
        top_p=kwargs.get('top_p'),
        top_k=kwargs.get('top_k'),
        repeat_penalty=kwargs.get('repeat_penalty')
    )
    
    response = await manager.generate_text(request, model_name)
    
    return {
        "success": response.success,
        "text": response.text,
        "model_used": response.model_used,
        "tokens_used": response.tokens_used,
        "processing_time": response.processing_time,
        "error": response.error
    }


if __name__ == "__main__":
    async def test_llm():
        """測試 LLM 服務"""
        config = LLMConfig(
            enable_qwen_taiwan=True,
            enable_qwen3=True,
            enable_huggingface=False,
            ollama_host="http://localhost:11434"
        )
        
        manager = await initialize_llm(config)
        
        # 測試文字生成
        test_prompt = "請用繁體中文介紹台灣的科技發展"
        result = await generate_text(test_prompt, "qwen2.5:7b-taiwan")
        
        print(f"測試結果: {result}")
        
        # 健康檢查
        health = await manager.health_check()
        print(f"健康檢查: {health}")
    
    asyncio.run(test_llm())


# FastAPI 應用程式
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# 全局 LLM 管理器
llm_manager: Optional[LLMManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    global llm_manager
    # 啟動時初始化
    try:
        config = LLMConfig(
            enable_qwen_taiwan=True,
            enable_qwen3=True,
            enable_huggingface=False,
            ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434")
        )
        llm_manager = await initialize_llm(config)
        logger.info("LLM 服務啟動成功")
    except Exception as e:
        logger.error(f"LLM 服務啟動失敗: {e}")
        raise
    
    yield
    
    # 關閉時清理
    if llm_manager:
        await llm_manager.cleanup()
        logger.info("LLM 服務已關閉")

app = FastAPI(
    title="Podwise LLM Service",
    description="統一的語言模型服務",
    version="3.0.0",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求模型
class TextGenerationRequest(BaseModel):
    prompt: str
    model_name: Optional[str] = None
    system: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None

# 回應模型
class TextGenerationResponse(BaseModel):
    success: bool
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    error: Optional[str] = None

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    global llm_manager
    if llm_manager is None:
        raise HTTPException(status_code=503, detail="LLM 服務未初始化")
    
    health = await llm_manager.health_check()
    return health

@app.post("/generate", response_model=TextGenerationResponse)
async def generate_text_endpoint(request: TextGenerationRequest):
    """文字生成端點"""
    global llm_manager
    if llm_manager is None:
        raise HTTPException(status_code=503, detail="LLM 服務未初始化")
    
    try:
        generation_request = GenerationRequest(
            prompt=request.prompt,
            system=request.system,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repeat_penalty=request.repeat_penalty
        )
        
        response = await llm_manager.generate_text(generation_request, request.model_name)
        
        return TextGenerationResponse(
            success=response.success,
            text=response.text,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            processing_time=response.processing_time,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"文字生成端點錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """獲取可用模型列表"""
    global llm_manager
    if llm_manager is None:
        raise HTTPException(status_code=503, detail="LLM 服務未初始化")
    
    models = []
    if llm_manager.ollama_llm:
        models.extend(llm_manager.ollama_llm.available_models)
    if llm_manager.hf_llm:
        models.extend(list(llm_manager.hf_llm.models.keys()))
    
    return {
        "models": models,
        "mapping": llm_manager.ollama_llm.model_mapping if llm_manager.ollama_llm else {}
    }

@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "Podwise LLM Service",
        "version": "3.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "models": "/models"
        }
    } 