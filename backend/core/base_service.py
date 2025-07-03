"""
基礎服務類別
提供所有服務的通用功能和介面定義
基於 MLOps 最佳實踐設計
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
import asyncio
from datetime import datetime
import json
import os


class BaseService(ABC):
    """
    基礎服務抽象類別
    定義所有服務的基本介面和通用功能
    遵循 MLOps 原則：可擴展性、可維護性、穩定性
    """
    
    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化基礎服務
        
        Args:
            service_name: 服務名稱
            config: 配置字典
        """
        self.service_name = service_name
        self.config = config or {}
        self.logger = self._setup_logger()
        self.is_initialized = False
        self.start_time = datetime.now()
        self.health_status = "unknown"
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
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
        """
        初始化服務
        子類別必須實作此方法
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        子類別必須實作此方法
        """
        pass
    
    async def start(self) -> bool:
        """啟動服務"""
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
        """停止服務"""
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
        """清理資源，子類別可覆寫"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "health_status": self.health_status,
            "start_time": self.start_time.isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "config": self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.config.update(new_config)
            self.logger.info(f"已更新 {self.service_name} 配置")
            return True
        except Exception as e:
            self.logger.error(f"更新配置時發生錯誤: {str(e)}")
            return False
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """記錄操作日誌"""
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
        """註冊服務"""
        try:
            self.services[service.service_name] = service
            self.logger.info(f"已註冊服務: {service.service_name}")
            return True
        except Exception as e:
            self.logger.error(f"註冊服務失敗: {str(e)}")
            return False
    
    def unregister_service(self, service_name: str) -> bool:
        """取消註冊服務"""
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
        """啟動所有服務"""
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.start()
            except Exception as e:
                self.logger.error(f"啟動服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """停止所有服務"""
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.stop()
            except Exception as e:
                self.logger.error(f"停止服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """獲取指定服務"""
        return self.services.get(service_name)
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有服務狀態"""
        return {
            service_name: service.get_status()
            for service_name, service in self.services.items()
        }
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """檢查所有服務健康狀態"""
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
        """載入模型"""
        try:
            self.logger.info(f"正在載入模型: {self.model_path}")
            # 子類別實作具體的模型載入邏輯
            return True
        except Exception as e:
            self.logger.error(f"載入模型失敗: {str(e)}")
            return False
    
    async def save_model(self, version: Optional[str] = None) -> bool:
        """保存模型"""
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
        """獲取模型資訊"""
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "model_metadata": self.model_metadata,
            "service_status": self.get_status()
        } 