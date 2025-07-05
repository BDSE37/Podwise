#!/usr/bin/env python3
"""
Keyword Mapper 工具模組

此模組提供基於關聯詞庫的智能分類功能，支援商業和教育類別的
自動判定，並提供信心值計算和多類別支援。

主要功能：
- 基於關鍵詞的查詢分類
- 信心值計算和推理說明
- 支援自定義關鍵詞擴展
- 多類別判定邏輯

作者: Podwise Team
版本: 2.0.0
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CategoryResult:
    """
    分類結果數據類別
    
    此類別封裝了查詢分類的完整結果，包含類別判定、
    信心值、找到的關鍵詞和推理說明。
    
    Attributes:
        category: 判定類別 ("商業", "教育", "雙類別")
        confidence: 信心值 (0.0-1.0)
        keywords_found: 找到的關鍵詞列表
        reasoning: 分類推理說明
        business_score: 商業類別分數
        education_score: 教育類別分數
    """
    category: str
    confidence: float
    keywords_found: List[str] = field(default_factory=list)
    reasoning: str = ""
    business_score: float = 0.0
    education_score: float = 0.0
    
    def __post_init__(self) -> None:
        """驗證數據完整性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("信心值必須在 0.0 到 1.0 之間")
        
        if self.category not in ["商業", "教育", "雙類別"]:
            raise ValueError("無效的類別值")


class KeywordProvider(ABC):
    """關鍵詞提供者抽象基類"""
    
    @abstractmethod
    def get_keywords(self) -> Dict[str, List[str]]:
        """獲取關鍵詞字典"""
        pass


class BusinessKeywordProvider(KeywordProvider):
    """商業類別關鍵詞提供者"""
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """
        獲取商業類別關鍵詞
        
        Returns:
            商業類別關鍵詞字典，按子類別組織
        """
        return {
            "股票市場": [
                "股票", "股價", "漲跌", "成交量", "市值", "本益比", 
                "股息", "除權除息", "台積電", "聯發科"
            ],
            "投資理財": [
                "投資", "理財", "基金", "債券", "保險", "定存", 
                "外匯", "期貨", "選擇權", "ETF", "共同基金"
            ],
            "總體經濟": [
                "GDP", "通膨", "利率", "匯率", "失業率", "經濟成長", 
                "央行", "財政政策", "貨幣政策", "景氣"
            ],
            "科技產業": [
                "AI", "人工智慧", "5G", "物聯網", "雲端", "大數據", 
                "區塊鏈", "元宇宙", "ChatGPT", "機器學習"
            ],
            "半導體": [
                "晶片", "半導體", "台積電", "聯發科", "英特爾", 
                "AMD", "高通", "三星", "SK海力士", "美光"
            ],
            "市場動態": [
                "市場", "趨勢", "分析", "預測", "報告", "研究", 
                "調查", "產業", "供應鏈", "競爭"
            ],
            "個股情報": [
                "個股", "財報", "營收", "獲利", "展望", "策略", 
                "併購", "股利", "股東會", "法說會"
            ],
            "產業分析": [
                "產業", "供應鏈", "競爭", "創新", "轉型", "升級", 
                "數位化", "自動化", "智能化"
            ],
            "基金投資": [
                "基金", "ETF", "共同基金", "指數基金", "債券基金", 
                "股票基金", "平衡基金", "貨幣基金"
            ],
            "金融保險": [
                "銀行", "保險", "證券", "期貨", "信託", "租賃", 
                "信用卡", "房貸", "車貸", "信貸"
            ],
            "消費零售": [
                "零售", "電商", "百貨", "超市", "餐飲", "旅遊", 
                "娛樂", "購物", "消費", "品牌"
            ],
            "房地產": [
                "房市", "房價", "建商", "土地", "租金", "房貸", 
                "不動產", "預售屋", "中古屋", "租屋"
            ],
            "能源": [
                "石油", "天然氣", "電力", "再生能源", "太陽能", 
                "風電", "核能", "綠能", "碳權", "ESG"
            ],
            "運輸物流": [
                "航運", "物流", "快遞", "倉儲", "配送", "供應鏈", 
                "海運", "空運", "陸運", "冷鏈"
            ],
            "媒體娛樂": [
                "媒體", "娛樂", "影視", "音樂", "遊戲", "廣告", 
                "行銷", "網紅", "直播", "串流"
            ]
        }


class EducationKeywordProvider(KeywordProvider):
    """教育類別關鍵詞提供者"""
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """
        獲取教育類別關鍵詞
        
        Returns:
            教育類別關鍵詞字典，按子類別組織
        """
        return {
            "職涯發展": [
                "職涯", "職業", "工作", "職場", "升遷", "轉職", 
                "創業", "副業", "履歷", "面試", "薪資"
            ],
            "自我實現": [
                "自我", "成長", "實現", "目標", "夢想", "價值", 
                "意義", "使命", "願景", "人生規劃"
            ],
            "設計思維": [
                "設計", "思維", "創新", "創意", "解決問題", 
                "用戶體驗", "原型", "設計思考", "人因工程"
            ],
            "職場技能": [
                "技能", "能力", "溝通", "領導", "管理", "團隊", 
                "協作", "談判", "簡報", "專案管理"
            ],
            "心態建設": [
                "心態", "心理", "情緒", "壓力", "抗壓", "樂觀", 
                "積極", "自信", "韌性", "心理素質"
            ],
            "目標管理": [
                "目標", "計劃", "執行", "追蹤", "檢討", "改進", 
                "效率", "時間管理", "優先級", "SMART"
            ],
            "創新思維": [
                "創新", "創意", "突破", "改變", "變革", "新思維", 
                "新方法", "顛覆", "破壞式創新"
            ],
            "學習方法": [
                "學習", "方法", "技巧", "策略", "記憶", "理解", 
                "應用", "實踐", "刻意練習", "費曼學習法"
            ],
            "知識管理": [
                "知識", "資訊", "整理", "歸納", "分析", "應用", 
                "分享", "知識庫", "筆記", "心智圖"
            ],
            "個人品牌": [
                "品牌", "形象", "聲譽", "影響力", "專業", "權威", 
                "信任", "個人IP", "自媒體", "網紅"
            ],
            "人際關係": [
                "人際", "關係", "社交", "網路", "人脈", "合作", 
                "信任", "溝通", "情商", "社交技巧"
            ],
            "財務素養": [
                "財務", "理財", "投資", "儲蓄", "預算", "規劃", 
                "風險", "財務自由", "被動收入"
            ],
            "健康生活": [
                "健康", "生活", "運動", "飲食", "睡眠", "養生", 
                "平衡", "身心靈", "生活品質", "工作生活平衡"
            ],
            "興趣發展": [
                "興趣", "愛好", "休閒", "娛樂", "創意", "藝術", 
                "音樂", "運動", "旅行", "嗜好"
            ],
            "心理成長": [
                "心理", "成長", "認知", "情緒", "自我認知", 
                "心態調整", "心理學", "自我覺察", "內省"
            ]
        }


class KeywordIndex:
    """關鍵詞索引管理器"""
    
    def __init__(self) -> None:
        """初始化關鍵詞索引"""
        self._business_index: Dict[str, Dict[str, Any]] = {}
        self._education_index: Dict[str, Dict[str, Any]] = {}
    
    def build_index(self, business_keywords: Dict[str, List[str]], 
                   education_keywords: Dict[str, List[str]]) -> None:
        """
        建立關鍵詞索引
        
        Args:
            business_keywords: 商業類別關鍵詞字典
            education_keywords: 教育類別關鍵詞字典
        """
        self._build_category_index(business_keywords, self._business_index)
        self._build_category_index(education_keywords, self._education_index)
        logger.info(f"已建立索引: 商業 {len(self._business_index)} 個, 教育 {len(self._education_index)} 個")
    
    def _build_category_index(self, keywords: Dict[str, List[str]], 
                            index: Dict[str, Dict[str, Any]]) -> None:
        """建立單一類別的關鍵詞索引"""
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                index[keyword.lower()] = {
                    "category": category,
                    "weight": 1.0,
                    "original": keyword
                }
    
    def get_business_index(self) -> Dict[str, Dict[str, Any]]:
        """獲取商業類別索引"""
        return self._business_index.copy()
    
    def get_education_index(self) -> Dict[str, Dict[str, Any]]:
        """獲取教育類別索引"""
        return self._education_index.copy()


class CategoryAnalyzer:
    """類別分析器"""
    
    def __init__(self, confidence_threshold: float = 0.7) -> None:
        """
        初始化類別分析器
        
        Args:
            confidence_threshold: 信心值閾值
        """
        self.confidence_threshold = confidence_threshold
    
    def determine_category(self, business_score: float, education_score: float,
                          business_keywords: List[str], 
                          education_keywords: List[str]) -> Tuple[str, float, str]:
        """
        判斷最終類別
        
        Args:
            business_score: 商業類別分數
            education_score: 教育類別分數
            business_keywords: 找到的商業關鍵詞
            education_keywords: 找到的教育關鍵詞
            
        Returns:
            類別、信心值、推理說明的元組
        """
        total_score = business_score + education_score
        
        if total_score == 0:
            return "教育", 0.3, "未找到明確關鍵詞，預設為教育類別"
        
        business_ratio = business_score / total_score
        education_ratio = education_score / total_score
        
        if business_ratio >= self.confidence_threshold:
            category = "商業"
            confidence = min(business_ratio + 0.2, 1.0)
            reasoning = self._generate_business_reasoning(business_score, business_keywords)
        elif education_ratio >= self.confidence_threshold:
            category = "教育"
            confidence = min(education_ratio + 0.2, 1.0)
            reasoning = self._generate_education_reasoning(education_score, education_keywords)
        else:
            category = "雙類別"
            confidence = min(max(business_ratio, education_ratio) + 0.1, 0.9)
            reasoning = self._generate_dual_category_reasoning(
                business_score, education_score, business_keywords, education_keywords
            )
        
        return category, confidence, reasoning
    
    def _generate_business_reasoning(self, score: float, keywords: List[str]) -> str:
        """生成商業類別推理說明"""
        top_keywords = ", ".join(keywords[:3])
        return f"商業類別分數較高 ({score:.2f})，找到關鍵詞: {top_keywords}"
    
    def _generate_education_reasoning(self, score: float, keywords: List[str]) -> str:
        """生成教育類別推理說明"""
        top_keywords = ", ".join(keywords[:3])
        return f"教育類別分數較高 ({score:.2f})，找到關鍵詞: {top_keywords}"
    
    def _generate_dual_category_reasoning(self, business_score: float, 
                                        education_score: float,
                                        business_keywords: List[str], 
                                        education_keywords: List[str]) -> str:
        """生成雙類別推理說明"""
        return (f"商業分數: {business_score:.2f}, 教育分數: {education_score:.2f}，"
                f"判定為跨類別查詢")


class KeywordMapper:
    """
    關鍵詞映射器
    
    此類別提供基於關聯詞庫的智能分類功能，支援商業和教育類別的
    自動判定，並提供信心值計算和多類別支援。
    
    主要功能：
    - 基於關鍵詞的查詢分類
    - 信心值計算和推理說明
    - 支援自定義關鍵詞擴展
    - 多類別判定邏輯
    """
    
    def __init__(self, business_provider: Optional[KeywordProvider] = None,
                 education_provider: Optional[KeywordProvider] = None) -> None:
        """
        初始化關鍵詞映射器
        
        Args:
            business_provider: 商業類別關鍵詞提供者
            education_provider: 教育類別關鍵詞提供者
        """
        self.business_provider = business_provider or BusinessKeywordProvider()
        self.education_provider = education_provider or EducationKeywordProvider()
        
        # 初始化組件
        self.keyword_index = KeywordIndex()
        self.category_analyzer = CategoryAnalyzer()
        
        # 載入關鍵詞
        self._load_keywords()
        
        logger.info("Keyword Mapper 初始化完成")
    
    def _load_keywords(self) -> None:
        """載入關鍵詞並建立索引"""
        business_keywords = self.business_provider.get_keywords()
        education_keywords = self.education_provider.get_keywords()
        
        self.business_keywords = business_keywords
        self.education_keywords = education_keywords
        
        # 建立索引
        self.keyword_index.build_index(business_keywords, education_keywords)
    
    def categorize_query(self, query: str) -> CategoryResult:
        """
        分類用戶查詢
        
        Args:
            query: 用戶輸入的查詢文字
            
        Returns:
            CategoryResult: 分類結果
            
        Raises:
            ValueError: 當查詢為空或無效時
        """
        if not query or not query.strip():
            raise ValueError("查詢不能為空")
        
        query_lower = query.lower().strip()
        
        # 計算各類別分數
        business_score, business_keywords = self._calculate_category_score(
            query_lower, self.keyword_index.get_business_index()
        )
        
        education_score, education_keywords = self._calculate_category_score(
            query_lower, self.keyword_index.get_education_index()
        )
        
        # 判斷類別
        category, confidence, reasoning = self.category_analyzer.determine_category(
            business_score, education_score, business_keywords, education_keywords
        )
        
        return CategoryResult(
            category=category,
            confidence=confidence,
            keywords_found=business_keywords + education_keywords,
            reasoning=reasoning,
            business_score=business_score,
            education_score=education_score
        )
    
    def _calculate_category_score(self, query: str, 
                                keyword_index: Dict[str, Dict[str, Any]]) -> Tuple[float, List[str]]:
        """
        計算類別分數
        
        Args:
            query: 查詢文字
            keyword_index: 關鍵詞索引
            
        Returns:
            分數和找到的關鍵詞的元組
        """
        found_keywords = []
        total_score = 0.0
        
        for keyword, info in keyword_index.items():
            if keyword in query:
                found_keywords.append(info["original"])
                total_score += info["weight"]
        
        # 根據關鍵詞密度調整分數
        if found_keywords:
            density_bonus = min(len(found_keywords) / len(query.split()), 0.3)
            total_score += density_bonus
        
        return total_score, found_keywords
    
    def get_category_keywords(self, category: str) -> Dict[str, List[str]]:
        """
        獲取指定類別的所有關鍵詞
        
        Args:
            category: 類別名稱 ("商業" 或 "教育")
            
        Returns:
            關鍵詞字典
        """
        if category == "商業":
            return self.business_keywords.copy()
        elif category == "教育":
            return self.education_keywords.copy()
        else:
            return {}
    
    def add_custom_keywords(self, category: str, new_keywords: Dict[str, List[str]]) -> None:
        """
        添加自定義關鍵詞
        
        Args:
            category: 類別名稱 ("商業" 或 "教育")
            new_keywords: 新的關鍵詞字典
        """
        if category == "商業":
            self.business_keywords.update(new_keywords)
        elif category == "教育":
            self.education_keywords.update(new_keywords)
        else:
            raise ValueError("無效的類別名稱")
        
        # 重新建立索引
        self._load_keywords()
        logger.info(f"已添加 {category} 類別的自定義關鍵詞")
    
    def export_keywords_to_json(self, filepath: str) -> None:
        """
        匯出關鍵詞到 JSON 檔案
        
        Args:
            filepath: 檔案路徑
        """
        data = {
            "business_keywords": self.business_keywords,
            "education_keywords": self.education_keywords,
            "export_timestamp": str(datetime.now()),
            "version": "2.0.0"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"關鍵詞已匯出到: {filepath}")
    
    def import_keywords_from_json(self, filepath: str) -> None:
        """
        從 JSON 檔案匯入關鍵詞
        
        Args:
            filepath: 檔案路徑
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.business_keywords = data.get("business_keywords", {})
        self.education_keywords = data.get("education_keywords", {})
        
        # 重新建立索引
        self._load_keywords()
        logger.info(f"關鍵詞已從 {filepath} 匯入")


def test_keyword_mapper() -> None:
    """測試 Keyword Mapper 功能"""
    mapper = KeywordMapper()
    
    # 測試案例
    test_cases = [
        "我想了解台積電的投資機會",
        "如何提升職場溝通技巧",
        "股票市場分析和職涯規劃",
        "學習新技能的方法"
    ]
    
    for query in test_cases:
        result = mapper.categorize_query(query)
        print(f"查詢: {query}")
        print(f"類別: {result.category}")
        print(f"信心值: {result.confidence:.2f}")
        print(f"推理: {result.reasoning}")
        print(f"關鍵詞: {result.keywords_found}")
        print("-" * 50)


if __name__ == "__main__":
    test_keyword_mapper() 