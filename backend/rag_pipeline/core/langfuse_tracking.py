#!/usr/bin/env python3
"""
Podwise RAG Pipeline - Langfuse Cloud 追蹤工具

提供 Langfuse Cloud 整合，用於追蹤：
- 查詢處理流程
- MCP 工具調用
- 推薦結果生成
- 異常處理
- 效能指標

作者: Podwise Team
版本: 1.0.0
"""

import os
import json
import time
import logging
import asyncio
from functools import wraps
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

# 嘗試導入 Langfuse
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("Langfuse 未安裝，追蹤功能將被禁用")
    # 定義一個假的 Langfuse 類別以避免 linter 錯誤
    class Langfuse:
        def __init__(self, **kwargs):
            pass
        def trace(self, **kwargs):
            return None


class LangfuseTracker:
    """Langfuse 追蹤器"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 Langfuse 客戶端"""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse 未安裝，追蹤功能禁用")
            return
        
        try:
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if not public_key or not secret_key:
                logger.warning("Langfuse 金鑰未設定，追蹤功能禁用")
                return
            
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            self.enabled = True
            logger.info("✅ Langfuse 追蹤器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Langfuse 初始化失敗: {e}")
            self.enabled = False
    
    def trace_query(self, query: str, user_id: str, metadata: Optional[Dict[str, Any]] = None):
        """追蹤查詢處理"""
        if not self.enabled or not self.client:
            return
        
        try:
            trace = self.client.trace(
                name="RAG Query Processing",
                metadata={
                    "query": query,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            )
            return trace
        except Exception as e:
            logger.error(f"查詢追蹤失敗: {e}")
            return None
    
    def trace_tool_call(self, tool_name: str, arguments: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """追蹤工具調用"""
        if not self.enabled or not self.client:
            return
        
        try:
            trace = self.client.trace(
                name=f"MCP Tool: {tool_name}",
                metadata={
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            )
            return trace
        except Exception as e:
            logger.error(f"工具調用追蹤失敗: {e}")
            return None
    
    def trace_recommendation(self, query: str, results_count: int, metadata: Optional[Dict[str, Any]] = None):
        """追蹤推薦結果"""
        if not self.enabled or not self.client:
            return
        
        try:
            trace = self.client.trace(
                name="Podcast Recommendation",
                metadata={
                    "query": query,
                    "results_count": results_count,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            )
            return trace
        except Exception as e:
            logger.error(f"推薦追蹤失敗: {e}")
            return None
    
    def log_success(self, trace, result: Any, processing_time: float):
        """記錄成功結果"""
        if not self.enabled or not trace:
            return
        
        try:
            trace.update(
                status="success",
                metadata={
                    "result": str(result)[:500],  # 限制長度
                    "processing_time": processing_time
                }
            )
        except Exception as e:
            logger.error(f"成功記錄失敗: {e}")
    
    def log_error(self, trace, error: Exception, processing_time: float):
        """記錄錯誤"""
        if not self.enabled or not trace:
            return
        
        try:
            trace.update(
                status="error",
                metadata={
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "traceback": traceback.format_exc(),
                    "processing_time": processing_time
                }
            )
        except Exception as e:
            logger.error(f"錯誤記錄失敗: {e}")


# 全局追蹤器實例
_tracker = None

def get_langfuse_tracker() -> LangfuseTracker:
    """獲取 Langfuse 追蹤器實例（單例模式）"""
    global _tracker
    if _tracker is None:
        _tracker = LangfuseTracker()
    return _tracker


def langfuse_trace(event_type: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Langfuse 追蹤裝飾器
    
    Args:
        event_type: 事件類型 ("query", "tool_call", "recommendation")
        metadata: 額外元數據
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = get_langfuse_tracker()
            start_time = time.time()
            trace = None
            
            try:
                # 根據事件類型創建追蹤
                if event_type == "query":
                    # 從參數中提取查詢資訊
                    query = kwargs.get('query') or (args[0].query if args else "")
                    user_id = kwargs.get('user_id') or (args[0].user_id if args else "")
                    trace = tracker.trace_query(query, user_id, metadata)
                
                elif event_type == "tool_call":
                    # 從參數中提取工具資訊
                    tool_name = kwargs.get('tool_name') or args[0] if args else ""
                    arguments = kwargs.get('arguments') or args[1] if len(args) > 1 else {}
                    trace = tracker.trace_tool_call(tool_name, arguments, metadata)
                
                elif event_type == "recommendation":
                    # 從參數中提取推薦資訊
                    query = kwargs.get('query') or args[0] if args else ""
                    trace = tracker.trace_recommendation(query, 0, metadata)
                
                # 執行原函數
                result = await func(*args, **kwargs)
                
                # 記錄成功
                processing_time = time.time() - start_time
                tracker.log_success(trace, result, processing_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                processing_time = time.time() - start_time
                tracker.log_error(trace, e, processing_time)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracker = get_langfuse_tracker()
            start_time = time.time()
            trace = None
            
            try:
                # 根據事件類型創建追蹤
                if event_type == "query":
                    query = kwargs.get('query') or (args[0].query if args else "")
                    user_id = kwargs.get('user_id') or (args[0].user_id if args else "")
                    trace = tracker.trace_query(query, user_id, metadata)
                
                elif event_type == "tool_call":
                    tool_name = kwargs.get('tool_name') or args[0] if args else ""
                    arguments = kwargs.get('arguments') or args[1] if len(args) > 1 else {}
                    trace = tracker.trace_tool_call(tool_name, arguments, metadata)
                
                elif event_type == "recommendation":
                    query = kwargs.get('query') or args[0] if args else ""
                    trace = tracker.trace_recommendation(query, 0, metadata)
                
                # 執行原函數
                result = func(*args, **kwargs)
                
                # 記錄成功
                processing_time = time.time() - start_time
                tracker.log_success(trace, result, processing_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                processing_time = time.time() - start_time
                tracker.log_error(trace, e, processing_time)
                raise
        
        # 根據函數類型返回對應的包裝器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def LangfuseTraceContext(event_type: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Langfuse 追蹤上下文管理器
    
    Args:
        event_type: 事件類型
        metadata: 額外元數據
    """
    tracker = get_langfuse_tracker()
    start_time = time.time()
    trace = None
    
    try:
        # 創建追蹤
        if event_type == "query":
            trace = tracker.trace_query("", "", metadata)
        elif event_type == "tool_call":
            trace = tracker.trace_tool_call("", {}, metadata)
        elif event_type == "recommendation":
            trace = tracker.trace_recommendation("", 0, metadata)
        
        yield trace
        
        # 記錄成功
        processing_time = time.time() - start_time
        tracker.log_success(trace, "Context completed", processing_time)
        
    except Exception as e:
        # 記錄錯誤
        processing_time = time.time() - start_time
        tracker.log_error(trace, e, processing_time)
        raise


def trace_function_call(func_name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    追蹤函數調用的簡化裝飾器
    
    Args:
        func_name: 函數名稱
        metadata: 額外元數據
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = get_langfuse_tracker()
            start_time = time.time()
            
            try:
                # 創建追蹤
                trace = None
                if tracker.enabled and tracker.client:
                    trace = tracker.client.trace(
                        name=func_name,
                        metadata={
                            "args": str(args)[:200],
                            "kwargs": str(kwargs)[:200],
                            "timestamp": datetime.now().isoformat(),
                            **(metadata or {})
                        }
                    )
                
                # 執行原函數
                result = await func(*args, **kwargs)
                
                # 記錄成功
                if trace:
                    processing_time = time.time() - start_time
                    tracker.log_success(trace, result, processing_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                if trace:
                    processing_time = time.time() - start_time
                    tracker.log_error(trace, e, processing_time)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracker = get_langfuse_tracker()
            start_time = time.time()
            
            try:
                # 創建追蹤
                trace = None
                if tracker.enabled and tracker.client:
                    trace = tracker.client.trace(
                        name=func_name,
                        metadata={
                            "args": str(args)[:200],
                            "kwargs": str(kwargs)[:200],
                            "timestamp": datetime.now().isoformat(),
                            **(metadata or {})
                        }
                    )
                
                # 執行原函數
                result = func(*args, **kwargs)
                
                # 記錄成功
                if trace:
                    processing_time = time.time() - start_time
                    tracker.log_success(trace, result, processing_time)
                
                return result
                
            except Exception as e:
                # 記錄錯誤
                if trace:
                    processing_time = time.time() - start_time
                    tracker.log_error(trace, e, processing_time)
                raise
        
        # 根據函數類型返回對應的包裝器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 導出接口
__all__ = [
    'LangfuseTracker',
    'get_langfuse_tracker',
    'langfuse_trace',
    'LangfuseTraceContext',
    'trace_function_call'
] 