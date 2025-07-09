#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
側邊欄介面模組
處理側邊欄相關的 UI 功能
"""

import streamlit as st
from typing import Dict, Any, Callable


class SidebarInterface:
    """側邊欄介面類別"""
    
    def __init__(self, api_manager, service_manager):
        """初始化側邊欄介面"""
        self.api_manager = api_manager
        self.service_manager = service_manager
        self._init_sidebar_styles()
    
    def _init_sidebar_styles(self):
        """初始化側邊欄樣式"""
        st.markdown("""
        <style>
        /* 側邊欄樣式 */
        .css-1d391kg {
            background: linear-gradient(180deg, #F5E6D3 0%, #E8D5B7 100%);
            border-right: 2px solid #8B4513;
        }
        
        /* API 狀態樣式 */
        .api-status {
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.25rem 0;
        }
        
        .api-status.success {
            background: #E8F5E8;
            border-left: 4px solid #4CAF50;
        }
        
        .api-status.error {
            background: #FFEBEE;
            border-left: 4px solid #F44336;
        }
        
        .api-status.warning {
            background: #FFF3E0;
            border-left: 4px solid #FF9800;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self, on_test_apis: Callable = None):
        """渲染側邊欄"""
        with st.sidebar:
            # 回到主頁按鈕
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <a href="http://localhost" target="_self" style="text-decoration: none;">
                    <div style="background: linear-gradient(135deg, #DAA520, #D2691E); color: white; padding: 10px; border-radius: 10px; text-align: center; margin: 10px 0;">
                        🏠 回到主頁
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 標題區域
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h3>🦊 Podri 智能助理</h3>
                <p>你的個人化聲音空間</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # API Key 管理
            self._render_api_key_management()
            
            # 服務狀態檢查
            self._render_service_status()
            
            # 熱門推薦
            self._render_popular_recommendations()
            
            # 每日聲音小卡
            self._render_daily_voice_card()
    
    def _render_api_key_management(self):
        """渲染 API Key 管理"""
        st.subheader("🔑 API Key 管理")
        
        # OpenAI API Key
        openai_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.user_preferences.get("openai_key", ""),
            type="password",
            help="輸入您的 OpenAI API Key",
            key="openai_key_input"
        )
        if openai_key != self.api_manager.get_api_key("openai"):
            self.api_manager.update_api_key("openai", openai_key)
        
        # Google Search API Key
        google_key = st.text_input(
            "Google Search API Key",
            value=st.session_state.user_preferences.get("google_key", ""),
            type="password",
            help="輸入您的 Google Search API Key",
            key="google_key_input"
        )
        if google_key != self.api_manager.get_api_key("google_search"):
            self.api_manager.update_api_key("google_search", google_key)
        
        # Gemini API Key
        gemini_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.user_preferences.get("gemini_key", ""),
            type="password",
            help="輸入您的 Gemini API Key",
            key="gemini_key_input"
        )
        if gemini_key != self.api_manager.get_api_key("gemini"):
            self.api_manager.update_api_key("gemini", gemini_key)
        
        # Anthropic API Key
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=st.session_state.user_preferences.get("anthropic_key", ""),
            type="password",
            help="輸入您的 Anthropic API Key",
            key="anthropic_key_input"
        )
        if anthropic_key != self.api_manager.get_api_key("anthropic"):
            self.api_manager.update_api_key("anthropic", anthropic_key)
        
        # 測試 API 連接
        if st.button("🧪 測試 API 連接", use_container_width=True):
            with st.spinner("測試 API 連接中..."):
                # 這裡會調用 API 測試功能
                pass
        
        # 顯示 API 狀態
        self._render_api_status()
    
    def _render_api_status(self):
        """渲染 API 狀態"""
        api_status = self.api_manager.get_api_status_summary()
        if api_status:
            st.markdown("**📊 API 狀態**")
            for api_name, status in api_status.items():
                if status.get("has_key"):
                    if status.get("available"):
                        st.markdown(f"""
                        <div class="api-status success">
                            ✅ {api_name}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="api-status error">
                            ❌ {api_name}: {status.get('error', '未知錯誤')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="api-status warning">
                        ⚠️ {api_name}: 未設定
                    </div>
                    """, unsafe_allow_html=True)
    
    def _render_service_status(self):
        """渲染服務狀態"""
        st.markdown("---")
        st.subheader("🔧 服務狀態")
        
        # 檢查 TTS 服務狀態
        tts_status = self.service_manager.check_tts_service_status()
        if tts_status["status"] == "healthy":
            st.success("🎤 TTS 服務: 正常運行")
        else:
            st.error(f"🎤 TTS 服務: {tts_status.get('error', '連接失敗')}")
        
        # 檢查 RAG 服務狀態
        rag_status = self.service_manager.check_rag_service_status()
        if rag_status["status"] == "healthy":
            st.success("🧠 RAG 服務: 正常運行")
        else:
            st.warning(f"🧠 RAG 服務: 維護中 ({rag_status.get('error', '連接失敗')})")
            st.info("💡 RAG 服務正在重新部署，請稍後再試")
    
    def _render_popular_recommendations(self):
        """渲染熱門推薦"""
        st.markdown("---")
        st.subheader("🔥 熱門推薦")
        
        recommendations = [
            {"title": "股癌", "category": "商業", "description": "晦澀金融投資知識直白講"},
            {"title": "天下學習", "category": "教育", "description": "向最厲害的人學習"}
        ]
        
        for rec in recommendations:
            with st.expander(f"📻 {rec['title']} ({rec['category']})"):
                st.write(rec['description'])
                if st.button(f"試聽 {rec['title']}", key=f"listen_{rec['title']}"):
                    # 這裡會調用試聽功能
                    pass
    
    def _render_daily_voice_card(self):
        """渲染每日聲音小卡"""
        st.markdown("---")
        st.subheader("🎵 每日聲音小卡")
        
        daily_cards = [
            {"title": "今日精選", "content": "科技早餐 05/29", "image": "images/科技報橘.png"},
            {"title": "推薦小卡", "content": "矽谷輕鬆談 S2E14", "image": "images/矽谷輕鬆談.png"}
        ]
        
        for card in daily_cards:
            st.markdown(f"""
            <div class="feature-card">
                <h5>{card['title']}</h5>
                <p>{card['content']}</p>
            </div>
            """, unsafe_allow_html=True) 