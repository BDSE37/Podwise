#!/usr/bin/env python3
"""
Apple Podcast 優先推薦系統

實現基於 Apple Podcast 評分、評論、使用者反饋的綜合評分機制：
- Apple Podcast 星等 (50%)
- 評論加減分 (40%)
- 使用者點擊率 (5%)
- Apple Podcast 評論數 (5%)

作者: Podwise Team
版本: 1.0.0
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CommentSentiment(Enum):
    """評論情感分類"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class ApplePodcastRating:
    """Apple Podcast 評分數據"""
    rss_id: str
    title: str
    apple_rating: float  # 1-5 星評分
    apple_review_count: int  # Apple Podcast 評論數
    user_click_rate: float  # 使用者點擊率 (0-1)
    comment_sentiment_score: float  # 評論情感分數 (-1 到 1)
    total_comments: int  # 總評論數
    positive_comments: int  # 正面評論數
    negative_comments: int  # 負面評論數
    neutral_comments: int  # 中性評論數
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RankingScore:
    """排名分數"""
    rss_id: str
    title: str
    total_score: float  # 總分 (0-5)
    apple_rating_score: float  # Apple 評分分數
    comment_score: float  # 評論分數
    click_rate_score: float  # 點擊率分數
    review_count_score: float  # 評論數分數
    ranking_details: Dict[str, Any] = field(default_factory=dict)


class ApplePodcastRankingSystem:
    """Apple Podcast 優先推薦系統"""
    
    def __init__(self):
        """初始化推薦系統"""
        # 權重配置
        self.weights = {
            'apple_rating': 0.50,      # Apple Podcast 星等 (50%)
            'comment_sentiment': 0.40, # 評論加減分 (40%)
            'click_rate': 0.05,        # 使用者點擊率 (5%)
            'review_count': 0.05       # Apple Podcast 評論數 (5%)
        }
        
        # 評論數級距配置
        self.review_count_tiers = {
            'low': {'min': 0, 'max': 50, 'score': 2.5},      # 50以下
            'medium': {'min': 51, 'max': 100, 'score': 3.5}, # 51~100
            'high': {'min': 101, 'max': float('inf'), 'score': 5.0}  # 101以上
        }
        
        # 評論情感權重
        self.sentiment_weights = {
            CommentSentiment.POSITIVE: 1.0,
            CommentSentiment.NEUTRAL: 0.5,
            CommentSentiment.NEGATIVE: -1.0
        }
        
        logger.info("Apple Podcast 優先推薦系統初始化完成")
    
    def calculate_ranking_score(self, podcast_data: ApplePodcastRating) -> RankingScore:
        """
        計算 Podcast 的綜合排名分數
        
        Args:
            podcast_data: Apple Podcast 評分數據
            
        Returns:
            RankingScore: 排名分數
        """
        try:
            # 1. Apple Podcast 星等分數 (50%)
            apple_rating_score = self._calculate_apple_rating_score(podcast_data.apple_rating)
            
            # 2. 評論情感分數 (40%)
            comment_score = self._calculate_comment_sentiment_score(
                podcast_data.comment_sentiment_score,
                podcast_data.total_comments
            )
            
            # 3. 使用者點擊率分數 (5%)
            click_rate_score = self._calculate_click_rate_score(podcast_data.user_click_rate)
            
            # 4. Apple Podcast 評論數分數 (5%)
            review_count_score = self._calculate_review_count_score(podcast_data.apple_review_count)
            
            # 5. 計算加權總分
            total_score = (
                apple_rating_score * self.weights['apple_rating'] +
                comment_score * self.weights['comment_sentiment'] +
                click_rate_score * self.weights['click_rate'] +
                review_count_score * self.weights['review_count']
            )
            
            # 6. 創建排名詳情
            ranking_details = {
                'apple_rating': {
                    'raw_score': podcast_data.apple_rating,
                    'weighted_score': apple_rating_score,
                    'weight': self.weights['apple_rating']
                },
                'comment_sentiment': {
                    'raw_score': podcast_data.comment_sentiment_score,
                    'total_comments': podcast_data.total_comments,
                    'positive_comments': podcast_data.positive_comments,
                    'negative_comments': podcast_data.negative_comments,
                    'neutral_comments': podcast_data.neutral_comments,
                    'weighted_score': comment_score,
                    'weight': self.weights['comment_sentiment']
                },
                'click_rate': {
                    'raw_score': podcast_data.user_click_rate,
                    'weighted_score': click_rate_score,
                    'weight': self.weights['click_rate']
                },
                'review_count': {
                    'raw_score': podcast_data.apple_review_count,
                    'weighted_score': review_count_score,
                    'weight': self.weights['review_count']
                },
                'calculation_timestamp': datetime.now().isoformat()
            }
            
            return RankingScore(
                rss_id=podcast_data.rss_id,
                title=podcast_data.title,
                total_score=total_score,
                apple_rating_score=apple_rating_score,
                comment_score=comment_score,
                click_rate_score=click_rate_score,
                review_count_score=review_count_score,
                ranking_details=ranking_details
            )
            
        except Exception as e:
            logger.error(f"計算排名分數失敗: {e}")
            # 返回預設分數
            return RankingScore(
                rss_id=podcast_data.rss_id,
                title=podcast_data.title,
                total_score=2.5,  # 中等分數
                apple_rating_score=2.5,
                comment_score=2.5,
                click_rate_score=2.5,
                review_count_score=2.5,
                ranking_details={'error': str(e)}
            )
    
    def _calculate_apple_rating_score(self, apple_rating: float) -> float:
        """
        計算 Apple Podcast 星等分數
        
        Args:
            apple_rating: Apple Podcast 星等 (1-5)
            
        Returns:
            float: 標準化分數 (0-5)
        """
        # 直接使用 Apple 評分，但確保在有效範圍內
        if apple_rating < 1.0:
            return 1.0
        elif apple_rating > 5.0:
            return 5.0
        else:
            return apple_rating
    
    def _calculate_comment_sentiment_score(self, sentiment_score: float, total_comments: int) -> float:
        """
        計算評論情感分數
        
        Args:
            sentiment_score: 情感分數 (-1 到 1)
            total_comments: 總評論數
            
        Returns:
            float: 標準化分數 (0-5)
        """
        if total_comments == 0:
            return 2.5  # 無評論時給中等分數
        
        # 將情感分數 (-1 到 1) 轉換為 (0 到 5)
        # 使用 sigmoid 函數進行平滑轉換
        normalized_sentiment = 1 / (1 + math.exp(-sentiment_score * 3))
        score = normalized_sentiment * 5
        
        # 根據評論數量調整分數
        comment_factor = min(total_comments / 100, 1.0)  # 最多 100 條評論為滿分
        adjusted_score = score * (0.5 + 0.5 * comment_factor)
        
        return max(0.0, min(5.0, adjusted_score))
    
    def _calculate_click_rate_score(self, click_rate: float) -> float:
        """
        計算使用者點擊率分數
        
        Args:
            click_rate: 點擊率 (0-1)
            
        Returns:
            float: 標準化分數 (0-5)
        """
        if click_rate < 0:
            return 0.0
        elif click_rate > 1:
            return 5.0
        else:
            # 使用對數函數進行轉換，讓低點擊率也有一定分數
            return 1.0 + 4.0 * (math.log(1 + click_rate * 9) / math.log(10))
    
    def _calculate_review_count_score(self, review_count: int) -> float:
        """
        計算 Apple Podcast 評論數分數
        
        Args:
            review_count: 評論數
            
        Returns:
            float: 標準化分數 (0-5)
        """
        for tier_name, tier_config in self.review_count_tiers.items():
            if tier_config['min'] <= review_count <= tier_config['max']:
                return tier_config['score']
        
        # 如果超出所有級距，返回最高分
        return 5.0
    
    def rank_podcasts(self, podcasts_data: List[ApplePodcastRating]) -> List[RankingScore]:
        """
        對 Podcast 列表進行排名
        
        Args:
            podcasts_data: Podcast 數據列表
            
        Returns:
            List[RankingScore]: 排名後的結果
        """
        try:
            # 計算每個 Podcast 的分數
            ranking_scores = []
            for podcast_data in podcasts_data:
                score = self.calculate_ranking_score(podcast_data)
                ranking_scores.append(score)
            
            # 按總分降序排序
            ranking_scores.sort(key=lambda x: x.total_score, reverse=True)
            
            logger.info(f"完成 {len(ranking_scores)} 個 Podcast 的排名")
            return ranking_scores
            
        except Exception as e:
            logger.error(f"Podcast 排名失敗: {e}")
            return []
    
    def get_top_recommendations(self, 
                              podcasts_data: List[ApplePodcastRating], 
                              top_k: int = 5) -> List[RankingScore]:
        """
        獲取前 K 個推薦
        
        Args:
            podcasts_data: Podcast 數據列表
            top_k: 返回數量
            
        Returns:
            List[RankingScore]: 前 K 個推薦
        """
        ranked_podcasts = self.rank_podcasts(podcasts_data)
        return ranked_podcasts[:top_k]
    
    def analyze_ranking_distribution(self, ranking_scores: List[RankingScore]) -> Dict[str, Any]:
        """
        分析排名分佈
        
        Args:
            ranking_scores: 排名分數列表
            
        Returns:
            Dict[str, Any]: 分佈分析結果
        """
        if not ranking_scores:
            return {}
        
        total_scores = [score.total_score for score in ranking_scores]
        apple_scores = [score.apple_rating_score for score in ranking_scores]
        comment_scores = [score.comment_score for score in ranking_scores]
        click_scores = [score.click_rate_score for score in ranking_scores]
        review_scores = [score.review_count_score for score in ranking_scores]
        
        def calculate_stats(scores: List[float]) -> Dict[str, float]:
            return {
                'mean': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'std': math.sqrt(sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))
            }
        
        return {
            'total_scores': calculate_stats(total_scores),
            'apple_rating_scores': calculate_stats(apple_scores),
            'comment_scores': calculate_stats(comment_scores),
            'click_rate_scores': calculate_stats(click_scores),
            'review_count_scores': calculate_stats(review_scores),
            'total_podcasts': len(ranking_scores)
        }
    
    def update_weights(self, new_weights: Dict[str, float]) -> bool:
        """
        更新權重配置
        
        Args:
            new_weights: 新的權重配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 驗證權重總和
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:  # 允許 1% 的誤差
                logger.warning(f"權重總和不等於 1.0: {total_weight}")
            
            self.weights.update(new_weights)
            logger.info(f"權重配置已更新: {new_weights}")
            return True
            
        except Exception as e:
            logger.error(f"更新權重失敗: {e}")
            return False
    
    def get_ranking_summary(self, ranking_scores: List[RankingScore]) -> str:
        """
        生成排名摘要
        
        Args:
            ranking_scores: 排名分數列表
            
        Returns:
            str: 排名摘要
        """
        if not ranking_scores:
            return "無 Podcast 數據"
        
        top_3 = ranking_scores[:3]
        summary_lines = [
            "🎧 Apple Podcast 優先推薦排名摘要",
            f"📊 總共評估 {len(ranking_scores)} 個 Podcast",
            "",
            "🏆 前三名推薦："
        ]
        
        for i, score in enumerate(top_3, 1):
            summary_lines.append(
                f"{i}. {score.title} (總分: {score.total_score:.2f})"
            )
        
        # 添加分數詳情
        if top_3:
            best = top_3[0]
            summary_lines.extend([
                "",
                "📈 最佳 Podcast 分數詳情：",
                f"   Apple 評分: {best.apple_rating_score:.2f}",
                f"   評論分數: {best.comment_score:.2f}",
                f"   點擊率分數: {best.click_rate_score:.2f}",
                f"   評論數分數: {best.review_count_score:.2f}"
            ])
        
        return "\n".join(summary_lines)


# 全域實例
apple_podcast_ranking = ApplePodcastRankingSystem()


def get_apple_podcast_ranking() -> ApplePodcastRankingSystem:
    """獲取 Apple Podcast 排名系統實例"""
    return apple_podcast_ranking


def create_sample_podcast_data() -> List[ApplePodcastRating]:
    """創建範例 Podcast 數據（用於測試）"""
    return [
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
        )
    ]


if __name__ == "__main__":
    # 測試 Apple Podcast 排名系統
    ranking_system = get_apple_podcast_ranking()
    
    # 創建範例數據
    sample_data = create_sample_podcast_data()
    
    # 執行排名
    results = ranking_system.rank_podcasts(sample_data)
    
    # 顯示結果
    print(ranking_system.get_ranking_summary(results))
    
    # 顯示分佈分析
    distribution = ranking_system.analyze_ranking_distribution(results)
    print(f"\n📊 分佈分析: {distribution}") 