#!/usr/bin/env python3
"""
增強版 Podcast 推薦器

整合 Apple Podcast 優先推薦系統與現有的向量搜尋功能，
提供基於多維度評分的智能推薦。

作者: Podwise Team
版本: 1.0.0
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 導入 Apple Podcast 排名系統
from core.apple_podcast_ranking import (
    ApplePodcastRankingSystem, 
    ApplePodcastRating, 
    RankingScore,
    get_apple_podcast_ranking
)

# 導入現有工具
from .enhanced_vector_search import RAGVectorSearch, RAGSearchConfig
from .podcast_formatter import PodcastFormatter, FormattedPodcast

logger = logging.getLogger(__name__)


@dataclass
class EnhancedRecommendationConfig:
    """增強推薦配置"""
    # 向量搜尋配置
    vector_search_config: RAGSearchConfig = field(default_factory=RAGSearchConfig)
    
    # Apple Podcast 排名配置
    use_apple_ranking: bool = True
    apple_ranking_weight: float = 0.6  # Apple 排名權重
    vector_search_weight: float = 0.4  # 向量搜尋權重
    
    # 推薦數量配置
    max_recommendations: int = 5
    min_confidence_threshold: float = 0.7
    
    # 混合策略配置
    enable_hybrid_ranking: bool = True
    enable_fallback: bool = True


@dataclass
class EnhancedRecommendationResult:
    """增強推薦結果"""
    recommendations: List[FormattedPodcast]
    total_found: int
    confidence: float
    ranking_method: str
    apple_ranking_scores: List[RankingScore] = field(default_factory=list)
    vector_search_results: List[Dict[str, Any]] = field(default_factory=list)
    hybrid_scores: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedPodcastRecommender:
    """增強版 Podcast 推薦器"""
    
    def __init__(self, config: Optional[EnhancedRecommendationConfig] = None):
        """
        初始化增強推薦器
        
        Args:
            config: 推薦配置
        """
        self.config = config or EnhancedRecommendationConfig()
        
        # 初始化 Apple Podcast 排名系統
        self.apple_ranking = get_apple_podcast_ranking()
        
        # 初始化向量搜尋
        self.vector_search = RAGVectorSearch(self.config.vector_search_config)
        
        # 初始化 Podcast 格式化器
        self.podcast_formatter = PodcastFormatter()
        
        logger.info("增強版 Podcast 推薦器初始化完成")
    
    async def get_recommendations(self, 
                                query: str, 
                                user_id: Optional[str] = None,
                                category_filter: Optional[str] = None) -> EnhancedRecommendationResult:
        """
        獲取增強推薦結果
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            category_filter: 類別過濾器
            
        Returns:
            EnhancedRecommendationResult: 增強推薦結果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"開始處理增強推薦查詢: {query}")
            
            # 1. 執行向量搜尋
            vector_results = await self._get_vector_search_results(query, category_filter)
            
            # 2. 獲取 Apple Podcast 排名
            apple_ranking_results = await self._get_apple_ranking_results(query, category_filter)
            
            # 3. 混合排名
            if self.config.enable_hybrid_ranking:
                final_recommendations = await self._hybrid_ranking(
                    vector_results, apple_ranking_results, query
                )
                ranking_method = "hybrid"
            else:
                # 僅使用 Apple 排名
                final_recommendations = await self._apply_apple_ranking_only(
                    vector_results, apple_ranking_results
                )
                ranking_method = "apple_ranking_only"
            
            # 4. 格式化結果
            formatted_recommendations = self._format_recommendations(final_recommendations)
            
            # 5. 計算整體信心度
            overall_confidence = self._calculate_overall_confidence(formatted_recommendations)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = EnhancedRecommendationResult(
                recommendations=formatted_recommendations,
                total_found=len(vector_results),
                confidence=overall_confidence,
                ranking_method=ranking_method,
                apple_ranking_scores=apple_ranking_results,
                vector_search_results=vector_results,
                processing_time=processing_time,
                metadata={
                    'query': query,
                    'user_id': user_id,
                    'category_filter': category_filter,
                    'config_used': self.config.__dict__
                }
            )
            
            logger.info(f"增強推薦完成: {len(formatted_recommendations)} 個推薦，信心度: {overall_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"增強推薦失敗: {e}")
            # 返回備用結果
            return await self._get_fallback_recommendations(query, start_time)
    
    async def _get_vector_search_results(self, query: str, category_filter: Optional[str]) -> List[Dict[str, Any]]:
        """獲取向量搜尋結果"""
        try:
            search_results = await self.vector_search.search(query, top_k=self.config.max_recommendations * 2)
            
            # 過濾結果
            filtered_results = []
            for result in search_results:
                # 將 SearchResult 轉換為字典格式
                result_dict = {
                    'rss_id': getattr(result, 'id', ''),
                    'title': getattr(result, 'title', ''),
                    'content': getattr(result, 'content', ''),
                    'score': getattr(result, 'score', 0.0),
                    'category': getattr(result, 'category', ''),
                    'tags': getattr(result, 'tags', []),
                    'metadata': getattr(result, 'metadata', {})
                }
                
                if category_filter:
                    result_category = result_dict.get('category', '').lower()
                    if category_filter.lower() not in result_category:
                        continue
                
                if result_dict.get('score', 0) >= self.config.min_confidence_threshold:
                    filtered_results.append(result_dict)
            
            return filtered_results[:self.config.max_recommendations]
            
        except Exception as e:
            logger.warning(f"向量搜尋失敗: {e}")
            return []
    
    async def _get_apple_ranking_results(self, query: str, category_filter: Optional[str]) -> List[RankingScore]:
        """獲取 Apple Podcast 排名結果"""
        try:
            # 這裡應該從資料庫或 API 獲取實際的 Apple Podcast 數據
            # 目前使用模擬數據進行演示
            sample_data = self._get_sample_apple_podcast_data(query, category_filter)
            
            # 執行排名
            ranking_results = self.apple_ranking.rank_podcasts(sample_data)
            
            return ranking_results[:self.config.max_recommendations]
            
        except Exception as e:
            logger.warning(f"Apple Podcast 排名失敗: {e}")
            return []
    
    def _get_sample_apple_podcast_data(self, query: str, category_filter: Optional[str]) -> List[ApplePodcastRating]:
        """獲取範例 Apple Podcast 數據（實際應用中應從資料庫獲取）"""
        # 根據查詢和類別過濾器生成相關的範例數據
        base_data = [
            ApplePodcastRating(
                rss_id="1234567890",
                title="投資理財大師",
                apple_rating=4.8,
                apple_review_count=150,
                user_click_rate=0.85,
                comment_sentiment_score=0.75,
                total_comments=45,
                positive_comments=35,
                negative_comments=5,
                neutral_comments=5
            ),
            ApplePodcastRating(
                rss_id="2345678901",
                title="科技趨勢分析",
                apple_rating=4.5,
                apple_review_count=80,
                user_click_rate=0.72,
                comment_sentiment_score=0.60,
                total_comments=30,
                positive_comments=22,
                negative_comments=3,
                neutral_comments=5
            ),
            ApplePodcastRating(
                rss_id="3456789012",
                title="職涯發展指南",
                apple_rating=4.2,
                apple_review_count=45,
                user_click_rate=0.65,
                comment_sentiment_score=0.45,
                total_comments=20,
                positive_comments=12,
                negative_comments=4,
                neutral_comments=4
            ),
            ApplePodcastRating(
                rss_id="4567890123",
                title="心理學與生活",
                apple_rating=4.6,
                apple_review_count=120,
                user_click_rate=0.78,
                comment_sentiment_score=0.68,
                total_comments=38,
                positive_comments=28,
                negative_comments=4,
                neutral_comments=6
            ),
            ApplePodcastRating(
                rss_id="5678901234",
                title="創業實戰分享",
                apple_rating=4.3,
                apple_review_count=65,
                user_click_rate=0.70,
                comment_sentiment_score=0.55,
                total_comments=25,
                positive_comments=18,
                negative_comments=3,
                neutral_comments=4
            )
        ]
        
        # 根據類別過濾器篩選
        if category_filter:
            filtered_data = []
            for data in base_data:
                # 這裡應該根據實際的類別標籤進行篩選
                # 目前使用簡單的關鍵詞匹配
                if category_filter.lower() in data.title.lower():
                    filtered_data.append(data)
            return filtered_data
        
        return base_data
    
    async def _hybrid_ranking(self, 
                            vector_results: List[Dict[str, Any]], 
                            apple_ranking_results: List[RankingScore],
                            query: str) -> List[Dict[str, Any]]:
        """混合排名策略"""
        try:
            # 創建 RSS ID 到 Apple 排名的映射
            apple_ranking_map = {score.rss_id: score for score in apple_ranking_results}
            
            # 為向量搜尋結果添加 Apple 排名分數
            enhanced_results = []
            for result in vector_results:
                rss_id = result.get('rss_id', '')
                apple_score = apple_ranking_map.get(rss_id)
                
                if apple_score:
                    # 計算混合分數
                    vector_score = result.get('score', 0.0)
                    hybrid_score = (
                        vector_score * self.config.vector_search_weight +
                        apple_score.total_score * self.config.apple_ranking_weight
                    )
                    
                    enhanced_result = result.copy()
                    enhanced_result['hybrid_score'] = hybrid_score
                    enhanced_result['apple_ranking_score'] = apple_score.total_score
                    enhanced_result['vector_score'] = vector_score
                    enhanced_results.append(enhanced_result)
                else:
                    # 如果沒有 Apple 排名，僅使用向量搜尋分數
                    enhanced_result = result.copy()
                    enhanced_result['hybrid_score'] = result.get('score', 0.0) * self.config.vector_search_weight
                    enhanced_result['apple_ranking_score'] = 0.0
                    enhanced_result['vector_score'] = result.get('score', 0.0)
                    enhanced_results.append(enhanced_result)
            
            # 按混合分數排序
            enhanced_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return enhanced_results[:self.config.max_recommendations]
            
        except Exception as e:
            logger.error(f"混合排名失敗: {e}")
            return vector_results[:self.config.max_recommendations]
    
    async def _apply_apple_ranking_only(self, 
                                      vector_results: List[Dict[str, Any]], 
                                      apple_ranking_results: List[RankingScore]) -> List[Dict[str, Any]]:
        """僅使用 Apple 排名"""
        try:
            # 創建 RSS ID 到向量結果的映射
            vector_results_map = {result.get('rss_id', ''): result for result in vector_results}
            
            # 按 Apple 排名排序，並添加向量搜尋信息
            enhanced_results = []
            for apple_score in apple_ranking_results:
                vector_result = vector_results_map.get(apple_score.rss_id)
                
                if vector_result:
                    enhanced_result = vector_result.copy()
                    enhanced_result['hybrid_score'] = apple_score.total_score
                    enhanced_result['apple_ranking_score'] = apple_score.total_score
                    enhanced_result['vector_score'] = vector_result.get('score', 0.0)
                    enhanced_results.append(enhanced_result)
            
            return enhanced_results[:self.config.max_recommendations]
            
        except Exception as e:
            logger.error(f"Apple 排名應用失敗: {e}")
            return vector_results[:self.config.max_recommendations]
    
    def _format_recommendations(self, enhanced_results: List[Dict[str, Any]]) -> List[FormattedPodcast]:
        """格式化推薦結果"""
        formatted_podcasts = []
        
        for result in enhanced_results:
            formatted_podcast = FormattedPodcast(
                title=result.get('title', ''),
                description=result.get('content', ''),
                apple_podcast_url=self.podcast_formatter.format_apple_podcast_url(
                    result.get('rss_id', '')
                ),
                rss_id=result.get('rss_id', ''),
                confidence=result.get('hybrid_score', result.get('score', 0.0)),
                category=result.get('category', ''),
                tags=result.get('tags', []),
                hidden_tags=self.podcast_formatter.create_hidden_tags(result.get('tags', []))
            )
            formatted_podcasts.append(formatted_podcast)
        
        return formatted_podcasts
    
    def _calculate_overall_confidence(self, recommendations: List[FormattedPodcast]) -> float:
        """計算整體信心度"""
        if not recommendations:
            return 0.0
        
        # 使用最高信心度作為整體信心度
        return max([rec.confidence for rec in recommendations])
    
    async def _get_fallback_recommendations(self, query: str, start_time: datetime) -> EnhancedRecommendationResult:
        """獲取備用推薦結果"""
        logger.info("使用備用推薦策略")
        
        # 創建基本的備用推薦
        fallback_recommendations = [
            FormattedPodcast(
                title="熱門 Podcast 推薦",
                description="基於您的查詢提供的智能推薦",
                apple_podcast_url="",
                rss_id="fallback_1",
                confidence=0.5,
                category="一般",
                tags=[],
                hidden_tags=""
            )
        ]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return EnhancedRecommendationResult(
            recommendations=fallback_recommendations,
            total_found=1,
            confidence=0.5,
            ranking_method="fallback",
            processing_time=processing_time,
            metadata={'fallback_used': True, 'query': query}
        )
    
    def get_ranking_analysis(self, result: EnhancedRecommendationResult) -> Dict[str, Any]:
        """獲取排名分析"""
        if not result.apple_ranking_scores:
            return {'error': '無 Apple 排名數據'}
        
        # 分析 Apple 排名分佈
        distribution = self.apple_ranking.analyze_ranking_distribution(result.apple_ranking_scores)
        
        # 分析混合分數
        hybrid_scores = [rec.confidence for rec in result.recommendations]
        hybrid_stats = {
            'mean': sum(hybrid_scores) / len(hybrid_scores) if hybrid_scores else 0,
            'min': min(hybrid_scores) if hybrid_scores else 0,
            'max': max(hybrid_scores) if hybrid_scores else 0,
            'count': len(hybrid_scores)
        }
        
        return {
            'apple_ranking_distribution': distribution,
            'hybrid_score_stats': hybrid_stats,
            'ranking_method': result.ranking_method,
            'processing_time': result.processing_time,
            'total_recommendations': len(result.recommendations)
        }
    
    def update_config(self, new_config: EnhancedRecommendationConfig) -> bool:
        """更新配置"""
        try:
            self.config = new_config
            logger.info("增強推薦器配置已更新")
            return True
        except Exception as e:
            logger.error(f"配置更新失敗: {e}")
            return False


# 全域實例
enhanced_recommender = EnhancedPodcastRecommender()


def get_enhanced_recommender() -> EnhancedPodcastRecommender:
    """獲取增強推薦器實例"""
    return enhanced_recommender


async def test_enhanced_recommender():
    """測試增強推薦器"""
    recommender = get_enhanced_recommender()
    
    # 測試查詢
    test_queries = [
        "投資理財",
        "科技趨勢",
        "職涯發展"
    ]
    
    for query in test_queries:
        print(f"\n🔍 測試查詢: {query}")
        result = await recommender.get_recommendations(query)
        
        print(f"📊 推薦結果:")
        print(f"   - 推薦數量: {len(result.recommendations)}")
        print(f"   - 信心度: {result.confidence:.2f}")
        print(f"   - 排名方法: {result.ranking_method}")
        print(f"   - 處理時間: {result.processing_time:.2f}秒")
        
        # 顯示前 3 個推薦
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"   {i}. {rec.title} (信心度: {rec.confidence:.2f})")
        
        # 顯示排名分析
        analysis = recommender.get_ranking_analysis(result)
        print(f"📈 排名分析: {analysis}")


if __name__ == "__main__":
    # 執行測試
    asyncio.run(test_enhanced_recommender()) 