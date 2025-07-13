#!/usr/bin/env python3
"""
LLM 整合服務

整合 LLM 服務來協助 Milvus 檢索：
- 查詢重寫和擴展
- 語意理解增強
- 智能標籤生成
- 檢索結果重排序

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置"""
    host: str = "localhost"
    port: int = 8003
    timeout: int = 30
    max_retries: int = 3
    model: str = "qwen3:8b"  # 預設使用 qwen3:8b
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMIntegrationService:
    """LLM 整合服務"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """獲取 HTTP 客戶端"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.config.timeout,
                limits=httpx.Limits(max_retries=self.config.max_retries)
            )
        return self.client
    
    async def health_check(self) -> bool:
        """檢查 LLM 服務健康狀態"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM 服務健康檢查失敗: {e}")
            return False
    
    async def generate_text(self, prompt: str, model: str = None) -> Optional[str]:
        """生成文字"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/generate",
                json={
                    "prompt": prompt,
                    "model": model or self.config.model,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"LLM 生成失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 生成錯誤: {e}")
            return None
    
    async def get_embedding(self, text: str, model: str = "bge-m3") -> Optional[List[float]]:
        """獲取向量嵌入"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/embed",
                json={
                    "text": text,
                    "model": model
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])
            else:
                logger.error(f"LLM 嵌入失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 嵌入錯誤: {e}")
            return None
    
    async def enhance_query(self, query: str, model: str = "qwen2.5-Taiwan") -> Dict[str, Any]:
        """增強查詢"""
        try:
            # 1. 查詢重寫
            rewrite_prompt = f"""
            請重寫以下查詢，使其更適合向量搜尋：
            原始查詢：{query}
            
            要求：
            1. 保持原始意圖
            2. 增加相關關鍵詞
            3. 使用更標準的表達方式
            4. 考慮同義詞和相關概念
            
            重寫後的查詢：
            """
            
            rewritten_query = await self.generate_text(rewrite_prompt, model)
            if not rewritten_query:
                rewritten_query = query
            
            # 2. 標籤提取
            tag_prompt = f"""
            請從以下查詢中提取相關標籤：
            查詢：{query}
            
            請提取以下類型的標籤：
            1. 主題標籤（如：商業、科技、健康等）
            2. 情感標籤（如：正面、負面、中性等）
            3. 時間標籤（如：最新、歷史、趨勢等）
            4. 地域標籤（如：台灣、全球、亞洲等）
            
            請以 JSON 格式返回：
            {{
                "themes": ["標籤1", "標籤2"],
                "sentiment": ["標籤1", "標籤2"],
                "time": ["標籤1", "標籤2"],
                "location": ["標籤1", "標籤2"]
            }}
            """
            
            tag_response = await self.generate_text(tag_prompt, model)
            tags = self._parse_tags(tag_response or "")
            
            # 3. 查詢擴展
            expansion_prompt = f"""
            請為以下查詢生成相關的擴展查詢：
            原始查詢：{query}
            
            請生成 3-5 個相關的查詢變體，考慮：
            1. 同義詞替換
            2. 相關概念
            3. 不同表達方式
            
            請以 JSON 格式返回：
            {{
                "expansions": ["擴展查詢1", "擴展查詢2", "擴展查詢3"]
            }}
            """
            
            expansion_response = await self.generate_text(expansion_prompt, model)
            expansions = self._parse_expansions(expansion_response or "")
            
            return {
                "original_query": query,
                "rewritten_query": rewritten_query,
                "tags": tags,
                "expansions": expansions,
                "enhanced_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"查詢增強失敗: {e}")
            return {
                "original_query": query,
                "rewritten_query": query,
                "tags": {},
                "expansions": [],
                "enhanced_at": datetime.now().isoformat()
            }
    
    async def rerank_results(self, query: str, results: List[Dict[str, Any]], model: str = "qwen3:8b") -> List[Dict[str, Any]]:
        """重新排序檢索結果"""
        try:
            if not results:
                return results
            
            # 創建重排序提示
            rerank_prompt = f"""
            請根據查詢的相關性對以下檢索結果進行重新排序：
            
            查詢：{query}
            
            檢索結果：
            {self._format_results_for_rerank(results)}
            
            請根據相關性評分（0-10）重新排序，並返回 JSON 格式：
            {{
                "ranked_results": [
                    {{"index": 0, "score": 8.5, "reason": "最相關的原因"}},
                    {{"index": 1, "score": 7.2, "reason": "相關的原因"}}
                ]
            }}
            """
            
            rerank_response = await self.generate_text(rerank_prompt, model)
            if not rerank_response:
                return results
            
            # 解析重排序結果
            ranked_indices = self._parse_rerank_response(rerank_response)
            if not ranked_indices:
                return results
            
            # 重新排序
            reranked_results = []
            for rank_item in ranked_indices:
                index = rank_item.get("index", 0)
                if 0 <= index < len(results):
                    result = results[index].copy()
                    result["llm_score"] = rank_item.get("score", 0.0)
                    result["llm_reason"] = rank_item.get("reason", "")
                    reranked_results.append(result)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"結果重排序失敗: {e}")
            return results
    
    def _parse_tags(self, tag_response: str) -> Dict[str, List[str]]:
        """解析標籤回應"""
        try:
            import json
            # 嘗試提取 JSON 部分
            start = tag_response.find('{')
            end = tag_response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = tag_response[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"標籤解析失敗: {e}")
        
        return {
            "themes": [],
            "sentiment": [],
            "time": [],
            "location": []
        }
    
    def _parse_expansions(self, expansion_response: str) -> List[str]:
        """解析擴展查詢回應"""
        try:
            import json
            # 嘗試提取 JSON 部分
            start = expansion_response.find('{')
            end = expansion_response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = expansion_response[start:end]
                data = json.loads(json_str)
                return data.get("expansions", [])
        except Exception as e:
            logger.warning(f"擴展查詢解析失敗: {e}")
        
        return []
    
    def _format_results_for_rerank(self, results: List[Dict[str, Any]]) -> str:
        """格式化結果用於重排序"""
        formatted = []
        for i, result in enumerate(results):
            content = result.get("content", result.get("chunk_text", ""))
            metadata = result.get("metadata", {})
            title = metadata.get("title", f"結果 {i+1}")
            formatted.append(f"{i+1}. {title}: {content[:200]}...")
        
        return "\n".join(formatted)
    
    def _parse_rerank_response(self, rerank_response: str) -> List[Dict[str, Any]]:
        """解析重排序回應"""
        try:
            import json
            # 嘗試提取 JSON 部分
            start = rerank_response.find('{')
            end = rerank_response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = rerank_response[start:end]
                data = json.loads(json_str)
                return data.get("ranked_results", [])
        except Exception as e:
            logger.warning(f"重排序回應解析失敗: {e}")
        
        return []
    
    async def close(self):
        """關閉客戶端"""
        if self.client:
            await self.client.aclose()
            self.client = None


# 創建全局實例
llm_integration = LLMIntegrationService() 