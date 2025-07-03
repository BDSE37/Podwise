#!/usr/bin/env python3
"""
DeepSeek 工具
用於與 DeepSeek LLM 進行互動
"""

import os
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class DeepseekTool:
    """DeepSeek 工具類別"""
    
    def __init__(self):
        """初始化 DeepSeek 工具"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.llm = None
        
        if self.api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model,
                    temperature=0.7,
                    max_tokens=2000
                )
                logger.info("✅ DeepSeek 工具初始化成功")
            except Exception as e:
                logger.warning(f"⚠️  DeepSeek 工具初始化失敗: {e}")
        else:
            logger.warning("⚠️  DeepSeek API Key 未設定")
    
    def is_available(self) -> bool:
        """檢查 DeepSeek 是否可用"""
        return self.llm is not None and self.api_key != ""
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """生成回應"""
        if not self.is_available():
            return {
                "response": "DeepSeek 工具不可用",
                "error": "API Key 未設定或初始化失敗",
                "success": False
            }
        
        try:
            messages = []
            
            if context:
                messages.append(SystemMessage(content=f"上下文資訊：{context}"))
            
            messages.append(HumanMessage(content=prompt))
            
            response = await self.llm.agenerate([messages])
            
            return {
                "response": response.generations[0][0].text,
                "success": True,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"DeepSeek 生成回應失敗: {e}")
            return {
                "response": f"生成回應時發生錯誤: {str(e)}",
                "error": str(e),
                "success": False
            }
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查詢"""
        prompt = f"""
        請分析以下查詢，並提供以下資訊：
        1. 查詢類型（商業/教育/其他）
        2. 關鍵詞
        3. 建議的處理方式
        
        查詢：{query}
        """
        
        return await self.generate_response(prompt)
    
    async def summarize_content(self, content: str) -> Dict[str, Any]:
        """總結內容"""
        prompt = f"""
        請總結以下內容，重點關注主要觀點和關鍵資訊：
        
        {content}
        """
        
        return await self.generate_response(prompt)
    
    async def generate_questions(self, topic: str, count: int = 5) -> Dict[str, Any]:
        """生成相關問題"""
        prompt = f"""
        基於主題「{topic}」，生成 {count} 個相關的問題，問題應該涵蓋不同層面和深度。
        """
        
        return await self.generate_response(prompt) 