"""
內容分類器 - 專門處理內容分類邏輯
"""

import re
import logging
from typing import List, Dict, Any
from .content_models import ContentCategory

logger = logging.getLogger(__name__)

class ContentCategorizer:
    """內容分類器 - 專門處理商業和教育類別分類"""
    
    def __init__(self):
        """初始化分類器"""
        # 商業類別關鍵詞 (參考 MoneyDJ 財經百科)
        self.business_keywords = {
            "股票市場": ["股票", "股價", "漲跌", "成交量", "市值", "本益比", "股息", "除權除息"],
            "投資理財": ["投資", "理財", "基金", "債券", "保險", "定存", "外匯", "期貨", "選擇權"],
            "總體經濟": ["GDP", "通膨", "利率", "匯率", "失業率", "經濟成長", "央行", "財政政策"],
            "科技產業": ["AI", "人工智慧", "5G", "物聯網", "雲端", "大數據", "區塊鏈", "元宇宙"],
            "半導體": ["晶片", "半導體", "台積電", "聯發科", "英特爾", "AMD", "高通"],
            "市場動態": ["市場", "趨勢", "分析", "預測", "報告", "研究", "調查"],
            "個股情報": ["個股", "財報", "營收", "獲利", "展望", "策略", "併購"],
            "產業分析": ["產業", "供應鏈", "競爭", "創新", "轉型", "升級"],
            "基金投資": ["基金", "ETF", "共同基金", "指數基金", "債券基金"],
            "金融保險": ["銀行", "保險", "證券", "期貨", "信託", "租賃"],
            "消費零售": ["零售", "電商", "百貨", "超市", "餐飲", "旅遊", "娛樂"],
            "房地產": ["房市", "房價", "建商", "土地", "租金", "房貸", "不動產"],
            "能源": ["石油", "天然氣", "電力", "再生能源", "太陽能", "風電"],
            "運輸物流": ["航運", "物流", "快遞", "倉儲", "配送", "供應鏈"],
            "媒體娛樂": ["媒體", "娛樂", "影視", "音樂", "遊戲", "廣告", "行銷"]
        }
        
        # 教育類別關鍵詞 (專注自我成長和學習)
        self.education_keywords = {
            "職涯發展": ["職涯", "職業", "工作", "職場", "升遷", "轉職", "創業", "副業"],
            "自我實現": ["自我", "成長", "實現", "目標", "夢想", "價值", "意義", "使命"],
            "設計思維": ["設計", "思維", "創新", "創意", "解決問題", "用戶體驗", "原型"],
            "職場技能": ["技能", "能力", "溝通", "領導", "管理", "團隊", "協作", "談判"],
            "心態建設": ["心態", "心理", "情緒", "壓力", "抗壓", "樂觀", "積極", "自信"],
            "目標管理": ["目標", "計劃", "執行", "追蹤", "檢討", "改進", "效率", "時間管理"],
            "創新思維": ["創新", "創意", "突破", "改變", "變革", "新思維", "新方法"],
            "學習方法": ["學習", "方法", "技巧", "策略", "記憶", "理解", "應用", "實踐"],
            "知識管理": ["知識", "資訊", "整理", "歸納", "分析", "應用", "分享"],
            "個人品牌": ["品牌", "形象", "聲譽", "影響力", "專業", "權威", "信任"],
            "人際關係": ["人際", "關係", "社交", "網路", "人脈", "合作", "信任"],
            "財務素養": ["財務", "理財", "投資", "儲蓄", "預算", "規劃", "風險"],
            "健康生活": ["健康", "生活", "運動", "飲食", "睡眠", "養生", "平衡"],
            "興趣發展": ["興趣", "愛好", "休閒", "娛樂", "創意", "藝術", "音樂"],
            "心理成長": ["心理", "成長", "認知", "情緒", "自我認知", "心態調整"]
        }
    
    def categorize_content(self, title: str, content: str) -> ContentCategory:
        """
        分類內容 (商業類別參考 MoneyDJ 財經百科，教育類別專注自我成長)
        
        Args:
            title: 內容標題
            content: 內容文本
            
        Returns:
            ContentCategory: 內容類別
        """
        text = f"{title} {content}".lower()
        
        # 首先判斷是否為商業類別
        business_keywords = [
            "股票", "投資", "理財", "基金", "債券", "保險", "定存", "外匯", "期貨",
            "GDP", "通膨", "利率", "匯率", "失業率", "經濟", "央行", "財政",
            "AI", "人工智慧", "5G", "物聯網", "雲端", "大數據", "區塊鏈",
            "晶片", "半導體", "台積電", "聯發科", "英特爾", "AMD", "高通",
            "市場", "趨勢", "分析", "預測", "報告", "研究", "調查",
            "個股", "財報", "營收", "獲利", "展望", "策略", "併購",
            "產業", "供應鏈", "競爭", "創新", "轉型", "升級",
            "銀行", "證券", "期貨", "信託", "租賃", "零售", "電商", "百貨",
            "房市", "房價", "建商", "土地", "租金", "房貸", "不動產",
            "石油", "天然氣", "電力", "再生能源", "太陽能", "風電",
            "航運", "物流", "快遞", "倉儲", "配送", "媒體", "娛樂", "影視"
        ]
        
        # 判斷是否為商業類別
        business_score = sum(1 for keyword in business_keywords if keyword.lower() in text)
        is_business = business_score >= 2  # 至少包含2個商業關鍵詞才判定為商業類別
        
        if is_business:
            # 商業類別：參考 MoneyDJ 財經百科的分類體系
            return self._categorize_business_content(title, content)
        else:
            # 非商業類別：專注教育、自我成長等
            return self._categorize_education_content(title, content)
    
    def _categorize_business_content(self, title: str, content: str) -> ContentCategory:
        """商業類別分類 (參考 MoneyDJ 財經百科)"""
        text = f"{title} {content}".lower()
        
        # 計算各類別分數
        scores = {category: 0 for category in self.business_keywords.keys()}
        
        for category, words in self.business_keywords.items():
            for word in words:
                if word.lower() in text:
                    if category in ["股票市場", "投資理財", "總體經濟", "科技產業", "半導體"]:
                        scores[category] += 3  # 核心財經類別
                    elif category in ["市場動態", "個股情報", "產業分析", "基金投資", "金融保險"]:
                        scores[category] += 2  # 重要財經類別
                    else:
                        scores[category] += 1  # 一般類別
        
        # 選擇得分最高的類別
        main_category = max(scores.items(), key=lambda x: x[1])[0]
        
        # 確定子類別
        if main_category == "股票市場":
            if "市場" in text or "趨勢" in text:
                sub_category = "市場動態"
            elif "個股" in text or "財報" in text:
                sub_category = "個股情報"
            elif "產業" in text:
                sub_category = "產業分析"
            else:
                sub_category = "一般股票"
        elif main_category == "投資理財":
            if "基金" in text:
                sub_category = "基金投資"
            elif "債券" in text or "定存" in text:
                sub_category = "固定收益"
            else:
                sub_category = "一般理財"
        elif main_category == "總體經濟":
            if "國際" in text or "全球" in text:
                sub_category = "國際金融"
            else:
                sub_category = "國內經濟"
        else:
            sub_category = "其他"
        
        # 生成標籤
        tags = []
        for category, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0 and len(tags) < 5:
                tags.append(category)
        
        return ContentCategory(
            main_category=main_category,
            sub_category=sub_category,
            tags=tags
        )
    
    def _categorize_education_content(self, title: str, content: str) -> ContentCategory:
        """教育類別分類 (專注自我成長和學習)"""
        text = f"{title} {content}".lower()
        
        # 計算各類別分數
        scores = {category: 0 for category in self.education_keywords.keys()}
        
        for category, words in self.education_keywords.items():
            for word in words:
                if word.lower() in text:
                    if category in ["職涯發展", "自我實現", "設計思維"]:
                        scores[category] += 3  # 核心教育類別
                    elif category in ["職場技能", "心態建設", "目標管理", "創新思維"]:
                        scores[category] += 2  # 重要教育類別
                    else:
                        scores[category] += 1  # 一般類別
        
        # 選擇得分最高的類別
        main_category = max(scores.items(), key=lambda x: x[1])[0]
        
        # 確定子類別
        if main_category == "職涯發展":
            if "技能" in text or "能力" in text:
                sub_category = "職場技能"
            elif "創業" in text or "副業" in text:
                sub_category = "專業成長"
            else:
                sub_category = "一般職涯"
        elif main_category == "自我實現":
            if "心態" in text or "心理" in text:
                sub_category = "心態建設"
            elif "目標" in text or "計劃" in text:
                sub_category = "目標管理"
            else:
                sub_category = "一般成長"
        elif main_category == "設計思維":
            if "創新" in text or "創意" in text:
                sub_category = "創新思維"
            else:
                sub_category = "一般設計"
        else:
            sub_category = "其他"
        
        # 生成標籤
        tags = []
        for category, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0 and len(tags) < 5:
                tags.append(category)
        
        return ContentCategory(
            main_category=main_category,
            sub_category=sub_category,
            tags=tags
        ) 