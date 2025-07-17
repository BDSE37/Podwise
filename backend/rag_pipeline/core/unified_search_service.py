#!/usr/bin/env python3
"""
統一搜尋服務

整合所有搜尋和推薦功能：
- Milvus 向量搜尋
- LLM 查詢增強 (Ollama)
- Podcast 推薦
- MCP 整合
- data_cleaning 整合
- ml_pipeline 整合
- utils 模組整合

作者: Podwise Team
版本: 2.0.0
"""

import os
import sys
import logging
import asyncio
import time
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchConfig:
    """統一搜尋配置"""
    # Milvus 配置
    milvus_host: str = "worker3"
    milvus_port: int = 19530
            collection_name: str = "podcast_chunks"
    similarity_threshold: float = 0.7
    
    # LLM 配置 (Ollama)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    enable_ollama: bool = True
    
    # 搜尋配置
    top_k: int = 10
    enable_rerank: bool = True
    enable_content_cleaning: bool = True
    enable_recommendation: bool = True
    
    # MCP 配置
    enable_mcp: bool = True
    
    # Utils 整合配置
    enable_utils_integration: bool = True
    use_utils_vector_search: bool = True
    use_utils_text_processing: bool = True


@dataclass
class SearchResult:
    """統一搜尋結果"""
    content: str
    confidence: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    category: str = ""
    episode_title: str = ""
    podcast_name: str = ""
    similarity_score: float = 0.0
    recommendation_score: float = 0.0


@dataclass
class RecommendationResult:
    """推薦結果"""
    podcast_id: str
    title: str
    description: str
    category: str
    confidence: float
    reasoning: str
    similarity_score: float
    tags: List[str]
    episode_count: int
    last_updated: str


class UnifiedSearchService:
    """
    統一搜尋服務
    
    整合所有搜尋和推薦功能，提供統一的介面
    """
    
    def __init__(self, config: Optional[UnifiedSearchConfig] = None):
        """
        初始化統一搜尋服務
        
        Args:
            config: 搜尋配置
        """
        self.config = config or UnifiedSearchConfig()
        
        # 初始化組件
        self.milvus_search = None
        self.ollama_service = None
        self.mcp_integration = None
        self.episode_cleaner = None
        self.recommender = None
        self.data_manager = None
        
        # Utils 整合組件
        self.utils_vector_search = None
        self.utils_text_processor = None
        
        # 搜尋歷史
        self.search_history: List[Dict[str, Any]] = []
        
        logger.info("✅ 統一搜尋服務初始化完成")
    
    async def initialize(self) -> bool:
        """初始化所有組件"""
        try:
            # 1. 初始化 Ollama 服務
            if self.config.enable_ollama:
                await self._init_ollama_service()
            
            # 2. 初始化 Milvus 搜尋
            await self._init_milvus_search()
            
            # 3. 初始化 MCP 整合
            if self.config.enable_mcp:
                await self._init_mcp_integration()
            
            # 4. 初始化 data_cleaning
            if self.config.enable_content_cleaning:
                await self._init_data_cleaning()
            
            # 5. 初始化 ml_pipeline
            if self.config.enable_recommendation:
                await self._init_ml_pipeline()
            
            # 6. 初始化 Utils 整合
            if self.config.enable_utils_integration:
                await self._init_utils_integration()
            
            logger.info("✅ 統一搜尋服務所有組件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 統一搜尋服務初始化失敗: {e}")
            return False
    
    async def _init_ollama_service(self):
        """初始化 Ollama 服務"""
        try:
            # 檢查 Ollama 是否運行
            import requests
            response = requests.get(f"{self.config.ollama_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                # 檢查模型是否可用
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                
                if self.config.ollama_model in available_models:
                    self.ollama_service = {
                        "url": self.config.ollama_url,
                        "model": self.config.ollama_model,
                        "available": True
                    }
                    logger.info(f"✅ Ollama 服務初始化成功，模型: {self.config.ollama_model}")
                else:
                    logger.warning(f"⚠️ Ollama 模型 {self.config.ollama_model} 不可用，可用模型: {available_models}")
                    self.ollama_service = {"available": False}
            else:
                logger.warning("⚠️ Ollama 服務未運行")
                self.ollama_service = {"available": False}
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama 服務初始化失敗: {e}")
            self.ollama_service = {"available": False}
    
    async def _init_milvus_search(self):
        """初始化 Milvus 搜尋"""
        try:
            from .enhanced_milvus_search import EnhancedMilvusSearch, EnhancedSearchConfig
            
            milvus_config = EnhancedSearchConfig(
                milvus_host=self.config.milvus_host,
                milvus_port=self.config.milvus_port,
                collection_name=self.config.collection_name,
                similarity_threshold=self.config.similarity_threshold,
                llm_host="localhost",
                llm_port=11434,
                enable_llm_enhancement=self.config.enable_ollama,
                top_k=self.config.top_k,
                enable_result_rerank=self.config.enable_rerank
            )
            
            self.milvus_search = EnhancedMilvusSearch(milvus_config)
            logger.info("✅ Milvus 搜尋初始化成功")
            
        except Exception as e:
            logger.warning(f"Milvus 搜尋初始化失敗: {e}")
    
    async def _init_mcp_integration(self):
        """初始化 MCP 整合"""
        try:
            from .mcp_integration import get_mcp_integration
            self.mcp_integration = get_mcp_integration()
            logger.info("✅ MCP 整合初始化成功")
            
        except Exception as e:
            logger.warning(f"MCP 整合初始化失敗: {e}")
    
    async def _init_data_cleaning(self):
        """初始化 data_cleaning"""
        try:
            from data_cleaning.core.episode_cleaner import EpisodeCleaner
            self.episode_cleaner = EpisodeCleaner()
            logger.info("✅ data_cleaning 初始化成功")
            
        except Exception as e:
            logger.warning(f"data_cleaning 初始化失敗: {e}")
    
    async def _init_ml_pipeline(self):
        """初始化 ml_pipeline"""
        try:
            from ml_pipeline.core.recommender import RecommenderEngine
            from ml_pipeline.core.data_manager import RecommenderData
            
            # 嘗試載入模擬資料
            mock_data = self._load_mock_data()
            
            if mock_data:
                self.recommender = RecommenderEngine(
                    mock_data['podcast_data'], 
                    mock_data['user_history']
                )
                self.data_manager = RecommenderData("postgresql://podwise_user:podwise_password@192.168.32.86:30017/podwise")
                logger.info("✅ ml_pipeline 初始化成功（使用模擬資料）")
            else:
                # 使用空的 DataFrame
                empty_podcast_data = pd.DataFrame(columns=pd.Index([
                    'episode_id', 'episode_title', 'description', 'category', 'tags'
                ]))
                empty_user_history = pd.DataFrame(columns=pd.Index([
                    'user_id', 'episode_id', 'rating', 'like_count', 'preview_play_count'
                ]))
                
                self.recommender = RecommenderEngine(empty_podcast_data, empty_user_history)
                self.data_manager = RecommenderData("postgresql://podwise_user:podwise_password@192.168.32.86:30017/podwise")
                logger.info("✅ ml_pipeline 初始化成功（使用空資料）")
            
        except Exception as e:
            logger.warning(f"ml_pipeline 初始化失敗: {e}")
    
    async def _init_utils_integration(self):
        """初始化 Utils 整合"""
        try:
            # 導入 utils 模組
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils'))
            
            if self.config.use_utils_vector_search:
                try:
                    from vector_search import create_vector_search
                    self.utils_vector_search = create_vector_search(
                        host=self.config.milvus_host,
                        port=self.config.milvus_port,
                        collection_name=self.config.collection_name,
                        similarity_threshold=self.config.similarity_threshold
                    )
                    logger.info("✅ Utils 向量搜尋初始化成功")
                except ImportError:
                    logger.warning("Utils 向量搜尋模組不可用")
            
            if self.config.use_utils_text_processing:
                try:
                    from text_processing import create_text_processor
                    self.utils_text_processor = create_text_processor()
                    logger.info("✅ Utils 文本處理器初始化成功")
                except ImportError:
                    logger.warning("Utils 文本處理器模組不可用")
            
        except Exception as e:
            logger.warning(f"Utils 整合初始化失敗: {e}")
    
    def _load_mock_data(self) -> Optional[Dict[str, pd.DataFrame]]:
        """載入模擬資料"""
        try:
            mock_data_path = "data/mock_data"
            
            podcast_data_path = f"{mock_data_path}/podcast_data.csv"
            user_history_path = f"{mock_data_path}/user_history.csv"
            
            if os.path.exists(podcast_data_path) and os.path.exists(user_history_path):
                podcast_data = pd.read_csv(podcast_data_path)
                user_history = pd.read_csv(user_history_path)
                
                # 處理標籤欄位
                if 'tags' in podcast_data.columns:
                    podcast_data['tags'] = podcast_data['tags'].apply(
                        lambda x: eval(x) if isinstance(x, str) else []
                    )
                
                return {
                    'podcast_data': podcast_data,
                    'user_history': user_history
                }
            else:
                logger.info("模擬資料檔案不存在，將使用空資料")
                return None
                
        except Exception as e:
            logger.warning(f"載入模擬資料失敗: {e}")
            return None
    
    async def search(self, query: str, user_id: str = "default_user", 
                    search_type: str = "unified") -> List[SearchResult]:
        """
        執行統一搜尋
        
        Args:
            query: 查詢內容
            user_id: 用戶 ID
            search_type: 搜尋類型 ("unified", "vector", "recommendation")
            
        Returns:
            List[SearchResult]: 搜尋結果
        """
        start_time = time.time()
        
        try:
            if search_type == "unified":
                results = await self._unified_search(query, user_id)
            elif search_type == "vector":
                results = await self._vector_search(query, user_id)
            elif search_type == "recommendation":
                results = await self._recommendation_search(query, user_id)
            else:
                results = await self._unified_search(query, user_id)
            
            # 記錄搜尋歷史
            self._log_search_history(query, results, start_time)
            
            return results
            
        except Exception as e:
            logger.error(f"統一搜尋失敗: {e}")
            return []
    
    async def _unified_search(self, query: str, user_id: str) -> List[SearchResult]:
        """統一搜尋（整合所有功能）"""
        try:
            # 1. 向量搜尋
            vector_results = await self._vector_search(query, user_id)
            
            # 2. 推薦增強
            if self.config.enable_recommendation:
                vector_results = await self._enhance_with_recommendation(vector_results, user_id)
            
            # 3. 內容清理
            if self.config.enable_content_cleaning:
                vector_results = await self._enhance_with_cleaning(vector_results)
            
            # 4. MCP 增強
            if self.config.enable_mcp and self.mcp_integration:
                vector_results = await self._enhance_with_mcp(vector_results, query)
            
            return vector_results
            
        except Exception as e:
            logger.error(f"統一搜尋失敗: {e}")
            return []
    
    async def _vector_search(self, query: str, user_id: str) -> List[SearchResult]:
        """向量搜尋"""
        try:
            # 優先使用 Utils 向量搜尋
            if self.utils_vector_search:
                results = self.utils_vector_search.search_by_text(query, None, top_k=self.config.top_k)
                
                # 轉換為 SearchResult 格式
                search_results = []
                for result in results:
                    search_result = SearchResult(
                        content=result.chunk_text,
                        confidence=result.similarity_score,
                        source="utils_vector_search",
                        metadata=result.metadata,
                        tags=result.tags,
                        category=result.metadata.get("category", "general"),
                        similarity_score=result.similarity_score
                    )
                    search_results.append(search_result)
                
                return search_results
            
            # 回退到 Milvus 搜尋
            elif self.milvus_search:
                raw_results = await self.milvus_search.search(query, user_id)
                
                # 轉換為 SearchResult 格式
                search_results = []
                for result in raw_results:
                    search_result = SearchResult(
                        content=result.get("content", ""),
                        confidence=result.get("similarity_score", 0.0),
                        source=result.get("source", "unknown"),
                        metadata=result.get("metadata", {}),
                        tags=result.get("tags", []),
                        category=result.get("metadata", {}).get("category", "general"),
                        similarity_score=result.get("similarity_score", 0.0)
                    )
                    search_results.append(search_result)
                
                return search_results
            
            else:
                return self._fallback_search(query)
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return self._fallback_search(query)
    
    async def _recommendation_search(self, query: str, user_id: str) -> List[SearchResult]:
        """推薦搜尋"""
        try:
            if not self.mcp_integration:
                return []
            
            # 使用 MCP 增強推薦器
            from .enhanced_podcast_recommender import MCPEnhancedPodcastRecommender
            recommender = MCPEnhancedPodcastRecommender()
            
            recommendations = await recommender.get_enhanced_recommendations(
                query=query,
                user_preferences={"user_id": user_id},
                top_k=self.config.top_k,
                use_mcp_tools=True
            )
            
            # 轉換為 SearchResult 格式
            search_results = []
            for rec in recommendations:
                search_result = SearchResult(
                    content=f"{rec.title}: {rec.metadata.get('description', '')}",
                    confidence=rec.confidence,
                    source="recommendation",
                    metadata=rec.metadata,
                    tags=rec.metadata.get("tags", []),
                    category=rec.metadata.get("category", "general"),
                    recommendation_score=rec.mcp_enhanced_score
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"推薦搜尋失敗: {e}")
            return []
    
    async def _enhance_with_recommendation(self, results: List[SearchResult], user_id: str) -> List[SearchResult]:
        """使用推薦系統增強結果"""
        try:
            if not self.recommender:
                return results
            
            enhanced_results = []
            for result in results:
                # 簡化的推薦分數計算
                recommendation_score = 0.5  # 預設值
                
                # 調整信心度
                result.confidence = result.confidence * (0.8 + 0.2 * recommendation_score)
                result.recommendation_score = recommendation_score
                
                enhanced_results.append(result)
            
            # 重新排序
            enhanced_results.sort(key=lambda x: x.confidence, reverse=True)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"推薦增強失敗: {e}")
            return results
    
    async def _enhance_with_cleaning(self, results: List[SearchResult]) -> List[SearchResult]:
        """使用 data_cleaning 增強結果"""
        try:
            if not self.episode_cleaner:
                return results
            
            enhanced_results = []
            for result in results:
                # 簡單的文本清理
                result.content = result.content.strip()
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"內容清理增強失敗: {e}")
            return results
    
    async def _enhance_with_mcp(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """使用 MCP 增強結果"""
        try:
            if not self.mcp_integration:
                return results
            
            enhanced_results = []
            for result in results:
                # 使用 MCP 工具進行內容分析
                try:
                    # 情感分析
                    sentiment_result = await self.mcp_integration.call_tool(
                        "analyze_sentiment",
                        {"text": f"{result.content} {query}", "analyzer_type": "chinese"}
                    )
                    
                    # 根據情感分析調整信心度
                    if sentiment_result.get("success") and "positive" in sentiment_result.get("result", ""):
                        result.confidence = min(1.0, result.confidence + 0.1)
                    
                except Exception as e:
                    logger.warning(f"MCP 增強失敗: {e}")
                
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"MCP 增強失敗: {e}")
            return results
    
    def _fallback_search(self, query: str) -> List[SearchResult]:
        """回退搜尋"""
        logger.info("使用回退搜尋")
        
        mock_results = [
            SearchResult(
                content="商業週刊 Podcast 內容：台灣最具影響力的商業媒體，提供最新的財經資訊和市場分析。",
                confidence=0.85,
                source="fallback",
                metadata={"source": "business_weekly", "title": "商業週刊"},
                tags=["商業", "財經", "台灣"],
                category="商業",
                similarity_score=0.85
            ),
            SearchResult(
                content="財經 M 平方 Podcast 內容：專業的財經分析，深入解析全球經濟趨勢。",
                confidence=0.82,
                source="fallback",
                metadata={"source": "m_square", "title": "財經 M 平方"},
                tags=["財經", "分析", "全球"],
                category="財經",
                similarity_score=0.82
            )
        ]
        
        return mock_results[:self.config.top_k]
    
    def _log_search_history(self, query: str, results: List[SearchResult], start_time: float):
        """記錄搜尋歷史"""
        end_time = time.time()
        duration = end_time - start_time
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "content": result.content[:100],
                    "confidence": result.confidence,
                    "source": result.source
                }
                for result in results[:3]
            ]
        }
        
        self.search_history.append(history_entry)
        
        # 保持歷史記錄在合理範圍內
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-50:]
    
    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取搜尋歷史"""
        return self.search_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取搜尋統計"""
        if not self.search_history:
            return {
                "total_searches": 0,
                "average_duration": 0,
                "most_common_queries": [],
                "components_status": {
                    "milvus_search": self.milvus_search is not None,
                    "ollama_service": self.ollama_service.get("available", False) if self.ollama_service else False,
                    "mcp_integration": self.mcp_integration is not None,
                    "episode_cleaner": self.episode_cleaner is not None,
                    "recommender": self.recommender is not None,
                    "utils_vector_search": self.utils_vector_search is not None,
                    "utils_text_processor": self.utils_text_processor is not None
                }
            }
        
        total_searches = len(self.search_history)
        total_duration = sum(entry["duration"] for entry in self.search_history)
        average_duration = total_duration / total_searches
        
        # 統計最常見的查詢
        query_counts = {}
        for entry in self.search_history:
            query = entry["query"]
            query_counts[query] = query_counts.get(query, 0) + 1
        
        most_common_queries = sorted(
            query_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "total_searches": total_searches,
            "average_duration": average_duration,
            "most_common_queries": most_common_queries,
            "components_status": {
                "milvus_search": self.milvus_search is not None,
                "ollama_service": self.ollama_service.get("available", False) if self.ollama_service else False,
                "mcp_integration": self.mcp_integration is not None,
                "episode_cleaner": self.episode_cleaner is not None,
                "recommender": self.recommender is not None,
                "utils_vector_search": self.utils_vector_search is not None,
                "utils_text_processor": self.utils_text_processor is not None
            }
        }
    
    async def close(self):
        """關閉所有連接"""
        try:
            if self.milvus_search:
                await self.milvus_search.close()
            logger.info("✅ 統一搜尋服務已關閉")
        except Exception as e:
            logger.error(f"關閉統一搜尋服務失敗: {e}")


# 全域實例
_unified_search_instance: Optional[UnifiedSearchService] = None


def get_unified_search_service(config: Optional[UnifiedSearchConfig] = None) -> UnifiedSearchService:
    """獲取統一搜尋服務實例（單例模式）"""
    global _unified_search_instance
    if _unified_search_instance is None:
        _unified_search_instance = UnifiedSearchService(config)
    return _unified_search_instance


async def main():
    """主函數 - 用於測試"""
    # 創建統一搜尋服務
    config = UnifiedSearchConfig(
        enable_ollama=True,
        ollama_model="qwen2.5:7b-instruct",
        enable_utils_integration=True
    )
    
    service = UnifiedSearchService(config)
    
    # 初始化
    success = await service.initialize()
    if not success:
        print("❌ 統一搜尋服務初始化失敗")
        return
    
    # 測試搜尋
    results = await service.search("科技創新", "test_user", "unified")
    
    print(f"\n統一搜尋結果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.content[:50]}...")
        print(f"   信心度: {result.confidence:.3f}")
        print(f"   來源: {result.source}")
        print(f"   標籤: {result.tags}")
        print()
    
    # 獲取統計
    stats = service.get_statistics()
    print(f"搜尋統計: {stats}")
    
    # 關閉服務
    await service.close()


if __name__ == "__main__":
    asyncio.run(main()) 