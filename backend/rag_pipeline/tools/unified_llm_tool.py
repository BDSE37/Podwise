"""
統一 LLM 工具
整合多種 LLM 模型的工具，避免重複代碼
"""

from typing import List, Dict, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class LLMInput(BaseModel):
    """LLM 輸入模型"""
    prompt: str = Field(description="輸入提示")
    context: Optional[List[str]] = Field(default=None, description="上下文文本列表")
    max_length: int = Field(default=2048, description="最大生成長度")
    temperature: float = Field(default=0.7, description="溫度參數")
    model_type: str = Field(default="qwen3", description="模型類型: qwen3, deepseek")

class UnifiedLLMTool(BaseTool):
    """統一 LLM 工具 - 支援多種模型"""
    
    name = "unified_llm"
    description = "使用多種 LLM 模型進行文本生成和處理"
    args_schema = LLMInput
    
    def __init__(self, model_configs: Dict[str, str] = None):
        """
        初始化統一 LLM 工具
        
        Args:
            model_configs: 模型配置字典
        """
        super().__init__()
        self.model_configs = model_configs or {
            "qwen3": "Qwen/Qwen3-7B-Instruct",
            "deepseek": "deepseek-ai/deepseek-r1"
        }
        self.models = {}
        self.tokenizers = {}
        self._load_models()
        
    def _load_models(self):
        """載入所有模型和分詞器"""
        for model_type, model_name in self.model_configs.items():
            try:
                logger.info(f"載入 {model_type} 模型: {model_name}")
                self.tokenizers[model_type] = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
                self.models[model_type] = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    device_map="auto"
                )
                logger.info(f"✅ {model_type} 模型載入成功")
            except Exception as e:
                logger.error(f"❌ 載入 {model_type} 模型失敗: {str(e)}")
                raise
    
    def _prepare_prompt(self, prompt: str, context: List[str] = None, model_type: str = "qwen3") -> str:
        """
        根據模型類型準備提示文本
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            model_type: 模型類型
            
        Returns:
            str: 格式化後的提示文本
        """
        if model_type == "deepseek" and context:
            # Deepseek 格式：上下文 + 問題
            formatted_prompt = "請根據以下上下文回答問題：\n\n"
            for i, ctx in enumerate(context, 1):
                formatted_prompt += f"上下文 {i}:\n{ctx}\n\n"
            formatted_prompt += f"問題：{prompt}\n\n回答："
        else:
            # Qwen3 或其他模型格式：直接使用提示
            formatted_prompt = prompt
            
        return formatted_prompt
    
    def _run(
        self, 
        prompt: str, 
        context: List[str] = None, 
        max_length: int = 2048, 
        temperature: float = 0.7,
        model_type: str = "qwen3"
    ) -> str:
        """
        執行文本生成
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            max_length: 最大生成長度
            temperature: 溫度參數
            model_type: 模型類型
            
        Returns:
            str: 生成的文本
        """
        try:
            if model_type not in self.models:
                raise ValueError(f"不支援的模型類型: {model_type}")
            
            # 準備提示
            formatted_prompt = self._prepare_prompt(prompt, context, model_type)
            
            # 準備輸入
            tokenizer = self.tokenizers[model_type]
            model = self.models[model_type]
            
            inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
            
            # 生成文本
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id
            )
            
            # 解碼輸出
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 根據模型類型提取回答
            if model_type == "deepseek" and context:
                answer = generated_text.split("回答：")[-1].strip()
            else:
                answer = generated_text
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ {model_type} 生成失敗: {str(e)}")
            return ""
    
    async def _arun(
        self, 
        prompt: str, 
        context: List[str] = None, 
        max_length: int = 2048, 
        temperature: float = 0.7,
        model_type: str = "qwen3"
    ) -> str:
        """
        非同步執行文本生成
        
        Args:
            prompt: 輸入提示
            context: 上下文文本列表
            max_length: 最大生成長度
            temperature: 溫度參數
            model_type: 模型類型
            
        Returns:
            str: 生成的文本
        """
        return self._run(prompt, context, max_length, temperature, model_type)
    
    def get_available_models(self) -> List[str]:
        """獲取可用的模型列表"""
        return list(self.models.keys())
    
    def switch_model(self, model_type: str) -> bool:
        """
        切換到指定模型
        
        Args:
            model_type: 模型類型
            
        Returns:
            bool: 切換是否成功
        """
        return model_type in self.models 