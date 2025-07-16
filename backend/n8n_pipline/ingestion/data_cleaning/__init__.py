#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Cleaning Package Initialization

統一導入核心模組、清理器 Orchestrator 及常用 API
"""

# 核心清理器
from .core.unified_cleaner import UnifiedCleaner

# Orchestrator 入口
from .services.cleaner_orchestrator import CleanerOrchestrator

# 便利執行 script
from .unified_cleanup_script import main as unified_cleanup

__all__ = [
    'UnifiedCleaner',
    'CleanerOrchestrator',
    'unified_cleanup',
]
