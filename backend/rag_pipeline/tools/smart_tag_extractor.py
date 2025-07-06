#!/usr/bin/env python3
"""
智能 TAG 提取工具

此模組實現智能 TAG 提取功能，當查詢中的詞彙不在現有標籤表時，
使用 Word2Vec + Transformer 進行智能標籤提取。

主要功能：
- 基礎 TAG 提取（現有邏輯）
- Word2Vec 語義相似度計算
- Transformer 語義理解
- 智能標籤映射

作者: Podwise Team
版本: 1.0.0
"""

import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import pickle
from datetime import datetime

# 機器學習相關導入
try:
    from gensim.models import Word2Vec
    from sklearn.metrics.pairwise import cosine_similarity
    from transformers import AutoTokenizer, AutoModel
    import torch
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("機器學習套件未安裝，將使用基礎 TAG 提取")

logger = logging.getLogger(__name__)


@dataclass
class TagMapping:
    """標籤映射結果"""
    original_tag: str
    mapped_tags: List[str]
    confidence: float
    method: str  # "exact", "word2vec", "transformer"


@dataclass
class SmartTagResult:
    """智能標籤提取結果"""
    extracted_tags: List[str]
    mapped_tags: List[TagMapping]
    confidence: float
    processing_time: float
    method_used: List[str]


class SmartTagExtractor:
    """智能標籤提取器"""
    
    def __init__(self, 
                 existing_tags_file: Optional[str] = None,
                 word2vec_model_path: Optional[str] = None,
                 transformer_model_name: str = "bert-base-chinese",
                 similarity_threshold: float = 0.7):
        """
        初始化智能標籤提取器
        
        Args:
            existing_tags_file: 現有標籤檔案路徑
            word2vec_model_path: Word2Vec 模型路徑
            transformer_model_name: Transformer 模型名稱
            similarity_threshold: 相似度閾值
        """
        self.existing_tags: Set[str] = set()
        self.word2vec_model = None
        self.transformer_tokenizer = None
        self.transformer_model = None
        self.similarity_threshold = similarity_threshold
        
        # 載入現有標籤
        if existing_tags_file:
            self.load_existing_tags(existing_tags_file)
        else:
            self.load_default_tags()
        
        # 初始化機器學習模型
        if ML_AVAILABLE:
            self._initialize_ml_models(word2vec_model_path, transformer_model_name)
        else:
            logger.warning("機器學習套件不可用，將使用基礎 TAG 提取")
    
    def load_existing_tags(self, tags_file: str) -> None:
        """
        載入現有標籤
        
        Args:
            tags_file: 標籤檔案路徑
        """
        try:
            file_path = Path(tags_file)
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.existing_tags = set(data)
                    elif isinstance(data, dict):
                        # 如果是字典格式，提取所有標籤
                        all_tags = []
                        for category, tags in data.items():
                            if isinstance(tags, list):
                                all_tags.extend(tags)
                            elif isinstance(tags, dict) and 'tags' in tags:
                                all_tags.extend(tags['tags'])
                        self.existing_tags = set(all_tags)
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.existing_tags = set(line.strip() for line in f if line.strip())
            else:
                logger.warning(f"不支援的檔案格式: {file_path.suffix}")
                self.load_default_tags()
                
            logger.info(f"載入 {len(self.existing_tags)} 個現有標籤")
            
        except Exception as e:
            logger.error(f"載入標籤檔案失敗: {str(e)}")
            self.load_default_tags()
    
    def load_default_tags(self) -> None:
        """載入預設標籤"""
        self.existing_tags = {
            # 商業相關
            "股票", "投資", "理財", "財經", "基金", "期貨", "外匯", "房地產",
            "創業", "企業", "管理", "策略", "市場", "行銷", "銷售", "客戶",
            "財務", "會計", "稅務", "保險", "銀行", "信貸", "融資", "併購",
            
            # 科技相關
            "AI", "人工智慧", "機器學習", "深度學習", "大數據", "雲端",
            "區塊鏈", "加密貨幣", "比特幣", "以太坊", "NFT", "元宇宙",
            "5G", "物聯網", "智慧手機", "電動車", "自駕車", "無人機",
            "VR", "AR", "MR", "量子計算", "晶片", "半導體", "台積電",
            
            # 教育相關
            "學習", "教育", "培訓", "課程", "學校", "大學", "研究所",
            "技能", "證照", "考試", "讀書", "知識", "研究", "論文",
            "語言", "英文", "日文", "韓文", "法文", "德文", "西班牙文",
            
            # 職涯相關
            "職涯", "工作", "職場", "求職", "面試", "履歷", "薪資",
            "升遷", "轉職", "創業", "自由工作者", "遠端工作", "兼職",
            "領導力", "溝通", "團隊合作", "時間管理", "效率", "生產力",
            
            # 生活相關
            "健康", "運動", "飲食", "減肥", "健身", "瑜珈", "跑步",
            "旅遊", "美食", "烹飪", "攝影", "音樂", "電影", "書籍",
            "心理", "情緒", "壓力", "睡眠", "冥想", "正念", "快樂",
            
            # 時事相關
            "政治", "經濟", "社會", "環境", "氣候", "疫情", "疫苗",
            "國際", "外交", "貿易", "戰爭", "和平", "人權", "平等",
            "台灣", "中國", "美國", "日本", "韓國", "歐洲", "東南亞"
        }
        logger.info(f"載入 {len(self.existing_tags)} 個預設標籤")
    
    def _initialize_ml_models(self, word2vec_model_path: Optional[str], transformer_model_name: str) -> None:
        """
        初始化機器學習模型
        
        Args:
            word2vec_model_path: Word2Vec 模型路徑
            transformer_model_name: Transformer 模型名稱
        """
        # 初始化 Word2Vec 模型
        if word2vec_model_path and Path(word2vec_model_path).exists():
            try:
                self.word2vec_model = Word2Vec.load(word2vec_model_path)
                logger.info(f"載入 Word2Vec 模型: {word2vec_model_path}")
            except Exception as e:
                logger.error(f"載入 Word2Vec 模型失敗: {str(e)}")
                self.word2vec_model = None
        
        # 初始化 Transformer 模型
        try:
            self.transformer_tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
            self.transformer_model = AutoModel.from_pretrained(transformer_model_name)
            if torch.cuda.is_available():
                self.transformer_model = self.transformer_model.cuda()
            logger.info(f"載入 Transformer 模型: {transformer_model_name}")
        except Exception as e:
            logger.error(f"載入 Transformer 模型失敗: {str(e)}")
            self.transformer_tokenizer = None
            self.transformer_model = None
    
    def extract_basic_tags(self, query: str) -> List[str]:
        """
        基礎 TAG 提取（現有邏輯）
        
        Args:
            query: 用戶查詢
            
        Returns:
            List[str]: 提取的 TAG 列表
        """
        tags = []
        
        # 提取大寫字母組成的詞彙
        uppercase_tags = re.findall(r'\b[A-Z][A-Z0-9]*\b', query)
        tags.extend(uppercase_tags)
        
        # 提取引號內的內容
        quoted_tags = re.findall(r'"([^"]*)"', query)
        tags.extend(quoted_tags)
        
        # 提取中文詞彙（簡單規則）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        # 過濾掉常見的停用詞
        stop_words = {'我想', '了解', '推薦', '關於', '相關', '節目', 'Podcast', '聽聽', '請'}
        chinese_tags = [word for word in chinese_words if word not in stop_words and len(word) >= 2]
        tags.extend(chinese_tags[:5])  # 限制數量
        
        # 去重並過濾空字串
        unique_tags = list(set([tag.strip() for tag in tags if tag.strip()]))
        
        return unique_tags
    
    def find_missing_tags(self, extracted_tags: List[str]) -> List[str]:
        """
        找出不在現有標籤表中的 TAG
        
        Args:
            extracted_tags: 提取的 TAG 列表
            
        Returns:
            List[str]: 缺失的 TAG 列表
        """
        return [tag for tag in extracted_tags if tag not in self.existing_tags]
    
    def word2vec_similarity(self, query_tag: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        使用 Word2Vec 計算語義相似度
        
        Args:
            query_tag: 查詢標籤
            top_k: 返回前 k 個相似標籤
            
        Returns:
            List[Tuple[str, float]]: (標籤, 相似度) 列表
        """
        if not self.word2vec_model or query_tag not in self.word2vec_model.wv:
            return []
        
        try:
            # 計算與所有現有標籤的相似度
            similarities = []
            for tag in self.existing_tags:
                if tag in self.word2vec_model.wv:
                    similarity = self.word2vec_model.wv.similarity(query_tag, tag)
                    similarities.append((tag, similarity))
            
            # 排序並返回前 k 個
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Word2Vec 相似度計算失敗: {str(e)}")
            return []
    
    def transformer_similarity(self, query_tag: str, context: str = "", top_k: int = 5) -> List[Tuple[str, float]]:
        """
        使用 Transformer 計算語義相似度
        
        Args:
            query_tag: 查詢標籤
            context: 上下文（可選）
            top_k: 返回前 k 個相似標籤
            
        Returns:
            List[Tuple[str, float]]: (標籤, 相似度) 列表
        """
        if not self.transformer_model or not self.transformer_tokenizer:
            return []
        
        try:
            # 準備輸入文本
            input_text = f"{context} {query_tag}" if context else query_tag
            
            # 編碼輸入
            inputs = self.transformer_tokenizer(
                input_text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            
            # 移動到 GPU（如果可用）
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 獲取嵌入向量
            with torch.no_grad():
                outputs = self.transformer_model(**inputs)
                query_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            
            # 計算與現有標籤的相似度
            similarities = []
            for tag in self.existing_tags:
                tag_inputs = self.transformer_tokenizer(
                    tag, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True, 
                    max_length=64
                )
                
                if torch.cuda.is_available():
                    tag_inputs = {k: v.cuda() for k, v in tag_inputs.items()}
                
                with torch.no_grad():
                    tag_outputs = self.transformer_model(**tag_inputs)
                    tag_embedding = tag_outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                
                # 計算餘弦相似度
                similarity = cosine_similarity(query_embedding, tag_embedding)[0][0]
                similarities.append((tag, similarity))
            
            # 排序並返回前 k 個
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Transformer 相似度計算失敗: {str(e)}")
            return []
    
    def smart_tag_mapping(self, missing_tags: List[str], context: str = "") -> List[TagMapping]:
        """
        智能標籤映射
        
        Args:
            missing_tags: 缺失的標籤列表
            context: 上下文（可選）
            
        Returns:
            List[TagMapping]: 標籤映射結果列表
        """
        mappings = []
        
        for tag in missing_tags:
            mapped_tags = []
            confidence = 0.0
            method = "exact"
            
            # 嘗試 Word2Vec 映射
            if self.word2vec_model:
                word2vec_results = self.word2vec_similarity(tag)
                if word2vec_results:
                    best_match, similarity = word2vec_results[0]
                    if similarity >= self.similarity_threshold:
                        mapped_tags.append(best_match)
                        confidence = similarity
                        method = "word2vec"
            
            # 嘗試 Transformer 映射
            if self.transformer_model and not mapped_tags:
                transformer_results = self.transformer_similarity(tag, context)
                if transformer_results:
                    best_match, similarity = transformer_results[0]
                    if similarity >= self.similarity_threshold:
                        mapped_tags.append(best_match)
                        confidence = similarity
                        method = "transformer"
            
            # 如果都沒有找到，使用模糊匹配
            if not mapped_tags:
                fuzzy_matches = self.fuzzy_match(tag)
                if fuzzy_matches:
                    mapped_tags = fuzzy_matches[:3]  # 最多3個
                    confidence = 0.6
                    method = "fuzzy"
            
            if mapped_tags:
                mappings.append(TagMapping(
                    original_tag=tag,
                    mapped_tags=mapped_tags,
                    confidence=confidence,
                    method=method
                ))
        
        return mappings
    
    def fuzzy_match(self, query_tag: str) -> List[str]:
        """
        模糊匹配
        
        Args:
            query_tag: 查詢標籤
            
        Returns:
            List[str]: 匹配的標籤列表
        """
        matches = []
        query_lower = query_tag.lower()
        
        for tag in self.existing_tags:
            tag_lower = tag.lower()
            
            # 包含關係
            if query_lower in tag_lower or tag_lower in query_lower:
                matches.append(tag)
            # 字符相似度
            elif self._calculate_char_similarity(query_lower, tag_lower) > 0.7:
                matches.append(tag)
        
        return matches
    
    def _calculate_char_similarity(self, str1: str, str2: str) -> float:
        """計算字符相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 使用編輯距離計算相似度
        len1, len2 = len(str1), len(str2)
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # 刪除
                        matrix[i][j-1] + 1,    # 插入
                        matrix[i-1][j-1] + 1   # 替換
                    )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def extract_smart_tags(self, query: str, context: str = "") -> SmartTagResult:
        """
        智能 TAG 提取主函數
        
        Args:
            query: 用戶查詢
            context: 上下文（可選）
            
        Returns:
            SmartTagResult: 智能標籤提取結果
        """
        start_time = datetime.now()
        
        # 1. 基礎 TAG 提取
        basic_tags = self.extract_basic_tags(query)
        logger.info(f"基礎 TAG 提取: {basic_tags}")
        
        # 2. 找出缺失的 TAG
        missing_tags = self.find_missing_tags(basic_tags)
        logger.info(f"缺失的 TAG: {missing_tags}")
        
        # 3. 智能映射
        mappings = []
        methods_used = ["basic"]
        
        if missing_tags and ML_AVAILABLE:
            mappings = self.smart_tag_mapping(missing_tags, context)
            methods_used.extend([m.method for m in mappings])
            logger.info(f"智能映射結果: {len(mappings)} 個映射")
        
        # 4. 組合最終結果
        final_tags = basic_tags.copy()
        for mapping in mappings:
            if mapping.confidence >= self.similarity_threshold:
                final_tags.extend(mapping.mapped_tags)
        
        # 去重
        final_tags = list(set(final_tags))
        
        # 計算整體信心度
        if mappings:
            avg_confidence = sum(m.confidence for m in mappings) / len(mappings)
        else:
            avg_confidence = 1.0 if basic_tags else 0.0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = SmartTagResult(
            extracted_tags=final_tags,
            mapped_tags=mappings,
            confidence=avg_confidence,
            processing_time=processing_time,
            method_used=methods_used
        )
        
        logger.info(f"智能 TAG 提取完成: {final_tags}, 信心度: {avg_confidence:.2f}")
        return result


def test_smart_tag_extractor():
    """測試智能標籤提取器"""
    # 初始化提取器
    extractor = SmartTagExtractor()
    
    # 測試查詢
    test_queries = [
        "我想了解 NVIDIA 的投資機會",
        "請推薦關於 '機器學習' 的 Podcast",
        "我想聽聽關於 TSMC 的分析",
        "請推薦職涯發展相關的節目",
        "我想了解區塊鏈和加密貨幣",
        "請推薦關於人工智慧和深度學習的內容"
    ]
    
    print("=== 智能 TAG 提取測試 ===")
    
    for query in test_queries:
        print(f"\n查詢: {query}")
        result = extractor.extract_smart_tags(query)
        
        print(f"提取的 TAG: {result.extracted_tags}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"使用的方法: {result.method_used}")
        print(f"處理時間: {result.processing_time:.3f}秒")
        
        if result.mapped_tags:
            print("映射結果:")
            for mapping in result.mapped_tags:
                print(f"  {mapping.original_tag} -> {mapping.mapped_tags} (信心度: {mapping.confidence:.2f}, 方法: {mapping.method})")


if __name__ == "__main__":
    test_smart_tag_extractor() 