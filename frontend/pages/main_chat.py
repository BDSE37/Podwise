"""
Podri Chat 主頁面
整合聊天、TTS、MusicGen等功能的主介面
使用 OOP 架構實作
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from frontend.chat.services.service_manager import ServiceManager
from frontend.chat.services.intelligent_processor import IntelligentProcessor
from frontend.chat.services.musicgen_service import MusicGenService
from frontend.chat.services.minio_audio_service import MinioAudioService
from frontend.chat.services.intelligent_audio_search import IntelligentAudioSearch
from frontend.chat.utils.api_key_manager import APIKeyManager
from frontend.chat.utils.env_config import EnvironmentConfig


class PodriChatInterface:
    """
    Podri Chat 主介面類別
    管理所有聊天相關功能和UI元件
    """
    
    def __init__(self):
        """初始化聊天介面"""
        self.config = EnvironmentConfig()
        self.api_manager = APIKeyManager()
        self.service_manager = ServiceManager()
        self.intelligent_processor = IntelligentProcessor()
        self.musicgen_service = MusicGenService()
        self.minio_service = MinioAudioService()
        self.audio_search = IntelligentAudioSearch()
        
        # 初始化 Streamlit 頁面配置
        self._setup_page_config()
        
    def _setup_page_config(self):
        """設置 Streamlit 頁面配置"""
        st.set_page_config(
            page_title="Podri Chat - 智能對話系統",
            page_icon="🎙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 自定義 CSS 樣式
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        .status-online { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """渲染頁面標題"""
        st.markdown('<h1 class="main-header">🎙️ Podri Chat 智能對話系統</h1>', unsafe_allow_html=True)
        
        # 顯示系統狀態
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("聊天服務", "🟢 運行中")
        with col2:
            st.metric("TTS 服務", "🟢 運行中")
        with col3:
            st.metric("MusicGen", "🟢 運行中")
        with col4:
            st.metric("RAG 系統", "🟢 運行中")
    
    def render_sidebar(self):
        """渲染側邊欄"""
        with st.sidebar:
            st.header("⚙️ 系統設定")
            
            # API 金鑰管理
            st.subheader("🔑 API 金鑰設定")
            api_provider = st.selectbox(
                "選擇 API 提供商",
                ["OpenAI", "Gemini", "Google Search", "Anthropic", "本地 LLM"],
                key="api_provider_select"
            )
            
            if api_provider != "本地 LLM":
                api_key = st.text_input(
                    f"{api_provider} API 金鑰",
                    type="password",
                    key=f"{api_provider.lower()}_api_key"
                )
                if st.button("保存 API 金鑰", key="save_api_key"):
                    self.api_manager.save_api_key(api_provider, api_key)
                    st.success("API 金鑰已保存")
            
            # TTS 設定
            st.subheader("🎤 TTS 設定")
            voice_model = st.selectbox(
                "語音模型",
                ["GPT-SoVITS", "Qwen25-TW", "原生 TTS"],
                key="voice_model_select"
            )
            
            voice_style = st.selectbox(
                "語音風格",
                ["自然", "活潑", "專業", "溫柔"],
                key="voice_style_select"
            )
            
            # MusicGen 設定
            st.subheader("🎵 MusicGen 設定")
            music_model = st.selectbox(
                "音樂模型",
                ["facebook/musicgen-small", "facebook/musicgen-medium", "facebook/musicgen-large"],
                key="music_model_select"
            )
            
            music_duration = st.slider(
                "音樂長度 (秒)",
                min_value=5,
                max_value=30,
                value=10,
                key="music_duration_slider"
            )
            
            # 系統設定
            st.subheader("🔧 系統設定")
            confidence_threshold = st.slider(
                "信心度閾值",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                key="confidence_threshold_slider"
            )
            
            max_tokens = st.number_input(
                "最大 Token 數",
                min_value=100,
                max_value=4000,
                value=2000,
                key="max_tokens_input"
            )
    
    def render_chat_interface(self):
        """渲染聊天介面"""
        st.header("💬 智能對話")
        
        # 初始化聊天歷史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 顯示聊天歷史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 聊天輸入
        if prompt := st.chat_input("輸入您的問題..."):
            # 添加用戶訊息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 處理回應
            with st.chat_message("assistant"):
                with st.spinner("正在思考中..."):
                    response = self._process_chat_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    def _process_chat_response(self, prompt: str) -> str:
        """處理聊天回應"""
        try:
            # 使用智能處理器處理回應
            response = self.intelligent_processor.process_query(prompt)
            return response
        except Exception as e:
            st.error(f"處理回應時發生錯誤: {str(e)}")
            return "抱歉，處理您的問題時發生錯誤。請稍後再試。"
    
    def render_tts_interface(self):
        """渲染 TTS 介面"""
        st.header("🎤 文字轉語音")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            text_input = st.text_area(
                "輸入要轉換的文字",
                height=150,
                key="tts_text_input"
            )
            
            if st.button("生成語音", key="generate_tts"):
                if text_input.strip():
                    with st.spinner("正在生成語音..."):
                        audio_data = self._generate_tts(text_input)
                        if audio_data:
                            st.audio(audio_data, format="audio/wav")
                            st.success("語音生成成功！")
                        else:
                            st.error("語音生成失敗")
                else:
                    st.warning("請輸入要轉換的文字")
        
        with col2:
            st.subheader("語音設定")
            
            # 語音試聽
            st.write("**試聽語音樣本**")
            sample_voices = ["自然女聲", "活潑男聲", "專業女聲", "溫柔男聲"]
            selected_voice = st.selectbox("選擇語音", sample_voices, key="sample_voice_select")
            
            if st.button("試聽", key="preview_voice"):
                st.info(f"試聽 {selected_voice} 語音樣本")
    
    def _generate_tts(self, text: str) -> bytes:
        """生成 TTS 音訊"""
        try:
            # 這裡應該調用 TTS 服務
            # 暫時返回空資料
            return b""
        except Exception as e:
            st.error(f"TTS 生成錯誤: {str(e)}")
            return b""
    
    def render_musicgen_interface(self):
        """渲染 MusicGen 介面"""
        st.header("🎵 AI 音樂生成")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            music_prompt = st.text_area(
                "音樂描述",
                placeholder="例如：輕快的鋼琴曲，適合放鬆心情",
                height=100,
                key="music_prompt_input"
            )
            
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                if st.button("生成音樂", key="generate_music"):
                    if music_prompt.strip():
                        with st.spinner("正在生成音樂..."):
                            audio_data = self._generate_music(music_prompt)
                            if audio_data:
                                st.audio(audio_data, format="audio/wav")
                                st.success("音樂生成成功！")
                            else:
                                st.error("音樂生成失敗")
                    else:
                        st.warning("請輸入音樂描述")
            
            with col_gen2:
                if st.button("隨機生成", key="random_music"):
                    with st.spinner("正在生成隨機音樂..."):
                        random_prompts = [
                            "輕快的鋼琴曲",
                            "搖滾樂隊演奏",
                            "古典交響樂",
                            "電子舞曲"
                        ]
                        import random
                        random_prompt = random.choice(random_prompts)
                        audio_data = self._generate_music(random_prompt)
                        if audio_data:
                            st.audio(audio_data, format="audio/wav")
                            st.success(f"隨機音樂生成成功！({random_prompt})")
        
        with col2:
            st.subheader("音樂設定")
            
            # 音樂風格選擇
            music_styles = ["古典", "流行", "搖滾", "電子", "爵士", "民謠"]
            selected_style = st.multiselect("音樂風格", music_styles, key="music_style_select")
            
            # 音樂長度
            duration = st.slider("音樂長度 (秒)", 5, 30, 10, key="music_duration_slider2")
            
            # 音樂情緒
            emotion = st.selectbox("音樂情緒", ["快樂", "悲傷", "平靜", "興奮", "神秘"], key="music_emotion_select")
    
    def _generate_music(self, prompt: str) -> bytes:
        """生成音樂"""
        try:
            # 這裡應該調用 MusicGen 服務
            # 暫時返回空資料
            return b""
        except Exception as e:
            st.error(f"音樂生成錯誤: {str(e)}")
            return b""
    
    def render_audio_search_interface(self):
        """渲染音訊搜尋介面"""
        st.header("🔍 智能音訊搜尋")
        
        search_query = st.text_input(
            "搜尋音訊內容",
            placeholder="例如：尋找包含鋼琴演奏的音訊",
            key="audio_search_input"
        )
        
        col_search1, col_search2 = st.columns([3, 1])
        
        with col_search1:
            if st.button("搜尋音訊", key="search_audio"):
                if search_query.strip():
                    with st.spinner("正在搜尋音訊..."):
                        results = self._search_audio(search_query)
                        if results:
                            st.success(f"找到 {len(results)} 個相關音訊")
                            for i, result in enumerate(results):
                                with st.expander(f"音訊 {i+1}: {result.get('title', '無標題')}"):
                                    st.write(f"**描述:** {result.get('description', '無描述')}")
                                    st.write(f"**時長:** {result.get('duration', '未知')}")
                                    if st.button(f"播放音訊 {i+1}", key=f"play_audio_{i}"):
                                        st.audio(result.get('audio_data', b''), format="audio/wav")
                        else:
                            st.warning("未找到相關音訊")
                else:
                    st.warning("請輸入搜尋關鍵字")
        
        with col_search2:
            st.subheader("搜尋選項")
            
            # 搜尋範圍
            search_scope = st.multiselect(
                "搜尋範圍",
                ["Podcast", "音樂", "語音", "音效"],
                default=["Podcast", "音樂"],
                key="search_scope_select"
            )
            
            # 時間範圍
            time_range = st.selectbox(
                "時間範圍",
                ["全部時間", "最近一天", "最近一週", "最近一個月"],
                key="time_range_select"
            )
    
    def _search_audio(self, query: str) -> list:
        """搜尋音訊"""
        try:
            # 這裡應該調用音訊搜尋服務
            # 暫時返回空列表
            return []
        except Exception as e:
            st.error(f"音訊搜尋錯誤: {str(e)}")
            return []
    
    def render_training_interface(self):
        """渲染訓練介面"""
        st.header("🏋️ 模型訓練")
        
        tab1, tab2, tab3 = st.tabs(["TTS 訓練", "音樂訓練", "模型管理"])
        
        with tab1:
            st.subheader("TTS 模型訓練")
            
            # 上傳訓練資料
            uploaded_files = st.file_uploader(
                "上傳音訊檔案",
                type=["wav", "mp3", "flac"],
                accept_multiple_files=True,
                key="tts_training_files"
            )
            
            if uploaded_files:
                st.write(f"已上傳 {len(uploaded_files)} 個檔案")
                
                # 訓練設定
                col_train1, col_train2 = st.columns(2)
                with col_train1:
                    epochs = st.number_input("訓練輪數", min_value=1, max_value=100, value=10, key="tts_epochs")
                    learning_rate = st.number_input("學習率", min_value=0.0001, max_value=0.01, value=0.001, key="tts_lr")
                
                with col_train2:
                    batch_size = st.number_input("批次大小", min_value=1, max_value=32, value=8, key="tts_batch_size")
                    model_name = st.text_input("模型名稱", value="my_tts_model", key="tts_model_name")
                
                if st.button("開始訓練", key="start_tts_training"):
                    with st.spinner("正在訓練 TTS 模型..."):
                        st.info("TTS 模型訓練已開始，請耐心等待...")
        
        with tab2:
            st.subheader("音樂模型訓練")
            
            # 音樂訓練設定
            music_data_path = st.text_input("音樂資料路徑", key="music_data_path")
            
            if st.button("開始音樂訓練", key="start_music_training"):
                with st.spinner("正在訓練音樂模型..."):
                    st.info("音樂模型訓練已開始，請耐心等待...")
        
        with tab3:
            st.subheader("模型管理")
            
            # 模型列表
            models = ["GPT-SoVITS-v1", "MusicGen-v1", "Qwen25-TW-v1"]
            selected_model = st.selectbox("選擇模型", models, key="model_select")
            
            col_model1, col_model2 = st.columns(2)
            with col_model1:
                if st.button("下載模型", key="download_model"):
                    st.info(f"正在下載 {selected_model}...")
            
            with col_model2:
                if st.button("刪除模型", key="delete_model"):
                    st.warning(f"確定要刪除 {selected_model} 嗎？")
    
    def run(self):
        """運行主介面"""
        # 渲染頁面標題
        self.render_header()
        
        # 渲染側邊欄
        self.render_sidebar()
        
        # 主要功能標籤頁
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 智能對話", 
            "🎤 TTS", 
            "🎵 MusicGen", 
            "🔍 音訊搜尋", 
            "🏋️ 訓練"
        ])
        
        with tab1:
            self.render_chat_interface()
        
        with tab2:
            self.render_tts_interface()
        
        with tab3:
            self.render_musicgen_interface()
        
        with tab4:
            self.render_audio_search_interface()
        
        with tab5:
            self.render_training_interface()


def main():
    """主函數"""
    # 創建並運行聊天介面
    chat_interface = PodriChatInterface()
    chat_interface.run()


if __name__ == "__main__":
    main() 