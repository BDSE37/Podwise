"""
Core Service 工具類
原 base_service.py，提供通用服務基礎類別，OOP 工具化
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
import asyncio
from datetime import datetime
import json
import os
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    """服務配置資料類別"""
    service_name: str
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30
    retry_count: int = 3
    log_level: str = "INFO"
    config: Optional[Dict[str, Any]] = None

@dataclass
class ServiceResponse:
    """服務回應資料類別"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: int = 200
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class BaseService(ABC):
    """
    基礎服務抽象類別
    定義所有服務的基本介面和通用功能
    遵循 MLOps 原則：可擴展性、可維護性、穩定性
    """
    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.config = config or {}
        self.logger = self._setup_logger()
        self.is_initialized = False
        self.start_time = datetime.now()
        self.health_status = "unknown"
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{self.service_name}_service")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        pass
    async def start(self) -> bool:
        try:
            self.logger.info(f"正在啟動 {self.service_name} 服務...")
            success = await self.initialize()
            if success:
                self.is_initialized = True
                self.health_status = "healthy"
                self.logger.info(f"{self.service_name} 服務啟動成功")
            else:
                self.health_status = "unhealthy"
                self.logger.error(f"{self.service_name} 服務啟動失敗")
            return success
        except Exception as e:
            self.health_status = "error"
            self.logger.error(f"啟動 {self.service_name} 服務時發生錯誤: {str(e)}")
            return False
    async def stop(self) -> bool:
        try:
            self.logger.info(f"正在停止 {self.service_name} 服務...")
            await self._cleanup()
            self.is_initialized = False
            self.health_status = "stopped"
            self.logger.info(f"{self.service_name} 服務已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止 {self.service_name} 服務時發生錯誤: {str(e)}")
            return False
    async def _cleanup(self):
        pass
    def get_status(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "health_status": self.health_status,
            "start_time": self.start_time.isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "config": self.config
        }
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        try:
            self.config.update(new_config)
            self.logger.info(f"已更新 {self.service_name} 配置")
            return True
        except Exception as e:
            self.logger.error(f"更新配置時發生錯誤: {str(e)}")
            return False
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        log_data = {
            "operation": operation,
            "service": self.service_name,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            log_data.update(details)
        self.logger.info(f"操作記錄: {json.dumps(log_data, ensure_ascii=False)}")

class ServiceManager:
    """
    服務管理器
    管理多個服務的生命週期
    實現 MLOps 中的服務編排功能
    """
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger("service_manager")
    def register_service(self, service: BaseService) -> bool:
        try:
            self.services[service.service_name] = service
            self.logger.info(f"已註冊服務: {service.service_name}")
            return True
        except Exception as e:
            self.logger.error(f"註冊服務失敗: {str(e)}")
            return False
    def unregister_service(self, service_name: str) -> bool:
        try:
            if service_name in self.services:
                del self.services[service_name]
                self.logger.info(f"已取消註冊服務: {service_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消註冊服務失敗: {str(e)}")
            return False
    async def start_all_services(self) -> Dict[str, bool]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.start()
            except Exception as e:
                self.logger.error(f"啟動服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    async def stop_all_services(self) -> Dict[str, bool]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.stop()
            except Exception as e:
                self.logger.error(f"停止服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    def get_service(self, service_name: str) -> Optional[BaseService]:
        return self.services.get(service_name)
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        return {
            service_name: service.get_status()
            for service_name, service in self.services.items()
        }
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.health_check()
            except Exception as e:
                self.logger.error(f"健康檢查服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = {"status": "error", "error": str(e)}
        return results

class ModelService(BaseService):
    """
    模型服務基礎類別
    專門用於管理 ML 模型的生命週期
    """
    def __init__(self, service_name: str, model_path: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.model_path = model_path
        self.model = None
        self.model_version = "1.0.0"
        self.model_metadata = {}
    async def load_model(self) -> bool:
        try:
            self.logger.info(f"正在載入模型: {self.model_path}")
            # 子類別實作具體的模型載入邏輯
            return True
        except Exception as e:
            self.logger.error(f"載入模型失敗: {str(e)}")
            return False
    async def save_model(self, version: Optional[str] = None) -> bool:
        try:
            if version:
                self.model_version = version
            self.logger.info(f"正在保存模型版本: {self.model_version}")
            # 子類別實作具體的模型保存邏輯
            return True
        except Exception as e:
            self.logger.error(f"保存模型失敗: {str(e)}")
            return False
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "model_metadata": self.model_metadata,
            "service_status": self.get_status()
        } 