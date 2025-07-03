#!/usr/bin/env python3
"""
信心值控制器
用於評估 RAG 回應的信心值，並在信心值過低時自動切換到 OpenAI
"""

import os
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceController:
    """
    信心值控制器
    負責評估回應品質並管理備援機制
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.7,
                 openai_api_key: Optional[str] = None,
                 openai_model: str = "gpt-3.5-turbo",
                 enable_fallback: bool = True):
        """
        初始化信心值控制器
        
        Args:
            confidence_threshold: 信心值閾值，低於此值會觸發備援
            openai_api_key: OpenAI API 金鑰
            openai_model: OpenAI 模型名稱
            enable_fallback: 是否啟用備援機制
        """
        self.confidence_threshold = confidence_threshold
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_model = openai_model
        self.enable_fallback = enable_fallback
        
        # 統計資訊
        self.stats = {
            "total_queries": 0,
            "rag_responses": 0,
            "fallback_responses": 0,
            "average_confidence": 0.0,
            "low_confidence_count": 0
        }
    
    def calculate_confidence(self, 
                           rag_response: str, 
                           sources: list, 
                           query: str,
                           processing_time: float) -> float:
        """
        計算 RAG 回應的信心值
        
        Args:
            rag_response: RAG 系統的回應
            sources: 來源文件列表
            query: 原始查詢
            processing_time: 處理時間
            
        Returns:
            信心值 (0.0 - 1.0)
        """
        try:
            confidence = 0.0
            
            # 1. 回應長度評估 (20%)
            response_length_score = min(len(rag_response) / 100, 1.0) * 0.2
            
            # 2. 來源文件數量評估 (25%)
            source_count_score = min(len(sources) / 3, 1.0) * 0.25
            
            # 3. 回應相關性評估 (30%)
            relevance_score = self._calculate_relevance_score(query, rag_response) * 0.3
            
            # 4. 處理時間評估 (15%)
            time_score = max(0, 1 - (processing_time / 10)) * 0.15  # 10秒內為滿分
            
            # 5. 回應完整性評估 (10%)
            completeness_score = self._calculate_completeness_score(rag_response) * 0.1
            
            confidence = response_length_score + source_count_score + relevance_score + time_score + completeness_score
            
            # 確保信心值在 0-1 範圍內
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(f"信心值計算: {confidence:.3f} (長度:{response_length_score:.3f}, 來源:{source_count_score:.3f}, 相關性:{relevance_score:.3f}, 時間:{time_score:.3f}, 完整性:{completeness_score:.3f})")
            
            return confidence
            
        except Exception as e:
            logger.error(f"信心值計算失敗: {e}")
            return 0.5  # 預設中等信心值
    
    def _calculate_relevance_score(self, query: str, response: str) -> float:
        """
        計算查詢與回應的相關性分數
        
        Args:
            query: 原始查詢
            response: RAG 回應
            
        Returns:
            相關性分數 (0.0 - 1.0)
        """
        try:
            # 簡單的關鍵字匹配評估
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            
            if not query_words:
                return 0.5
            
            # 計算關鍵字匹配率
            matched_words = query_words.intersection(response_words)
            match_ratio = len(matched_words) / len(query_words)
            
            # 考慮回應長度
            length_factor = min(len(response) / 50, 1.0)  # 至少50字
            
            # 綜合分數
            relevance_score = (match_ratio * 0.7) + (length_factor * 0.3)
            
            return relevance_score
            
        except Exception as e:
            logger.error(f"相關性計算失敗: {e}")
            return 0.5
    
    def _calculate_completeness_score(self, response: str) -> float:
        """
        計算回應完整性分數
        
        Args:
            response: RAG 回應
            
        Returns:
            完整性分數 (0.0 - 1.0)
        """
        try:
            # 檢查回應是否包含完整的句子結構
            sentences = response.split('。')
            if len(sentences) < 2:
                return 0.3
            
            # 檢查是否有問答結構
            has_question = '?' in response or '？' in response
            has_answer = len(response) > 20
            
            # 檢查是否有具體資訊
            has_specific_info = any(word in response for word in ['是', '有', '可以', '建議', '推薦'])
            
            completeness = 0.0
            if has_answer:
                completeness += 0.4
            if has_specific_info:
                completeness += 0.3
            if len(sentences) >= 3:
                completeness += 0.3
            
            return completeness
            
        except Exception as e:
            logger.error(f"完整性計算失敗: {e}")
            return 0.5
    
    async def get_openai_fallback(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用 OpenAI 作為備援回應
        
        Args:
            query: 原始查詢
            context: 可選的上下文資訊
            
        Returns:
            OpenAI 回應結果
        """
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API 金鑰未設定，無法使用備援功能")
                return {
                    "success": False,
                    "error": "OpenAI API 金鑰未設定"
                }
            
            # 構建提示詞
            system_prompt = """你是一個專業的職涯諮詢助手，專門回答關於職涯規劃、工作技能、求職建議等問題。
請用繁體中文回答，提供實用且具體的建議。"""
            
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
                    "max_tokens": 1000
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
                            "confidence": 0.8,  # OpenAI 預設較高信心值
                            "method": "OpenAI Fallback",
                            "sources": [],
                            "used_llm": self.openai_model,
                            "fallback_used": True
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"OpenAI API 調用失敗: {response.status} - {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"OpenAI 備援失敗: {e}")
            return {
                "success": False,
                "error": f"OpenAI 備援失敗: {str(e)}"
            }
    
    async def process_query_with_confidence(self, 
                                          query: str, 
                                          rag_response: str, 
                                          sources: list,
                                          processing_time: float,
                                          context: Optional[str] = None) -> Dict[str, Any]:
        """
        處理查詢並評估信心值，必要時使用備援
        
        Args:
            query: 原始查詢
            rag_response: RAG 系統回應
            sources: 來源文件
            processing_time: 處理時間
            context: 可選上下文
            
        Returns:
            處理結果
        """
        try:
            self.stats["total_queries"] += 1
            
            # 計算信心值
            confidence = self.calculate_confidence(rag_response, sources, query, processing_time)
            
            # 更新統計
            self.stats["average_confidence"] = (
                (self.stats["average_confidence"] * (self.stats["total_queries"] - 1) + confidence) / 
                self.stats["total_queries"]
            )
            
            # 檢查是否需要備援
            if confidence < self.confidence_threshold and self.enable_fallback:
                logger.info(f"信心值過低 ({confidence:.3f} < {self.confidence_threshold})，啟用 OpenAI 備援")
                self.stats["low_confidence_count"] += 1
                
                # 使用 OpenAI 備援
                fallback_result = await self.get_openai_fallback(query, context)
                
                if fallback_result["success"]:
                    self.stats["fallback_responses"] += 1
                    return fallback_result
                else:
                    # 備援失敗，返回 RAG 結果但標記信心值低
                    logger.warning(f"備援失敗，返回 RAG 結果: {fallback_result['error']}")
                    self.stats["rag_responses"] += 1
                    return {
                        "success": True,
                        "response": rag_response,
                        "confidence": confidence,
                        "method": "RAG (Low Confidence)",
                        "sources": sources,
                        "used_llm": "RAG System",
                        "fallback_used": False,
                        "fallback_failed": True
                    }
            else:
                # 信心值足夠，返回 RAG 結果
                self.stats["rag_responses"] += 1
                return {
                    "success": True,
                    "response": rag_response,
                    "confidence": confidence,
                    "method": "RAG Pipeline",
                    "sources": sources,
                    "used_llm": "RAG System",
                    "fallback_used": False
                }
                
        except Exception as e:
            logger.error(f"信心值處理失敗: {e}")
            return {
                "success": False,
                "error": f"信心值處理失敗: {str(e)}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        return {
            **self.stats,
            "confidence_threshold": self.confidence_threshold,
            "enable_fallback": self.enable_fallback,
            "fallback_rate": (
                self.stats["fallback_responses"] / max(self.stats["total_queries"], 1)
            ),
            "low_confidence_rate": (
                self.stats["low_confidence_count"] / max(self.stats["total_queries"], 1)
            )
        }
    
    def update_confidence_threshold(self, new_threshold: float):
        """更新信心值閾值"""
        if 0.0 <= new_threshold <= 1.0:
            self.confidence_threshold = new_threshold
            logger.info(f"信心值閾值已更新為: {new_threshold}")
        else:
            logger.error(f"無效的信心值閾值: {new_threshold}")

# 全域信心值控制器實例
_confidence_controller = None

def get_confidence_controller() -> ConfidenceController:
    """獲取全域信心值控制器實例"""
    global _confidence_controller
    if _confidence_controller is None:
        _confidence_controller = ConfidenceController()
    return _confidence_controller 