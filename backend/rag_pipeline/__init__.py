#!/usr/bin/env python3
"""
Podwise RAG Pipeline 模組

整合三層 CrewAI 架構、智能 TAG 提取、向量搜尋、Web Search 備援等功能。
遵循 Google Clean Code 原則，提供統一的 OOP 介面。

作者: Podwise Team
版本: 3.0.0
"""

# 核心 RAG Pipeline
from .main import (
    PodwiseRAGPipeline,
    get_rag_pipeline
)

# 核心組件
from .core.base_agent import BaseAgent, AgentResponse, UserQuery
from .core.agent_manager import AgentManager
from .core.crew_agents import (
    LeaderAgent,
    BusinessExpertAgent,
    EducationExpertAgent,
    RAGExpertAgent,
    SummaryExpertAgent,
    TagClassificationExpertAgent,
    TTSExpertAgent,
    UserManagerAgent
)

# 配置管理
from .config.integrated_config import get_config
from .config.agent_roles_config import get_agent_roles_manager
from .config.prompt_templates import get_prompt_template, format_prompt

# 工具和服務
from .tools.enhanced_vector_search import UnifiedVectorSearch
from .tools.podcast_formatter import PodcastFormatter
from .tools.web_search_tool import WebSearchTool
from .core.content_categorizer import ContentProcessor
from .core.hierarchical_rag_pipeline import HierarchicalRAGPipeline

# 監控和工具
from .utils.langfuse_integration import get_langfuse_monitor
from .core.chat_history_service import get_chat_history_service

__version__ = "3.0.0"
__author__ = "Podwise Team"

__all__ = [
    # 核心 RAG Pipeline
    "PodwiseRAGPipeline",
    "get_rag_pipeline",
    
    # 基礎代理組件
    "BaseAgent",
    "AgentResponse", 
    "UserQuery",
    "AgentManager",
    
    # CrewAI 代理
    "LeaderAgent",
    "BusinessExpertAgent",
    "EducationExpertAgent",
    "RAGExpertAgent",
    "SummaryExpertAgent",
    "TagClassificationExpertAgent",
    "TTSExpertAgent",
    "UserManagerAgent",
    
    # 配置管理
    "get_config",
    "get_agent_roles_manager",
    "get_prompt_template",
    "format_prompt",
    
    # 工具和服務
    "UnifiedVectorSearch",
    "PodcastFormatter",
    "WebSearchTool",
    "ContentProcessor",
    "HierarchicalRAGPipeline",
    
    # 監控和工具
    "get_langfuse_monitor",
    "get_chat_history_service"
] 