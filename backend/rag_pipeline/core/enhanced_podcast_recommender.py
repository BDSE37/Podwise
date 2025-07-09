#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 增強 Podcast 推薦器

整合 MCP (Model Context Protocol) 以提供更智能的推薦功能：
- 動態工具調用
- 外部資源整合
- 上下文感知推薦
- 多模態分析

作者: Podwise Team
版本: 2.0.0
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .mcp_integration import get_mcp_integration, PodwiseMCPIntegration
from .langfuse_tracking import langfuse_trace

logger = logging.getLogger(__name__)


@dataclass
class MCPEnhancedRecommendation:
    """MCP 增強推薦結果"""
    podcast_id: str
    title: str
    score: float
    mcp_enhanced_score: float
    ranking_factors: Dict[str, float]
    mcp_tools_used: List[str]
    confidence: float
    metadata: Dict[str, Any]


class MCPEnhancedPodcastRecommender:
    """
    MCP 增強 Podcast 推薦器
    
    整合 Model Context Protocol 以提供更智能的推薦功能
    """
    
    def __init__(self, 
                 use_mcp: bool = True,
                 mcp_config_path: str = "config/mcp_config.yaml"):
        """
        初始化 MCP 增強推薦器
        
        Args:
            use_mcp: 是否啟用 MCP 功能
            mcp_config_path: MCP 配置檔案路徑
        """
        self.use_mcp = use_mcp
        self.mcp_config_path = mcp_config_path
        
        # MCP 整合實例
        self.mcp_integration: Optional[PodwiseMCPIntegration] = None
        if self.use_mcp:
            try:
                self.mcp_integration = get_mcp_integration()
                logger.info("✅ MCP 整合已啟用")
            except Exception as e:
                logger.warning(f"❌ MCP 整合初始化失敗: {e}")
                self.use_mcp = False
        
        # 推薦權重配置
        self.ranking_weights = {
            "apple_rating": 0.25,
            "user_click_rate": 0.20,
            "comment_sentiment": 0.20,
            "comment_count": 0.15,
            "mcp_enhancement": 0.20
        }
        
        logger.info("✅ MCP 增強 Podcast 推薦器初始化完成")
    
    @langfuse_trace("recommendation")
    async def get_enhanced_recommendations(self, 
                                         query: str,
                                         user_preferences: Optional[Dict[str, Any]] = None,
                                         top_k: int = 10,
                                         use_mcp_tools: bool = True) -> List[MCPEnhancedRecommendation]:
        """
        獲取 MCP 增強推薦
        
        Args:
            query: 搜尋查詢
            user_preferences: 用戶偏好
            top_k: 返回結果數量
            use_mcp_tools: 是否使用 MCP 工具
            
        Returns:
            List[MCPEnhancedRecommendation]: 增強推薦結果
        """
        try:
            # 1. 基礎搜尋
            base_results = await self._perform_base_search(query, top_k)
            
            # 2. MCP 增強處理
            if self.use_mcp and use_mcp_tools:
                enhanced_results = await self._apply_mcp_enhancement(
                    base_results, query, user_preferences
                )
            else:
                enhanced_results = base_results
            
            # 3. 排序和過濾
            final_results = await self._rank_and_filter_results(
                enhanced_results, top_k
            )
            
            logger.info(f"✅ 生成 {len(final_results)} 個 MCP 增強推薦")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ MCP 增強推薦失敗: {e}")
            # 回退到基礎推薦
            return await self._perform_base_search(query, top_k)
    
    async def _perform_base_search(self, query: str, top_k: int) -> List[MCPEnhancedRecommendation]:
        """執行基礎搜尋"""
        # 模擬基礎搜尋結果
        mock_results = [
            {
                "podcast_id": "podcast_001",
                "title": "科技早知道",
                "base_score": 0.85,
                "apple_rating": 4.5,
                "user_click_rate": 0.75,
                "comment_sentiment": 0.8,
                "comment_count": 1250
            },
            {
                "podcast_id": "podcast_002", 
                "title": "商業就是這樣",
                "base_score": 0.78,
                "apple_rating": 4.2,
                "user_click_rate": 0.68,
                "comment_sentiment": 0.75,
                "comment_count": 890
            },
            {
                "podcast_id": "podcast_003",
                "title": "學習成長",
                "base_score": 0.92,
                "apple_rating": 4.7,
                "user_click_rate": 0.82,
                "comment_sentiment": 0.85,
                "comment_count": 2100
            }
        ]
        
        recommendations = []
        for result in mock_results[:top_k]:
            recommendation = MCPEnhancedRecommendation(
                podcast_id=result["podcast_id"],
                title=result["title"],
                score=result["base_score"],
                mcp_enhanced_score=result["base_score"],
                ranking_factors={
                    "apple_rating": result["apple_rating"],
                    "user_click_rate": result["user_click_rate"],
                    "comment_sentiment": result["comment_sentiment"],
                    "comment_count": result["comment_count"]
                },
                mcp_tools_used=[],
                confidence=0.8,
                metadata=result
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _apply_mcp_enhancement(self, 
                                   base_results: List[MCPEnhancedRecommendation],
                                   query: str,
                                   user_preferences: Optional[Dict[str, Any]] = None) -> List[MCPEnhancedRecommendation]:
        """應用 MCP 增強"""
        if not self.mcp_integration:
            return base_results
        
        enhanced_results = []
        
        for result in base_results:
            try:
                # 1. 使用 MCP 工具進行內容分析
                mcp_tools_used = []
                mcp_enhancement_score = 0.0
                
                # 情感分析增強
                sentiment_result = await self.mcp_integration.call_tool(
                    "analyze_sentiment",
                    {"text": f"{result.title} {query}", "analyzer_type": "chinese"}
                )
                if sentiment_result.get("success"):
                    mcp_tools_used.append("analyze_sentiment")
                    # 根據情感分析調整分數
                    if "positive" in sentiment_result.get("result", ""):
                        mcp_enhancement_score += 0.1
                
                # Apple Podcast 排名增強
                ranking_result = await self.mcp_integration.call_tool(
                    "get_apple_podcast_ranking",
                    {"rss_id": result.podcast_id, "include_details": True}
                )
                if ranking_result.get("success"):
                    mcp_tools_used.append("get_apple_podcast_ranking")
                    mcp_enhancement_score += 0.05
                
                # 內容分類增強
                classification_result = await self.mcp_integration.call_tool(
                    "classify_content",
                    {"content": f"{result.title} {query}"}
                )
                if classification_result.get("success"):
                    mcp_tools_used.append("classify_content")
                    mcp_enhancement_score += 0.05
                
                # 2. 計算 MCP 增強分數
                enhanced_score = result.score + (mcp_enhancement_score * self.ranking_weights["mcp_enhancement"])
                
                # 3. 更新推薦結果
                enhanced_result = MCPEnhancedRecommendation(
                    podcast_id=result.podcast_id,
                    title=result.title,
                    score=result.score,
                    mcp_enhanced_score=enhanced_score,
                    ranking_factors=result.ranking_factors.copy(),
                    mcp_tools_used=mcp_tools_used,
                    confidence=min(0.95, result.confidence + 0.1),
                    metadata={
                        **result.metadata,
                        "mcp_enhancement": {
                            "tools_used": mcp_tools_used,
                            "enhancement_score": mcp_enhancement_score,
                            "sentiment_analysis": sentiment_result.get("result") if "analyze_sentiment" in mcp_tools_used else None,
                            "ranking_data": ranking_result.get("result") if "get_apple_podcast_ranking" in mcp_tools_used else None,
                            "classification": classification_result.get("result") if "classify_content" in mcp_tools_used else None
                        }
                    }
                )
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.warning(f"MCP 增強處理失敗 (Podcast {result.podcast_id}): {e}")
                enhanced_results.append(result)
        
        return enhanced_results
    
    async def _rank_and_filter_results(self, 
                                     results: List[MCPEnhancedRecommendation],
                                     top_k: int) -> List[MCPEnhancedRecommendation]:
        """排序和過濾結果"""
        # 按 MCP 增強分數排序
        sorted_results = sorted(
            results,
            key=lambda x: x.mcp_enhanced_score,
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    async def get_mcp_tools_status(self) -> Dict[str, Any]:
        """獲取 MCP 工具狀態"""
        if not self.mcp_integration:
            return {"mcp_enabled": False, "error": "MCP 整合未初始化"}
        
        try:
            # 獲取可用工具
            available_tools = await self.mcp_integration.list_available_tools()
            
            # 健康檢查
            health = await self.mcp_integration.health_check()
            
            return {
                "mcp_enabled": True,
                "available_tools_count": len(available_tools),
                "available_tools": [tool["name"] for tool in available_tools],
                "health_status": health,
                "ranking_weights": self.ranking_weights
            }
            
        except Exception as e:
            return {
                "mcp_enabled": True,
                "error": str(e),
                "ranking_weights": self.ranking_weights
            }
    
    async def test_mcp_tools(self) -> Dict[str, Any]:
        """測試 MCP 工具"""
        if not self.mcp_integration:
            return {"error": "MCP 整合未初始化"}
        
        test_results = {}
        
        try:
            # 測試情感分析
            sentiment_test = await self.mcp_integration.call_tool(
                "analyze_sentiment",
                {"text": "這個 Podcast 真的很棒！", "analyzer_type": "chinese"}
            )
            test_results["sentiment_analysis"] = sentiment_test
            
            # 測試 Apple Podcast 排名
            ranking_test = await self.mcp_integration.call_tool(
                "get_apple_podcast_ranking",
                {"rss_id": "test_podcast_001", "include_details": False}
            )
            test_results["apple_podcast_ranking"] = ranking_test
            
            # 測試內容分類
            classification_test = await self.mcp_integration.call_tool(
                "classify_content",
                {"content": "科技創新與商業發展"}
            )
            test_results["content_classification"] = classification_test
            
            # 測試向量搜尋
            vector_test = await self.mcp_integration.call_tool(
                "vector_search",
                {"query": "科技 Podcast", "top_k": 3}
            )
            test_results["vector_search"] = vector_test
            
            test_results["overall_status"] = "success"
            
        except Exception as e:
            test_results["overall_status"] = "error"
            test_results["error"] = str(e)
        
        return test_results


# 全域實例
_mcp_enhanced_recommender_instance: Optional[MCPEnhancedPodcastRecommender] = None


def get_mcp_enhanced_recommender() -> MCPEnhancedPodcastRecommender:
    """獲取 MCP 增強推薦器實例（單例模式）"""
    global _mcp_enhanced_recommender_instance
    if _mcp_enhanced_recommender_instance is None:
        _mcp_enhanced_recommender_instance = MCPEnhancedPodcastRecommender()
    return _mcp_enhanced_recommender_instance


async def main():
    """主函數 - 用於測試"""
    # 創建 MCP 增強推薦器
    recommender = MCPEnhancedPodcastRecommender(use_mcp=True)
    
    # 測試 MCP 工具狀態
    status = await recommender.get_mcp_tools_status()
    print(f"MCP 工具狀態: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    # 測試 MCP 工具
    test_results = await recommender.test_mcp_tools()
    print(f"MCP 工具測試結果: {json.dumps(test_results, ensure_ascii=False, indent=2)}")
    
    # 測試增強推薦
    recommendations = await recommender.get_enhanced_recommendations(
        query="科技創新",
        top_k=3,
        use_mcp_tools=True
    )
    
    print(f"\n增強推薦結果:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.title}")
        print(f"   基礎分數: {rec.score:.3f}")
        print(f"   MCP 增強分數: {rec.mcp_enhanced_score:.3f}")
        print(f"   使用的 MCP 工具: {rec.mcp_tools_used}")
        print(f"   信心度: {rec.confidence:.3f}")
        print()


if __name__ == "__main__":
    asyncio.run(main()) 