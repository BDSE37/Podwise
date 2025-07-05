#!/usr/bin/env python3
"""
Podwise RAG Pipeline 客戶端

此模組提供完整的 RAG Pipeline 功能整合，包含：
- 三層 CrewAI 架構
- 智能 TAG 提取
- Podcast 格式化
- Web Search 整合
- 向量搜尋
- 用戶管理

作者: Podwise Team
版本: 3.0.0
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

# 導入核心組件
from core.crew_agents import AgentManager, UserQuery, AgentResponse
from core.chat_history_service import ChatHistoryService
from core.qwen3_llm_manager import Qwen3LLMManager

# 導入工具
from tools.keyword_mapper import KeywordMapper, CategoryResult
from tools.knn_recommender import KNNRecommender, PodcastItem, RecommendationResult
from tools.enhanced_vector_search import EnhancedVectorSearchTool
from tools.web_search_tool import WebSearchTool
from tools.podcast_formatter import PodcastFormatter, FormattedPodcast, PodcastRecommendationResult
from tools.smart_tag_extractor import SmartTagExtractor

# 導入配置
from config.integrated_config import get_config
from config.crewai_config import get_crewai_config, validate_config

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    """查詢請求數據類別"""
    query: str
    user_id: str
    session_id: Optional[str] = None
    category_filter: Optional[str] = None
    use_web_search: bool = True
    use_smart_tags: bool = True
    max_recommendations: int = 3


@dataclass
class QueryResponse:
    """查詢回應數據類別"""
    query: str
    response: str
    category: str
    confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning: str
    processing_time: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """系統狀態數據類別"""
    is_ready: bool
    components: Dict[str, bool]
    version: str
    timestamp: str


class RAGPipelineClient:
    """
    Podwise RAG Pipeline 客戶端
    
    提供完整的 RAG Pipeline 功能整合，包含三層 CrewAI 架構、
    智能 TAG 提取、Podcast 格式化等功能。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 RAG Pipeline 客戶端
        
        Args:
            config_path: 配置檔案路徑，如果為 None 則使用預設配置
        """
        self.config = get_config()
        self.crewai_config = get_crewai_config()
        
        # 核心組件
        self.agent_manager: Optional[AgentManager] = None
        self.keyword_mapper: Optional[KeywordMapper] = None
        self.knn_recommender: Optional[KNNRecommender] = None
        self.chat_history_service: Optional[ChatHistoryService] = None
        self.qwen3_manager: Optional[Qwen3LLMManager] = None
        self.vector_search_tool: Optional[EnhancedVectorSearchTool] = None
        self.web_search_tool: Optional[WebSearchTool] = None
        self.podcast_formatter: Optional[PodcastFormatter] = None
        self.smart_tag_extractor: Optional[SmartTagExtractor] = None
        
        # 系統狀態
        self._is_initialized = False
        self._initialization_lock = asyncio.Lock()
        
        logger.info("RAG Pipeline 客戶端初始化完成")
    
    async def initialize(self) -> None:
        """
        初始化所有核心組件
        
        Raises:
            RuntimeError: 初始化失敗時拋出
        """
        async with self._initialization_lock:
            if self._is_initialized:
                return
            
            try:
                logger.info("🚀 初始化 Podwise RAG Pipeline 客戶端...")
                
                # 驗證 CrewAI 配置
                if not validate_config(self.crewai_config):
                    raise ValueError("CrewAI 配置驗證失敗")
                
                # 初始化核心組件
                await self._initialize_core_components()
                
                # 載入示例數據
                await self._load_sample_data()
                
                self._is_initialized = True
                logger.info("✅ RAG Pipeline 客戶端初始化完成")
                
            except Exception as e:
                logger.error(f"❌ 初始化失敗: {str(e)}")
                raise RuntimeError(f"RAG Pipeline 初始化失敗: {str(e)}")
    
    async def _initialize_core_components(self) -> None:
        """初始化核心組件"""
        # 初始化 Keyword Mapper
        self.keyword_mapper = KeywordMapper()
        logger.info("✅ Keyword Mapper 初始化完成")
        
        # 初始化 KNN 推薦器
        self.knn_recommender = KNNRecommender(k=5, metric="cosine")
        logger.info("✅ KNN 推薦器初始化完成")
        
        # 初始化聊天歷史服務
        self.chat_history_service = ChatHistoryService()
        logger.info("✅ 聊天歷史服務初始化完成")
        
        # 初始化 Qwen3 LLM 管理器
        self.qwen3_manager = Qwen3LLMManager()
        logger.info("✅ Qwen3 LLM 管理器初始化完成")
        
        # 初始化向量搜尋工具
        self.vector_search_tool = EnhancedVectorSearchTool()
        logger.info("✅ 向量搜尋工具初始化完成")
        
        # 初始化 Web Search 工具
        self.web_search_tool = WebSearchTool()
        if self.web_search_tool.is_configured():
            logger.info("✅ Web Search 工具初始化完成 (OpenAI 可用)")
        else:
            logger.warning("⚠️ Web Search 工具初始化完成 (OpenAI 未配置)")
        
        # 初始化 Podcast 格式化工具
        self.podcast_formatter = PodcastFormatter()
        logger.info("✅ Podcast 格式化工具初始化完成")
        
        # 初始化智能 TAG 提取工具
        self.smart_tag_extractor = SmartTagExtractor()
        logger.info("✅ 智能 TAG 提取工具初始化完成")
        
        # 初始化 Agent Manager（三層 CrewAI 架構）
        self.agent_manager = AgentManager(self.crewai_config)
        logger.info("✅ Agent Manager 初始化完成")
    
    async def _load_sample_data(self) -> None:
        """載入示例 Podcast 數據"""
        if self.knn_recommender is None:
            return
        
        import numpy as np
        
        sample_items = [
            PodcastItem(
                rss_id="rss_001",
                title="股癌 EP310",
                description="台股投資分析與市場趨勢",
                category="商業",
                tags=["股票", "投資", "台股", "財經"],
                vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
                updated_at="2025-01-15",
                confidence=0.9
            ),
            PodcastItem(
                rss_id="rss_002",
                title="大人學 EP110",
                description="職涯發展與個人成長指南",
                category="教育",
                tags=["職涯", "成長", "技能", "學習"],
                vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
                updated_at="2025-01-14",
                confidence=0.85
            ),
            PodcastItem(
                rss_id="rss_003",
                title="財報狗 Podcast",
                description="財報分析與投資策略",
                category="商業",
                tags=["財報", "投資", "分析", "策略"],
                vector=np.array([0.9, 0.5, 0.8, 0.6, 0.9, 0.5, 0.8, 0.6]),
                updated_at="2025-01-13",
                confidence=0.88
            ),
            PodcastItem(
                rss_id="rss_004",
                title="生涯決策學 EP52",
                description="人生規劃與決策思維",
                category="教育",
                tags=["生涯", "決策", "規劃", "思維"],
                vector=np.array([0.4, 0.7, 0.5, 0.8, 0.4, 0.7, 0.5, 0.8]),
                updated_at="2025-01-12",
                confidence=0.82
            )
        ]
        
        self.knn_recommender.add_podcast_items(sample_items)
        logger.info(f"✅ 已載入 {len(sample_items)} 個示例 Podcast 項目")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        處理用戶查詢
        
        Args:
            request: 查詢請求
            
        Returns:
            QueryResponse: 查詢回應
            
        Raises:
            RuntimeError: 系統未初始化或處理失敗
        """
        if not self._is_initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            logger.info(f"處理查詢: {request.query} (用戶: {request.user_id})")
            
            # 1. 創建用戶查詢對象
            user_query = UserQuery(
                query=request.query,
                user_id=request.user_id,
                category=request.category_filter
            )
            
            # 2. 通過三層 CrewAI 架構處理
            agent_response = await self.agent_manager.process_query(
                query=request.query,
                user_id=request.user_id,
                category=request.category_filter
            )
            
            # 3. 獲取推薦
            recommendations = await self._get_recommendations(
                request.query, 
                agent_response,
                request.max_recommendations
            )
            
            # 4. 格式化回應
            response = await self._format_response(
                request.query,
                agent_response,
                recommendations,
                request
            )
            
            # 5. 記錄聊天歷史
            await self._log_chat_history(request, response)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                query=request.query,
                response=response,
                category=agent_response.metadata.get("category", "未知"),
                confidence=agent_response.confidence,
                recommendations=recommendations,
                reasoning=agent_response.reasoning,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                metadata=agent_response.metadata
            )
            
        except Exception as e:
            logger.error(f"處理查詢失敗: {str(e)}")
            raise RuntimeError(f"查詢處理失敗: {str(e)}")
    
    async def _get_recommendations(
        self, 
        query: str, 
        agent_response: AgentResponse,
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """獲取 Podcast 推薦"""
        try:
            # 使用 KNN 推薦器
            if self.knn_recommender:
                # 生成簡單向量（實際應用中應使用嵌入模型）
                import numpy as np
                query_vector = self._generate_simple_vector(query)
                
                result = self.knn_recommender.recommend(
                    query_vector, 
                    top_k=max_recommendations
                )
                
                recommendations = []
                for item in result.recommendations:
                    recommendations.append({
                        "rss_id": item.rss_id,
                        "title": item.title,
                        "description": item.description,
                        "category": item.category,
                        "tags": item.tags,
                        "confidence": item.confidence,
                        "updated_at": item.updated_at
                    })
                
                return recommendations
            
            return []
            
        except Exception as e:
            logger.error(f"獲取推薦失敗: {str(e)}")
            return []
    
    def _generate_simple_vector(self, text: str) -> 'np.ndarray':
        """生成簡單向量（用於演示）"""
        import numpy as np
        
        # 簡單的向量生成邏輯（實際應用中應使用嵌入模型）
        vector = np.random.rand(8)
        vector = vector / np.linalg.norm(vector)  # 正規化
        return vector
    
    async def _format_response(
        self,
        query: str,
        agent_response: AgentResponse,
        recommendations: List[Dict[str, Any]],
        request: QueryRequest
    ) -> str:
        """格式化回應"""
        try:
            # 使用 Podcast 格式化工具
            if self.podcast_formatter and recommendations:
                # 提取智能 TAG
                if request.use_smart_tags and self.smart_tag_extractor:
                    extracted_tags = self.smart_tag_extractor.extract_tags_from_query(query)
                    logger.info(f"提取的 TAG: {extracted_tags}")
                
                # 格式化 Podcast 推薦
                formatted_result = self.podcast_formatter.format_recommendations(
                    recommendations=recommendations,
                    query=query,
                    max_recommendations=request.max_recommendations
                )
                
                return formatted_result.formatted_response
            
            # 回退到原始回應
            return agent_response.content
            
        except Exception as e:
            logger.error(f"格式化回應失敗: {str(e)}")
            return agent_response.content
    
    async def _log_chat_history(self, request: QueryRequest, response: QueryResponse) -> None:
        """記錄聊天歷史"""
        try:
            if self.chat_history_service:
                await self.chat_history_service.save_multi_agent_message(
                    user_id=request.user_id,
                    session_id=request.session_id or "default",
                    role="user",
                    content=request.query,
                    agents_used=["rag_pipeline_client"],
                    confidence=response.confidence,
                    processing_time=response.processing_time,
                    metadata={
                        "category": response.category,
                        "recommendations_count": len(response.recommendations)
                    }
                )
        except Exception as e:
            logger.error(f"記錄聊天歷史失敗: {str(e)}")
    
    async def validate_user(self, user_id: str) -> Dict[str, Any]:
        """
        驗證用戶
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            Dict[str, Any]: 驗證結果
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            # 檢查用戶歷史
            if self.chat_history_service:
                history = await self.chat_history_service.get_chat_history(
                    user_id=user_id, 
                    limit=10
                )
                
                has_history = len(history) > 0
                preferred_category = self._analyze_user_preference(history) if has_history else None
                
                return {
                    "user_id": user_id,
                    "is_valid": True,
                    "has_history": has_history,
                    "preferred_category": preferred_category,
                    "message": "用戶驗證成功"
                }
            
            return {
                "user_id": user_id,
                "is_valid": True,
                "has_history": False,
                "preferred_category": None,
                "message": "用戶驗證成功（無歷史記錄）"
            }
            
        except Exception as e:
            logger.error(f"用戶驗證失敗: {str(e)}")
            return {
                "user_id": user_id,
                "is_valid": False,
                "has_history": False,
                "preferred_category": None,
                "message": f"用戶驗證失敗: {str(e)}"
            }
    
    def _analyze_user_preference(self, history: List[Dict[str, Any]]) -> Optional[str]:
        """分析用戶偏好"""
        if not history:
            return None
        
        category_counts = {}
        for record in history:
            category = record.get("metadata", {}).get("category")
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            return max(category_counts, key=category_counts.get)
        
        return None
    
    async def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取聊天歷史
        
        Args:
            user_id: 用戶 ID
            limit: 返回數量限制
            
        Returns:
            List[Dict[str, Any]]: 聊天歷史
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if self.chat_history_service:
                return await self.chat_history_service.get_chat_history(
                    user_id=user_id, 
                    limit=limit
                )
            return []
            
        except Exception as e:
            logger.error(f"獲取聊天歷史失敗: {str(e)}")
            return []
    
    def get_system_status(self) -> SystemStatus:
        """
        獲取系統狀態
        
        Returns:
            SystemStatus: 系統狀態
        """
        components = {
            "agent_manager": self.agent_manager is not None,
            "keyword_mapper": self.keyword_mapper is not None,
            "knn_recommender": self.knn_recommender is not None,
            "chat_history_service": self.chat_history_service is not None,
            "qwen3_manager": self.qwen3_manager is not None,
            "vector_search_tool": self.vector_search_tool is not None,
            "web_search_tool": self.web_search_tool is not None,
            "podcast_formatter": self.podcast_formatter is not None,
            "smart_tag_extractor": self.smart_tag_extractor is not None
        }
        
        return SystemStatus(
            is_ready=self._is_initialized,
            components=components,
            version="3.0.0",
            timestamp=datetime.now().isoformat()
        )
    
    async def close(self) -> None:
        """關閉客戶端並清理資源"""
        try:
            if self.chat_history_service:
                self.chat_history_service.close()
            
            logger.info("RAG Pipeline 客戶端已關閉")
            
        except Exception as e:
            logger.error(f"關閉客戶端失敗: {str(e)}")


# 全域客戶端實例
_client_instance: Optional[RAGPipelineClient] = None


async def get_rag_pipeline_client() -> RAGPipelineClient:
    """
    獲取 RAG Pipeline 客戶端實例（單例模式）
    
    Returns:
        RAGPipelineClient: 客戶端實例
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = RAGPipelineClient()
        await _client_instance.initialize()
    
    return _client_instance


async def close_rag_pipeline_client() -> None:
    """關閉 RAG Pipeline 客戶端實例"""
    global _client_instance
    
    if _client_instance:
        await _client_instance.close()
        _client_instance = None


# 便捷函數
async def process_query_simple(
    query: str, 
    user_id: str, 
    session_id: Optional[str] = None
) -> QueryResponse:
    """
    簡單的查詢處理函數
    
    Args:
        query: 查詢內容
        user_id: 用戶 ID
        session_id: 會話 ID
        
    Returns:
        QueryResponse: 查詢回應
    """
    client = await get_rag_pipeline_client()
    
    request = QueryRequest(
        query=query,
        user_id=user_id,
        session_id=session_id
    )
    
    return await client.process_query(request)


async def validate_user_simple(user_id: str) -> Dict[str, Any]:
    """
    簡單的用戶驗證函數
    
    Args:
        user_id: 用戶 ID
        
    Returns:
        Dict[str, Any]: 驗證結果
    """
    client = await get_rag_pipeline_client()
    return await client.validate_user(user_id)


async def get_chat_history_simple(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    簡單的聊天歷史獲取函數
    
    Args:
        user_id: 用戶 ID
        limit: 返回數量限制
        
    Returns:
        List[Dict[str, Any]]: 聊天歷史
    """
    client = await get_rag_pipeline_client()
    return await client.get_chat_history(user_id, limit)


if __name__ == "__main__":
    """測試和演示"""
    async def main():
        """主函數"""
        try:
            # 獲取客戶端
            client = await get_rag_pipeline_client()
            
            # 檢查系統狀態
            status = client.get_system_status()
            print(f"系統狀態: {status}")
            
            # 測試查詢
            response = await process_query_simple(
                query="我想了解台積電的投資分析",
                user_id="test_user_001"
            )
            
            print(f"查詢回應: {response}")
            
            # 測試用戶驗證
            validation = await validate_user_simple("test_user_001")
            print(f"用戶驗證: {validation}")
            
            # 測試聊天歷史
            history = await get_chat_history_simple("test_user_001", limit=5)
            print(f"聊天歷史: {history}")
            
        except Exception as e:
            print(f"測試失敗: {str(e)}")
        
        finally:
            # 關閉客戶端
            await close_rag_pipeline_client()
    
    # 執行測試
    asyncio.run(main()) 