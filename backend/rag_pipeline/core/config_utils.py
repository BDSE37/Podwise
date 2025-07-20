#!/usr/bin/env python3
"""
配置工具模組

提供統一的配置導入功能，解決模組路徑問題

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def get_agent_roles_manager():
    """獲取代理人角色管理器"""
    try:
        # 添加配置目錄到路徑
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        
        from agent_roles_config import get_agent_roles_manager
        return get_agent_roles_manager()
    except ImportError as e:
        logger.warning(f"無法載入代理人角色管理器: {e}")
        return None


def get_integrated_config():
    """獲取整合配置"""
    try:
        # 添加配置目錄到路徑
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        
        from integrated_config import get_config
        return get_config()
    except ImportError as e:
        logger.warning(f"無法載入整合配置: {e}")
        return None


def get_prompt_templates():
    """獲取提示詞模板"""
    try:
        # 添加配置目錄到路徑
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        
        from prompt_templates import PodwisePromptTemplates
        return PodwisePromptTemplates()
    except ImportError as e:
        logger.warning(f"無法載入提示詞模板: {e}")
        return None


def get_tools_module(module_name: str):
    """獲取工具模組"""
    try:
        # 添加工具目錄到路徑
        tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        
        return __import__(module_name)
    except ImportError as e:
        logger.warning(f"無法載入工具模組 {module_name}: {e}")
        return None


def safe_import_config():
    """安全導入配置，返回導入狀態"""
    config_status = {
        "agent_roles_manager": get_agent_roles_manager() is not None,
        "integrated_config": get_integrated_config() is not None,
        "prompt_templates": get_prompt_templates() is not None
    }
    
    return config_status 