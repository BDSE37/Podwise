#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 統一數據模型

定義所有核心數據類別，確保類型安全和一致性

作者: Podwise Team
版本: 4.0.0
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """代理狀態枚舉"""
    IDLE = "idle"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


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
class SearchResult:
    """搜尋結果"""
    document_id: str
    content: str
    score: float
    source: str
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
class UserQuery:
    """用戶查詢"""
    query: str
    user_id: str
    category: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not self.query.strip():
            raise ValueError("查詢內容不能為空")
        
        if not self.user_id.strip():
            raise ValueError("用戶 ID 不能為空")


@dataclass
class AgentResponse:
    """代理回應"""
    content: str
    confidence: float
    reasoning: str
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.SUCCESS


@dataclass
class RecommendationResult:
    """推薦結果"""
    title: str
    description: str
    category: str
    confidence: float
    reasoning: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SummaryResult:
    """摘要結果"""
    original_text: str
    summary: str
    word_count: int
    confidence: float
    key_points: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """分類結果"""
    primary_category: str
    primary_confidence: float
    secondary_category: Optional[str] = None
    secondary_confidence: float = 0.0
    is_cross_category: bool = False
    matched_keywords: List[Dict[str, Any]] = field(default_factory=list)
    classification_reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSearchResult:
    """Web 搜尋結果"""
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    relevance_score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingMetrics:
    """處理指標"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_time: Optional[float] = None
    steps_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """計算總時間"""
        if self.end_time and self.start_time:
            self.total_time = (self.end_time - self.start_time).total_seconds()


@dataclass
class SystemHealth:
    """系統健康狀態"""
    status: str
    timestamp: datetime
    components: Dict[str, bool]
    version: str
    uptime: float
    memory_usage: float
    cpu_usage: float
    active_connections: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# 工廠函數
def create_rag_response(
    content: str,
    confidence: float,
    sources: List[str],
    processing_time: float,
    level_used: str,
    **metadata
) -> RAGResponse:
    """創建 RAG 回應"""
    return RAGResponse(
        content=content,
        confidence=confidence,
        sources=sources,
        processing_time=processing_time,
        level_used=level_used,
        metadata=metadata
    )


def create_agent_response(
    content: str,
    confidence: float,
    reasoning: str,
    processing_time: float,
    status: AgentStatus = AgentStatus.SUCCESS,
    **metadata
) -> AgentResponse:
    """創建代理回應"""
    return AgentResponse(
        content=content,
        confidence=confidence,
        reasoning=reasoning,
        processing_time=processing_time,
        status=status,
        metadata=metadata
    )


def create_user_query(
    query: str,
    user_id: str,
    category: Optional[str] = None,
    context: Optional[str] = None,
    **metadata
) -> UserQuery:
    """創建用戶查詢"""
    return UserQuery(
        query=query,
        user_id=user_id,
        category=category,
        context=context,
        metadata=metadata
    )


def create_processing_metrics(
    start_time: Optional[datetime] = None,
    **metadata
) -> ProcessingMetrics:
    """創建處理指標"""
    return ProcessingMetrics(
        start_time=start_time or datetime.now(),
        metadata=metadata
    ) 