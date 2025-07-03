#!/usr/bin/env python3
"""
Podwise 共用工具模組
解決重複代碼問題，提供統一的工具函數
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DictToAttrRecursive(dict):
    """
    統一的字典到屬性轉換類別
    解決多個檔案中重複定義的問題
    """
    
    def __init__(self, input_dict: Dict[str, Any]):
        """
        初始化字典到屬性轉換器
        
        Args:
            input_dict: 輸入字典
        """
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

    def __getattr__(self, item: str) -> Any:
        """獲取屬性"""
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

    def __setattr__(self, key: str, value: Any) -> None:
        """設置屬性"""
        if isinstance(value, dict):
            value = DictToAttrRecursive(value)
        super(DictToAttrRecursive, self).__setitem__(key, value)
        super().__setattr__(key, value)

    def __delattr__(self, item: str) -> None:
        """刪除屬性"""
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

def clean_path(path_str: str) -> str:
    """
    統一的路徑清理函數
    解決多個檔案中重複定義的問題
    
    Args:
        path_str: 原始路徑字串
        
    Returns:
        清理後的路徑字串
    """
    if not path_str:
        return ""
    
    # 遞歸移除尾部斜線
    if path_str.endswith(("\\", "/")):
        return clean_path(path_str[0:-1])
    
    # 統一路徑分隔符
    path_str = path_str.replace("/", os.sep).replace("\\", os.sep)
    
    # 移除特殊字符
    return path_str.strip(" '\n\"\u202a")

def normalize_text(text: str) -> str:
    """
    標準化文本，用於去重比較
    
    Args:
        text: 原始文本
        
    Returns:
        標準化後的文本
    """
    if not text:
        return ""
    
    # 轉換為小寫
    text = text.lower()
    
    # 移除多餘空格
    text = " ".join(text.split())
    
    # 移除標點符號（可選）
    import re
    text = re.sub(r'[^\w\s]', '', text)
    
    return text

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全獲取字典值
    
    Args:
        dictionary: 字典
        key: 鍵
        default: 預設值
        
    Returns:
        值或預設值
    """
    return dictionary.get(key, default)

def ensure_directory(path: str) -> bool:
    """
    確保目錄存在
    
    Args:
        path: 目錄路徑
        
    Returns:
        是否成功創建或已存在
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"創建目錄失敗: {path}, 錯誤: {e}")
        return False

def validate_file_path(file_path: str) -> bool:
    """
    驗證檔案路徑
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        是否有效
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False

def get_file_extension(file_path: str) -> str:
    """
    獲取檔案副檔名
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        副檔名（不含點）
    """
    try:
        return Path(file_path).suffix.lstrip('.')
    except Exception:
        return ""

def format_file_size(size_bytes: int) -> str:
    """
    格式化檔案大小
    
    Args:
        size_bytes: 位元組數
        
    Returns:
        格式化後的大小字串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def create_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    創建統一的日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別
        
    Returns:
        日誌記錄器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    重試裝飾器
    
    Args:
        max_retries: 最大重試次數
        delay: 重試延遲（秒）
    """
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"函數 {func.__name__} 執行失敗，重試 {attempt + 1}/{max_retries}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"函數 {func.__name__} 最終執行失敗: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator

def is_empty(*items: Any) -> bool:
    """
    檢查任意項目是否為空
    解決多個檔案中重複定義的問題
    
    Args:
        *items: 要檢查的項目
        
    Returns:
        是否所有項目都為空
    """
    for item in items:
        if item is not None and item != "":
            return False
    return True

def remove_duplicates(items: list, key_func=None) -> list:
    """
    移除重複項目
    
    Args:
        items: 項目列表
        key_func: 用於比較的鍵函數
        
    Returns:
        去重後的列表
    """
    if key_func is None:
        return list(dict.fromkeys(items))
    
    seen = set()
    result = []
    
    for item in items:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result

# 版本資訊
__version__ = "1.0.0"
__author__ = "Podwise Team"
__description__ = "Podwise 共用工具模組" 