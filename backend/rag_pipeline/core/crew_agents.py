#!/usr/bin/env python3
"""
三層代理人架構模組

此模組實現三層 CrewAI 架構，包含領導者層、類別專家層和功能專家層，
提供智能的查詢處理和決策制定功能。

架構層次：
- 第一層：領導者層 (Leader Layer) - 協調和決策
- 第二層：類別專家層 (Category Expert Layer) - 商業/教育專家
- 第三層：功能專家層 (Functional Expert Layer) - 專業功能處理

作者: Podwise Team
版本: 2.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentResponse:
    """
    代理人回應數據類別
    
    此類別封裝了代理人的處理結果，包含內容、信心值、
    推理說明和元數據。
    
    Attributes:
        content: 回應內容
        confidence: 信心值 (0.0-1.0)
        reasoning: 推理說明
        metadata: 元數據字典
        processing_time: 處理時間
    """
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")
        
        if self.processing_time < 0:
            raise ValueError("處理時間不能為負數")


@dataclass(frozen=True)
class UserQuery:
    """
    用戶查詢數據類別
    
    此類別封裝了用戶查詢的完整資訊，包含查詢內容、
    用戶 ID 和上下文資訊。
    
    Attributes:
        query: 查詢內容
        user_id: 用戶 ID
        category: 預分類類別
        context: 上下文資訊
    """
    query: str
    user_id: str
    category: Optional[str] = None
    context: Optional[str] = None
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not self.query.strip():
            raise ValueError("查詢內容不能為空")
        
        if not self.user_id.strip():
            raise ValueError("用戶 ID 不能為空")


class BaseAgent(ABC):
    """
    代理人基礎抽象類別
    
    此類別定義了所有代理人的基本介面和共同功能，
    包括信心值計算和基本配置管理。
    """
    
    def __init__(self, name: str, role: str, config: Dict[str, Any]) -> None:
        """
        初始化基礎代理人
        
        Args:
            name: 代理人名稱
            role: 代理人角色
            config: 配置字典
        """
        self.name = name
        self.role = role
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.max_processing_time = config.get('max_processing_time', 30.0)
    
    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        """
        處理輸入數據
        
        Args:
            input_data: 輸入數據
            
        Returns:
            AgentResponse: 處理結果
        """
        raise NotImplementedError("子類別必須實作 process 方法")
    
    def calculate_confidence(self, response: str, context: str) -> float:
        """
        計算信心值
        
        Args:
            response: 回應內容
            context: 上下文資訊
            
        Returns:
            float: 信心值 (0.0-1.0)
        """
        confidence = 0.8  # 基礎信心值
        
        # 根據回應長度調整
        if len(response) > 100:
            confidence += 0.1
        
        # 根據關鍵詞匹配調整
        if any(keyword in response.lower() for keyword in ['podcast', '推薦', '建議']):
            confidence += 0.1
        
        # 根據上下文相關性調整
        if context and any(word in response.lower() for word in context.lower().split()):
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據
        
        Args:
            input_data: 輸入數據
            
        Returns:
            bool: 驗證結果
        """
        return input_data is not None


# ==================== 第三層：功能專家層 ====================

class RAGExpertAgent(BaseAgent):
    """
    RAG 檢索專家代理人
    
    此代理人負責語意檢索和向量搜尋，提供最相關的
    內容檢索功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 RAG 專家代理人"""
        super().__init__("RAG Expert", "語意檢索和向量搜尋專家", config)
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理 RAG 檢索請求
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 檢索結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 執行語意檢索
        search_results = await self._semantic_search(input_data.query)
        
        # 執行向量搜尋
        vector_results = await self._vector_search(input_data.query)
        
        # 合併結果
        combined_results = self._merge_results(search_results, vector_results)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            content=f"找到 {len(combined_results)} 個相關 Podcast",
            confidence=0.85,
            reasoning="結合語意檢索和向量搜尋，提供最相關的結果",
            metadata={"results": combined_results, "search_method": "hybrid"},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"RAG 專家處理失敗: {str(e)}")
            return AgentResponse(
                content="檢索過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """執行語意檢索"""
        # 實作語意檢索邏輯
        return [{"title": "語意檢索結果", "score": 0.9}]
    
    async def _vector_search(self, query: str) -> List[Dict[str, Any]]:
        """執行向量搜尋"""
        # 實作向量搜尋邏輯
        return [{"title": "向量搜尋結果", "score": 0.8}]
    
    def _merge_results(self, semantic: List, vector: List) -> List[Dict[str, Any]]:
        """合併搜尋結果"""
        return semantic + vector


class SummaryExpertAgent(BaseAgent):
    """
    摘要生成專家代理人
    
    此代理人負責內容摘要生成，提供精準的內容分析
    和摘要功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化摘要專家代理人"""
        super().__init__("Summary Expert", "內容摘要生成專家", config)
    
    async def process(self, input_data: List[Dict[str, Any]]) -> AgentResponse:
        """
        處理摘要生成請求
        
        Args:
            input_data: 內容列表
            
        Returns:
            AgentResponse: 摘要結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 生成內容摘要
        summary = await self._generate_summary(input_data)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            content=summary,
            confidence=0.9,
            reasoning="基於內容分析生成精準摘要",
            metadata={"summary_type": "content_analysis"},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"摘要專家處理失敗: {str(e)}")
            return AgentResponse(
                content="摘要生成過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _generate_summary(self, content: List[Dict[str, Any]]) -> str:
        """生成摘要"""
        return "基於內容分析生成的 Podcast 摘要"


class RatingExpertAgent(BaseAgent):
    """
    評分專家代理人
    
    此代理人負責質量評估和評分，提供多維度的
    內容質量評估功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化評分專家代理人"""
        super().__init__("Rating Expert", "質量評估和評分專家", config)
    
    async def process(self, input_data: List[Dict[str, Any]]) -> AgentResponse:
        """
        處理評分請求
        
        Args:
            input_data: 內容列表
            
        Returns:
            AgentResponse: 評分結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 評估內容質量
        ratings = await self._evaluate_quality(input_data)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            content=f"評估完成，平均評分: {sum(ratings)/len(ratings):.2f}",
            confidence=0.8,
            reasoning="基於多維度指標進行質量評估",
            metadata={"ratings": ratings, "evaluation_criteria": ["relevance", "quality", "popularity"]},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"評分專家處理失敗: {str(e)}")
            return AgentResponse(
                content="評分過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _evaluate_quality(self, content: List[Dict[str, Any]]) -> List[float]:
        """評估內容質量"""
        return [0.8, 0.9, 0.7]  # 示例評分


class TTSExpertAgent(BaseAgent):
    """
    TTS 專家代理人
    
    此代理人負責語音合成，提供高品質的語音
    生成功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 TTS 專家代理人"""
        super().__init__("TTS Expert", "語音合成專家", config)
    
    async def process(self, input_data: str) -> AgentResponse:
        """
        處理語音合成請求
        
        Args:
            input_data: 文本內容
            
        Returns:
            AgentResponse: 語音合成結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 生成語音
        audio_url = await self._generate_speech(input_data)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            content="語音合成完成",
            confidence=0.95,
            reasoning="使用 Edge TW 語音模型生成自然語音",
            metadata={"audio_url": audio_url, "voice_model": "edge_tw"},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"TTS 專家處理失敗: {str(e)}")
            return AgentResponse(
                content="語音合成過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _generate_speech(self, text: str) -> str:
        """生成語音"""
        return "generated_audio_url.mp3"


class UserManagerAgent(BaseAgent):
    """
    用戶管理專家代理人
    
    此代理人負責用戶 ID 管理和記錄追蹤，提供
    完整的用戶行為分析功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化用戶管理專家代理人"""
        super().__init__("User Manager", "用戶 ID 管理和記錄追蹤專家", config)
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理用戶管理請求
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 用戶管理結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 驗證用戶 ID
        is_valid = await self._validate_user_id(input_data.user_id)
        
        # 記錄用戶行為
        await self._log_user_behavior(input_data)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
                content=f"用戶 {input_data.user_id} 驗證{'成功' if is_valid else '失敗'}",
                confidence=0.9 if is_valid else 0.3,
                reasoning="完成用戶 ID 驗證和行為記錄",
                metadata={"user_id": input_data.user_id, "is_valid": is_valid},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"用戶管理專家處理失敗: {str(e)}")
            return AgentResponse(
                content="用戶管理過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _validate_user_id(self, user_id: str) -> bool:
        """驗證用戶 ID"""
        return len(user_id) >= 3 and user_id.isalnum()
    
    async def _log_user_behavior(self, query: UserQuery) -> None:
        """記錄用戶行為"""
        logger.info(f"記錄用戶行為: {query.user_id} - {query.query}")


# ==================== 第二層：類別專家層 ====================

class BusinessExpertAgent(BaseAgent):
    """
    商業專家代理人
    
    此代理人專門處理商業類別的查詢，提供專業的
    商業分析和推薦功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化商業專家代理人"""
        super().__init__("Business Expert", "商業類別專家", config)
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理商業類別查詢
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 商業分析結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 分析商業相關性
            relevance_score = self._analyze_business_relevance(input_data.query)
        
            # 生成商業推薦
            recommendations = await self._generate_business_recommendations(input_data.query)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
                content=f"商業分析完成，相關性: {relevance_score:.2f}",
                confidence=relevance_score,
                reasoning="基於商業關鍵詞和市場趨勢進行分析",
                metadata={"recommendations": recommendations, "relevance_score": relevance_score},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"商業專家處理失敗: {str(e)}")
            return AgentResponse(
                content="商業分析過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _analyze_business_relevance(self, query: str) -> float:
        """分析商業相關性"""
        business_keywords = ["股票", "投資", "理財", "財經", "市場", "經濟"]
        query_lower = query.lower()
        
        relevance = 0.0
        for keyword in business_keywords:
            if keyword in query_lower:
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    async def _generate_business_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """生成商業推薦"""
        return [{"title": "商業推薦", "category": "商業", "confidence": 0.8}]


class EducationExpertAgent(BaseAgent):
    """
    教育專家代理人
    
    此代理人專門處理教育類別的查詢，提供專業的
    教育分析和推薦功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化教育專家代理人"""
        super().__init__("Education Expert", "教育類別專家", config)
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理教育類別查詢
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 教育分析結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
        # 分析教育相關性
            relevance_score = self._analyze_education_relevance(input_data.query)
        
            # 生成教育推薦
            recommendations = await self._generate_education_recommendations(input_data.query)
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
                content=f"教育分析完成，相關性: {relevance_score:.2f}",
                confidence=relevance_score,
                reasoning="基於教育關鍵詞和學習需求進行分析",
                metadata={"recommendations": recommendations, "relevance_score": relevance_score},
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"教育專家處理失敗: {str(e)}")
            return AgentResponse(
                content="教育分析過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _analyze_education_relevance(self, query: str) -> float:
        """分析教育相關性"""
        education_keywords = ["學習", "技能", "成長", "職涯", "發展", "教育"]
        query_lower = query.lower()
        
        relevance = 0.0
        for keyword in education_keywords:
            if keyword in query_lower:
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    async def _generate_education_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """生成教育推薦"""
        return [{"title": "教育推薦", "category": "教育", "confidence": 0.8}]


# ==================== 第一層：領導者層 ====================

class LeaderAgent(BaseAgent):
    """
    領導者代理人
    
    此代理人作為三層架構的協調者，負責整合各層專家的
    結果並做出最終決策。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化領導者代理人"""
        super().__init__("Leader", "三層架構協調者", config)
        
        # 初始化下層專家
        self.rag_expert = RAGExpertAgent(config.get('rag_expert', {}))
        self.summary_expert = SummaryExpertAgent(config.get('summary_expert', {}))
        self.rating_expert = RatingExpertAgent(config.get('rating_expert', {}))
        self.tts_expert = TTSExpertAgent(config.get('tts_expert', {}))
        self.user_manager = UserManagerAgent(config.get('user_manager', {}))
        
        # 類別專家
        self.business_expert = BusinessExpertAgent(config.get('business_expert', {}))
        self.education_expert = EducationExpertAgent(config.get('education_expert', {}))
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理查詢並協調各層專家
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 最終決策結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 1. 用戶管理層
            user_result = await self.user_manager.process(input_data)
        
            # 2. RAG 檢索層
            rag_result = await self.rag_expert.process(input_data)
        
            # 3. 類別專家層
            if input_data.category == "商業":
                category_result = await self.business_expert.process(input_data)
            elif input_data.category == "教育":
                category_result = await self.education_expert.process(input_data)
            else:
                # 雙類別情況，需要進一步分析
                category_result = await self._analyze_dual_category(input_data)
        
            # 4. 功能專家層
            summary_result = await self.summary_expert.process(rag_result.metadata.get("results", []))
            rating_result = await self.rating_expert.process(rag_result.metadata.get("results", []))
        
            # 5. 最終決策
        final_response = await self._make_final_decision(
                input_data, rag_result, category_result, summary_result, rating_result
        )
        
        processing_time = time.time() - start_time
        
        return AgentResponse(
            content=final_response,
                confidence=min(rag_result.confidence, category_result.confidence),
                reasoning="基於三層專家協作的最終決策",
            metadata={
                    "user_result": user_result.metadata,
                    "rag_result": rag_result.metadata,
                    "category_result": category_result.metadata,
                    "summary_result": summary_result.metadata,
                    "rating_result": rating_result.metadata
            },
            processing_time=processing_time
        )
            
        except Exception as e:
            logger.error(f"領導者代理人處理失敗: {str(e)}")
            return AgentResponse(
                content="處理過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _analyze_dual_category(self, input_data: UserQuery) -> AgentResponse:
        """分析雙類別情況"""
        business_result = await self.business_expert.process(input_data)
        education_result = await self.education_expert.process(input_data)
        
        # 選擇信心值較高的結果
        if business_result.confidence > education_result.confidence:
            return business_result
        else:
            return education_result
    
    async def _make_final_decision(self, query: UserQuery, rag_result: AgentResponse, 
                                 category_result: AgentResponse, summary_result: AgentResponse, 
                                 rating_result: AgentResponse) -> str:
        """做出最終決策"""
        # 整合各專家的結果
        response_parts = []
        
        # 添加類別分析
        response_parts.append(f"根據您的查詢，我將其分類為 {query.category or '混合'} 類別")
        
        # 添加檢索結果
        response_parts.append(rag_result.content)
        
        # 添加摘要
        if summary_result.content:
            response_parts.append(f"內容摘要: {summary_result.content}")
        
        # 添加評分
        if rating_result.content:
            response_parts.append(f"質量評估: {rating_result.content}")
        
        return "\n\n".join(response_parts)


# ==================== 代理人管理器 ====================

class AgentManager:
    """
    代理人管理器
    
    此類別負責管理所有代理人，提供統一的介面來
    處理用戶查詢和協調代理人協作。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化代理人管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.leader_agent = LeaderAgent(config.get('leader', {}))
        
        logger.info("代理人管理器初始化完成")
    
    async def process_query(self, query: str, user_id: str, 
                          category: Optional[str] = None) -> AgentResponse:
        """
        處理用戶查詢
        
        Args:
            query: 查詢內容
            user_id: 用戶 ID
            category: 預分類類別
            
        Returns:
            AgentResponse: 處理結果
        """
        try:
            # 創建用戶查詢對象
        user_query = UserQuery(
            query=query,
            user_id=user_id,
            category=category
        )
        
            # 委託給領導者代理人處理
            return await self.leader_agent.process(user_query)
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {str(e)}")
            return AgentResponse(
                content="查詢處理失敗",
                confidence=0.0,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=0.0
            )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        獲取代理人狀態
        
        Returns:
            Dict: 代理人狀態資訊
        """
        return {
            "leader_agent": {
                "name": self.leader_agent.name,
                "role": self.leader_agent.role,
                "status": "active"
            },
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        } 