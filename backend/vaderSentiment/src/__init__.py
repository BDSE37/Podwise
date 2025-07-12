"""
VaderSentiment 模組

提供 podcast 情感分析功能的完整解決方案
包含情感分析、排名分析、評論分析等功能

作者: Podwise Team
版本: 2.0.0
"""

from .core.sentiment_analyzer import SentimentAnalyzer
from .core.podcast_ranking import PodcastRankingAnalyzer
from .core.comment_analyzer import CommentAnalyzer
from .utils.data_processor import DataProcessor
from .utils.report_generator import ReportGenerator

__version__ = "2.0.0"
__author__ = "Podwise Team"

__all__ = [
    "SentimentAnalyzer",
    "PodcastRankingAnalyzer", 
    "CommentAnalyzer",
    "DataProcessor",
    "ReportGenerator"
] 