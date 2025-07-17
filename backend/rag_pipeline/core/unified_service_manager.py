#!/usr/bin/env python3
"""
Unified Service Manager

統一的服務管理器，整合所有 RAG Pipeline 功能，提供 OOP 介面
消除重複功能，確保模組化設計

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from rag_pipeline.config.database_config import get_database_config_manager
from rag_pipeline.config.agent_roles_config import get_agent_config

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    """服務狀態數據類別"""
    name: str
    is_available: bool
    is_initialized: bool
    error_message: Optional[str] = None
    last_check: Optional[str] = None


class BaseService(ABC):
    """基礎服務抽象類別"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_initialized = False
        self.error_message = None
        self.last_check = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康檢查"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理資源"""
        pass
    
    def get_status(self) -> ServiceStatus:
        """獲取服務狀態"""
        return ServiceStatus(
            name=self.name,
            is_available=self.is_initialized,
            is_initialized=self.is_initialized,
            error_message=self.error_message,
            last_check=self.last_check
        )


class DatabaseService(BaseService):
    """資料庫服務管理器"""
    
    def __init__(self):
        super().__init__("DatabaseService")
        self.config_manager = get_database_config_manager()
        self.connections = {}
    
    async def initialize(self) -> bool:
        """初始化資料庫連接"""
        try:
            # 驗證配置
            validation = self.config_manager.validate_config()
            if not all(validation.values()):
                missing = [k for k, v in validation.items() if not v]
                raise ValueError(f"配置不完整: {missing}")
            
            # 初始化連接（實際連接會在需要時建立）
            self.is_initialized = True
            self.last_check = "初始化成功"
            logger.info("資料庫服務初始化成功")
            return True
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"資料庫服務初始化失敗: {e}")
            return False
    
    async def health_check(self) -> bool:
        """檢查資料庫健康狀態"""
        try:
            # 這裡可以添加實際的連接測試
            self.last_check = "健康檢查通過"
            return self.is_initialized
            
        except Exception as e:
            self.error_message = str(e)
            self.last_check = f"健康檢查失敗: {e}"
            return False
    
    async def cleanup(self) -> None:
        """清理資料庫連接"""
        try:
            for connection in self.connections.values():
                if hasattr(connection, 'close'):
                    await connection.close()
            self.connections.clear()
            logger.info("資料庫連接已清理")
            
        except Exception as e:
            logger.error(f"清理資料庫連接失敗: {e}")
    
    def get_mongodb_config(self) -> Dict[str, str]:
        """獲取 MongoDB 配置"""
        return self.config_manager.get_mongodb_config()
    
    def get_postgres_config(self) -> Dict[str, Any]:
        """獲取 PostgreSQL 配置"""
        return self.config_manager.get_postgres_config()
    
    def get_redis_config(self) -> Dict[str, Any]:
        """獲取 Redis 配置"""
        return self.config_manager.get_redis_config()
    
    def get_milvus_config(self) -> Dict[str, Any]:
        """獲取 Milvus 配置"""
        return self.config_manager.get_milvus_config()


class LLMService(BaseService):
    """LLM 服務管理器"""
    
    def __init__(self):
        super().__init__("LLMService")
        self.llm_managers = {}
    
    async def initialize(self) -> bool:
        """初始化 LLM 服務"""
        try:
            # 初始化 Qwen LLM 管理器
            try:
                from .qwen_llm_manager import Qwen3LLMManager
                self.llm_managers['qwen'] = Qwen3LLMManager()
                logger.info("Qwen LLM 管理器初始化成功")
            except ImportError as e:
                logger.warning(f"Qwen LLM 管理器導入失敗: {e}")
            
            # 初始化 Ollama LLM
            try:
                from llm.core.ollama_llm import OllamaLLM, OllamaConfig
                from llm.main import get_llm_manager
                
                # 使用 LLM 管理器
                llm_manager = get_llm_manager()
                await llm_manager.initialize()
                self.llm_managers['ollama'] = llm_manager
                logger.info("Ollama LLM 管理器初始化成功")
            except ImportError as e:
                logger.warning(f"Ollama LLM 導入失敗: {e}")
            except Exception as e:
                logger.warning(f"Ollama LLM 初始化失敗: {e}")
            
            self.is_initialized = len(self.llm_managers) > 0
            self.last_check = "初始化成功"
            return self.is_initialized
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"LLM 服務初始化失敗: {e}")
            return False
    
    async def health_check(self) -> bool:
        """檢查 LLM 服務健康狀態"""
        try:
            for name, manager in self.llm_managers.items():
                if hasattr(manager, 'health_check'):
                    await manager.health_check()
            self.last_check = "健康檢查通過"
            return True
            
        except Exception as e:
            self.error_message = str(e)
            self.last_check = f"健康檢查失敗: {e}"
            return False
    
    async def cleanup(self) -> None:
        """清理 LLM 服務"""
        try:
            for manager in self.llm_managers.values():
                if hasattr(manager, 'cleanup'):
                    await manager.cleanup()
            logger.info("LLM 服務已清理")
            
        except Exception as e:
            logger.error(f"清理 LLM 服務失敗: {e}")
    
    def get_llm_manager(self, name: str = "qwen"):
        """獲取指定的 LLM 管理器"""
        return self.llm_managers.get(name)


class TTSService(BaseService):
    """TTS 服務管理器"""
    
    def __init__(self):
        super().__init__("TTSService")
        self.tts_service = None
    
    async def initialize(self) -> bool:
        """初始化 TTS 服務"""
        try:
            from tts.core.tts_service import TTSService as TTSCore
            self.tts_service = TTSCore()
            self.is_initialized = True
            self.last_check = "初始化成功"
            logger.info("TTS 服務初始化成功")
            return True
            
        except ImportError as e:
            self.error_message = f"TTS 服務導入失敗: {e}"
            logger.warning(f"TTS 服務導入失敗: {e}")
            return False
    
    async def health_check(self) -> bool:
        """檢查 TTS 服務健康狀態"""
        try:
            if self.tts_service and hasattr(self.tts_service, 'health_check'):
                await self.tts_service.health_check()
            self.last_check = "健康檢查通過"
            return True
            
        except Exception as e:
            self.error_message = str(e)
            self.last_check = f"健康檢查失敗: {e}"
            return False
    
    async def cleanup(self) -> None:
        """清理 TTS 服務"""
        try:
            if self.tts_service and hasattr(self.tts_service, 'cleanup'):
                await self.tts_service.cleanup()
            logger.info("TTS 服務已清理")
            
        except Exception as e:
            logger.error(f"清理 TTS 服務失敗: {e}")
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """語音合成"""
        if not self.tts_service:
            return None
        
        try:
            # 轉換語速參數為字串格式
            rate_param = f"+{(speed-1)*100:.0f}%" if speed != 1.0 else "+0%"
            return await self.tts_service.synthesize_speech(text, voice, rate_param)
        except Exception as e:
            logger.error(f"語音合成失敗: {e}")
            return None


class RecommendationService(BaseService):
    """推薦服務管理器"""
    
    def __init__(self):
        super().__init__("RecommendationService")
        self.recommender = None
    
    async def initialize(self) -> bool:
        """初始化推薦服務"""
        try:
            # 嘗試導入 ML Pipeline 推薦器
            try:
                from ml_pipeline.core.recommender import RecommenderEngine
                # 需要提供資料來初始化推薦器
                import pandas as pd
                empty_podcast_data = pd.DataFrame()
                empty_user_history = pd.DataFrame()
                self.recommender = RecommenderEngine(empty_podcast_data, empty_user_history)
                logger.info("ML Pipeline 推薦器初始化成功")
            except ImportError as e:
                logger.warning(f"ML Pipeline 推薦器導入失敗: {e}")
            except Exception as e:
                logger.warning(f"ML Pipeline 推薦器初始化失敗: {e}")
            
            # 嘗試導入增強推薦器
            if not self.recommender:
                try:
                    from .enhanced_podcast_recommender import MCPEnhancedPodcastRecommender
                    self.recommender = MCPEnhancedPodcastRecommender()
                    logger.info("增強推薦器初始化成功")
                except ImportError as e:
                    logger.warning(f"增強推薦器導入失敗: {e}")
            
            self.is_initialized = self.recommender is not None
            self.last_check = "初始化成功"
            return self.is_initialized
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"推薦服務初始化失敗: {e}")
            return False
    
    async def health_check(self) -> bool:
        """檢查推薦服務健康狀態"""
        try:
            if self.recommender and hasattr(self.recommender, 'health_check'):
                await self.recommender.health_check()
            self.last_check = "健康檢查通過"
            return True
            
        except Exception as e:
            self.error_message = str(e)
            self.last_check = f"健康檢查失敗: {e}"
            return False
    
    async def cleanup(self) -> None:
        """清理推薦服務"""
        try:
            if self.recommender and hasattr(self.recommender, 'cleanup'):
                await self.recommender.cleanup()
            logger.info("推薦服務已清理")
            
        except Exception as e:
            logger.error(f"清理推薦服務失敗: {e}")
    
    async def get_recommendations(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """獲取推薦"""
        if not self.recommender:
            return []
        
        try:
            if hasattr(self.recommender, 'get_recommendations'):
                # 檢查是否為異步方法
                import asyncio
                if asyncio.iscoroutinefunction(self.recommender.get_recommendations):
                    return await self.recommender.get_recommendations(query, user_id, limit)
                else:
                    return self.recommender.get_recommendations(query, user_id, limit)
            else:
                logger.warning("推薦器沒有 get_recommendations 方法")
                return []
        except Exception as e:
            logger.error(f"獲取推薦失敗: {e}")
            return []


class VectorSearchService(BaseService):
    """向量搜尋服務管理器"""
    
    def __init__(self):
        super().__init__("VectorSearchService")
        self.vector_search = None
        self.milvus_search = None
    
    async def initialize(self) -> bool:
        """初始化向量搜尋服務"""
        try:
            # 初始化增強向量搜尋
            try:
                from .enhanced_vector_search import RAGVectorSearch
                self.vector_search = RAGVectorSearch()
                logger.info("增強向量搜尋初始化成功")
            except ImportError as e:
                logger.warning(f"增強向量搜尋導入失敗: {e}")
            
            # 初始化 Milvus 搜尋
            try:
                from .enhanced_milvus_search import EnhancedMilvusSearch
                self.milvus_search = EnhancedMilvusSearch()
                logger.info("Milvus 搜尋初始化成功")
            except ImportError as e:
                logger.warning(f"Milvus 搜尋導入失敗: {e}")
            
            self.is_initialized = self.vector_search is not None or self.milvus_search is not None
            self.last_check = "初始化成功"
            return self.is_initialized
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"向量搜尋服務初始化失敗: {e}")
            return False
    
    async def health_check(self) -> bool:
        """檢查向量搜尋服務健康狀態"""
        try:
            if self.vector_search and hasattr(self.vector_search, 'health_check'):
                await self.vector_search.health_check()
            if self.milvus_search and hasattr(self.milvus_search, 'health_check'):
                await self.milvus_search.health_check()
            self.last_check = "健康檢查通過"
            return True
            
        except Exception as e:
            self.error_message = str(e)
            self.last_check = f"健康檢查失敗: {e}"
            return False
    
    async def cleanup(self) -> None:
        """清理向量搜尋服務"""
        try:
            if self.vector_search and hasattr(self.vector_search, 'cleanup'):
                await self.vector_search.cleanup()
            if self.milvus_search and hasattr(self.milvus_search, 'cleanup'):
                await self.milvus_search.cleanup()
            logger.info("向量搜尋服務已清理")
            
        except Exception as e:
            logger.error(f"清理向量搜尋服務失敗: {e}")
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """執行向量搜尋"""
        results = []
        
        # 嘗試使用增強向量搜尋
        if self.vector_search:
            try:
                if hasattr(self.vector_search, 'search'):
                    results.extend(await self.vector_search.search(query, limit))
            except Exception as e:
                logger.error(f"增強向量搜尋失敗: {e}")
        
        # 嘗試使用 Milvus 搜尋
        if self.milvus_search and not results:
            try:
                if hasattr(self.milvus_search, 'search'):
                    results.extend(await self.milvus_search.search(query, limit))
            except Exception as e:
                logger.error(f"Milvus 搜尋失敗: {e}")
        
        return results


class UnifiedServiceManager:
    """統一的服務管理器"""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """初始化服務管理器"""
        try:
            logger.info("正在初始化統一服務管理器...")
            
            # 初始化資料庫配置
            self.config_manager = get_database_config_manager()
            
            # 初始化整合服務（LLM + ML Pipeline）
            try:
                from .integrated_services import get_integrated_service_manager
                self.integrated_services = get_integrated_service_manager()
                await self.integrated_services.initialize()
                logger.info("✅ 整合服務初始化成功")
            except Exception as e:
                logger.warning(f"整合服務初始化失敗: {e}")
                self.integrated_services = None
            
            # 初始化其他服務
            await self._initialize_database_services()
            await self._initialize_llm_services()
            await self._initialize_tts_services()
            await self._initialize_vector_services()
            await self._initialize_recommendation_services()
            await self._initialize_web_services()
            
            self.is_initialized = True
            logger.info("✅ 統一服務管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"統一服務管理器初始化失敗: {e}")
            return False
    
    async def _initialize_database_services(self) -> None:
        """初始化資料庫服務"""
        try:
            # 創建資料庫服務實例
            self.database_service = DatabaseService()
            success = await self.database_service.initialize()
            if success:
                self.services['database'] = self.database_service
                logger.info("✅ 資料庫服務初始化成功")
            else:
                logger.warning("⚠️ 資料庫服務初始化失敗")
        except Exception as e:
            logger.error(f"❌ 資料庫服務初始化錯誤: {e}")
    
    async def _initialize_llm_services(self) -> None:
        """初始化 LLM 服務"""
        try:
            # 創建 LLM 服務實例
            self.llm_service = LLMService()
            success = await self.llm_service.initialize()
            if success:
                self.services['llm'] = self.llm_service
                logger.info("✅ LLM 服務初始化成功")
            else:
                logger.warning("⚠️ LLM 服務初始化失敗")
        except Exception as e:
            logger.error(f"❌ LLM 服務初始化錯誤: {e}")
    
    async def _initialize_tts_services(self) -> None:
        """初始化 TTS 服務"""
        try:
            # 創建 TTS 服務實例
            self.tts_service = TTSService()
            success = await self.tts_service.initialize()
            if success:
                self.services['tts'] = self.tts_service
                logger.info("✅ TTS 服務初始化成功")
            else:
                logger.warning("⚠️ TTS 服務初始化失敗")
        except Exception as e:
            logger.error(f"❌ TTS 服務初始化錯誤: {e}")
    
    async def _initialize_vector_services(self) -> None:
        """初始化向量搜尋服務"""
        try:
            # 創建向量搜尋服務實例
            self.vector_search_service = VectorSearchService()
            success = await self.vector_search_service.initialize()
            if success:
                self.services['vector_search'] = self.vector_search_service
                logger.info("✅ 向量搜尋服務初始化成功")
            else:
                logger.warning("⚠️ 向量搜尋服務初始化失敗")
        except Exception as e:
            logger.error(f"❌ 向量搜尋服務初始化錯誤: {e}")
    
    async def _initialize_recommendation_services(self) -> None:
        """初始化推薦服務"""
        try:
            # 創建推薦服務實例
            self.recommendation_service = RecommendationService()
            success = await self.recommendation_service.initialize()
            if success:
                self.services['recommendation'] = self.recommendation_service
                logger.info("✅ 推薦服務初始化成功")
            else:
                logger.warning("⚠️ 推薦服務初始化失敗")
        except Exception as e:
            logger.error(f"❌ 推薦服務初始化錯誤: {e}")
    
    async def _initialize_web_services(self) -> None:
        """初始化 Web 服務"""
        try:
            # 這裡可以添加 Web 搜尋等服務的初始化
            logger.info("✅ Web 服務初始化完成")
        except Exception as e:
            logger.error(f"❌ Web 服務初始化錯誤: {e}")
    
    async def health_check(self) -> Dict[str, ServiceStatus]:
        """檢查所有服務健康狀態"""
        health_results = {}
        
        for name, service in self.services.items():
            try:
                is_healthy = await service.health_check()
                health_results[name] = service.get_status()
            except Exception as e:
                health_results[name] = ServiceStatus(
                    name=name,
                    is_available=False,
                    is_initialized=False,
                    error_message=str(e)
                )
        
        return health_results
    
    async def cleanup(self) -> None:
        """清理所有服務"""
        cleanup_tasks = [
            service.cleanup() 
            for service in self.services.values()
        ]
        
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        logger.info("所有服務已清理")
    
    def get_service(self, name: str) -> Optional[BaseService]:
        """獲取指定服務"""
        return self.services.get(name)
    
    def get_database_service(self) -> Optional[DatabaseService]:
        """獲取資料庫服務"""
        return self.get_service('database')
    
    def get_llm_service(self) -> Optional[LLMService]:
        """獲取 LLM 服務"""
        return self.get_service('llm')
    
    def get_tts_service(self) -> Optional[TTSService]:
        """獲取 TTS 服務"""
        return self.get_service('tts')
    
    def get_recommendation_service(self) -> Optional[RecommendationService]:
        """獲取推薦服務"""
        return self.get_service('recommendation')
    
    def get_vector_search_service(self) -> Optional[VectorSearchService]:
        """獲取向量搜尋服務"""
        return self.get_service('vector_search')
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            "is_initialized": self.is_initialized,
            "services": {
                name: service.get_status().__dict__ 
                for name, service in self.services.items()
            },
            "total_services": len(self.services),
            "available_services": sum(
                1 for service in self.services.values() 
                if service.is_initialized
            )
        }


# 全域服務管理器實例
service_manager = UnifiedServiceManager()


def get_service_manager() -> UnifiedServiceManager:
    """獲取服務管理器"""
    return service_manager


async def initialize_services() -> bool:
    """初始化所有服務"""
    return await service_manager.initialize()


async def cleanup_services() -> None:
    """清理所有服務"""
    await service_manager.cleanup()


if __name__ == "__main__":
    # 測試服務管理器
    async def test_service_manager():
        print("服務管理器測試")
        print("=" * 50)
        
        # 初始化服務
        success = await initialize_services()
        print(f"服務初始化: {'成功' if success else '失敗'}")
        
        # 健康檢查
        health_status = await service_manager.health_check()
        print(f"\n健康檢查結果:")
        for service_name, status in health_status.items():
            print(f"  {service_name}: {'✅' if status.is_available else '❌'}")
        
        # 系統狀態
        system_status = service_manager.get_system_status()
        print(f"\n系統狀態:")
        print(f"  總服務數: {system_status['total_services']}")
        print(f"  可用服務數: {system_status['available_services']}")
        print(f"  已初始化: {system_status['is_initialized']}")
        
        # 清理服務
        await cleanup_services()
        print(f"\n服務已清理")
    
    # 執行測試
    asyncio.run(test_service_manager()) 