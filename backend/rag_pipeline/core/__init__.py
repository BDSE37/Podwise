"""
Podwise RAG Pipeline - 核心模組

三層 CrewAI 架構核心模組：
- 第一層：領導者層 (Leader Layer) - 決策統籌
- 第二層：類別專家層 (Category Expert Layer) - 商業/教育專家  
- 第三層：功能專家層 (Functional Expert Layer) - 專業功能處理

作者: Podwise Team
版本: 4.0.0
"""

# ==================== 統一數據模型 ====================
from .data_models import (
    RAGResponse,
    UserQuery,
    AgentResponse,
    SearchResult,
    QueryContext,
    AgentStatus,
    RecommendationResult,
    SummaryResult,
    ClassificationResult,
    WebSearchResult,
    ProcessingMetrics,
    SystemHealth,
    create_rag_response,
    create_agent_response,
    create_user_query,
    create_processing_metrics
)

# ==================== 基礎代理類別 ====================
from .base_agent import BaseAgent

# ==================== 第一層：領導者層 ====================
from .crew_agents import LeaderAgent

# ==================== 第二層：類別專家層 ====================
from .crew_agents import BusinessExpertAgent, EducationExpertAgent

# ==================== 第三層：功能專家層 ====================
from .crew_agents import (
    UserManagerAgent,
    WebSearchAgent,
    RAGExpertAgent,
    SummaryExpertAgent,
    TagClassificationExpertAgent,
    TTSExpertAgent
)

# ==================== 核心服務 ====================
# 延遲導入以避免循環導入問題
def _import_core_services():
    """延遲導入核心服務"""
    try:
        from .hierarchical_rag_pipeline import HierarchicalRAGPipeline
        from .enhanced_vector_search import RAGVectorSearch
        from .qwen_llm_manager import Qwen3LLMManager
        from .content_categorizer import ContentCategorizer
        from .apple_podcast_ranking import ApplePodcastRankingSystem
        from .default_qa_processor import DefaultQAProcessor, create_default_qa_processor
        from .unified_service_manager import UnifiedServiceManager
        
        return {
            'HierarchicalRAGPipeline': HierarchicalRAGPipeline,
            'RAGVectorSearch': RAGVectorSearch,
            'Qwen3LLMManager': Qwen3LLMManager,
            'ContentCategorizer': ContentCategorizer,
            'ApplePodcastRankingSystem': ApplePodcastRankingSystem,
            'DefaultQAProcessor': DefaultQAProcessor,
            'create_default_qa_processor': create_default_qa_processor,
            'UnifiedServiceManager': UnifiedServiceManager
        }
    except ImportError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ℹ️ 核心服務導入失敗: {e}")
        return {}

__all__ = [
    # 統一數據模型
    "RAGResponse",
    "UserQuery", 
    "AgentResponse",
    "SearchResult",
    "QueryContext",
    "AgentStatus",
    "RecommendationResult",
    "SummaryResult",
    "ClassificationResult",
    "WebSearchResult",
    "ProcessingMetrics",
    "SystemHealth",
    "create_rag_response",
    "create_agent_response",
    "create_user_query",
    "create_processing_metrics",
    
    # 基礎代理類別
    "BaseAgent",
    
    # 第一層：領導者層
    "LeaderAgent",
    
    # 第二層：類別專家層
    "BusinessExpertAgent",
    "EducationExpertAgent",
    
    # 第三層：功能專家層
    "UserManagerAgent",
    "WebSearchAgent", 
    "RAGExpertAgent",
    "SummaryExpertAgent",
    "TagClassificationExpertAgent",
    "TTSExpertAgent",
    
    # 延遲導入函數
    "_import_core_services"
] 