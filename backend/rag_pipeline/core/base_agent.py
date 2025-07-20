#!/usr/bin/env python3
"""
RAG Pipeline 基礎代理人模組

定義所有代理人的基礎類別，使用統一數據模型
符合 OOP 原則和 Google Clean Code 標準

作者: Podwise Team
版本: 4.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

# 導入統一數據模型
from .data_models import (
    UserQuery, AgentResponse, AgentStatus,
    create_agent_response
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    代理人基類
    
    所有 RAG Pipeline 代理人都應該繼承此基類，
    提供統一的介面和監控功能
    """
    
    def __init__(self, 
                 name: str,
                 config: Optional[Dict[str, Any]] = None,
                 timeout: float = 30.0):
        """
        初始化代理人
        
        Args:
            name: 代理人名稱
            config: 配置字典
            timeout: 處理超時時間（秒）
        """
        self.name = name
        self.config = config or {}
        self.timeout = timeout
        self.status = AgentStatus.IDLE
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "last_request_time": None
        }
        
        logger.info(f"初始化代理人: {self.name}")
    
    @abstractmethod
    async def process(self, input_data: Union[UserQuery, str, Any]) -> AgentResponse:
        """
        處理輸入數據（抽象方法）
        
        Args:
            input_data: 輸入數據
            
        Returns:
            AgentResponse: 處理結果
        """
        pass
    
    async def execute_with_monitoring(self, 
                                    input_data: Union[UserQuery, str, Any]) -> AgentResponse:
        """
        執行處理並監控
        
        Args:
            input_data: 輸入數據
            
        Returns:
            AgentResponse: 處理結果
        """
        import time
        start_time = time.time()
        self.status = AgentStatus.PROCESSING
        self.metrics["total_requests"] += 1
        
        try:
            # 設置超時
            if self.timeout > 0:
                response = await asyncio.wait_for(
                    self.process(input_data),
                    timeout=self.timeout
                )
            else:
                response = await self.process(input_data)
            
            # 更新成功指標
            processing_time = time.time() - start_time
            self._update_success_metrics(processing_time)
            
            # 設置回應元數據
            response.agent_name = self.name
            response.processing_time = processing_time
            
            self.status = AgentStatus.SUCCESS
            logger.info(f"代理人 {self.name} 處理成功，耗時: {processing_time:.2f}秒")
            
            return response
            
        except asyncio.TimeoutError:
            # 處理超時
            processing_time = time.time() - start_time
            self._update_failure_metrics(processing_time)
            
            error_response = create_agent_response(
                content=f"代理人 {self.name} 處理超時",
                confidence=0.0,
                reasoning=f"處理時間超過 {self.timeout} 秒",
                processing_time=processing_time,
                status=AgentStatus.TIMEOUT,
                agent_name=self.name,
                error_message="Timeout"
            )
            
            self.status = AgentStatus.TIMEOUT
            logger.error(f"代理人 {self.name} 處理超時")
            return error_response
            
        except Exception as e:
            # 處理其他錯誤
            processing_time = time.time() - start_time
            self._update_failure_metrics(processing_time)
            
            error_response = create_agent_response(
                content=f"代理人 {self.name} 處理失敗",
                confidence=0.0,
                reasoning=f"處理過程中發生錯誤: {str(e)}",
                processing_time=processing_time,
                status=AgentStatus.ERROR,
                agent_name=self.name,
                error_message=str(e)
            )
            
            self.status = AgentStatus.ERROR
            logger.error(f"代理人 {self.name} 處理失敗: {e}")
            return error_response
    
    def _update_success_metrics(self, processing_time: float) -> None:
        """更新成功指標"""
        import time
        self.metrics["successful_requests"] += 1
        self.metrics["last_request_time"] = time.time()
        
        # 更新平均處理時間
        total_successful = self.metrics["successful_requests"]
        current_avg = self.metrics["average_processing_time"]
        new_avg = ((current_avg * (total_successful - 1)) + processing_time) / total_successful
        self.metrics["average_processing_time"] = new_avg
    
    def _update_failure_metrics(self, processing_time: float) -> None:
        """更新失敗指標"""
        import time
        self.metrics["failed_requests"] += 1
        self.metrics["last_request_time"] = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取代理人指標"""
        return {
            "name": self.name,
            "status": self.status.value,
            "metrics": self.metrics.copy(),
            "config": self.config,
            "timeout": self.timeout
        }
    
    def reset_metrics(self) -> None:
        """重置指標"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "last_request_time": None
        }
        logger.info(f"代理人 {self.name} 指標已重置")
    
    def is_available(self) -> bool:
        """檢查代理人是否可用"""
        return self.status != AgentStatus.ERROR
    
    def get_status(self) -> AgentStatus:
        """獲取代理人狀態"""
        return self.status
    
    def __str__(self) -> str:
        """字串表示"""
        return f"BaseAgent(name={self.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """詳細字串表示"""
        return f"BaseAgent(name='{self.name}', status={self.status.value}, metrics={self.metrics})" 