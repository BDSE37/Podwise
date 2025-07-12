#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析器核心類別

提供中文文本情感分析功能
使用關鍵字匹配方法進行情感分析

作者: Podwise Team
版本: 2.0.0
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """情感分析結果數據類別"""
    text: str
    positive_score: float
    negative_score: float
    neutral_score: float
    compound_score: float
    sentiment_label: str
    confidence: float


class SentimentAnalyzer:
    """
    情感分析器
    
    使用關鍵字匹配方法進行中文情感分析
    專門用於 podcast 評論的情感分析
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化情感分析器
        
        Args:
            config_path: 配置檔案路徑，如果為 None 則使用預設配置
        """
        self._load_sentiment_lexicon()
        self._setup_logging()
        
    def _load_sentiment_lexicon(self) -> None:
        """載入情感詞彙庫"""
        # 正面情感關鍵字
        self.positive_words = {
            '推薦', '喜歡', '很棒', '優秀', '讚', '好', '棒', '讚美', '滿意', '開心',
            '感動', '受益', '收穫', '啟發', '幫助', '實用', '精彩', '有趣', '專業',
            '用心', '認真', '負責', '熱情', '友善', '親切', '溫暖', '貼心', '周到',
            '準確', '清晰', '易懂', '深入', '全面', '詳細', '完整', '豐富', '充實',
            '有價值', '有意義', '有幫助', '有啟發', '有收穫', '有進步', '有成長',
            '支持', '鼓勵', '肯定', '認同', '理解', '共鳴', '感謝', '謝謝', '愛',
            '學習', '知識', '智慧', '經驗', '分享', '交流', '討論', '思考', '反思',
            '成長', '進步', '提升', '改善', '解決', '答案', '方法', '技巧', '策略',
            '觀點', '見解', '分析', '研究', '成功', '成就', '突破', '創新', '創意',
            '想法', '概念', '理論', '實踐', '爆笑', '真實', '不可思議', '愛上',
            '正經', '崩潰', '煩惱', '心路歷程', '心靈成長', '時事', '興趣', '試試'
        }
        
        # 負面情感關鍵字
        self.negative_words = {
            '不喜歡', '討厭', '差', '爛', '糟', '壞', '失望', '不滿', '抱怨', '批評',
            '指責', '責怪', '厭惡', '反感', '不適', '不舒服', '無聊', '枯燥', '乏味',
            '單調', '重複', '老套', '過時', '落伍', '錯誤', '不準確', '不清楚', '難懂',
            '複雜', '混亂', '雜亂', '無序', '浪費', '無用', '無意義', '無幫助',
            '無啟發', '無收穫', '無進步', '反對', '否定', '拒絕', '排斥', '不認同',
            '不理解', '不開心', '不滿意', '不快樂', '不幸福', '不順利', '不成功',
            '傷害', '靈魂出竅', '鬧劇', '煩惱', '傷害'
        }
        
        # 否定詞（會反轉情感）
        self.negation_words = {
            '不', '沒', '無', '非', '未', '別', '莫', '勿', '毋', '弗', '否', '反',
            '反對', '拒絕', '否定', '不是', '沒有', '無法', '不能', '不會', '不該',
            '不該', '不該', '不該', '不該', '不該', '不該', '不該', '不該', '不該'
        }
        
        # 程度副詞（會增強或減弱情感）
        self.intensifier_words = {
            '非常', '極其', '特別', '十分', '很', '相當', '比較', '有點', '稍微',
            '超級', '極度', '無比', '異常', '格外', '尤其', '更加', '越發', '愈發'
        }
        
    def _setup_logging(self) -> None:
        """設定日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def analyze_text(self, text: str) -> SentimentResult:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            SentimentResult: 情感分析結果
        """
        if not text or not text.strip():
            return self._create_neutral_result(text)
            
        # 清理文本
        cleaned_text = self._clean_text(text)
        
        # 提取詞彙
        words = self._extract_words(cleaned_text)
        
        # 計算情感分數
        positive_score, negative_score, neutral_score = self._calculate_scores(words)
        
        # 計算複合分數
        compound_score = self._calculate_compound_score(positive_score, negative_score)
        
        # 確定情感標籤
        sentiment_label = self._determine_sentiment_label(compound_score)
        
        # 計算信心度
        confidence = self._calculate_confidence(positive_score, negative_score, neutral_score)
        
        return SentimentResult(
            text=text,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            compound_score=compound_score,
            sentiment_label=sentiment_label,
            confidence=confidence
        )
        
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除特殊字符，保留中文、英文、數字和基本標點
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】]', '', text)
        return text.strip()
        
    def _extract_words(self, text: str) -> List[str]:
        """提取詞彙"""
        # 分割詞彙（中文按字符，英文按單詞）
        words = re.findall(r'[\u4e00-\u9fff]|\w+', text)
        return [word for word in words if len(word) > 0]
        
    def _calculate_scores(self, words: List[str]) -> Tuple[float, float, float]:
        """計算情感分數"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for i, word in enumerate(words):
            # 檢查否定詞
            is_negated = self._is_negated(words, i)
            # 檢查程度副詞
            intensity = self._get_intensity(words, i)
            
            if word in self.positive_words:
                score = 1.0 * intensity
                if is_negated:
                    negative_count += score
                else:
                    positive_count += score
            elif word in self.negative_words:
                score = 1.0 * intensity
                if is_negated:
                    positive_count += score
                else:
                    negative_count += score
            else:
                neutral_count += 1
                
        total_words = len(words) if words else 1
        
        return (
            positive_count / total_words,
            negative_count / total_words,
            neutral_count / total_words
        )
        
    def _is_negated(self, words: List[str], index: int) -> bool:
        """檢查詞彙是否被否定"""
        # 檢查前後的否定詞
        for i in range(max(0, index - 2), min(len(words), index + 3)):
            if words[i] in self.negation_words:
                return True
        return False
        
    def _get_intensity(self, words: List[str], index: int) -> float:
        """獲取程度強度"""
        intensity = 1.0
        # 檢查前後的程度副詞
        for i in range(max(0, index - 2), min(len(words), index + 3)):
            if words[i] in self.intensifier_words:
                if '非常' in words[i] or '極其' in words[i] or '超級' in words[i]:
                    intensity *= 2.0
                elif '很' in words[i] or '十分' in words[i]:
                    intensity *= 1.5
                elif '有點' in words[i] or '稍微' in words[i]:
                    intensity *= 0.5
        return intensity
        
    def _calculate_compound_score(self, positive: float, negative: float) -> float:
        """計算複合分數"""
        # 將 -1 到 1 的範圍轉換為 0 到 1
        if positive > negative:
            return (positive - negative) / (positive + negative + 0.1)
        elif negative > positive:
            return -(negative - positive) / (positive + negative + 0.1)
        else:
            return 0.0
            
    def _determine_sentiment_label(self, compound_score: float) -> str:
        """確定情感標籤"""
        if compound_score >= 0.1:
            return 'positive'
        elif compound_score <= -0.1:
            return 'negative'
        else:
            return 'neutral'
            
    def _calculate_confidence(self, positive: float, negative: float, neutral: float) -> float:
        """計算信心度"""
        total = positive + negative + neutral
        if total == 0:
            return 0.0
        # 信心度基於情感詞彙的比例
        return (positive + negative) / total
        
    def _create_neutral_result(self, text: str) -> SentimentResult:
        """創建中性結果"""
        return SentimentResult(
            text=text,
            positive_score=0.0,
            negative_score=0.0,
            neutral_score=1.0,
            compound_score=0.0,
            sentiment_label='neutral',
            confidence=0.0
        )
        
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        批量分析文本
        
        Args:
            texts: 文本列表
            
        Returns:
            List[SentimentResult]: 情感分析結果列表
        """
        results = []
        for text in texts:
            try:
                result = self.analyze_text(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"分析文本失敗: {e}")
                results.append(self._create_neutral_result(text))
        return results
        
    def get_statistics(self, results: List[SentimentResult]) -> Dict[str, float]:
        """
        獲取統計資訊
        
        Args:
            results: 情感分析結果列表
            
        Returns:
            Dict[str, float]: 統計資訊
        """
        if not results:
            return {}
            
        total = len(results)
        positive_count = sum(1 for r in results if r.sentiment_label == 'positive')
        negative_count = sum(1 for r in results if r.sentiment_label == 'negative')
        neutral_count = sum(1 for r in results if r.sentiment_label == 'neutral')
        
        avg_confidence = sum(r.confidence for r in results) / total
        avg_compound = sum(r.compound_score for r in results) / total
        
        return {
            'total_texts': total,
            'positive_ratio': positive_count / total,
            'negative_ratio': negative_count / total,
            'neutral_ratio': neutral_count / total,
            'average_confidence': avg_confidence,
            'average_compound_score': avg_compound
        } 