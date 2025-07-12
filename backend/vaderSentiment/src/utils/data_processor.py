#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據處理工具類別

提供數據清理、轉換、驗證等功能

作者: Podwise Team
版本: 2.0.0
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    數據處理器
    
    提供數據清理、轉換、驗證等功能
    """
    
    def __init__(self):
        """初始化數據處理器"""
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """設定日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理後的文本
        """
        if not text:
            return ""
            
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符，保留中文、英文、數字和基本標點
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】]', '', text)
        
        return text.strip()
        
    def extract_words(self, text: str) -> List[str]:
        """
        提取詞彙
        
        Args:
            text: 文本
            
        Returns:
            List[str]: 詞彙列表
        """
        if not text:
            return []
            
        # 分割詞彙（中文按字符，英文按單詞）
        words = re.findall(r'[\u4e00-\u9fff]+|\w+', text)
        return [word for word in words if len(word) > 0]
        
    def load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        載入 JSON 檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            Dict[str, Any]: JSON 數據
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"載入 JSON 檔案失敗 {file_path}: {e}")
            return {}
            
    def save_json_file(self, data: Dict[str, Any], file_path: Path) -> bool:
        """
        儲存 JSON 檔案
        
        Args:
            data: 要儲存的數據
            file_path: 檔案路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"儲存 JSON 檔案失敗 {file_path}: {e}")
            return False
            
    def validate_podcast_data(self, data: Dict[str, Any]) -> bool:
        """
        驗證 podcast 數據格式
        
        Args:
            data: podcast 數據
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['title', 'rating', 'comment_count', 'comments']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"缺少必要欄位: {field}")
                return False
                
        # 驗證數據類型
        if not isinstance(data.get('title'), str):
            logger.warning("title 必須是字串")
            return False
            
        if not isinstance(data.get('rating'), (int, float)):
            logger.warning("rating 必須是數字")
            return False
            
        if not isinstance(data.get('comment_count'), int):
            logger.warning("comment_count 必須是整數")
            return False
            
        if not isinstance(data.get('comments'), list):
            logger.warning("comments 必須是列表")
            return False
            
        return True
        
    def analyze_word_frequency(self, texts: List[str]) -> Dict[str, int]:
        """
        分析詞彙頻率
        
        Args:
            texts: 文本列表
            
        Returns:
            Dict[str, int]: 詞彙頻率字典
        """
        word_counter = Counter()
        
        for text in texts:
            words = self.extract_words(text)
            word_counter.update(words)
            
        return dict(word_counter)
        
    def filter_comments_by_length(self, comments: List[str], 
                                 min_length: int = 10, 
                                 max_length: int = 1000) -> List[str]:
        """
        根據長度過濾評論
        
        Args:
            comments: 評論列表
            min_length: 最小長度
            max_length: 最大長度
            
        Returns:
            List[str]: 過濾後的評論列表
        """
        filtered_comments = []
        
        for comment in comments:
            if min_length <= len(comment) <= max_length:
                filtered_comments.append(comment)
                
        return filtered_comments
        
    def remove_duplicate_comments(self, comments: List[str]) -> List[str]:
        """
        移除重複評論
        
        Args:
            comments: 評論列表
            
        Returns:
            List[str]: 去重後的評論列表
        """
        seen = set()
        unique_comments = []
        
        for comment in comments:
            cleaned_comment = self.clean_text(comment)
            if cleaned_comment and cleaned_comment not in seen:
                seen.add(cleaned_comment)
                unique_comments.append(comment)
                
        return unique_comments
        
    def split_text_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        將文本分割成塊
        
        Args:
            text: 文本
            chunk_size: 塊大小
            
        Returns:
            List[str]: 文本塊列表
        """
        if not text:
            return []
            
        chunks = []
        words = self.extract_words(text)
        
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > chunk_size and current_chunk:
                chunks.append(''.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word)
                
        if current_chunk:
            chunks.append(''.join(current_chunk))
            
        return chunks
        
    def get_data_statistics(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        獲取數據統計資訊
        
        Args:
            data_list: 數據列表
            
        Returns:
            Dict[str, Any]: 統計資訊
        """
        if not data_list:
            return {}
            
        stats = {
            'total_count': len(data_list),
            'fields': {},
            'missing_fields': {}
        }
        
        # 分析欄位
        all_fields = set()
        for item in data_list:
            all_fields.update(item.keys())
            
        for field in all_fields:
            field_values = [item.get(field) for item in data_list]
            non_null_values = [v for v in field_values if v is not None]
            
            stats['fields'][field] = {
                'count': len(non_null_values),
                'missing_count': len(data_list) - len(non_null_values),
                'missing_ratio': (len(data_list) - len(non_null_values)) / len(data_list)
            }
            
        return stats 