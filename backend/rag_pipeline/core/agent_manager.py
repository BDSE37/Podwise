#!/usr/bin/env python3
"""
代理人管理器

負責管理所有代理人，提供統一的介面來處理用戶查詢和協調代理人協作
遵循 Google Clean Code 原則，採用 OOP 設計模式

作者: Podwise Team
版本: 3.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse, UserQuery
from config.agent_roles_config import get_agent_roles_manager, AgentLayer

logger = logging.getLogger(__name__)


class AgentRegistry:
    """代理人註冊表"""
    
    def __init__(self):
        """初始化註冊表"""
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
    
    def register_agent_class(self, agent_name: str, agent_class: Type[BaseAgent]) -> None:
        """
        註冊代理人類別
        
        Args:
            agent_name: 代理人名稱
            agent_class: 代理人類別
        """
        self._agent_classes[agent_name] = agent_class
        logger.info(f"註冊代理人類別: {agent_name} -> {agent_class.__name__}")
    
    def create_agent(self, agent_name: str, **kwargs) -> BaseAgent:
        """
        創建代理人實例
        
        Args:
            agent_name: 代理人名稱
            **kwargs: 額外參數
            
        Returns:
            BaseAgent: 代理人實例
            
        Raises:
            ValueError: 當代理人類別未註冊時
        """
        if agent_name not in self._agent_classes:
            raise ValueError(f"代理人類別 '{agent_name}' 未註冊")
        
        agent_class = self._agent_classes[agent_name]
        agent = agent_class(agent_name, **kwargs)
        self._agents[agent_name] = agent
        
        logger.info(f"創建代理人實例: {agent_name}")
        return agent
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """獲取代理人實例"""
        return self._agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """獲取所有代理人實例"""
        return self._agents.copy()
    
    def remove_agent(self, agent_name: str) -> bool:
        """移除代理人實例"""
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info(f"移除代理人實例: {agent_name}")
            return True
        return False


class AgentCoordinator:
    """代理人協調器"""
    
    def __init__(self, registry: AgentRegistry):
        """
        初始化協調器
        
        Args:
            registry: 代理人註冊表
        """
        self.registry = registry
        self.roles_manager = get_agent_roles_manager()
    
    async def execute_layer_processing(self, 
                                     layer: AgentLayer, 
                                     input_data: Any,
                                     agent_filter: Optional[List[str]] = None) -> Dict[str, AgentResponse]:
        """
        執行指定層級的處理
        
        Args:
            layer: 代理人層級
            input_data: 輸入數據
            agent_filter: 代理人過濾器（只執行指定的代理人）
            
        Returns:
            Dict[str, AgentResponse]: 各代理人的回應
        """
        layer_roles = self.roles_manager.get_roles_by_layer(layer)
        results = {}
        
        # 過濾代理人
        if agent_filter:
            layer_roles = {
                name: config for name, config in layer_roles.items()
                if name in agent_filter
            }
        
        # 並行執行同層級的代理人
        tasks = []
        for agent_name in layer_roles.keys():
            agent = self.registry.get_agent(agent_name)
            if agent:
                task = asyncio.create_task(
                    agent.execute_with_monitoring(input_data),
                    name=f"agent_{agent_name}"
                )
                tasks.append((agent_name, task))
        
        # 等待所有任務完成
        for agent_name, task in tasks:
            try:
                response = await task
                results[agent_name] = response
                logger.info(f"層級 {layer.value} 代理人 {agent_name} 完成處理")
            except Exception as e:
                logger.error(f"層級 {layer.value} 代理人 {agent_name} 處理失敗: {str(e)}")
                results[agent_name] = AgentResponse(
                    content=f"代理人 {agent_name} 處理失敗",
                    confidence=0.0,
                    reasoning=str(e),
                    agent_name=agent_name
                )
        
        return results
    
    async def execute_sequential_processing(self, 
                                          agent_sequence: List[str], 
                                          initial_input: Any) -> List[AgentResponse]:
        """
        執行順序處理
        
        Args:
            agent_sequence: 代理人執行順序
            initial_input: 初始輸入
            
        Returns:
            List[AgentResponse]: 按順序的回應列表
        """
        results = []
        current_input = initial_input
        
        for agent_name in agent_sequence:
            agent = self.registry.get_agent(agent_name)
            if not agent:
                logger.warning(f"代理人 {agent_name} 不存在，跳過")
                continue
            
            try:
                response = await agent.execute_with_monitoring(current_input)
                results.append(response)
                
                # 將當前回應作為下一個代理人的輸入
                current_input = response
                
                logger.info(f"順序處理: {agent_name} 完成")
                
            except Exception as e:
                logger.error(f"順序處理: {agent_name} 失敗 - {str(e)}")
                error_response = AgentResponse(
                    content=f"代理人 {agent_name} 處理失敗",
                    confidence=0.0,
                    reasoning=str(e),
                    agent_name=agent_name
                )
                results.append(error_response)
                break  # 順序處理中斷
        
        return results


class AgentManager:
    """
    代理人管理器
    
    負責管理所有代理人，提供統一的介面來處理用戶查詢和協調代理人協作
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化代理人管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.registry = AgentRegistry()
        self.coordinator = AgentCoordinator(self.registry)
        self.roles_manager = get_agent_roles_manager()
        
        # 系統指標
        self.system_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_processing_time": 0.0,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info("代理人管理器初始化完成")
    
    def register_agent_classes(self, agent_classes: Dict[str, Type[BaseAgent]]) -> None:
        """
        批量註冊代理人類別
        
        Args:
            agent_classes: 代理人類別字典 {agent_name: agent_class}
        """
        for agent_name, agent_class in agent_classes.items():
            self.registry.register_agent_class(agent_name, agent_class)
    
    def initialize_all_agents(self, **kwargs) -> None:
        """
        初始化所有已註冊的代理人
        
        Args:
            **kwargs: 傳遞給代理人構造函數的額外參數
        """
        all_roles = self.roles_manager.get_all_roles()
        
        for agent_name in all_roles.keys():
            try:
                self.registry.create_agent(agent_name, **kwargs)
                logger.info(f"初始化代理人: {agent_name}")
            except Exception as e:
                logger.error(f"初始化代理人 {agent_name} 失敗: {str(e)}")
    
    async def process_query_with_three_layer_architecture(self, 
                                                        query: str, 
                                                        user_id: str,
                                                        category: Optional[str] = None) -> AgentResponse:
        """
        使用三層架構處理用戶查詢
        
        Args:
            query: 查詢內容
            user_id: 用戶 ID
            category: 預分類類別
            
        Returns:
            AgentResponse: 最終處理結果
        """
        start_time = datetime.now()
        
        try:
            # 創建用戶查詢對象
            user_query = UserQuery(
                query=query,
                user_id=user_id,
                category=category
            )
            
            # 第三層：功能專家層（並行處理）
            logger.info("🔧 執行第三層：功能專家層")
            functional_results = await self.coordinator.execute_layer_processing(
                layer=AgentLayer.FUNCTIONAL_EXPERT,
                input_data=user_query
            )
            
            # 第二層：類別專家層（根據分類選擇專家）
            logger.info("🎓 執行第二層：類別專家層")
            category_filter = self._determine_category_experts(category)
            category_results = await self.coordinator.execute_layer_processing(
                layer=AgentLayer.CATEGORY_EXPERT,
                input_data=user_query,
                agent_filter=category_filter
            )
            
            # 第一層：領導者層（整合決策）
            logger.info("👑 執行第一層：領導者層")
            integration_data = {
                "user_query": user_query,
                "functional_results": functional_results,
                "category_results": category_results
            }
            
            leader_results = await self.coordinator.execute_layer_processing(
                layer=AgentLayer.LEADER,
                input_data=integration_data
            )
            
            # 獲取領導者的最終決策
            final_response = self._extract_final_response(leader_results)
            
            # 更新系統指標
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_success_metrics(processing_time)
            
            logger.info(f"✅ 三層架構處理完成，處理時間: {processing_time:.3f}s")
            
            return final_response
            
        except Exception as e:
            # 更新失敗指標
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_failure_metrics(processing_time)
            
            logger.error(f"❌ 三層架構處理失敗: {str(e)}")
            
            return AgentResponse(
                content="查詢處理失敗",
                confidence=0.0,
                reasoning=f"三層架構處理失敗: {str(e)}",
                processing_time=processing_time,
                agent_name="system"
            )
    
    def _determine_category_experts(self, category: Optional[str]) -> Optional[List[str]]:
        """
        根據分類決定需要的類別專家
        
        Args:
            category: 分類
            
        Returns:
            Optional[List[str]]: 專家列表
        """
        if not category:
            return None  # 執行所有類別專家
        
        category_mapping = {
            "商業": ["business_expert"],
            "教育": ["education_expert"],
            "混合": ["business_expert", "education_expert"]
        }
        
        return category_mapping.get(category)
    
    def _extract_final_response(self, leader_results: Dict[str, AgentResponse]) -> AgentResponse:
        """
        從領導者結果中提取最終回應
        
        Args:
            leader_results: 領導者層結果
            
        Returns:
            AgentResponse: 最終回應
        """
        if "leader" in leader_results:
            return leader_results["leader"]
        
        # 如果沒有領導者回應，返回預設回應
        return AgentResponse(
            content="無法獲得領導者決策",
            confidence=0.0,
            reasoning="領導者代理人未回應",
            agent_name="system"
        )
    
    def _update_success_metrics(self, processing_time: float) -> None:
        """更新成功指標"""
        self.system_metrics["total_queries"] += 1
        self.system_metrics["successful_queries"] += 1
        
        # 更新平均處理時間
        total_queries = self.system_metrics["total_queries"]
        current_avg = self.system_metrics["average_processing_time"]
        self.system_metrics["average_processing_time"] = (
            (current_avg * (total_queries - 1) + processing_time) / total_queries
        )
    
    def _update_failure_metrics(self, processing_time: float) -> None:
        """更新失敗指標"""
        self.system_metrics["total_queries"] += 1
        self.system_metrics["failed_queries"] += 1
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            Dict[str, Any]: 系統狀態資訊
        """
        agents_status = {}
        for agent_name, agent in self.registry.get_all_agents().items():
            agents_status[agent_name] = {
                "role_info": agent.get_role_info(),
                "metrics": agent.get_metrics(),
                "status": "active"
            }
        
        success_rate = 0.0
        if self.system_metrics["total_queries"] > 0:
            success_rate = (
                self.system_metrics["successful_queries"] / 
                self.system_metrics["total_queries"]
            )
        
        return {
            "system_metrics": {
                **self.system_metrics,
                "success_rate": success_rate
            },
            "agents_status": agents_status,
            "architecture": self.roles_manager.get_agent_summary(),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_all_metrics(self) -> None:
        """重置所有指標"""
        # 重置系統指標
        self.system_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_processing_time": 0.0,
            "start_time": datetime.now().isoformat()
        }
        
        # 重置所有代理人指標
        for agent in self.registry.get_all_agents().values():
            agent.reset_metrics()
        
        logger.info("所有指標已重置")
    
    def get_agent_by_name(self, agent_name: str) -> Optional[BaseAgent]:
        """根據名稱獲取代理人"""
        return self.registry.get_agent(agent_name)
    
    def list_available_agents(self) -> List[str]:
        """列出所有可用的代理人"""
        return list(self.registry.get_all_agents().keys())
    
    def shutdown(self) -> None:
        """關閉管理器"""
        logger.info("代理人管理器正在關閉...")
        # 這裡可以添加清理邏輯
        logger.info("代理人管理器已關閉") 