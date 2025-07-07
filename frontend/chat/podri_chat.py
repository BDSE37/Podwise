#!/usr/bin/env python3
"""
Podri 智能助理 - 修正版本
整合 TTS 語音回覆功能，支援三個台灣語音
"""

import streamlit as st
import asyncio
import requests
import base64
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 導入服務管理器
try:
    from services.service_manager import service_manager
    from services.intelligent_processor import intelligent_processor
    from services.intelligent_audio_search import intelligent_audio_search
    from services.voice_recorder import VoiceRecorder
    from services.minio_audio_service import minio_audio_service
    SERVICES_AVAILABLE = True
except ImportError as e:
    st.warning(f"服務模組不可用: {e}")
    SERVICES_AVAILABLE = False

# 設定奶茶色主題樣式
st.markdown("""
<style>
/* 整體背景色 */
.stApp {
    background-color: #FDF8F3 !important;
}

/* 主要內容區域 */
.main .block-container {
    background-color: #FDF8F3 !important;
    padding: 2rem;
}

/* 側邊欄樣式 */
section[data-testid="stSidebar"] {
    background-color: #F5E6D3 !important;
    border-right: 2px solid #E8D5C4;
}

/* 標題顏色 */
h1, h2, h3 {
    color: #8B4513 !important;
}

/* 按鈕樣式 */
.stButton > button {
    background-color: #D4A574 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 24px !important;
}

.stButton > button:hover {
    background-color: #C79463 !important;
}

/* 聊天氣泡樣式 */
.user-bubble {
    background-color: #2f4f4f !important;
    color: white !important;
    margin-left: auto !important;
}

.bot-bubble {
    background-color: #c0c0c0 !important;
    color: #333333 !important;
    margin-right: auto !important;
}

/* 輸入框樣式 */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 2px solid #E8D5C4 !important;
    border-radius: 25px !important;
    padding: 12px 20px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #D4A574 !important;
    box-shadow: 0 0 0 2px rgba(212, 165, 116, 0.2) !important;
}

/* 快捷按鈕樣式 */
.stButton > button[data-testid*="quick_"] {
    background-color: #2196F3 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    margin: 2px !important;
}

.stButton > button[data-testid*="quick_"]:hover {
    background-color: #1976D2 !important;
}

/* 成功訊息樣式 */
.stSuccess {
    background-color: #E8F5E8 !important;
    border-left: 4px solid #4CAF50 !important;
}

/* 警告訊息樣式 */
.stWarning {
    background-color: #FFF3CD !important;
    border-left: 4px solid #FFC107 !important;
}
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "user_authenticated" not in st.session_state:
    st.session_state["user_authenticated"] = False
if "initial_question_answered" not in st.session_state:
    st.session_state["initial_question_answered"] = False
if "has_user_id" not in st.session_state:
    st.session_state["has_user_id"] = None
if "input_mode" not in st.session_state:
    st.session_state["input_mode"] = "text"
if "voice_input_result" not in st.session_state:
    st.session_state["voice_input_result"] = ""
if "audio_url" not in st.session_state:
    st.session_state["audio_url"] = None
if "voice_reply" not in st.session_state:
    st.session_state["voice_reply"] = False
if "current_audio_file" not in st.session_state:
    st.session_state["current_audio_file"] = None

# TTS Backend 整合函數
async def call_tts_backend(text: str, voice: str, volume: str, speed: str, pitch: str) -> Optional[str]:
    """調用 Podri TTS Backend 生成語音"""
    try:
        # 調用本地 Podri TTS 服務
        tts_url = "http://localhost:8000/synthesize"
        
        payload = {
            "文字": text,
            "語音": voice,
            "語速": speed,
            "音量": volume,
            "音調": pitch
        }
        
        response = requests.post(tts_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("成功"):
                # 將 Base64 音頻數據轉換為臨時文件
                audio_data = base64.b64decode(result["音訊檔案"])
                
                # 創建臨時音頻文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name
                
                return temp_file_path
            else:
                st.error(f"TTS 生成失敗: {result.get('錯誤訊息', '未知錯誤')}")
                return None
        else:
            st.error(f"TTS 服務請求失敗: {response.status_code}")
            return None
        
    except requests.exceptions.ConnectionError:
        st.error("無法連接到 TTS 服務，請確認服務是否啟動")
        return None
    except Exception as e:
        st.error(f"TTS 服務調用失敗: {e}")
        return None

# 智能處理函數
async def process_with_intelligent_services(query: str, user_id: str = "default_user") -> str:
    """使用智能服務處理查詢"""
    if not SERVICES_AVAILABLE:
        return f"[智能回覆]：{query} 的相關內容... (服務不可用)"
    
    try:
        # 1. 使用服務管理器檢查 RAG Pipeline 服務
        rag_result = await service_manager.make_service_request(
            service_name="rag_pipeline",
            method="POST",
            endpoint="/process",
            data={
                "query": query,
                "user_id": user_id,
                "use_agents": True
            },
            use_cache=True,
            cache_ttl=300  # 5分鐘快取
        )
        
        if rag_result["success"]:
            # 使用智能處理器優化結果
            raw_results = [rag_result["data"]]
            processed_results = intelligent_processor.process_search_results(
                raw_results, query, max_results=3
            )
            
            if processed_results:
                # 組合最佳結果
                best_result = processed_results[0]
                response = f"[智能回覆]：{best_result.content}"
                
                # 如果有相關音檔，提供音檔建議
                audio_results = await intelligent_audio_search.search_related_audio(
                    query, minio_audio_service
                )
                
                if audio_results:
                    audio_suggestions = "\n\n🎵 相關音檔建議："
                    for i, audio in enumerate(audio_results[:3]):
                        audio_suggestions += f"\n• {audio.get('title', audio.get('name', '未知音檔'))}"
                    response += audio_suggestions
                
                return response
            else:
                return f"[智能回覆]：{rag_result['data'].get('content', '處理完成但無結果')}"
        else:
            # RAG 服務失敗，使用智能音檔搜尋作為備用
            audio_results = await intelligent_audio_search.search_related_audio(
                query, minio_audio_service
            )
            
            if audio_results:
                response = f"[智能回覆]：關於「{query}」，我找到以下相關音檔：\n\n"
                for i, audio in enumerate(audio_results[:5]):
                    response += f"🎵 {audio.get('title', audio.get('name', '未知音檔'))}\n"
                return response
            else:
                return f"[智能回覆]：{query} 的相關內容... (RAG 服務異常: {rag_result.get('error', '未知錯誤')})"
            
    except Exception as e:
        return f"[智能回覆]：{query} 的相關內容... (處理錯誤: {str(e)})"

# 語音回覆函數
async def generate_voice_reply(text: str, voice: str, volume: int, speed: int, pitch: int) -> Optional[str]:
    """為機器人回覆生成語音"""
    if not st.session_state["voice_reply"]:
            return None
    
    try:
        audio_file = await call_tts_backend(
            text=text,
            voice=voice,
            volume=f"{volume:+d}%",
            speed=f"{speed:+d}%",
            pitch=f"{pitch:+d}Hz"
        )
        return audio_file
    except Exception as e:
        st.error(f"語音生成失敗: {e}")
        return None

# 側邊欄
with st.sidebar:
    st.markdown("## ⌂ Podri 智能助理")
    st.markdown("---")
    
    if not st.session_state["initial_question_answered"]:
        st.info("請先在主畫面選擇是否有使用者ID")
    else:
        if not st.session_state["user_authenticated"]:
            if st.session_state["has_user_id"]:
                user_id = st.text_input("請輸入使用者ID", key="user_id_input")
                if st.button("登入", key="login_btn"):
                    if user_id:
                        st.session_state["user_authenticated"] = True
                        st.session_state["current_user"] = user_id
                        st.success(f"歡迎，{user_id}")
                        st.rerun()
                    else:
                        st.warning("請輸入ID")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                      if st.button("訪客模式", key="guest_btn"):
                        st.session_state["user_authenticated"] = True
                        st.session_state["current_user"] = "guest"
                        st.success("已進入訪客模式")
                        st.rerun()
                    with col2:
                      if st.button("匿名模式", key="anon_btn"):
                        st.session_state["user_authenticated"] = True
                        st.session_state["current_user"] = "anonymous"
                        st.success("已進入匿名模式")
                        st.rerun()
            else:
              st.success(f"已登入：{st.session_state.get('current_user', '未知')}")
            if st.button("登出", key="logout_btn"):
                st.session_state["user_authenticated"] = False
                st.session_state["current_user"] = None
                st.session_state["messages"] = []
                st.rerun()
            
    st.markdown("---")
    st.markdown("### 語音設定")
    st.session_state["voice_reply"] = st.checkbox("啟用語音回覆", value=st.session_state["voice_reply"])
    
    if st.session_state["voice_reply"]:
        # TTS 語音選擇 - 使用三個實際可用的語音
        tts_voice = st.selectbox(
            "選擇語音",
            ["podrina", "podrisa", "podrino"],
            format_func=lambda x: {
                "podrina": "Podrina (溫柔女聲)",
                "podrisa": "Podrisa (活潑女聲)", 
                "podrino": "Podrino (穩重男聲)"
            }[x],
            key="tts_voice_select"
        )
        
        # 語音參數調整
        col1, col2, col3 = st.columns(3)
        with col1:
            volume = st.slider("音量", -50, 50, 0, key="volume_slider")
        with col2:
            speed = st.slider("語速", -50, 50, 0, key="speed_slider")
        with col3:
            pitch = st.slider("音調", -50, 50, 0, key="pitch_slider")
        
        # 顯示當前參數
        st.caption(f"音量: {volume:+d}% | 語速: {speed:+d}% | 音調: {pitch:+d}Hz")
        
        # 試聽按鈕
        if st.button("🔊 試聽語音", key="test_voice_btn"):
            test_text = "您好，我是 Podri 智能助理，很高興為您服務！"
            st.success(f"正在使用 {tts_voice} 語音生成試聽...")
            
            # 調用您的 TTS backend
            audio_url = asyncio.run(call_tts_backend(
                text=test_text,
                voice=tts_voice,
                volume=f"{volume:+d}%",
                speed=f"{speed:+d}%",
                pitch=f"{pitch:+d}Hz"
            ))
            
            if audio_url:
                st.audio(audio_url, format="audio/wav")
                # 清理臨時文件
                try:
                    os.unlink(audio_url)
                except:
                    pass
            else:
                st.error("語音生成失敗，請檢查 TTS 服務狀態")
            
    st.markdown("---")
    st.markdown("### 服務狀態")
    
    # 檢查 TTS 服務狀態
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            st.success("✅ TTS 服務正常")
        else:
            st.warning("⚠️ TTS 服務異常")
    except:
        st.error("❌ TTS 服務未啟動")
    
    # 檢查 RAG 服務狀態（改用 service_manager）
    if SERVICES_AVAILABLE:
        try:
            health = asyncio.run(service_manager.check_service_health("rag_pipeline"))
            if health.status.value == "healthy":
                st.success("✅ RAG 服務正常")
            elif health.status.value == "degraded":
                st.warning("⚠️ RAG 服務部分異常")
            elif health.status.value == "unhealthy":
                st.error("❌ RAG 服務異常")
            else:
                st.warning(f"RAG 服務狀態：{health.status.value}")
        except Exception as e:
            st.error(f"❌ RAG 服務檢查失敗: {e}")
    else:
        st.error("❌ RAG 服務不可用")

# 首次引導
if not st.session_state["initial_question_answered"]:
    st.markdown("# 👋 歡迎使用 Podri 智能助理！")
    st.markdown("請問您是否有使用者ID？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 我有使用者ID", key="has_id_btn"):
            st.session_state["has_user_id"] = True
            st.session_state["initial_question_answered"] = True
            st.rerun()
    with col2:
        if st.button("❌ 沒有ID，訪客/匿名", key="no_id_btn"):
            st.session_state["has_user_id"] = False
            st.session_state["initial_question_answered"] = True
            st.rerun()
    st.stop()
            
# 主區塊
    st.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>
  <!-- LOGO 區塊，請將 src 換成您的 logo 路徑 -->
  <div style='width:40px;height:40px;background:#eee;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;'>🤖</div>
  <span style='font-size:1.6rem;font-weight:bold;'>Podri 智能助理</span>
            </div>
            """, unsafe_allow_html=True)
            
# 快捷問答泡泡
quick_questions = [
    "請推薦一些有趣的播客節目",
    "我想搜尋關於科技創新的播客內容",
    "請告訴我如何使用這個播客助理",
    "請推薦商業類播客"
]

colq = st.columns(len(quick_questions))
for i, q in enumerate(quick_questions):
    with colq[i]:
        if st.button(q, key=f"quick_{i}"):
            st.session_state["messages"].append({"role": "user", "content": q, "time": datetime.now()})
            # 使用智能服務處理
            user_id = st.session_state.get("current_user", "guest")
            intelligent_reply = asyncio.run(process_with_intelligent_services(q, user_id))
            st.session_state["messages"].append({"role": "assistant", "content": intelligent_reply, "time": datetime.now()})
            
            # 語音回覆
            if st.session_state["voice_reply"]:
                voice = st.session_state.get("tts_voice_select", "podrina")
                volume = st.session_state.get("volume_slider", 0)
                speed = st.session_state.get("speed_slider", 0)
                pitch = st.session_state.get("pitch_slider", 0)
                
                audio_file = asyncio.run(generate_voice_reply(
                    text=intelligent_reply,
                    voice=voice,
                    volume=volume,
                    speed=speed,
                    pitch=pitch
                ))
                if audio_file:
                    st.session_state["current_audio_file"] = audio_file
            
                    st.rerun()
            
# 聊天訊息區（仿 ChatGPT 風格）
st.markdown("<div style='height:400px;overflow-y:auto;padding:8px 0;'>", unsafe_allow_html=True)
for msg in st.session_state["messages"]:
    align = "flex-end" if msg["role"] == "user" else "flex-start"
    bubble_color = "#2f4f4f" if msg["role"] == "user" else "#f1f0f0"
    text_color = "#fff" if msg["role"] == "user" else "#222"
    st.markdown(f"""
    <div style='display:flex;justify-content:{align};margin-bottom:8px;'>
      <div style='max-width:70%;background:{bubble_color};color:{text_color};padding:12px 16px;border-radius:16px;'>{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 若有語音回覆且是機器人訊息
    if msg["role"] == "assistant" and st.session_state["voice_reply"] and st.session_state["current_audio_file"]:
        if os.path.exists(st.session_state["current_audio_file"]):
            st.audio(st.session_state["current_audio_file"], format="audio/wav")
st.markdown("</div>", unsafe_allow_html=True)

# 使用者輸入區
st.markdown("---")
col1, col2 = st.columns([8,1])
with col1:
    user_input = st.text_input("請輸入您的問題...", key="chat_input_text", placeholder="例如：請推薦一些科技類的播客節目")
with col2:
    if st.button("送出", key="send_text_btn"):
        if user_input:
            st.session_state["messages"].append({"role": "user", "content": user_input, "time": datetime.now()})
            # 使用智能服務處理
            user_id = st.session_state.get("current_user", "guest")
            intelligent_reply = asyncio.run(process_with_intelligent_services(user_input, user_id))
            st.session_state["messages"].append({"role": "assistant", "content": intelligent_reply, "time": datetime.now()})
            
            # 語音回覆
            if st.session_state["voice_reply"]:
                voice = st.session_state.get("tts_voice_select", "podrina")
                volume = st.session_state.get("volume_slider", 0)
                speed = st.session_state.get("speed_slider", 0)
                pitch = st.session_state.get("pitch_slider", 0)
                
                audio_file = asyncio.run(generate_voice_reply(
                    text=intelligent_reply,
                    voice=voice,
                    volume=volume,
                    speed=speed,
                    pitch=pitch
                ))
                if audio_file:
                    st.session_state["current_audio_file"] = audio_file
            
            st.rerun()
