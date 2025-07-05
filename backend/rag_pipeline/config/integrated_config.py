"""
Podwise 整合配置檔案
整合 BGE-M3 向量模型、Qwen3:8b LLM、Langfuse 追蹤、雙代理機制
"""

import os
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
    milvus_collection: str = "podwise_vectors"


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
    """Langfuse 追蹤配置"""
    public_key: str = ""
    secret_key: str = ""
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True
    
    # 追蹤配置
    trace_thinking_process: bool = True
    trace_model_selection: bool = True
    trace_agent_interactions: bool = True
    trace_vector_search: bool = True


@dataclass
class AgentConfig:
    """雙代理機制配置"""
    enabled: bool = True
    agent_1_type: str = "researcher"
    agent_2_type: str = "analyst"
    coordination_mode: str = "hierarchical"
    communication_protocol: str = "sequential"
    
    # 代理信心閾值
    confidence_threshold: float = 0.7
    fallback_threshold: float = 0.5
    
    # 自動決策配置
    auto_decision_enabled: bool = True
    recommendation_trigger: str = "low_confidence"


@dataclass
class RAGConfig:
    """RAG Pipeline 配置"""
    model_name: str = "BAAI/bge-m3"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # 向量搜索配置
    vector_search_enabled: bool = True
    hybrid_search_enabled: bool = True
    semantic_search_enabled: bool = True


# 職缺推薦功能已移除


class PodwiseIntegratedConfig(BaseSettings):
    """Podwise 整合配置主類別"""
    
    # 環境配置
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # 模型配置
    models: ModelConfig = Field(default_factory=ModelConfig)
    
    # 資料庫配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # API 配置
    api: APIConfig = Field(default_factory=APIConfig)
    
    # Langfuse 配置
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    
    # 代理配置
    agents: AgentConfig = Field(default_factory=AgentConfig)
    
    # RAG 配置
    rag: RAGConfig = Field(default_factory=RAGConfig)
    
    # 職缺推薦功能已移除
    
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_from_env()
    
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
    
    def get_agent_config(self) -> Dict[str, Any]:
        """獲取代理配置"""
        return {
            "enabled": self.agents.enabled,
            "agent_1_type": self.agents.agent_1_type,
            "agent_2_type": self.agents.agent_2_type,
            "coordination_mode": self.agents.coordination_mode,
            "communication_protocol": self.agents.communication_protocol,
            "confidence_threshold": self.agents.confidence_threshold,
            "fallback_threshold": self.agents.fallback_threshold,
            "auto_decision": self.agents.auto_decision_enabled,
            "recommendation_trigger": self.agents.recommendation_trigger
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
        """打印配置摘要"""
        validation = self.validate_config()
        
        print("🔧 Podwise 整合配置摘要")
        print("=" * 60)
        print(f"環境：{self.environment}")
        print(f"除錯模式：{self.debug}")
        print(f"日誌等級：{self.log_level}")
        
        print("\n🤖 模型配置：")
        print(f"  主要 LLM：{self.models.llm_priority[0]}")
        print(f"  台灣優化：{self.models.llm_priority[1]}")
        print(f"  向量模型：{self.models.bge_m3_model}")
        print(f"  向量維度：{self.models.bge_m3_dimension}")
        
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
        print(f"  雙代理機制：{'✅' if self.agents.enabled else '❌'}")
        print(f"  職缺推薦：❌ (已移除)")
        print(f"  向量搜索：{'✅' if self.rag.vector_search_enabled else '❌'}")
        print(f"  混合搜索：{'✅' if self.rag.hybrid_search_enabled else '❌'}")
        print(f"  語義搜索：{'✅' if self.rag.semantic_search_enabled else '❌'}")
        
        print("\n🔐 安全配置狀態：")
        print(f"  Secret Key：{'✅' if validation['secret_key'] else '❌'}")
        print(f"  JWT Secret：{'✅' if validation['jwt_secret_key'] else '❌'}")


# 全域配置實例
podwise_config = PodwiseIntegratedConfig()


def get_config() -> PodwiseIntegratedConfig:
    """獲取配置實例"""
    return podwise_config


if __name__ == "__main__":
    # 測試配置
    config = get_config()
    config.print_config_summary() 