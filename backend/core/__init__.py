#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise Core 模組
提供核心服務和功能
"""

from .podwise_service_manager import PodwiseServiceManager, podwise_service

# 從 RAG Pipeline 導入核心組件
try:
    from ..rag_pipeline.core import HierarchicalRAGPipeline
    __all__ = ['PodwiseServiceManager', 'podwise_service', 'HierarchicalRAGPipeline']
except ImportError:
    # 如果無法導入，創建一個虛擬類別
    class HierarchicalRAGPipeline:
        def __init__(self):
            pass
    __all__ = ['PodwiseServiceManager', 'podwise_service', 'HierarchicalRAGPipeline'] 