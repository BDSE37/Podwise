#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析器模組

提供中文情感分析和 VADER 情感分析功能
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple
import jieba
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .text_preprocessor import TextPreprocessor
from .lexicon_manager import LexiconManager


@dataclass
class SentimentResult:
    """情感分析結果資料類別"""
    compound: float
    positive: float
    negative: float
    neutral: float
    label: str
    confidence: float


class SentimentAnalyzer(ABC):
    """情感分析器抽象基類"""
    
    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        """分析文本情感"""
        pass


class ChineseSentimentAnalyzer(SentimentAnalyzer):
    """中文情感分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.preprocessor = TextPreprocessor()
        self.lexicon = LexiconManager()
    
    def analyze(self, text: str) -> SentimentResult:
        """
        分析中文文本情感
        
        Args:
            text: 輸入文本
            
        Returns:
            情感分析結果
        """
        # 文本預處理
        cleaned_text = self.preprocessor.clean_text(text)
        tokens = self.preprocessor.tokenize(cleaned_text)
        
        if not tokens:
            return SentimentResult(
                compound=0.0, positive=0.0, negative=0.0, neutral=1.0,
                label='中性', confidence=0.0
            )
        
        # 計算情感分數
        scores = self._calculate_sentiment_scores(tokens)
        
        # 正規化分數
        total_score = abs(scores['positive']) + abs(scores['negative'])
        if total_score > 0:
            positive_norm = scores['positive'] / total_score
            negative_norm = scores['negative'] / total_score
            neutral_norm = 1.0 - positive_norm - negative_norm
        else:
            positive_norm = 0.0
            negative_norm = 0.0
            neutral_norm = 1.0
        
        # 計算 compound 分數
        compound_score = positive_norm - negative_norm
        
        # 獲取情感標籤
        sentiment_label = self._get_sentiment_label(compound_score)
        
        # 計算信心度
        confidence = min(1.0, total_score / len(tokens))
        
        return SentimentResult(
            compound=compound_score,
            positive=positive_norm,
            negative=negative_norm,
            neutral=neutral_norm,
            label=sentiment_label,
            confidence=confidence
        )
    
    def _calculate_sentiment_scores(self, tokens: List[str]) -> Dict[str, float]:
        """計算情感分數"""
        positive_score = 0.0
        negative_score = 0.0
        
        positive_words = self.lexicon.get_positive_words()
        negative_words = self.lexicon.get_negative_words()
        intensifiers = self.lexicon.get_intensifiers()
        negations = self.lexicon.get_negations()
        
        for i, token in enumerate(tokens):
            # 檢查程度詞
            intensity = 1.0
            if token in intensifiers:
                intensity = intensifiers[token]
            
            # 檢查否定詞
            negation_factor = 1.0
            if i > 0 and tokens[i-1] in negations:
                negation_factor = -1.0
            
            # 計算分數
            if token in positive_words:
                positive_score += intensity * negation_factor
            elif token in negative_words:
                negative_score += intensity * negation_factor
        
        return {
            'positive': positive_score,
            'negative': negative_score
        }
    
    def _get_sentiment_label(self, compound_score: float) -> str:
        """根據 compound 分數獲取情感標籤"""
        if compound_score >= 0.3:
            return '正面'
        elif compound_score <= -0.3:
            return '負面'
        else:
            return '中性'


class VADERSentimentAnalyzer(SentimentAnalyzer):
    """VADER 情感分析器"""
    
    def __init__(self):
        """初始化 VADER 分析器"""
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> SentimentResult:
        """
        使用 VADER 分析文本情感
        
        Args:
            text: 輸入文本
            
        Returns:
            情感分析結果
        """
        if not text or len(text.strip()) < 5:
            return SentimentResult(
                compound=0.0, positive=0.0, negative=0.0, neutral=1.0,
                label='中性', confidence=0.0
            )
        
        # VADER 分析
        scores = self.analyzer.polarity_scores(text)
        
        # 獲取情感標籤
        sentiment_label = self._get_sentiment_label(scores['compound'])
        
        # 計算信心度（基於分數強度）
        confidence = abs(scores['compound'])
        
        return SentimentResult(
            compound=scores['compound'],
            positive=scores['pos'],
            negative=scores['neg'],
            neutral=scores['neu'],
            label=sentiment_label,
            confidence=confidence
        )
    
    def _get_sentiment_label(self, compound_score: float) -> str:
        """根據 compound 分數獲取情感標籤"""
        if compound_score >= 0.05:
            return '正面'
        elif compound_score <= -0.05:
            return '負面'
        else:
            return '中性' 