#!/usr/bin/env python3
"""
Qwen3 工具
用於與 Qwen3 LLM 進行互動
"""

import os
import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)

class Qwen3Tool:
    """Qwen3 工具類別"""
    
    def __init__(self):
        """初始化 Qwen3 工具"""
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:8b")
        self.api_url = f"{self.ollama_host}/api/generate"
        
        # 測試連接
        self._available = self._test_connection()
        
        if self._available:
            logger.info("✅ Qwen3 工具初始化成功")
        else:
            logger.warning("⚠️  Qwen3 工具初始化失敗 - Ollama 服務不可用")
    
    def _test_connection(self) -> bool:
        """測試 Ollama 連接"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 連接測試失敗: {e}")
            return False
    
    def is_available(self) -> bool:
        """檢查 Qwen3 是否可用"""
        return self._available
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """生成回應"""
        if not self.is_available():
            return {
                "response": "Qwen3 工具不可用",
                "error": "Ollama 服務不可用",
                "success": False
            }
        
        try:
            # 準備請求資料
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            # 如果有上下文，添加到提示中
            if context:
                data["prompt"] = f"上下文：{context}\n\n問題：{prompt}"
            
            # 發送請求
            response = requests.post(self.api_url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "success": True,
                    "model": self.model,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "response": f"API 請求失敗: {response.status_code}",
                    "error": response.text,
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Qwen3 生成回應失敗: {e}")
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
        
        請以 JSON 格式回應：
        {{
            "type": "查詢類型",
            "keywords": ["關鍵詞1", "關鍵詞2"],
            "suggestions": "建議處理方式"
        }}
        """
        
        return await self.generate_response(prompt)
    
    async def summarize_content(self, content: str) -> Dict[str, Any]:
        """總結內容"""
        prompt = f"""
        請總結以下內容，重點關注主要觀點和關鍵資訊：
        
        {content}
        
        請提供簡潔明瞭的總結。
        """
        
        return await self.generate_response(prompt)
    
    async def generate_questions(self, topic: str, count: int = 5) -> Dict[str, Any]:
        """生成相關問題"""
        prompt = f"""
        基於主題「{topic}」，生成 {count} 個相關的問題，問題應該涵蓋不同層面和深度。
        
        請以列表形式回應：
        1. 問題1
        2. 問題2
        ...
        """
        
        return await self.generate_response(prompt)
    
    async def translate_content(self, content: str, target_language: str = "繁體中文") -> Dict[str, Any]:
        """翻譯內容"""
        prompt = f"""
        請將以下內容翻譯成{target_language}：
        
        {content}
        
        請確保翻譯準確且自然。
        """
        
        return await self.generate_response(prompt) 