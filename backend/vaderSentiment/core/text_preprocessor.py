#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本預處理器

負責文本清理、分詞、停用詞過濾等功能
"""

import re
from typing import List, Set
import jieba


class TextPreprocessor:
    """文本預處理器"""
    
    def __init__(self):
        """初始化停用詞集合 - 只包含真正的中性詞彙"""
        self.stop_words = {
            # 基礎語法詞彙
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '自己', '這', '那', '他', '她', '它', '我們', '你們', '他們', '她們', '它們', '這個', '那個', '這些', '那些',
            
            # 疑問詞和指示詞
            '什麼', '怎麼', '為什麼', '哪裡', '什麼時候', '誰', '多少', '幾個', '一些', '很多', '少', '大', '小', '高', '低', '長', '短', '新', '舊', '快', '慢', '早', '晚', '多', '少', '對', '錯', '真', '假',
            
            # 時間詞彙
            '現在', '過去', '未來', '今天', '昨天', '明天', '早上', '中午', '晚上', '凌晨', '深夜', '春天', '夏天', '秋天', '冬天', '一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月', '週一', '週二', '週三', '週四', '週五', '週六', '週日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日',
            
            # 空間位置詞彙
            '上面', '下面', '左邊', '右邊', '前面', '後面', '裡面', '外面', '中間', '旁邊', '附近', '遠處', '這裡', '那裡', '北方', '南方', '東方', '西方', '城市', '鄉村', '國際', '國內', '全球', '本地'
        }
    
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理後的文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        # 移除特殊字符，保留中文、英文、數字和空格
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
        
        # 移除多餘空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        中文分詞
        
        Args:
            text: 清理後的文本
            
        Returns:
            分詞結果列表
        """
        if not text:
            return []
        
        # 使用 jieba 進行分詞
        tokens = jieba.lcut(text)
        
        # 過濾停用詞和單字符
        tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 1
        ]
        
        return tokens
    
    def get_stop_words(self) -> Set[str]:
        """獲取停用詞集合"""
        return self.stop_words.copy()
    
    def add_stop_words(self, words: List[str]) -> None:
        """添加停用詞"""
        self.stop_words.update(words)
    
    def remove_stop_words(self, words: List[str]) -> None:
        """移除停用詞"""
        self.stop_words.difference_update(words) 