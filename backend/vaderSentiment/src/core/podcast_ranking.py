#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podcast 排名分析器

根據多個評分標準對 podcast 進行排名分析
包含星等、情感分析、點擊率、評論數等指標

作者: Podwise Team
版本: 2.0.0
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from .sentiment_analyzer import SentimentAnalyzer, SentimentResult

logger = logging.getLogger(__name__)


@dataclass
class PodcastInfo:
    """Podcast 資訊數據類別"""
    title: str
    rating: float
    comment_count: int
    comments: List[str]
    engagement_rate: float
    source: str


@dataclass
class RankingResult:
    """排名結果數據類別"""
    title: str
    rating_score: float
    sentiment_score: float
    engagement_score: float
    comment_count_score: float
    total_score: float
    rank: int
    source: str


class PodcastRankingAnalyzer:
    """
    Podcast 排名分析器
    
    根據四個評分標準對 podcast 進行排名：
    1. Apple podcast 星等 (40%)
    2. 評論文字情感分析 (35%)
    3. 使用者點擊率 (15%)
    4. Apple podcast 評論數 (10%)
    """
    
    def __init__(self, podcast_info_dir: str = "Podcast_info"):
        """
        初始化排名分析器
        
        Args:
            podcast_info_dir: Podcast_info 目錄路徑
        """
        self.podcast_info_dir = Path(podcast_info_dir)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ranking_results = []
        
        # 評分權重
        self.weights = {
            'rating': 0.40,      # Apple podcast 星等 (40%)
            'sentiment': 0.35,   # 評論文字分析 (35%)
            'engagement': 0.15,  # 使用者點擊率 (15%)
            'comment_count': 0.10  # 評論數 (10%)
        }
        
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """設定日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def load_podcast_data(self) -> List[PodcastInfo]:
        """
        載入 podcast 數據
        
        Returns:
            List[PodcastInfo]: Podcast 資訊列表
        """
        podcast_data = []
        
        if not self.podcast_info_dir.exists():
            logger.error(f"Podcast_info 目錄不存在: {self.podcast_info_dir}")
            return podcast_data
            
        json_files = list(self.podcast_info_dir.glob("*.json"))
        logger.info(f"找到 {len(json_files)} 個 podcast 檔案")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 提取 podcast 資訊
                title = data.get('title', '')
                rating = float(data.get('rating', 0.0))
                comment_count = int(data.get('comment_count', 0))
                comments = data.get('comments', [])
                engagement_rate = float(data.get('engagement_rate', 0.0))
                source = data.get('source', '')
                
                podcast_info = PodcastInfo(
                    title=title,
                    rating=rating,
                    comment_count=comment_count,
                    comments=comments,
                    engagement_rate=engagement_rate,
                    source=source
                )
                
                podcast_data.append(podcast_info)
                
            except Exception as e:
                logger.warning(f"載入檔案 {file_path} 失敗: {e}")
                
        logger.info(f"成功載入 {len(podcast_data)} 個 podcast")
        return podcast_data
        
    def calculate_sentiment_score(self, comments: List[str]) -> float:
        """
        計算評論情感分析分數
        
        Args:
            comments: 評論列表
            
        Returns:
            float: 情感分析分數 (0-1)
        """
        if not comments:
            return 0.0
            
        try:
            # 使用情感分析器分析評論
            sentiment_scores = []
            for comment in comments:
                if comment.strip():
                    result = self.sentiment_analyzer.analyze_text(comment)
                    # 將 -1 到 1 的範圍轉換為 0 到 1
                    normalized_score = (result.compound_score + 1) / 2
                    sentiment_scores.append(normalized_score)
            
            if sentiment_scores:
                # 計算平均情感分數
                return statistics.mean(sentiment_scores)
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"情感分析失敗: {e}")
            return 0.0
            
    def normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """
        正規化分數到 0-1 範圍
        
        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            float: 正規化後的分數 (0-1)
        """
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)
        
    def calculate_ranking_scores(self, podcast_data: List[PodcastInfo]) -> List[RankingResult]:
        """
        計算排名分數
        
        Args:
            podcast_data: Podcast 資訊列表
            
        Returns:
            List[RankingResult]: 排名結果列表
        """
        if not podcast_data:
            return []
            
        # 計算各項指標的範圍
        ratings = [p.rating for p in podcast_data]
        engagement_rates = [p.engagement_rate for p in podcast_data]
        comment_counts = [p.comment_count for p in podcast_data]
        
        min_rating, max_rating = min(ratings), max(ratings)
        min_engagement, max_engagement = min(engagement_rates), max(engagement_rates)
        min_comments, max_comments = min(comment_counts), max(comment_counts)
        
        ranking_results = []
        
        for podcast in podcast_data:
            # 計算各項分數
            rating_score = self.normalize_score(podcast.rating, min_rating, max_rating)
            sentiment_score = self.calculate_sentiment_score(podcast.comments)
            engagement_score = self.normalize_score(podcast.engagement_rate, min_engagement, max_engagement)
            comment_count_score = self.normalize_score(podcast.comment_count, min_comments, max_comments)
            
            # 計算加權總分
            total_score = (
                rating_score * self.weights['rating'] +
                sentiment_score * self.weights['sentiment'] +
                engagement_score * self.weights['engagement'] +
                comment_count_score * self.weights['comment_count']
            )
            
            result = RankingResult(
                title=podcast.title,
                rating_score=rating_score,
                sentiment_score=sentiment_score,
                engagement_score=engagement_score,
                comment_count_score=comment_count_score,
                total_score=total_score,
                rank=0,  # 稍後設定
                source=podcast.source
            )
            
            ranking_results.append(result)
            
        # 按總分排序並設定排名
        ranking_results.sort(key=lambda x: x.total_score, reverse=True)
        for i, result in enumerate(ranking_results):
            result.rank = i + 1
            
        return ranking_results
        
    def generate_ranking_report(self, ranking_results: List[RankingResult], 
                               output_path: str = "podcast_ranking_report.csv") -> None:
        """
        生成排名報告
        
        Args:
            ranking_results: 排名結果列表
            output_path: 輸出檔案路徑
        """
        if not ranking_results:
            logger.warning("沒有排名結果可生成報告")
            return
            
        # 創建 DataFrame
        data = []
        for result in ranking_results:
            data.append({
                '排名': result.rank,
                '節目名稱': result.title,
                '星等分數': round(result.rating_score, 3),
                '情感分數': round(result.sentiment_score, 3),
                '點擊率分數': round(result.engagement_score, 3),
                '評論數分數': round(result.comment_count_score, 3),
                '總分': round(result.total_score, 3),
                '來源': result.source
            })
            
        df = pd.DataFrame(data)
        
        # 儲存 CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"排名報告已儲存至: {output_path}")
        
        # 打印摘要
        self._print_ranking_summary(ranking_results)
        
    def _print_ranking_summary(self, ranking_results: List[RankingResult]) -> None:
        """打印排名摘要"""
        print("\n" + "="*80)
        print("📊 PODCAST 排名分析報告")
        print("="*80)
        
        print(f"📁 分析節目數: {len(ranking_results)}")
        print(f"📊 評分標準權重:")
        print(f"   • Apple podcast 星等: {self.weights['rating']*100}%")
        print(f"   • 評論情感分析: {self.weights['sentiment']*100}%")
        print(f"   • 使用者點擊率: {self.weights['engagement']*100}%")
        print(f"   • Apple podcast 評論數: {self.weights['comment_count']*100}%")
        
        print(f"\n🏆 前 10 名節目:")
        for i, result in enumerate(ranking_results[:10]):
            print(f"   {result.rank:2d}. {result.title[:50]:<50} {result.total_score:.3f}")
            
        print("="*80)
        
    def run_analysis(self, output_path: str = "podcast_ranking_report.csv") -> List[RankingResult]:
        """
        執行完整分析流程
        
        Args:
            output_path: 輸出檔案路徑
            
        Returns:
            List[RankingResult]: 排名結果列表
        """
        logger.info("開始執行 podcast 排名分析...")
        
        # 載入數據
        podcast_data = self.load_podcast_data()
        if not podcast_data:
            logger.error("沒有載入到 podcast 數據")
            return []
            
        # 計算排名
        ranking_results = self.calculate_ranking_scores(podcast_data)
        
        # 生成報告
        self.generate_ranking_report(ranking_results, output_path)
        
        logger.info("Podcast 排名分析完成")
        return ranking_results 