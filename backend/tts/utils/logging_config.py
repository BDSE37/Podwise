#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging 配置模組
"""

import logging
import colorlog
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    獲取配置好的 logger
    
    Args:
        name: logger 名稱
        level: 日誌級別，預設為 INFO
        
    Returns:
        logging.Logger: 配置好的 logger
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 設置日誌級別
    if level is None:
        level = logging.INFO
    logger.setLevel(level)
    
    # 創建 console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 設置顏色格式
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
    """
    設置全域日誌配置
    
    Args:
        level: 日誌級別
    """
    # 設置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除現有 handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加 console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 設置格式
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


if __name__ == "__main__":
    # 測試代碼
    setup_logging()
    logger = get_logger(__name__)
    
    logger.debug("這是 DEBUG 訊息")
    logger.info("這是 INFO 訊息")
    logger.warning("這是 WARNING 訊息")
    logger.error("這是 ERROR 訊息")
    logger.critical("這是 CRITICAL 訊息") 