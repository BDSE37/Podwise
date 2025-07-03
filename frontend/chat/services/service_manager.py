#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服務管理器
提供重試機制、健康檢查、服務降級策略和快取功能
"""

import os
import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服務狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    """服務健康狀態"""
    service_name: str
    status: ServiceStatus
    response_time: float
    last_check: float
    error_count: int
    success_count: int
    error_message: Optional[str] = None

@dataclass
class CacheEntry:
    """快取項目"""
    data: Any
    timestamp: float
    ttl: float
    key: str

class RetryConfig:
    """重試配置"""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 10.0, exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

class ServiceManager:
    """服務管理器"""
    
    def __init__(self):
        """初始化服務管理器"""
        self.services = {}
        self.health_cache = {}
        self.response_cache = {}
        self.cache_ttl = 300  # 5分鐘快取
        self.health_check_interval = 60  # 1分鐘健康檢查
        
        # 重試配置
        self.retry_config = RetryConfig()
        
        # 服務配置
        self._init_services()
    
    def _init_services(self):
        """初始化服務配置"""
        self.services = {
            "tts": {
                "urls": [
                    "http://192.168.32.56:30852",  # K8s NodePort
                    "http://localhost:8501",       # 本地開發
                    "http://tts:8501"              # 容器環境
                ],
                "health_endpoint": "/health",
                "timeout": 10,
                "priority": 1
            },
            "vector_search": {
                "urls": [
                    "http://localhost:8002",
                    "http://vector-search:8002"
                ],
                "health_endpoint": "/health",
                "timeout": 15,
                "priority": 1
            },
            "musicgen": {
                "urls": [
                    "http://localhost:3000",
                    "http://musicgen:3000"
                ],
                "health_endpoint": "/health",
                "timeout": 30,
                "priority": 2
            },
            "rag_pipeline": {
                "urls": [
                    "http://localhost:8001",
                    "http://rag-pipeline:8001"
                ],
                "health_endpoint": "/health",
                "timeout": 20,
                "priority": 1
            }
        }
    
    def retry_with_backoff(self, max_retries: Optional[int] = None, base_delay: Optional[float] = None):
        """重試裝飾器"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retries = max_retries or self.retry_config.max_retries
                delay = base_delay or self.retry_config.base_delay
                
                for attempt in range(retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == retries:
                            logger.error(f"最終重試失敗: {func.__name__} - {str(e)}")
                            raise
                        
                        wait_time = min(delay * (self.retry_config.exponential_base ** attempt), 
                                      self.retry_config.max_delay)
                        logger.warning(f"重試 {attempt + 1}/{retries}: {func.__name__} - {str(e)}, "
                                     f"等待 {wait_time:.2f} 秒")
                        await asyncio.sleep(wait_time)
                
            return wrapper
        return decorator
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """檢查服務健康狀態"""
        if service_name not in self.services:
            return ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNKNOWN,
                response_time=0.0,
                last_check=time.time(),
                error_count=0,
                success_count=0,
                error_message="服務未配置"
            )
        
        service_config = self.services[service_name]
        start_time = time.time()
        
        for url in service_config["urls"]:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{url}{service_config['health_endpoint']}",
                        timeout=service_config["timeout"]
                    ) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            
                            # 更新健康狀態
                            health = ServiceHealth(
                                service_name=service_name,
                                status=ServiceStatus.HEALTHY,
                                response_time=response_time,
                                last_check=time.time(),
                                error_count=0,
                                success_count=1
                            )
                            
                            self.health_cache[service_name] = health
                            return health
                        else:
                            logger.warning(f"服務 {service_name} ({url}) 回應異常: {response.status}")
                            
            except Exception as e:
                logger.warning(f"服務 {service_name} ({url}) 健康檢查失敗: {str(e)}")
                continue
        
        # 所有服務都失敗
        health = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.UNHEALTHY,
            response_time=time.time() - start_time,
            last_check=time.time(),
            error_count=1,
            success_count=0,
            error_message="所有服務端點都無法連接"
        )
        
        self.health_cache[service_name] = health
        return health
    
    async def get_healthy_service_url(self, service_name: str) -> Optional[str]:
        """獲取健康的服務 URL"""
        health = await self.check_service_health(service_name)
        
        if health.status == ServiceStatus.HEALTHY:
            service_config = self.services[service_name]
            # 返回第一個配置的 URL（假設健康檢查通過）
            return service_config["urls"][0]
        
        return None
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """生成快取鍵"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """獲取快取的回應"""
        if cache_key in self.response_cache:
            entry = self.response_cache[cache_key]
            if time.time() - entry.timestamp < entry.ttl:
                return entry.data
            else:
                # 過期，移除
                del self.response_cache[cache_key]
        return None
    
    def cache_response(self, cache_key: str, data: Any, ttl: float = None):
        """快取回應"""
        ttl = ttl or self.cache_ttl
        self.response_cache[cache_key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl,
            key=cache_key
        )
    
    async def make_service_request(self, service_name: str, method: str, 
                                 endpoint: str, data: Any = None, 
                                 use_cache: bool = True, cache_ttl: Optional[float] = None) -> Dict[str, Any]:
        """向服務發送請求"""
        cache_key = None
        if use_cache:
            cache_key = self.get_cache_key(service_name, method, endpoint, data)
            cached_response = self.get_cached_response(cache_key)
            if cached_response:
                return {
                    "success": True,
                    "data": cached_response,
                    "source": "cache",
                    "service": service_name
                }
        
        service_url = await self.get_healthy_service_url(service_name)
        if not service_url:
            return {
                "success": False,
                "error": f"服務 {service_name} 不可用",
                "service": service_name
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{service_url}{endpoint}"
                
                if method.upper() == "GET":
                    async with session.get(url, timeout=30) as response:
                        result = await self._handle_response(response)
                elif method.upper() == "POST":
                    async with session.post(url, json=data, timeout=30) as response:
                        result = await self._handle_response(response)
                else:
                    return {
                        "success": False,
                        "error": f"不支援的 HTTP 方法: {method}",
                        "service": service_name
                    }
                
                # 快取成功回應
                if result["success"] and use_cache and cache_key:
                    self.cache_response(cache_key, result["data"], cache_ttl or self.cache_ttl)
                
                result["service"] = service_name
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"服務請求失敗: {str(e)}",
                "service": service_name
            }
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """處理 HTTP 回應"""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status}: {error_text}",
                    "status_code": response.status
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"回應解析失敗: {str(e)}",
                "status_code": response.status
            }
    
    async def get_all_services_status(self) -> Dict[str, ServiceHealth]:
        """獲取所有服務狀態"""
        tasks = []
        for service_name in self.services.keys():
            tasks.append(self.check_service_health(service_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_dict = {}
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            if isinstance(result, Exception):
                status_dict[service_name] = ServiceHealth(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    response_time=0.0,
                    last_check=time.time(),
                    error_count=1,
                    success_count=0,
                    error_message=str(result)
                )
            else:
                status_dict[service_name] = result
        
        return status_dict
    
    def clear_cache(self, service_name: str = None):
        """清除快取"""
        if service_name:
            # 清除特定服務的快取
            keys_to_remove = [k for k in self.response_cache.keys() 
                            if k.startswith(service_name)]
            for key in keys_to_remove:
                del self.response_cache[key]
        else:
            # 清除所有快取
            self.response_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計"""
        return {
            "total_entries": len(self.response_cache),
            "cache_size_mb": sum(len(json.dumps(entry.data)) for entry in self.response_cache.values()) / 1024 / 1024,
            "services": list(self.services.keys())
        }

# 全域服務管理器實例
service_manager = ServiceManager() 