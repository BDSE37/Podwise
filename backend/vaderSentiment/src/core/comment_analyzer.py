#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
評論分析器核心類別

提供評論數據分析功能
包含評論情感分析、關鍵詞提取、推薦理由生成等

作者: Podwise Team
版本: 2.0.0
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from collections import Counter

from .sentiment_analyzer import SentimentAnalyzer, SentimentResult
from ..utils.data_processor import DataProcessor

logger = logging.getLogger(__name__)


@dataclass
class CommentAnalysis:
    """評論分析結果數據類別"""
    comment: str
    sentiment_result: SentimentResult
    keywords: List[str]
    recommendation_reason: str
    confidence: float


@dataclass
class PodcastRecommendation:
    """Podcast 推薦結果數據類別"""
    title: str
    positive_comments: List[CommentAnalysis]
    negative_comments: List[CommentAnalysis]
    overall_sentiment: float
    top_keywords: List[Tuple[str, int]]
    recommendation_summary: str
    source: str


class CommentAnalyzer:
    """
    評論分析器
    
    提供評論數據的深度分析功能
    """
    
    def __init__(self, comment_data_dir: str = "comment_data"):
        """
        初始化評論分析器
        
        Args:
            comment_data_dir: 評論數據目錄路徑
        """
        self.comment_data_dir = Path(comment_data_dir)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_processor = DataProcessor()
        
        # 推薦關鍵詞
        self.recommendation_keywords = {
            '推薦', '喜歡', '很棒', '優秀', '實用', '有幫助', '有啟發', '有收穫',
            '精彩', '有趣', '專業', '用心', '認真', '負責', '熱情', '友善',
            '準確', '清晰', '易懂', '深入', '全面', '詳細', '完整', '豐富',
            '有價值', '有意義', '支持', '鼓勵', '肯定', '認同', '理解', '共鳴',
            '感謝', '謝謝', '愛', '學習', '知識', '智慧', '經驗', '分享',
            '成長', '進步', '提升', '改善', '解決', '答案', '方法', '技巧',
            '策略', '觀點', '見解', '分析', '研究', '成功', '成就', '突破',
            '創新', '創意', '想法', '概念', '理論', '實踐'
        }
        
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """設定日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def load_comment_data(self, podcast_title: str) -> List[str]:
        """
        載入指定 podcast 的評論數據
        
        Args:
            podcast_title: podcast 標題
            
        Returns:
            List[str]: 評論列表
        """
        comments = []
        
        if not self.comment_data_dir.exists():
            logger.error(f"評論數據目錄不存在: {self.comment_data_dir}")
            return comments
            
        # 搜尋相關的評論檔案
        json_files = list(self.comment_data_dir.glob("*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 檢查是否包含 podcast 標題相關內容
                if self._is_related_to_podcast(data, podcast_title):
                    comment_text = data.get('content', '')
                    if comment_text and comment_text.strip():
                        comments.append(comment_text)
                        
            except Exception as e:
                logger.warning(f"載入評論檔案失敗 {file_path}: {e}")
                
        logger.info(f"為 {podcast_title} 載入 {len(comments)} 條評論")
        return comments
        
    def _is_related_to_podcast(self, data: Dict[str, Any], podcast_title: str) -> bool:
        """檢查數據是否與指定 podcast 相關"""
        # 簡單的關鍵詞匹配
        title_keywords = set(podcast_title.lower().split())
        
        # 檢查檔案名
        filename = data.get('filename', '')
        if any(keyword in filename.lower() for keyword in title_keywords):
            return True
            
        # 檢查內容
        content = data.get('content', '')
        if any(keyword in content.lower() for keyword in title_keywords):
            return True
            
        return False
        
    def analyze_comment(self, comment: str) -> CommentAnalysis:
        """
        分析單條評論
        
        Args:
            comment: 評論內容
            
        Returns:
            CommentAnalysis: 評論分析結果
        """
        # 情感分析
        sentiment_result = self.sentiment_analyzer.analyze_text(comment)
        
        # 提取關鍵詞
        keywords = self._extract_keywords(comment)
        
        # 生成推薦理由
        recommendation_reason = self._generate_recommendation_reason(
            comment, sentiment_result, keywords
        )
        
        # 計算信心度
        confidence = self._calculate_confidence(sentiment_result, keywords)
        
        return CommentAnalysis(
            comment=comment,
            sentiment_result=sentiment_result,
            keywords=keywords,
            recommendation_reason=recommendation_reason,
            confidence=confidence
        )
        
    def _extract_keywords(self, text: str) -> List[str]:
        """提取關鍵詞"""
        words = self.data_processor.extract_words(text)
        
        # 過濾推薦關鍵詞
        keywords = [word for word in words if word in self.recommendation_keywords]
        
        return keywords
        
    def _generate_recommendation_reason(self, comment: str, 
                                       sentiment_result: SentimentResult,
                                       keywords: List[str]) -> str:
        """生成推薦理由"""
        if sentiment_result.sentiment_label == 'positive':
            if keywords:
                return f"正面評價，包含關鍵詞: {', '.join(keywords[:3])}"
            else:
                return "正面評價，內容積極"
        elif sentiment_result.sentiment_label == 'negative':
            return "負面評價，不推薦"
        else:
            return "中性評價，需要更多資訊"
            
    def _calculate_confidence(self, sentiment_result: SentimentResult, 
                             keywords: List[str]) -> float:
        """計算信心度"""
        # 基於情感分析信心度和關鍵詞數量
        sentiment_confidence = sentiment_result.confidence
        keyword_confidence = min(len(keywords) / 5.0, 1.0)  # 最多 5 個關鍵詞
        
        return (sentiment_confidence + keyword_confidence) / 2
        
    def analyze_podcast_comments(self, podcast_title: str) -> PodcastRecommendation:
        """
        分析 podcast 的所有評論
        
        Args:
            podcast_title: podcast 標題
            
        Returns:
            PodcastRecommendation: podcast 推薦結果
        """
        # 載入評論
        comments = self.load_comment_data(podcast_title)
        
        if not comments:
            logger.warning(f"沒有找到 {podcast_title} 的評論數據")
            return self._create_empty_recommendation(podcast_title)
            
        # 分析每條評論
        comment_analyses = []
        for comment in comments:
            try:
                analysis = self.analyze_comment(comment)
                comment_analyses.append(analysis)
            except Exception as e:
                logger.warning(f"分析評論失敗: {e}")
                
        # 分類評論
        positive_comments = [
            ca for ca in comment_analyses 
            if ca.sentiment_result.sentiment_label == 'positive'
        ]
        negative_comments = [
            ca for ca in comment_analyses 
            if ca.sentiment_result.sentiment_label == 'negative'
        ]
        
        # 計算整體情感
        if comment_analyses:
            overall_sentiment = sum(
                ca.sentiment_result.compound_score for ca in comment_analyses
            ) / len(comment_analyses)
        else:
            overall_sentiment = 0.0
            
        # 提取頂級關鍵詞
        all_keywords = []
        for ca in comment_analyses:
            all_keywords.extend(ca.keywords)
            
        keyword_counter = Counter(all_keywords)
        top_keywords = keyword_counter.most_common(10)
        
        # 生成推薦摘要
        recommendation_summary = self._generate_recommendation_summary(
            positive_comments, negative_comments, overall_sentiment, top_keywords
        )
        
        return PodcastRecommendation(
            title=podcast_title,
            positive_comments=positive_comments,
            negative_comments=negative_comments,
            overall_sentiment=overall_sentiment,
            top_keywords=top_keywords,
            recommendation_summary=recommendation_summary,
            source="comment_data"
        )
        
    def _generate_recommendation_summary(self, positive_comments: List[CommentAnalysis],
                                        negative_comments: List[CommentAnalysis],
                                        overall_sentiment: float,
                                        top_keywords: List[Tuple[str, int]]) -> str:
        """生成推薦摘要"""
        summary_parts = []
        
        # 情感傾向
        if overall_sentiment > 0.1:
            summary_parts.append("整體情感傾向正面")
        elif overall_sentiment < -0.1:
            summary_parts.append("整體情感傾向負面")
        else:
            summary_parts.append("整體情感傾向中性")
            
        # 評論數量
        total_comments = len(positive_comments) + len(negative_comments)
        summary_parts.append(f"共分析 {total_comments} 條評論")
        
        # 正面評論比例
        if total_comments > 0:
            positive_ratio = len(positive_comments) / total_comments
            summary_parts.append(f"正面評論佔 {positive_ratio:.1%}")
            
        # 關鍵詞
        if top_keywords:
            top_keywords_str = ", ".join([f"{word}({count})" for word, count in top_keywords[:5]])
            summary_parts.append(f"主要關鍵詞: {top_keywords_str}")
            
        return "；".join(summary_parts)
        
    def _create_empty_recommendation(self, podcast_title: str) -> PodcastRecommendation:
        """創建空的推薦結果"""
        return PodcastRecommendation(
            title=podcast_title,
            positive_comments=[],
            negative_comments=[],
            overall_sentiment=0.0,
            top_keywords=[],
            recommendation_summary="沒有找到相關評論數據",
            source="comment_data"
        )
        
    def generate_recommendation_report(self, recommendations: List[PodcastRecommendation],
                                      output_path: str = "podcast_recommendations.txt") -> bool:
        """
        生成推薦報告
        
        Args:
            recommendations: 推薦結果列表
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            report_content = self._create_recommendation_report_content(recommendations)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            logger.info(f"推薦報告已生成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成推薦報告失敗: {e}")
            return False
            
    def _create_recommendation_report_content(self, 
                                             recommendations: List[PodcastRecommendation]) -> str:
        """創建推薦報告內容"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("🎧 PODCAST 推薦分析報告")
        report_lines.append("=" * 80)
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"\n{i}. {rec.title}")
            report_lines.append("-" * 60)
            report_lines.append(f"📊 整體情感分數: {rec.overall_sentiment:.3f}")
            report_lines.append(f"👍 正面評論: {len(rec.positive_comments)} 條")
            report_lines.append(f"👎 負面評論: {len(rec.negative_comments)} 條")
            
            if rec.top_keywords:
                report_lines.append(f"🔑 主要關鍵詞: {', '.join([f'{word}({count})' for word, count in rec.top_keywords[:5]])}")
                
            report_lines.append(f"💡 推薦摘要: {rec.recommendation_summary}")
            
            # 顯示部分正面評論
            if rec.positive_comments:
                report_lines.append("\n   📝 正面評論範例:")
                for j, comment_analysis in enumerate(rec.positive_comments[:3]):
                    comment_preview = comment_analysis.comment[:100] + "..." if len(comment_analysis.comment) > 100 else comment_analysis.comment
                    report_lines.append(f"      {j+1}. {comment_preview}")
                    
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines) 