#!/usr/bin/env python3
"""
統一 LLM 工具模組

此模組提供統一的 LLM 工具介面，整合多種 LLM 模型，
支援 CrewAI 和 LangChain 生態系統，提供一致的文本生成功能。

主要功能：
- 多模型支援 (Qwen3, DeepSeek, 等)
- LangChain 工具整合
- CrewAI 代理人支援
- 異步處理
- 模型健康檢查
- 自動回退機制

作者: Podwise Team
版本: 2.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import time

from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# 導入配置
from config.integrated_config import get_config

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelConfig:
    """
    模型配置數據類別
    
    此類別封裝了 LLM 模型的基本配置資訊，包括模型名稱、
    路徑、參數設定等。
    
    Attributes:
        name: 模型名稱
        path: 模型路徑或標識符
        model_type: 模型類型
        max_length: 最大生成長度
        temperature: 溫度參數
        device: 設備配置
        trust_remote_code: 是否信任遠程代碼
    """
    name: str
    path: str
    model_type: str
    max_length: int = 2048
    temperature: float = 0.7
    device: str = "auto"
    trust_remote_code: bool = True


@dataclass
class GenerationResult:
    """
    生成結果數據類別
    
    此類別封裝了文本生成的結果資訊，包括生成的文本、
    處理時間、模型資訊等。
    
    Attributes:
        text: 生成的文本
        model_type: 使用的模型類型
        processing_time: 處理時間
        tokens_generated: 生成的 token 數量
        metadata: 額外元數據
    """
    text: str
    model_type: str
    processing_time: float
    tokens_generated: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMInput(BaseModel):
    """
    LLM 輸入模型
    
    此模型定義了 LLM 工具的輸入參數結構，支援
    LangChain 的標準化輸入格式。
    
    Attributes:
        prompt: 輸入提示文本
        context: 上下文文本列表
        max_length: 最大生成長度
        temperature: 溫度參數
        model_type: 模型類型
        system_prompt: 系統提示
    """
    prompt: str = Field(description="輸入提示文本")
    context: Optional[List[str]] = Field(default=None, description="上下文文本列表")
    max_length: int = Field(default=2048, description="最大生成長度")
    temperature: float = Field(default=0.7, description="溫度參數")
    model_type: str = Field(default="qwen3", description="模型類型: qwen3, deepseek")
    system_prompt: Optional[str] = Field(default=None, description="系統提示")


class BaseLLMProvider(ABC):
    """
    LLM 提供者基礎抽象類別
    
    此類別定義了所有 LLM 提供者的基本介面，確保
    不同模型提供者的一致性。
    """
    
    def __init__(self, config: ModelConfig) -> None:
        """
        初始化基礎 LLM 提供者
        
        Args:
            config: 模型配置
        """
        self.config = config
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.is_loaded = False
    
    @abstractmethod
    async def load_model(self) -> bool:
        """
        載入模型
        
        Returns:
            bool: 載入是否成功
        """
        raise NotImplementedError("子類別必須實作 load_model 方法")
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> GenerationResult:
        """
        生成文本
        
        Args:
            prompt: 輸入提示
            **kwargs: 額外參數
            
        Returns:
            GenerationResult: 生成結果
        """
        raise NotImplementedError("子類別必須實作 generate_text 方法")
    
    @abstractmethod
    def format_prompt(self, prompt: str, context: Optional[List[str]] = None) -> str:
        """
        格式化提示文本
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            
        Returns:
            str: 格式化後的提示文本
        """
        raise NotImplementedError("子類別必須實作 format_prompt 方法")
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 模型是否健康
        """
        try:
            if not self.is_loaded:
                await self.load_model()
            
            test_prompt = "你好"
            result = await self.generate_text(test_prompt)
            return len(result.text) > 0 and "錯誤" not in result.text
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {str(e)}")
            return False


class Qwen3Provider(BaseLLMProvider):
    """
    Qwen3 模型提供者
    
    此類別實作了 Qwen3 模型的載入和文本生成功能，
    支援多種 Qwen3 變體。
    """
    
    async def load_model(self) -> bool:
        """
        載入 Qwen3 模型
        
        Returns:
            bool: 載入是否成功
        """
        try:
            logger.info(f"載入 Qwen3 模型: {self.config.path}")
            
            # 載入分詞器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.path,
                trust_remote_code=self.config.trust_remote_code
            )
            
            # 載入模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.path,
                trust_remote_code=self.config.trust_remote_code,
                device_map=self.config.device
            )
            
            self.is_loaded = True
            logger.info(f"✅ Qwen3 模型載入成功: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Qwen3 模型載入失敗: {str(e)}")
            return False
    
    async def generate_text(self, prompt: str, **kwargs) -> GenerationResult:
        """
        使用 Qwen3 生成文本
        
        Args:
            prompt: 輸入提示
            **kwargs: 額外參數
            
        Returns:
            GenerationResult: 生成結果
        """
        start_time = time.time()
        
        try:
            if not self.is_loaded:
                await self.load_model()
            
            # 檢查模型和分詞器是否已載入
            if self.model is None or self.tokenizer is None:
                return GenerationResult(
                    text="模型未正確載入",
                    model_type=self.config.model_type,
                    processing_time=time.time() - start_time
                )
            
            # 格式化提示
            formatted_prompt = self.format_prompt(prompt, kwargs.get('context'))
            
            # 準備輸入
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            # 生成文本
            outputs = self.model.generate(
                **inputs,
                max_length=kwargs.get('max_length', self.config.max_length),
                temperature=kwargs.get('temperature', self.config.temperature),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )
            
            # 解碼輸出
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取回答部分
            answer = self._extract_answer(generated_text, formatted_prompt)
            
            processing_time = time.time() - start_time
            tokens_generated = len(outputs[0]) - len(inputs['input_ids'][0])
            
            return GenerationResult(
                text=answer,
                model_type=self.config.model_type,
                processing_time=processing_time,
                tokens_generated=tokens_generated,
                metadata={"model_name": self.config.name}
            )
            
        except Exception as e:
            logger.error(f"❌ Qwen3 生成失敗: {str(e)}")
            return GenerationResult(
                text=f"生成失敗: {str(e)}",
                model_type=self.config.model_type,
                processing_time=time.time() - start_time
            )
    
    def format_prompt(self, prompt: str, context: Optional[List[str]] = None) -> str:
        """
        格式化 Qwen3 提示文本
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            
        Returns:
            str: 格式化後的提示文本
        """
        if context:
            formatted_prompt = "請根據以下上下文回答問題：\n\n"
            for i, ctx in enumerate(context, 1):
                formatted_prompt += f"上下文 {i}:\n{ctx}\n\n"
            formatted_prompt += f"問題：{prompt}\n\n回答："
        else:
            formatted_prompt = prompt
            
        return formatted_prompt
    
    def _extract_answer(self, generated_text: str, original_prompt: str) -> str:
        """
        從生成的文本中提取回答部分
        
        Args:
            generated_text: 生成的完整文本
            original_prompt: 原始提示
            
        Returns:
            str: 提取的回答
        """
        if "回答：" in generated_text:
            return generated_text.split("回答：")[-1].strip()
        elif len(generated_text) > len(original_prompt):
            return generated_text[len(original_prompt):].strip()
        else:
            return generated_text


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek 模型提供者
    
    此類別實作了 DeepSeek 模型的載入和文本生成功能。
    """
    
    async def load_model(self) -> bool:
        """
        載入 DeepSeek 模型
        
        Returns:
            bool: 載入是否成功
        """
        try:
            logger.info(f"載入 DeepSeek 模型: {self.config.path}")
            
            # 載入分詞器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.path,
                trust_remote_code=self.config.trust_remote_code
            )
            
            # 載入模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.path,
                trust_remote_code=self.config.trust_remote_code,
                device_map=self.config.device
            )
            
            self.is_loaded = True
            logger.info(f"✅ DeepSeek 模型載入成功: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DeepSeek 模型載入失敗: {str(e)}")
            return False
    
    async def generate_text(self, prompt: str, **kwargs) -> GenerationResult:
        """
        使用 DeepSeek 生成文本
        
        Args:
            prompt: 輸入提示
            **kwargs: 額外參數
            
        Returns:
            GenerationResult: 生成結果
        """
        start_time = time.time()
        
        try:
            if not self.is_loaded:
                await self.load_model()
            
            # 檢查模型和分詞器是否已載入
            if self.model is None or self.tokenizer is None:
                return GenerationResult(
                    text="模型未正確載入",
                    model_type=self.config.model_type,
                    processing_time=time.time() - start_time
                )
            
            # 格式化提示
            formatted_prompt = self.format_prompt(prompt, kwargs.get('context'))
            
            # 準備輸入
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            # 生成文本
            outputs = self.model.generate(
                **inputs,
                max_length=kwargs.get('max_length', self.config.max_length),
                temperature=kwargs.get('temperature', self.config.temperature),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )
            
            # 解碼輸出
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取回答部分
            answer = self._extract_answer(generated_text, formatted_prompt)
            
            processing_time = time.time() - start_time
            tokens_generated = len(outputs[0]) - len(inputs['input_ids'][0])
            
            return GenerationResult(
                text=answer,
                model_type=self.config.model_type,
                processing_time=processing_time,
                tokens_generated=tokens_generated,
                metadata={"model_name": self.config.name}
            )
            
            except Exception as e:
            logger.error(f"❌ DeepSeek 生成失敗: {str(e)}")
            return GenerationResult(
                text=f"生成失敗: {str(e)}",
                model_type=self.config.model_type,
                processing_time=time.time() - start_time
            )
    
    def format_prompt(self, prompt: str, context: Optional[List[str]] = None) -> str:
        """
        格式化 DeepSeek 提示文本
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            
        Returns:
            str: 格式化後的提示文本
        """
        if context:
            formatted_prompt = "請根據以下上下文回答問題：\n\n"
            for i, ctx in enumerate(context, 1):
                formatted_prompt += f"上下文 {i}:\n{ctx}\n\n"
            formatted_prompt += f"問題：{prompt}\n\n回答："
        else:
            formatted_prompt = prompt
            
        return formatted_prompt
    
    def _extract_answer(self, generated_text: str, original_prompt: str) -> str:
        """
        從生成的文本中提取回答部分
        
        Args:
            generated_text: 生成的完整文本
            original_prompt: 原始提示
            
        Returns:
            str: 提取的回答
        """
        if "回答：" in generated_text:
            return generated_text.split("回答：")[-1].strip()
        elif len(generated_text) > len(original_prompt):
            return generated_text[len(original_prompt):].strip()
        else:
            return generated_text


class UnifiedLLMTool(BaseTool):
    """
    統一 LLM 工具
    
    此工具整合了多種 LLM 模型，提供統一的介面，
    支援 LangChain 和 CrewAI 生態系統。
    
    Attributes:
        name: 工具名稱
        description: 工具描述
        args_schema: 輸入參數模式
    """
    
    name: str = "unified_llm"
    description: str = "使用多種 LLM 模型進行文本生成和處理，支援 Qwen3、DeepSeek 等模型"
    args_schema = LLMInput
    
    def __init__(self, model_configs: Optional[Dict[str, ModelConfig]] = None) -> None:
        """
        初始化統一 LLM 工具
        
        Args:
            model_configs: 模型配置字典
        """
        super().__init__(
            name="unified_llm",
            description="使用多種 LLM 模型進行文本生成和處理，支援 Qwen3、DeepSeek 等模型",
            args_schema=LLMInput
        )
        
        # 設定預設模型配置
        self.model_configs = model_configs or self._get_default_configs()
        
        # 初始化提供者
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.current_provider: Optional[str] = None
        
        # 載入配置
        self.config = get_config()
        
        # 初始化提供者
        self._initialize_providers()
    
    def _get_default_configs(self) -> Dict[str, ModelConfig]:
        """
        獲取預設模型配置
        
        Returns:
            Dict[str, ModelConfig]: 預設配置字典
        """
        return {
            "qwen3": ModelConfig(
                name="Qwen3-7B-Instruct",
                path="Qwen/Qwen3-7B-Instruct",
                model_type="qwen3",
                max_length=2048,
                temperature=0.7
            ),
            "deepseek": ModelConfig(
                name="DeepSeek-R1",
                path="deepseek-ai/deepseek-r1",
                model_type="deepseek",
                max_length=2048,
                temperature=0.7
            )
        }
    
    def _initialize_providers(self) -> None:
        """初始化所有模型提供者"""
        try:
            for model_type, config in self.model_configs.items():
                if model_type == "qwen3":
                    self.providers[model_type] = Qwen3Provider(config)
                elif model_type == "deepseek":
                    self.providers[model_type] = DeepSeekProvider(config)
                else:
                    logger.warning(f"不支援的模型類型: {model_type}")
            
            # 設定預設提供者
            if "qwen3" in self.providers:
                self.current_provider = "qwen3"
            elif self.providers:
                self.current_provider = list(self.providers.keys())[0]
            
            logger.info(f"✅ 初始化 {len(self.providers)} 個模型提供者")
            
        except Exception as e:
            logger.error(f"❌ 初始化提供者失敗: {str(e)}")
            raise
    
    def _run(
        self, 
        prompt: str, 
        context: Optional[List[str]] = None, 
        max_length: int = 2048, 
        temperature: float = 0.7,
        model_type: str = "qwen3",
        system_prompt: Optional[str] = None
    ) -> str:
        """
        同步執行文本生成
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            max_length: 最大生成長度
            temperature: 溫度參數
            model_type: 模型類型
            system_prompt: 系統提示
            
        Returns:
            str: 生成的文本
        """
        try:
            # 使用異步方法
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已經在事件循環中，創建新線程
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._agenerate_text(prompt, context, max_length, temperature, model_type, system_prompt)
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    self._agenerate_text(prompt, context, max_length, temperature, model_type, system_prompt)
                )
            
            return result.text
            
        except Exception as e:
            logger.error(f"❌ 同步生成失敗: {str(e)}")
            return f"生成失敗: {str(e)}"
    
    async def _arun(
        self, 
        prompt: str, 
        context: Optional[List[str]] = None, 
        max_length: int = 2048, 
        temperature: float = 0.7,
        model_type: str = "qwen3",
        system_prompt: Optional[str] = None
    ) -> str:
        """
        異步執行文本生成
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            max_length: 最大生成長度
            temperature: 溫度參數
            model_type: 模型類型
            system_prompt: 系統提示
            
        Returns:
            str: 生成的文本
        """
        try:
            result = await self._agenerate_text(prompt, context, max_length, temperature, model_type, system_prompt)
            return result.text
            
        except Exception as e:
            logger.error(f"❌ 異步生成失敗: {str(e)}")
            return f"生成失敗: {str(e)}"
    
    async def _agenerate_text(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        max_length: int = 2048,
        temperature: float = 0.7,
        model_type: str = "qwen3",
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """
        異步生成文本的核心方法
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            max_length: 最大生成長度
            temperature: 溫度參數
            model_type: 模型類型
            system_prompt: 系統提示
            
        Returns:
            GenerationResult: 生成結果
        """
        # 選擇提供者
        provider = self._get_provider(model_type)
        if not provider:
            return GenerationResult(
                text=f"不支援的模型類型: {model_type}",
                model_type=model_type,
                processing_time=0.0
            )
        
        # 準備參數
        kwargs = {
            'max_length': max_length,
            'temperature': temperature,
            'context': context
        }
        
        if system_prompt:
            kwargs['system_prompt'] = system_prompt
        
        # 生成文本
        return await provider.generate_text(prompt, **kwargs)
    
    def _get_provider(self, model_type: str) -> Optional[BaseLLMProvider]:
        """
        獲取指定的模型提供者
        
        Args:
            model_type: 模型類型
            
        Returns:
            Optional[BaseLLMProvider]: 模型提供者
        """
        if model_type in self.providers:
            return self.providers[model_type]
        elif self.current_provider:
            logger.warning(f"模型 {model_type} 不存在，使用預設模型: {self.current_provider}")
            return self.providers[self.current_provider]
        else:
            return None
    
    def get_available_models(self) -> List[str]:
        """
        獲取可用的模型列表
        
        Returns:
            List[str]: 可用模型列表
        """
        return list(self.providers.keys())
    
    def switch_model(self, model_type: str) -> bool:
        """
        切換到指定模型
        
        Args:
            model_type: 模型類型
            
        Returns:
            bool: 切換是否成功
        """
        if model_type in self.providers:
            self.current_provider = model_type
            logger.info(f"✅ 切換到模型: {model_type}")
            return True
        else:
            logger.error(f"❌ 模型 {model_type} 不存在")
            return False
    
    async def health_check(self, model_type: Optional[str] = None) -> Dict[str, Any]:
        """
        健康檢查
        
        Args:
            model_type: 模型類型，如果為 None 則檢查所有模型
            
        Returns:
            Dict[str, Any]: 健康檢查結果
        """
        results = {}
        
        if model_type:
            providers_to_check = {model_type: self.providers.get(model_type)}
        else:
            providers_to_check = self.providers
        
        for mt, provider in providers_to_check.items():
            if provider:
                is_healthy = await provider.health_check()
                results[mt] = {
                    "healthy": is_healthy,
                    "model_name": provider.config.name,
                    "is_loaded": provider.is_loaded
                }
            else:
                results[mt] = {
                    "healthy": False,
                    "error": "Provider not found"
                }
        
        return results


# 全域工具實例
unified_llm_tool = UnifiedLLMTool()


def get_unified_llm_tool() -> UnifiedLLMTool:
    """
    獲取統一 LLM 工具實例
    
    Returns:
        UnifiedLLMTool: 工具實例
    """
    return unified_llm_tool


if __name__ == "__main__":
    # 測試統一 LLM 工具
    async def test_unified_llm():
        """測試統一 LLM 工具"""
        print("🔧 統一 LLM 工具測試")
        print("=" * 50)
        
        tool = get_unified_llm_tool()
        
        # 顯示可用模型
        print(f"可用模型: {tool.get_available_models()}")
        print(f"當前模型: {tool.current_provider}")
        
        # 健康檢查
        print("\n🏥 模型健康檢查:")
        health_results = await tool.health_check()
        for model_type, result in health_results.items():
            status = "✅" if result["healthy"] else "❌"
            print(f"  {model_type}: {status} - {result}")
        
        # 測試文本生成
        print("\n🤖 文本生成測試:")
        test_prompt = "請用繁體中文介紹一下你自己"
        response = await tool._arun(test_prompt)
        print(f"回應: {response}")
        
        print("\n✅ 測試完成")
    
    # 執行測試
    asyncio.run(test_unified_llm()) 