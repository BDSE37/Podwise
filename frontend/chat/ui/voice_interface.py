#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語音介面模組
處理語音相關的 UI 功能
"""

import streamlit as st
from typing import Dict, Any, List


class VoiceInterface:
    """語音介面類別"""
    
    def __init__(self, tts_service):
        """初始化語音介面"""
        self.tts_service = tts_service
        self.voice_options = {
            "zh-TW-HsiaoChenNeural": "Podria (溫柔女聲)",
            "zh-TW-YunJheNeural": "Podrick (穩重男聲)",
            "zh-TW-HanHanNeural": "Podlisa (活潑女聲)",
            "zh-TW-ZhiYuanNeural": "Podvid (專業男聲)"
        }
        self.voice_categories = {
            "Edge TTS 語音": ["zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-TW-HanHanNeural", "zh-TW-ZhiYuanNeural"]
        }
    
    def render_voice_settings(self):
        """渲染語音設定"""
        st.markdown("---")
        st.subheader("🎤 TTS 語音設定")
        
        # 語音開關
        voice_enabled = st.checkbox(
            "啟用語音回答",
            value=st.session_state.user_preferences.get("voice_enabled", True),
            key="voice_enabled_checkbox"
        )
        st.session_state.user_preferences["voice_enabled"] = voice_enabled
        
        if voice_enabled:
            # 顯示語音分類選擇
            st.markdown("**🎤 語音選擇**")
            
            # 顯示語音分類
            for category_name, voice_ids in self.voice_categories.items():
                if voice_ids:  # 只顯示有語音的分類
                    with st.expander(f"📁 {category_name} ({len(voice_ids)} 個語音)", expanded=True):
                        # 為每個分類創建選擇框
                        category_voices = {vid: self.voice_options.get(vid, vid) for vid in voice_ids}
                        
                        # 顯示語音選項
                        for voice_id, voice_name in category_voices.items():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                # 檢查是否為當前選中的語音
                                is_selected = st.session_state.user_preferences.get("selected_voice") == voice_id
                                if is_selected:
                                    st.markdown(f"✅ **{voice_name}**")
                                else:
                                    st.markdown(f"🔘 {voice_name}")
                            
                            with col2:
                                if st.button(f"試聽", key=f"test_{voice_id}"):
                                    self.play_voice_sample(voice_id)
                            
                            with col3:
                                if st.button(f"選擇", key=f"select_{voice_id}"):
                                    st.session_state.user_preferences["selected_voice"] = voice_id
                                    st.success(f"✅ 已選擇 {voice_name}")
                                    st.rerun()
            
            # 顯示當前選中的語音
            current_voice = st.session_state.user_preferences.get("selected_voice", "")
            if current_voice and current_voice in self.voice_options:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #E8F5E8, #F1F8E9); padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50; margin: 1rem 0;">
                    <h5 style="margin: 0 0 0.5rem 0; color: #2E7D32;">🎤 當前選擇: {self.voice_options[current_voice]}</h5>
                    <p style="margin: 0; color: #424242;">語音 ID: <code>{current_voice}</code></p>
                </div>
                """, unsafe_allow_html=True)
            
            # 語音試聽和控制
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重新載入語音列表", use_container_width=True):
                    self._init_voice_options()
                    st.success("✅ 語音列表已重新載入")
                    st.rerun()
            with col2:
                if st.button("🔍 檢查語音服務", use_container_width=True):
                    self._check_tts_service_status()
            
            # 語音參數調整
            st.markdown("**🎛️ 語音參數調整**")
            
            col1, col2 = st.columns(2)
            with col1:
                # 音量調整
                volume = st.slider(
                    "音量", 
                    0.0, 1.0, 
                    st.session_state.user_preferences.get("voice_volume", 0.8), 
                    0.1, 
                    key="voice_volume_slider"
                )
                st.session_state.user_preferences["voice_volume"] = volume
            with col2:
                # 速度調整
                speed = st.slider(
                    "語音速度", 
                    0.5, 2.0, 
                    st.session_state.user_preferences.get("voice_speed", 1.0), 
                    0.1, 
                    key="voice_speed_slider"
                )
                st.session_state.user_preferences["voice_speed"] = speed
            
            # 進階語音設定
            with st.expander("🔧 進階語音設定"):
                col1, col2 = st.columns(2)
                with col1:
                    pitch = st.slider(
                        "音調調整", 
                        -12, 12, 
                        0, 
                        help="調整語音的音調高低", 
                        key="voice_pitch_slider"
                    )
                    st.session_state.user_preferences["voice_pitch"] = pitch
                with col2:
                    timbre = st.slider(
                        "音色調整", 
                        0.0, 1.0, 
                        0.5, 
                        0.1, 
                        help="調整語音的音色特性", 
                        key="voice_timbre_slider"
                    )
                    st.session_state.user_preferences["voice_timbre"] = timbre
            
            # 語音狀態檢查
            if st.button("🔍 檢查語音服務狀態", use_container_width=True):
                self._check_tts_service_status()
    
    def play_voice_sample(self, voice_id: str):
        """播放語音樣本"""
        try:
            # 這裡會調用 TTS 服務播放樣本
            sample_text = "您好，這是語音樣本測試。"
            result = self.tts_service.generate_speech(sample_text, voice_id)
            
            if result and result.get("success"):
                st.success(f"✅ 語音樣本播放成功")
                # 這裡可以添加音訊播放功能
            else:
                st.error(f"❌ 語音樣本播放失敗: {result.get('error', '未知錯誤')}")
        except Exception as e:
            st.error(f"❌ 語音樣本播放錯誤: {str(e)}")
    
    def _init_voice_options(self):
        """初始化語音選項"""
        try:
            # 這裡會從 TTS 服務獲取語音列表
            voices = self.tts_service.get_voice_list()
            if voices:
                self.voice_options = {voice["id"]: voice["name"] for voice in voices}
                st.success("✅ 語音列表更新成功")
            else:
                st.warning("⚠️ 無法獲取語音列表，使用預設選項")
        except Exception as e:
            st.error(f"❌ 初始化語音選項失敗: {str(e)}")
    
    def _check_tts_service_status(self):
        """檢查 TTS 服務狀態"""
        try:
            status = self.tts_service.check_service_status()
            if status["status"] == "healthy":
                st.success("🎤 TTS 服務: 正常運行")
            else:
                st.error(f"🎤 TTS 服務: {status.get('error', '連接失敗')}")
        except Exception as e:
            st.error(f"❌ 檢查 TTS 服務狀態失敗: {str(e)}")
    
    def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """獲取語音資訊"""
        voice_info_map = {
            "podri": {
                "name": "Podri (智能男聲)",
                "description": "智能男聲，適合一般對話和日常交流",
                "gender": "male",
                "language": "zh-TW",
                "style": "自然親切",
                "best_for": "一般對話、客服、導覽"
            },
            "podria": {
                "name": "Podria (溫柔女聲)",
                "description": "溫柔甜美的女聲，適合日常對話和情感表達",
                "gender": "female",
                "language": "zh-TW",
                "style": "溫柔甜美",
                "best_for": "日常對話、情感內容、兒童內容"
            },
            "podrick": {
                "name": "Podrick (穩重男聲)",
                "description": "穩重成熟的男聲，適合專業內容和正式場合",
                "gender": "male",
                "language": "zh-TW",
                "style": "穩重專業",
                "best_for": "專業內容、新聞播報、教育內容"
            },
            "podlisa": {
                "name": "Podlisa (活潑女聲)",
                "description": "活潑開朗的女聲，適合娛樂內容和輕鬆話題",
                "gender": "female",
                "language": "zh-TW",
                "style": "活潑開朗",
                "best_for": "娛樂內容、輕鬆話題、活動主持"
            },
            "podvid": {
                "name": "Podvid (專業男聲)",
                "description": "專業權威的男聲，適合新聞播報和正式場合",
                "gender": "male",
                "language": "zh-TW",
                "style": "專業權威",
                "best_for": "新聞播報、正式場合、權威內容"
            }
        }
        return voice_info_map.get(voice_id, {}) 