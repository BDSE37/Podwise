#!/usr/bin/env python3
"""
RAG Pipeline 統一介面

提供簡潔的介面來調用所有 RAG Pipeline 功能
遵循 Google Clean Code 原則，確保易於使用

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# 添加當前目錄到 Python 路徑
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入核心模組
from core.rag_pipeline_core import (
    RAGPipelineCore, QueryRequest, QueryResponse, 
    get_rag_pipeline_core, initialize_rag_pipeline, cleanup_rag_pipeline
)
from core.unified_service_manager import get_service_manager
try:
    from config.database_config import get_database_config_manager
    DATABASE_CONFIG_AVAILABLE = True
except ImportError:
    DATABASE_CONFIG_AVAILABLE = False
    get_database_config_manager = None


class RAGPipeline:
    """RAG Pipeline 統一介面類別"""
    
    def __init__(self, 
                 enable_monitoring: bool = True,
                 enable_semantic_retrieval: bool = True,
                 enable_chat_history: bool = True,
                 enable_apple_ranking: bool = True,
                 confidence_threshold: float = 0.7):
        """
        初始化 RAG Pipeline
        
        Args:
            enable_monitoring: 是否啟用監控
            enable_semantic_retrieval: 是否啟用語意檢索
            enable_chat_history: 是否啟用聊天歷史
            enable_apple_ranking: 是否啟用 Apple 排名
            confidence_threshold: 信心度閾值
        """
        self.core = RAGPipelineCore(
            enable_monitoring=enable_monitoring,
            enable_semantic_retrieval=enable_semantic_retrieval,
            enable_chat_history=enable_chat_history,
            enable_apple_ranking=enable_apple_ranking,
            confidence_threshold=confidence_threshold
        )
        self.service_manager = get_service_manager()
        self.config_manager = get_database_config_manager() if get_database_config_manager else None
        
        logger.info("RAG Pipeline 統一介面初始化完成")
    
    async def start(self) -> bool:
        """啟動 RAG Pipeline"""
        try:
            success = await self.core.initialize()
            if success:
                logger.info("RAG Pipeline 啟動成功")
            else:
                logger.error("RAG Pipeline 啟動失敗")
            return success
        except Exception as e:
            logger.error(f"啟動 RAG Pipeline 時發生錯誤: {e}")
            return False
    
    async def stop(self) -> None:
        """停止 RAG Pipeline"""
        try:
            await self.core.cleanup()
            logger.info("RAG Pipeline 已停止")
        except Exception as e:
            logger.error(f"停止 RAG Pipeline 時發生錯誤: {e}")
    
    async def query(self, 
                   query: str, 
                   user_id: str = "default_user",
                   session_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   enable_tts: bool = False,
                   voice: str = "podrina",
                   speed: float = 1.0) -> QueryResponse:
        """
        執行查詢
        
        Args:
            query: 查詢內容
            user_id: 用戶ID
            session_id: 會話ID
            metadata: 額外元數據
            enable_tts: 是否啟用TTS
            voice: 語音模型
            speed: 語音速度
            
        Returns:
            查詢回應
        """
        request = QueryRequest(
            query=query,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            enable_tts=enable_tts,
            voice=voice,
            speed=speed
        )
        
        return await self.core.process_query(request)
    
    async def get_recommendations(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        獲取推薦
        
        Args:
            query: 查詢內容
            user_id: 用戶ID
            limit: 推薦數量限制
            
        Returns:
            推薦列表
        """
        return await self.core.get_recommendations(query, user_id, limit)
    
    async def synthesize_speech(self, text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        語音合成
        
        Args:
            text: 要合成的文字
            voice: 語音模型
            speed: 語音速度
            
        Returns:
            語音合成結果
        """
        return await self.core.synthesize_speech(text, voice, speed)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            健康狀態資訊
        """
        return await self.core.health_check()
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        獲取系統資訊
        
        Returns:
            系統資訊
        """
        system_info = self.core.get_system_info()
        return {
            'version': system_info.version,
            'status': system_info.status,
            'components': system_info.components,
            'timestamp': system_info.timestamp
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        獲取資料庫配置
        
        Returns:
            資料庫配置資訊
        """
        if self.config_manager is None:
            return {
                'error': 'Database config manager not available',
                'mongodb': {},
                'postgres': {},
                'redis': {},
                'milvus': {}
            }
        
        config = self.config_manager.config
        return {
            'mongodb': {
                'uri': config.mongodb_uri,
                'database': config.mongodb_database,
                'collection': config.mongodb_collection
            },
            'postgres': {
                'host': config.postgres_host,
                'port': config.postgres_port,
                'database': config.postgres_db,
                'user': config.postgres_user
            },
            'redis': {
                'host': config.redis_host,
                'port': config.redis_port,
                'db': config.redis_db
            },
            'milvus': {
                'host': config.milvus_host,
                'port': config.milvus_port,
                'collection': config.milvus_collection
            }
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """
        驗證配置
        
        Returns:
            配置驗證結果
        """
        if self.config_manager is None:
            return {
                'database_config': False,
                'error': 'Database config manager not available'
            }
        return self.config_manager.validate_config()


# 全域 RAG Pipeline 實例
rag_pipeline = RAGPipeline()


async def start_pipeline() -> bool:
    """啟動 RAG Pipeline"""
    return await rag_pipeline.start()


async def stop_pipeline() -> None:
    """停止 RAG Pipeline"""
    await rag_pipeline.stop()


async def query(query: str, 
               user_id: str = "default_user",
               enable_tts: bool = False) -> QueryResponse:
    """
    執行查詢（簡化介面）
    
    Args:
        query: 查詢內容
        user_id: 用戶ID
        enable_tts: 是否啟用TTS
        
    Returns:
        查詢回應
    """
    return await rag_pipeline.query(query, user_id, enable_tts=enable_tts)


async def get_recommendations(query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    獲取推薦（簡化介面）
    
    Args:
        query: 查詢內容
        user_id: 用戶ID
        limit: 推薦數量限制
        
    Returns:
        推薦列表
    """
    return await rag_pipeline.get_recommendations(query, user_id, limit)


async def synthesize_speech(text: str, voice: str = "podrina", speed: float = 1.0) -> Optional[Dict[str, Any]]:
    """
    語音合成（簡化介面）
    
    Args:
        text: 要合成的文字
        voice: 語音模型
        speed: 語音速度
        
    Returns:
        語音合成結果
    """
    return await rag_pipeline.synthesize_speech(text, voice, speed)


async def health_check() -> Dict[str, Any]:
    """
    健康檢查（簡化介面）
    
    Returns:
        健康狀態資訊
    """
    return await rag_pipeline.health_check()


def get_system_info() -> Dict[str, Any]:
    """
    獲取系統資訊（簡化介面）
    
    Returns:
        系統資訊
    """
    return rag_pipeline.get_system_info()


def get_database_config() -> Dict[str, Any]:
    """
    獲取資料庫配置（簡化介面）
    
    Returns:
        資料庫配置資訊
    """
    return rag_pipeline.get_database_config()


def validate_config() -> Dict[str, bool]:
    """
    驗證配置（簡化介面）
    
    Returns:
        配置驗證結果
    """
    return rag_pipeline.validate_config()


# 快速使用範例
async def example_usage():
    """使用範例"""
    print("RAG Pipeline 使用範例")
    print("=" * 50)
    
    # 啟動 Pipeline
    success = await start_pipeline()
    if not success:
        print("啟動失敗")
        return
    
    # 執行查詢
    response = await query("什麼是機器學習？", "test_user")
    print(f"查詢回應: {response.response[:100]}...")
    print(f"信心度: {response.confidence:.2f}")
    
    # 獲取推薦
    recommendations = await get_recommendations("機器學習", "test_user", 3)
    print(f"推薦數量: {len(recommendations)}")
    
    # 語音合成
    tts_result = await synthesize_speech("這是一個測試語音合成", "podrina")
    if tts_result:
        print("語音合成成功")
    
    # 健康檢查
    health = await health_check()
    print(f"系統狀態: {health['status']}")
    
    # 停止 Pipeline
    await stop_pipeline()


if __name__ == "__main__":
    # 執行範例
    asyncio.run(example_usage()) 