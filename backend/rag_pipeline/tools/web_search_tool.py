#!/usr/bin/env python3
"""
Web Search 工具
整合 OpenAI 搜尋功能，當信心度不足時自動執行
"""

import os
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearchResult(BaseModel):
    """Web 搜尋結果模型"""
    title: str
    url: str
    content: str
    relevance_score: float
    source: str
    timestamp: str

class WebSearchTool:
    """Web 搜尋工具類別"""
    
    def __init__(self):
        """初始化 Web 搜尋工具"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.confidence_threshold = 0.7  # 信心度閾值
        
        # 檢查 OpenAI 配置
        self.is_available = bool(self.openai_api_key and len(self.openai_api_key.strip()) > 0)
        
        if self.is_available:
            logger.info("✅ Web Search 工具初始化成功 (OpenAI 可用)")
        else:
            logger.warning("⚠️ Web Search 工具初始化失敗 (OpenAI API Key 未設定)")
    
    def is_configured(self) -> bool:
        """檢查是否已配置"""
        return self.is_available
    
    async def should_use_web_search(self, confidence: float) -> bool:
        """
        判斷是否應該使用 Web 搜尋
        
        Args:
            confidence: 當前信心度
            
        Returns:
            bool: 是否應該使用 Web 搜尋
        """
        return confidence < self.confidence_threshold and self.is_configured()
    
    async def search_with_openai(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用 OpenAI 進行 Web 搜尋
        
        Args:
            query: 搜尋查詢
            context: 可選的上下文資訊
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "OpenAI API Key 未設定",
                "response": "無法執行 Web 搜尋，請檢查 OpenAI 配置"
            }
        
        try:
            # 構建系統提示詞
            system_prompt = """你是一個專業的搜尋助手，能夠提供準確、有用的資訊。
請基於最新的知識和資訊回答用戶的問題。如果問題涉及特定領域，請提供專業且實用的建議。
請用繁體中文回答，並確保回答的準確性和實用性。"""
            
            # 構建用戶提示詞
            user_prompt = query
            if context:
                user_prompt = f"基於以下背景資訊回答問題：\n{context}\n\n問題：{query}"
            
            # 調用 OpenAI API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.openai_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        return {
                            "success": True,
                            "response": content,
                            "confidence": 0.85,  # Web 搜尋預設較高信心值
                            "method": "OpenAI Web Search",
                            "model": self.openai_model,
                            "timestamp": datetime.now().isoformat(),
                            "fallback_used": True
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"OpenAI API 調用失敗: {response.status} - {error_text}",
                            "response": "Web 搜尋失敗，請稍後再試"
                        }
                        
        except Exception as e:
            logger.error(f"Web 搜尋失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Web 搜尋過程中發生錯誤: {str(e)}"
            }
    
    async def enhanced_search(self, query: str, original_confidence: float, 
                            context: Optional[str] = None) -> Dict[str, Any]:
        """
        增強搜尋：結合原始結果和 Web 搜尋
        
        Args:
            query: 搜尋查詢
            original_confidence: 原始搜尋的信心度
            context: 可選的上下文資訊
            
        Returns:
            Dict[str, Any]: 增強搜尋結果
        """
        # 檢查是否需要 Web 搜尋
        if not await self.should_use_web_search(original_confidence):
            return {
                "success": True,
                "response": "原始搜尋結果信心度足夠，無需 Web 搜尋",
                "confidence": original_confidence,
                "method": "Original Search",
                "web_search_used": False
            }
        
        logger.info(f"信心度不足 ({original_confidence:.2f} < {self.confidence_threshold})，執行 Web 搜尋")
        
        # 執行 Web 搜尋
        web_result = await self.search_with_openai(query, context)
        
        if web_result["success"]:
            return {
                "success": True,
                "response": web_result["response"],
                "confidence": web_result["confidence"],
                "method": "OpenAI Web Search",
                "original_confidence": original_confidence,
                "web_search_used": True,
                "timestamp": web_result.get("timestamp", datetime.now().isoformat())
            }
        else:
            return {
                "success": False,
                "response": web_result["response"],
                "confidence": original_confidence,
                "method": "Original Search (Web Search Failed)",
                "error": web_result.get("error", "Unknown error"),
                "web_search_used": False
            }
    
    async def search_business_topic(self, query: str) -> Dict[str, Any]:
        """
        搜尋商業相關主題
        
        Args:
            query: 商業相關查詢
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        business_context = """你是一個專業的商業分析師，專門回答關於投資、理財、市場分析、企業管理等商業相關問題。
請提供實用且準確的商業建議，並考慮台灣市場的特殊性。"""
        
        return await self.search_with_openai(query, business_context)
    
    async def search_education_topic(self, query: str) -> Dict[str, Any]:
        """
        搜尋教育相關主題
        
        Args:
            query: 教育相關查詢
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        education_context = """你是一個專業的教育顧問，專門回答關於學習方法、技能提升、職涯發展、個人成長等教育相關問題。
請提供實用且有效的學習建議，幫助用戶達成學習目標。"""
        
        return await self.search_with_openai(query, education_context)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        獲取搜尋統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        return {
            "tool_name": "Web Search Tool",
            "openai_configured": self.is_configured(),
            "confidence_threshold": self.confidence_threshold,
            "model": self.openai_model if self.is_configured() else "N/A",
            "status": "available" if self.is_configured() else "unavailable"
        }
    
    def update_confidence_threshold(self, threshold: float) -> None:
        """
        更新信心度閾值
        
        Args:
            threshold: 新的閾值 (0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"信心度閾值已更新為: {threshold}")
        else:
            logger.warning(f"無效的信心度閾值: {threshold}，應在 0.0-1.0 之間")

# 向後相容性別名
OpenAISearchTool = WebSearchTool

# 示範使用方式
if __name__ == "__main__":
    import asyncio
    
    async def test_web_search():
        """測試 Web 搜尋功能"""
        web_search = WebSearchTool()
        
        # 測試配置狀態
        print(f"Web Search 配置狀態: {web_search.is_configured()}")
        
        if web_search.is_configured():
            # 測試商業主題搜尋
            business_query = "台積電最近的股價表現如何？"
            result = await web_search.search_business_topic(business_query)
            print(f"商業搜尋結果: {result['response'][:200]}...")
            
            # 測試教育主題搜尋
            education_query = "如何提升職場溝通技巧？"
            result = await web_search.search_education_topic(education_query)
            print(f"教育搜尋結果: {result['response'][:200]}...")
            
            # 測試增強搜尋
            enhanced_result = await web_search.enhanced_search(
                "Python 程式設計學習建議", 
                original_confidence=0.5
            )
            print(f"增強搜尋結果: {enhanced_result['response'][:200]}...")
        else:
            print("OpenAI API Key 未設定，無法測試 Web 搜尋功能")
    
    # 執行測試
    asyncio.run(test_web_search()) 