#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search Expert - 網路搜尋專家

使用 OpenAI 官方的 Web Search 工具進行智能網路搜尋，支援多語言查詢和多來源搜尋。
整合到 RAG Pipeline 的 fallback 機制中。

Author: Podwise Team
License: MIT
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import httpx
except ImportError:
    httpx = None
    logging.warning("httpx 未安裝，將使用 urllib 作為備選")

try:
    from utils.logging_config import get_logger
except ImportError:
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜尋結果資料結構"""
    title: str
    url: str
    snippet: str
    source: str
    confidence: float
    timestamp: datetime


@dataclass
class SearchRequest:
    """搜尋請求資料結構"""
    query: str
    max_results: int = 3
    language: str = "zh-TW"
    search_type: str = "web"  # web, news, academic
    include_summary: bool = True


@dataclass
class SearchResponse:
    """搜尋回應資料結構"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    confidence: float
    summary: Optional[str] = None
    source: str = "openai_web_search"


class WebSearchExpert:
    """網路搜尋專家類別
    
    使用 OpenAI 官方的 Web Search 工具，支援：
    - 多語言查詢
    - 多來源搜尋
    - 智能摘要生成
    - 信心度評估
    """
    
    def __init__(self, api_key: Optional[str] = None, 
                 api_base: Optional[str] = None,
                 model: str = "gpt-4o",
                 timeout: int = 30):
        """
        初始化 Web Search Expert
        
        Args:
            api_key: OpenAI API 金鑰
            api_base: OpenAI API 基礎 URL
            model: 使用的模型名稱（建議使用 gpt-4o 以支援 tools）
            timeout: 請求超時時間
        """
        # 嘗試載入 backend/.env 檔案
        backend_env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        if os.path.exists(backend_env_path):
            from dotenv import load_dotenv
            load_dotenv(backend_env_path)
            logger.info(f"已載入環境變數檔案: {backend_env_path}")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("OpenAI API 金鑰未設定，WebSearchExpert 將以受限模式運行")
            self._initialized = False
            return
        
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        
        logger.info(f"WebSearchExpert 初始化完成，模型: {self.model}")
    
    async def initialize(self) -> bool:
        """初始化 HTTP 客戶端"""
        try:
            if httpx is not None:
                self.http_client = httpx.AsyncClient(
                    timeout=self.timeout,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            self._initialized = True
            logger.info("WebSearchExpert HTTP 客戶端初始化成功")
            return True
        except Exception as e:
            logger.error(f"WebSearchExpert 初始化失敗: {e}")
            return False
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        執行網路搜尋
        
        Args:
            request: 搜尋請求
            
        Returns:
            搜尋回應
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            # 使用 OpenAI 官方 Web Search 工具
            search_results = await self._openai_web_search_with_tools(request)
            
            # 生成摘要（如果需要）
            summary = None
            if request.include_summary and search_results:
                summary = await self._generate_summary_with_tools(request.query, search_results)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 計算信心度
            confidence = self._calculate_confidence(search_results, summary)
            
            return SearchResponse(
                query=request.query,
                results=search_results,
                summary=summary,
                total_results=len(search_results),
                processing_time=processing_time,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"網路搜尋失敗: {e}")
            return SearchResponse(
                query=request.query,
                results=[],
                summary="搜尋失敗，請稍後再試",
                total_results=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                confidence=0.0
            )
    
    async def _openai_web_search_with_tools(self, request: SearchRequest) -> List[SearchResult]:
        """使用 OpenAI 官方 Web Search 工具進行搜尋"""
        try:
            # 構建搜尋提示
            search_prompt = self._build_search_prompt(request)
            
            # 調用 OpenAI API 使用 tools
            response = await self._call_openai_api_with_tools(search_prompt)
            
            # 解析回應
            results = self._parse_openai_tools_response(response, request)
            
            return results
            
        except Exception as e:
            logger.error(f"OpenAI Web Search 失敗: {e}")
            return []
    
    def _build_search_prompt(self, request: SearchRequest) -> str:
        """構建搜尋提示"""
        language_map = {
            "zh-TW": "繁體中文",
            "zh-CN": "簡體中文", 
            "en": "English",
            "ja": "日本語"
        }
        
        language = language_map.get(request.language, "繁體中文")
        
        prompt = f"""
請為以下查詢進行網路搜尋並提供最新的相關資訊：

查詢：{request.query}
語言：{language}
搜尋類型：{request.search_type}

請使用網路搜尋工具獲取最新的相關資訊，並提供以下格式的結果：
1. 標題
2. URL
3. 摘要（100-200字）
4. 來源
5. 相關性評分（0-1）

如果找不到相關資訊，請說明原因。
"""
        return prompt
    
    async def _call_openai_api_with_tools(self, prompt: str) -> Dict[str, Any]:
        """調用 OpenAI API 使用 tools"""
        if not self.http_client:
            raise RuntimeError("HTTP 客戶端未初始化")
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一個專業的網路搜尋助手，能夠提供準確、最新的資訊。請使用網路搜尋工具獲取最新資訊。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "tools": [
                {
                    "type": "web_search"
                }
            ],
            "tool_choice": {
                "type": "function",
                "function": {
                    "name": "web_search"
                }
            },
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        try:
            response = await self.http_client.post(
                f"{self.api_base}/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                raise Exception(f"OpenAI API 錯誤: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OpenAI API 調用失敗: {e}")
            raise
    
    def _parse_openai_tools_response(self, response: Dict[str, Any], request: SearchRequest) -> List[SearchResult]:
        """解析 OpenAI tools 回應"""
        results = []
        
        try:
            # 檢查是否有 tool calls
            choices = response.get("choices", [])
            if not choices:
                return results
            
            choice = choices[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])
            
            # 處理 tool calls
            for tool_call in tool_calls:
                if tool_call.get("type") == "function" and tool_call.get("function", {}).get("name") == "web_search":
                    # 解析 web_search 結果
                    function_response = tool_call.get("function", {}).get("output", "")
                    parsed_results = self._parse_web_search_output(function_response, request)
                    results.extend(parsed_results)
            
            # 如果沒有 tool calls，嘗試解析一般回應
            if not results:
                content = message.get("content", "")
                results = self._parse_fallback_response(content, request)
            
            return results[:request.max_results]
            
        except Exception as e:
            logger.error(f"解析 OpenAI tools 回應失敗: {e}")
            return []
    
    def _parse_web_search_output(self, output: str, request: SearchRequest) -> List[SearchResult]:
        """解析 web_search 工具輸出"""
        results = []
        
        try:
            # 嘗試解析 JSON 格式
            if output.startswith('{') or output.startswith('['):
                data = json.loads(output)
                if isinstance(data, list):
                    for item in data:
                        results.append(SearchResult(
                            title=item.get('title', '未知標題'),
                            url=item.get('url', ''),
                            snippet=item.get('snippet', ''),
                            source=item.get('source', 'Web Search'),
                            confidence=item.get('confidence', 0.8),
                            timestamp=datetime.now()
                        ))
                elif isinstance(data, dict):
                    results.append(SearchResult(
                        title=data.get('title', '未知標題'),
                        url=data.get('url', ''),
                        snippet=data.get('snippet', ''),
                        source=data.get('source', 'Web Search'),
                        confidence=data.get('confidence', 0.8),
                        timestamp=datetime.now()
                    ))
            else:
                # 解析文本格式
                results = self._parse_text_output(output, request)
            
            return results
            
        except Exception as e:
            logger.error(f"解析 web_search 輸出失敗: {e}")
            return []
    
    def _parse_text_output(self, text: str, request: SearchRequest) -> List[SearchResult]:
        """解析文本格式的搜尋結果"""
        results = []
        
        try:
            lines = text.split('\n')
            current_result = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('標題：') or line.startswith('Title:'):
                    if current_result:
                        results.append(self._create_search_result(current_result))
                        current_result = {}
                    current_result['title'] = line.split('：', 1)[1] if '：' in line else line.split(':', 1)[1]
                
                elif line.startswith('URL：') or line.startswith('URL:'):
                    current_result['url'] = line.split('：', 1)[1] if '：' in line else line.split(':', 1)[1]
                
                elif line.startswith('摘要：') or line.startswith('Summary:'):
                    current_result['snippet'] = line.split('：', 1)[1] if '：' in line else line.split(':', 1)[1]
                
                elif line.startswith('來源：') or line.startswith('Source:'):
                    current_result['source'] = line.split('：', 1)[1] if '：' in line else line.split(':', 1)[1]
                
                elif line.startswith('評分：') or line.startswith('Score:'):
                    try:
                        score_text = line.split('：', 1)[1] if '：' in line else line.split(':', 1)[1]
                        current_result['confidence'] = float(score_text)
                    except:
                        current_result['confidence'] = 0.7
            
            # 添加最後一個結果
            if current_result:
                results.append(self._create_search_result(current_result))
            
            return results
            
        except Exception as e:
            logger.error(f"解析文本輸出失敗: {e}")
            return []
    
    def _parse_fallback_response(self, content: str, request: SearchRequest) -> List[SearchResult]:
        """解析備用回應"""
        return [SearchResult(
            title=f"搜尋結果：{request.query}",
            url="",
            snippet=content[:500] + "..." if len(content) > 500 else content,
            source="OpenAI Web Search",
            confidence=0.7,
            timestamp=datetime.now()
        )]
    
    def _create_search_result(self, data: Dict[str, Any]) -> SearchResult:
        """創建搜尋結果"""
        return SearchResult(
            title=data.get('title', '未知標題'),
            url=data.get('url', ''),
            snippet=data.get('snippet', ''),
            source=data.get('source', 'OpenAI Web Search'),
            confidence=data.get('confidence', 0.7),
            timestamp=datetime.now()
        )
    
    async def _generate_summary_with_tools(self, query: str, results: List[SearchResult]) -> str:
        """使用 tools 生成搜尋摘要"""
        try:
            # 構建摘要提示
            summary_prompt = f"""
基於以下搜尋結果，為查詢「{query}」生成一個簡潔的摘要（100-150字）：

"""
            for i, result in enumerate(results, 1):
                summary_prompt += f"""
結果 {i}：
標題：{result.title}
摘要：{result.snippet}
來源：{result.source}
"""
            
            summary_prompt += "\n請提供一個客觀、準確的摘要。"
            
            # 調用 OpenAI API 生成摘要
            response = await self._call_openai_api_with_tools(summary_prompt)
            
            # 解析摘要
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                return content.strip()
            
            return "無法生成摘要"
            
        except Exception as e:
            logger.error(f"生成摘要失敗: {e}")
            return "無法生成摘要"
    
    def _calculate_confidence(self, results: List[SearchResult], summary: Optional[str]) -> float:
        """計算搜尋信心度"""
        if not results:
            return 0.0
        
        # 基於結果數量、摘要存在性、平均信心度計算
        avg_confidence = sum(r.confidence for r in results) / len(results)
        summary_bonus = 0.1 if summary else 0.0
        count_bonus = min(len(results) * 0.05, 0.2)
        
        return min(avg_confidence + summary_bonus + count_bonus, 1.0)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 簡單的 API 測試
            test_prompt = "測試"
            await self._call_openai_api_with_tools(test_prompt)
            
            return {
                "status": "healthy",
                "api_key_configured": bool(self.api_key),
                "model": self.model,
                "tools_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self) -> bool:
        """清理資源"""
        try:
            if self.http_client:
                await self.http_client.aclose()
            return True
        except Exception as e:
            logger.error(f"清理資源失敗: {e}")
            return False


# 全域 WebSearchExpert 實例
_web_search_expert: Optional[WebSearchExpert] = None


def get_web_search_expert() -> WebSearchExpert:
    """獲取全域 WebSearchExpert 實例"""
    global _web_search_expert
    if _web_search_expert is None:
        _web_search_expert = WebSearchExpert()
    return _web_search_expert


async def search_web(query: str, max_results: int = 3, language: str = "zh-TW") -> SearchResponse:
    """便捷的網路搜尋函數"""
    expert = get_web_search_expert()
    request = SearchRequest(
        query=query,
        max_results=max_results,
        language=language
    )
    return await expert.search(request)


# 測試函數
async def test_web_search():
    """測試網路搜尋功能"""
    try:
        expert = WebSearchExpert()
        await expert.initialize()
        
        request = SearchRequest(
            query="台灣最新科技新聞",
            max_results=2,
            language="zh-TW"
        )
        
        response = await expert.search(request)
        print(f"搜尋結果: {response}")
        
        await expert.cleanup()
        
    except Exception as e:
        print(f"測試失敗: {e}")


if __name__ == "__main__":
    asyncio.run(test_web_search()) 