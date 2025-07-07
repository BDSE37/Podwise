#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri 日誌配置模組

提供統一的日誌配置和格式化功能。

Author: Podri Team
License: MIT
"""

import logging
import colorlog
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """獲取配置好的日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別，預設為 INFO
        
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    logger = logging.getLogger(name)
    
    # 如果已經配置過，直接返回
    if logger.handlers:
        return logger
    
    # 設定日誌級別
    log_level = level or logging.INFO
    logger.setLevel(log_level)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 創建彩色日誌格式
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def setup_logging(level: int = logging.INFO) -> None:
    """設定全域日誌配置
    
    Args:
        level: 全域日誌級別
    """
    # 設定根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除現有處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 創建格式化器
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


# 預設設定
setup_logging() 