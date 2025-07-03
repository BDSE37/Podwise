# src/core/llm_manager.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.logging_config import get_logger

logger = get_logger(__name__)

class LLMManager:
    """Qwen2.5-Taiwan 語言模型管理器"""
    
    # 台灣優化模型列表
    TAIWAN_MODELS = {
        "qwen-taiwan-7b": "weiren119/Qwen2.5-Taiwan-7B-Instruct",
        "qwen-taiwan-3b": "weiren119/Qwen2.5-Taiwan-3B-Instruct",
        "qwen-taiwan-1.5b": "weiren119/Qwen2.5-Taiwan-1.5B-Instruct",
        "qwen-taiwan-0.5b": "weiren119/Qwen2.5-Taiwan-0.5B-Instruct"
    }
    
    def __init__(self, model_size: str = "3b", custom_model: Optional[str] = None):
        """
        初始化 LLM 管理器
        
        Args:
            model_size: 模型大小 ("7b", "3b", "1.5b", "0.5b")
            custom_model: 自定義模型路徑
        """
        if custom_model:
            self.model_name = custom_model
        else:
            model_key = f"qwen-taiwan-{model_size}"
            self.model_name = self.TAIWAN_MODELS.get(model_key, self.TAIWAN_MODELS["qwen-taiwan-3b"])
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # 台灣特色系統提示詞
        self.taiwan_system_prompt = """你是 Podri，一個專為台灣用戶設計的 AI 助理。請遵守以下規則：
1. 使用台灣的繁體中文和用語習慣
2. 了解台灣的文化、地理、歷史和時事
3. 使用台灣人熟悉的詞彙（例如：軟體而非软件、程式而非程序）
4. 保持友善、親切的對話風格
5. 適時使用台灣常見的語助詞讓對話更自然"""
        
        logger.info(f"初始化 Qwen2.5-Taiwan 管理器")
        logger.info(f"使用模型: {self.model_name}")
        logger.info(f"使用設備: {self.device}")
    
    async def initialize(self):
        """異步初始化模型"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._load_model)
    
    def _load_model(self):
        """載入模型和分詞器"""
        try:
            logger.info(f"正在載入 Qwen2.5-Taiwan 模型: {self.model_name}")
            
            # 載入分詞器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=True
            )
            
            # 根據設備選擇適當的配置
            if self.device == "cuda":
                # GPU 配置
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            else:
                # CPU 配置
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            
            # 設置 pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Qwen2.5-Taiwan 模型載入完成")
            
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        taiwan_mode: bool = True
    ) -> str:
        """
        生成回應
        
        Args:
            prompt: 用戶輸入
            system_prompt: 系統提示詞
            context: 對話上下文
            max_length: 最大生成長度
            temperature: 溫度參數
            top_p: Top-p 採樣參數
            taiwan_mode: 是否使用台灣模式
            
        Returns:
            生成的回應文字
        """
        if not self.model or not self.tokenizer:
            await self.initialize()
        
        # 使用台灣特色系統提示詞
        if taiwan_mode and not system_prompt:
            system_prompt = self.taiwan_system_prompt
        
        # 構建對話
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # 添加上下文
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        # 異步生成
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            self._generate,
            messages,
            max_length,
            temperature,
            top_p
        )
        
        return response
    
    def _generate(
        self,
        messages: List[Dict[str, str]],
        max_length: int,
        temperature: float,
        top_p: float
    ) -> str:
        """同步生成方法"""
        try:
            # 應用對話模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 編碼輸入
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # 生成回應
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1  # 避免重複
                )
            
            # 解碼回應
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            # 後處理：確保使用台灣用語
            response = self._post_process_taiwan(response)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成回應失敗: {e}")
            raise
    
    def _post_process_taiwan(self, text: str) -> str:
        """後處理以確保台灣用語"""
        # 簡單的詞彙替換示例
        replacements = {
            "軟件": "軟體",
            "硬件": "硬體",
            "程序": "程式",
            "信息": "資訊",
            "網絡": "網路",
            "數據": "資料",
            "服務器": "伺服器",
            "內存": "記憶體",
            "文檔": "文件",
            "默認": "預設"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
