#!/usr/bin/env python3
"""
CrewAI 架構配置文件
確保所有專家都通過 Leader Agent 和 Category 專家協調使用
"""

from typing import Dict, Any

def get_crewai_config() -> Dict[str, Any]:
    """
    獲取 CrewAI 架構配置
    
    Returns:
        Dict[str, Any]: 完整的配置字典
    """
    return {
        # Leader Agent 配置
        "leader": {
            "name": "Leader",
            "role": "三層架構協調者",
            "enabled": True,
            
            # 下層專家配置
            "rag_expert": {
                "enabled": True,
                "name": "RAG Expert",
                "role": "語意檢索和向量搜尋專家",
                "tools": ["EnhancedVectorSearchTool", "KNNRecommender"],
                "confidence_threshold": 0.7
            },
            
            "summary_expert": {
                "enabled": True,
                "name": "Summary Expert", 
                "role": "內容摘要生成專家",
                "tools": ["UnifiedLLMTool"],
                "confidence_threshold": 0.8
            },
            
            "rating_expert": {
                "enabled": True,
                "name": "Rating Expert",
                "role": "質量評估和評分專家",
                "tools": ["QualityEvaluator"],
                "confidence_threshold": 0.7
            },
            
            "tts_expert": {
                "enabled": True,
                "name": "TTS Expert",
                "role": "語音合成專家", 
                "tools": ["TTSService"],
                "confidence_threshold": 0.9
            },
            
            "user_manager": {
                "enabled": True,
                "name": "User Manager",
                "role": "用戶 ID 管理和記錄追蹤專家",
                "tools": ["ChatHistoryService"],
                "confidence_threshold": 0.8
            },
            
            # 類別專家配置
            "business_expert": {
                "enabled": True,
                "name": "Business Expert",
                "role": "商業類別專家",
                "tools": ["KeywordMapper", "BusinessKnowledgeBase"],
                "confidence_threshold": 0.7,
                "keywords": [
                    "股票", "投資", "理財", "財經", "市場", "經濟",
                    "台積電", "聯發科", "基金", "債券", "保險"
                ]
            },
            
            "education_expert": {
                "enabled": True,
                "name": "Education Expert", 
                "role": "教育類別專家",
                "tools": ["KeywordMapper", "EducationKnowledgeBase"],
                "confidence_threshold": 0.7,
                "keywords": [
                    "學習", "技能", "成長", "職涯", "發展", "教育",
                    "自我提升", "目標", "習慣", "時間管理"
                ]
            }
        },
        
        # 工具配置
        "tools": {
            "EnhancedVectorSearchTool": {
                "enabled": True,
                "collection_name": "podcast_embeddings",
                "host": "milvus",
                "port": 19530,
                "dimension": 1536
            },
            
            "KNNRecommender": {
                "enabled": True,
                "k": 5,
                "metric": "cosine",
                "category_filter": True
            },
            
            "KeywordMapper": {
                "enabled": True,
                "business_keywords_file": "business_keywords.json",
                "education_keywords_file": "education_keywords.json",
                "confidence_threshold": 0.7
            },
            
            "UnifiedLLMTool": {
                "enabled": True,
                "models": ["qwen3", "deepseek"],
                "fallback_model": "qwen3",
                "max_tokens": 2000
            },
            
            "ChatHistoryService": {
                "enabled": True,
                "mongo_uri": "mongodb://localhost:27017",
                "database": "podwise",
                "collection": "chat_history"
            }
        },
        
        # 處理流程配置
        "workflow": {
            "steps": [
                {
                    "name": "user_validation",
                    "agent": "user_manager",
                    "required": True,
                    "order": 1
                },
                {
                    "name": "query_categorization", 
                    "agent": "keyword_mapper",
                    "required": True,
                    "order": 2
                },
                {
                    "name": "rag_retrieval",
                    "agent": "rag_expert",
                    "required": True,
                    "order": 3
                },
                {
                    "name": "category_analysis",
                    "agent": "business_expert|education_expert",
                    "required": True,
                    "order": 4
                },
                {
                    "name": "content_summarization",
                    "agent": "summary_expert",
                    "required": False,
                    "order": 5
                },
                {
                    "name": "quality_rating",
                    "agent": "rating_expert", 
                    "required": False,
                    "order": 6
                },
                {
                    "name": "final_decision",
                    "agent": "leader",
                    "required": True,
                    "order": 7
                }
            ],
            
            "fallback_strategy": {
                "rag_failure": "use_keyword_search",
                "llm_failure": "use_rule_based_response",
                "category_uncertainty": "dual_category_analysis"
            }
        },
        
        # 性能配置
        "performance": {
            "max_concurrent_agents": 3,
            "timeout_seconds": 30,
            "retry_attempts": 2,
            "cache_enabled": True,
            "cache_ttl": 3600
        },
        
        # 監控配置
        "monitoring": {
            "enabled": True,
            "log_level": "INFO",
            "metrics_collection": True,
            "performance_tracking": True,
            "error_reporting": True
        }
    }

def get_agent_config() -> Dict[str, Any]:
    """
    獲取代理人配置（向後相容）
    
    Returns:
        Dict[str, Any]: 代理人配置
    """
    return get_crewai_config()

def validate_config(config: Dict[str, Any]) -> bool:
    """
    驗證配置完整性
    
    Args:
        config: 配置字典
        
    Returns:
        bool: 配置是否有效
    """
    required_sections = ["leader", "tools", "workflow"]
    
    for section in required_sections:
        if section not in config:
            return False
    
    # 檢查 Leader 配置
    leader_config = config.get("leader", {})
    required_agents = [
        "rag_expert", "summary_expert", "rating_expert", 
        "tts_expert", "user_manager", "business_expert", "education_expert"
    ]
    
    for agent in required_agents:
        if agent not in leader_config:
            return False
    
    return True

# 預設配置實例
DEFAULT_CONFIG = get_crewai_config() 