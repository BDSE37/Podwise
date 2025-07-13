#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 服務管理器

提供統一的服務管理介面，遵循 OOP 設計模式和 Google Clean Code 原則。
負責服務的初始化、健康檢查、配置管理和錯誤處理。

Author: Podwise Team
License: MIT
"""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json

# 添加專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import httpx
except ImportError:
    # 如果 httpx 不可用，使用 urllib 作為備選
    import urllib.request
    import urllib.error
    httpx = None

try:
    from utils.logging_config import get_logger
except ImportError:
    # 如果 logging_config 不可用，使用標準 logging
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)


class ServiceStatus(Enum):
    """服務狀態枚舉"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceType(Enum):
    """服務類型枚舉"""
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    RAG_PIPELINE = "rag_pipeline"
    ML_PIPELINE = "ml_pipeline"
    WEB_SEARCH = "web_search"
    FRONTEND = "frontend"
    PODRI_CHAT = "podri_chat"
    CRAWLER = "crawler"
    DATA_PROCESSOR = "data_processor"


@dataclass
class ServiceConfig:
    """服務配置資料類別"""
    name: str
    service_type: ServiceType
    host: str
    port: int
    health_check_url: str
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 5
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """服務健康狀態資料類別"""
    service_name: str
    status: ServiceStatus
    response_time: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ServiceInterface(ABC):
    """服務介面抽象類別"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """健康檢查"""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """啟動服務"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止服務"""
        pass
    
    @abstractmethod
    def get_config(self) -> ServiceConfig:
        """獲取服務配置"""
        pass


class BaseService(ServiceInterface):
    """基礎服務類別"""
    
    def __init__(self, config: ServiceConfig):
        """
        初始化基礎服務
        
        Args:
            config: 服務配置
        """
        self.config = config
        self.health_status = ServiceHealth(
            service_name=config.name,
            status=ServiceStatus.UNKNOWN
        )
        self._initialized = False
        self._running = False
        
    async def initialize(self) -> bool:
        """初始化服務"""
        try:
            logger.info(f"初始化服務: {self.config.name}")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"服務初始化失敗 {self.config.name}: {e}")
            return False
    
    async def health_check(self) -> ServiceHealth:
        """執行健康檢查"""
        try:
            start_time = datetime.now()
            
            if httpx is not None:
                # 使用 httpx 進行健康檢查
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.get(self.config.health_check_url)
                    
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status_code == 200:
                        self.health_status = ServiceHealth(
                            service_name=self.config.name,
                            status=ServiceStatus.HEALTHY,
                            response_time=response_time,
                            last_check=datetime.now(),
                            details=response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                        )
                    else:
                        self.health_status = ServiceHealth(
                            service_name=self.config.name,
                            status=ServiceStatus.UNHEALTHY,
                            response_time=response_time,
                            last_check=datetime.now(),
                            error_message=f"HTTP {response.status_code}"
                        )
            else:
                # 使用 urllib 作為備選
                import urllib.request
                import urllib.error
                
                try:
                    response = urllib.request.urlopen(self.config.health_check_url, timeout=self.config.timeout)
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.getcode() == 200:
                        self.health_status = ServiceHealth(
                            service_name=self.config.name,
                            status=ServiceStatus.HEALTHY,
                            response_time=response_time,
                            last_check=datetime.now()
                        )
                    else:
                        self.health_status = ServiceHealth(
                            service_name=self.config.name,
                            status=ServiceStatus.UNHEALTHY,
                            response_time=response_time,
                            last_check=datetime.now(),
                            error_message=f"HTTP {response.getcode()}"
                        )
                except urllib.error.URLError as e:
                    raise Exception(f"URL 錯誤: {e}")
                    
        except Exception as e:
            self.health_status = ServiceHealth(
                service_name=self.config.name,
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
            
        return self.health_status
    
    async def start(self) -> bool:
        """啟動服務"""
        try:
            logger.info(f"啟動服務: {self.config.name}")
            self._running = True
            return True
        except Exception as e:
            logger.error(f"服務啟動失敗 {self.config.name}: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止服務"""
        try:
            logger.info(f"停止服務: {self.config.name}")
            self._running = False
            return True
        except Exception as e:
            logger.error(f"服務停止失敗 {self.config.name}: {e}")
            return False
    
    def get_config(self) -> ServiceConfig:
        """獲取服務配置"""
        return self.config
    
    def is_healthy(self) -> bool:
        """檢查服務是否健康"""
        return self.health_status.status == ServiceStatus.HEALTHY
    
    def is_running(self) -> bool:
        """檢查服務是否運行中"""
        return self._running


class LLMService(BaseService):
    """LLM 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="LLM Service",
            service_type=ServiceType.LLM,
            host="localhost",
            port=8000,
            health_check_url="http://localhost:8000/health",
            environment_vars={
                "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://192.168.32.38:31134"),
                "LANGFUSE_HOST": os.getenv("LANGFUSE_HOST", "http://192.168.32.38:30000")
            }
        )
        super().__init__(config)


class STTService(BaseService):
    """STT 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="STT Service",
            service_type=ServiceType.STT,
            host="localhost",
            port=8001,
            health_check_url="http://localhost:8001/health",
            environment_vars={
                "MONGODB_HOST": os.getenv("MONGODB_HOST", "mongodb.podwise.svc.cluster.local"),
                "MONGODB_PORT": os.getenv("MONGODB_PORT", "27017")
            }
        )
        super().__init__(config)


class TTSService(BaseService):
    """TTS 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="TTS Service",
            service_type=ServiceType.TTS,
            host="localhost",
            port=8003,
            health_check_url="http://localhost:8003/health",
            environment_vars={
                "DEFAULT_VOICE": os.getenv("DEFAULT_VOICE", "podri"),
                "API_SERVER_PORT": "8003"
            }
        )
        super().__init__(config)


class RAGPipelineService(BaseService):
    """RAG Pipeline 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="RAG Pipeline",
            service_type=ServiceType.RAG_PIPELINE,
            host="localhost",
            port=8005,
            health_check_url="http://localhost:8005/health",
            dependencies=["tts"],
            environment_vars={
                "MILVUS_HOST": os.getenv("MILVUS_HOST", "worker3"),
                "MONGODB_HOST": os.getenv("MONGODB_HOST", "mongodb.podwise.svc.cluster.local"),
                "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres.podwise.svc.cluster.local")
            }
        )
        super().__init__(config)


class MLPipelineService(BaseService):
    """ML Pipeline 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="ML Pipeline",
            service_type=ServiceType.ML_PIPELINE,
            host="localhost",
            port=8004,
            health_check_url="http://localhost:8004/health",
            environment_vars={
                "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres.podwise.svc.cluster.local"),
                "MONGODB_HOST": os.getenv("MONGODB_HOST", "mongodb.podwise.svc.cluster.local"),
                "MILVUS_HOST": os.getenv("MILVUS_HOST", "worker3")
            }
        )
        super().__init__(config)


class WebSearchService(BaseService):
    """Web Search 服務類別"""
    
    def __init__(self):
        config = ServiceConfig(
            name="Web Search Service",
            service_type=ServiceType.WEB_SEARCH,
            host="localhost",
            port=8006,
            health_check_url="http://localhost:8006/health",
            environment_vars={
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY") or "",
                "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                "WEB_SEARCH_MODEL": os.getenv("WEB_SEARCH_MODEL", "gpt-3.5-turbo")
            }
        )
        super().__init__(config)
        
        # 初始化 WebSearchExpert
        try:
            from rag_pipeline.tools.web_search_tool import WebSearchExpert
            self.expert = WebSearchExpert(
                api_key=config.environment_vars["OPENAI_API_KEY"],
                api_base=config.environment_vars["OPENAI_API_BASE"],
                model=config.environment_vars["WEB_SEARCH_MODEL"]
            )
            self._expert_initialized = False
        except ImportError:
            self.expert = None
            logger.warning("WebSearchExpert 無法載入")
    
    async def initialize(self) -> bool:
        """初始化 Web Search 服務"""
        try:
            if self.expert:
                self._expert_initialized = await self.expert.initialize()
                return self._expert_initialized
            return False
        except Exception as e:
            logger.error(f"Web Search 服務初始化失敗: {e}")
            return False
    
    async def search(self, query: str, max_results: int = 3, language: str = "zh-TW"):
        """執行網路搜尋"""
        if not self._expert_initialized or not self.expert:
            raise RuntimeError("Web Search 服務未初始化")
        
        from rag_pipeline.tools.web_search_tool import SearchRequest
        request = SearchRequest(
            query=query,
            max_results=max_results,
            language=language
        )
        return await self.expert.search(request)
    
    async def health_check(self) -> ServiceHealth:
        """執行健康檢查"""
        try:
            if not self.expert:
                return ServiceHealth(
                    service_name=self.config.name,
                    status=ServiceStatus.ERROR,
                    error_message="WebSearchExpert 未載入"
                )
            
            health_info = await self.expert.health_check()
            
            if health_info["status"] == "healthy":
                return ServiceHealth(
                    service_name=self.config.name,
                    status=ServiceStatus.HEALTHY,
                    last_check=datetime.now(),
                    details=health_info
                )
            else:
                return ServiceHealth(
                    service_name=self.config.name,
                    status=ServiceStatus.UNHEALTHY,
                    last_check=datetime.now(),
                    error_message=health_info.get("error", "未知錯誤")
                )
                
        except Exception as e:
            return ServiceHealth(
                service_name=self.config.name,
                status=ServiceStatus.ERROR,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def cleanup(self) -> bool:
        """清理資源"""
        try:
            if self.expert:
                return await self.expert.cleanup()
            return True
        except Exception as e:
            logger.error(f"Web Search 服務清理失敗: {e}")
            return False


class ServiceManager:
    """服務管理器主類別"""
    
    def __init__(self):
        """初始化服務管理器"""
        self.services: Dict[str, BaseService] = {}
        self.health_check_interval = 30  # 秒
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
    def register_service(self, service: BaseService) -> None:
        """
        註冊服務
        
        Args:
            service: 要註冊的服務
        """
        self.services[service.config.name] = service
        logger.info(f"註冊服務: {service.config.name}")
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        獲取服務
        
        Args:
            service_name: 服務名稱
            
        Returns:
            服務實例或 None
        """
        return self.services.get(service_name)
    
    async def initialize_all_services(self) -> bool:
        """初始化所有服務"""
        logger.info("開始初始化所有服務...")
        
        for service in self.services.values():
            if not await service.initialize():
                logger.error(f"服務初始化失敗: {service.config.name}")
                return False
        
        logger.info("所有服務初始化完成")
        return True
    
    async def start_all_services(self) -> bool:
        """啟動所有服務"""
        logger.info("開始啟動所有服務...")
        
        # 按照依賴關係排序服務
        sorted_services = self._sort_services_by_dependencies()
        
        for service in sorted_services:
            if not await service.start():
                logger.error(f"服務啟動失敗: {service.config.name}")
                return False
        
        self._running = True
        logger.info("所有服務啟動完成")
        return True
    
    async def stop_all_services(self) -> bool:
        """停止所有服務"""
        logger.info("開始停止所有服務...")
        
        for service in reversed(list(self.services.values())):
            if not await service.stop():
                logger.warning(f"服務停止失敗: {service.config.name}")
        
        self._running = False
        logger.info("所有服務停止完成")
        return True
    
    async def health_check_all_services(self) -> Dict[str, ServiceHealth]:
        """檢查所有服務的健康狀態"""
        health_results = {}
        
        for service in self.services.values():
            health = await service.health_check()
            health_results[service.config.name] = health
            
        return health_results
    
    async def start_monitoring(self) -> None:
        """開始監控服務"""
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._monitoring_task = asyncio.create_task(self._monitor_services())
        logger.info("服務監控已啟動")
    
    async def stop_monitoring(self) -> None:
        """停止監控服務"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("服務監控已停止")
    
    async def _monitor_services(self) -> None:
        """監控服務的內部方法"""
        while self._running:
            try:
                health_results = await self.health_check_all_services()
                
                # 記錄不健康的服務
                unhealthy_services = [
                    name for name, health in health_results.items()
                    if health.status != ServiceStatus.HEALTHY
                ]
                
                if unhealthy_services:
                    logger.warning(f"不健康的服務: {unhealthy_services}")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"服務監控錯誤: {e}")
                await asyncio.sleep(5)
    
    def _sort_services_by_dependencies(self) -> List[BaseService]:
        """根據依賴關係排序服務"""
        # 簡單的拓撲排序實現
        visited = set()
        temp_visited = set()
        sorted_services = []
        
        def visit(service: BaseService) -> None:
            if service.config.name in temp_visited:
                raise ValueError(f"檢測到循環依賴: {service.config.name}")
            
            if service.config.name in visited:
                return
            
            temp_visited.add(service.config.name)
            
            # 先訪問依賴服務
            for dep_name in service.config.dependencies:
                dep_service = self.get_service(dep_name)
                if dep_service:
                    visit(dep_service)
            
            temp_visited.remove(service.config.name)
            visited.add(service.config.name)
            sorted_services.append(service)
        
        for service in self.services.values():
            if service.config.name not in visited:
                visit(service)
        
        return sorted_services
    
    def get_service_status_summary(self) -> Dict[str, Any]:
        """獲取服務狀態摘要"""
        summary = {
            "total_services": len(self.services),
            "healthy_services": 0,
            "unhealthy_services": 0,
            "services": {}
        }
        
        for service in self.services.values():
            is_healthy = service.is_healthy()
            if is_healthy:
                summary["healthy_services"] += 1
            else:
                summary["unhealthy_services"] += 1
            
            summary["services"][service.config.name] = {
                "type": service.config.service_type.value,
                "healthy": is_healthy,
                "running": service.is_running(),
                "status": service.health_status.status.value,
                "last_check": service.health_status.last_check.isoformat() if service.health_status.last_check else None
            }
        
        return summary


# 全域服務管理器實例
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """獲取全域服務管理器實例"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
        
        # 註冊所有服務
        _service_manager.register_service(LLMService())
        _service_manager.register_service(STTService())
        _service_manager.register_service(TTSService())
        _service_manager.register_service(RAGPipelineService())
        _service_manager.register_service(MLPipelineService())
        _service_manager.register_service(WebSearchService())
    
    return _service_manager


async def main():
    """主函數 - 用於測試"""
    service_manager = get_service_manager()
    
    try:
        # 初始化服務
        if not await service_manager.initialize_all_services():
            logger.error("服務初始化失敗")
            return
        
        # 啟動服務
        if not await service_manager.start_all_services():
            logger.error("服務啟動失敗")
            return
        
        # 開始監控
        await service_manager.start_monitoring()
        
        # 保持運行
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在停止服務...")
    finally:
        await service_manager.stop_monitoring()
        await service_manager.stop_all_services()


if __name__ == "__main__":
    asyncio.run(main()) 