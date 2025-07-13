"""
LLM 服務主程式
整合 Qwen3、bge-m3 和 Deepseek R1 模型
支援 qwen2.5-Taiwan 和 qwen3:8b 模型
採用 OOP 架構設計
"""

import os
import logging
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
import torch
from dotenv import load_dotenv
import httpx
from langfuse import Langfuse

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI
app = FastAPI(title="LLM Service")

# 初始化 Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

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
    trace_id: Optional[str] = None

@dataclass
class GenerationResponse:
    """生成回應資料結構"""
    text: str
    model_used: str
    tokens_used: int
    processing_time: float
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

class LLMService:
    """LLM 服務類別 - OOP 架構"""
    
    def __init__(self):
        """初始化 LLM 服務"""
        self.models: Dict[str, ModelConfig] = {}
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # 載入模型配置
        self._load_model_configs()
        
        logger.info(f"LLM 服務初始化完成，可用模型: {list(self.models.keys())}")
        logger.info("Langfuse 追蹤功能已啟用")
    
    def _load_model_configs(self):
        """載入模型配置"""
        # Qwen2.5-Taiwan 模型配置
        self.models["qwen2.5-Taiwan"] = ModelConfig(
            model_name="Qwen2.5-Taiwan",
            model_id="qwen2.5:7b",
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            api_endpoint="/api/generate",
            max_tokens=2048,
            temperature=0.7,
            priority=1
        )
        
        # Qwen3:8b 模型配置
        self.models["qwen3:8b"] = ModelConfig(
            model_name="Qwen3:8b",
            model_id="qwen3:8b",
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            api_endpoint="/api/generate",
            max_tokens=2048,
            temperature=0.7,
            priority=2
        )
        
        # 通用 Qwen 模型配置（向後相容）
        self.models["qwen"] = ModelConfig(
            model_name="Qwen",
            model_id="qwen3:8b",
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            api_endpoint="/api/generate",
            max_tokens=2048,
            temperature=0.7,
            priority=3
        )
        
        # DeepSeek 模型配置
        self.models["deepseek"] = ModelConfig(
            model_name="DeepSeek",
            model_id="deepseek-coder:6.7b",
            host=os.getenv("OLLAMA_HOST", "localhost"),
            port=int(os.getenv("OLLAMA_PORT", "11434")),
            api_endpoint="/api/generate",
            max_tokens=2048,
            temperature=0.7,
            priority=4
        )
    
    async def initialize(self) -> bool:
        """初始化服務"""
        try:
            # 創建 HTTP 會話
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
            
            # 測試模型連接
            await self._test_model_connections()
            
            logger.info("LLM 服務初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"LLM 服務初始化失敗: {str(e)}")
            return False
    
    async def _test_model_connections(self):
        """測試模型連接"""
        for model_name, model_config in self.models.items():
            if not model_config.enabled:
                continue
                
            try:
                # 簡單的連接測試
                url = f"http://{model_config.host}:{model_config.port}/api/tags"
                async with self.http_session.get(url, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"模型 {model_name} 連接正常")
                    else:
                        logger.warning(f"模型 {model_name} 連接異常: {response.status}")
                        model_config.enabled = False
                        
            except Exception as e:
                logger.warning(f"模型 {model_name} 連接失敗: {str(e)}")
                model_config.enabled = False
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """生成文字"""
        start_time = time.time()
        
        try:
            # 選擇模型
            model_name = request.model_name or self._select_best_model()
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 不可用")
            
            model_config = self.models[model_name]
            
            # 準備請求數據
            payload = self._prepare_payload(request, model_config)
            
            # 發送請求
            url = f"http://{model_config.host}:{model_config.port}{model_config.api_endpoint}"
            async with self.http_session.post(url, json=payload, timeout=60) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="模型 API 錯誤")
                
                result = await response.json()
                
                # 解析回應
                generated_text = result.get("response", "")
                tokens_used = len(generated_text.split())  # 簡化計算
                
                processing_time = time.time() - start_time
                confidence = self._calculate_confidence(generated_text, tokens_used)
                
                return GenerationResponse(
                    text=generated_text,
                    model_used=model_name,
                    tokens_used=tokens_used,
                    processing_time=processing_time,
                    confidence=confidence,
                    metadata=request.metadata,
                    trace_id=request.trace_id
                )
                
        except Exception as e:
            logger.error(f"生成文字失敗: {str(e)}")
            # 嘗試 fallback
            return await self._fallback_generation(request, model_name)
    
    def _prepare_payload(self, request: GenerationRequest, model_config: ModelConfig) -> Dict[str, Any]:
        """準備請求數據"""
        return {
            "model": model_config.model_id,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens or model_config.max_tokens,
                "temperature": request.temperature or model_config.temperature
            }
        }
    
    def _select_best_model(self) -> str:
        """選擇最佳模型"""
        available_models = [
            (name, config) for name, config in self.models.items() 
            if config.enabled
        ]
        
        if not available_models:
            raise ValueError("沒有可用的模型")
        
        # 按優先級排序
        available_models.sort(key=lambda x: x[1].priority)
        return available_models[0][0]
    
    async def _fallback_generation(self, request: GenerationRequest, failed_model: str) -> GenerationResponse:
        """Fallback 生成"""
        logger.warning(f"模型 {failed_model} 失敗，嘗試 fallback")
        
        # 禁用失敗的模型
        if failed_model in self.models:
            self.models[failed_model].enabled = False
        
        # 嘗試其他模型
        for model_name, model_config in self.models.items():
            if model_name != failed_model and model_config.enabled:
                try:
                    request.model_name = model_name
                    return await self.generate_text(request)
                except Exception as e:
                    logger.warning(f"Fallback 模型 {model_name} 也失敗: {str(e)}")
                    continue
        
        # 所有模型都失敗，返回預設回應
        return GenerationResponse(
            text="抱歉，目前無法生成回應，請稍後再試。",
            model_used="fallback",
            tokens_used=0,
            processing_time=0,
            confidence=0.0,
            metadata=request.metadata,
            trace_id=request.trace_id
        )
    
    def _calculate_confidence(self, text: str, tokens_used: int) -> float:
        """計算信心度"""
        if not text:
            return 0.0
        
        # 基於文本長度和內容的簡單信心度計算
        base_confidence = min(len(text) / 100, 1.0)  # 文本越長信心度越高
        token_confidence = min(tokens_used / 50, 1.0)  # token 數量適中時信心度較高
        
        return (base_confidence + token_confidence) / 2
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """獲取可用模型列表"""
        return [
            {
                "name": name,
                "model_id": config.model_id,
                "enabled": config.enabled,
                "priority": config.priority
            }
            for name, config in self.models.items()
        ]
    
    async def cleanup(self) -> bool:
        """清理資源"""
        try:
            if self.http_session:
                await self.http_session.close()
            return True
        except Exception as e:
            logger.error(f"清理資源失敗: {str(e)}")
            return False

# 創建 LLM 服務實例
llm_service = LLMService()

# Pydantic 模型
class LLMRequest(BaseModel):
    """LLM 請求模型"""
    prompt: str
    model: str = "qwen2.5-Taiwan"  # 預設使用 Qwen2.5-Taiwan
    max_tokens: int = 2048
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingRequest(BaseModel):
    """向量嵌入請求模型"""
    text: str
    model: str = "bge-m3"  # 預設使用 bge-m3

# 載入向量模型
def load_embedding_models():
    """載入向量嵌入模型"""
    models = {}
    
    # 檢查模型路徑是否存在
    bge_path = os.getenv("BGE_MODEL_PATH", "/app/models/external/bge-m3")
    
    # 載入 BGE-M3 模型（如果存在）
    if os.path.exists(bge_path) and os.path.exists(os.path.join(bge_path, "config.json")):
        try:
            models["bge-m3"] = {
                "tokenizer": AutoTokenizer.from_pretrained(bge_path),
                "model": AutoModel.from_pretrained(bge_path)
            }
            logging.info(f"BGE-M3 模型載入成功: {bge_path}")
        except Exception as e:
            logging.error(f"BGE-M3 模型載入失敗: {e}")
    else:
        logging.warning(f"BGE-M3 模型路徑不存在或無效: {bge_path}")
    
    return models

# 初始化模型
embedding_models = load_embedding_models()

@app.on_event("startup")
async def startup_event():
    """啟動事件"""
    await llm_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """關閉事件"""
    await llm_service.cleanup()

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    available_models = await llm_service.get_available_models()
    return {
        "status": "healthy", 
        "models": available_models,
        "embedding_models": list(embedding_models.keys())
    }

@app.post("/generate")
async def generate_text(request: LLMRequest):
    """生成文字端點"""
    try:
        with langfuse.trace(name="generate_text") as trace:
            # 創建生成請求
            gen_request = GenerationRequest(
                prompt=request.prompt,
                model_name=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system_prompt=request.system_prompt,
                user_id=request.user_id,
                metadata=request.metadata,
                trace_id=trace.id
            )
            
            # 生成文字
            response = await llm_service.generate_text(gen_request)
            
            # 記錄追蹤
            trace.span(
                name="llm_generation",
                input={"prompt": request.prompt, "model": request.model},
                output={"response": response.text, "confidence": response.confidence}
            )

            return {
                "text": response.text,
                "model_used": response.model_used,
                "tokens_used": response.tokens_used,
                "processing_time": response.processing_time,
                "confidence": response.confidence,
                "trace_id": response.trace_id
            }

    except Exception as e:
        logger.error(f"生成文字失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
async def get_embedding(request: EmbeddingRequest):
    """獲取向量嵌入端點"""
    try:
        with langfuse.trace(name="get_embedding") as trace:
            # 檢查模型是否可用
            if request.model not in embedding_models:
                raise HTTPException(status_code=400, detail=f"模型 {request.model} 不可用")

            model = embedding_models[request.model]
            inputs = model["tokenizer"](
                request.text,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            with torch.no_grad():
                outputs = model["model"](**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)

            trace.span(
                name="embedding_generation",
                input={"text": request.text},
                output={"embedding_shape": embeddings.shape}
            )

            return {"embedding": embeddings.tolist()}

    except Exception as e:
        logger.error(f"生成向量嵌入失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    """獲取可用模型列表"""
    try:
        available_models = await llm_service.get_available_models()
        return {
            "llm_models": available_models,
            "embedding_models": list(embedding_models.keys())
        }
    except Exception as e:
        logger.error(f"獲取模型列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 