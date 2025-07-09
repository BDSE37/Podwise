#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 整合核心模組
統一所有核心功能，避免重複實現

功能包括：
- 統一數據模型
- 基礎代理類別
- 信心值控制
- 查詢處理
- 回應生成

作者: Podwise Team
版本: 3.0.0
"""

import os
import json
import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 統一數據模型 ====================

@dataclass
class SearchResult:
    """統一搜尋結果數據類別"""
    id: str
    title: str
    content: str
    score: float
    category: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    document_id: Optional[str] = None

    def __post_init__(self):
        if self.document_id is None:
            self.document_id = self.id

@dataclass
class QueryContext:
    """查詢上下文"""
    original_query: str
    rewritten_query: str
    intent: str
    entities: List[str]
    domain: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RAGResponse:
    """RAG 回應"""
    content: str
    confidence: float
    sources: List[str]
    processing_time: float
    level_used: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResponse:
    """代理回應統一格式"""
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    agent_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")

@dataclass
class UserQuery:
    """用戶查詢數據類別"""
    query: str
    user_id: str
    category: Optional[str] = None
    context: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.query.strip():
            raise ValueError("查詢內容不能為空")
        if not self.user_id.strip():
            raise ValueError("用戶 ID 不能為空")

# ==================== 統一信心值控制器 ====================

class UnifiedConfidenceController:
    """統一信心值控制器"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.stats = {
            "total_calculations": 0,
            "average_confidence": 0.0,
            "low_confidence_count": 0
        }
    
    def calculate_confidence(self, 
                           response: str, 
                           sources: Optional[List[str]] = None,
                           query: Optional[str] = None,
                           processing_time: Optional[float] = None,
                           context: Optional[str] = None,
                           additional_factors: Optional[Dict[str, float]] = None) -> float:
        """
        統一計算信心值
        
        Args:
            response: 回應內容
            sources: 來源文件列表
            query: 原始查詢
            processing_time: 處理時間
            context: 上下文資訊
            additional_factors: 額外因素
            
        Returns:
            信心值 (0.0 - 1.0)
        """
        try:
            confidence = 0.0
            
            # 1. 回應長度和完整性評估 (30%)
            if response and len(response.strip()) > 0:
                length_score = min(len(response) / 100, 1.0) * 0.3
                confidence += length_score
            
            # 2. 來源文件數量評估 (20%)
            if sources:
                source_score = min(len(sources) / 3, 1.0) * 0.2
                confidence += source_score
            
            # 3. 查詢相關性評估 (25%)
            if query and response:
                relevance_score = self._calculate_relevance(query, response) * 0.25
                confidence += relevance_score
            
            # 4. 處理時間評估 (15%)
            if processing_time:
                time_score = max(0, 1 - (processing_time / 10)) * 0.15
                confidence += time_score
            
            # 5. 上下文相關性 (10%)
            if context and response:
                context_score = self._calculate_context_relevance(context, response) * 0.1
                confidence += context_score
            
            # 6. 額外因素
            if additional_factors:
                for factor, weight in additional_factors.items():
                    confidence += weight
            
            # 確保在 0-1 範圍內
            confidence = max(0.0, min(1.0, confidence))
            
            # 更新統計
            self._update_stats(confidence)
            
            return confidence
            
        except Exception as e:
            logger.error(f"信心值計算失敗: {e}")
            return 0.5
    
    def _calculate_relevance(self, query: str, response: str) -> float:
        """計算查詢與回應的相關性"""
        try:
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            
            if not query_words:
                return 0.5
            
            matched_words = query_words.intersection(response_words)
            match_ratio = len(matched_words) / len(query_words)
            
            return match_ratio
            
        except Exception:
            return 0.5
    
    def _calculate_context_relevance(self, context: str, response: str) -> float:
        """計算上下文相關性"""
        try:
            context_words = set(context.lower().split())
            response_words = set(response.lower().split())
            
            if not context_words:
                return 0.5
            
            overlap = len(context_words.intersection(response_words))
            return overlap / len(context_words)
            
        except Exception:
            return 0.5
    
    def _update_stats(self, confidence: float):
        """更新統計信息"""
        self.stats["total_calculations"] += 1
        
        # 更新平均信心值
        total = self.stats["total_calculations"]
        current_avg = self.stats["average_confidence"]
        self.stats["average_confidence"] = (current_avg * (total - 1) + confidence) / total
        
        # 更新低信心值計數
        if confidence < self.confidence_threshold:
            self.stats["low_confidence_count"] += 1
    
    def should_use_fallback(self, confidence: float) -> bool:
        """判斷是否需要使用備援"""
        return confidence < self.confidence_threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            "confidence_threshold": self.confidence_threshold,
            "low_confidence_rate": (
                self.stats["low_confidence_count"] / max(self.stats["total_calculations"], 1)
            )
        }

# ==================== 基礎代理類別 ====================

class BaseAgent(ABC):
    """統一基礎代理類別"""
    
    def __init__(self, agent_name: str, role: str, config: Dict[str, Any]):
        self.agent_name = agent_name
        self.role = role
        self.config = config
        self.confidence_controller = UnifiedConfidenceController(
            config.get('confidence_threshold', 0.7)
        )
        
        # 效能指標
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "last_used": None
        }
        
        logger.info(f"初始化代理人: {agent_name} ({role})")
    
    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        """處理輸入數據（抽象方法）"""
        raise NotImplementedError("子類別必須實作 process 方法")
    
    async def execute_with_monitoring(self, input_data: Any) -> AgentResponse:
        """帶監控的執行方法"""
        start_time = time.time()
        
        try:
            # 驗證輸入
            if not self.validate_input(input_data):
                raise ValueError("輸入數據驗證失敗")
            
            # 執行處理
            response = await self.process(input_data)
            
            # 更新成功指標
            processing_time = time.time() - start_time
            self._update_success_metrics(response.confidence, processing_time)
            
            # 更新回應資訊
            response.metadata.update({
                "agent_name": self.agent_name,
                "agent_role": self.role,
                "processing_time": processing_time
            })
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_failure_metrics(processing_time)
            
            logger.error(f"代理人 {self.agent_name} 處理失敗: {str(e)}")
            
            return AgentResponse(
                content=f"處理失敗: {str(e)}",
                confidence=0.0,
                reasoning=f"代理人 {self.agent_name} 執行時發生錯誤",
                metadata={"error": str(e), "agent_name": self.agent_name},
                processing_time=processing_time,
                agent_name=self.agent_name
            )
    
    def validate_input(self, input_data: Any) -> bool:
        """驗證輸入數據"""
        return input_data is not None
    
    def _update_success_metrics(self, confidence: float, processing_time: float):
        """更新成功指標"""
        self.metrics["total_calls"] += 1
        self.metrics["successful_calls"] += 1
        self.metrics["last_used"] = datetime.now().isoformat()
        
        # 更新平均值
        total = self.metrics["total_calls"]
        self.metrics["average_processing_time"] = (
            (self.metrics["average_processing_time"] * (total - 1) + processing_time) / total
        )
        self.metrics["average_confidence"] = (
            (self.metrics["average_confidence"] * (total - 1) + confidence) / total
        )
    
    def _update_failure_metrics(self, processing_time: float):
        """更新失敗指標"""
        self.metrics["total_calls"] += 1
        self.metrics["failed_calls"] += 1
        self.metrics["last_used"] = datetime.now().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取代理人指標"""
        success_rate = 0.0
        if self.metrics["total_calls"] > 0:
            success_rate = self.metrics["successful_calls"] / self.metrics["total_calls"]
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "agent_name": self.agent_name,
            "agent_role": self.role
        }

# ==================== 統一查詢處理器 ====================

# 導入 Apple Podcast 排名系統
from .apple_podcast_ranking import (
    ApplePodcastRankingSystem,
    ApplePodcastRating,
    RankingScore,
    get_apple_podcast_ranking
)

# 導入 Langfuse 追蹤
from .langfuse_tracking import langfuse_trace

class UnifiedQueryProcessor:
    """統一查詢處理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 初始化 Apple Podcast 排名系統
        self.apple_ranking = get_apple_podcast_ranking()
    
    @langfuse_trace("query")
    async def process_query(self, user_query: UserQuery) -> RAGResponse:
        """
        處理用戶查詢（整合 Apple Podcast 優先推薦）
        
        Args:
            user_query: 用戶查詢
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        
        try:
            # 1. 查詢分析
            query_context = await self._analyze_query(user_query)
            
            # 2. 內容檢索
            search_results = await self._retrieve_content(query_context)
            
            # 3. 應用 Apple Podcast 優先推薦
            enhanced_results = await self._apply_apple_podcast_ranking(search_results, user_query)
            
            # 4. 生成回應
            response_content = await self._generate_response(query_context, enhanced_results)
            
            # 5. 計算處理時間和信心度
            processing_time = (datetime.now() - start_time).total_seconds()
            confidence = self._calculate_response_confidence(response_content, enhanced_results)
            
            return RAGResponse(
                content=response_content,
                confidence=confidence,
                sources=[result.id for result in enhanced_results],
                processing_time=processing_time,
                level_used="enhanced_with_apple_ranking",
                metadata={
                    "apple_ranking_applied": True,
                    "original_results_count": len(search_results),
                    "enhanced_results_count": len(enhanced_results),
                    "user_id": user_query.user_id,
                    "category": user_query.category
                }
            )
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return RAGResponse(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=[],
                processing_time=processing_time,
                level_used="error",
                metadata={"error": str(e)}
            )
    
    async def _analyze_query(self, user_query: UserQuery) -> QueryContext:
        """分析查詢"""
        # 簡化的查詢分析
        return QueryContext(
            original_query=user_query.query,
            rewritten_query=user_query.query,  # 簡化版本
            intent=self._detect_intent(user_query.query),
            entities=self._extract_entities(user_query.query),
            domain=user_query.category or "general",
            confidence=0.8,
            metadata={"user_id": user_query.user_id}
        )
    
    async def _retrieve_content(self, query_context: QueryContext) -> List[SearchResult]:
        """檢索內容"""
        # 模擬檢索結果
        return [
            SearchResult(
                id="result_1",
                title="相關內容 1",
                content="這是與查詢相關的內容...",
                score=0.9,
                category=query_context.domain,
                tags=query_context.entities,
                source="unified_retriever"
            )
        ]
    
    async def _generate_response(self, query_context: QueryContext, search_results: List[SearchResult]) -> str:
        """生成回應"""
        if not search_results:
            return "抱歉，沒有找到相關的內容。"
        
        # 簡化的回應生成
        response = f"根據您的查詢「{query_context.original_query}」，我找到了以下相關資訊：\n\n"
        
        for i, result in enumerate(search_results[:3], 1):
            response += f"{i}. {result.title}\n{result.content[:100]}...\n\n"
        
        return response
    
    def _detect_intent(self, query: str) -> str:
        """檢測意圖"""
        query_lower = query.lower()
        if any(word in query_lower for word in ["推薦", "建議", "介紹"]):
            return "recommendation"
        elif any(word in query_lower for word in ["分析", "比較", "差異"]):
            return "analysis"
        else:
            return "general"
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取實體"""
        entities = []
        query_lower = query.lower()
        
        if "播客" in query_lower or "podcast" in query_lower:
            entities.append("podcast")
        if "商業" in query_lower or "投資" in query_lower:
            entities.append("business")
        if "教育" in query_lower or "學習" in query_lower:
            entities.append("education")
            
        return entities

    async def _apply_apple_podcast_ranking(self, 
                                         search_results: List[SearchResult], 
                                         user_query: UserQuery) -> List[SearchResult]:
        """
        應用 Apple Podcast 優先推薦
        
        Args:
            search_results: 原始搜尋結果
            user_query: 用戶查詢
            
        Returns:
            List[SearchResult]: 增強後的搜尋結果
        """
        try:
            # 1. 獲取 Apple Podcast 排名數據
            apple_podcast_data = await self._get_apple_podcast_data(search_results)
            
            if not apple_podcast_data:
                logger.warning("無法獲取 Apple Podcast 排名數據，使用原始結果")
                return search_results
            
            # 2. 計算 Apple Podcast 排名分數
            ranking_scores = self.apple_ranking.rank_podcasts(apple_podcast_data)
            
            # 3. 創建 RSS ID 到排名分數的映射
            ranking_map = {score.rss_id: score for score in ranking_scores}
            
            # 4. 增強搜尋結果
            enhanced_results = []
            for result in search_results:
                enhanced_result = result
                
                # 查找對應的 Apple Podcast 排名
                apple_score = ranking_map.get(result.id)
                if apple_score:
                    # 計算混合分數（向量搜尋分數 + Apple 排名分數）
                    vector_score = result.score
                    apple_ranking_score = apple_score.total_score
                    
                    # 權重配置：Apple 排名 60%，向量搜尋 40%
                    hybrid_score = (
                        vector_score * 0.4 + 
                        apple_ranking_score * 0.6
                    )
                    
                    # 更新結果分數和元數據
                    enhanced_result.score = hybrid_score
                    enhanced_result.metadata.update({
                        "apple_ranking_score": apple_ranking_score,
                        "vector_score": vector_score,
                        "hybrid_score": hybrid_score,
                        "apple_rating": apple_score.apple_rating_score,
                        "comment_score": apple_score.comment_score,
                        "click_rate_score": apple_score.click_rate_score,
                        "review_count_score": apple_score.review_count_score
                    })
                
                enhanced_results.append(enhanced_result)
            
            # 5. 按混合分數重新排序
            enhanced_results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Apple Podcast 優先推薦完成: {len(enhanced_results)} 個結果")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Apple Podcast 優先推薦失敗: {e}")
            return search_results
    
    async def _get_apple_podcast_data(self, search_results: List[SearchResult]) -> List[ApplePodcastRating]:
        """
        獲取 Apple Podcast 排名數據
        
        Args:
            search_results: 搜尋結果
            
        Returns:
            List[ApplePodcastRating]: Apple Podcast 排名數據
        """
        try:
            # 這裡應該從資料庫或 API 獲取實際的 Apple Podcast 數據
            # 目前使用模擬數據進行演示
            apple_podcast_data = []
            
            for result in search_results:
                # 根據 RSS ID 查找對應的 Apple Podcast 數據
                # 實際應用中應該查詢資料庫
                apple_data = self._get_sample_apple_data(result.id)
                if apple_data:
                    apple_podcast_data.append(apple_data)
            
            return apple_podcast_data
            
        except Exception as e:
            logger.error(f"獲取 Apple Podcast 數據失敗: {e}")
            return []
    
    def _get_sample_apple_data(self, rss_id: str) -> Optional[ApplePodcastRating]:
        """
        獲取範例 Apple Podcast 數據（實際應用中應從資料庫獲取）
        
        Args:
            rss_id: RSS ID
            
        Returns:
            Optional[ApplePodcastRating]: Apple Podcast 數據
        """
        # 模擬數據庫查詢
        sample_data = {
            "1234567890": ApplePodcastRating(
                rss_id="1234567890",
                title="投資理財大師",
                apple_rating=4.8,
                apple_review_count=150,
                user_click_rate=0.85,
                comment_sentiment_score=0.75,
                total_comments=45,
                positive_comments=35,
                negative_comments=5,
                neutral_comments=5
            ),
            "2345678901": ApplePodcastRating(
                rss_id="2345678901",
                title="科技趨勢分析",
                apple_rating=4.5,
                apple_review_count=80,
                user_click_rate=0.72,
                comment_sentiment_score=0.60,
                total_comments=30,
                positive_comments=22,
                negative_comments=3,
                neutral_comments=5
            ),
            "3456789012": ApplePodcastRating(
                rss_id="3456789012",
                title="職涯發展指南",
                apple_rating=4.2,
                apple_review_count=45,
                user_click_rate=0.65,
                comment_sentiment_score=0.45,
                total_comments=20,
                positive_comments=12,
                negative_comments=4,
                neutral_comments=4
            )
        }
        
        return sample_data.get(rss_id)
    
    def _calculate_response_confidence(self, response: str, results: List[SearchResult]) -> float:
        """
        計算回應信心度（整合 Apple Podcast 排名）
        
        Args:
            response: 回應內容
            results: 搜尋結果
            
        Returns:
            float: 信心度
        """
        if not results:
            return 0.0
        
        # 獲取最高分數作為基礎信心度
        max_score = max([result.score for result in results])
        
        # 檢查是否有 Apple Podcast 排名數據
        has_apple_ranking = any(
            "apple_ranking_score" in result.metadata 
            for result in results
        )
        
        # 如果有 Apple Podcast 排名，提升信心度
        if has_apple_ranking:
            confidence_boost = 0.1
        else:
            confidence_boost = 0.0
        
        return min(1.0, max_score + confidence_boost)

# ==================== 全局實例管理 ====================

# 全局實例
_confidence_controller = None
_query_processor = None

def get_confidence_controller() -> UnifiedConfidenceController:
    """獲取全局信心值控制器"""
    global _confidence_controller
    if _confidence_controller is None:
        _confidence_controller = UnifiedConfidenceController()
    return _confidence_controller

def get_query_processor(config: Optional[Dict[str, Any]] = None) -> UnifiedQueryProcessor:
    """獲取全局查詢處理器"""
    global _query_processor
    if _query_processor is None:
        _query_processor = UnifiedQueryProcessor(config or {})
    return _query_processor

# ==================== 工廠函數 ====================

def create_agent_response(content: str, confidence: float, reasoning: str, 
                         agent_name: str = "", **kwargs) -> AgentResponse:
    """創建代理回應的工廠函數"""
    return AgentResponse(
        content=content,
        confidence=confidence,
        reasoning=reasoning,
        agent_name=agent_name,
        metadata=kwargs.get('metadata', {}),
        processing_time=kwargs.get('processing_time', 0.0)
    )

def create_search_result(id: str, title: str, content: str, score: float,
                        category: str, **kwargs) -> SearchResult:
    """創建搜尋結果的工廠函數"""
    return SearchResult(
        id=id,
        title=title,
        content=content,
        score=score,
        category=category,
        tags=kwargs.get('tags', []),
        metadata=kwargs.get('metadata', {}),
        source=kwargs.get('source', "")
    )

# ==================== 導出接口 ====================

__all__ = [
    # 數據模型
    'SearchResult', 'QueryContext', 'RAGResponse', 'AgentResponse', 'UserQuery',
    # 核心類別
    'UnifiedConfidenceController', 'BaseAgent', 'UnifiedQueryProcessor',
    # 全局實例
    'get_confidence_controller', 'get_query_processor',
    # 工廠函數
    'create_agent_response', 'create_search_result'
] 