#!/usr/bin/env python3
"""
Podwise VADER Sentiment Analysis 模組

提供統一的 OOP 介面，整合所有情感分析功能：
- 中文情感分析
- VADER 情感分析
- 文本預處理
- 詞彙管理
- 數據處理
- 可視化介面

作者: Podwise Team
版本: 2.0.0
"""

# 主要介面
from .main import PodwiseSentimentAnalysis, get_sentiment_analysis

# 核心模組
from .core.sentiment_analyzer import (
    ChineseSentimentAnalyzer, 
    VADERSentimentAnalyzer, 
    SentimentResult
)
from .core.text_preprocessor import TextPreprocessor
from .core.lexicon_manager import LexiconManager
from .core.data_processor import DataProcessor, ProcessedItem

# 腳本模組
from .scripts.interactive_dashboard import InteractiveAnalyzer, InteractiveVisualizer
from .scripts.sentiment_multitopic_polar import (
    set_chinese_font,
    get_json_files,
    classify_topic,
    classify_emotions,
    plot_sentiment_polarity_doughnut,
    plot_topic_sentiment_polarity_doughnut
)

# 版本資訊
__version__ = "2.0.0"
__author__ = "Podwise Team"
__description__ = "整合中文和 VADER 情感分析的智能系統"

# 主要導出
__all__ = [
    # 主要介面
    "PodwiseSentimentAnalysis",
    "get_sentiment_analysis",
    
    # 核心模組
    "ChineseSentimentAnalyzer",
    "VADERSentimentAnalyzer", 
    "SentimentResult",
    "TextPreprocessor",
    "LexiconManager",
    "DataProcessor",
    "ProcessedItem",
    
    # 腳本模組
    "InteractiveAnalyzer",
    "InteractiveVisualizer",
    "set_chinese_font",
    "get_json_files",
    "classify_topic",
    "classify_emotions",
    "plot_sentiment_polarity_doughnut",
    "plot_topic_sentiment_polarity_doughnut",
    
    # 版本資訊
    "__version__",
    "__author__",
    "__description__"
] 