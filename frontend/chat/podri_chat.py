#!/usr/bin/env python3
"""
Podri 智能助理 - 簡化版本
整合 TTS 語音回覆功能
"""

import streamlit as st
import asyncio
import requests
import base64
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

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
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "voice_reply" not in st.session_state:
    st.session_state["voice_reply"] = False

# TTS Backend 整合函數
async def call_tts_backend(text: str, voice: str, volume: str, speed: str, pitch: str) -> Optional[str]:
    """調用 Podri TTS Backend 生成語音"""
    try:
        # 調用本地 Podri TTS 服務
        tts_url = "http://localhost:8003/synthesize"
        
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
    # 簡化的回覆邏輯
    responses = {
        "請推薦一些有趣的播客節目": "我推薦您聽聽《股癌》、《科技報橘》和《矽谷輕鬆談》，這些都是非常有趣的播客節目！",
        "我想搜尋關於科技創新的播客內容": "關於科技創新，我推薦《科技報橘》和《矽谷輕鬆談》，它們經常討論最新的科技趨勢和創新話題。",
        "請告訴我如何使用這個播客助理": "我是 Podri 智能助理，您可以：\n1. 直接輸入問題\n2. 點擊快捷按鈕\n3. 啟用語音回覆功能\n4. 選擇不同的語音設定",
        "請推薦商業類播客": "商業類播客我推薦《股癌》、《天下學習》和《商業週刊》，這些都是高質量的商業內容。"
    }
    
    return responses.get(query, f"關於「{query}」，我正在學習中，請稍後再試！")

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
    st.markdown("### 語音設定")
    st.session_state["voice_reply"] = st.checkbox("啟用語音回覆", value=st.session_state["voice_reply"])
    
    if st.session_state["voice_reply"]:
        # TTS 語音選擇
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
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ TTS 服務正常")
        else:
            st.warning("⚠️ TTS 服務異常")
    except:
        st.error("❌ TTS 服務未啟動")

# 主區塊
st.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>
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
            intelligent_reply = asyncio.run(process_with_intelligent_services(q, "guest"))
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

# 聊天訊息區
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
    if msg["role"] == "assistant" and st.session_state["voice_reply"] and st.session_state.get("current_audio_file"):
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
            intelligent_reply = asyncio.run(process_with_intelligent_services(user_input, "guest"))
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
