#!/usr/bin/env python3
"""
Langfuse 整合模組
用於監控 LLM 思考過程、模型選擇、代理互動和向量搜尋
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# 嘗試導入 Langfuse
try:
    from langfuse import Langfuse
    from langfuse.model import CreateTrace, CreateSpan, CreateGeneration
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logging.warning("Langfuse 未安裝，監控功能將不可用")

logger = logging.getLogger(__name__)

class LangfuseMonitor:
    """Langfuse 監控器"""
    
    def __init__(self, 
                 public_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 host: str = "https://cloud.langfuse.com"):
        """
        初始化 Langfuse 監控器
        
        Args:
            public_key: Langfuse 公鑰
            secret_key: Langfuse 私鑰
            host: Langfuse 主機地址
        """
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        self.langfuse = None
        self.enabled = False
        
        self._initialize_langfuse()
    
    def _initialize_langfuse(self):
        """初始化 Langfuse 客戶端"""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse 套件未安裝")
            return
        
        if not self.public_key or not self.secret_key:
            logger.warning("Langfuse 金鑰未設定")
            return
        
        try:
            self.langfuse = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host
            )
            self.enabled = True
            logger.info("✅ Langfuse 監控器初始化成功")
        except Exception as e:
            logger.error(f"❌ Langfuse 初始化失敗: {e}")
            self.enabled = False
    
    def create_trace(self, 
                    name: str,
                    user_id: str,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        創建追蹤
        
        Args:
            name: 追蹤名稱
            user_id: 用戶 ID
            metadata: 元數據
            
        Returns:
            Optional[str]: 追蹤 ID
        """
        if not self.enabled or not self.langfuse:
            return None
        
        try:
            trace = self.langfuse.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {}
            )
            return trace.id
        except Exception as e:
            logger.error(f"創建追蹤失敗: {e}")
            return None
    
    def trace_thinking_process(self,
                              trace_id: str,
                              query: str,
                              thinking_steps: List[Dict[str, Any]],
                              final_decision: str) -> bool:
        """
        追蹤思考過程
        
        Args:
            trace_id: 追蹤 ID
            query: 用戶查詢
            thinking_steps: 思考步驟
            final_decision: 最終決策
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            # 創建思考過程 span
            span = self.langfuse.span(
                trace_id=trace_id,
                name="思考過程分析",
                input={
                    "query": query,
                    "thinking_steps": thinking_steps
                },
                output={
                    "final_decision": final_decision,
                    "steps_count": len(thinking_steps)
                },
                metadata={
                    "process_type": "thinking_analysis",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # 記錄每個思考步驟
            for i, step in enumerate(thinking_steps):
                self.langfuse.span(
                    trace_id=trace_id,
                    name=f"思考步驟 {i+1}",
                    input=step.get("input", {}),
                    output=step.get("output", {}),
                    metadata={
                        "step_number": i + 1,
                        "step_type": step.get("type", "unknown"),
                        "confidence": step.get("confidence", 0.0)
                    }
                )
            
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤思考過程失敗: {e}")
            return False
    
    def trace_model_selection(self,
                             trace_id: str,
                             available_models: List[str],
                             selected_model: str,
                             selection_reason: str,
                             performance_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        追蹤模型選擇過程
        
        Args:
            trace_id: 追蹤 ID
            available_models: 可用模型列表
            selected_model: 選擇的模型
            selection_reason: 選擇原因
            performance_metrics: 效能指標
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            span = self.langfuse.span(
                trace_id=trace_id,
                name="模型選擇",
                input={
                    "available_models": available_models,
                    "selection_criteria": "confidence_and_performance"
                },
                output={
                    "selected_model": selected_model,
                    "selection_reason": selection_reason,
                    "performance_metrics": performance_metrics or {}
                },
                metadata={
                    "process_type": "model_selection",
                    "models_count": len(available_models),
                    "timestamp": datetime.now().isoformat()
                }
            )
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤模型選擇失敗: {e}")
            return False
    
    def trace_agent_interactions(self,
                                trace_id: str,
                                agent_name: str,
                                agent_role: str,
                                input_data: Any,
                                output_data: Any,
                                confidence: float,
                                processing_time: float) -> bool:
        """
        追蹤代理互動
        
        Args:
            trace_id: 追蹤 ID
            agent_name: 代理名稱
            agent_role: 代理角色
            input_data: 輸入數據
            output_data: 輸出數據
            confidence: 信心值
            processing_time: 處理時間
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            span = self.langfuse.span(
                trace_id=trace_id,
                name=f"代理互動: {agent_name}",
                input={
                    "agent_role": agent_role,
                    "input_data": input_data
                },
                output={
                    "output_data": output_data,
                    "confidence": confidence,
                    "processing_time": processing_time
                },
                metadata={
                    "agent_name": agent_name,
                    "agent_role": agent_role,
                    "confidence": confidence,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤代理互動失敗: {e}")
            return False
    
    def trace_vector_search(self,
                           trace_id: str,
                           query: str,
                           search_results: List[Dict[str, Any]],
                           search_config: Dict[str, Any],
                           processing_time: float) -> bool:
        """
        追蹤向量搜尋
        
        Args:
            trace_id: 追蹤 ID
            query: 搜尋查詢
            search_results: 搜尋結果
            search_config: 搜尋配置
            processing_time: 處理時間
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            span = self.langfuse.span(
                trace_id=trace_id,
                name="向量搜尋",
                input={
                    "query": query,
                    "search_config": search_config
                },
                output={
                    "results_count": len(search_results),
                    "top_results": search_results[:3] if search_results else [],
                    "processing_time": processing_time
                },
                metadata={
                    "search_type": "vector_search",
                    "results_count": len(search_results),
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤向量搜尋失敗: {e}")
            return False
    
    def trace_semantic_retrieval(self,
                                trace_id: str,
                                query: str,
                                semantic_score: float,
                                tag_matches: List[Dict[str, Any]],
                                hybrid_score: float,
                                final_results: List[Dict[str, Any]]) -> bool:
        """
        追蹤語意檢索（整合 text2vec-base-chinese 和 TAG_info.csv）
        
        Args:
            trace_id: 追蹤 ID
            query: 查詢
            semantic_score: 語意分數
            tag_matches: 標籤匹配
            hybrid_score: 混合分數
            final_results: 最終結果
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            span = self.langfuse.span(
                trace_id=trace_id,
                name="語意檢索",
                input={
                    "query": query,
                    "model": "text2vec-base-chinese",
                    "tag_source": "TAG_info.csv"
                },
                output={
                    "semantic_score": semantic_score,
                    "tag_matches_count": len(tag_matches),
                    "hybrid_score": hybrid_score,
                    "final_results_count": len(final_results),
                    "top_matches": tag_matches[:3] if tag_matches else []
                },
                metadata={
                    "retrieval_type": "semantic_hybrid",
                    "semantic_weight": 0.7,
                    "tag_weight": 0.3,
                    "confidence_threshold": 0.7,
                    "timestamp": datetime.now().isoformat()
                }
            )
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤語意檢索失敗: {e}")
            return False
    
    def trace_rag_pipeline(self,
                          trace_id: str,
                          query: str,
                          category: str,
                          rag_results: Dict[str, Any],
                          final_response: str,
                          confidence: float,
                          processing_time: float) -> bool:
        """
        追蹤完整 RAG Pipeline
        
        Args:
            trace_id: 追蹤 ID
            query: 用戶查詢
            category: 分類結果
            rag_results: RAG 結果
            final_response: 最終回應
            confidence: 信心值
            processing_time: 處理時間
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            # 創建 RAG Pipeline span
            span = self.langfuse.span(
                trace_id=trace_id,
                name="RAG Pipeline 處理",
                input={
                    "query": query,
                    "category": category
                },
                output={
                    "final_response": final_response,
                    "confidence": confidence,
                    "processing_time": processing_time
                },
                metadata={
                    "pipeline_type": "hierarchical_rag",
                    "category": category,
                    "confidence": confidence,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # 記錄子步驟
            if "rag_result" in rag_results:
                self.langfuse.span(
                    trace_id=trace_id,
                    name="RAG 檢索",
                    input={"query": query},
                    output={"results": rag_results["rag_result"]},
                    metadata={"step": "rag_retrieval"}
                )
            
            if "category_result" in rag_results:
                self.langfuse.span(
                    trace_id=trace_id,
                    name="類別分析",
                    input={"query": query},
                    output={"category": category},
                    metadata={"step": "category_analysis"}
                )
            
            span.end()
            return True
            
        except Exception as e:
            logger.error(f"追蹤 RAG Pipeline 失敗: {e}")
            return False
    
    def end_trace(self, trace_id: str, status: str = "success") -> bool:
        """
        結束追蹤
        
        Args:
            trace_id: 追蹤 ID
            status: 狀態
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.langfuse:
            return False
        
        try:
            self.langfuse.trace(id=trace_id).update(status=status)
            return True
        except Exception as e:
            logger.error(f"結束追蹤失敗: {e}")
            return False
    
    def get_trace_url(self, trace_id: str) -> str:
        """
        獲取追蹤 URL
        
        Args:
            trace_id: 追蹤 ID
            
        Returns:
            str: 追蹤 URL
        """
        return f"{self.host}/traces/{trace_id}"
    
    def is_enabled(self) -> bool:
        """檢查是否啟用"""
        return self.enabled

# 全域 Langfuse 監控器實例
_langfuse_monitor = None

def get_langfuse_monitor() -> LangfuseMonitor:
    """獲取 Langfuse 監控器實例"""
    global _langfuse_monitor
    if _langfuse_monitor is None:
        _langfuse_monitor = LangfuseMonitor()
    return _langfuse_monitor 