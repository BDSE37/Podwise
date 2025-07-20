#!/usr/bin/env python3
"""
Hugging Face LLM 實作

直接使用本地 Hugging Face 模型，不依賴 Ollama。

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import time
import logging
import torch
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer

# 修正導入路徑
try:
    from .base_llm import BaseLLM, LLMConfig, GenerationRequest, GenerationResponse, ModelInfo
except ImportError:
    # 備用導入路徑
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from base_llm import BaseLLM, LLMConfig, GenerationRequest, GenerationResponse, ModelInfo


@dataclass
class HuggingFaceConfig:
    """Hugging Face 模型配置"""
    model_name: str
    model_id: str
    model_path: str
    host: str = "localhost"
    port: int = 11434
    api_endpoint: str = "/api"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    priority: int = 1
    enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    device: str = "auto"
    torch_dtype: str = "auto"
    trust_remote_code: bool = True
    use_cache: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class HuggingFaceLLM:
    """Hugging Face LLM 實作類別"""
    
    def __init__(self, config: HuggingFaceConfig):
        """
        初始化 Hugging Face LLM
        
        Args:
            config: Hugging Face 模型配置
        """
        self.config = config
        self.model_path = config.model_path
        self.device = config.device
        self.torch_dtype = config.torch_dtype
        self.trust_remote_code = config.trust_remote_code
        self.use_cache = config.use_cache
        self.is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 模型組件
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.pipeline: Optional[Any] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # 自動檢測設備
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 自動檢測數據類型
        if self.torch_dtype == "auto":
            self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    async def initialize(self) -> bool:
        """
        初始化 Hugging Face LLM 服務
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info(f"初始化 Hugging Face LLM: {self.config.model_name}")
            self.logger.info(f"模型路徑: {self.model_path}")
            self.logger.info(f"設備: {self.device}")
            
            # 在執行緒池中載入模型以避免阻塞
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            
            self.is_initialized = True
            self.logger.info(f"Hugging Face LLM {self.config.model_name} 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Hugging Face LLM 初始化失敗: {str(e)}")
            return False
    
    def _load_model(self):
        """載入模型（在執行緒中執行）"""
        try:
            # 載入 tokenizer
            self.logger.info("載入 tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=self.trust_remote_code,
                use_cache=self.use_cache
            )
            
            # 設定 pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 載入模型
            self.logger.info("載入模型...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=self.torch_dtype,
                device_map=self.device,
                trust_remote_code=self.trust_remote_code,
                use_cache=self.use_cache
            )
            
            # 建立 pipeline
            self.logger.info("建立 pipeline...")
            
            # 檢查是否使用 accelerate 載入
            if hasattr(self.model, 'hf_device_map') and self.model.hf_device_map:
                # 使用 accelerate 載入的模型，不指定 device
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    torch_dtype=self.torch_dtype
                )
            else:
                # 一般載入的模型，可以指定 device
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=self.device,
                    torch_dtype=self.torch_dtype
                )
            
            # 載入嵌入模型（使用較小的模型）
            self.logger.info("載入嵌入模型...")
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
            except Exception as e:
                self.logger.warning(f"無法載入 SentenceTransformer，將使用簡單嵌入: {e}")
                self.embedding_model = None
            
            self.logger.info("模型載入完成")
            
        except Exception as e:
            self.logger.error(f"模型載入失敗: {str(e)}")
            raise
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """
        生成文本
        
        Args:
            request: 生成請求
            
        Returns:
            GenerationResponse: 生成回應
        """
        if not self.is_initialized:
            raise RuntimeError("Hugging Face LLM 尚未初始化")
        
        start_time = time.time()
        
        try:
            # 準備輸入文本
            input_text = self._prepare_input_text(request)
            
            # 在執行緒池中執行生成
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._generate_text_sync, 
                input_text, 
                request
            )
            
            processing_time = time.time() - start_time
            
            return GenerationResponse(
                text=result["text"],
                model_used=self.config.model_name,
                tokens_used=result.get("tokens_used", 0),
                processing_time=processing_time,
                confidence=self._calculate_confidence(result["text"]),
                finish_reason=result.get("finish_reason", "stop"),
                metadata={
                    "model_path": self.model_path,
                    "device": self.device,
                    "provider": "huggingface"
                }
            )
                
        except Exception as e:
            self.logger.error(f"Hugging Face 文本生成失敗: {str(e)}")
            raise
    
    def _prepare_input_text(self, request: GenerationRequest) -> str:
        """
        準備輸入文本
        
        Args:
            request: 生成請求
            
        Returns:
            str: 格式化的輸入文本
        """
        # 使用 Qwen 格式的模板
        if request.system_prompt:
            input_text = f"<|im_start|>system\n{request.system_prompt}<|im_end|>\n"
        else:
            input_text = ""
        
        input_text += f"<|im_start|>user\n{request.prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        return input_text
    
    def _generate_text_sync(self, input_text: str, request: GenerationRequest) -> Dict[str, Any]:
        """
        同步生成文本
        
        Args:
            input_text: 輸入文本
            request: 生成請求
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            # 生成參數
            generation_kwargs = {
                "max_new_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "top_k": request.top_k,
                "repetition_penalty": request.repetition_penalty,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            # 移除 None 值
            generation_kwargs = {k: v for k, v in generation_kwargs.items() if v is not None}
            
            # 執行生成
            outputs = self.pipeline(
                input_text,
                **generation_kwargs,
                return_full_text=False
            )
            
            # 提取生成的文本
            generated_text = outputs[0]["generated_text"]
            
            # 移除輸入文本部分
            if input_text in generated_text:
                generated_text = generated_text[len(input_text):]
            
            # 清理停止標記
            stop_tokens = ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]
            for stop_token in stop_tokens:
                if stop_token in generated_text:
                    generated_text = generated_text.split(stop_token)[0]
            
            return {
                "text": generated_text.strip(),
                "tokens_used": len(outputs[0].get("generated_tokens", [])),
                "finish_reason": "stop"
            }
            
        except Exception as e:
            self.logger.error(f"同步生成失敗: {str(e)}")
            raise
    
    def _calculate_confidence(self, text: str) -> float:
        """
        計算回應信心度
        
        Args:
            text: 生成文本
            
        Returns:
            float: 信心度分數 (0-1)
        """
        if not text:
            return 0.0
        
        # 簡單的信心度計算邏輯
        length_score = min(len(text) / 100, 1.0)
        content_score = 0.8
        
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
            raise RuntimeError("Hugging Face LLM 尚未初始化")
        
        try:
            if self.embedding_model is not None:
                # 使用 SentenceTransformer
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    None, 
                    self.embedding_model.encode, 
                    texts
                )
                return embeddings.tolist()
            else:
                # 使用簡單的詞頻嵌入作為備用
                return self._simple_embeddings(texts)
                
        except Exception as e:
            self.logger.error(f"Hugging Face 嵌入獲取失敗: {str(e)}")
            return self._simple_embeddings(texts)
    
    def _simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        簡單的詞頻嵌入（備用方法）
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        # 簡單的詞頻向量化
        from collections import Counter
        import re
        
        # 建立詞彙表
        all_words = set()
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            all_words.update(words)
        
        word_to_idx = {word: idx for idx, word in enumerate(sorted(all_words))}
        vocab_size = len(word_to_idx)
        
        embeddings = []
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            word_counts = Counter(words)
            
            # 建立向量
            vector = [0.0] * vocab_size
            for word, count in word_counts.items():
                if word in word_to_idx:
                    vector[word_to_idx[word]] = count
            
            # 正規化
            norm = sum(x * x for x in vector) ** 0.5
            if norm > 0:
                vector = [x / norm for x in vector]
            
            embeddings.append(vector)
        
        return embeddings
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 服務是否健康
        """
        try:
            if not self.is_initialized:
                return False
            
            # 簡單的測試生成
            test_request = GenerationRequest(
                prompt="Hello",
                max_tokens=10,
                temperature=0.1
            )
            
            await self.generate_text(test_request)
            return True
            
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {str(e)}")
            return False
    
    async def get_model_info(self) -> ModelInfo:
        """
        獲取模型資訊
        
        Returns:
            ModelInfo: 模型資訊
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("模型尚未初始化")
            
            # 獲取模型配置
            config = self.model.config if self.model else None
            
            return ModelInfo(
                model_name=self.config.model_name,
                model_id=self.config.model_id,
                model_type="causal_lm",
                provider="huggingface",
                context_length=config.max_position_embeddings if config else 4096,
                embedding_dimension=config.hidden_size if config else 4096,
                parameters=config.num_parameters if hasattr(config, 'num_parameters') else None,
                device=self.device,
                dtype=str(self.torch_dtype),
                metadata={
                    "model_path": self.model_path,
                    "trust_remote_code": self.trust_remote_code,
                    "use_cache": self.use_cache
                }
            )
            
        except Exception as e:
            self.logger.error(f"獲取模型資訊失敗: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """
        清理資源
        """
        try:
            if self.model:
                del self.model
                self.model = None
            
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            
            if self.pipeline:
                del self.pipeline
                self.pipeline = None
            
            if self.embedding_model:
                del self.embedding_model
                self.embedding_model = None
            
            # 清理 CUDA 快取
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.is_initialized = False
            self.logger.info("Hugging Face LLM 資源已清理")
            
        except Exception as e:
            self.logger.error(f"清理資源失敗: {str(e)}") 