"""
RAG 層級基礎類別
定義所有 RAG 層級的通用介面和行為
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class RAGLevel(ABC):
    """RAG 層級抽象基類"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 RAG 層級
        
        Args:
            config: 層級配置
        """
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.fallback_strategy = config.get('fallback_strategy', None)
    
    @abstractmethod
    async def process(self, input_data: Any) -> Tuple[Any, float]:
        """
        處理輸入數據
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Tuple[Any, float]: 處理結果和信心值
        """
        raise NotImplementedError("子類別必須實作 process 方法")
    
    async def should_fallback(self, confidence: float) -> bool:
        """
        判斷是否需要降級
        
        Args:
            confidence: 信心值
            
        Returns:
            bool: 是否需要降級
        """
        return confidence < self.confidence_threshold
    
    def get_config(self) -> Dict[str, Any]:
        """
        獲取層級配置
        
        Returns:
            Dict[str, Any]: 層級配置
        """
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """
        更新層級配置
        
        Args:
            updates: 配置更新
        """
        self.config.update(updates)
        # 更新相關屬性
        if 'name' in updates:
            self.name = updates['name']
        if 'confidence_threshold' in updates:
            self.confidence_threshold = updates['confidence_threshold']
        if 'fallback_strategy' in updates:
            self.fallback_strategy = updates['fallback_strategy'] 