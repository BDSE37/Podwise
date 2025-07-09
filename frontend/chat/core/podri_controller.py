#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri 控制器
整合所有服務和介面，提供統一的應用程式控制
"""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# 匯入服務模組
from services.tts_service import TTSService
from services.rag_service import RAGService
from services.minio_audio_service import MinIOAudioService
from services.intelligent_audio_search import IntelligentAudioSearch
from services.service_manager import ServiceManager
from services.intelligent_processor import IntelligentProcessor
from services.voice_recorder import VoiceRecorder

# 匯入 UI 模組
from ui.main_interface import MainInterface

# 匯入工具模組
from utils.api_key_manager import APIKeyManager
from utils.env_config import EnvConfig


class PodriController:
    """Podri 控制器類別"""
    
    def __init__(self):
        """初始化控制器"""
        # 初始化配置
        self.env_config = EnvConfig()
        
        # 初始化服務
        self.api_manager = APIKeyManager()
        self.tts_service = TTSService()
        self.rag_service = RAGService()
        self.minio_audio_service = MinIOAudioService()
        self.intelligent_audio_search = IntelligentAudioSearch()
        self.service_manager = ServiceManager()
        self.intelligent_processor = IntelligentProcessor()
        self.voice_recorder = VoiceRecorder()
        
        # 初始化 UI 介面
        self.main_interface = MainInterface(
            api_manager=self.api_manager,
            service_manager=self.service_manager,
            tts_service=self.tts_service
        )
        
        # 初始化會話狀態
        self._init_session_state()
    
    def _init_session_state(self):
        """初始化會話狀態"""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {
                "voice_enabled": True,
                "selected_voice": "zh-TW-HsiaoChenNeural",
                "voice_volume": 0.8,
                "voice_speed": 1.0,
                "openai_key": "",
                "google_key": "",
                "gemini_key": "",
                "anthropic_key": ""
            }
        
        if "current_user_id" not in st.session_state:
            st.session_state.current_user_id = ""
        
        if "is_guest" not in st.session_state:
            st.session_state.is_guest = True
        
        if "current_session" not in st.session_state:
            st.session_state.current_session = {
                "start_time": datetime.now(),
                "message_count": 0,
                "voice_count": 0,
                "music_count": 0
            }
    
    def run(self):
        """運行應用程式"""
        # 渲染側邊欄
        self.main_interface.render_sidebar()
        
        # 渲染主介面
        self.main_interface.render_main_interface(self.handle_message)
    
    async def handle_message(self, message: str):
        """處理用戶訊息"""
        try:
            # 記錄用戶訊息
            self._add_message_to_history("user", message)
            
            # 更新統計
            st.session_state.current_session["message_count"] += 1
            
            # 顯示載入狀態
            with st.spinner("🤔 正在思考中..."):
                # 發送到 RAG 服務
                rag_response = await self.rag_service.send_message(
                    message, 
                    st.session_state.get("current_user_id", "guest")
                )
                
                if rag_response.get("success"):
                    response_text = rag_response.get("response", "")
                    
                    # 記錄 AI 回答
                    self._add_message_to_history("assistant", response_text)
                    
                    # 如果啟用語音，生成語音
                    if st.session_state.user_preferences.get("voice_enabled", True):
                        await self._generate_and_play_voice(response_text)
                    
                    # 顯示來源資訊
                    if rag_response.get("sources"):
                        self._show_sources(rag_response["sources"])
                    
                    # 顯示處理時間
                    if rag_response.get("processing_time"):
                        st.info(f"⏱️ 處理時間: {rag_response['processing_time']:.2f} 秒")
                
                else:
                    # 如果 RAG 失敗，使用預設回答
                    fallback_response = "抱歉，我目前無法處理您的請求。請稍後再試。"
                    self._add_message_to_history("assistant", fallback_response)
                    st.error(f"❌ 處理失敗: {rag_response.get('error', '未知錯誤')}")
            
            # 重新渲染頁面
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 處理訊息時發生錯誤: {str(e)}")
    
    def _add_message_to_history(self, role: str, content: str):
        """添加訊息到歷史記錄"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        st.session_state.chat_history.append(message)
    
    async def _generate_and_play_voice(self, text: str):
        """生成並播放語音"""
        try:
            selected_voice = st.session_state.user_preferences.get("selected_voice", "zh-TW-HsiaoChenNeural")
            
            # 生成語音
            voice_result = await self.tts_service.generate_speech(text, selected_voice)
            
            if voice_result and voice_result.get("success"):
                # 更新統計
                st.session_state.current_session["voice_count"] += 1
                
                # 這裡可以添加音訊播放功能
                st.success("🎤 語音生成成功")
                
                # 顯示語音資訊
                duration = voice_result.get("duration", 0)
                if duration > 0:
                    st.info(f"🎵 音訊時長: {duration:.1f} 秒")
            
            else:
                st.warning("⚠️ 語音生成失敗，僅顯示文字")
                
        except Exception as e:
            st.warning(f"⚠️ 語音生成錯誤: {str(e)}")
    
    def _show_sources(self, sources: List[Dict[str, Any]]):
        """顯示來源資訊"""
        if sources:
            with st.expander("📚 參考來源"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**{i}. {source.get('title', '未知標題')}**")
                    st.markdown(f"來源: {source.get('source', '未知來源')}")
                    if source.get('content'):
                        st.markdown(f"內容: {source.get('content', '')[:100]}...")
                    st.markdown("---")
    
    def validate_user_id(self, user_id: str) -> bool:
        """驗證用戶 ID"""
        # 這裡可以添加實際的用戶驗證邏輯
        if not user_id or len(user_id) < 3:
            return False
        
        # 簡單的驗證規則
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return all(c in valid_chars for c in user_id)
    
    def generate_random_user_id(self) -> str:
        """生成隨機用戶 ID"""
        import random
        import string
        
        # 生成 8 位隨機字串
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(8))
    
    def save_user_session(self, user_id: str, category: str = "", program: str = "") -> bool:
        """保存用戶會話"""
        try:
            # 這裡可以添加實際的會話保存邏輯
            session_data = {
                "user_id": user_id,
                "category": category,
                "program": program,
                "timestamp": datetime.now().isoformat(),
                "message_count": st.session_state.current_session.get("message_count", 0)
            }
            
            # 可以保存到資料庫或檔案
            print(f"保存會話: {session_data}")
            return True
            
        except Exception as e:
            print(f"保存會話失敗: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            "tts_status": self.tts_service.check_service_status(),
            "rag_status": self.rag_service.check_service_status(),
            "api_status": self.api_manager.get_api_status_summary(),
            "session_info": {
                "user_id": st.session_state.get("current_user_id", ""),
                "is_guest": st.session_state.get("is_guest", True),
                "message_count": st.session_state.current_session.get("message_count", 0),
                "voice_count": st.session_state.current_session.get("voice_count", 0)
            }
        } 