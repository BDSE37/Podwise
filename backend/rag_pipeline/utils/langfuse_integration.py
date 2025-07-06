#!/usr/bin/env python3
"""
Langfuse 整合模組

提供 Langfuse 追蹤和監控功能，用於 AB testing 和性能分析。

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from langfuse import Langfuse
    from langfuse.model import CreateTrace, CreateSpan
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    CreateTrace = None
    CreateSpan = None

logger = logging.getLogger(__name__)


@dataclass
class LangfuseConfig:
    """Langfuse 配置"""
    public_key: str
    secret_key: str
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True
    trace_thinking_process: bool = True
    trace_model_selection: bool = True
    trace_agent_interactions: bool = True
    trace_vector_search: bool = True


class LangfuseManager:
    """Langfuse 管理器"""
    
    def __init__(self, config: LangfuseConfig):
        """初始化 Langfuse 管理器"""
        self.config = config
        self.client = None
        self.is_initialized = False
        
        if not LANGFUSE_AVAILABLE:
            logger.warning("⚠️ Langfuse 未安裝，追蹤功能將被禁用")
            self.config.enabled = False
    
    async def initialize(self) -> None:
        """初始化 Langfuse 客戶端"""
        if not self.config.enabled or not LANGFUSE_AVAILABLE:
            logger.info("Langfuse 追蹤已禁用")
            return
        
        try:
            self.client = Langfuse(
                public_key=self.config.public_key,
                secret_key=self.config.secret_key,
                host=self.config.host
            )
            
            # 測試連接
            await self.client.auth_check()
            self.is_initialized = True
            logger.info("✅ Langfuse 初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Langfuse 初始化失敗: {e}")
            self.config.enabled = False
    
    async def start_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        開始追蹤
        
        Args:
            name: 追蹤名稱
            metadata: 元數據
            
        Returns:
            追蹤物件
        """
        if not self.is_initialized or not self.config.enabled:
            return None
        
        try:
            trace = self.client.trace(
                name=name,
                metadata=metadata or {}
            )
            return trace
            
        except Exception as e:
            logger.error(f"❌ 開始追蹤失敗: {e}")
            return None
    
    async def end_trace(
        self,
        trace: Any,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        結束追蹤
        
        Args:
            trace: 追蹤物件
            output: 輸出結果
            error: 錯誤訊息
            metadata: 元數據
        """
        if not trace or not self.is_initialized:
            return
        
        try:
            if error:
                trace.update(
                    status_message=error,
                    metadata=metadata or {}
                )
            else:
                trace.update(
                    output=output,
                    metadata=metadata or {}
                )
            
            await trace.flush()
            
        except Exception as e:
            logger.error(f"❌ 結束追蹤失敗: {e}")
    
    async def create_span(
        self,
        trace: Any,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        創建 span
        
        Args:
            trace: 追蹤物件
            name: span 名稱
            input_data: 輸入資料
            output_data: 輸出資料
            metadata: 元數據
            
        Returns:
            span 物件
        """
        if not trace or not self.is_initialized:
            return None
        
        try:
            span = trace.span(
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata or {}
            )
            return span
            
        except Exception as e:
            logger.error(f"❌ 創建 span 失敗: {e}")
            return None
    
    async def track_model_usage(
        self,
        trace: Any,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        追蹤模型使用情況
        
        Args:
            trace: 追蹤物件
            model_name: 模型名稱
            input_tokens: 輸入 token 數
            output_tokens: 輸出 token 數
            cost: 成本
            metadata: 元數據
        """
        if not self.config.trace_model_selection or not trace:
            return
        
        try:
            span = await self.create_span(
                trace=trace,
                name=f"model_usage_{model_name}",
                input_data={"input_tokens": input_tokens},
                output_data={"output_tokens": output_tokens},
                metadata={
                    "model_name": model_name,
                    "cost": cost,
                    **(metadata or {})
                }
            )
            
            if span:
                await span.flush()
                
        except Exception as e:
            logger.error(f"❌ 追蹤模型使用失敗: {e}")
    
    async def track_agent_interaction(
        self,
        trace: Any,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence: float,
        processing_time: float
    ) -> None:
        """
        追蹤代理人互動
        
        Args:
            trace: 追蹤物件
            agent_name: 代理人名稱
            input_data: 輸入資料
            output_data: 輸出資料
            confidence: 信心度
            processing_time: 處理時間
        """
        if not self.config.trace_agent_interactions or not trace:
            return
        
        try:
            span = await self.create_span(
                trace=trace,
                name=f"agent_{agent_name}",
                input_data=input_data,
                output_data=output_data,
                metadata={
                    "agent_name": agent_name,
                    "confidence": confidence,
                    "processing_time": processing_time
                }
            )
            
            if span:
                await span.flush()
                
        except Exception as e:
            logger.error(f"❌ 追蹤代理人互動失敗: {e}")
    
    async def track_vector_search(
        self,
        trace: Any,
        query: str,
        results_count: int,
        search_time: float,
        top_k: int,
        similarity_threshold: float
    ) -> None:
        """
        追蹤向量搜尋
        
        Args:
            trace: 追蹤物件
            query: 查詢內容
            results_count: 結果數量
            search_time: 搜尋時間
            top_k: 返回數量
            similarity_threshold: 相似度閾值
        """
        if not self.config.trace_vector_search or not trace:
            return
        
        try:
            span = await self.create_span(
                trace=trace,
                name="vector_search",
                input_data={"query": query, "top_k": top_k},
                output_data={"results_count": results_count},
                metadata={
                    "search_time": search_time,
                    "similarity_threshold": similarity_threshold
                }
            )
            
            if span:
                await span.flush()
                
        except Exception as e:
            logger.error(f"❌ 追蹤向量搜尋失敗: {e}")
    
    async def close(self) -> None:
        """關閉 Langfuse 連接"""
        if self.client:
            try:
                await self.client.flush()
                logger.info("✅ Langfuse 連接已關閉")
            except Exception as e:
                logger.error(f"❌ 關閉 Langfuse 連接失敗: {e}")


def get_langfuse_manager(config: LangfuseConfig) -> LangfuseManager:
    """獲取 Langfuse 管理器實例"""
    return LangfuseManager(config) 