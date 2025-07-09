#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主介面模組
整合所有 UI 介面，提供統一的介面管理
"""

import streamlit as st
from typing import Dict, Any, Callable
from .chat_interface import ChatInterface
from .sidebar_interface import SidebarInterface
from .voice_interface import VoiceInterface


class MainInterface:
    """主介面類別"""
    
    def __init__(self, api_manager, service_manager, tts_service):
        """初始化主介面"""
        self.api_manager = api_manager
        self.service_manager = service_manager
        self.tts_service = tts_service
        
        # 初始化子介面
        self.chat_interface = ChatInterface()
        self.sidebar_interface = SidebarInterface(api_manager, service_manager)
        self.voice_interface = VoiceInterface(tts_service)
        
        self._init_page_config()
        self._init_styles()
    
    def _init_page_config(self):
        """初始化頁面配置"""
        st.set_page_config(
            page_title="Podri 智能助理",
            page_icon="🦊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def _init_styles(self):
        """初始化樣式"""
        st.markdown("""
        <style>
        /* 主要色系定義 */
        :root {
            --milk-tea: #F5E6D3;
            --light-milk-tea: #FDF6E3;
            --dark-milk-tea: #E8D5B7;
            --earth-brown: #8B4513;
            --light-earth: #D2691E;
            --warm-beige: #F5DEB3;
            --accent-gold: #DAA520;
        }

        /* 整體背景 */
        .main {
            background: linear-gradient(135deg, var(--light-milk-tea) 0%, var(--warm-beige) 100%);
        }

        /* 標題樣式 */
        .main-header {
            background: linear-gradient(90deg, var(--accent-gold), var(--light-earth));
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* 按鈕樣式 */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-gold), var(--light-earth));
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.5rem 1.5rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        /* 輸入框樣式 */
        .stTextInput > div > div > input {
            border: 2px solid var(--dark-milk-tea);
            border-radius: 25px;
            background: var(--light-milk-tea);
        }

        /* 選擇框樣式 */
        .stSelectbox > div > div > select {
            border: 2px solid var(--dark-milk-tea);
            border-radius: 10px;
            background: var(--light-milk-tea);
        }

        /* 聊天容器 */
        .chat-container {
            background: white;
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: 500px;
            overflow-y: auto;
        }

        /* 功能卡片 */
        .feature-card {
            background: linear-gradient(135deg, var(--milk-tea), var(--warm-beige));
            border: 1px solid var(--dark-milk-tea);
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_main_interface(self, on_send_message: Callable[[str], None]):
        """渲染主介面 - 三欄式佈局"""
        # 創建三欄佈局：左側功能控制 | 中間對話區 | 右側系統狀態
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            # 左側 1/4：功能控制欄
            self.render_left_control_panel()

        with col2:
            # 中間 2/4：主對話區
            self.render_main_chat_interface(on_send_message)

        with col3:
            # 右側 1/4：系統狀態和統計
            self.render_right_status_panel()
    
    def render_left_control_panel(self):
        """渲染左側功能控制面板"""
        st.markdown("### 🎛️ 功能控制")

        # 1. 回到首頁按鈕（最上方）
        if st.button("🏠 回到首頁", use_container_width=True, type="primary"):
            st.session_state.current_page = "home"
            st.rerun()

        st.markdown("---")

        # 2. 用戶 ID 驗證區域
        st.markdown("#### 🔐 用戶驗證")
        user_id_input = st.text_input(
            "輸入用戶 ID",
            value=st.session_state.get("current_user_id", ""),
            placeholder="請輸入您的用戶 ID",
            help="輸入正確的用戶 ID 以啟用完整功能"
        )

        if st.button("✅ 驗證 ID", use_container_width=True):
            if user_id_input.strip():
                # 這裡會調用用戶驗證功能
                st.session_state["current_user_id"] = user_id_input.strip()
                st.session_state["is_guest"] = False
                st.success("✅ 用戶驗證成功！")
                st.rerun()
            else:
                st.warning("請輸入用戶 ID")

        # 顯示當前用戶狀態
        if st.session_state.get("current_user_id"):
            st.success(f"✅ 已登入用戶: {st.session_state.current_user_id}")
        else:
            st.info("👤 訪客模式")

        st.markdown("---")

        # 3. 語音設定區域
        self.voice_interface.render_voice_settings()

        st.markdown("---")

        # 4. 清除對話
        if st.button("🗑️ 清除對話紀錄", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    def render_main_chat_interface(self, on_send_message: Callable[[str], None]):
        """渲染主聊天介面"""
        # 標題
        st.markdown("""
        <div class="main-header">
            <h1 style="text-align: center; color: white; margin: 0;">🦊 Podri 智能助理</h1>
            <p style="text-align: center; color: white; margin: 0.5rem 0 0 0;">您的個人化聲音空間</p>
        </div>
        """, unsafe_allow_html=True)

        # 聊天訊息區域
        chat_history = st.session_state.get("chat_history", [])
        self.chat_interface.render_chat_messages(chat_history)

        # 輸入區域
        self.chat_interface.render_input_area(on_send_message)
    
    def render_right_status_panel(self):
        """渲染右側狀態面板"""
        st.markdown("### 📊 系統狀態")
        st.info("系統運行正常")
        
        # 服務狀態
        st.markdown("**服務狀態：**")
        st.markdown("""
        - Podri-Chat: ✅ 正常
        - RAG Pipeline: ⚠️ 維護中
        - TTS 服務: ✅ 正常
        """)
        
        # 使用統計
        current_session = st.session_state.get("current_session", {})
        st.markdown("**使用統計：**")
        st.markdown(f"""
        - 訊息數: {current_session.get('message_count', 0)}
        - 語音生成: {current_session.get('voice_count', 0)}
        """)
        
        # 快速功能
        st.markdown("### ⚡ 快速功能")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 聊天歷史", use_container_width=True):
                self.show_chat_history()
        
        with col2:
            if st.button("📊 使用統計", use_container_width=True):
                self.show_usage_stats()
        
        # 系統資訊
        st.markdown("### ℹ️ 系統資訊")
        st.markdown("""
        - 版本: v1.0.0
        - 更新時間: 2024-01-01
        - 支援語言: 繁體中文
        """)
    
    def show_chat_history(self):
        """顯示聊天歷史"""
        chat_history = st.session_state.get("chat_history", [])
        self.chat_interface.show_chat_history(chat_history)
    
    def show_usage_stats(self):
        """顯示使用統計"""
        current_session = st.session_state.get("current_session", {})
        self.chat_interface.show_usage_stats(current_session)
    
    def render_sidebar(self, on_test_apis: Callable = None):
        """渲染側邊欄"""
        self.sidebar_interface.render_sidebar(on_test_apis) 