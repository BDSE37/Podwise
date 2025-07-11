#!/usr/bin/env python3
"""
Podcast 格式化工具

此模組負責處理 Podcast 推薦的格式化，包含：
- Apple Podcast 連結格式
- TAG 標註（隱藏格式，供 RAG 檢索使用）
- 節目去重
- 信心度排序
- RSSID 字典序排序
- 智能 TAG 提取（Word2Vec + Transformer）

作者: Podwise Team
版本: 1.0.0
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# 導入智能 TAG 提取器
try:
    from ..scripts.tag_processor import SmartTagExtractor
except ImportError:
    # 如果無法導入，創建一個簡化版本
    class SmartTagExtractor:
        def __init__(self, existing_tags_file: Optional[str] = None):
            self.existing_tags_file = existing_tags_file
        
        def extract_smart_tags(self, query: str):
            # 簡化的標籤提取
            class SmartTagResult:
                def __init__(self):
                    self.extracted_tags = ["一般"]
                    self.method_used = "fallback"
                    self.confidence = 0.5
                    self.mapped_tags = []
            
            return SmartTagResult()

logger = logging.getLogger(__name__)


@dataclass
class FormattedPodcast:
    """格式化後的 Podcast 項目"""
    title: str
    description: str
    apple_podcast_url: str
    rss_id: str
    confidence: float
    category: str
    tags: List[str] = field(default_factory=list)
    hidden_tags: str = ""  # 隱藏的 TAG 標註，供 RAG 檢索使用


@dataclass
class PodcastRecommendationResult:
    """Podcast 推薦結果"""
    recommendations: List[FormattedPodcast]
    total_found: int
    confidence: float
    tags_used: List[str]
    reasoning: str
    processing_time: float


class PodcastFormatter:
    """Podcast 格式化器"""
    
    def __init__(self, existing_tags_file: Optional[str] = None):
        """
        初始化格式化器
        
        Args:
            existing_tags_file: 現有標籤檔案路徑（可選）
        """
        self.apple_podcast_base_url = "https://podcasts.apple.com/tw/podcast/id"
        
        # 初始化智能 TAG 提取器
        self.smart_extractor = SmartTagExtractor(existing_tags_file=existing_tags_file)
    
    def extract_tags_from_query(self, query: str) -> List[str]:
        """
        從查詢中提取 TAG（整合智能提取）
        
        Args:
            query: 用戶查詢
            
        Returns:
            List[str]: 提取的 TAG 列表
        """
        # 使用智能 TAG 提取器
        smart_result = self.smart_extractor.extract_smart_tags(query)
        
        logger.info(f"智能 TAG 提取結果: {smart_result.extracted_tags}")
        logger.info(f"使用的方法: {smart_result.method_used}")
        logger.info(f"信心度: {smart_result.confidence:.2f}")
        
        # 如果有映射結果，記錄詳細信息
        if smart_result.mapped_tags:
            logger.info("TAG 映射詳情:")
            for mapping in smart_result.mapped_tags:
                logger.info(f"  {mapping.original_tag} -> {mapping.mapped_tags} (方法: {mapping.method}, 信心度: {mapping.confidence:.2f})")
        
        return smart_result.extracted_tags
    
    def format_apple_podcast_url(self, rss_id: str) -> str:
        """
        格式化 Apple Podcast URL
        
        Args:
            rss_id: RSS ID
            
        Returns:
            str: 格式化的 Apple Podcast URL
        """
        return f"{self.apple_podcast_base_url}{rss_id}"
    
    def create_hidden_tags(self, tags: List[str]) -> str:
        """
        創建隱藏的 TAG 標註（供 RAG 檢索使用）
        
        Args:
            tags: TAG 列表
            
        Returns:
            str: 隱藏的 TAG 標註
        """
        if not tags:
            return ""
        
        # 創建隱藏的 TAG 標註，格式為 <!--TAG:tag1,tag2,tag3-->
        hidden_tags = f"<!--TAG:{','.join(tags)}-->"
        return hidden_tags
    
    def deduplicate_podcasts(self, podcasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重複的 Podcast（以節目為單位）
        
        Args:
            podcasts: Podcast 列表
            
        Returns:
            List[Dict[str, Any]]: 去重後的列表
        """
        seen_titles = set()
        unique_podcasts = []
        
        for podcast in podcasts:
            title = podcast.get('title', '').strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_podcasts.append(podcast)
        
        logger.info(f"去重前: {len(podcasts)} 個，去重後: {len(unique_podcasts)} 個")
        return unique_podcasts
    
    def sort_podcasts_by_confidence_and_rssid(self, podcasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按信心度和 RSSID 排序 Podcast
        
        Args:
            podcasts: Podcast 列表
            
        Returns:
            List[Dict[str, Any]]: 排序後的列表
        """
        # 按信心度降序排序，同信心度按 RSSID 字典序排序
        sorted_podcasts = sorted(
            podcasts,
            key=lambda x: (-x.get('confidence', 0.0), x.get('rss_id', ''))
        )
        
        return sorted_podcasts
    
    def format_podcast_recommendations(
        self,
        raw_podcasts: List[Dict[str, Any]],
        query: str,
        max_recommendations: int = 3
    ) -> PodcastRecommendationResult:
        """
        格式化 Podcast 推薦結果
        
        Args:
            raw_podcasts: 原始 Podcast 數據
            query: 用戶查詢
            max_recommendations: 最大推薦數量
            
        Returns:
            PodcastRecommendationResult: 格式化後的推薦結果
        """
        start_time = datetime.now()
        
        # 提取查詢中的 TAG
        tags = self.extract_tags_from_query(query)
        
        # 去重
        unique_podcasts = self.deduplicate_podcasts(raw_podcasts)
        
        # 排序
        sorted_podcasts = self.sort_podcasts_by_confidence_and_rssid(unique_podcasts)
        
        # 取前 N 個
        top_podcasts = sorted_podcasts[:max_recommendations]
        
        # 格式化為最終格式
        formatted_podcasts = []
        for podcast in top_podcasts:
            formatted_podcast = FormattedPodcast(
                title=podcast.get('title', ''),
                description=podcast.get('description', ''),
                apple_podcast_url=self.format_apple_podcast_url(podcast.get('rss_id', '')),
                rss_id=podcast.get('rss_id', ''),
                confidence=podcast.get('confidence', 0.0),
                category=podcast.get('category', ''),
                tags=podcast.get('tags', []),
                hidden_tags=self.create_hidden_tags(tags)
            )
            formatted_podcasts.append(formatted_podcast)
        
        # 計算整體信心度
        overall_confidence = max([p.confidence for p in formatted_podcasts]) if formatted_podcasts else 0.0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = PodcastRecommendationResult(
            recommendations=formatted_podcasts,
            total_found=len(raw_podcasts),
            confidence=overall_confidence,
            tags_used=tags,
            reasoning=f"找到 {len(raw_podcasts)} 個相關 Podcast，去重後 {len(unique_podcasts)} 個，推薦前 {len(formatted_podcasts)} 個",
            processing_time=processing_time
        )
        
        logger.info(f"格式化完成: {len(formatted_podcasts)} 個推薦，信心度: {overall_confidence:.2f}")
        return result
    
    def generate_recommendation_text(self, result: PodcastRecommendationResult) -> str:
        """
        生成推薦文字
        
        Args:
            result: 推薦結果
            
        Returns:
            str: 格式化的推薦文字
        """
        if not result.recommendations:
            return "抱歉，目前沒有找到相關的 Podcast 推薦。"
        
        lines = []
        for i, podcast in enumerate(result.recommendations, 1):
            # 格式：節目名稱：該集針對使用者問題推薦簡答
            line = f"{i}. **{podcast.title}**：{podcast.description}\n"
            line += f"   {podcast.apple_podcast_url}"
            
            # 添加隱藏的 TAG 標註
            if podcast.hidden_tags:
                line += f" {podcast.hidden_tags}"
            
            lines.append(line)
        
        # 添加 TAG 說明（如果有的話）
        if result.tags_used:
            tag_info = f"\n\n> 基於您的查詢中的關鍵詞：{', '.join(result.tags_used)}"
            lines.append(tag_info)
        
        return "\n\n".join(lines)
    
    def should_use_web_search(self, confidence: float, result_count: int) -> bool:
        """
        判斷是否應該使用 Web 搜尋
        
        Args:
            confidence: 信心度
            result_count: 結果數量
            
        Returns:
            bool: 是否應該使用 Web 搜尋
        """
        return confidence < 0.7 or result_count < 2


# 測試功能已移除，請使用 main.py 進行測試 