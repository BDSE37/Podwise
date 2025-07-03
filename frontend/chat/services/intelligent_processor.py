#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能結果處理器
提供結果過濾、排序、去重和智能快取功能
"""

import re
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """內容類型"""
    PODCAST = "podcast"
    NEWS = "news"
    ARTICLE = "article"
    VIDEO = "video"
    AUDIO = "audio"
    UNKNOWN = "unknown"

class QualityLevel(Enum):
    """質量等級"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ProcessedResult:
    """處理後的結果"""
    title: str
    content: str
    url: Optional[str] = None
    source: str = ""
    content_type: ContentType = ContentType.UNKNOWN
    quality_score: float = 0.0
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    overall_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class IntelligentProcessor:
    """智能結果處理器"""
    
    def __init__(self):
        """初始化處理器"""
        self.cache = {}
        self.cache_ttl = 3600  # 1小時快取
        self.quality_keywords = {
            "podcast": ["節目", "播客", "音頻", "廣播", "訪談", "討論"],
            "business": ["商業", "創業", "投資", "管理", "策略", "市場"],
            "education": ["教育", "學習", "知識", "技能", "成長", "發展"],
            "technology": ["科技", "技術", "創新", "AI", "人工智慧", "數位"]
        }
        
        # 停用詞列表
        self.stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一個", "上", "也", "很", "到", "說", "要", "去", "你", "會", "著", "沒有", "看", "好", "自己", "這"
        }
    
    def process_search_results(self, results: List[Dict[str, Any]], 
                             query: str, max_results: int = 10) -> List[ProcessedResult]:
        """處理搜尋結果"""
        processed_results = []
        
        for result in results:
            processed = self._process_single_result(result, query)
            if processed:
                processed_results.append(processed)
        
        # 去重
        processed_results = self._remove_duplicates(processed_results)
        
        # 排序
        processed_results = self._sort_results(processed_results, query)
        
        # 限制結果數量
        return processed_results[:max_results]
    
    def _process_single_result(self, result: Dict[str, Any], query: str) -> Optional[ProcessedResult]:
        """處理單個結果"""
        try:
            title = result.get("title", "")
            content = result.get("snippet", "") or result.get("content", "")
            url = result.get("link", "") or result.get("url", "")
            source = result.get("source", "unknown")
            
            if not title and not content:
                return None
            
            # 計算各種分數
            quality_score = self._calculate_quality_score(title, content)
            relevance_score = self._calculate_relevance_score(title, content, query)
            freshness_score = self._calculate_freshness_score(result)
            
            # 計算總分
            overall_score = (quality_score * 0.4 + 
                           relevance_score * 0.4 + 
                           freshness_score * 0.2)
            
            # 判斷內容類型
            content_type = self._classify_content(title, content)
            
            return ProcessedResult(
                title=title,
                content=content,
                url=url,
                source=source,
                content_type=content_type,
                quality_score=quality_score,
                relevance_score=relevance_score,
                freshness_score=freshness_score,
                overall_score=overall_score,
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            logger.warning(f"處理結果失敗: {str(e)}")
            return None
    
    def _calculate_quality_score(self, title: str, content: str) -> float:
        """計算質量分數"""
        score = 0.0
        
        # 標題長度檢查
        if 10 <= len(title) <= 100:
            score += 0.2
        elif 5 <= len(title) <= 150:
            score += 0.1
        
        # 內容長度檢查
        if 50 <= len(content) <= 500:
            score += 0.3
        elif 20 <= len(content) <= 1000:
            score += 0.2
        
        # 關鍵詞密度檢查
        keyword_density = self._calculate_keyword_density(title + " " + content)
        score += min(keyword_density * 0.3, 0.3)
        
        # 格式檢查
        if self._has_good_formatting(title, content):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, title: str, content: str, query: str) -> float:
        """計算相關性分數"""
        score = 0.0
        
        # 查詢詞匹配
        query_words = set(re.findall(r'\w+', query.lower()))
        title_words = set(re.findall(r'\w+', title.lower()))
        content_words = set(re.findall(r'\w+', content.lower()))
        
        # 標題匹配
        title_matches = len(query_words.intersection(title_words))
        if title_matches > 0:
            score += min(title_matches / len(query_words), 1.0) * 0.5
        
        # 內容匹配
        content_matches = len(query_words.intersection(content_words))
        if content_matches > 0:
            score += min(content_matches / len(query_words), 1.0) * 0.3
        
        # 語意相似度（簡化版本）
        semantic_score = self._calculate_semantic_similarity(query, title + " " + content)
        score += semantic_score * 0.2
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, result: Dict[str, Any]) -> float:
        """計算新鮮度分數"""
        # 這裡可以根據實際資料結構調整
        # 假設有時間戳或日期資訊
        timestamp = result.get("timestamp") or result.get("date")
        
        if timestamp:
            try:
                # 解析時間戳
                import datetime
                if isinstance(timestamp, str):
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.datetime.fromtimestamp(timestamp)
                
                # 計算時間差（天）
                now = datetime.datetime.now(dt.tzinfo)
                days_diff = (now - dt).days
                
                # 新鮮度分數：越新分數越高
                if days_diff <= 1:
                    return 1.0
                elif days_diff <= 7:
                    return 0.8
                elif days_diff <= 30:
                    return 0.6
                elif days_diff <= 90:
                    return 0.4
                else:
                    return 0.2
                    
            except Exception:
                pass
        
        # 預設分數
        return 0.5
    
    def _calculate_keyword_density(self, text: str) -> float:
        """計算關鍵詞密度"""
        words = re.findall(r'\w+', text.lower())
        if not words:
            return 0.0
        
        # 計算所有關鍵詞的出現次數
        keyword_count = 0
        for category, keywords in self.quality_keywords.items():
            for keyword in keywords:
                keyword_count += text.lower().count(keyword)
        
        return min(keyword_count / len(words), 1.0)
    
    def _has_good_formatting(self, title: str, content: str) -> bool:
        """檢查格式是否良好"""
        # 檢查是否有適當的標點符號
        has_punctuation = bool(re.search(r'[。！？，；：]', title + content))
        
        # 檢查是否有適當的長度
        good_length = 10 <= len(title) <= 200 and 20 <= len(content) <= 2000
        
        # 檢查是否包含數字或特殊符號
        has_special_chars = bool(re.search(r'[0-9a-zA-Z]', title + content))
        
        return has_punctuation and good_length and has_special_chars
    
    def _calculate_semantic_similarity(self, query: str, text: str) -> float:
        """計算語意相似度（簡化版本）"""
        # 這裡可以整合更複雜的語意相似度算法
        # 目前使用簡單的詞彙重疊計算
        
        query_words = set(re.findall(r'\w+', query.lower())) - self.stop_words
        text_words = set(re.findall(r'\w+', text.lower())) - self.stop_words
        
        if not query_words:
            return 0.0
        
        intersection = len(query_words.intersection(text_words))
        union = len(query_words.union(text_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _classify_content(self, title: str, content: str) -> ContentType:
        """分類內容類型"""
        text = (title + " " + content).lower()
        
        # Podcast 相關關鍵詞
        podcast_keywords = ["podcast", "播客", "節目", "音頻", "廣播", "訪談"]
        if any(keyword in text for keyword in podcast_keywords):
            return ContentType.PODCAST
        
        # 新聞相關關鍵詞
        news_keywords = ["新聞", "報導", "最新", "消息", "公告"]
        if any(keyword in text for keyword in news_keywords):
            return ContentType.NEWS
        
        # 文章相關關鍵詞
        article_keywords = ["文章", "專欄", "評論", "分析", "研究"]
        if any(keyword in text for keyword in article_keywords):
            return ContentType.ARTICLE
        
        # 影片相關關鍵詞
        video_keywords = ["影片", "視頻", "直播", "錄製"]
        if any(keyword in text for keyword in video_keywords):
            return ContentType.VIDEO
        
        return ContentType.UNKNOWN
    
    def _remove_duplicates(self, results: List[ProcessedResult]) -> List[ProcessedResult]:
        """去除重複結果"""
        seen_titles = set()
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # 檢查標題相似度
            title_normalized = self._normalize_text(result.title)
            
            # 檢查 URL
            url_normalized = result.url.lower() if result.url else ""
            
            if (title_normalized not in seen_titles and 
                url_normalized not in seen_urls):
                seen_titles.add(title_normalized)
                if url_normalized:
                    seen_urls.add(url_normalized)
                unique_results.append(result)
        
        return unique_results
    
    def _normalize_text(self, text: str) -> str:
        """標準化文字"""
        # 移除多餘空格
        text = re.sub(r'\s+', ' ', text.strip())
        # 轉為小寫
        text = text.lower()
        # 移除標點符號
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _sort_results(self, results: List[ProcessedResult], query: str) -> List[ProcessedResult]:
        """排序結果"""
        # 主要按總分排序
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        # 如果總分相同，按相關性排序
        results.sort(key=lambda x: (x.overall_score, x.relevance_score), reverse=True)
        
        return results
    
    def get_cache_key(self, query: str, results: List[Dict[str, Any]]) -> str:
        """生成快取鍵"""
        # 結合查詢和結果的雜湊值
        data = query + json.dumps(results, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()
    
    def get_cached_results(self, cache_key: str) -> Optional[List[ProcessedResult]]:
        """獲取快取結果"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["results"]
            else:
                # 過期，移除
                del self.cache[cache_key]
        return None
    
    def cache_results(self, cache_key: str, results: List[ProcessedResult]):
        """快取結果"""
        self.cache[cache_key] = {
            "results": results,
            "timestamp": time.time()
        }
    
    def clear_cache(self):
        """清除快取"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計"""
        return {
            "total_entries": len(self.cache),
            "cache_size_mb": sum(len(json.dumps(entry)) for entry in self.cache.values()) / 1024 / 1024
        }

# 全域處理器實例
intelligent_processor = IntelligentProcessor() 