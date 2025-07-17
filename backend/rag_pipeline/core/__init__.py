"""
Podwise RAG Pipeline - 核心模組

提供各種核心功能：
- 向量搜尋工具
- LLM 管理器
- 聊天歷史服務
- 內容分類器
- Apple Podcast 排名系統
- CrewAI 代理
- 層級化 RAG Pipeline

作者: Podwise Team
版本: 2.0.0
"""

# 向量搜尋相關
from .enhanced_vector_search import RAGVectorSearch, RAGSearchConfig, create_rag_vector_search

# LLM 管理器
from .qwen_llm_manager import Qwen3LLMManager

# 聊天歷史服務
from .chat_history_service import ChatHistoryService

# 內容分類器
from .content_categorizer import ContentCategorizer

# Apple Podcast 排名系統
from .apple_podcast_ranking import ApplePodcastRankingSystem

# CrewAI 代理
from .crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent

# 層級化 RAG Pipeline
from .hierarchical_rag_pipeline import HierarchicalRAGPipeline

# 整合核心
from .integrated_core import AgentResponse, UserQuery, RAGResponse, BaseAgent

# 增強推薦器
from .enhanced_podcast_recommender import MCPEnhancedPodcastRecommender

__all__ = [
    # 向量搜尋
    "RAGVectorSearch",
    "RAGSearchConfig", 
    "create_rag_vector_search",
    
    # LLM 管理器
    "Qwen3LLMManager",
    
    # 聊天歷史服務
    "ChatHistoryService",
    
    # 內容分類器
    "ContentCategorizer",
    
    # Apple Podcast 排名系統
    "ApplePodcastRankingSystem",
    
    # CrewAI 代理
    "LeaderAgent",
    "BusinessExpertAgent", 
    "EducationExpertAgent",
    "UserManagerAgent",
    
    # 層級化 RAG Pipeline
    "HierarchicalRAGPipeline",
    
    # 整合核心
    "AgentResponse",
    "UserQuery",
    "RAGResponse", 
    "BaseAgent",
    
    # 增強推薦器
    "MCPEnhancedPodcastRecommender"
] 