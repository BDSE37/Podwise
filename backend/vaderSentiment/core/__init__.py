"""
繁體中文情感分析核心模組

提供統一的 OOP 架構，包含：
- 文本預處理
- 情感分析引擎
- 資料處理器
- 詞典管理
"""

from .text_preprocessor import TextPreprocessor
from .sentiment_analyzer import ChineseSentimentAnalyzer, VADERSentimentAnalyzer
from .data_processor import DataProcessor
from .lexicon_manager import LexiconManager

__all__ = [
    'TextPreprocessor',
    'ChineseSentimentAnalyzer', 
    'VADERSentimentAnalyzer',
    'DataProcessor',
    'LexiconManager'
] 