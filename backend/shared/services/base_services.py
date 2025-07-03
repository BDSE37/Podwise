"""
統一的基礎服務模組
避免在不同模組中重複定義相同的服務類別
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class APIType(Enum):
    """API 類型枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"

class ServiceStatus(Enum):
    """服務狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceHealth(BaseModel):
    """服務健康狀態模型"""
    status: ServiceStatus
    message: str
    timestamp: datetime
    response_time: Optional[float] = None
    error_count: int = 0

class CacheEntry(BaseModel):
    """快取項目模型"""
    data: Any
    timestamp: datetime
    ttl: int  # 存活時間（秒）

class RetryConfig(BaseModel):
    """重試配置模型"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0

class APIKeyManager:
    """統一的 API 金鑰管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化 API 金鑰管理器
        
        Args:
            config_path: 配置檔案路徑
        """
        self.config_path = config_path or os.getenv("API_KEYS_CONFIG", "api_keys.json")
        self.api_keys = {}
        self.load_api_keys()
    
    def load_api_keys(self):
        """載入 API 金鑰"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.api_keys = json.load(f)
                logger.info("✅ API 金鑰載入成功")
            else:
                # 從環境變數載入
                self.api_keys = {
                    "openai": os.getenv("OPENAI_API_KEY"),
                    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
                    "google": os.getenv("GOOGLE_API_KEY"),
                    "qwen": os.getenv("QWEN_API_KEY"),
                    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
                    "ollama": os.getenv("OLLAMA_API_KEY")
                }
                logger.info("✅ 從環境變數載入 API 金鑰")
        except Exception as e:
            logger.error(f"❌ API 金鑰載入失敗: {str(e)}")
            self.api_keys = {}
    
    def get_api_key(self, api_type: APIType) -> Optional[str]:
        """
        獲取指定類型的 API 金鑰
        
        Args:
            api_type: API 類型
            
        Returns:
            Optional[str]: API 金鑰
        """
        return self.api_keys.get(api_type.value)
    
    def set_api_key(self, api_type: APIType, api_key: str):
        """
        設定 API 金鑰
        
        Args:
            api_type: API 類型
            api_key: API 金鑰
        """
        self.api_keys[api_type.value] = api_key
        self.save_api_keys()
    
    def save_api_keys(self):
        """儲存 API 金鑰"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.api_keys, f, indent=2, ensure_ascii=False)
            logger.info("✅ API 金鑰儲存成功")
        except Exception as e:
            logger.error(f"❌ API 金鑰儲存失敗: {str(e)}")

class ServiceManager:
    """統一的服務管理器"""
    
    def __init__(self):
        """初始化服務管理器"""
        self.services: Dict[str, ServiceHealth] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self.retry_config = RetryConfig()
    
    def register_service(self, service_name: str, health_check_func=None):
        """
        註冊服務
        
        Args:
            service_name: 服務名稱
            health_check_func: 健康檢查函數
        """
        self.services[service_name] = ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            message="服務已註冊",
            timestamp=datetime.now()
        )
        logger.info(f"📝 註冊服務: {service_name}")
    
    async def check_service_health(self, service_name: str, health_check_func=None) -> ServiceHealth:
        """
        檢查服務健康狀態
        
        Args:
            service_name: 服務名稱
            health_check_func: 健康檢查函數
            
        Returns:
            ServiceHealth: 服務健康狀態
        """
        try:
            start_time = datetime.now()
            
            if health_check_func:
                result = await health_check_func()
                response_time = (datetime.now() - start_time).total_seconds()
                
                health = ServiceHealth(
                    status=ServiceStatus.HEALTHY if result else ServiceStatus.UNHEALTHY,
                    message="健康檢查完成",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
            else:
                # 預設健康檢查
                health = ServiceHealth(
                    status=ServiceStatus.HEALTHY,
                    message="預設健康檢查通過",
                    timestamp=datetime.now()
                )
            
            self.services[service_name] = health
            return health
            
        except Exception as e:
            health = ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message=f"健康檢查失敗: {str(e)}",
                timestamp=datetime.now(),
                error_count=self.services.get(service_name, ServiceHealth(
                    status=ServiceStatus.UNKNOWN,
                    message="",
                    timestamp=datetime.now()
                )).error_count + 1
            )
            self.services[service_name] = health
            return health
    
    def get_service_status(self, service_name: str) -> Optional[ServiceHealth]:
        """
        獲取服務狀態
        
        Args:
            service_name: 服務名稱
            
        Returns:
            Optional[ServiceHealth]: 服務健康狀態
        """
        return self.services.get(service_name)
    
    def get_all_services_status(self) -> Dict[str, ServiceHealth]:
        """
        獲取所有服務狀態
        
        Returns:
            Dict[str, ServiceHealth]: 所有服務狀態
        """
        return self.services.copy()
    
    def set_cache(self, key: str, data: Any, ttl: int = 3600):
        """
        設定快取
        
        Args:
            key: 快取鍵
            data: 快取數據
            ttl: 存活時間（秒）
        """
        self.cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=ttl
        )
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        獲取快取
        
        Args:
            key: 快取鍵
            
        Returns:
            Optional[Any]: 快取數據
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.now() - entry.timestamp > timedelta(seconds=entry.ttl):
            del self.cache[key]
            return None
        
        return entry.data
    
    def clear_cache(self, key: str = None):
        """
        清除快取
        
        Args:
            key: 快取鍵，如果為 None 則清除所有快取
        """
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """
        使用指數退避重試函數
        
        Args:
            func: 要重試的函數
            *args: 函數參數
            **kwargs: 函數關鍵字參數
            
        Returns:
            函數執行結果
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.retry_config.max_retries - 1:
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                        self.retry_config.max_delay
                    )
                    logger.warning(f"重試 {attempt + 1}/{self.retry_config.max_retries}: {str(e)}")
                    await asyncio.sleep(delay)
        
        raise last_exception 