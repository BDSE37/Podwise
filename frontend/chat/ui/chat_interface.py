#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天介面模組
處理聊天對話相關的 UI 功能
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime


class ChatInterface:
    """聊天介面類別"""
    
    def __init__(self):
        """初始化聊天介面"""
        self._init_chat_styles()
    
    def _init_chat_styles(self):
        """初始化聊天樣式"""
        st.markdown("""
        <style>
        /* 聊天氣泡樣式 */
        .chat-bubble {
            padding: 1rem;
            border-radius: 15px;
            margin: 0.5rem 0;
            max-width: 80%;
            word-wrap: break-word;
        }

        .user-bubble {
            background: linear-gradient(135deg, #DAA520, #D2691E);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }

        .bot-bubble {
            background: linear-gradient(135deg, #F5E6D3, #F5DEB3);
            color: #8B4513;
            margin-right: auto;
            border-bottom-left-radius: 5px;
            border: 1px solid #E8D5B7;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_chat_messages(self, chat_history: List[Dict[str, Any]]):
        """渲染聊天訊息"""
        if not chat_history:
            st.info("👋 歡迎使用 Podri 智能助理！請開始對話。")
            return
        
        for message in chat_history:
            if message.get("role") == "user":
                st.markdown(f"""
                <div class="chat-bubble user-bubble">
                    👤 <strong>您：</strong><br>
                    {message.get("content", "")}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble bot-bubble">
                    🤖 <strong>Podri：</strong><br>
                    {message.get("content", "")}
                </div>
                """, unsafe_allow_html=True)
    
    def render_input_area(self, on_send_message):
        """渲染輸入區域"""
        st.markdown("---")
        
        # 輸入區域
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "輸入您的問題：",
                placeholder="請輸入您的問題或指令...",
                height=100,
                key="user_input"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 發送", use_container_width=True, type="primary"):
                if user_input.strip():
                    on_send_message(user_input.strip())
                    st.rerun()
                else:
                    st.warning("請輸入內容")
        
        # 快速操作按鈕
        st.markdown("**💡 快速操作：**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📚 學習建議", use_container_width=True):
                on_send_message("請給我一些學習建議")
                st.rerun()
        
        with col2:
            if st.button("🎵 推薦 Podcast", use_container_width=True):
                on_send_message("請推薦一些好的 Podcast")
                st.rerun()
        
        with col3:
            if st.button("🔍 搜尋內容", use_container_width=True):
                on_send_message("請幫我搜尋相關內容")
                st.rerun()
        
        with col4:
            if st.button("🎤 語音對話", use_container_width=True):
                on_send_message("我想用語音對話")
                st.rerun()
    
    def show_chat_history(self, chat_history: List[Dict[str, Any]]):
        """顯示聊天歷史"""
        if not chat_history:
            st.info("尚無聊天記錄")
            return
        
        st.markdown("### 📝 聊天歷史")
        
        # 按日期分組
        history_by_date = {}
        for message in chat_history:
            date = message.get("timestamp", datetime.now()).strftime("%Y-%m-%d")
            if date not in history_by_date:
                history_by_date[date] = []
            history_by_date[date].append(message)
        
        # 顯示歷史記錄
        for date, messages in history_by_date.items():
            with st.expander(f"📅 {date} ({len(messages)} 條訊息)"):
                for message in messages[-10:]:  # 只顯示最近10條
                    time_str = message.get("timestamp", datetime.now()).strftime("%H:%M")
                    role_icon = "👤" if message.get("role") == "user" else "🤖"
                    st.markdown(f"**{time_str}** {role_icon} {message.get('content', '')[:50]}...")
    
    def show_usage_stats(self, session_data: Dict[str, Any]):
        """顯示使用統計"""
        st.markdown("### 📊 使用統計")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("訊息數", session_data.get("message_count", 0))
        
        with col2:
            st.metric("語音生成", session_data.get("voice_count", 0))
        
        with col3:
            st.metric("音樂生成", session_data.get("music_count", 0))
        
        # 會話時長
        if "start_time" in session_data:
            duration = datetime.now() - session_data["start_time"]
            st.metric("會話時長", f"{duration.seconds // 60} 分鐘") 