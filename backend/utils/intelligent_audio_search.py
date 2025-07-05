#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能音檔搜尋服務
根據對話內容自動搜尋相關的音檔，支援商業類別、Podcast 等
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import streamlit as st

class IntelligentAudioSearch:
    """智能音檔搜尋類別"""
    
    def __init__(self):
        """初始化智能音檔搜尋"""
        # 商業類別關鍵字映射
        self.business_keywords = {
            "股癌": {
                "keywords": ["股癌", "股市", "投資", "股票", "理財", "財經"],
                "category": "投資理財",
                "podcast_name": "股癌",
                "description": "知名投資理財 Podcast",
                "search_terms": ["股癌", "投資", "股市分析", "理財建議"]
            },
            "矽谷輕鬆談": {
                "keywords": ["矽谷", "科技", "創業", "新創", "startup"],
                "category": "科技創業",
                "podcast_name": "矽谷輕鬆談",
                "description": "矽谷科技創業分享",
                "search_terms": ["矽谷", "科技", "創業", "新創公司"]
            },
            "科技早餐": {
                "keywords": ["科技", "早餐", "科技新聞", "科技趨勢"],
                "category": "科技新聞",
                "podcast_name": "科技早餐",
                "description": "每日科技新聞摘要",
                "search_terms": ["科技新聞", "科技趨勢", "科技早餐"]
            },
            "商業思維": {
                "keywords": ["商業", "思維", "商業模式", "策略"],
                "category": "商業策略",
                "podcast_name": "商業思維",
                "description": "商業思維與策略分析",
                "search_terms": ["商業思維", "商業模式", "策略分析"]
            },
            "財經早知道": {
                "keywords": ["財經", "金融", "經濟", "市場"],
                "category": "財經分析",
                "podcast_name": "財經早知道",
                "description": "財經市場分析",
                "search_terms": ["財經", "金融", "市場分析"]
            }
        }
        
        # 音樂風格關鍵字映射
        self.music_keywords = {
            "古典": ["古典", "優雅", "莊嚴", "交響樂", "鋼琴"],
            "流行": ["流行", "現代", "時尚", "輕快"],
            "電子": ["電子", "電音", "舞曲", "節奏"],
            "爵士": ["爵士", "藍調", "即興", "慵懶"],
            "搖滾": ["搖滾", "重金屬", "激情", "力量"],
            "民謠": ["民謠", "鄉村", "溫暖", "樸實"],
            "放鬆": ["放鬆", "舒緩", "平靜", "冥想"],
            "激勵": ["激勵", "活力", "動力", "振奮"]
        }
        
        # 情感關鍵字映射
        self.emotion_keywords = {
            "愉悅": ["開心", "快樂", "愉悅", "興奮", "歡樂"],
            "放鬆": ["放鬆", "平靜", "舒緩", "安詳", "寧靜"],
            "激勵": ["激勵", "鼓舞", "振奮", "動力", "活力"],
            "浪漫": ["浪漫", "溫柔", "甜蜜", "愛情", "溫馨"],
            "專業": ["專業", "正式", "權威", "可靠", "穩重"],
            "創意": ["創意", "創新", "有趣", "活潑", "新奇"]
        }
    
    def analyze_content(self, text: str) -> Dict[str, Any]:
        """分析文本內容，識別關鍵字和類別"""
        analysis = {
            "business_podcasts": [],
            "music_styles": [],
            "emotions": [],
            "search_terms": [],
            "confidence": 0.0
        }
        
        text_lower = text.lower()
        
        # 識別商業 Podcast
        for podcast_name, info in self.business_keywords.items():
            for keyword in info["keywords"]:
                if keyword.lower() in text_lower:
                    analysis["business_podcasts"].append({
                        "name": podcast_name,
                        "category": info["category"],
                        "description": info["description"],
                        "search_terms": info["search_terms"],
                        "confidence": 0.9
                    })
                    analysis["search_terms"].extend(info["search_terms"])
                    break
        
        # 識別音樂風格
        for style, keywords in self.music_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    analysis["music_styles"].append({
                        "style": style,
                        "keyword": keyword,
                        "confidence": 0.8
                    })
                    analysis["search_terms"].append(f"{style}音樂")
                    break
        
        # 識別情感
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    analysis["emotions"].append({
                        "emotion": emotion,
                        "keyword": keyword,
                        "confidence": 0.7
                    })
                    analysis["search_terms"].append(f"{emotion}風格")
                    break
        
        # 計算整體信心度
        total_matches = len(analysis["business_podcasts"]) + len(analysis["music_styles"]) + len(analysis["emotions"])
        analysis["confidence"] = min(total_matches * 0.3, 1.0)
        
        return analysis
    
    async def search_related_audio(self, text: str, minio_service=None) -> List[Dict[str, Any]]:
        """搜尋相關音檔"""
        try:
            # 分析文本內容
            analysis = self.analyze_content(text)
            
            # 如果沒有識別到任何關鍵字，返回空列表
            if analysis["confidence"] < 0.1:
                return []
            
            # 搜尋結果
            search_results = []
            
            # 搜尋商業 Podcast 音檔
            for podcast in analysis["business_podcasts"]:
                podcast_results = await self._search_podcast_audio(podcast, minio_service)
                search_results.extend(podcast_results)
            
            # 搜尋音樂音檔
            for music_style in analysis["music_styles"]:
                music_results = await self._search_music_audio(music_style, minio_service)
                search_results.extend(music_results)
            
            # 搜尋情感相關音檔
            for emotion in analysis["emotions"]:
                emotion_results = await self._search_emotion_audio(emotion, minio_service)
                search_results.extend(emotion_results)
            
            # 去重並排序
            unique_results = self._deduplicate_results(search_results)
            sorted_results = sorted(unique_results, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return sorted_results
            
        except Exception as e:
            st.error(f"音檔搜尋失敗: {str(e)}")
            return []
    
    async def _search_podcast_audio(self, podcast_info: Dict[str, Any], minio_service=None) -> List[Dict[str, Any]]:
        """搜尋 Podcast 音檔"""
        results = []
        
        # 模擬 Podcast 音檔搜尋結果
        podcast_name = podcast_info["name"]
        category = podcast_info["category"]
        
        # 根據 Podcast 名稱生成模擬音檔
        sample_episodes = [
            {
                "name": f"{podcast_name}_episode_001.wav",
                "title": f"{podcast_name} 第001集",
                "category": category,
                "duration": 1800,  # 30分鐘
                "size": 20480000,  # 20MB
                "relevance_score": 0.95,
                "type": "podcast",
                "description": f"{podcast_info['description']} - 第001集",
                "tags": podcast_info["search_terms"]
            },
            {
                "name": f"{podcast_name}_episode_002.wav",
                "title": f"{podcast_name} 第002集",
                "category": category,
                "duration": 2100,  # 35分鐘
                "size": 23552000,  # 23MB
                "relevance_score": 0.90,
                "type": "podcast",
                "description": f"{podcast_info['description']} - 第002集",
                "tags": podcast_info["search_terms"]
            },
            {
                "name": f"{podcast_name}_highlight.wav",
                "title": f"{podcast_name} 精華片段",
                "category": category,
                "duration": 300,  # 5分鐘
                "size": 3072000,  # 3MB
                "relevance_score": 0.85,
                "type": "podcast_highlight",
                "description": f"{podcast_info['description']} - 精華片段",
                "tags": podcast_info["search_terms"]
            }
        ]
        
        results.extend(sample_episodes)
        
        # 如果有 MinIO 服務，嘗試從 MinIO 搜尋
        if minio_service:
            try:
                minio_results = await minio_service.search_audio_files(
                    " ".join(podcast_info["search_terms"]),
                    category="podcast"
                )
                for result in minio_results:
                    result["relevance_score"] = 0.8
                    result["type"] = "podcast"
                results.extend(minio_results)
            except Exception as e:
                st.warning(f"MinIO 搜尋失敗: {str(e)}")
        
        return results
    
    async def _search_music_audio(self, music_style: Dict[str, Any], minio_service=None) -> List[Dict[str, Any]]:
        """搜尋音樂音檔"""
        results = []
        
        style = music_style["style"]
        
        # 模擬音樂音檔搜尋結果
        sample_music = [
            {
                "name": f"{style}_background_001.wav",
                "title": f"{style}背景音樂",
                "category": "音樂",
                "duration": 180,  # 3分鐘
                "size": 5120000,  # 5MB
                "relevance_score": 0.85,
                "type": "background_music",
                "description": f"{style}風格的背景音樂",
                "tags": [f"{style}音樂", "背景音樂"]
            },
            {
                "name": f"{style}_instrumental.wav",
                "title": f"{style}器樂",
                "category": "音樂",
                "duration": 240,  # 4分鐘
                "size": 6144000,  # 6MB
                "relevance_score": 0.80,
                "type": "instrumental",
                "description": f"{style}風格的器樂演奏",
                "tags": [f"{style}音樂", "器樂"]
            }
        ]
        
        results.extend(sample_music)
        
        # 如果有 MinIO 服務，嘗試從 MinIO 搜尋
        if minio_service:
            try:
                minio_results = await minio_service.search_audio_files(
                    f"{style}音樂",
                    category="music"
                )
                for result in minio_results:
                    result["relevance_score"] = 0.75
                    result["type"] = "music"
                results.extend(minio_results)
            except Exception as e:
                st.warning(f"MinIO 音樂搜尋失敗: {str(e)}")
        
        return results
    
    async def _search_emotion_audio(self, emotion: Dict[str, Any], minio_service=None) -> List[Dict[str, Any]]:
        """搜尋情感相關音檔"""
        results = []
        
        emotion_name = emotion["emotion"]
        
        # 模擬情感音檔搜尋結果
        sample_emotion_audio = [
            {
                "name": f"{emotion_name}_mood_001.wav",
                "title": f"{emotion_name}氛圍音樂",
                "category": "氛圍音樂",
                "duration": 300,  # 5分鐘
                "size": 7680000,  # 7.5MB
                "relevance_score": 0.75,
                "type": "mood_music",
                "description": f"{emotion_name}氛圍的音樂",
                "tags": [f"{emotion_name}風格", "氛圍音樂"]
            }
        ]
        
        results.extend(sample_emotion_audio)
        
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重搜尋結果"""
        seen_names = set()
        unique_results = []
        
        for result in results:
            name = result.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                unique_results.append(result)
        
        return unique_results
    
    def get_search_suggestions(self, text: str) -> List[str]:
        """獲取搜尋建議"""
        analysis = self.analyze_content(text)
        suggestions = []
        
        # 基於識別的內容生成建議
        for podcast in analysis["business_podcasts"]:
            suggestions.append(f"搜尋 {podcast['name']} 相關音檔")
            suggestions.append(f"播放 {podcast['category']} 類別內容")
        
        for music_style in analysis["music_styles"]:
            suggestions.append(f"生成 {music_style['style']} 風格音樂")
            suggestions.append(f"搜尋 {music_style['style']} 背景音樂")
        
        for emotion in analysis["emotions"]:
            suggestions.append(f"播放 {emotion['emotion']} 氛圍音樂")
            suggestions.append(f"生成 {emotion['emotion']} 風格內容")
        
        # 如果沒有識別到特定內容，提供一般建議
        if not suggestions:
            suggestions = [
                "搜尋相關 Podcast 音檔",
                "生成背景音樂",
                "播放語音內容"
            ]
        
        return suggestions

# 創建全域實例
intelligent_audio_search = IntelligentAudioSearch() 