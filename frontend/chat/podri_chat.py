#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri 智能聊天對話框
整合 RAG 雙代理系統、TTS 語音合成、STT 語音識別
"""

import streamlit as st
import asyncio
import aiohttp
import json
import base64
import io
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import os

# 匯入自定義模組
try:
    from utils.api_key_manager import APIType, APIKeyManager
    from services.minio_audio_service import MinIOAudioService
    from services.intelligent_audio_search import IntelligentAudioSearch
    from services.service_manager import ServiceManager
    from services.intelligent_processor import IntelligentProcessor
    from services.voice_recorder import VoiceRecorder

    # 創建實例
    api_manager = APIKeyManager()
    minio_audio_service = MinIOAudioService()
    intelligent_audio_search = IntelligentAudioSearch()
    service_manager = ServiceManager()
    intelligent_processor = IntelligentProcessor()
except ImportError:
    # 如果模組不存在，建立空的替代類別
    class APIType:
        OPENAI = "openai"
        GOOGLE_SEARCH = "google_search"
        GEMINI = "gemini"
        ANTHROPIC = "anthropic"
        OLLAMA = "ollama"

    class APIKeyManager:
        def get_api_key(self, api_type):
            return None
        def update_api_key(self, api_type, api_key):
            pass
        def get_best_api_for_query(self, query):
            return None
        def get_api_status_summary(self):
            return {}

    class MinIOAudioService:
        async def search_audio_files(self, query, category=None):
            return []
        async def test_connection(self):
            return False

    class IntelligentAudioSearch:
        def analyze_content(self, text):
            return {"confidence": 0.0}
        async def search_related_audio(self, text, minio_service=None):
            return []
        def get_search_suggestions(self, text):
            return []

    class ServiceManager:
        async def check_service_health(self, service_name):
            return None
        async def get_all_services_status(self):
            return {}

    class IntelligentProcessor:
        def process_search_results(self, results, query, max_results=10):
            return []

    # 創建實例
    api_manager = APIKeyManager()
    minio_audio_service = MinIOAudioService()
    intelligent_audio_search = IntelligentAudioSearch()
    service_manager = ServiceManager()
    intelligent_processor = IntelligentProcessor()

# 設定頁面配置
st.set_page_config(
    page_title="Podri 智能助理",
    page_icon="🦊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式 - 奶茶色系搭配大地色系
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

    /* 側邊欄樣式 */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--milk-tea) 0%, var(--dark-milk-tea) 100%);
        border-right: 2px solid var(--earth-brown);
    }

    /* 標題樣式 */
    .main-header {
        background: linear-gradient(90deg, var(--accent-gold), var(--light-earth));
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 聊天氣泡樣式 */
    .chat-bubble {
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
    }

    .user-bubble {
        background: linear-gradient(135deg, var(--accent-gold), var(--light-earth));
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }

    .bot-bubble {
        background: linear-gradient(135deg, var(--milk-tea), var(--warm-beige));
        color: var(--earth-brown);
        margin-right: auto;
        border-bottom-left-radius: 5px;
        border: 1px solid var(--dark-milk-tea);
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

    /* API 狀態指示器 */
    .api-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }

    .api-status.success {
        background: #E8F5E8;
        border-left: 4px solid #4CAF50;
        color: #2E7D32;
    }

    .api-status.error {
        background: #FFEBEE;
        border-left: 4px solid #F44336;
        color: #C62828;
    }

    .api-status.warning {
        background: #FFF3E0;
        border-left: 4px solid #FF9800;
        color: #E65100;
    }
</style>
""", unsafe_allow_html=True)

class PodriChatApp:
    """Podri 聊天應用程式類別"""

    def __init__(self):
        """初始化聊天應用程式"""
        # API 端點配置 - 支援本地開發和容器環境
        self.rag_url = "http://localhost:8004"  # 本地開發
        self.tts_url = "http://localhost:8502"  # 本地開發 - 修正為正確的 TTS 端口
        self.stt_url = "http://localhost:8001"  # 本地開發

        # K8s 環境的服務 URL（使用 NodePort）
        self.k8s_rag_url = "http://192.168.32.56:30806"  # K8s NodePort 服務 - RAG Pipeline
        self.k8s_tts_url = "http://192.168.32.56:30852"  # K8s NodePort 服務 - TTS 服務
        self.k8s_stt_url = "http://192.168.32.56:30804"  # K8s NodePort 服務 - STT 服務

        # 容器環境的備用 URL（如果本地連接失敗）
        self.container_rag_url = "http://rag-pipeline-service:8004"  # 容器服務名稱
        self.container_tts_url = "http://tts-service:8502"  # 容器服務名稱 - 修正為正確的 TTS 端口
        self.container_stt_url = "http://stt-service:8001"  # 容器服務名稱

        # 語音選項 - 動態從 TTS 服務獲取
        self.voice_options = {}
        self.voice_categories = {}

        # 初始化語音選項
        self._init_voice_options()

        # 初始化語音錄製器
        self.voice_recorder = VoiceRecorder(self.stt_url)

        # 初始化會話狀態
        self._init_session_state()

    def _init_voice_options(self):
        """動態初始化語音選項 - 從 TTS 服務獲取"""
        try:
            import requests

            # 嘗試從 TTS 服務獲取語音列表
            tts_endpoints = [
                self.k8s_tts_url,      # K8s NodePort 服務
                self.tts_url,          # 本地開發
                self.container_tts_url # 容器環境
            ]

            for endpoint in tts_endpoints:
                try:
                    response = requests.get(f"{endpoint}/voices", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        # 清空現有選項
                        self.voice_options = {}
                        self.voice_categories = {"Edge TTS 語音": []}

                        # 處理語音列表 - 支援兩種格式
                        if data.get("成功") and data.get("語音列表"):
                            # 格式1: {"成功": true, "語音列表": [...]}
                            voices = data["語音列表"]
                        elif data.get("edge_tts"):
                            # 格式2: {"edge_tts": [...]}
                            voices = data["edge_tts"]
                        else:
                            voices = []

                        # 只處理 Edge TTS 語音
                        for voice in voices:
                            voice_id = voice.get("id", "")
                            voice_name = voice.get("name", "")
                            voice_type = voice.get("type", "")

                            # 只保留 Edge TTS 語音
                            if voice_id and voice_name and voice_type == "edge_tts":
                                self.voice_options[voice_id] = voice_name
                                self.voice_categories["Edge TTS 語音"].append(voice_id)

                            print(f"✅ 成功從 {endpoint} 獲取 {len(self.voice_options)} 個 Edge TTS 語音選項")
                            return

                except Exception as e:
                    print(f"⚠️ 無法從 {endpoint} 獲取語音列表: {str(e)}")
                    continue

            # 如果所有服務都失敗，使用預設語音選項
            print("⚠️ 無法從 TTS 服務獲取語音列表，使用預設選項")
            self.voice_options = {
                "zh-TW-HsiaoChenNeural": "Podria (溫柔女聲)",
                "zh-TW-YunJheNeural": "Podrick (穩重男聲)",
                "zh-TW-HanHanNeural": "Podlisa (活潑女聲)",
                "zh-TW-ZhiYuanNeural": "Podvid (專業男聲)"
            }
            self.voice_categories = {
                "Edge TTS 語音": ["zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-TW-HanHanNeural", "zh-TW-ZhiYuanNeural"]
            }

        except ImportError:
            print("❌ 缺少 requests 模組，使用預設語音選項")
            self.voice_options = {
                "zh-TW-HsiaoChenNeural": "Podria (溫柔女聲)",
                "zh-TW-YunJheNeural": "Podrick (穩重男聲)",
                "zh-TW-HanHanNeural": "Podlisa (活潑女聲)",
                "zh-TW-ZhiYuanNeural": "Podvid (專業男聲)"
            }
            self.voice_categories = {
                "Edge TTS 語音": ["zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-TW-HanHanNeural", "zh-TW-ZhiYuanNeural"]
            }
        except Exception as e:
            print(f"❌ 初始化語音選項失敗: {str(e)}")
            # 使用預設選項
            self.voice_options = {
                "zh-TW-HsiaoChenNeural": "Podria (溫柔女聲)",
                "zh-TW-YunJheNeural": "Podrick (穩重男聲)",
                "zh-TW-HanHanNeural": "Podlisa (活潑女聲)",
                "zh-TW-ZhiYuanNeural": "Podvid (專業男聲)"
            }
            self.voice_categories = {
                "Edge TTS 語音": ["zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-TW-HanHanNeural", "zh-TW-ZhiYuanNeural"]
            }

    def _init_session_state(self):
        """初始化會話狀態"""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "current_session" not in st.session_state:
            st.session_state.current_session = {
                "session_id": f"session_{int(time.time())}",
                "start_time": datetime.now(),
                "message_count": 0,
                "voice_count": 0,
                "music_count": 0
            }

        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {
                "voice_enabled": True,
                "selected_voice": "zh-TW-HsiaoChenNeural",
                "voice_volume": 0.8,
                "voice_speed": 1.0,
                "music_enabled": False
            }

        # 新增用戶驗證相關狀態
        if "current_user_id" not in st.session_state:
            st.session_state.current_user_id = ""

        if "is_guest" not in st.session_state:
            st.session_state.is_guest = True

        if "user_info" not in st.session_state:
            st.session_state.user_info = {}

        if "api_keys" not in st.session_state:
            st.session_state.api_keys = {
                "openai": "",
                "google_search": "",
                "gemini": "",
                "anthropic": ""
            }

    def render_sidebar(self):
        """渲染側邊欄"""
        with st.sidebar:
            # 回到主頁按鈕 - 放在最上方
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

            # API Key 管理 - 放在最上方
            st.subheader("🔑 API Key 管理")

            # OpenAI API Key
            openai_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.user_preferences.get("openai_key", ""),
                type="password",
                help="輸入您的 OpenAI API Key",
                key="openai_key_input"
            )
            if openai_key != api_manager.get_api_key(APIType.OPENAI):
                api_manager.update_api_key(APIType.OPENAI, openai_key)

            # Google Search API Key
            google_key = st.text_input(
                "Google Search API Key",
                value=st.session_state.user_preferences.get("google_key", ""),
                type="password",
                help="輸入您的 Google Search API Key",
                key="google_key_input"
            )
            if google_key != api_manager.get_api_key(APIType.GOOGLE_SEARCH):
                api_manager.update_api_key(APIType.GOOGLE_SEARCH, google_key)

            # Gemini API Key
            gemini_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.user_preferences.get("gemini_key", ""),
                type="password",
                help="輸入您的 Gemini API Key",
                key="gemini_key_input"
            )
            if gemini_key != api_manager.get_api_key(APIType.GEMINI):
                api_manager.update_api_key(APIType.GEMINI, gemini_key)

            # Anthropic API Key
            anthropic_key = st.text_input(
                "Anthropic API Key",
                value=st.session_state.user_preferences.get("anthropic_key", ""),
                type="password",
                help="輸入您的 Anthropic API Key",
                key="anthropic_key_input"
            )
            if anthropic_key != api_manager.get_api_key(APIType.ANTHROPIC):
                api_manager.update_api_key(APIType.ANTHROPIC, anthropic_key)

            # 測試 API 連接
            if st.button("🧪 測試 API 連接", use_container_width=True):
                with st.spinner("測試 API 連接中..."):
                    self._test_all_apis()

            # 顯示 API 狀態
            self._render_api_status()

            # 服務狀態檢查
            st.markdown("---")
            st.subheader("🔧 服務狀態")

            # 檢查 TTS 服務狀態
            tts_status = self._check_tts_service_status()
            if tts_status["status"] == "healthy":
                st.success("🎤 TTS 服務: 正常運行")
            else:
                st.error(f"🎤 TTS 服務: {tts_status.get('error', '連接失敗')}")

            # 檢查 RAG 服務狀態
            rag_status = self._check_rag_service_status()
            if rag_status["status"] == "healthy":
                st.success("🧠 RAG 服務: 正常運行")
            else:
                st.warning(f"🧠 RAG 服務: 維護中 ({rag_status.get('error', '連接失敗')})")
                st.info("💡 RAG 服務正在重新部署，請稍後再試")

            # 顯示 RAG 反饋統計
            if "rag_feedback_history" in st.session_state and st.session_state.rag_feedback_history:
                st.markdown("---")
                st.subheader("📊 RAG 反饋統計")

                feedback_history = st.session_state.rag_feedback_history
                total_feedback = len(feedback_history)
                positive_feedback = sum(1 for f in feedback_history if f["feedback"] == 1)
                negative_feedback = total_feedback - positive_feedback

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("👍 滿意", positive_feedback)
                with col2:
                    st.metric("👎 不滿意", negative_feedback)

                if total_feedback > 0:
                    satisfaction_rate = (positive_feedback / total_feedback) * 100
                    st.metric("滿意度", f"{satisfaction_rate:.1f}%")

                # 顯示最近的反饋
                with st.expander("📝 最近反饋"):
                    for i, feedback in enumerate(feedback_history[-5:]):  # 顯示最近5個
                        feedback_time = datetime.fromtimestamp(feedback["timestamp"]).strftime("%H:%M")
                        feedback_icon = "👍" if feedback["feedback"] == 1 else "👎"
                        st.markdown(f"{feedback_icon} **{feedback_time}** - {feedback['message'][:30]}...")

            st.markdown("---")

            # TTS 語音設定
            st.subheader("🎤 TTS 語音設定")

            # 語音開關
            voice_enabled = st.checkbox("啟用語音回答", value=st.session_state.user_preferences["voice_enabled"], key="voice_enabled_checkbox")
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
                    volume = st.slider("音量", 0.0, 1.0, st.session_state.user_preferences["voice_volume"], 0.1, key="voice_volume_slider")
                    st.session_state.user_preferences["voice_volume"] = volume

                with col2:
                    # 速度調整
                    speed = st.slider("語音速度", 0.5, 2.0, st.session_state.user_preferences["voice_speed"], 0.1, key="voice_speed_slider")
                    st.session_state.user_preferences["voice_speed"] = speed

                # 進階語音設定
                with st.expander("🔧 進階語音設定"):
                    col1, col2 = st.columns(2)
                    with col1:
                        pitch = st.slider("音調調整", -12, 12, 0, help="調整語音的音調高低", key="voice_pitch_slider")
                        st.session_state.user_preferences["voice_pitch"] = pitch

                    with col2:
                        timbre = st.slider("音色調整", 0.0, 1.0, 0.5, 0.1, help="調整語音的音色特性", key="voice_timbre_slider")
                        st.session_state.user_preferences["voice_timbre"] = timbre

                # 語音狀態檢查
                if st.button("🔍 檢查語音服務狀態", use_container_width=True):
                    self._check_tts_service_status()

            st.markdown("---")

            # 熱門推薦
            st.subheader("🔥 熱門推薦")
            self.render_popular_recommendations()

            st.markdown("---")

            # 每日聲音小卡
            st.subheader("🎵 每日聲音小卡")
            self.render_daily_voice_card()

            st.markdown("---")

            # 清除對話
            if st.button("🗑️ 清除對話紀錄", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    def _test_all_apis(self):
        """測試所有 API 連接"""
        async def test_apis():
            tasks = []
            for api_type in APIType:
                if api_manager.get_api_key(api_type):
                    tasks.append(api_manager.test_api_connection(api_type))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        st.error(f"API 測試失敗: {str(result)}")
                    else:
                        if result.get("available"):
                            st.success(f"✅ {list(APIType)[i].value} 連接正常")
                        else:
                            st.error(f"❌ {list(APIType)[i].value}: {result.get('error', '未知錯誤')}")
            else:
                st.warning("⚠️ 沒有設定任何 API Key")

        # 執行非同步測試
        asyncio.run(test_apis())

    def _render_api_status(self):
        """渲染 API 狀態"""
        api_status = api_manager.get_api_status_summary()
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

    def render_popular_recommendations(self):
        """渲染熱門推薦"""
        recommendations = [
            {"title": "股癌", "category": "商業", "description": "晦澀金融投資知識直白講"},
            {"title": "天下學習", "category": "教育", "description": "向最厲害的人學習"}
        ]

        for rec in recommendations:
            with st.expander(f"📻 {rec['title']} ({rec['category']})"):
                st.write(rec['description'])
                if st.button(f"試聽 {rec['title']}", key=f"listen_{rec['title']}"):
                    self.play_podcast_sample(rec['title'])

    def render_daily_voice_card(self):
        """渲染每日聲音小卡"""
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
                if self.validate_user_id(user_id_input.strip()):
                    st.session_state["current_user_id"] = user_id_input.strip()
                    st.session_state["is_guest"] = False
                    st.success("✅ 用戶驗證成功！")
                    st.rerun()
                else:
                    st.session_state["is_guest"] = True
                    st.warning("❌ 用戶 ID 驗證失敗，以訪客模式登入")
                    st.rerun()
            else:
                st.warning("請輸入用戶 ID")

        # 顯示當前用戶狀態
        if st.session_state.get("current_user_id"):
            st.success(f"✅ 已登入用戶: {st.session_state.current_user_id}")
        else:
            st.info("👤 訪客模式")

        st.markdown("---")

        # 3. API Key 管理區域
        st.markdown("#### 🔑 API Key 管理")

        # OpenAI API Key
        openai_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.get("api_keys", {}).get("openai", ""),
            type="password",
            help="輸入您的 OpenAI API Key"
        )
        if openai_key != st.session_state.get("api_keys", {}).get("openai", ""):
            if "api_keys" not in st.session_state:
                st.session_state["api_keys"] = {}
            st.session_state["api_keys"]["openai"] = openai_key

        # Google Search API Key
        google_key = st.text_input(
            "Google Search API Key",
            value=st.session_state.get("api_keys", {}).get("google_search", ""),
            type="password",
            help="輸入您的 Google Search API Key"
        )
        if google_key != st.session_state.get("api_keys", {}).get("google_search", ""):
            if "api_keys" not in st.session_state:
                st.session_state["api_keys"] = {}
            st.session_state["api_keys"]["google_search"] = google_key

        # Gemini API Key
        gemini_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("api_keys", {}).get("gemini", ""),
            type="password",
            help="輸入您的 Gemini API Key"
        )
        if gemini_key != st.session_state.get("api_keys", {}).get("gemini", ""):
            if "api_keys" not in st.session_state:
                st.session_state["api_keys"] = {}
            st.session_state["api_keys"]["gemini"] = gemini_key

        # Anthropic API Key
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=st.session_state.get("api_keys", {}).get("anthropic", ""),
            type="password",
            help="輸入您的 Anthropic API Key"
        )
        if anthropic_key != st.session_state.get("api_keys", {}).get("anthropic", ""):
            if "api_keys" not in st.session_state:
                st.session_state["api_keys"] = {}
            st.session_state["api_keys"]["anthropic"] = anthropic_key

        # API Key 狀態顯示
        api_status = self._check_api_keys_status()
        if api_status:
            st.markdown("**API Key 狀態：**")
            for api_name, status in api_status.items():
                if status:
                    st.success(f"✅ {api_name}")
                else:
                    st.warning(f"❌ {api_name}")

        st.markdown("---")

        # 4. 語音設定區域
        st.markdown("#### 🎤 語音設定")

        # 語音回覆開關
        voice_reply = st.checkbox(
            "啟用語音回覆",
            value=st.session_state.user_preferences.get("voice_reply", True),
            help="是否啟用語音回覆功能"
        )
        st.session_state.user_preferences["voice_reply"] = voice_reply

        # TTS 語音選擇
        st.markdown("**選擇語音：**")
        voice_options = {
            "podri": "Podri (智能男聲)",
            "podria": "Podria (溫柔女聲)",
            "podrick": "Podrick (穩重男聲)",
            "podlisa": "Podlisa (活潑女聲)",
            "podvid": "Podvid (專業男聲)"
        }

        selected_voice = st.selectbox(
            "TTS 語音",
            options=list(voice_options.keys()),
            format_func=lambda x: voice_options[x],
            index=0,
            key="voice_selection"
        )
        st.session_state.user_preferences["selected_voice"] = selected_voice

        # 語速調整 (0.5x - 2.0x)
        raw_speed = st.session_state.user_preferences.get("voice_speed", 1.0)
        if isinstance(raw_speed, list):
            raw_speed = raw_speed[0] if raw_speed else 1.0
        voice_speed = st.slider(
            "語速調整",
            min_value=0.5,
            max_value=2.0,
            value=float(raw_speed),
            step=0.1,
            help="調整語音播放速度 (0.5x - 2.0x)"
        )
        st.session_state.user_preferences["voice_speed"] = voice_speed

        # 音量調整 (0-100%)
        raw_volume = st.session_state.user_preferences.get("voice_volume", 80)
        if isinstance(raw_volume, list):
            raw_volume = raw_volume[0] if raw_volume else 80
        voice_volume = st.slider(
            "音量調整",
            min_value=0,
            max_value=100,
            value=int(raw_volume),
            step=5,
            help="調整語音音量 (0-100%)"
        )
        st.session_state.user_preferences["voice_volume"] = voice_volume

        # 語音試聽功能
        st.markdown("---")
        st.markdown("#### 🎵 語音試聽")
        preview_text = st.text_area(
            "試聽文字",
            value="您好，我是 Podri 智能助理，很高興為您服務！",
            height=80,
            key="preview_text"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 試聽語音", use_container_width=True):
                if preview_text.strip():
                    with st.spinner("正在生成試聽語音..."):
                        # 這裡調用 TTS 服務生成試聽語音
                        st.info("試聽功能開發中...")
                else:
                    st.warning("請輸入試聽文字")

        with col2:
            if st.button("🔄 重置設定", use_container_width=True):
                st.session_state.user_preferences = {
                    "voice_reply": True,
                    "selected_voice": "zh-TW-HsiaoChenNeural",
                    "voice_speed": 1.0,
                    "voice_volume": 80
                }
                st.success("設定已重置")
                st.rerun()

        # 顯示當前設定
        st.markdown("---")
        st.markdown("#### ⚙️ 當前設定")
        st.info(f"""
        **語音回覆:** {'✅ 啟用' if voice_reply else '❌ 停用'}
        **選擇語音:** {voice_options[selected_voice]}
        **語速:** {voice_speed}x
        **音量:** {voice_volume}%
        """)

    def validate_user_id(self, user_id: str) -> bool:
        """驗證用戶 ID 是否存在於資料庫中"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # 資料庫連接配置
            db_config = {
                'host': 'postgres',  # K8s 服務名稱
                'port': 5432,
                'database': 'podcast',
                'user': 'bdse37',
                'password': '111111'
            }

            # 連接到資料庫
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 查詢用戶是否存在
            cursor.execute(
                "SELECT user_id, username, email, is_active FROM users WHERE user_id = %s",
                (user_id,)
            )

            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and user['is_active']:
                # 儲存用戶資訊到 session
                st.session_state["user_info"] = {
                    "user_id": user['user_id'],
                    "username": user['username'],
                    "email": user['email']
                }
                return True
            else:
                return False

        except Exception as e:
            st.error(f"資料庫連接錯誤: {str(e)}")
            return False

    def _check_api_keys_status(self) -> dict:
        """檢查 API Key 狀態"""
        api_keys = st.session_state.get("api_keys", {})
        status = {}

        # 檢查 OpenAI API Key
        if api_keys.get("openai"):
            status["OpenAI"] = True
        else:
            status["OpenAI"] = False

        # 檢查 Google Search API Key
        if api_keys.get("google_search"):
            status["Google Search"] = True
        else:
            status["Google Search"] = False

        # 檢查 Gemini API Key
        if api_keys.get("gemini"):
            status["Gemini"] = True
        else:
            status["Gemini"] = False

        # 檢查 Anthropic API Key
        if api_keys.get("anthropic"):
            status["Anthropic"] = True
        else:
            status["Anthropic"] = False

        return status

    def generate_random_user_id(self) -> str:
        """生成隨機用戶 ID"""
        import random
        import string

        # 生成 8 位數字 ID
        user_id = ''.join(random.choices(string.digits, k=8))
        return user_id

    def save_user_session(self, user_id: str, category: str, program: str) -> bool:
        """儲存用戶會話資訊到資料庫"""
        try:
            import psycopg2
            from datetime import datetime

            # 資料庫連接配置
            db_config = {
                'host': 'postgres',
                'port': 5432,
                'database': 'podcast',
                'user': 'bdse37',
                'password': '111111'
            }

            # 連接到資料庫
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # 插入或更新用戶會話資訊
            cursor.execute("""
                INSERT INTO system_event_log (user_id, event_type, source_service, event_detail, severity, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                'user_session_created',
                'frontend',
                f'Category: {category}, Program: {program}',
                'info',
                datetime.now()
            ))

            conn.commit()
            cursor.close()
            conn.close()

            return True

        except Exception as e:
            st.error(f"儲存用戶會話失敗: {str(e)}")
            return False

    def render_main_chat_interface(self):
        """渲染主要聊天介面"""
        st.markdown("""
        <div class="main-header">
            <h2>🦊 Podri 智能助理</h2>
            <p>您的個人化 Podcast 推薦與音樂生成助手</p>
        </div>
        """, unsafe_allow_html=True)

        # 聊天對話框
        self.render_chat_messages()

        # 輸入區域
        self.render_input_area()

    def render_chat_messages(self):
        """渲染聊天訊息"""
        st.markdown("""
        <div class="chat-container">
        """, unsafe_allow_html=True)

        # 顯示聊天歷史
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
                    <div class="chat-bubble user-bubble">
                        <div style="display: flex; align-items: center;">
                            <span>{message['content']}</span>
                            <img src="assets/images/user_avatar.png" style="width: 30px; height: 30px; margin-left: 10px; border-radius: 50%;">
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                    <div class="chat-bubble bot-bubble">
                        <div style="display: flex; align-items: center;">
                            <img src="assets/images/bot_avatar.png" style="width: 30px; height: 30px; margin-right: 10px; border-radius: 50%;">
                            <span>{message['content']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def render_input_area(self):
        """渲染輸入區域"""
        st.markdown("---")

        # 輸入方式選擇
        input_method = st.radio(
            "選擇輸入方式",
            ["文字輸入", "語音輸入"],
            horizontal=True
        )

        if input_method == "文字輸入":
            # 文字輸入
            user_input = st.text_input(
                "輸入您的問題...",
                key="user_input_text",
                placeholder="例如：推薦一些科技類的 Podcast..."
            )

            col1, col2 = st.columns([4, 1])

            with col1:
                if st.button("💬 發送", use_container_width=True):
                    if user_input.strip():
                        self.process_user_message(user_input)
                        st.rerun()

            with col2:
                if st.button("🎤 語音", use_container_width=True):
                    st.info("語音輸入功能開發中...")
        else:
            # 語音輸入 - 使用語音錄製器
            transcribed_text = self.voice_recorder.render_voice_recorder()

            if transcribed_text:
                # 顯示轉錄的文字並提供發送按鈕
                st.markdown(f"**轉錄結果:** {transcribed_text}")

                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("💬 發送轉錄文字", use_container_width=True):
                        self.process_user_message(transcribed_text)
                        st.rerun()

                with col2:
                    if st.button("🔄 重新錄音", use_container_width=True):
                        st.rerun()

    async def send_message_to_rag(self, message: str) -> Dict[str, Any]:
        """發送訊息到 RAG 系統"""
        # 優先使用 K8s 環境的 RAG 服務，然後是容器環境，最後是本地開發
        rag_urls = [
            self.k8s_rag_url,      # K8s 服務名稱
            self.container_rag_url, # 容器環境
            self.rag_url           # 本地開發
        ]

        for rag_url in rag_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    # 先測試連接
                    async with session.get(f"{rag_url}/health", timeout=5) as health_response:
                        if health_response.status != 200:
                            st.warning(f"RAG 服務健康檢查失敗: {rag_url} (狀態: {health_response.status})")
                            continue

                    # RAG pipeline 使用 POST 請求，需要 JSON 格式的請求體
                    payload = {
                        "query": message,
                        "user_id": st.session_state.current_user_id or "guest",
                        "session_id": st.session_state.current_session["session_id"],
                        "category_filter": None,  # 可選：商業、教育
                        "use_advanced_features": True
                    }

                    async with session.post(
                        f"{rag_url}/api/v1/query",
                        json=payload,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            st.success(f"✅ RAG 系統回應成功 (使用服務: {rag_url})")

                            # 顯示 RAG 回應
                            rag_response = data.get("response", "")
                            recommendations = data.get("recommendations", [])
                            confidence = data.get("confidence", 0.0)

                            # 顯示回應內容
                            st.markdown(f"""
                            <div style="background: #E8F5E8; padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50;">
                                <h4>🤖 RAG 智能回應</h4>
                                <p>{rag_response}</p>
                                <small>信心度: {confidence:.2f}</small>
                            </div>
                            """, unsafe_allow_html=True)

                            # 如果有推薦內容，顯示它們
                            if recommendations:
                                st.markdown("**📚 相關推薦:**")
                                for i, rec in enumerate(recommendations[:3]):  # 只顯示前3個推薦
                                    st.markdown(f"• {rec}")

                            # 添加用戶反饋機制
                            st.markdown("---")
                            st.markdown("**💭 這個回答對您有幫助嗎？**")

                            # 使用 st.feedback 組件
                            feedback_result = st.feedback(
                                options="thumbs",
                                key=f"rag_feedback_{int(time.time())}",
                                help="請為這個回答評分"
                            )

                            # 處理反饋結果
                            if feedback_result is not None:
                                feedback_mapping = ["👎 不滿意", "👍 滿意"]
                                feedback_text = feedback_mapping[feedback_result]

                                # 儲存反饋到會話狀態
                                if "rag_feedback_history" not in st.session_state:
                                    st.session_state.rag_feedback_history = []

                                feedback_data = {
                                    "timestamp": time.time(),
                                    "message": message,
                                    "response": rag_response,
                                    "feedback": feedback_result,
                                    "feedback_text": feedback_text,
                                    "confidence": confidence,
                                    "service_url": rag_url
                                }
                                st.session_state.rag_feedback_history.append(feedback_data)

                                # 顯示反饋確認
                                if feedback_result == 1:
                                    st.success("🎉 謝謝您的正面反饋！我們會繼續努力提供更好的服務。")
                                else:
                                    st.info("📝 謝謝您的反饋！我們會改進回答品質。")

                                # 可選：提供詳細反饋輸入
                                if feedback_result == 0:  # 不滿意時
                                    detailed_feedback = st.text_area(
                                        "請告訴我們如何改進（可選）:",
                                        placeholder="例如：回答不夠詳細、資訊不準確、格式不清晰...",
                                        key=f"detailed_feedback_{int(time.time())}"
                                    )
                                    if detailed_feedback:
                                        feedback_data["detailed_feedback"] = detailed_feedback

                            return {
                                "success": True,
                                "response": rag_response,
                                "recommendations": recommendations,
                                "confidence": confidence
                            }
                        else:
                            st.warning(f"RAG 服務回應錯誤: {rag_url} (狀態: {response.status})")
                            try:
                                error_detail = await response.json()
                                st.warning(f"錯誤詳情: {error_detail}")
                            except:
                                st.warning(f"錯誤內容: {await response.text()}")
                            continue

            except aiohttp.ClientConnectorError:
                st.warning(f"無法連接到 RAG 服務: {rag_url}")
                continue
            except asyncio.TimeoutError:
                st.warning(f"RAG 服務連接超時: {rag_url}")
                continue
            except Exception as e:
                st.warning(f"RAG 服務錯誤: {rag_url} - {str(e)}")
                continue

        # 如果所有 RAG 服務都失敗，返回錯誤
        return {
            "success": False,
            "error": "所有 RAG 服務都無法連接"
        }

    async def generate_speech(self, text: str, voice: str) -> Optional[Dict[str, Any]]:
        """生成語音 - 返回包含音訊資料和元資料的字典"""
        try:
            # 優先使用 K8s 環境的 TTS 服務，然後是本地和容器環境
            tts_urls = [
                self.k8s_tts_url,      # K8s NodePort 服務
                self.tts_url,          # 本地開發
                self.container_tts_url # 容器環境
            ]

            for tts_url in tts_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        # 先測試連接
                        async with session.get(f"{tts_url}/health", timeout=5) as health_response:
                            if health_response.status != 200:
                                st.warning(f"TTS 服務健康檢查失敗: {tts_url} (狀態: {health_response.status})")
                                continue

                        # 發送語音生成請求 - 使用 TTS 服務的正確端點和參數格式
                        payload = {
                            "text": text,
                            "voice": voice,
                            "speed": st.session_state.user_preferences["voice_speed"],
                            "volume": st.session_state.user_preferences["voice_volume"],
                            "method": "edge_tts"  # 指定使用 Edge TTS
                        }

                        async with session.post(
                            f"{tts_url}/generate_speech",  # 使用正確的 TTS API 端點
                            json=payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                audio_data = await response.read()

                                # 計算音訊長度（估算）
                                estimated_duration = self._estimate_audio_duration(audio_data, text)

                                # 返回包含元資料的音訊資訊
                                audio_info = {
                                    "audio_data": audio_data,
                                    "duration": estimated_duration,
                                    "text_length": len(text),
                                    "voice": voice,
                                    "service_url": tts_url,
                                    "timestamp": time.time()
                                }

                                st.success(f"✅ 語音生成成功 (使用服務: {tts_url})")
                                return audio_info
                            else:
                                st.warning(f"TTS 服務回應錯誤: {tts_url} (狀態: {response.status})")
                                try:
                                    error_detail = await response.json()
                                    st.warning(f"錯誤詳情: {error_detail}")
                                except:
                                    st.warning(f"錯誤內容: {await response.text()}")
                                continue

                except aiohttp.ClientConnectorError:
                    st.warning(f"無法連接到 TTS 服務: {tts_url}")
                    continue
                except asyncio.TimeoutError:
                    st.warning(f"TTS 服務連接超時: {tts_url}")
                    continue
                except Exception as e:
                    st.warning(f"TTS 服務錯誤: {tts_url} - {str(e)}")
                    continue

            # 如果所有 TTS 服務都失敗，顯示詳細錯誤信息
            st.error("""
            🚨 TTS 服務連接失敗

            **已嘗試的服務：**
            1. K8s NodePort 服務: http://192.168.32.56:30852
            2. 本地開發服務: http://localhost:8501
            3. 容器服務: http://tts:8501

            **可能的原因：**
            1. TTS 服務未啟動
            2. 端口被佔用
            3. 防火牆阻擋
            4. K8s 服務配置問題

            **解決方案：**
            1. 檢查 TTS Pod 狀態：
               ```bash
               kubectl get pods -n podwise | grep tts
               ```
            2. 檢查 TTS 服務狀態：
               ```bash
               kubectl get services -n podwise | grep tts
               ```
            3. 檢查 TTS 服務日誌：
               ```bash
               kubectl logs -n podwise <tts-pod-name>
               ```
            4. 確認 NodePort 端口 30852 是否可訪問
            5. 測試 TTS 服務：
               ```bash
               curl -X POST http://192.168.32.56:30852/synthesize \\
                 -H "Content-Type: application/json" \\
                 -d '{"文字": "測試", "語音": "zh-TW-HsiaoChenNeural"}' \\
                 -o test.wav
               ```
            """)
            return None

        except Exception as e:
            st.error(f"語音生成錯誤: {str(e)}")
            return None

    def _estimate_audio_duration(self, audio_data: bytes, text: str) -> float:
        """估算音訊長度"""
        try:
            # 基於文字長度和語速估算
            base_duration_per_char = 0.1  # 每個字元約 0.1 秒
            speed_factor = st.session_state.user_preferences.get("voice_speed", 1.0)

            # 考慮標點符號的停頓
            pause_chars = "，。！？；："
            pause_duration = sum(0.3 for char in text if char in pause_chars)

            estimated_duration = (len(text) * base_duration_per_char + pause_duration) / speed_factor

            # 基於音訊檔案大小進行微調
            if len(audio_data) > 0:
                # 假設 16kHz 16-bit 單聲道，每秒約 32KB
                bytes_per_second = 32000
                file_based_duration = len(audio_data) / bytes_per_second

                # 取兩種估算的平均值
                estimated_duration = (estimated_duration + file_based_duration) / 2

            return max(estimated_duration, 0.5)  # 最少 0.5 秒

        except Exception:
            # 如果估算失敗，返回基於文字長度的預設值
            return max(len(text) * 0.1, 1.0)

    def _display_audio_player(self, audio_info: Dict[str, Any]):
        """顯示音訊播放器"""
        try:
            audio_data = audio_info["audio_data"]
            duration = audio_info["duration"]
            voice = audio_info["voice"]
            text_length = audio_info["text_length"]

            # 格式化時間顯示
            duration_str = f"{duration:.1f}秒"

            # 顯示音訊播放器
            st.audio(audio_data, format="audio/wav")

            # 顯示詳細資訊
            voice_info = self._get_voice_info(voice)
            voice_name = voice_info.get('name', '未知') if voice_info else voice

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎤 語音", voice_name)
            with col2:
                st.metric("⏱️ 時長", duration_str)
            with col3:
                st.metric("📝 字數", f"{text_length} 字")

            # 顯示語音參數
            with st.expander("🔧 語音參數"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**音量:** {st.session_state.user_preferences['voice_volume']:.1f}")
                    st.write(f"**語速:** {st.session_state.user_preferences['voice_speed']:.1f}x")
                with col2:
                    st.write(f"**服務:** {audio_info['service_url']}")
                    st.write(f"**生成時間:** {datetime.fromtimestamp(audio_info['timestamp']).strftime('%H:%M:%S')}")

        except Exception as e:
            st.error(f"音訊播放器顯示失敗: {str(e)}")
            # 回退到簡單的播放器
            st.audio(audio_info["audio_data"], format="audio/wav")

    def process_user_message(self, message: str):
        """處理用戶訊息"""
        try:
            # 添加用戶訊息到聊天歷史
            st.session_state.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now()
            })

            # 更新會話統計
            st.session_state.current_session["message_count"] += 1

            # 智能音檔搜尋 - 在處理回應前先搜尋相關音檔
            audio_search_results = []
            search_suggestions = []

            try:
                # 分析用戶訊息內容
                analysis = intelligent_audio_search.analyze_content(message)

                if analysis["confidence"] > 0.1:
                    # 顯示搜尋分析結果
                    st.info(f"🔍 檢測到相關內容，正在搜尋音檔...")

                    # 搜尋相關音檔
                    audio_search_results = asyncio.run(
                        intelligent_audio_search.search_related_audio(message, minio_audio_service)
                    )

                    # 獲取搜尋建議
                    search_suggestions = intelligent_audio_search.get_search_suggestions(message)

                    # 顯示搜尋結果
                    if audio_search_results:
                        st.success(f"🎵 找到 {len(audio_search_results)} 個相關音檔")

                        # 創建音檔選擇器
                        with st.expander("🎧 相關音檔推薦", expanded=True):
                            for i, audio in enumerate(audio_search_results):
                                col1, col2, col3 = st.columns([3, 1, 1])

                                with col1:
                                    st.markdown(f"""
                                    **{audio.get('title', audio.get('name', '未知標題'))}**
                                    - 類型: {audio.get('type', '未知')}
                                    - 類別: {audio.get('category', '未知')}
                                    - 相關度: {audio.get('relevance_score', 0):.1%}
                                    """)

                                with col2:
                                    if st.button("播放", key=f"play_audio_{i}"):
                                        st.audio(audio.get('name', ''), format='audio/wav')

                                with col3:
                                    if st.button("下載", key=f"download_audio_{i}"):
                                        st.download_button(
                                            label="下載",
                                            data=b"",  # 這裡應該是真實的音檔數據
                                            file_name=audio.get('name', 'audio.wav'),
                                            mime="audio/wav"
                                        )

                        # 顯示搜尋建議
                        if search_suggestions:
                            st.markdown("💡 **智能建議:**")
                            for suggestion in search_suggestions[:3]:  # 只顯示前3個建議
                                st.markdown(f"• {suggestion}")

                    else:
                        st.info("🔍 未找到完全匹配的音檔，但您可以嘗試以下建議:")
                        if search_suggestions:
                            for suggestion in search_suggestions[:3]:
                                st.markdown(f"• {suggestion}")

            except Exception as e:
                st.warning(f"音檔搜尋功能暫時無法使用: {str(e)}")

            # 使用智能 API 選擇
            with st.spinner("🤔 正在思考..."):
                # 調用智能 API 選擇
                response = asyncio.run(self.send_message_with_api_selection(message))

                if response.get("success"):
                    # 獲取回應內容
                    response_text = response["response"]

                    # 添加機器人回應到聊天歷史
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now(),
                        "source": response.get("source", "rag"),
                        "audio_results": len(audio_search_results) if audio_search_results else 0
                    })

                    # 如果啟用語音，生成語音
                    if st.session_state.user_preferences["voice_enabled"]:
                        voice = st.session_state.user_preferences["selected_voice"]

                        # 顯示語音生成狀態
                        with st.spinner("🎤 正在生成語音..."):
                            audio_info = asyncio.run(self.generate_speech(response_text, voice))

                            if audio_info:
                                st.session_state.current_session["voice_count"] += 1

                                # 顯示語音播放器
                                self._display_audio_player(audio_info)

                                # 顯示語音資訊
                                voice_info = self._get_voice_info(voice)
                                if voice_info:
                                    st.info(f"""
                                    🎤 **語音資訊**
                                    - 語音: {voice_info.get('name', '未知')}
                                    - 內容長度: {len(response_text)} 字元
                                    - 生成時間: {datetime.now().strftime('%H:%M:%S')}
                                    """)
                                else:
                                    st.error("❌ 語音資訊獲取失敗")
                            else:
                                st.error("❌ 語音生成失敗")
                                st.info("💡 請檢查 TTS 服務狀態或嘗試重新生成")
                else:
                    st.error(f"回應失敗: {response.get('error', '未知錯誤')}")

        except Exception as e:
            st.error(f"處理訊息失敗: {str(e)}")
            st.info("💡 請檢查服務連接狀態")

    def play_voice_sample(self, voice: str):
        """播放語音樣本"""
        try:
            # 顯示載入狀態
            with st.spinner(f"🎤 正在生成 {voice} 語音樣本..."):
                # 根據語音類型選擇不同的樣本文字
                voice_samples = {
                    "zh-TW-HsiaoChenNeural": "您好，我是 Podria，溫柔甜美的語音助手，隨時為您效勞。",
                    "zh-TW-YunJheNeural": "您好，我是 Podrick，穩重成熟的語音助手，為您提供專業服務。",
                    "zh-TW-HanHanNeural": "嗨！我是 Podlisa，活潑開朗的語音助手，讓我們一起開心聊天吧！",
                    "zh-TW-ZhiYuanNeural": "您好，我是 Podvid，專業權威的語音助手，為您播報最新資訊。"
                }

                sample_text = voice_samples.get(voice, "你好，我是智能語音助手，很高興為您服務！")

                # 使用同步方式調用 TTS 服務
                import requests

                # 嘗試從 TTS 服務生成語音
                tts_url = "http://192.168.32.56:30852"  # 直接使用 K8s NodePort

                payload = {
                    "文字": sample_text,
                    "語音": voice,
                    "音量": st.session_state.user_preferences.get("voice_volume", 0.8),
                    "語速": st.session_state.user_preferences.get("voice_speed", 1.0)
                }

                try:
                    response = requests.post(
                        f"{tts_url}/synthesize",
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        audio_data = response.content

                        # 計算音訊長度（估算）
                        estimated_duration = self._estimate_audio_duration(audio_data, sample_text)

                        # 創建音訊資訊
                        audio_info = {
                            "audio_data": audio_data,
                            "duration": estimated_duration,
                            "text_length": len(sample_text),
                            "voice": voice,
                            "service_url": tts_url,
                            "timestamp": time.time()
                        }

                        # 顯示成功訊息
                        st.success(f"✅ {voice} 語音樣本生成成功！")

                        # 顯示音訊播放器
                        self._display_audio_player(audio_info)

                        # 顯示下載按鈕
                        st.download_button(
                            label="💾 下載音檔",
                            data=audio_data,
                            file_name=f"{voice}_sample.wav",
                            mime="audio/wav",
                            use_container_width=True
                        )

                        # 更新會話統計
                        st.session_state.current_session["voice_count"] += 1

                    else:
                        st.error(f"❌ TTS 服務回應錯誤: {response.status_code}")
                        st.info(f"錯誤內容: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ 無法連接到 TTS 服務")
                    st.info("💡 請檢查 TTS 服務是否正常運行")
                except requests.exceptions.Timeout:
                    st.error("⏰ TTS 服務請求超時")
                    st.info("💡 請稍後再試")
                except Exception as e:
                    st.error(f"❌ TTS 服務錯誤: {str(e)}")
                    st.info("💡 請檢查網路連接和服務狀態")

        except Exception as e:
            st.error(f"❌ 播放語音樣本失敗: {str(e)}")
            st.info("💡 請檢查網路連接和服務狀態")

    def play_podcast_sample(self, podcast_title: str):
        """播放 Podcast 樣本"""
        st.info(f"播放 {podcast_title} 樣本")

    def show_chat_history(self):
        """顯示聊天歷史"""
        st.subheader("📚 聊天歷史")

        if not st.session_state.chat_history:
            st.info("還沒有聊天記錄")
            return

        # 建立聊天歷史 DataFrame
        history_data = []
        for msg in st.session_state.chat_history:
            history_data.append({
                "時間": msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "角色": "用戶" if msg["role"] == "user" else "Podri",
                "內容": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                "來源": msg.get("source", "未知")
            })

        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)

        # 統計資訊
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總訊息數", len(st.session_state.chat_history))
        with col2:
            user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
            st.metric("用戶訊息", user_messages)
        with col3:
            bot_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
            st.metric("Podri 回應", bot_messages)

    def show_daily_picks(self):
        """顯示每日精選"""
        st.subheader("⭐ 每日精選")

        picks = [
            {"title": "科技早餐", "category": "科技", "duration": "15分鐘", "rating": 4.8},
            {"title": "矽谷輕鬆談", "category": "商業", "duration": "25分鐘", "rating": 4.9},
            {"title": "股癌", "category": "投資", "duration": "45分鐘", "rating": 4.7}
        ]

        for pick in picks:
            with st.expander(f"🎧 {pick['title']} ({pick['category']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**時長:** {pick['duration']}")
                    st.write(f"**評分:** {'⭐' * int(pick['rating'])} {pick['rating']}")
                with col2:
                    if st.button("試聽", key=f"daily_pick_{pick['title']}"):
                        self.play_podcast_sample(pick['title'])

    def show_today_recommendations(self):
        """顯示今日推薦"""
        st.subheader("🎯 今日推薦")

        # 模擬推薦算法
        recommendations = [
            {"title": "AI 時代的職涯規劃", "confidence": 0.95, "reason": "基於您的科技興趣"},
            {"title": "投資理財入門", "confidence": 0.87, "reason": "符合您的學習需求"},
            {"title": "健康生活指南", "confidence": 0.82, "reason": "平衡工作與生活"}
        ]

        for rec in recommendations:
            st.markdown(f"""
            <div class="feature-card">
                <h5>📻 {rec['title']}</h5>
                <p>**推薦度:** {rec['confidence']:.1%}</p>
                <p>**原因:** {rec['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

    def show_usage_stats(self):
        """顯示使用統計"""
        st.subheader("📊 使用統計")

        session = st.session_state.current_session
        start_time = session["start_time"]
        duration = datetime.now() - start_time

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("會話時長", f"{duration.seconds // 60}分鐘")

        with col2:
            st.metric("訊息數量", session["message_count"])

        with col3:
            st.metric("語音生成", session["voice_count"])

        with col4:
            st.metric("音樂生成", session["music_count"])

        # 使用趨勢圖
        st.subheader("📈 使用趨勢")

        # 模擬使用數據
        hours = list(range(24))
        messages = [max(0, 10 - abs(h - 12) + 5) for h in hours]  # 模擬使用模式

        df = pd.DataFrame({
            "小時": hours,
            "訊息數": messages
        })

        fig = px.line(df, x="小時", y="訊息數", title="24小時使用趨勢")
        st.plotly_chart(fig, use_container_width=True)

    def start_voice_recording(self):
        """開始語音錄音 - 已棄用，使用 VoiceRecorder"""
        st.info("🎙️ 請使用新的語音輸入功能")

    def stop_voice_recording(self):
        """停止語音錄音 - 已棄用，使用 VoiceRecorder"""
        st.info("⏹️ 請使用新的語音輸入功能")

    # MusicGen 功能已移除
    pass

    async def send_message_with_api_selection(self, message: str) -> Dict[str, Any]:
        """根據查詢內容智能選擇 API 發送訊息，包含重試機制和智能處理"""
        try:
            # 檢查快取
            cache_key = intelligent_processor.get_cache_key(message, [])
            cached_response = intelligent_processor.get_cached_results(cache_key)
            if cached_response:
                return {
                    "success": True,
                    "response": "快取回應",
                    "results": cached_response,
                    "source": "cache"
                }

            # 選擇最適合的 API
            best_api = api_manager.get_best_api_for_query(message)

            # 嘗試向量搜尋作為優先選項
            vector_result = await self.send_vector_search_query(message)
            if vector_result["success"]:
                # 處理向量搜尋結果
                processed_results = intelligent_processor.process_search_results(
                    vector_result.get("results", []), message, max_results=5
                )

                if processed_results:
                    # 快取結果
                    intelligent_processor.cache_results(cache_key, processed_results)

                    return {
                        "success": True,
                        "response": f"找到 {len(processed_results)} 個相關的 Podcast",
                        "results": processed_results,
                        "source": "vector_search",
                        "confidence": sum(r.overall_score for r in processed_results) / len(processed_results)
                    }

            # 如果向量搜尋失敗或沒有結果，嘗試其他 API
            api_results = []

            if best_api == APIType.GOOGLE_SEARCH:
                # 使用 Google Search API
                result = await self.send_google_search_query(message)
                if result["success"]:
                    api_results.append(result)
            elif best_api == APIType.OPENAI:
                # 使用 OpenAI API
                result = await self.send_openai_query(message)
                if result["success"]:
                    api_results.append(result)
            elif best_api == APIType.ANTHROPIC:
                # 使用 Anthropic API
                result = await self.send_anthropic_query(message)
                if result["success"]:
                    api_results.append(result)
            elif best_api == APIType.GEMINI:
                # 使用 Gemini API
                result = await self.send_gemini_query(message)
                if result["success"]:
                    api_results.append(result)

            # 如果所有 API 都失敗，使用 RAG 系統
            if not api_results:
                rag_result = await self.send_message_to_rag(message)
                if rag_result["success"]:
                    api_results.append(rag_result)

            # 處理和合併結果
            if api_results:
                # 選擇最佳結果
                best_result = max(api_results, key=lambda x: x.get("confidence", 0))

                # 如果是搜尋結果，進行智能處理
                if "results" in best_result:
                    processed_results = intelligent_processor.process_search_results(
                        best_result["results"], message, max_results=5
                    )

                    # 快取結果
                    intelligent_processor.cache_results(cache_key, processed_results)

                    return {
                        "success": True,
                        "response": best_result["response"],
                        "results": processed_results,
                        "source": best_result["source"],
                        "confidence": best_result.get("confidence", 0.7)
                    }
            else:
                    # 直接回應（如 LLM 回應）
                    return best_result

            # 如果所有方法都失敗
            return {
                "success": False,
                "error": "所有 API 都無法處理您的查詢",
                "source": "fallback"
            }

        except Exception as e:
            st.error(f"API 選擇失敗: {str(e)}")
            # 回退到預設 RAG 系統
            return await self.send_message_to_rag(message)

    async def send_google_search_query(self, query: str) -> Dict[str, Any]:
        """發送 Google Search 查詢"""
        try:
            api_key = api_manager.get_api_key(APIType.GOOGLE_SEARCH)
            cse_id = os.getenv("GOOGLE_CSE_ID")

            if not api_key or not cse_id:
        return {
                    "success": False,
                    "error": "Google Search API 配置不完整，請設定 GOOGLE_API_KEY 和 GOOGLE_CSE_ID"
                }

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'q': query,
                'key': api_key,
                'cx': cse_id,
                'hl': 'zh-TW',
                'num': 5,
                'dateRestrict': 'm1'  # 限制為最近一個月
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        for item in data.get("items", []):
                            results.append({
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", ""),
                                "link": item.get("link", ""),
                                "source": "google_search"
                            })

        return {
            "success": True,
                            "response": f"找到 {len(results)} 個相關結果",
                            "results": results,
                            "source": "google_search",
                            "total_results": data.get("searchInformation", {}).get("totalResults", 0)
                        }
                    else:
                        error_detail = await response.text()
                        return {
                            "success": False,
                            "error": f"Google Search API 錯誤 (狀態: {response.status}): {error_detail}"
                        }

        except asyncio.TimeoutError:
        return {
                "success": False,
                "error": "Google Search API 請求超時 (10秒)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Google Search API 錯誤: {str(e)}"
            }

    async def send_openai_query(self, query: str) -> Dict[str, Any]:
        """發送 OpenAI 查詢"""
        try:
            api_key = api_manager.get_api_key(APIType.OPENAI)
            if not api_key:
        return {
                    "success": False,
                    "error": "OpenAI API Key 未設定"
                }

            import openai
            client = openai.OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的 Podcast 推薦助手，請用繁體中文回答。"},
                    {"role": "user", "content": query}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return {
                "success": True,
                "response": response.choices[0].message.content,
                "source": "openai",
                "model": "gpt-3.5-turbo",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except openai.AuthenticationError:
            return {
                "success": False,
                "error": "OpenAI API 認證失敗，請檢查 API Key"
            }
        except openai.RateLimitError:
            return {
                "success": False,
                "error": "OpenAI API 請求頻率過高，請稍後再試"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API 錯誤: {str(e)}"
            }

    async def send_anthropic_query(self, query: str) -> Dict[str, Any]:
        """發送 Anthropic 查詢"""
        try:
            api_key = api_manager.get_api_key(APIType.ANTHROPIC)
            if not api_key:
                return {
                    "success": False,
                    "error": "Anthropic API Key 未設定"
                }

            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": f"你是一個專業的 Podcast 推薦助手，請用繁體中文回答：{query}"}
                ]
            )

            return {
                "success": True,
                "response": response.content[0].text,
                "source": "anthropic",
                "model": "claude-3-sonnet",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except anthropic.AuthenticationError:
            return {
                "success": False,
                "error": "Anthropic API 認證失敗，請檢查 API Key"
            }
        except anthropic.RateLimitError:
            return {
                "success": False,
                "error": "Anthropic API 請求頻率過高，請稍後再試"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Anthropic API 錯誤: {str(e)}"
            }

    async def send_gemini_query(self, query: str) -> Dict[str, Any]:
        """發送 Gemini 查詢"""
        try:
            api_key = api_manager.get_api_key(APIType.GEMINI)
            if not api_key:
                return {
                    "success": False,
                    "error": "Gemini API Key 未設定"
                }

            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')

            response = model.generate_content(
                f"你是一個專業的 Podcast 推薦助手，請用繁體中文回答：{query}",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7
                )
            )

            return {
                "success": True,
                "response": response.text,
                "source": "gemini",
                "model": "gemini-pro"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini API 錯誤: {str(e)}"
            }

    async def send_vector_search_query(self, query: str) -> Dict[str, Any]:
        """發送向量搜尋查詢到 Milvus"""
        try:
            # 向量搜尋服務 URL
            vector_search_url = os.getenv("VECTOR_SEARCH_URL", "http://localhost:8002")

            payload = {
                "query": query,
                "top_k": 5,
                "collection_name": "podcast_embeddings"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{vector_search_url}/search",
                    json=payload,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        for item in data.get("results", []):
                            results.append({
                                "title": item.get("title", ""),
                                "content": item.get("content", ""),
                                "similarity": item.get("similarity", 0.0),
                                "source": "vector_search"
                            })

                        return {
                            "success": True,
                            "response": f"找到 {len(results)} 個相關的 Podcast",
                            "results": results,
                            "source": "vector_search",
                            "query_vector": data.get("query_vector", [])
                        }
                    else:
                        error_detail = await response.text()
                        return {
                            "success": False,
                            "error": f"向量搜尋服務錯誤 (狀態: {response.status}): {error_detail}"
                        }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "向量搜尋服務請求超時 (15秒)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"向量搜尋服務錯誤: {str(e)}"
            }

    # MusicGen 面板已移除
    pass

    # MusicGen 功能已移除

    def _check_tts_service_status(self):
        """檢查 TTS 服務狀態"""
        try:
            import requests

            # 嘗試從 TTS 服務獲取健康狀態
            tts_endpoints = [
                self.k8s_tts_url,      # K8s NodePort 服務
                self.tts_url,          # 本地開發
                self.container_tts_url # 容器環境
            ]

            for endpoint in tts_endpoints:
            try:
                    response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                        return {"status": "healthy", "endpoint": endpoint}
                except Exception as e:
                    continue

            return {"status": "unhealthy", "error": "無法連接到任何 TTS 服務"}

        except ImportError:
            return {"status": "unhealthy", "error": "缺少 requests 模組"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_rag_service_status(self):
        """檢查 RAG 服務狀態"""
        try:
            import requests

            # 嘗試從 RAG 服務獲取健康狀態
            rag_endpoints = [
                self.k8s_rag_url,      # K8s NodePort 服務
                self.rag_url,          # 本地開發
                self.container_rag_url # 容器環境
            ]

            for endpoint in rag_endpoints:
                try:
                    response = requests.get(f"{endpoint}/health", timeout=5)
                    if response.status_code == 200:
                        return {"status": "healthy", "endpoint": endpoint}
            except Exception as e:
                    continue

            return {"status": "unhealthy", "error": "無法連接到任何 RAG 服務"}

        except ImportError:
            return {"status": "unhealthy", "error": "缺少 requests 模組"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _get_voice_info(self, voice_id: str) -> dict:
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

    def render_main_interface(self):
        """渲染主要介面 - 三欄式佈局"""
        # 創建三欄佈局：左側功能控制 | 中間對話區 | 右側音樂生成
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            # 左側 1/4：功能控制欄
            self.render_left_control_panel()

        with col2:
            # 中間 2/4：主對話區
        self.render_main_chat_interface()

        with col3:
            # 右側 1/4：系統狀態和統計
            st.markdown("### 📊 系統狀態")
            st.info("系統運行正常")
            st.markdown("""
            **服務狀態：**
            - Podri-Chat: ✅ 正常
            - RAG Pipeline: ⚠️ 維護中
            - TTS 服務: ✅ 正常

            **使用統計：**
            - 訊息數: {st.session_state.current_session.get('message_count', 0)}
            - 語音生成: {st.session_state.current_session.get('voice_count', 0)}
            """)

def main():
    """主函數"""
    # 創建應用程式實例
    app = PodriChatApp()

    # 渲染主要介面
    app.render_main_interface()

if __name__ == "__main__":
    main()