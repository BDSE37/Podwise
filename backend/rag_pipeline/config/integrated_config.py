#!/usr/bin/env python3
"""
Podwise 統一配置管理器

整合所有配置功能：
- 模型配置（LLM、向量、嵌入）
- 資料庫配置（MongoDB、PostgreSQL、Redis、Milvus）
- API 配置（OpenAI、Anthropic、Google、Supabase）
- Langfuse 監控配置
- CrewAI 代理配置
- RAG Pipeline 配置
- 語意檢索配置

作者: Podwise Team
版本: 2.0.0
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    # LLM 模型配置
    qwen3_8b_model: str = "Qwen/Qwen2.5-8B-Instruct"
    qwen3_taiwan_model: str = "weiren119/Qwen2.5-Taiwan-8B-Instruct"
    
    # 向量模型配置
    bge_m3_model: str = "BAAI/bge-m3"
    bge_m3_dimension: int = 1024
    
    # 語意檢索模型配置
    text2vec_model: str = "text2vec-base-chinese"
    text2vec_path: str = "shibing624/text2vec-base-chinese"
    text2vec_max_length: int = 512
    text2vec_batch_size: int = 32
    text2vec_normalize_embeddings: bool = True
    text2vec_pooling_strategy: str = "mean"
    text2vec_device: str = "auto"
    
    # 嵌入模型配置
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    
    # 模型優先級配置
    llm_priority: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.llm_priority is None:
            self.llm_priority = [
                "qwen2.5:taiwan",     # 第一優先：台灣優化版本
                "qwen3:8b",           # 第二優先：Qwen3:8b
                "openai:gpt-3.5",     # 備援：OpenAI GPT-3.5
                "openai:gpt-4"        # 最後備援：OpenAI GPT-4
            ]


@dataclass
class DatabaseConfig:
    """資料庫配置"""
    # MongoDB
    mongodb_uri: str = "mongodb://worker3:27017/podwise"
    mongodb_database: str = "podwise"
    mongodb_collection: str = "conversations"
    
    # PostgreSQL
    postgres_host: str = "worker3"
    postgres_port: int = 5432
    postgres_db: str = "podwise"
    postgres_user: str = "podwise_user"
    postgres_password: str = ""
    
    # Redis
    redis_host: str = "worker3"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Milvus
    milvus_host: str = "worker3"
    milvus_port: int = 19530
    milvus_collection: str = "podcast_chunks"


@dataclass
class APIConfig:
    """API 配置"""
    # OpenAI
    openai_api_key: str = ""
    openai_organization: str = ""
    openai_chat_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"
    
    # Google
    google_api_key: str = ""
    google_genai_model: str = "gemini-pro"
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""


@dataclass
class LangfuseConfig:
    """Langfuse 追蹤配置 (已移除，使用 Langfuse Cloud)"""
    public_key: str = ""
    secret_key: str = ""
    host: str = "https://cloud.langfuse.com"
    enabled: bool = False  # 已停用
    
    # 追蹤配置
    trace_thinking_process: bool = False
    trace_model_selection: bool = False
    trace_agent_interactions: bool = False
    trace_vector_search: bool = False


@dataclass
class CrewAIConfig:
    """CrewAI 代理配置"""
    enabled: bool = True
    
    # 代理配置
    confidence_threshold: float = 0.7
    fallback_threshold: float = 0.5
    max_processing_time: float = 30.0
    
    # 領導者代理
    leader_model: str = "qwen2.5-7b-instruct"
    leader_temperature: float = 0.7
    leader_max_tokens: int = 2048
    
    # 商業專家
    business_expert_model: str = "qwen2.5-7b-instruct"
    business_expert_temperature: float = 0.8
    business_expert_max_tokens: int = 1024
    
    # 教育專家
    education_expert_model: str = "qwen2.5-7b-instruct"
    education_expert_temperature: float = 0.8
    education_expert_max_tokens: int = 1024
    
    # 自動決策配置
    auto_decision_enabled: bool = True
    recommendation_trigger: str = "low_confidence"


@dataclass
class RAGConfig:
    """RAG Pipeline 配置"""
    # 基礎配置
    model_name: str = "BAAI/bge-m3"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # 向量搜索配置
    vector_search_enabled: bool = True
    hybrid_search_enabled: bool = True
    semantic_search_enabled: bool = True
    
    # 層級化 RAG 配置
    level1_enabled: bool = True
    level2_enabled: bool = True
    level3_enabled: bool = True
    level4_enabled: bool = True
    level5_enabled: bool = True
    level6_enabled: bool = True
    
    # 檢索配置
    retrieval_top_k: int = 10
    retrieval_similarity_threshold: float = 0.3
    retrieval_time_weight_factor: float = 0.1
    retrieval_tag_weight_factor: float = 0.3
    retrieval_semantic_weight_factor: float = 0.7
    retrieval_max_tag_matches: int = 5
    
    # 分類權重
    category_business_weight: float = 1.0
    category_education_weight: float = 1.0
    category_other_weight: float = 0.8


@dataclass
class SemanticConfig:
    """語意檢索配置"""
    # 標籤匹配配置
    tag_file_path: Optional[str] = None
    tag_matching_enabled: bool = True
    
    # 混合檢索配置
    hybrid_search_enabled: bool = True
    semantic_weight: float = 0.7
    tag_weight: float = 0.3
    
    # 分類關鍵詞
    business_keywords: List[str] = None
    education_keywords: List[str] = None
    
    def __post_init__(self):
        if self.business_keywords is None:
            self.business_keywords = [
                "股票", "投資", "理財", "財經", "市場", "經濟", "創業", "職場", 
                "科技", "財務", "ETF", "台積電", "美股", "基金", "房地產"
            ]
        
        if self.education_keywords is None:
            self.education_keywords = [
                "學習", "成長", "職涯", "心理", "溝通", "語言", "親子", 
                "斜槓", "副業", "技能", "發展", "教育", "自我提升"
            ]


class PodwiseIntegratedConfig(BaseSettings):
    """Podwise 統一配置主類別"""
    
    # 環境配置
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # 各模組配置
    models: ModelConfig = Field(default_factory=ModelConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    crewai: CrewAIConfig = Field(default_factory=CrewAIConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    
    # 服務配置
    rag_pipeline_host: str = Field(default="localhost")
    rag_pipeline_port: int = Field(default=8002)
    tts_host: str = Field(default="localhost")
    tts_port: int = Field(default=8002)
    stt_host: str = Field(default="localhost")
    stt_port: int = Field(default=8003)
    llm_host: str = Field(default="localhost")
    llm_port: int = Field(default=8004)
    
    # Ollama 配置
    ollama_host: str = Field(default="http://worker1:11434")
    ollama_model: str = Field(default="qwen2.5:8b")
    
    # 安全配置
    secret_key: str = Field(default="")
    jwt_secret_key: str = Field(default="")
    encryption_key: str = Field(default="")
    
    # Kubernetes 配置
    k8s_namespace: str = Field(default="podwise")
    k8s_registry: str = Field(default="192.168.32.38:5000")
    k8s_image_tag: str = Field(default="latest")
    
    # 快取配置
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    cache_max_size: int = Field(default=1000)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 允許額外的輸入參數
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_from_env()
        self._load_from_yaml()
    
    def _load_from_env(self):
        """從環境變數載入配置"""
        # 載入 API 金鑰
        self.api.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.api.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.api.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.api.supabase_url = os.getenv("SUPABASE_URL", "")
        self.api.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.api.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        
        # 載入資料庫配置
        self.database.mongodb_uri = os.getenv("MONGODB_URI", self.database.mongodb_uri)
        self.database.postgres_host = os.getenv("POSTGRES_HOST", self.database.postgres_host)
        self.database.postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        self.database.redis_password = os.getenv("REDIS_PASSWORD", "")
        self.database.milvus_host = os.getenv("MILVUS_HOST", self.database.milvus_host)
        
        # 載入 Langfuse 配置
        self.langfuse.public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.langfuse.secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.langfuse.host = os.getenv("LANGFUSE_HOST", self.langfuse.host)
        
        # 載入安全配置
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "")
    
    def _load_from_yaml(self):
        """從 YAML 檔案載入配置"""
        yaml_path = "config/hierarchical_rag_config.yaml"
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                
                # 更新 RAG 配置
                if 'rag' in yaml_config:
                    rag_config = yaml_config['rag']
                    for key, value in rag_config.items():
                        if hasattr(self.rag, key):
                            setattr(self.rag, key, value)
                
                # 更新語意檢索配置
                if 'semantic' in yaml_config:
                    semantic_config = yaml_config['semantic']
                    for key, value in semantic_config.items():
                        if hasattr(self.semantic, key):
                            setattr(self.semantic, key, value)
                            
            except Exception as e:
                print(f"載入 YAML 配置失敗: {e}")
    
    # ==================== 配置檢查方法 ====================
    
    def is_openai_configured(self) -> bool:
        """檢查 OpenAI 是否已配置"""
        return bool(self.api.openai_api_key and len(self.api.openai_api_key.strip()) > 0)
    
    def is_anthropic_configured(self) -> bool:
        """檢查 Anthropic 是否已配置"""
        return bool(self.api.anthropic_api_key and len(self.api.anthropic_api_key.strip()) > 0)
    
    def is_google_configured(self) -> bool:
        """檢查 Google AI 是否已配置"""
        return bool(self.api.google_api_key and len(self.api.google_api_key.strip()) > 0)
    
    def is_supabase_configured(self) -> bool:
        """檢查 Supabase 是否已配置"""
        return bool(
            self.api.supabase_url and 
            self.api.supabase_key and 
            len(self.api.supabase_url.strip()) > 0 and 
            len(self.api.supabase_key.strip()) > 0
        )
    
    def is_langfuse_configured(self) -> bool:
        """檢查 Langfuse 是否已配置"""
        return bool(
            self.langfuse.public_key and 
            self.langfuse.secret_key and 
            len(self.langfuse.public_key.strip()) > 0 and 
            len(self.langfuse.secret_key.strip()) > 0
        )
    
    # ==================== 配置獲取方法 ====================
    
    def get_llm_config(self) -> Dict[str, Any]:
        """獲取 LLM 配置"""
        return {
            "primary_model": "qwen3:8b",
            "taiwan_model": "qwen3:taiwan",
            "models": self.models.llm_priority,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model
        }
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """獲取嵌入配置"""
        return {
            "model": self.models.bge_m3_model,
            "dimension": self.models.bge_m3_dimension,
            "chunk_size": self.rag.chunk_size,
            "chunk_overlap": self.rag.chunk_overlap
        }
    
    def get_vector_search_config(self) -> Dict[str, Any]:
        """獲取向量搜索配置"""
        return {
            "milvus_host": self.database.milvus_host,
            "milvus_port": self.database.milvus_port,
            "collection": self.database.milvus_collection,
            "top_k": self.rag.top_k,
            "similarity_threshold": self.rag.similarity_threshold,
            "hybrid_search": self.rag.hybrid_search_enabled,
            "semantic_search": self.rag.semantic_search_enabled
        }
    
    def get_crewai_config(self) -> Dict[str, Any]:
        """獲取 CrewAI 配置"""
        return {
            "enabled": self.crewai.enabled,
            "confidence_threshold": self.crewai.confidence_threshold,
            "fallback_threshold": self.crewai.fallback_threshold,
            "max_processing_time": self.crewai.max_processing_time,
            "leader": {
                "model": self.crewai.leader_model,
                "temperature": self.crewai.leader_temperature,
                "max_tokens": self.crewai.leader_max_tokens
            },
            "business_expert": {
                "model": self.crewai.business_expert_model,
                "temperature": self.crewai.business_expert_temperature,
                "max_tokens": self.crewai.business_expert_max_tokens
            },
            "education_expert": {
                "model": self.crewai.education_expert_model,
                "temperature": self.crewai.education_expert_temperature,
                "max_tokens": self.crewai.education_expert_max_tokens
            },
            "auto_decision": self.crewai.auto_decision_enabled,
            "recommendation_trigger": self.crewai.recommendation_trigger
        }
    
    def get_semantic_config(self) -> Dict[str, Any]:
        """獲取語意檢索配置"""
        return {
            "model_config": {
                "model_name": self.models.text2vec_model,
                "model_path": self.models.text2vec_path,
                "max_length": self.models.text2vec_max_length,
                "batch_size": self.models.text2vec_batch_size,
                "normalize_embeddings": self.models.text2vec_normalize_embeddings,
                "pooling_strategy": self.models.text2vec_pooling_strategy,
                "device": self.models.text2vec_device
            },
            "retrieval_config": {
                "top_k": self.rag.retrieval_top_k,
                "similarity_threshold": self.rag.retrieval_similarity_threshold,
                "time_weight_factor": self.rag.retrieval_time_weight_factor,
                "tag_weight_factor": self.rag.retrieval_tag_weight_factor,
                "semantic_weight_factor": self.rag.retrieval_semantic_weight_factor,
                "max_tag_matches": self.rag.retrieval_max_tag_matches
            },
            "category_weights": {
                "商業": self.rag.category_business_weight,
                "教育": self.rag.category_education_weight,
                "其他": self.rag.category_other_weight
            },
            "tag_matching": {
                "enabled": self.semantic.tag_matching_enabled,
                "file_path": self.semantic.tag_file_path
            },
            "business_keywords": self.semantic.business_keywords,
            "education_keywords": self.semantic.education_keywords
        }
    
    def get_langfuse_config(self) -> Dict[str, Any]:
        """獲取 Langfuse 配置"""
        return {
            "public_key": self.langfuse.public_key,
            "secret_key": self.langfuse.secret_key,
            "host": self.langfuse.host,
            "enabled": self.langfuse.enabled,
            "trace_thinking": self.langfuse.trace_thinking_process,
            "trace_model_selection": self.langfuse.trace_model_selection,
            "trace_agent_interactions": self.langfuse.trace_agent_interactions,
            "trace_vector_search": self.langfuse.trace_vector_search
        }
    
    def get_rag_config(self) -> Dict[str, Any]:
        """獲取 RAG Pipeline 配置"""
        return {
            "model_name": self.rag.model_name,
            "chunk_size": self.rag.chunk_size,
            "chunk_overlap": self.rag.chunk_overlap,
            "top_k": self.rag.top_k,
            "similarity_threshold": self.rag.similarity_threshold,
            "vector_search_enabled": self.rag.vector_search_enabled,
            "hybrid_search_enabled": self.rag.hybrid_search_enabled,
            "semantic_search_enabled": self.rag.semantic_search_enabled,
            "levels": {
                "level1_enabled": self.rag.level1_enabled,
                "level2_enabled": self.rag.level2_enabled,
                "level3_enabled": self.rag.level3_enabled,
                "level4_enabled": self.rag.level4_enabled,
                "level5_enabled": self.rag.level5_enabled,
                "level6_enabled": self.rag.level6_enabled
            }
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """驗證配置"""
        return {
            "openai": self.is_openai_configured(),
            "anthropic": self.is_anthropic_configured(),
            "google": self.is_google_configured(),
            "supabase": self.is_supabase_configured(),
            "langfuse": self.is_langfuse_configured(),
            "mongodb": self.database.mongodb_uri != "mongodb://worker3:27017/podwise",
            "postgres": bool(self.database.postgres_password),
            "redis": bool(self.database.redis_password),
            "milvus": True,  # 預設為 True
            "secret_key": bool(self.secret_key),
            "jwt_secret_key": bool(self.jwt_secret_key)
        }
    
    def print_config_summary(self):
        """顯示配置摘要"""
        validation = self.validate_config()
        
        print("🔧 Podwise 統一配置摘要")
        print("=" * 60)
        print(f"環境：{self.environment}")
        print(f"除錯模式：{self.debug}")
        print(f"日誌等級：{self.log_level}")
        
        print("\n🤖 模型配置：")
        print(f"  主要 LLM：{self.models.llm_priority[0]}")
        print(f"  台灣優化：{self.models.llm_priority[1]}")
        print(f"  向量模型：{self.models.bge_m3_model}")
        print(f"  語意模型：{self.models.text2vec_model}")
        
        print("\n📋 API 配置狀態：")
        print(f"  OpenAI：{'✅' if validation['openai'] else '❌'}")
        print(f"  Anthropic：{'✅' if validation['anthropic'] else '❌'}")
        print(f"  Google AI：{'✅' if validation['google'] else '❌'}")
        print(f"  Supabase：{'✅' if validation['supabase'] else '❌'}")
        
        print("\n🗄️ 資料庫配置狀態：")
        print(f"  MongoDB：{'✅' if validation['mongodb'] else '❌'}")
        print(f"  PostgreSQL：{'✅' if validation['postgres'] else '❌'}")
        print(f"  Redis：{'✅' if validation['redis'] else '❌'}")
        print(f"  Milvus：{'✅' if validation['milvus'] else '❌'}")
        
        print("\n🔍 追蹤配置狀態：")
        print(f"  Langfuse：{'✅' if validation['langfuse'] else '❌'}")
        print(f"  思考過程追蹤：{'✅' if self.langfuse.trace_thinking_process else '❌'}")
        print(f"  模型選擇追蹤：{'✅' if self.langfuse.trace_model_selection else '❌'}")
        print(f"  代理互動追蹤：{'✅' if self.langfuse.trace_agent_interactions else '❌'}")
        
        print("\n🚀 功能配置：")
        print(f"  CrewAI 代理：{'✅' if self.crewai.enabled else '❌'}")
        print(f"  向量搜索：{'✅' if self.rag.vector_search_enabled else '❌'}")
        print(f"  混合搜索：{'✅' if self.rag.hybrid_search_enabled else '❌'}")
        print(f"  語義搜索：{'✅' if self.rag.semantic_search_enabled else '❌'}")
        print(f"  標籤匹配：{'✅' if self.semantic.tag_matching_enabled else '❌'}")
        
        print("\n🔐 安全配置狀態：")
        print(f"  Secret Key：{'✅' if validation['secret_key'] else '❌'}")
        print(f"  JWT Secret：{'✅' if validation['jwt_secret_key'] else '❌'}")


# 全域配置實例
podwise_config = None


def get_config() -> PodwiseIntegratedConfig:
    """獲取配置實例"""
    global podwise_config
    if podwise_config is None:
        # 確保載入環境變數
        from dotenv import load_dotenv
        import os
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env'))
        
        # 初始化配置
        podwise_config = PodwiseIntegratedConfig()
        podwise_config._load_from_env()
        podwise_config._load_from_yaml()
    
    return podwise_config


# 向後相容性別名
def get_crewai_config() -> Dict[str, Any]:
    """獲取 CrewAI 配置（向後相容）"""
    return get_config().get_crewai_config()


def get_semantic_config() -> Dict[str, Any]:
    """獲取語意檢索配置（向後相容）"""
    return get_config().get_semantic_config()


def validate_config(config: Dict[str, Any]) -> bool:
    """驗證配置（向後相容）"""
    return all(get_config().validate_config().values())


if __name__ == "__main__":
    # 測試配置
    config = get_config()
    config.print_config_summary() 