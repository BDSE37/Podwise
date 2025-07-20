#!/usr/bin/env python3
"""
Podwise RAG Pipeline - FAQ Fallback 服務

提供基於 FAQ 的備援回話功能，當向量檢索信心度低時使用。
整合到 RAG Pipeline 的 fallback 機制中。

作者: Podwise Team
版本: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from config.prompt_templates import get_prompt_template, format_prompt
except ImportError:
    # 備用導入
    def get_prompt_template(name: str):
        return None
    def format_prompt(template, **kwargs):
        return "抱歉，我暫時無法理解您的需求。請嘗試重新描述。"

logger = logging.getLogger(__name__)


@dataclass
class FAQItem:
    """FAQ 項目資料結構"""
    keywords: List[str]
    category: str
    response_template: str
    confidence_threshold: float = 0.6
    priority: int = 1


@dataclass
class FallbackResult:
    """Fallback 結果資料結構"""
    content: str
    confidence: float
    source: str
    matched_faq: Optional[FAQItem] = None
    suggested_categories: List[str] = None


class FAQFallbackService:
    """FAQ Fallback 服務類別"""
    
    def __init__(self):
        """初始化 FAQ Fallback 服務"""
        self.faq_database = self._initialize_faq_database()
        self.category_keywords = self._initialize_category_keywords()
        logger.info("FAQ Fallback 服務初始化完成")
    
    def _initialize_faq_database(self) -> List[FAQItem]:
        """初始化 FAQ 資料庫"""
        return [
            # 投資理財相關
            FAQItem(
                keywords=["投資", "理財", "股票", "基金", "ETF", "賺錢", "財務自由"],
                category="商業",
                response_template="投資理財",
                confidence_threshold=0.7,
                priority=1
            ),
            FAQItem(
                keywords=["創業", "職場", "工作", "事業", "副業", "斜槓"],
                category="商業",
                response_template="職涯發展",
                confidence_threshold=0.7,
                priority=1
            ),
            
            # 教育學習相關
            FAQItem(
                keywords=["學習", "成長", "自我提升", "技能", "知識"],
                category="教育",
                response_template="自我成長",
                confidence_threshold=0.7,
                priority=1
            ),
            FAQItem(
                keywords=["語言", "英文", "日文", "韓文", "外語"],
                category="教育",
                response_template="語言學習",
                confidence_threshold=0.7,
                priority=1
            ),
            FAQItem(
                keywords=["心理", "心靈", "情緒", "壓力", "焦慮", "冥想"],
                category="教育",
                response_template="心理健康",
                confidence_threshold=0.7,
                priority=1
            ),
            
            # 生活娛樂相關
            FAQItem(
                keywords=["通勤", "上班", "下班", "路上", "車上"],
                category="其他",
                response_template="通勤時段",
                confidence_threshold=0.7,
                priority=1
            ),
            FAQItem(
                keywords=["睡前", "睡覺", "助眠", "放鬆", "休息"],
                category="其他",
                response_template="睡前放鬆",
                confidence_threshold=0.7,
                priority=1
            ),
            FAQItem(
                keywords=["無聊", "打發時間", "背景", "隨機", "推薦"],
                category="其他",
                response_template="隨機推薦",
                confidence_threshold=0.6,
                priority=2
            ),
            
            # 技術相關
            FAQItem(
                keywords=["科技", "AI", "人工智慧", "程式", "技術"],
                category="商業",
                response_template="科技趨勢",
                confidence_threshold=0.7,
                priority=1
            ),
            
            # 健康相關
            FAQItem(
                keywords=["健康", "運動", "健身", "飲食", "營養"],
                category="教育",
                response_template="健康生活",
                confidence_threshold=0.7,
                priority=1
            ),
        ]
    
    def _initialize_category_keywords(self) -> Dict[str, List[str]]:
        """初始化類別關鍵字"""
        return {
            "商業": ["投資", "理財", "股票", "創業", "職場", "科技", "經濟", "財務"],
            "教育": ["學習", "成長", "語言", "心理", "健康", "職涯", "技能"],
            "其他": ["通勤", "睡前", "放鬆", "娛樂", "隨機", "背景"]
        }
    
    def get_fallback_reply(self, user_query: str) -> FallbackResult:
        """
        獲取 FAQ fallback 回覆
        
        Args:
            user_query: 用戶查詢
            
        Returns:
            FallbackResult: fallback 回覆結果
        """
        try:
            # 1. 嘗試匹配 FAQ
            matched_faq = self._match_faq(user_query)
            
            if matched_faq:
                # 使用 FAQ 模板生成回覆
                content = self._generate_faq_reply(user_query, matched_faq)
                return FallbackResult(
                    content=content,
                    confidence=matched_faq.confidence_threshold,
                    source="faq_fallback",
                    matched_faq=matched_faq,
                    suggested_categories=self._get_suggested_categories(user_query)
                )
            else:
                # 使用預設 fallback 模板
                content = self._generate_default_fallback_reply(user_query)
                return FallbackResult(
                    content=content,
                    confidence=0.5,
                    source="default_fallback",
                    suggested_categories=self._get_suggested_categories(user_query)
                )
                
        except Exception as e:
            logger.error(f"FAQ fallback 處理失敗: {e}")
            return FallbackResult(
                content="抱歉，我暫時無法理解您的需求。請嘗試重新描述。",
                confidence=0.3,
                source="error_fallback"
            )
    
    def _match_faq(self, user_query: str) -> Optional[FAQItem]:
        """匹配 FAQ 項目"""
        query_lower = user_query.lower()
        best_match = None
        best_score = 0.0
        
        for faq in self.faq_database:
            score = self._calculate_match_score(query_lower, faq)
            if score > best_score and score >= faq.confidence_threshold:
                best_score = score
                best_match = faq
        
        return best_match
    
    def _calculate_match_score(self, query: str, faq: FAQItem) -> float:
        """計算匹配分數"""
        score = 0.0
        total_keywords = len(faq.keywords)
        matched_keywords = 0
        
        for keyword in faq.keywords:
            if keyword in query:
                matched_keywords += 1
                # 精確匹配給予更高分數
                if re.search(r'\b' + re.escape(keyword) + r'\b', query):
                    score += 1.0
                else:
                    score += 0.7
        
        # 計算匹配率
        match_rate = matched_keywords / total_keywords if total_keywords > 0 else 0
        
        # 綜合分數：匹配率 + 關鍵字分數
        final_score = (match_rate * 0.6) + (score / total_keywords * 0.4) if total_keywords > 0 else 0
        
        return min(final_score, 1.0)
    
    def _generate_faq_reply(self, user_query: str, matched_faq: FAQItem) -> str:
        """生成 FAQ 回覆"""
        try:
            template = get_prompt_template("faq_fallback")
            if template:
                return format_prompt(
                    template,
                    user_question=user_query,
                    matched_faq=matched_faq.response_template,
                    suggested_categories=self._get_suggested_categories(user_query)
                )
            else:
                # 備用回覆
                return f"""嗨嗨👋 我理解您想了解「{matched_faq.response_template}」相關的 Podcast！

💡 建議您可以：
1. 試試「{matched_faq.category}」類別的節目
2. 或者告訴我您具體想聽什麼類型的內容
3. 也可以說說您的使用情境（通勤、睡前、學習等）

🎧 我這裡有豐富的節目庫，一定能找到適合您的內容！

有什麼想法都可以跟我說，我會繼續為您推薦 😊"""
                
        except Exception as e:
            logger.error(f"生成 FAQ 回覆失敗: {e}")
            return "抱歉，我暫時無法理解您的需求。請嘗試重新描述。"
    
    def _generate_default_fallback_reply(self, user_query: str) -> str:
        """生成預設 fallback 回覆"""
        try:
            template = get_prompt_template("default_fallback")
            if template:
                return format_prompt(template, user_question=user_query)
            else:
                # 備用回覆
                return """嗨嗨👋 抱歉，我可能沒有完全理解您的需求 😅

🎧 我是 Podri，專門為您推薦適合的 Podcast 節目！

💡 您可以試試：
• 「我想聽投資理財的 Podcast」
• 「推薦一些自我成長的節目」
• 「通勤時間有什麼推薦？」
• 「睡前想聽放鬆的內容」

或者直接說「推薦」，我會為您精選一些熱門節目！

有什麼想法都可以跟我說，我會努力為您找到最適合的內容 😊"""
                
        except Exception as e:
            logger.error(f"生成預設 fallback 回覆失敗: {e}")
            return "抱歉，我暫時無法理解您的需求。請嘗試重新描述。"
    
    def _get_suggested_categories(self, user_query: str) -> List[str]:
        """獲取建議類別"""
        query_lower = user_query.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            category_scores[category] = score
        
        # 按分數排序，返回前兩個建議類別
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, score in sorted_categories[:2] if score > 0]
    
    def add_faq_item(self, keywords: List[str], category: str, response_template: str, 
                     confidence_threshold: float = 0.7, priority: int = 1) -> bool:
        """添加 FAQ 項目"""
        try:
            new_faq = FAQItem(
                keywords=keywords,
                category=category,
                response_template=response_template,
                confidence_threshold=confidence_threshold,
                priority=priority
            )
            self.faq_database.append(new_faq)
            logger.info(f"成功添加 FAQ 項目: {response_template}")
            return True
        except Exception as e:
            logger.error(f"添加 FAQ 項目失敗: {e}")
            return False
    
    def get_faq_statistics(self) -> Dict[str, Any]:
        """獲取 FAQ 統計資訊"""
        category_counts = {}
        for faq in self.faq_database:
            category = faq.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_faq_items": len(self.faq_database),
            "category_distribution": category_counts,
            "categories": list(set(faq.category for faq in self.faq_database))
        }


# 全域 FAQ Fallback 服務實例
_faq_fallback_service: Optional[FAQFallbackService] = None


def get_faq_fallback_service() -> FAQFallbackService:
    """獲取全域 FAQ Fallback 服務實例"""
    global _faq_fallback_service
    if _faq_fallback_service is None:
        _faq_fallback_service = FAQFallbackService()
    return _faq_fallback_service


def get_fallback_reply(user_query: str) -> FallbackResult:
    """便捷的 fallback 回覆函數"""
    service = get_faq_fallback_service()
    return service.get_fallback_reply(user_query)


# 測試函數
def test_faq_fallback():
    """測試 FAQ fallback 功能"""
    service = FAQFallbackService()
    
    test_queries = [
        "我想聽投資理財的 Podcast",
        "推薦一些自我成長的節目",
        "通勤時間有什麼推薦？",
        "睡前想聽放鬆的內容",
        "我想學習英文",
        "無聊想聽點什麼",
        "這是什麼亂七八糟的問題"
    ]
    
    print("=== FAQ Fallback 測試 ===")
    for query in test_queries:
        result = service.get_fallback_reply(query)
        print(f"\n查詢: {query}")
        print(f"回覆: {result.content}")
        print(f"信心度: {result.confidence}")
        print(f"來源: {result.source}")


if __name__ == "__main__":
    test_faq_fallback() 