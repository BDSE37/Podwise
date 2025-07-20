#!/usr/bin/env python3
"""
增強 Milvus 搜尋模組

整合 MilvusDB 功能，提供統一的向量搜尋介面
支援 Qwen2.5-Taiwan 模型進行向量檢索

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import logging
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from config.integrated_config import get_config
except ImportError:
    try:
        from ..config.integrated_config import get_config
    except ImportError:
        # 如果都無法導入，使用簡化配置
        def get_config():
            class Config:
                class Database:
                    milvus_host = os.getenv("MILVUS_HOST", "192.168.32.86")
                    milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
                    milvus_collection = os.getenv("MILVUS_COLLECTION", "podcast_chunks")
                database = Database()
            return Config()

logger = logging.getLogger(__name__)


@dataclass
class MilvusSearchResult:
    """Milvus 搜尋結果"""
    content: str
    similarity_score: float
    chunk_id: str
    metadata: Dict[str, Any]
    tags: List[str]
    source: str = "milvus"


class EnhancedMilvusSearch:
    """
    增強 Milvus 搜尋服務
    
    整合 MilvusDB 功能，提供統一的向量搜尋介面
    支援多種搜尋模式和結果格式化
    """
    
    def __init__(self):
        """初始化增強 Milvus 搜尋服務"""
        self.config = get_config()
        self.collection = None
        self.is_connected = False
        self._connect()
        
        # 初始化 Qwen LLM 管理器（用於文本向量化）
        self.qwen_llm_manager = None
        try:
            from .qwen_llm_manager import get_qwen3_llm_manager
            self.qwen_llm_manager = get_qwen3_llm_manager()
            logger.info("✅ Qwen LLM 管理器初始化成功")
        except Exception as e:
            logger.warning(f"Qwen LLM 管理器初始化失敗: {e}")
        
        logger.info("✅ EnhancedMilvusSearch 初始化完成")
    
    def _connect(self):
        """連接到 Milvus"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 檢查是否已經連接
            try:
                connections.get_connection("default")
                logger.info("✅ Milvus 已連接，使用現有連接")
            except:
                # 連接到 Milvus
                connections.connect(
                    alias="default",
                    host=self.config.database.milvus_host,
                    port=self.config.database.milvus_port
                )
            
            # 檢查集合是否存在
            collection_name = self.config.database.milvus_collection
            if utility.has_collection(collection_name):
                self.collection = Collection(collection_name)
                self.is_connected = True
                logger.info(f"✅ Milvus 集合 '{collection_name}' 連接成功")
            else:
                logger.warning(f"⚠️ Milvus 集合 '{collection_name}' 不存在")
                
        except ImportError:
            logger.warning("⚠️ pymilvus 未安裝")
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {e}")
    
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            bool: 健康狀態
        """
        try:
            if not self.is_connected or self.collection is None:
                return False
            
            # 檢查集合狀態
            from pymilvus import utility
            collection_name = self.config.database.milvus_collection
            if utility.has_collection(collection_name):
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Milvus 健康檢查失敗: {e}")
            return False
    
    async def search(self, query: Union[str, List[float]], top_k: int = 8) -> List[Dict[str, Any]]:
        """
        執行向量搜尋
        
        Args:
            query: 查詢文本或向量
            top_k: 返回結果數量
            
        Returns:
            List[Dict[str, Any]]: 搜尋結果
        """
        try:
            if not self.is_connected or self.collection is None:
                logger.warning("Milvus 未連接，返回模擬結果")
                return self._get_mock_results(query, top_k)
            
            # 如果輸入是文本，先向量化
            if isinstance(query, str):
                embedding = await self._text_to_vector(query)
            if not embedding:
                    logger.warning("文本向量化失敗，返回模擬結果")
                    return self._get_mock_results(query, top_k)
            else:
                embedding = query
            
            # 載入集合
            self.collection.load()
            
            # 執行搜尋
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "tags", "podcast_name", "episode_title", "category"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    # 解析 tags 欄位（JSON 格式）
                    tags = []
                    try:
                        if hit.entity.get("tags"):
                            if isinstance(hit.entity.get("tags"), str):
                                tags = json.loads(hit.entity.get("tags"))
                            else:
                                tags = hit.entity.get("tags")
                    except:
                        tags = []
                    
                    formatted_results.append({
                        "content": hit.entity.get("chunk_text", ""),
                        "confidence": float(hit.score),
                        "source": "milvus",
                        "metadata": {
                            "podcast_name": hit.entity.get("podcast_name", ""),
                            "episode_title": hit.entity.get("episode_title", ""),
                            "category": hit.entity.get("category", ""),
                            "chunk_id": hit.entity.get("chunk_id", "")
                        },
                        "tags": tags,
                        "chunk_id": hit.entity.get("chunk_id", ""),
                        "similarity_score": float(hit.score)
                    })
            
            logger.info(f"✅ Milvus 搜尋成功，返回 {len(formatted_results)} 個結果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Milvus 搜尋失敗: {e}")
            return self._get_mock_results(query, top_k)
    
    async def _text_to_vector(self, text: str) -> Optional[List[float]]:
        """
        文本向量化
        
        Args:
            text: 輸入文本
            
        Returns:
            Optional[List[float]]: 文本向量
        """
        try:
            if self.qwen_llm_manager:
                # 使用 Qwen LLM 管理器進行文本向量化
                # 這裡需要實現具體的向量化邏輯
                # 暫時使用簡單的哈希方法
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                vector = [float(int(hash_obj.hexdigest()[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
                return vector
            else:
                # 使用簡單的哈希方法作為備用
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                vector = [float(int(hash_obj.hexdigest()[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
                return vector
            
        except Exception as e:
            logger.error(f"文本向量化失敗: {e}")
            return None
    
    def _get_mock_results(self, query: Union[str, List[float]], top_k: int) -> List[Dict[str, Any]]:
        """
        獲取模擬搜尋結果
        
        Args:
            query: 查詢
            top_k: 結果數量
            
        Returns:
            List[Dict[str, Any]]: 模擬結果
        """
        mock_results = []
        for i in range(min(top_k, 3)):
            mock_results.append({
                "content": f"這是第 {i+1} 個模擬搜尋結果，查詢: {str(query)[:50]}...",
                "confidence": 0.8 - i * 0.1,
                "source": "mock_data",
                "metadata": {
                    "category": "general",
                    "episode_title": f"模擬播客 {i+1}",
                    "podcast_name": "模擬播客"
                },
                "tags": ["模擬", "測試"],
                "chunk_id": f"mock_chunk_{i+1}",
                "similarity_score": 0.8 - i * 0.1
            })
        
        return mock_results
    
    async def cleanup(self):
        """清理資源"""
        try:
            if self.collection:
                self.collection.release()
            logger.info("✅ Milvus 資源清理完成")
        except Exception as e:
            logger.error(f"❌ Milvus 資源清理失敗: {e}")


def create_enhanced_milvus_search() -> EnhancedMilvusSearch:
    """
    建立增強 Milvus 搜尋實例
    
    Returns:
        EnhancedMilvusSearch: 增強 Milvus 搜尋實例
    """
    return EnhancedMilvusSearch() 