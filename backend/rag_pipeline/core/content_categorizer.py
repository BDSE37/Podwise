#!/usr/bin/env python3
"""
統一內容處理模組

整合所有內容處理功能：
- 內容分類
- 關鍵詞映射
- 內容摘要
- 標籤提取
- 智能分析

作者: Podwise Team
版本: 2.0.0
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """內容分類枚舉"""
    BUSINESS = "商業"
    EDUCATION = "教育"
    OTHER = "其他"
    MIXED = "混合"


@dataclass
class ContentAnalysis:
    """內容分析結果"""
    category: ContentCategory
    confidence: float
    keywords: List[str] = field(default_factory=list)
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    reasoning: str = ""
    processing_time: float = 0.0


@dataclass
class CategoryResult:
    """分類結果"""
    category: str
    confidence: float
    keywords_found: List[str] = field(default_factory=list)
    reasoning: str = ""
    business_score: float = 0.0
    education_score: float = 0.0


@dataclass
class ContentSummary:
    """內容摘要"""
    summary: str
    key_points: List[str] = field(default_factory=list)
    category: ContentCategory
    confidence: float
    processing_time: float = 0.0


class KeywordProvider(ABC):
    """關鍵詞提供者抽象類別"""
    
    @abstractmethod
    def get_keywords(self) -> Dict[str, List[str]]:
        """獲取關鍵詞"""
        pass


class BusinessKeywordProvider(KeywordProvider):
    """商業關鍵詞提供者"""
    
    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "投資理財": [
                "股票", "基金", "ETF", "債券", "期貨", "選擇權", "外匯",
                "投資組合", "資產配置", "風險管理", "報酬率", "股息",
                "資本利得", "複利", "定存", "活存", "儲蓄", "理財規劃"
            ],
            "股票市場": [
                "台股", "美股", "港股", "日股", "歐股", "新興市場",
                "大盤", "指數", "漲跌", "成交量", "技術分析", "基本面",
                "財報", "EPS", "本益比", "股價淨值比", "ROE", "ROA"
            ],
            "經濟趨勢": [
                "GDP", "通貨膨脹", "利率", "匯率", "失業率", "消費者物價指數",
                "生產者物價指數", "貨幣政策", "財政政策", "經濟成長",
                "景氣循環", "經濟指標", "市場趨勢", "產業分析"
            ],
            "創業職場": [
                "創業", "新創", "募資", "商業模式", "市場定位", "競爭分析",
                "行銷策略", "品牌建立", "客戶開發", "營運管理", "財務管理",
                "人力資源", "領導力", "團隊管理", "職涯發展", "升遷"
            ],
            "科技產業": [
                "AI", "人工智慧", "機器學習", "深度學習", "大數據",
                "雲端運算", "物聯網", "區塊鏈", "加密貨幣", "數位轉型",
                "軟體開發", "硬體製造", "半導體", "晶片", "5G", "6G"
            ]
        }


class EducationKeywordProvider(KeywordProvider):
    """教育關鍵詞提供者"""
    
    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "自我成長": [
                "個人發展", "自我提升", "目標設定", "時間管理", "習慣養成",
                "心態調整", "壓力管理", "情緒管理", "自我認知", "價值觀",
                "人生觀", "世界觀", "自我實現", "成就感", "滿足感"
            ],
            "職涯發展": [
                "職涯規劃", "職業選擇", "技能發展", "專業認證", "進修學習",
                "轉職", "斜槓", "副業", "自由工作者", "遠端工作",
                "工作生活平衡", "職場人際關係", "溝通技巧", "談判技巧"
            ],
            "學習方法": [
                "學習策略", "記憶技巧", "閱讀方法", "筆記技巧", "複習方法",
                "考試準備", "專案學習", "線上學習", "實體課程", "自學",
                "學習動機", "學習效率", "知識管理", "資訊整理"
            ],
            "語言學習": [
                "英文", "日文", "韓文", "法文", "德文", "西班牙文",
                "聽說讀寫", "文法", "單字", "發音", "會話", "翻譯",
                "語言交換", "沉浸式學習", "語言考試", "證照"
            ],
            "心理學": [
                "認知心理學", "社會心理學", "發展心理學", "臨床心理學",
                "行為心理學", "心理治療", "諮商", "心理健康", "心理疾病",
                "心理測驗", "人格特質", "動機理論", "學習理論"
            ],
            "親子教育": [
                "育兒", "親子關係", "兒童發展", "青少年教育", "家庭教育",
                "學校教育", "特殊教育", "資優教育", "品格教育", "性教育",
                "數位素養", "媒體素養", "理財教育", "生命教育"
            ]
        }


class ContentProcessor:
    """統一內容處理器"""
    
    def __init__(self):
        self.business_provider = BusinessKeywordProvider()
        self.education_provider = EducationKeywordProvider()
        self.business_keywords = self._flatten_keywords(self.business_provider.get_keywords())
        self.education_keywords = self._flatten_keywords(self.education_provider.get_keywords())
        
        logger.info("統一內容處理器初始化完成")
    
    def _flatten_keywords(self, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """扁平化關鍵詞字典"""
        flattened = []
        for keywords in keyword_dict.values():
            flattened.extend(keywords)
        return flattened
    
    def analyze_content(self, title: str, content: str) -> ContentAnalysis:
        """
        分析內容
        
        Args:
            title: 標題
            content: 內容
            
        Returns:
            ContentAnalysis: 分析結果
        """
        import time
        start_time = time.time()
        
        # 1. 分類內容
        category_result = self.categorize_content(title, content)
        
        # 2. 提取關鍵詞
        keywords = self.extract_keywords(title + " " + content)
        
        # 3. 生成摘要
        summary = self.generate_summary(content, category_result.category)
        
        # 4. 提取標籤
        tags = self.extract_tags(title + " " + content)
        
        processing_time = time.time() - start_time
        
        return ContentAnalysis(
            category=ContentCategory(category_result.category),
            confidence=category_result.confidence,
            keywords=keywords,
            summary=summary.summary,
            tags=tags,
            reasoning=category_result.reasoning,
            processing_time=processing_time
        )
    
    def categorize_content(self, title: str, content: str) -> CategoryResult:
        """
        分類內容
        
        Args:
            title: 標題
            content: 內容
            
        Returns:
            CategoryResult: 分類結果
        """
        text = (title + " " + content).lower()
        
        # 計算商業分數
        business_score = 0.0
        business_keywords_found = []
        for keyword in self.business_keywords:
            if keyword in text:
                business_score += 0.1
                business_keywords_found.append(keyword)
        
        # 計算教育分數
        education_score = 0.0
        education_keywords_found = []
        for keyword in self.education_keywords:
            if keyword in text:
                education_score += 0.1
                education_keywords_found.append(keyword)
        
        # 正規化分數
        business_score = min(business_score, 1.0)
        education_score = min(education_score, 1.0)
        
        # 決定分類
        if business_score > 0.5 and education_score > 0.5:
            category = "混合"
            confidence = max(business_score, education_score)
            reasoning = f"同時包含商業({business_score:.2f})和教育({education_score:.2f})元素"
        elif business_score > education_score and business_score > 0.3:
            category = "商業"
            confidence = business_score
            reasoning = f"主要為商業內容，分數: {business_score:.2f}"
        elif education_score > business_score and education_score > 0.3:
            category = "教育"
            confidence = education_score
            reasoning = f"主要為教育內容，分數: {education_score:.2f}"
        else:
            category = "其他"
            confidence = max(business_score, education_score, 0.2)
            reasoning = "不屬於主要分類範疇"
        
        return CategoryResult(
            category=category,
            confidence=confidence,
            keywords_found=business_keywords_found + education_keywords_found,
            reasoning=reasoning,
            business_score=business_score,
            education_score=education_score
        )
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        提取關鍵詞
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 關鍵詞列表
        """
        text_lower = text.lower()
        keywords = []
        
        # 從商業關鍵詞中提取
        for keyword in self.business_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # 從教育關鍵詞中提取
        for keyword in self.education_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # 去重並限制數量
        keywords = list(set(keywords))[:10]
        
        return keywords
    
    def generate_summary(self, content: str, category: str) -> ContentSummary:
        """
        生成內容摘要
        
        Args:
            content: 內容
            category: 分類
            
        Returns:
            ContentSummary: 摘要結果
        """
        import time
        start_time = time.time()
        
        # 根據分類生成不同風格的摘要
        if category == "商業":
            summary = self._generate_business_summary(content)
        elif category == "教育":
            summary = self._generate_education_summary(content)
        else:
            summary = self._generate_general_summary(content)
        
        processing_time = time.time() - start_time
        
        return ContentSummary(
            summary=summary,
            key_points=self._extract_key_points(content),
            category=ContentCategory(category),
            confidence=0.8,
            processing_time=processing_time
        )
    
    def _generate_business_summary(self, content: str) -> str:
        """生成商業摘要"""
        # 提取關鍵商業概念
        business_concepts = []
        for keyword in self.business_keywords:
            if keyword in content.lower():
                business_concepts.append(keyword)
        
        # 生成摘要
        if business_concepts:
            summary = f"此內容主要討論{', '.join(business_concepts[:3])}等商業議題。"
        else:
            summary = "此內容涉及商業相關主題。"
        
        # 添加長度資訊
        if len(content) > 500:
            summary += "內容詳實，提供深入分析。"
        else:
            summary += "內容簡潔，重點突出。"
        
        return summary
    
    def _generate_education_summary(self, content: str) -> str:
        """生成教育摘要"""
        # 提取關鍵教育概念
        education_concepts = []
        for keyword in self.education_keywords:
            if keyword in content.lower():
                education_concepts.append(keyword)
        
        # 生成摘要
        if education_concepts:
            summary = f"此內容主要探討{', '.join(education_concepts[:3])}等教育議題。"
        else:
            summary = "此內容涉及教育相關主題。"
        
        # 添加學習價值
        summary += "適合學習者參考和應用。"
        
        return summary
    
    def _generate_general_summary(self, content: str) -> str:
        """生成一般摘要"""
        # 簡單的摘要生成
        sentences = content.split('。')
        if len(sentences) > 1:
            summary = sentences[0] + "。"
        else:
            summary = content[:100] + "..." if len(content) > 100 else content
        
        return summary
    
    def _extract_key_points(self, content: str) -> List[str]:
        """提取關鍵點"""
        # 簡單的關鍵點提取
        sentences = content.split('。')
        key_points = []
        
        for sentence in sentences[:5]:  # 取前5句
            if len(sentence.strip()) > 10:
                key_points.append(sentence.strip() + "。")
        
        return key_points
    
    def extract_tags(self, text: str) -> List[str]:
        """
        提取標籤
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 標籤列表
        """
        # 結合關鍵詞和標籤提取
        keywords = self.extract_keywords(text)
        
        # 添加一些通用標籤
        tags = keywords.copy()
        
        # 根據內容長度添加標籤
        if len(text) > 1000:
            tags.append("詳細")
        else:
            tags.append("簡潔")
        
        # 根據內容類型添加標籤
        if any(word in text.lower() for word in ["podcast", "節目", "音頻"]):
            tags.append("podcast")
        
        if any(word in text.lower() for word in ["推薦", "建議", "分享"]):
            tags.append("推薦")
        
        return list(set(tags))[:10]  # 去重並限制數量
    
    def get_category_keywords(self, category: str) -> Dict[str, List[str]]:
        """
        獲取分類關鍵詞
        
        Args:
            category: 分類
            
        Returns:
            Dict[str, List[str]]: 關鍵詞字典
        """
        if category == "商業":
            return self.business_provider.get_keywords()
        elif category == "教育":
            return self.education_provider.get_keywords()
        else:
            return {}
    
    def add_custom_keywords(self, category: str, new_keywords: Dict[str, List[str]]) -> None:
        """
        添加自定義關鍵詞
        
        Args:
            category: 分類
            new_keywords: 新關鍵詞
        """
        if category == "商業":
            # 更新商業關鍵詞
            current_keywords = self.business_provider.get_keywords()
            current_keywords.update(new_keywords)
            self.business_keywords = self._flatten_keywords(current_keywords)
        elif category == "教育":
            # 更新教育關鍵詞
            current_keywords = self.education_provider.get_keywords()
            current_keywords.update(new_keywords)
            self.education_keywords = self._flatten_keywords(current_keywords)


# 向後相容性別名
ContentCategorizer = ContentProcessor
KeywordMapper = ContentProcessor


# 全域實例
content_processor = ContentProcessor()


def get_content_processor() -> ContentProcessor:
    """獲取內容處理器實例"""
    return content_processor


# 使用範例
if __name__ == "__main__":
    # 測試內容處理
    processor = get_content_processor()
    
    # 測試商業內容
    business_title = "股癌 EP310 - 台股投資分析"
    business_content = "本集討論台股市場趨勢，分析投資策略和風險管理，適合投資者參考。"
    
    business_analysis = processor.analyze_content(business_title, business_content)
    print("商業內容分析:")
    print(f"分類: {business_analysis.category.value}")
    print(f"信心度: {business_analysis.confidence:.2f}")
    print(f"關鍵詞: {', '.join(business_analysis.keywords)}")
    print(f"摘要: {business_analysis.summary}")
    print(f"標籤: {', '.join(business_analysis.tags)}")
    
    print("\n" + "="*50 + "\n")
    
    # 測試教育內容
    education_title = "大人學 EP110 - 職涯發展指南"
    education_content = "本集分享職涯規劃技巧，討論技能發展和個人成長，幫助聽眾提升職場競爭力。"
    
    education_analysis = processor.analyze_content(education_title, education_content)
    print("教育內容分析:")
    print(f"分類: {education_analysis.category.value}")
    print(f"信心度: {education_analysis.confidence:.2f}")
    print(f"關鍵詞: {', '.join(education_analysis.keywords)}")
    print(f"摘要: {education_analysis.summary}")
    print(f"標籤: {', '.join(education_analysis.tags)}") 