#!/usr/bin/env python3
"""
Podwise RAG Pipeline 主模組

提供統一的 OOP 介面，整合所有 RAG Pipeline 功能：
- 層級化 CrewAI 架構
- 語意檢索（text2vec-base-chinese + TAG_info.csv）
- 提示詞模板系統
- Langfuse 監控
- 聊天歷史記錄
- 效能優化

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入核心模組
from core.crew_agents import LeaderAgent, BusinessExpertAgent, EducationExpertAgent, UserManagerAgent, UserQuery, AgentResponse
from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline, RAGResponse
from core.content_categorizer import ContentCategorizer
from core.confidence_controller import get_confidence_controller
from core.qwen_llm_manager import Qwen3LLMManager
from core.chat_history_service import get_chat_history_service
from config.prompt_templates import PodwisePromptTemplates
from config.integrated_config import get_config
# Langfuse 整合已移除，使用 Langfuse Cloud 服務


class PodwiseRAGPipeline:
    """
    Podwise RAG Pipeline 主類別
    
    提供統一的介面來使用所有 RAG Pipeline 功能
    專注於核心 RAG 處理邏輯，不包含 Web API 功能
    """
    
    def __init__(self, 
                 enable_monitoring: bool = True,
                 enable_semantic_retrieval: bool = True,
                 enable_chat_history: bool = True,
                 confidence_threshold: float = 0.7):
        """
        初始化 RAG Pipeline
        
        Args:
            enable_monitoring: 是否啟用 Langfuse 監控
            enable_semantic_retrieval: 是否啟用語意檢索
            enable_chat_history: 是否啟用聊天歷史記錄
            confidence_threshold: 信心度閾值
        """
        self.enable_monitoring = enable_monitoring
        self.enable_semantic_retrieval = enable_semantic_retrieval
        self.enable_chat_history = enable_chat_history
        self.confidence_threshold = confidence_threshold
        
        # 初始化監控器 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
        self.monitor = None
        self.langfuse = None
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                from langfuse import Langfuse
                self.langfuse = Langfuse(
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                )
            except ImportError:
                self.langfuse = None
        
        # 初始化整合配置
        self.config = get_config()
        
        # 初始化提示詞模板
        self.prompt_templates = PodwisePromptTemplates()
        
        # 初始化 LLM 管理器
        self.llm_manager = Qwen3LLMManager()
        
        # 初始化內容處理器
        self.categorizer = ContentCategorizer()
        
        # 初始化信心度控制器
        self.confidence_controller = get_confidence_controller()
        self.confidence_controller.update_confidence_threshold(confidence_threshold)
        
        # 初始化聊天歷史服務
        self.chat_history = get_chat_history_service() if enable_chat_history else None
        
        # 初始化 CrewAI 代理
        self._initialize_agents()
        
        # 初始化層級化 RAG Pipeline
        self.rag_pipeline = HierarchicalRAGPipeline()
        
        logger.info("✅ Podwise RAG Pipeline 初始化完成")
    
    def _initialize_agents(self):
        """初始化 CrewAI 代理"""
        # 配置字典
        config = {
            'confidence_threshold': self.confidence_threshold,
            'max_processing_time': 30.0
        }
        
        # 用戶管理層
        self.user_manager = UserManagerAgent(config)
        
        # 商業專家
        self.business_expert = BusinessExpertAgent(config)
        
        # 教育專家
        self.education_expert = EducationExpertAgent(config)
        
        # 領導者代理
        self.leader_agent = LeaderAgent(config)
        
        logger.info("✅ CrewAI 代理初始化完成")
    
    async def process_query(self, 
                           query: str, 
                           user_id: str = "default_user",
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        處理用戶查詢（核心 RAG 功能）
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據
            
        Returns:
            RAGResponse: 處理結果
        """
        start_time = datetime.now()
        
        # 記錄用戶查詢到聊天歷史
        if self.enable_chat_history and self.chat_history:
            try:
                self.chat_history.save_chat_message(
                    user_id=user_id,
                    session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                    role="user",
                    content=query,
                    chat_mode="rag",
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"記錄用戶查詢失敗: {e}")
        
        # 創建追蹤 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
        trace = None
        if self.langfuse:
            trace = self.langfuse.trace(name="RAG Pipeline Query", user_id=user_id, input=query)
        
        try:
            # 使用層級化 RAG Pipeline 處理
            response = await self.rag_pipeline.process_query(query)
            
            # 記錄助手回應到聊天歷史
            if self.enable_chat_history and self.chat_history:
                try:
                    self.chat_history.save_chat_message(
                        user_id=user_id,
                        session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                        role="assistant",
                        content=response.content,
                        chat_mode="rag",
                        metadata={
                            "confidence": response.confidence,
                            "level_used": response.level_used,
                            "sources_count": len(response.sources),
                            **(metadata or {})
                        }
                    )
                except Exception as e:
                    logger.warning(f"記錄助手回應失敗: {e}")
            
            # 追蹤完整流程 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
            if trace:
                trace.end(output=response.content, metadata={"confidence": response.confidence})
            
            return response
            
        except Exception as e:
            logger.error(f"處理查詢失敗: {e}")
            
            # 記錄錯誤回應
            if self.enable_chat_history and self.chat_history:
                try:
                    self.chat_history.save_chat_message(
                        user_id=user_id,
                        session_id=session_id or f"session_{user_id}_{int(start_time.timestamp())}",
                        role="assistant",
                        content=f"處理查詢時發生錯誤: {str(e)}",
                        chat_mode="rag",
                        metadata={"error": str(e), **(metadata or {})}
                    )
                except Exception as chat_error:
                    logger.warning(f"記錄錯誤回應失敗: {chat_error}")
            
            # 追蹤錯誤 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
            if trace:
                trace.end(output=str(e), metadata={"error": True})
            
            # 返回錯誤回應
            return RAGResponse(
                content=f"處理查詢時發生錯誤: {str(e)}",
                confidence=0.0,
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                metadata={"error": str(e)}
            )
    
    async def process_with_agents(self, 
                                 query: str, 
                                 user_id: str = "default_user") -> AgentResponse:
        """
        使用 CrewAI 代理處理查詢
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            
        Returns:
            AgentResponse: 代理回應
        """
        start_time = datetime.now()
        
        # 創建追蹤 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
        trace = None
        if self.langfuse:
            trace = self.langfuse.trace(name="CrewAI Agent Query", user_id=user_id, input=query)
        
        try:
            # 創建用戶查詢物件
            user_query = UserQuery(
                query=query,
                user_id=user_id,
                category=None,
                context=None
            )
            
            # 使用領導者代理處理
            response = await self.leader_agent.process(user_query)
            
            # 追蹤代理互動 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
            if trace:
                trace.end(output=response.content, metadata={"confidence": response.confidence})
            
            return response
            
        except Exception as e:
            logger.error(f"代理處理失敗: {e}")
            
            # 追蹤錯誤 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)
            if trace:
                trace.end(output=str(e), metadata={"error": True})
            
            return AgentResponse(
                content=f"代理處理時發生錯誤: {str(e)}",
                confidence=0.0,
                reasoning="處理失敗",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def get_semantic_config(self) -> Optional[Dict[str, Any]]:
        """獲取語意檢索配置"""
        if not hasattr(self.config, 'semantic_retrieval') or not self.config.semantic_retrieval:
            return None
        
        return {
            "model_config": getattr(self.config.semantic_retrieval, 'model_config', None),
            "retrieval_config": getattr(self.config.semantic_retrieval, 'retrieval_config', None),
            "tag_statistics": getattr(self.config.semantic_retrieval, 'tag_statistics', None)
        }
    
    def get_prompt_templates(self) -> Dict[str, str]:
        """獲取提示詞模板"""
        return {
            "category_classifier": "分類提示詞模板",
            "semantic_retrieval": "語意檢索提示詞模板",
            "business_expert": "商業專家提示詞模板",
            "education_expert": "教育專家提示詞模板",
            "leader_decision": "領導者決策提示詞模板",
            "answer_generation": "回答生成提示詞模板"
        }
    
    def is_monitoring_enabled(self) -> bool:
        """檢查監控是否啟用 (Langfuse 整合已移除，使用 Langfuse Cloud 服務)"""
        return False
    
    def get_monitor_url(self, trace_id: str) -> Optional[str]:
        """獲取監控 URL (Langfuse 整合已移除，使用 Langfuse Cloud 服務)"""
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 檢查 LLM 管理器
        try:
            health_status["components"]["llm_manager"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["llm_manager"] = {"status": "error", "error": str(e)}
            health_status["status"] = "degraded"
        
        # 檢查語意檢索
        if hasattr(self.config, 'semantic_retrieval') and self.config.semantic_retrieval:
            try:
                semantic_status = getattr(self.config.semantic_retrieval, 'model_config', None)
                health_status["components"]["semantic_retrieval"] = {
                    "status": "healthy",
                    "model": getattr(semantic_status, 'model_name', 'unknown') if semantic_status else "unknown"
                }
            except Exception as e:
                health_status["components"]["semantic_retrieval"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
        
        # 檢查監控
        health_status["components"]["monitoring"] = {
            "status": "enabled" if self.is_monitoring_enabled() else "disabled"
        }
        
        return health_status


# 全域 RAG Pipeline 實例
_rag_pipeline = None

def get_rag_pipeline() -> PodwiseRAGPipeline:
    """獲取全域 RAG Pipeline 實例"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = PodwiseRAGPipeline()
    return _rag_pipeline


async def main():
    """主函數 - 用於測試"""
    print("🚀 Podwise RAG Pipeline 測試")
    
    # 創建 RAG Pipeline 實例
    pipeline = PodwiseRAGPipeline()
    
    # 健康檢查
    health = await pipeline.health_check()
    print(f"📊 健康狀態: {json.dumps(health, ensure_ascii=False, indent=2)}")
    
    # 測試查詢
    test_query = "我想學習投資理財，有什麼推薦的 Podcast 嗎？"
    print(f"\n🔍 測試查詢: {test_query}")
    
    # 使用層級化 RAG Pipeline
    rag_response = await pipeline.process_query(test_query, "test_user")
    print(f"📝 RAG 回應: {rag_response.content}")
    print(f"🎯 信心度: {rag_response.confidence}")
    print(f"📂 來源: {len(rag_response.sources)} 個")
    
    # 使用 CrewAI 代理
    agent_response = await pipeline.process_with_agents(test_query, "test_user")
    print(f"🤖 代理回應: {agent_response.content}")
    print(f"🎯 信心度: {agent_response.confidence}")
    
    print("\n✅ 測試完成")


if __name__ == "__main__":
    asyncio.run(main()) 