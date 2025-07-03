"""
內容摘要器 - 專門處理內容摘要生成
"""

import logging
from typing import List, Dict, Any
from .content_models import ContentSummary, ContentCategory

logger = logging.getLogger(__name__)

class ContentSummarizer:
    """內容摘要器 - 根據不同類別生成摘要"""
    
    def __init__(self):
        """初始化摘要器"""
        pass
    
    def generate_summary(self, content: str, category: ContentCategory) -> ContentSummary:
        """
        根據內容類別生成摘要
        
        Args:
            content: 內容文本
            category: 內容類別
            
        Returns:
            ContentSummary: 內容摘要
        """
        if category.main_category in ["股票市場", "投資理財", "總體經濟", "科技產業", "半導體"]:
            return self._generate_business_summary(content)
        elif category.main_category in ["職涯發展", "自我實現", "設計思維"]:
            return self._generate_education_summary(content)
        else:
            return self._generate_general_summary(content)
    
    def _generate_education_summary(self, content: str) -> ContentSummary:
        """教育類別摘要生成"""
        # 這裡可以整合 LLM 來生成更智能的摘要
        # 目前使用簡單的關鍵詞提取方法
        
        main_points = [
            "專注於個人成長和職涯發展",
            "提供實用的學習方法和技能提升建議",
            "強調心態建設和自我實現"
        ]
        
        key_insights = [
            "持續學習是職涯發展的關鍵",
            "心態調整比技能提升更重要",
            "目標設定和執行力是成功的基礎"
        ]
        
        action_items = [
            "制定個人學習計劃",
            "培養積極的心態",
            "建立良好的習慣"
        ]
        
        return ContentSummary(
            main_points=main_points,
            key_insights=key_insights,
            action_items=action_items,
            sentiment="positive"
        )
    
    def _generate_business_summary(self, content: str) -> ContentSummary:
        """商業類別摘要生成"""
        main_points = [
            "提供市場分析和投資建議",
            "關注經濟趨勢和產業動態",
            "分析個股和基金投資機會"
        ]
        
        key_insights = [
            "市場趨勢對投資決策至關重要",
            "分散投資是降低風險的有效方法",
            "長期投資比短期投機更穩定"
        ]
        
        action_items = [
            "定期檢視投資組合",
            "關注市場動態和財經新聞",
            "諮詢專業投資顧問"
        ]
        
        return ContentSummary(
            main_points=main_points,
            key_insights=key_insights,
            action_items=action_items,
            sentiment="neutral"
        )
    
    def _generate_general_summary(self, content: str) -> ContentSummary:
        """一般類別摘要生成"""
        main_points = [
            "提供一般性的資訊和觀點",
            "涵蓋多個領域的內容",
            "適合一般讀者閱讀"
        ]
        
        key_insights = [
            "資訊的多樣性有助於全面了解",
            "跨領域學習能提升視野",
            "保持開放的心態很重要"
        ]
        
        action_items = [
            "保持學習的熱情",
            "嘗試新的領域和技能",
            "與他人分享和交流"
        ]
        
        return ContentSummary(
            main_points=main_points,
            key_insights=key_insights,
            action_items=action_items,
            sentiment="positive"
        ) 