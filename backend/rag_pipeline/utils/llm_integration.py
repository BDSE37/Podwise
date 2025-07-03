"""
LLM 整合模組
整合 AnythingLLM 來改進摘要生成和搜索功能
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import requests
import json
from datetime import datetime

class LLMConfig(BaseModel):
    """LLM 配置模型"""
    
    api_base: str = Field(description="API 基礎 URL")
    api_key: str = Field(description="API 金鑰")
    model_name: str = Field(description="模型名稱")
    temperature: float = Field(description="溫度參數", ge=0, le=1)
    max_tokens: int = Field(description="最大 token 數")
    
class SearchResult(BaseModel):
    """搜索結果模型"""
    
    content: str = Field(description="內容")
    score: float = Field(description="相關性分數")
    metadata: Dict[str, Any] = Field(description="元數據")
    
class LLMIntegration:
    """LLM 整合類"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化 LLM 整合
        
        Args:
            config: LLM 配置
        """
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
    async def generate_summary(
        self,
        content: str,
        category: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成內容摘要
        
        Args:
            content: 原始內容
            category: 內容類別
            context: 額外上下文
            
        Returns:
            Dict[str, Any]: 摘要結果
        """
        try:
            # 準備提示詞
            prompt = self._prepare_summary_prompt(content, category, context)
            
            # 調用 LLM API
            response = await self._call_llm_api(prompt)
            
            # 解析結果
            summary = self._parse_summary_response(response)
            
            return summary
            
        except Exception as e:
            print(f"生成摘要時發生錯誤: {str(e)}")
            return {}
            
    async def semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        語義搜索
        
        Args:
            query: 搜索查詢
            filters: 過濾條件
            top_k: 返回結果數量
            
        Returns:
            List[SearchResult]: 搜索結果列表
        """
        try:
            # 準備搜索請求
            search_request = {
                "query": query,
                "filters": filters or {},
                "top_k": top_k
            }
            
            # 調用搜索 API
            response = await self._call_search_api(search_request)
            
            # 解析結果
            results = self._parse_search_results(response)
            
            return results
            
        except Exception as e:
            print(f"執行語義搜索時發生錯誤: {str(e)}")
            return []
            
    def _prepare_summary_prompt(
        self,
        content: str,
        category: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        準備摘要提示詞
        
        Args:
            content: 原始內容
            category: 內容類別
            context: 額外上下文
            
        Returns:
            str: 提示詞
        """
        # 根據類別選擇不同的提示詞模板
        templates = {
            "教育": """
            請分析以下教育類內容，並提供：
            1. 主要觀點（3-5點）
            2. 關鍵洞察（2-3點）
            3. 實用建議（2-3點）
            4. 情感傾向分析
            
            內容：
            {content}
            
            額外上下文：
            {context}
            """,
            
            "商業": """
            請分析以下商業類內容，並提供：
            1. 市場分析要點（3-5點）
            2. 投資建議（2-3點）
            3. 風險提示（2-3點）
            4. 市場情緒分析
            
            內容：
            {content}
            
            額外上下文：
            {context}
            """
        }
        
        template = templates.get(category, templates["教育"])
        return template.format(
            content=content,
            context=json.dumps(context, ensure_ascii=False) if context else "無"
        )
        
    async def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        調用 LLM API
        
        Args:
            prompt: 提示詞
            
        Returns:
            Dict[str, Any]: API 響應
        """
        try:
            url = f"{self.config.api_base}/v1/chat/completions"
            
            payload = {
                "model": self.config.model_name,
                "messages": [
                    {"role": "system", "content": "你是一個專業的內容分析專家"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            async with requests.post(url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            print(f"調用 LLM API 時發生錯誤: {str(e)}")
            raise
            
    async def _call_search_api(self, search_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        調用搜索 API
        
        Args:
            search_request: 搜索請求
            
        Returns:
            Dict[str, Any]: API 響應
        """
        try:
            url = f"{self.config.api_base}/v1/search"
            
            async with requests.post(url, headers=self.headers, json=search_request) as response:
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            print(f"調用搜索 API 時發生錯誤: {str(e)}")
            raise
            
    def _parse_summary_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析摘要響應
        
        Args:
            response: API 響應
            
        Returns:
            Dict[str, Any]: 解析後的摘要
        """
        try:
            content = response["choices"][0]["message"]["content"]
            
            # 解析結構化摘要
            sections = content.split("\n\n")
            summary = {}
            
            for section in sections:
                if "主要觀點" in section or "市場分析要點" in section:
                    summary["main_points"] = self._extract_list_items(section)
                elif "關鍵洞察" in section or "投資建議" in section:
                    summary["key_insights"] = self._extract_list_items(section)
                elif "實用建議" in section or "風險提示" in section:
                    summary["action_items"] = self._extract_list_items(section)
                elif "情感傾向" in section or "市場情緒" in section:
                    summary["sentiment"] = self._extract_sentiment(section)
                    
            return summary
            
        except Exception as e:
            print(f"解析摘要響應時發生錯誤: {str(e)}")
            return {}
            
    def _parse_search_results(self, response: Dict[str, Any]) -> List[SearchResult]:
        """
        解析搜索結果
        
        Args:
            response: API 響應
            
        Returns:
            List[SearchResult]: 搜索結果列表
        """
        try:
            results = []
            
            for item in response["results"]:
                result = SearchResult(
                    content=item["content"],
                    score=item["score"],
                    metadata=item["metadata"]
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            print(f"解析搜索結果時發生錯誤: {str(e)}")
            return []
            
    def _extract_list_items(self, text: str) -> List[str]:
        """
        提取列表項目
        
        Args:
            text: 文本內容
            
        Returns:
            List[str]: 列表項目
        """
        items = []
        lines = text.split("\n")
        
        for line in lines:
            if line.strip().startswith(("-", "•", "1.", "2.", "3.")):
                item = line.strip().lstrip("-•123456789. ")
                if item:
                    items.append(item)
                    
        return items
        
    def _extract_sentiment(self, text: str) -> str:
        """
        提取情感傾向
        
        Args:
            text: 文本內容
            
        Returns:
            str: 情感傾向
        """
        if "正面" in text or "樂觀" in text:
            return "正面"
        elif "負面" in text or "悲觀" in text:
            return "負面"
        else:
            return "中性" 