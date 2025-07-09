"""
Podwise RAG Pipeline - 核心模組

提供 RAG (Retrieval-Augmented Generation) Pipeline 的核心功能：
- 代理管理
- 工具整合
- MCP (Model Context Protocol) 整合
- 增強推薦系統
- 向量搜尋
- 情感分析

作者: Podwise Team
版本: 2.0.0
"""

# 基礎模組
from .agent_manager import AgentManager
from .api_models import (
    QueryRequest, QueryResponse, UserQueryRequest, UserQueryResponse,
    VectorSearchRequest, VectorSearchResponse, ContentProcessRequest, ContentProcessResponse,
    SystemInfoResponse, HealthCheckResponse, ErrorResponse
)

# MCP 整合模組
from .mcp_integration import (
    PodwiseMCPIntegration,
    get_mcp_integration,
    MCPTool,
    MCPResource
)

# Langfuse 追蹤模組
from .langfuse_tracking import (
    LangfuseTracker,
    get_langfuse_tracker,
    langfuse_trace,
    LangfuseTraceContext,
    trace_function_call
)

# 增強推薦器 (MCP 整合版本)
from .enhanced_podcast_recommender import (
    MCPEnhancedPodcastRecommender,
    get_mcp_enhanced_recommender,
    MCPEnhancedRecommendation
)

# 向量搜尋工具
from ..tools.enhanced_vector_search import RAGVectorSearch

# Apple Podcast 排名系統
from .apple_podcast_ranking import (
    ApplePodcastRankingSystem,
    get_apple_podcast_ranking
)

__all__ = [
    # 基礎模組
    "AgentManager",
    "QueryRequest",
    "QueryResponse", 
    "UserQueryRequest",
    "UserQueryResponse",
    "VectorSearchRequest",
    "VectorSearchResponse",
    "ContentProcessRequest",
    "ContentProcessResponse",
    "SystemInfoResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    
    # MCP 整合
    "PodwiseMCPIntegration",
    "get_mcp_integration",
    "MCPTool",
    "MCPResource",
    
    # Langfuse 追蹤
    "LangfuseTracker",
    "get_langfuse_tracker",
    "langfuse_trace",
    "LangfuseTraceContext",
    "trace_function_call",
    
    # 增強推薦器
    "MCPEnhancedPodcastRecommender",
    "get_mcp_enhanced_recommender",
    "MCPEnhancedRecommendation",
    
    # 向量搜尋
    "RAGVectorSearch",
    
    # Apple Podcast 排名
    "ApplePodcastRankingSystem",
    "get_apple_podcast_ranking"
]
