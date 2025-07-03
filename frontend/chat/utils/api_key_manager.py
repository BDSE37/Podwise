#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Key 管理模組
提供多種 API 的統一管理和智能選擇功能
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum
import streamlit as st

class APIType(Enum):
    """API 類型枚舉"""
    OPENAI = "openai"
    GOOGLE_SEARCH = "google_search"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class APIKeyManager:
    """API Key 管理類別"""
    
    def __init__(self):
        """初始化 API Key 管理器"""
        self.api_keys = {}
        self.api_status = {}
        self.load_api_keys()
        
        # API 查詢模式定義
        self.query_patterns = {
            APIType.GOOGLE_SEARCH: [
                r"搜尋|查詢|最新|新聞|時事|今天|昨天|明天",
                r"天氣|股票|匯率|價格|市場",
                r"如何|怎麼|什麼時候|哪裡|誰",
                r"推薦|比較|評價|評論"
            ],
            APIType.OPENAI: [
                r"程式|代碼|開發|技術|算法",
                r"創意|寫作|故事|詩歌|劇本",
                r"分析|解釋|概念|理論|原理",
                r"翻譯|語言|語法|文法"
            ],
            APIType.GEMINI: [
                r"圖像|圖片|視覺|設計|繪圖",
                r"多媒體|影片|音頻|處理",
                r"Google|Android|Chrome|Gmail",
                r"機器學習|AI|人工智慧"
            ],
            APIType.ANTHROPIC: [
                r"倫理|道德|哲學|價值觀",
                r"安全|隱私|保護|風險",
                r"分析|研究|學術|論文",
                r"創意寫作|故事|敘事"
            ]
        }
    
    def load_api_keys(self):
        """從 Streamlit session state 載入 API Keys"""
        for api_type in APIType:
            key = st.session_state.get(f"api_key_{api_type.value}", "")
            if key:
                self.api_keys[api_type] = key
    
    def save_api_key(self, api_type: APIType, api_key: str):
        """儲存 API Key 到 session state"""
        st.session_state[f"api_key_{api_type.value}"] = api_key
        self.api_keys[api_type] = api_key
    
    def get_api_key(self, api_type: APIType) -> Optional[str]:
        """獲取指定 API 的 Key"""
        return self.api_keys.get(api_type)
    
    def update_api_key(self, api_type: APIType, api_key: str):
        """更新 API Key"""
        if api_key.strip():
            self.save_api_key(api_type, api_key)
            # 清除該 API 的狀態快取
            if api_type in self.api_status:
                del self.api_status[api_type]
        else:
            # 如果 key 為空，從儲存中移除
            if api_type in self.api_keys:
                del self.api_keys[api_type]
            if f"api_key_{api_type.value}" in st.session_state:
                del st.session_state[f"api_key_{api_type.value}"]
    
    def get_best_api_for_query(self, query: str) -> Optional[APIType]:
        """根據查詢內容智能選擇最適合的 API"""
        if not query.strip():
            return None
        
        # 計算每個 API 的匹配分數
        api_scores = {}
        
        for api_type, patterns in self.query_patterns.items():
            if not self.get_api_key(api_type):
                continue  # 跳過沒有 key 的 API
            
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                api_scores[api_type] = score
        
        # 返回分數最高的 API
        if api_scores:
            return max(api_scores.items(), key=lambda x: x[1])[0]
        
        # 如果沒有匹配，返回有 key 的第一個 API
        for api_type in APIType:
            if self.get_api_key(api_type):
                return api_type
        
        return None
    
    async def test_api_connection(self, api_type: APIType) -> Dict[str, Any]:
        """測試 API 連接"""
        try:
            api_key = self.get_api_key(api_type)
            if not api_key:
                return {
                    "available": False,
                    "error": "API Key 未設定"
                }
            
            # 根據 API 類型進行不同的測試
            if api_type == APIType.OPENAI:
                return await self._test_openai_connection(api_key)
            elif api_type == APIType.GOOGLE_SEARCH:
                return await self._test_google_search_connection(api_key)
            elif api_type == APIType.GEMINI:
                return await self._test_gemini_connection(api_key)
            elif api_type == APIType.ANTHROPIC:
                return await self._test_anthropic_connection(api_key)
            else:
                return {
                    "available": False,
                    "error": "不支援的 API 類型"
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _test_openai_connection(self, api_key: str) -> Dict[str, Any]:
        """測試 OpenAI API 連接"""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {
                "available": True,
                "model": "gpt-3.5-turbo",
                "response_time": "正常"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _test_google_search_connection(self, api_key: str) -> Dict[str, Any]:
        """測試 Google Search API 連接"""
        try:
            # 這裡實作 Google Search API 測試
            # 由於需要額外的設定，這裡先返回模擬結果
            return {
                "available": True,
                "service": "Google Custom Search",
                "response_time": "正常"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _test_gemini_connection(self, api_key: str) -> Dict[str, Any]:
        """測試 Gemini API 連接"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello")
            return {
                "available": True,
                "model": "gemini-pro",
                "response_time": "正常"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _test_anthropic_connection(self, api_key: str) -> Dict[str, Any]:
        """測試 Anthropic API 連接"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return {
                "available": True,
                "model": "claude-3-sonnet",
                "response_time": "正常"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    def get_api_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有 API 的狀態摘要"""
        summary = {}
        
        for api_type in APIType:
            api_name = api_type.value.replace("_", " ").title()
            has_key = bool(self.get_api_key(api_type))
            
            summary[api_name] = {
                "has_key": has_key,
                "available": False,
                "error": None
            }
            
            # 如果有 key，檢查狀態
            if has_key and api_type in self.api_status:
                summary[api_name].update(self.api_status[api_type])
        
        return summary
    
    def get_available_apis(self) -> List[APIType]:
        """獲取所有可用的 API 列表"""
        available = []
        for api_type in APIType:
            if self.get_api_key(api_type):
                available.append(api_type)
        return available
    
    def get_api_display_name(self, api_type: APIType) -> str:
        """獲取 API 的顯示名稱"""
        display_names = {
            APIType.OPENAI: "OpenAI GPT",
            APIType.GOOGLE_SEARCH: "Google Search",
            APIType.GEMINI: "Google Gemini",
            APIType.ANTHROPIC: "Anthropic Claude",
            APIType.OLLAMA: "Ollama"
        }
        return display_names.get(api_type, api_type.value)
    
    def get_api_description(self, api_type: APIType) -> str:
        """獲取 API 的描述"""
        descriptions = {
            APIType.OPENAI: "強大的語言模型，適合創意寫作和程式開發",
            APIType.GOOGLE_SEARCH: "即時網路搜尋，獲取最新資訊",
            APIType.GEMINI: "Google 的多模態 AI 模型，支援圖像和文字",
            APIType.ANTHROPIC: "注重安全性和倫理的 AI 助手",
            APIType.OLLAMA: "本地部署的開源 AI 模型"
        }
        return descriptions.get(api_type, "AI 助手服務")

# 建立全域實例
api_manager = APIKeyManager() 