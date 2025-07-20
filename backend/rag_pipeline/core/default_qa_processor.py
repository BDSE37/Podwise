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
# 新增 jieba 分詞支援
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

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
    
    def __init__(self, csv_path: str = "scripts/csv/default_QA.csv"):
        """
        初始化預設問答處理器
        
        Args:
            csv_path: default_QA.csv 檔案路徑
        """
        self.csv_path = csv_path
        self.qa_data: List[DefaultQA] = []
        self.tags_mapping: Dict[str, List[str]] = {}
        self._load_qa_data()
        self._load_tags_mapping()
        logger.info(f"✅ 預設問答處理器初始化完成，載入 {len(self.qa_data)} 筆資料")
    
    def _load_qa_data(self) -> None:
        """載入預設問答資料"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"預設問答檔案不存在: {self.csv_path}")
                return
            
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # 跳過第一行空行
                next(file, None)
                
                # 手動設定欄位名稱
                fieldnames = ['提問人', '類別', '問題', 'Mapping到的tag', '答案', '修改方向', '', '']
                reader = csv.DictReader(file, fieldnames=fieldnames)
                
                for row in reader:
                    # 檢查是否有有效的問題和類別
                    question = row.get('問題', '').strip()
                    category = row.get('類別', '').strip()
                    
                    if question and category and question != '問題 (keywords請幫我標紅字)':
                        qa = DefaultQA(
                            category=category,
                            question=question,
                            tags=row.get('Mapping到的tag', '').strip(),
                            answer=row.get('答案', '').strip()
                        )
                        self.qa_data.append(qa)
            
            logger.info(f"成功載入 {len(self.qa_data)} 筆預設問答")
            
        except Exception as e:
            logger.error(f"載入預設問答資料失敗: {e}")
            self.qa_data = []
    
    def _load_tags_mapping(self) -> None:
        """載入 tags_info.csv 的關鍵字映射"""
        try:
            tags_path = "scripts/csv/tags_info.csv"
            if not os.path.exists(tags_path):
                logger.warning(f"tags_info.csv 檔案不存在: {tags_path}")
                return
            
            with open(tags_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    tag = row.get('TAG', '').strip()
                    if tag:
                        # 收集所有非空的同義詞
                        synonyms = []
                        for i in range(1, 15):  # sync1 到 sync14
                            sync_key = f'sync{i}'
                            synonym = row.get(sync_key, '').strip()
                            if synonym:
                                synonyms.append(synonym)
                        
                        if synonyms:
                            self.tags_mapping[tag] = synonyms
            
            logger.info(f"成功載入 {len(self.tags_mapping)} 個 TAG 映射")
            
        except Exception as e:
            logger.error(f"載入 tags_info.csv 失敗: {e}")
            self.tags_mapping = {}
    
    def find_best_match(self, user_query: str, confidence_threshold: float = 0.4) -> Optional[Tuple[DefaultQA, float]]:
        """
        尋找最佳匹配的預設問答
        
        Args:
            user_query: 用戶查詢
            confidence_threshold: 信心度閾值 (降低到 0.4 以提高匹配率)
            
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
            
            # 調試信息：檢查包含「商業」關鍵字的問答
            if '商業' in qa.question and confidence > 0:
                logger.info(f"商業相關問答: '{qa.question}' -> 信心度: {confidence:.3f}")
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = qa
        
        # 檢查是否達到閾值
        if best_confidence >= confidence_threshold and best_match is not None:
            logger.info(f"找到預設問答匹配: {best_match.question[:50]}... (信心度: {best_confidence:.2f})")
            return best_match, best_confidence
        
        logger.info(f"未找到符合閾值的預設問答 (最高信心度: {best_confidence:.2f})")
        logger.info(f"查詢: '{user_query}', 閾值: {confidence_threshold}")
        if best_match:
            logger.info(f"最佳匹配問題: '{best_match.question}'")
        return None
    
    def _preprocess_query(self, query: str) -> list:
        """預處理查詢文字並分詞"""
        query = re.sub(r'\s+', ' ', query.strip()).lower()
        if JIEBA_AVAILABLE:
            return [w for w in jieba.lcut(query) if w.strip()]
        else:
            return [w for w in query.split() if w.strip()]
    
    def _calculate_similarity(self, user_words: list, qa: DefaultQA) -> float:
        """
        計算查詢與預設問答的相似度（優化版，支援分詞）
        """
        # 分詞處理
        qa_question_words = self._preprocess_query(qa.question)
        qa_tags_words = self._preprocess_query(qa.tags) if qa.tags else []

        # 特殊處理：NVIDIA 相關查詢
        user_query_text = ' '.join(user_words).lower()
        qa_question_text = qa.question.lower()
        
        # 檢查是否為 NVIDIA 相關查詢 (修正關鍵字列表)
        nvidia_keywords = ['nvidia', 'nvidia', 'nvidia', 'nvidia', 'nvidia']
        if any(keyword in user_query_text for keyword in nvidia_keywords) and 'nvidia' in qa_question_text:
            logger.info(f"NVIDIA 相關查詢匹配: 用戶='{user_query_text}', 預設問答='{qa_question_text}'")
            return 0.95  # 高信心度匹配

        # 1. 標籤匹配（提高權重）
        tag_score = self._tag_similarity(user_words, qa_tags_words)
        # 2. 關鍵字匹配
        keyword_score = self._keyword_similarity(user_words, qa_question_words, qa_tags_words)
        # 3. 語意相似度（基於詞彙重疊）
        semantic_score = self._semantic_similarity(user_words, qa_question_words)
        # 4. 模糊匹配（新增）
        fuzzy_score = self._fuzzy_similarity(user_words, qa_question_words, qa_tags_words)

        if tag_score >= 0.8:
            return 1.0
        final_score = (tag_score * 0.6 + keyword_score * 0.2 + semantic_score * 0.1 + fuzzy_score * 0.1)
        return min(final_score, 1.0)
    
    def _keyword_similarity(self, user_words: list, qa_question_words: list, qa_tags_words: list) -> float:
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這'}
        user_set = set(w for w in user_words if w not in stop_words and len(w) > 1)
        qa_set = set(w for w in qa_question_words if w not in stop_words and len(w) > 1)
        tag_set = set(w for w in qa_tags_words if w not in stop_words and len(w) > 1)
        all_qa_words = qa_set.union(tag_set)
        if not user_set or not all_qa_words:
            return 0.0
        intersection = len(user_set.intersection(all_qa_words))
        union = len(user_set.union(all_qa_words))
        return intersection / union if union > 0 else 0.0
    
    def _semantic_similarity(self, user_words: list, qa_question_words: list) -> float:
        user_set = set(user_words)
        qa_set = set(qa_question_words)
        if not user_set or not qa_set:
            return 0.0
        common_words = user_set.intersection(qa_set)
        total_words = user_set.union(qa_set)
        return len(common_words) / len(total_words) if total_words else 0.0
    
    def _tag_similarity(self, user_words: list, qa_tags_words: list) -> float:
        if not qa_tags_words:
            return 0.0
        user_set = set(user_words)
        total_matches = 0
        total_possible_matches = len(qa_tags_words)
        for tag in qa_tags_words:
            tag = tag.strip()
            if not tag:
                continue
            if tag in user_set:
                total_matches += 1
                continue
            if tag in self.tags_mapping:
                synonyms = self.tags_mapping[tag]
                for synonym in synonyms:
                    if synonym in user_set:
                        total_matches += 1
                        break
            for user_word in user_set:
                if len(user_word) > 2 and len(tag) > 2:
                    if user_word in tag or tag in user_word:
                        total_matches += 0.5
                        break
        return total_matches / total_possible_matches if total_possible_matches > 0 else 0.0
    
    def _fuzzy_similarity(self, user_words: list, qa_question_words: list, qa_tags_words: list) -> float:
        try:
            def char_similarity(str1: str, str2: str) -> float:
                if not str1 or not str2:
                    return 0.0
                common_chars = set(str1) & set(str2)
                total_chars = set(str1) | set(str2)
                if not total_chars:
                    return 0.0
                return len(common_chars) / len(total_chars)
            question_fuzzy = max([char_similarity(''.join(user_words), ''.join(qa_question_words))], default=0.0)
            tag_fuzzy = max([char_similarity(''.join(user_words), ''.join(qa_tags_words))], default=0.0) if qa_tags_words else 0.0
            return max(question_fuzzy, tag_fuzzy)
        except Exception as e:
            logger.warning(f"模糊相似度計算失敗: {e}")
            return 0.0
    
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


def create_default_qa_processor(csv_path: str = "scripts/csv/default_QA.csv") -> DefaultQAProcessor:
    """創建預設問答處理器實例"""
    return DefaultQAProcessor(csv_path) 