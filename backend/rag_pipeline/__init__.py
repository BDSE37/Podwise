#!/usr/bin/env python3
"""
Podwise RAG Pipeline 模組

提供統一的 OOP 介面，整合所有 RAG Pipeline 功能：
- Apple Podcast 優先推薦系統
- 層級化 CrewAI 架構
- 語意檢索（text2vec-base-chinese + TAG_info.csv）
- 提示詞模板系統
- 聊天歷史記錄
- 效能優化

作者: Podwise Team
版本: 2.0.0
"""

# 主要介面
from .main import PodwiseRAGPipeline, get_rag_pipeline

# 核心模組
from .core.apple_podcast_ranking import ApplePodcastRankingSystem, get_apple_podcast_ranking
from .core.integrated_core import UnifiedQueryProcessor, get_query_processor
from .core.hierarchical_rag_pipeline import HierarchicalRAGPipeline, RAGResponse
from .core.crew_agents import (
    LeaderAgent, BusinessExpertAgent, EducationExpertAgent, 
    UserManagerAgent, UserQuery, AgentResponse
)
from .core.content_categorizer import ContentCategorizer, get_content_processor
from .core.qwen_llm_manager import Qwen3LLMManager, get_qwen3_llm_manager
from .core.chat_history_service import ChatHistoryService, get_chat_history_service

# 配置模組
from .config.integrated_config import get_config, PodwiseIntegratedConfig
from .config.prompt_templates import PodwisePromptTemplates, get_prompt_template, format_prompt
from .config.agent_roles_config import AgentRolesManager, get_agent_roles_manager

# 工具模組
from .tools.enhanced_podcast_recommender import EnhancedPodcastRecommender
from .tools.enhanced_vector_search import RAGVectorSearch, create_rag_vector_search
from .tools.podcast_formatter import PodcastFormatter, FormattedPodcast

# 腳本模組
# from .scripts.tag_processor import SmartTagExtractor  # 暫時註解，避免導入錯誤
# from .scripts.audio_transcription_pipeline import AudioTranscriptionPipeline  # 暫時註解，避免導入錯誤

# 版本資訊
__version__ = "2.0.0"
__author__ = "Podwise Team"
__description__ = "整合 Apple Podcast 排名系統的智能推薦引擎"

# 主要導出
__all__ = [
    # 主要介面
    "PodwiseRAGPipeline",
    "get_rag_pipeline",
    
    # 核心模組
    "ApplePodcastRankingSystem",
    "get_apple_podcast_ranking",
    "UnifiedQueryProcessor",
    "get_query_processor",
    "HierarchicalRAGPipeline",
    "RAGResponse",
    "LeaderAgent",
    "BusinessExpertAgent", 
    "EducationExpertAgent",
    "UserManagerAgent",
    "UserQuery",
    "AgentResponse",
    "ContentCategorizer",
    "get_content_processor",
    "Qwen3LLMManager",
    "get_qwen3_llm_manager",
    "ChatHistoryService",
    "get_chat_history_service",
    
    # 配置模組
    "get_config",
    "PodwiseIntegratedConfig",
    "PodwisePromptTemplates",
    "get_prompt_template",
    "format_prompt",
    "AgentRolesManager",
    "get_agent_roles_manager",
    
    # 工具模組
    "EnhancedPodcastRecommender",
    "RAGVectorSearch",
    "create_rag_vector_search",
    "PodcastFormatter",
    "FormattedPodcast",
    
    # 腳本模組
    # "SmartTagExtractor",  # 暫時註解
    # "AudioTranscriptionPipeline",  # 暫時註解
    
    # 版本資訊
    "__version__",
    "__author__",
    "__description__"
] 