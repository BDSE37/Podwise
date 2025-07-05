#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PodWise Backend 共用工具套件

提供跨模組共用的工具函數和配置管理。

Author: Podri Team
License: MIT
"""

from .logging_config import get_logger
from .common_utils import (
    DictToAttrRecursive,
    clean_path,
    normalize_text,
    safe_get,
    ensure_directory,
    validate_file_path,
    get_file_extension,
    format_file_size,
    create_logger,
    retry_on_failure,
    is_empty,
    remove_duplicates
)
from .env_config import PodriConfig, config
from .langfuse_client import langfuse
from .audio_search import IntelligentAudioSearch
from .core_services import BaseService, ServiceManager, ModelService, ServiceConfig, ServiceResponse

__version__ = "1.0.0"
__author__ = "Podri Team"

# 便捷的 import 介面
__all__ = [
    # 日誌工具
    "get_logger",
    
    # 通用工具
    "DictToAttrRecursive",
    "clean_path",
    "normalize_text",
    "safe_get",
    "ensure_directory",
    "validate_file_path",
    "get_file_extension",
    "format_file_size",
    "create_logger",
    "retry_on_failure",
    "is_empty",
    "remove_duplicates",
    
    # 配置管理
    "PodriConfig",
    "config",
    
    # Langfuse 客戶端
    "langfuse",

    # 智能音訊搜尋
    "IntelligentAudioSearch",
    "BaseService",
    "ServiceManager",
    "ModelService",
    "ServiceConfig",
    "ServiceResponse"
] 