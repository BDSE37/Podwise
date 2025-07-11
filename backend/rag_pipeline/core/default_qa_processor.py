#!/usr/bin/env python3
"""
預設問答處理器

載入 default_QA.csv 並提供問答匹配功能：
- 載入預設問答資料
- 提供語意匹配功能
- 支援關鍵字匹配
- 回傳格式化的答案

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 1.0.0
"""

import os
import csv
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class DefaultQA:
    """預設問答資料結構"""
    category: str
    question: str
    tags: str
    answer: str


class DefaultQAProcessor:
    """預設問答處理器"""
    
    def __init__(self, csv_path: str = "scripts/default_QA.csv"):
        """
        初始化預設問答處理器
        
        Args:
            csv_path: default_QA.csv 檔案路徑
        """
        self.csv_path = csv_path
        self.qa_data: List[DefaultQA] = []
        self._load_qa_data()
        logger.info(f"✅ 預設問答處理器初始化完成，載入 {len(self.qa_data)} 筆資料")
    
    def _load_qa_data(self) -> None:
        """載入預設問答資料"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"預設問答檔案不存在: {self.csv_path}")
                return
            
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('類別') and row.get('問題'):
                        qa = DefaultQA(
                            category=row['類別'].strip(),
                            question=row['問題'].strip(),
                            tags=row.get('Mapping到的tag', '').strip(),
                            answer=row.get('答案', '').strip()
                        )
                        self.qa_data.append(qa)
            
            logger.info(f"成功載入 {len(self.qa_data)} 筆預設問答")
            
        except Exception as e:
            logger.error(f"載入預設問答資料失敗: {e}")
            self.qa_data = []
    
    def find_best_match(self, user_query: str, confidence_threshold: float = 0.6) -> Optional[Tuple[DefaultQA, float]]:
        """
        尋找最佳匹配的預設問答
        
        Args:
            user_query: 用戶查詢
            confidence_threshold: 信心度閾值
            
        Returns:
            Tuple[DefaultQA, float]: 匹配的問答和信心度，如果沒有匹配則返回 None
        """
        if not self.qa_data:
            return None
        
        best_match: Optional[DefaultQA] = None
        best_confidence = 0.0
        
        # 預處理用戶查詢
        processed_query = self._preprocess_query(user_query)
        
        for qa in self.qa_data:
            confidence = self._calculate_similarity(processed_query, qa)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = qa
        
        # 檢查是否達到閾值
        if best_confidence >= confidence_threshold and best_match is not None:
            logger.info(f"找到預設問答匹配: {best_match.question[:50]}... (信心度: {best_confidence:.2f})")
            return best_match, best_confidence
        
        logger.info(f"未找到符合閾值的預設問答 (最高信心度: {best_confidence:.2f})")
        return None
    
    def _preprocess_query(self, query: str) -> str:
        """預處理查詢文字"""
        # 移除多餘空白
        query = re.sub(r'\s+', ' ', query.strip())
        # 轉換為小寫
        query = query.lower()
        return query
    
    def _calculate_similarity(self, user_query: str, qa: DefaultQA) -> float:
        """
        計算查詢與預設問答的相似度
        
        Args:
            user_query: 預處理後的用戶查詢
            qa: 預設問答
            
        Returns:
            float: 相似度分數 (0.0 - 1.0)
        """
        # 預處理預設問答
        qa_question = self._preprocess_query(qa.question)
        qa_tags = self._preprocess_query(qa.tags) if qa.tags else ""
        
        # 1. 關鍵字匹配
        keyword_score = self._keyword_similarity(user_query, qa_question, qa_tags)
        
        # 2. 語意相似度（基於詞彙重疊）
        semantic_score = self._semantic_similarity(user_query, qa_question)
        
        # 3. 標籤匹配
        tag_score = self._tag_similarity(user_query, qa_tags)
        
        # 綜合評分
        final_score = (keyword_score * 0.5 + semantic_score * 0.3 + tag_score * 0.2)
        
        return min(final_score, 1.0)
    
    def _keyword_similarity(self, user_query: str, qa_question: str, qa_tags: str) -> float:
        """關鍵字相似度計算"""
        # 提取關鍵字（移除常見停用詞）
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這'}
        
        user_words = set(word for word in user_query.split() if word not in stop_words and len(word) > 1)
        qa_words = set(word for word in qa_question.split() if word not in stop_words and len(word) > 1)
        tag_words = set(word for word in qa_tags.split() if word not in stop_words and len(word) > 1)
        
        all_qa_words = qa_words.union(tag_words)
        
        if not user_words or not all_qa_words:
            return 0.0
        
        # 計算 Jaccard 相似度
        intersection = len(user_words.intersection(all_qa_words))
        union = len(user_words.union(all_qa_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _semantic_similarity(self, user_query: str, qa_question: str) -> float:
        """語意相似度計算（基於詞彙重疊）"""
        user_words = set(user_query.split())
        qa_words = set(qa_question.split())
        
        if not user_words or not qa_words:
            return 0.0
        
        # 計算詞彙重疊率
        common_words = user_words.intersection(qa_words)
        total_words = user_words.union(qa_words)
        
        return len(common_words) / len(total_words) if total_words else 0.0
    
    def _tag_similarity(self, user_query: str, qa_tags: str) -> float:
        """標籤相似度計算"""
        if not qa_tags:
            return 0.0
        
        tag_words = set(qa_tags.split())
        user_words = set(user_query.split())
        
        if not tag_words:
            return 0.0
        
        # 計算標籤匹配率
        matched_tags = user_words.intersection(tag_words)
        return len(matched_tags) / len(tag_words)
    
    def get_answer_by_category(self, category: str) -> List[DefaultQA]:
        """根據類別獲取問答"""
        return [qa for qa in self.qa_data if qa.category == category]
    
    def get_all_categories(self) -> List[str]:
        """獲取所有類別"""
        return list(set(qa.category for qa in self.qa_data))
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        categories: Dict[str, int] = {}
        for qa in self.qa_data:
            categories[qa.category] = categories.get(qa.category, 0) + 1
        
        return {
            "total_qa": len(self.qa_data),
            "categories": categories
        }


def create_default_qa_processor(csv_path: str = "scripts/default_QA.csv") -> DefaultQAProcessor:
    """創建預設問答處理器實例"""
    return DefaultQAProcessor(csv_path) 