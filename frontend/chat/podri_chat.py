#!/usr/bin/env python3
"""
Podri 智能助理 - OOP 架構版本
正確引用 Backend 服務類別，遵循 OOP 設計原則
"""

import streamlit as st
from PIL import Image
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import os
import uuid

# 添加 backend 路徑到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# 導入 Backend 服務類別
try:
    from backend.utils.core_services import BaseService, ServiceConfig, ServiceResponse
    from backend.main import BackendManager
    from backend.stt import STTService
    from backend.tts import TTSService
    from backend.llm import LLMService
    from backend.ml_pipeline.services import RecommendationService
    from backend.rag_pipeline.core.api_models import ChatRequest, ChatResponse
    from backend.utils.user_auth_service import UserAuthService
    from backend.config.db_config import POSTGRES_CONFIG
except ImportError as e:
    st.error(f"無法導入 Backend 服務類別: {e}")
    st.info("請確保 Backend 路徑正確且服務已啟動")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """聊天訊息資料類別"""
    role: str  # "user" 或 "bot"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class PodriChatService(BaseService):
    """Podri 聊天服務類別 - 繼承自 BaseService"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 Podri 聊天服務"""
        super().__init__("PodriChat", config)
        
        # 初始化子服務
        self.backend_manager: Optional[BackendManager] = None
        self.stt_service: Optional[STTService] = None
        self.tts_service: Optional[TTSService] = None
        self.llm_service: Optional[LLMService] = None
        self.recommendation_service: Optional[RecommendationService] = None
        
        # 使用者驗證服務
        self.user_auth_service: Optional[UserAuthService] = None
        
        # 聊天相關
        self.chat_history: List[ChatMessage] = []
        self.current_user_id: Optional[str] = None
        self.current_user_info: Optional[Dict[str, Any]] = None
        self.session_id: str = str(uuid.uuid4())
        
        logger.info("PodriChat 服務初始化完成")
    
    async def initialize(self) -> bool:
        """初始化所有子服務"""
        try:
            logger.info("正在初始化 PodriChat 子服務...")
            
            # 初始化 Backend 管理器
            self.backend_manager = BackendManager()
            await self.backend_manager.initialize_modules()
            
            # 初始化使用者驗證服務
            self.user_auth_service = UserAuthService(POSTGRES_CONFIG)
            
            # 初始化各子服務（這裡可以根據實際需求調整）
            # self.stt_service = STTService()
            # self.tts_service = TTSService()
            # self.llm_service = LLMService()
            # self.recommendation_service = RecommendationService()
            
            logger.info("PodriChat 子服務初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"PodriChat 初始化失敗: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            backend_status = self.backend_manager.get_system_status() if self.backend_manager else {"status": "not_initialized"}
            
            return {
                "status": "healthy",
                "backend_manager": backend_status,
                "chat_history_count": len(self.chat_history),
                "current_user": self.current_user_id
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def process_user_message(self, message: str, user_id: str = None) -> str:
        """處理用戶訊息 - 主要使用 RAG Pipeline 進行對話"""
        try:
            # 記錄用戶訊息
            user_msg = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.now(),
                metadata={"user_id": user_id}
            )
            self.chat_history.append(user_msg)
            
            # 記錄聊天訊息到資料庫（只有有效使用者才記錄）
            if (self.user_auth_service and self.current_user_info and 
                self.current_user_info.get('user_id') is not None and 
                self.current_user_info.get('user_type') != 'anonymous'):
                self.user_auth_service.log_chat_message(
                    user_id=self.current_user_info['user_id'],
                    session_id=self.session_id,
                    message_type='user',
                    content=message,
                    metadata={"service": "rag_pipeline"}
                )
            
            # 使用 Backend 服務處理訊息
            if self.backend_manager:
                # 預設使用 RAG Pipeline 進行所有對話
                # 只有特定關鍵字才使用其他服務
                
                query_type = "rag"  # 預設查詢類型
                
                # 檢查是否為推薦相關查詢
                if any(keyword in message.lower() for keyword in ["推薦", "podcast", "節目", "建議"]):
                    query_type = "recommendation"
                    # 調用推薦服務
                    response = await self.backend_manager.run_module("ml_pipeline", user_id=user_id)
                    bot_response = f"根據您的偏好，我推薦以下 Podcast：{response.get('message', '推薦服務暫時不可用')}"
                # 檢查是否為語音相關查詢
                elif any(keyword in message.lower() for keyword in ["語音轉文字", "語音識別", "stt", "轉錄"]):
                    query_type = "voice"
                    # 調用 STT 服務
                    response = await self.backend_manager.run_module("stt")
                    bot_response = f"語音轉文字服務狀態：{response.get('message', 'STT 服務暫時不可用')}"
                # 檢查是否為語音合成相關查詢
                elif any(keyword in message.lower() for keyword in ["文字轉語音", "語音合成", "tts", "發音"]):
                    query_type = "voice"
                    # 調用 TTS 服務
                    response = await self.backend_manager.run_module("tts")
                    bot_response = f"文字轉語音服務狀態：{response.get('message', 'TTS 服務暫時不可用')}"
                else:
                    # 預設使用 RAG Pipeline 進行智能對話
                    # 使用 QueryRequest 格式傳遞參數
                    rag_request = {
                        "query": message,
                        "user_id": user_id or "default_user",
                        "session_id": f"session_{user_id}" if user_id else "default_session",
                        "use_advanced_features": True,
                        "use_openai_search": True,
                        "use_llm_generation": True
                    }
                    
                    response = await self.backend_manager.run_module("rag_pipeline", **rag_request)
                    
                    # 從回應中提取內容
                    if isinstance(response, dict):
                        bot_response = response.get('response') or response.get('message', '抱歉，我暫時無法回應您的問題')
                    else:
                        bot_response = str(response) if response else '抱歉，我暫時無法回應您的問題'
                    
                    # 如果 RAG Pipeline 沒有回應，提供預設回應
                    if not bot_response or bot_response == '抱歉，我暫時無法回應您的問題':
                        bot_response = "我是 Podri，您的智能播客助理。我可以幫您搜尋播客內容、回答問題，或推薦適合的節目。請告訴我您想了解什麼？"
            else:
                bot_response = "抱歉，Backend 服務尚未初始化，請稍後再試"
            
            # 記錄機器人回應
            bot_msg = ChatMessage(
                role="bot",
                content=bot_response,
                timestamp=datetime.now(),
                metadata={"user_id": user_id}
            )
            self.chat_history.append(bot_msg)
            
            # 記錄機器人回應到資料庫（只有有效使用者才記錄）
            if (self.user_auth_service and self.current_user_info and 
                self.current_user_info.get('user_id') is not None and 
                self.current_user_info.get('user_type') != 'anonymous'):
                self.user_auth_service.log_chat_message(
                    user_id=self.current_user_info['user_id'],
                    session_id=self.session_id,
                    message_type='bot',
                    content=bot_response,
                    metadata={"service": "rag_pipeline", "query_type": query_type}
                )
                
                # 更新使用者行為統計
                self.user_auth_service.update_user_behavior_stats(
                    user_id=self.current_user_info['user_id'],
                    query_type=query_type
                )
            
            return bot_response
            
        except Exception as e:
            logger.error(f"處理用戶訊息失敗: {e}")
            return f"抱歉，處理您的訊息時發生錯誤：{str(e)}"
    
    def get_chat_history(self, user_id: str = None) -> List[ChatMessage]:
        """獲取聊天歷史"""
        if user_id:
            return [msg for msg in self.chat_history if msg.metadata and msg.metadata.get("user_id") == user_id]
        return self.chat_history
    
    def clear_chat_history(self, user_id: str = None):
        """清除聊天歷史"""
        if user_id:
            self.chat_history = [msg for msg in self.chat_history 
                               if not (msg.metadata and msg.metadata.get("user_id") == user_id)]
        else:
            self.chat_history.clear()
    
    def validate_user(self, user_identifier: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """驗證使用者 ID"""
        if not self.user_auth_service:
            return False, None
        
        is_valid, user_info = self.user_auth_service.validate_user_id(user_identifier)
        if is_valid:
            self.current_user_id = user_identifier
            self.current_user_info = user_info
            return True, user_info
        return False, None
    
    def set_anonymous_user(self):
        """設定匿名使用者（不記錄行為）"""
        self.current_user_id = "anonymous"
        self.current_user_info = {
            "user_id": None,
            "user_identifier": "anonymous",
            "user_type": "anonymous",
            "given_name": "匿名使用者",
            "username": "anonymous"
        }
    
    def create_guest_user(self) -> Optional[Dict[str, Any]]:
        """建立訪客使用者"""
        if not self.user_auth_service:
            return None
        
        guest_info = self.user_auth_service.create_guest_user()
        if guest_info:
            self.current_user_id = guest_info['user_identifier']
            self.current_user_info = guest_info
        return guest_info
    
    def get_user_stats(self) -> Optional[Dict[str, Any]]:
        """獲取使用者統計資訊"""
        if not self.user_auth_service or not self.current_user_info:
            return None
        
        return self.user_auth_service.get_user_stats(self.current_user_info['user_id'])

class PodriChatUI:
    """Podri 聊天 UI 類別"""
    
    def __init__(self):
        """初始化 UI"""
        self.chat_service = PodriChatService()
        self.setup_page_config()
        self.setup_custom_css()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """設定頁面配置"""
        st.set_page_config(
            page_title="Podri 你的智能助理",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_custom_css(self):
        """設定自訂 CSS"""
st.markdown("""
    <style>
    body {
        background-color: #F5EBDD;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 20px;
        max-width: 60%;
        margin: 6px;
        font-size: 16px;
        line-height: 1.5em;
    }
    .user-bubble {
        background-color: #FFF4DA;
        float: left;
    }
    .bot-bubble {
        background-color: #FFD700;
        float: right;
    }
    .chat-row {
        display: flex;
        align-items: flex-end;
        margin-bottom: 12px;
    }
    .chat-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
    }
        .service-status {
            padding: 8px;
            border-radius: 8px;
            margin: 4px 0;
            font-size: 12px;
        }
        .status-healthy {
            background-color: #E8F5E8;
            border-left: 4px solid #4CAF50;
        }
        .status-unhealthy {
            background-color: #FFEBEE;
            border-left: 4px solid #F44336;
    }
    </style>
""", unsafe_allow_html=True)

    def initialize_session_state(self):
        """初始化 Streamlit 會話狀態"""
if "messages" not in st.session_state:
    st.session_state.messages = []
        if "chat_service_initialized" not in st.session_state:
            st.session_state.chat_service_initialized = False
        if "user_authenticated" not in st.session_state:
            st.session_state.user_authenticated = False
        if "current_user_info" not in st.session_state:
            st.session_state.current_user_info = None
        if "initial_question_answered" not in st.session_state:
            st.session_state.initial_question_answered = False
        if "has_user_id" not in st.session_state:
            st.session_state.has_user_id = None
    
    async def initialize_chat_service(self):
        """初始化聊天服務"""
        if not st.session_state.chat_service_initialized:
            with st.spinner("正在初始化 Podri 聊天服務..."):
                success = await self.chat_service.initialize()
                if success:
                    st.session_state.chat_service_initialized = True
                    st.success("Podri 聊天服務初始化成功！")
                else:
                    st.error("Podri 聊天服務初始化失敗")
    
    def render_sidebar(self):
        """渲染側邊欄"""
with st.sidebar:
    st.image("logo_red.png", width=100)
    st.markdown("### ⌂ 回首頁")
            
            # 如果還沒有回答初始問題，顯示提示
            if not st.session_state.initial_question_answered:
                st.markdown("### ⚠️ 請先回答問題")
                st.info("請在主要介面回答是否有使用者 ID 的問題")
                return
            
            # 使用者驗證區域
            st.markdown("### 👤 使用者驗證")
            
            if not st.session_state.user_authenticated:
                # 根據初始問題的回答顯示不同的選項
                if st.session_state.has_user_id:
                    # 有使用者 ID 的情況 - 要求登入
                    st.markdown("#### 🔐 請登入您的帳號")
                    user_identifier = st.text_input("請輸入使用者 ID", placeholder="例如: user123, bdse37")
                    
                    if st.button("🔐 登入", type="primary", use_container_width=True):
                        if user_identifier:
                            is_valid, user_info = self.chat_service.validate_user(user_identifier)
                            if is_valid:
                                st.session_state.user_authenticated = True
                                st.session_state.current_user_info = user_info
                                st.success(f"歡迎回來，{user_info.get('given_name', user_info.get('username', user_identifier))}！")
                                st.rerun()
                            else:
                                st.error("使用者 ID 無效，請檢查後重試")
                        else:
                            st.warning("請輸入使用者 ID")
                    
                    # 提供其他選項
                    st.markdown("---")
                    st.markdown("#### 或者選擇其他方式：")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("👥 訪客模式"):
                            guest_info = self.chat_service.create_guest_user()
                            if guest_info:
                                st.session_state.user_authenticated = True
                                st.session_state.current_user_info = guest_info
                                st.success(f"歡迎使用訪客模式！您的 ID: {guest_info['user_identifier']}")
                                st.rerun()
                            else:
                                st.error("建立訪客帳號失敗")
                    
                    with col2:
                        if st.button("👤 匿名模式"):
                            self.chat_service.set_anonymous_user()
                            st.session_state.user_authenticated = True
                            st.session_state.current_user_info = self.chat_service.current_user_info
                            st.success("已切換到匿名模式")
                            st.rerun()
                
                else:
                    # 沒有使用者 ID 的情況 - 提供訪客和匿名選項
                    st.markdown("#### 👥 選擇使用方式")
                    st.info("您沒有使用者 ID，請選擇以下任一方式：")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("👥 訪客模式", use_container_width=True):
                            guest_info = self.chat_service.create_guest_user()
                            if guest_info:
                                st.session_state.user_authenticated = True
                                st.session_state.current_user_info = guest_info
                                st.success(f"歡迎使用訪客模式！您的 ID: {guest_info['user_identifier']}")
                                st.rerun()
                            else:
                                st.error("建立訪客帳號失敗")
                    
                    with col2:
                        if st.button("👤 匿名模式", use_container_width=True):
                            self.chat_service.set_anonymous_user()
                            st.session_state.user_authenticated = True
                            st.session_state.current_user_info = self.chat_service.current_user_info
                            st.success("已切換到匿名模式")
                            st.rerun()
                    
                    # 提供重新選擇的選項
                    st.markdown("---")
                    if st.button("🔄 重新選擇", use_container_width=True):
                        st.session_state.initial_question_answered = False
                        st.session_state.has_user_id = None
                        st.rerun()
            else:
                # 顯示已登入使用者資訊
                user_info = st.session_state.current_user_info
                user_type = user_info.get('user_type', 'anonymous')
                
                if user_type == 'anonymous':
                    user_type_icon = "👤"
                    user_name = "匿名使用者"
                    user_type_text = "匿名模式"
                    bg_color = "#FFF3CD"
                elif user_type == 'registered':
                    user_type_icon = "👤"
                    user_name = user_info.get('given_name') or user_info.get('username') or user_info.get('user_identifier')
                    user_type_text = "註冊用戶"
                    bg_color = "#E8F5E8"
                else:
                    user_type_icon = "👥"
                    user_name = user_info.get('user_identifier')
                    user_type_text = "訪客"
                    bg_color = "#E3F2FD"
                
                st.markdown(f"""
                <div style="padding: 10px; background-color: {bg_color}; border-radius: 8px; margin: 10px 0;">
                    <strong>{user_type_icon} {user_name}</strong><br>
                    <small>ID: {user_info.get('user_identifier')}</small><br>
                    <small>類型: {user_type_text}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚪 登出"):
                    st.session_state.user_authenticated = False
                    st.session_state.current_user_info = None
                    st.session_state.messages.clear()
                    st.session_state.initial_question_answered = False
                    st.session_state.has_user_id = None
                    st.success("已登出")
                    st.rerun()
            
            # 服務狀態顯示
            st.markdown("### 🔧 服務狀態")
            if st.session_state.chat_service_initialized:
                # 使用 asyncio.run 來執行 async 函數
                health_status = asyncio.run(self.chat_service.health_check())
                
                # Backend 整體狀態
                status_class = "status-healthy" if health_status["status"] == "healthy" else "status-unhealthy"
                st.markdown(f"""
                <div class="service-status {status_class}">
                    Backend 服務: {health_status["status"]}
                </div>
                """, unsafe_allow_html=True)
                
                # RAG Pipeline 狀態（主要對話服務）
                if "backend_manager" in health_status:
                    rag_status = health_status["backend_manager"].get("modules", {}).get("rag_pipeline", {})
                    rag_status_text = rag_status.get("status", "unknown")
                    rag_status_class = "status-healthy" if rag_status_text == "initialized" else "status-unhealthy"
                    st.markdown(f"""
                    <div class="service-status {rag_status_class}">
                        RAG Pipeline (主要對話): {rag_status_text}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 使用者統計資訊（只有有效使用者才顯示）
            if (st.session_state.user_authenticated and st.session_state.current_user_info and 
                st.session_state.current_user_info.get('user_type') != 'anonymous'):
                st.markdown("### 📊 使用統計")
                user_stats = self.chat_service.get_user_stats()
                if user_stats:
                    stats = user_stats.get('today_stats', {})
                    st.metric("今日查詢", stats.get('total_queries', 0))
                    st.metric("RAG 查詢", stats.get('rag_queries', 0))
                    st.metric("推薦查詢", stats.get('recommendation_queries', 0))
                else:
                    st.info("📊 統計資訊載入中...")
            elif st.session_state.user_authenticated and st.session_state.current_user_info.get('user_type') == 'anonymous':
                st.markdown("### 📊 使用統計")
                st.info("👤 匿名模式：不記錄使用統計")
            
            # 語音設定
            st.markdown("### 🔊 語音設定")
    voice_reply = st.checkbox("✅ 啟用語音回覆")
    tts_model = st.selectbox("TTS 語音選擇", ["Qwen2.5-TW", "Breeze2", "EdgeTTS"])
    st.slider("音量", 0.0, 1.0, 0.5)
    st.slider("語速", 0.5, 2.0, 1.0)
            
    if st.button("🔊 試聽語音"):
        st.success("（此處播放語音示意）")
            
    st.markdown("---")
            
            # 聊天歷史
    if st.button("🕓 查看歷史訊息"):
        for msg in st.session_state.messages:
            st.text(f"{msg['role']}: {msg['content']}")

            # 清除歷史
            if st.button("🗑️ 清除聊天歷史"):
                st.session_state.messages.clear()
                st.success("聊天歷史已清除")
    
    def render_chat_interface(self):
        """渲染聊天介面"""
        st.markdown("## 💬 Podri 智能對話 (RAG Pipeline)")
        st.markdown("*基於檢索增強生成的智能播客助理*")
        
        # 如果還沒有回答初始問題，顯示詢問介面
        if not st.session_state.initial_question_answered:
            self.render_initial_question()
            return
        
        # 顯示聊天訊息
chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            cols = st.columns([1, 9])
            with cols[0]:
                        st.image("user_avatar.png", width=48)
            with cols[1]:
                        st.markdown(f'<div class="chat-bubble user-bubble">{msg["content"]}</div>', 
                                  unsafe_allow_html=True)
        else:
            cols = st.columns([9, 1])
            with cols[0]:
                        st.markdown(f'<div class="chat-bubble bot-bubble">{msg["content"]}</div>', 
                                  unsafe_allow_html=True)
            with cols[1]:
                        st.image("bot_avatar.png", width=48)
    
    def render_initial_question(self):
        """渲染初始詢問介面"""
        st.markdown("### 👋 歡迎使用 Podri 智能助理！")
        st.markdown("在開始對話之前，請告訴我您是否有使用者 ID？")
        
        # 使用容器來美化顯示
        with st.container():
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>🔐 請選擇您的使用方式：</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 我有使用者 ID", type="primary", use_container_width=True):
                    st.session_state.has_user_id = True
                    st.session_state.initial_question_answered = True
                    st.success("請在側邊欄輸入您的使用者 ID 並登入")
                    st.rerun()
            
            with col2:
                if st.button("❌ 我沒有使用者 ID", use_container_width=True):
                    st.session_state.has_user_id = False
                    st.session_state.initial_question_answered = True
                    st.info("您可以選擇訪客模式或匿名模式繼續使用")
                    st.rerun()
            
            # 顯示說明
            st.markdown("""
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h5>📋 使用說明：</h5>
                <ul>
                    <li><strong>有使用者 ID：</strong>登入後可以享受完整的個人化服務，包括聊天記錄保存、使用統計等</li>
                    <li><strong>沒有使用者 ID：</strong>可以選擇訪客模式（臨時 ID）或匿名模式（不記錄任何資訊）</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def render_input_area(self):
        """渲染輸入區域"""
        # 如果還沒有回答初始問題或沒有驗證，不顯示輸入區域
        if not st.session_state.initial_question_answered or not st.session_state.user_authenticated:
            return
        
st.markdown("---")
        
cols = st.columns([8, 1, 1])
        
with cols[0]:
    user_input = st.text_input("🔤 請輸入訊息...", key="input")
        
with cols[1]:
            if st.button("🎤", help="語音輸入"):
        st.info("（語音轉文字模擬輸入）")
        
with cols[2]:
    if st.button("📨", help="送出訊息"):
                if user_input and st.session_state.chat_service_initialized:
                    # 顯示用戶訊息
            st.session_state.messages.append({"role": "user", "content": user_input})
                    
                    # 處理訊息
                    with st.spinner("Podri 正在思考..."):
                        user_id = st.session_state.current_user_info.get('user_identifier')
                        response = asyncio.run(self.chat_service.process_user_message(user_input, user_id))
                    
                    # 顯示機器人回應
                    st.session_state.messages.append({"role": "bot", "content": response})
            st.experimental_rerun()
                elif not st.session_state.chat_service_initialized:
                    st.error("聊天服務尚未初始化，請稍候...")
    
    def run(self):
        """運行應用程式"""
        # 初始化聊天服務
        asyncio.run(self.initialize_chat_service())
        
        # 渲染側邊欄
        self.render_sidebar()
        
        # 渲染主要聊天介面
        self.render_chat_interface()
        
        # 渲染輸入區域
        self.render_input_area()

def main():
    """主函數"""
    try:
        # 創建並運行 UI
        ui = PodriChatUI()
        ui.run()
    except Exception as e:
        st.error(f"應用程式執行錯誤: {e}")
        logger.error(f"應用程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
