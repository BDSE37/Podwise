#!/usr/bin/env python3
"""
Podwise RAG Pipeline 模組

整合三層 CrewAI 架構、智能 TAG 提取、向量搜尋、Web Search 備援等功能。

作者: Podwise Team
版本: 3.0.0
"""

from .main import (
    RAGPipelineManager,
    get_rag_pipeline_manager,
    close_rag_pipeline_manager,
    run_fastapi_app
)

__version__ = "3.0.0"
__author__ = "Podwise Team"

__all__ = [
    "RAGPipelineManager",
    "get_rag_pipeline_manager", 
    "close_rag_pipeline_manager",
    "run_fastapi_app"
] 