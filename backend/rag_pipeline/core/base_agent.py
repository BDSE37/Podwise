#!/usr/bin/env python3
"""
基礎代理人抽象類別

定義所有代理人的基本介面和共同功能，遵循 Google Clean Code 原則
採用 OOP 設計模式，便於維護和擴展

作者: Podwise Team
版本: 3.0.0
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from config.agent_roles_config import get_agent_roles_manager, AgentRoleConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentResponse:
    """
    代理人回應數據類別
    
    封裝代理人的處理結果，包含內容、信心值、推理說明和元數據
    
    Attributes:
        content: 回應內容
        confidence: 信心值 (0.0-1.0)
        reasoning: 推理說明
        metadata: 元數據字典
        processing_time: 處理時間（秒）
        agent_name: 代理人名稱
        timestamp: 處理時間戳
    """
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    agent_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")
        
        if self.processing_time < 0:
            raise ValueError("處理時間不能為負數")


@dataclass(frozen=True)
class UserQuery:
    """
    用戶查詢數據類別
    
    封裝用戶查詢的完整資訊，包含查詢內容、用戶 ID 和上下文資訊
    
    Attributes:
        query: 查詢內容
        user_id: 用戶 ID
        category: 預分類類別
        context: 上下文資訊
        session_id: 會話 ID
        metadata: 額外元數據
    """
    query: str
    user_id: str
    category: Optional[str] = None
    context: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not self.query.strip():
            raise ValueError("查詢內容不能為空")
        
        if not self.user_id.strip():
            raise ValueError("用戶 ID 不能為空")


class BaseAgent(ABC):
    """
    代理人基礎抽象類別
    
    定義所有代理人的基本介面和共同功能，包括：
    - 角色配置管理
    - 信心值計算
    - 錯誤處理
    - 效能監控
    - 日誌記錄
    """
    
    def __init__(self, agent_name: str, custom_config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化基礎代理人
        
        Args:
            agent_name: 代理人名稱（必須在 agent_roles_config 中定義）
            custom_config: 自定義配置覆蓋
        
        Raises:
            ValueError: 當代理人名稱不存在時
        """
        self.agent_name = agent_name
        self.role_config = self._load_role_config(agent_name)
        self.custom_config = custom_config or {}
        
        # 初始化效能指標
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "last_used": None
        }
        
        logger.info(f"初始化代理人: {self.role_config.name} ({self.role_config.role})")
    
    def _load_role_config(self, agent_name: str) -> AgentRoleConfig:
        """
        載入代理人角色配置
        
        Args:
            agent_name: 代理人名稱
            
        Returns:
            AgentRoleConfig: 角色配置
            
        Raises:
            ValueError: 當代理人名稱不存在時
        """
        roles_manager = get_agent_roles_manager()
        role_config = roles_manager.get_role(agent_name)
        
        if not role_config:
            available_roles = list(roles_manager.get_all_roles().keys())
            raise ValueError(
                f"代理人 '{agent_name}' 不存在。"
                f"可用的代理人: {', '.join(available_roles)}"
            )
        
        return role_config
    
    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        """
        處理輸入數據（抽象方法）
        
        子類別必須實作此方法來定義具體的處理邏輯
        
        Args:
            input_data: 輸入數據
            
        Returns:
            AgentResponse: 處理結果
        """
        raise NotImplementedError("子類別必須實作 process 方法")
    
    async def execute_with_monitoring(self, input_data: Any) -> AgentResponse:
        """
        帶監控的執行方法
        
        包裝 process 方法，添加效能監控、錯誤處理和指標更新
        
        Args:
            input_data: 輸入數據
            
        Returns:
            AgentResponse: 處理結果
        """
        start_time = time.time()
        
        try:
            # 驗證輸入
            if not self.validate_input(input_data):
                raise ValueError("輸入數據驗證失敗")
            
            # 執行處理
            response = await self.process(input_data)
            
            # 更新成功指標
            processing_time = time.time() - start_time
            self._update_success_metrics(response.confidence, processing_time)
            
            # 更新回應中的代理人資訊
            response.metadata.update({
                "agent_name": self.agent_name,
                "agent_role": self.role_config.role,
                "processing_time": processing_time
            })
            
            logger.info(
                f"代理人 {self.agent_name} 處理成功 - "
                f"信心值: {response.confidence:.3f}, "
                f"處理時間: {processing_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # 更新失敗指標
            processing_time = time.time() - start_time
            self._update_failure_metrics(processing_time)
            
            logger.error(f"代理人 {self.agent_name} 處理失敗: {str(e)}")
            
            return AgentResponse(
                content=f"處理失敗: {str(e)}",
                confidence=0.0,
                reasoning=f"代理人 {self.agent_name} 執行時發生錯誤",
                metadata={
                    "error": str(e),
                    "agent_name": self.agent_name,
                    "agent_role": self.role_config.role
                },
                processing_time=processing_time,
                agent_name=self.agent_name
            )
    
    def calculate_confidence(self, 
                           response: str, 
                           context: Optional[str] = None,
                           additional_factors: Optional[Dict[str, float]] = None) -> float:
        """
        計算信心值
        
        基於多個因素計算代理人對回應的信心程度
        
        Args:
            response: 回應內容
            context: 上下文資訊
            additional_factors: 額外的信心值因素
            
        Returns:
            float: 信心值 (0.0-1.0)
        """
        confidence = 0.0
        
        # 基礎信心值（根據回應長度和完整性）
        if response and len(response.strip()) > 0:
            confidence += 0.3
            
            # 根據回應長度調整
            if len(response) > 50:
                confidence += 0.2
            if len(response) > 200:
                confidence += 0.1
        
        # 關鍵詞匹配度
        if self._contains_relevant_keywords(response):
            confidence += 0.2
        
        # 上下文相關性
        if context and self._is_contextually_relevant(response, context):
            confidence += 0.2
        
        # 額外因素
        if additional_factors:
            for factor, weight in additional_factors.items():
                confidence += weight
        
        return min(max(confidence, 0.0), 1.0)
    
    def _contains_relevant_keywords(self, response: str) -> bool:
        """檢查回應是否包含相關關鍵詞"""
        relevant_keywords = ["podcast", "推薦", "建議", "節目", "內容"]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in relevant_keywords)
    
    def _is_contextually_relevant(self, response: str, context: str) -> bool:
        """檢查回應與上下文的相關性"""
        if not context:
            return False
        
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        
        # 計算詞彙重疊率
        overlap = len(context_words.intersection(response_words))
        total_context_words = len(context_words)
        
        return overlap / max(total_context_words, 1) > 0.1
    
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據
        
        Args:
            input_data: 輸入數據
            
        Returns:
            bool: 驗證結果
        """
        return input_data is not None
    
    def _update_success_metrics(self, confidence: float, processing_time: float) -> None:
        """更新成功指標"""
        self.metrics["total_calls"] += 1
        self.metrics["successful_calls"] += 1
        self.metrics["last_used"] = datetime.now().isoformat()
        
        # 更新平均處理時間
        total_calls = self.metrics["total_calls"]
        current_avg_time = self.metrics["average_processing_time"]
        self.metrics["average_processing_time"] = (
            (current_avg_time * (total_calls - 1) + processing_time) / total_calls
        )
        
        # 更新平均信心值
        current_avg_confidence = self.metrics["average_confidence"]
        self.metrics["average_confidence"] = (
            (current_avg_confidence * (total_calls - 1) + confidence) / total_calls
        )
    
    def _update_failure_metrics(self, processing_time: float) -> None:
        """更新失敗指標"""
        self.metrics["total_calls"] += 1
        self.metrics["failed_calls"] += 1
        self.metrics["last_used"] = datetime.now().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        獲取代理人效能指標
        
        Returns:
            Dict[str, Any]: 效能指標
        """
        success_rate = 0.0
        if self.metrics["total_calls"] > 0:
            success_rate = self.metrics["successful_calls"] / self.metrics["total_calls"]
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "agent_name": self.agent_name,
            "agent_role": self.role_config.role,
            "confidence_threshold": self.role_config.confidence_threshold
        }
    
    def reset_metrics(self) -> None:
        """重置效能指標"""
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "last_used": None
        }
        logger.info(f"代理人 {self.agent_name} 指標已重置")
    
    def get_role_info(self) -> Dict[str, Any]:
        """
        獲取角色資訊
        
        Returns:
            Dict[str, Any]: 角色資訊
        """
        return {
            "name": self.role_config.name,
            "role": self.role_config.role,
            "goal": self.role_config.goal,
            "layer": self.role_config.layer.value,
            "category": self.role_config.category.value,
            "skills": self.role_config.skills,
            "tools": self.role_config.tools,
            "confidence_threshold": self.role_config.confidence_threshold,
            "priority": self.role_config.priority
        }
    
    def __str__(self) -> str:
        """字串表示"""
        return f"{self.role_config.name} ({self.agent_name})"
    
    def __repr__(self) -> str:
        """詳細字串表示"""
        return (
            f"BaseAgent(agent_name='{self.agent_name}', "
            f"role='{self.role_config.role}', "
            f"layer='{self.role_config.layer.value}')"
        ) 