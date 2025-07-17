#!/usr/bin/env python3
"""
RAG Pipeline Tools

統一的工具模組，提供所有 RAG Pipeline 所需的功能工具
遵循 Google Clean Code 原則，確保模組化設計

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)


# 導入所有工具模組
try:
    from .cross_db_text_fetcher import CrossDBTextFetcher
    CROSS_DB_FETCHER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrossDBTextFetcher 導入失敗: {e}")
    CROSS_DB_FETCHER_AVAILABLE = False
    CrossDBTextFetcher = None

try:
    from .summary_generator import SummaryGenerator
    SUMMARY_GENERATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SummaryGenerator 導入失敗: {e}")
    SUMMARY_GENERATOR_AVAILABLE = False
    SummaryGenerator = None

try:
    from .similarity_matcher import SimilarityMatcher
    SIMILARITY_MATCHER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SimilarityMatcher 導入失敗: {e}")
    SIMILARITY_MATCHER_AVAILABLE = False
    SimilarityMatcher = None

try:
    from .podcast_formatter import PodcastFormatter
    PODCAST_FORMATTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PodcastFormatter 導入失敗: {e}")
    PODCAST_FORMATTER_AVAILABLE = False
    PodcastFormatter = None

try:
    from .web_search_tool import WebSearchExpert
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"WebSearchExpert 導入失敗: {e}")
    WEB_SEARCH_AVAILABLE = False
    WebSearchExpert = None

try:
    from .vector_search_tool import VectorSearchTool, get_vector_search_tool
    VECTOR_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"VectorSearchTool 導入失敗: {e}")
    VECTOR_SEARCH_AVAILABLE = False
    VectorSearchTool = None
    get_vector_search_tool = None


class ToolsManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self) -> None:
        """初始化所有工具"""
        # 初始化跨資料庫文本擷取器
        if CROSS_DB_FETCHER_AVAILABLE and CrossDBTextFetcher is not None:
            try:
                self.tools['cross_db_fetcher'] = CrossDBTextFetcher()
                logger.info("CrossDBTextFetcher 初始化成功")
            except Exception as e:
                logger.error(f"CrossDBTextFetcher 初始化失敗: {e}")
        
        # 初始化摘要生成器
        if SUMMARY_GENERATOR_AVAILABLE and SummaryGenerator is not None:
            try:
                self.tools['summary_generator'] = SummaryGenerator()
                logger.info("SummaryGenerator 初始化成功")
            except Exception as e:
                logger.error(f"SummaryGenerator 初始化失敗: {e}")
        
        # 初始化相似度匹配器
        if SIMILARITY_MATCHER_AVAILABLE and SimilarityMatcher is not None:
            try:
                self.tools['similarity_matcher'] = SimilarityMatcher()
                logger.info("SimilarityMatcher 初始化成功")
            except Exception as e:
                logger.error(f"SimilarityMatcher 初始化失敗: {e}")
        
        # 初始化 Podcast 格式化器
        if PODCAST_FORMATTER_AVAILABLE and PodcastFormatter is not None:
            try:
                self.tools['podcast_formatter'] = PodcastFormatter()
                logger.info("PodcastFormatter 初始化成功")
            except Exception as e:
                logger.error(f"PodcastFormatter 初始化失敗: {e}")
        
        # 初始化 Web 搜尋專家
        if WEB_SEARCH_AVAILABLE and WebSearchExpert is not None:
            try:
                self.tools['web_search'] = WebSearchExpert()
                logger.info("WebSearchExpert 初始化成功")
            except Exception as e:
                logger.error(f"WebSearchExpert 初始化失敗: {e}")
        
        # 初始化向量搜尋工具
        if VECTOR_SEARCH_AVAILABLE and VectorSearchTool is not None and get_vector_search_tool is not None:
            try:
                self.tools['vector_search'] = get_vector_search_tool()
                logger.info("VectorSearchTool 初始化成功")
            except Exception as e:
                logger.error(f"VectorSearchTool 初始化失敗: {e}")
    
    def get_tool(self, name: str) -> Optional[Any]:
        """獲取指定工具"""
        return self.tools.get(name)
    
    def get_cross_db_fetcher(self) -> Optional[Any]:
        """獲取跨資料庫文本擷取器"""
        return self.get_tool('cross_db_fetcher')
    
    def get_summary_generator(self) -> Optional[Any]:
        """獲取摘要生成器"""
        return self.get_tool('summary_generator')
    
    def get_similarity_matcher(self) -> Optional[Any]:
        """獲取相似度匹配器"""
        return self.get_tool('similarity_matcher')
    
    def get_podcast_formatter(self) -> Optional[Any]:
        """獲取 Podcast 格式化器"""
        return self.get_tool('podcast_formatter')
    
    def get_web_search(self) -> Optional[Any]:
        """獲取 Web 搜尋專家"""
        return self.get_tool('web_search')
    
    def get_vector_search(self) -> Optional[Any]:
        """獲取向量搜尋工具"""
        return self.get_tool('vector_search')
    
    def get_available_tools(self) -> List[str]:
        """獲取可用工具列表"""
        return list(self.tools.keys())
    
    def get_tools_status(self) -> Dict[str, bool]:
        """獲取工具狀態"""
        return {
            'cross_db_fetcher': CROSS_DB_FETCHER_AVAILABLE,
            'summary_generator': SUMMARY_GENERATOR_AVAILABLE,
            'similarity_matcher': SIMILARITY_MATCHER_AVAILABLE,
            'podcast_formatter': PODCAST_FORMATTER_AVAILABLE,
            'web_search': WEB_SEARCH_AVAILABLE,
            'vector_search': VECTOR_SEARCH_AVAILABLE
        }


# 全域工具管理器實例
tools_manager = ToolsManager()


def get_tools_manager() -> ToolsManager:
    """獲取工具管理器"""
    return tools_manager


def get_cross_db_fetcher() -> Optional[Any]:
    """獲取跨資料庫文本擷取器"""
    return tools_manager.get_cross_db_fetcher()


def get_summary_generator() -> Optional[Any]:
    """獲取摘要生成器"""
    return tools_manager.get_summary_generator()


def get_similarity_matcher() -> Optional[Any]:
    """獲取相似度匹配器"""
    return tools_manager.get_similarity_matcher()


def get_podcast_formatter() -> Optional[Any]:
    """獲取 Podcast 格式化器"""
    return tools_manager.get_podcast_formatter()


def get_web_search() -> Optional[Any]:
    """獲取 Web 搜尋專家"""
    return tools_manager.get_web_search()

def get_vector_search() -> Optional[Any]:
    """獲取向量搜尋工具"""
    return tools_manager.get_vector_search()


def get_available_tools() -> List[str]:
    """獲取可用工具列表"""
    return tools_manager.get_available_tools()


def get_tools_status() -> Dict[str, bool]:
    """獲取工具狀態"""
    return tools_manager.get_tools_status()


# 便捷函數
async def fetch_text_from_databases(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """從多個資料庫擷取文本"""
    fetcher = get_cross_db_fetcher()
    if fetcher:
        return await fetcher.fetch_text(query, limit)
    return []


async def generate_summary(text: str, max_length: int = 150) -> Optional[str]:
    """生成文本摘要"""
    generator = get_summary_generator()
    if generator:
        return await generator.generate_summary(text, max_length)
    return None


def calculate_similarity(vector1: List[float], vector2: List[float]) -> float:
    """計算向量相似度"""
    matcher = get_similarity_matcher()
    if matcher:
        return matcher.calculate_cosine_similarity(vector1, vector2)
    return 0.0


def format_podcast_data(podcast_data: List[Dict[str, Any]], query: str = "", max_recommendations: int = 3) -> Any:
    """格式化 Podcast 資料"""
    formatter = get_podcast_formatter()
    if formatter:
        return formatter.format_podcast_recommendations(podcast_data, query, max_recommendations)
    return podcast_data


async def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """執行 Web 搜尋"""
    web_search = get_web_search()
    if web_search:
        try:
            from .web_search_tool import SearchRequest
            request = SearchRequest(query=query, max_results=max_results)
            response = await web_search.search(request)
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                    "confidence": result.confidence
                }
                for result in response.results
            ]
        except Exception as e:
            logger.error(f"網路搜尋失敗: {e}")
            return []
    return []


def search_vectors(query_vector: np.ndarray, top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """便捷的向量搜尋函數"""
    vector_search = get_vector_search()
    if vector_search:
        try:
            results = vector_search.search_by_vector(query_vector, top_k)
            return [
                {
                    "chunk_id": result.chunk_id,
                    "chunk_text": result.chunk_text,
                    "similarity_score": result.similarity_score,
                    "episode_title": result.episode_title,
                    "podcast_name": result.podcast_name,
                    "tags": result.tags
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return []
    return []


if __name__ == "__main__":
    # 測試工具管理器
    print("RAG Pipeline Tools 測試")
    print("=" * 50)
    
    # 顯示工具狀態
    status = get_tools_status()
    print("工具狀態:")
    for tool_name, is_available in status.items():
        status_icon = "✅" if is_available else "❌"
        print(f"  {tool_name}: {status_icon}")
    
    # 顯示可用工具
    available_tools = get_available_tools()
    print(f"\n可用工具: {available_tools}")
    
    # 測試工具管理器
    manager = get_tools_manager()
    print(f"\n工具管理器初始化完成，共 {len(manager.tools)} 個工具") 