#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語音錄製服務
整合瀏覽器語音錄製和 STT 服務
"""

import streamlit as st
import asyncio
import aiohttp
import base64
import io
import tempfile
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VoiceRecorder:
    """語音錄製器 - 整合瀏覽器錄製和 STT 服務"""
    
    def __init__(self, stt_url: str):
        """
        初始化語音錄製器
        
        Args:
            stt_url: STT 服務的 URL
        """
        self.stt_url = stt_url
        self.is_recording = False
        self.audio_data = None
        
    def render_voice_recorder(self) -> Optional[str]:
        """
        渲染語音錄製介面並返回轉錄的文字
        
        Returns:
            轉錄的文字，如果沒有錄製則返回 None
        """
        st.markdown("### 🎤 語音輸入")
        
        # 使用文件上傳器來模擬語音錄製
        uploaded_file = st.file_uploader(
            "上傳音頻文件或錄製語音",
            type=['wav', 'mp3', 'm4a'],
            help="支援 WAV、MP3、M4A 格式的音頻文件"
        )
        
        if uploaded_file is not None:
            # 讀取音頻數據
            audio_bytes = uploaded_file.read()
            
            # 顯示音頻播放器
            st.audio(audio_bytes, format=f"audio/{uploaded_file.type}")
            
            # 顯示處理中狀態
            with st.spinner("正在轉錄語音..."):
                # 調用 STT 服務
                transcribed_text = self._transcribe_audio(audio_bytes)
                
                if transcribed_text:
                    st.success(f"✅ 轉錄成功: {transcribed_text}")
                    return transcribed_text
                else:
                    st.error("❌ 語音轉錄失敗")
                    return None
        
        return None
    
    def _transcribe_audio(self, audio_bytes: bytes) -> Optional[str]:
        """
        調用 STT 服務轉錄音頻
        
        Args:
            audio_bytes: 音頻數據
            
        Returns:
            轉錄的文字
        """
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # 使用 requests 發送文件到 STT 服務
                import requests
                
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('audio.wav', f, 'audio/wav')}
                    data = {'language': 'zh'}
                    
                    response = requests.post(
                        f"{self.stt_url}/transcribe",
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('text', '').strip()
                else:
                    logger.error(f"STT 服務錯誤: {response.status_code} - {response.text}")
                    return None
                    
            finally:
                # 清理臨時文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"語音轉錄失敗: {str(e)}")
            return None
    
    async def transcribe_audio_async(self, audio_bytes: bytes) -> Optional[str]:
        """
        異步調用 STT 服務轉錄音頻
        
        Args:
            audio_bytes: 音頻數據
            
        Returns:
            轉錄的文字
        """
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # 使用 aiohttp 發送文件到 STT 服務
                async with aiohttp.ClientSession() as session:
                    with open(temp_file_path, 'rb') as f:
                        data = aiohttp.FormData()
                        data.add_field('file', f, filename='audio.wav', content_type='audio/wav')
                        data.add_field('language', 'zh')
                        
                        async with session.post(
                            f"{self.stt_url}/transcribe",
                            data=data,
                            timeout=30
                        ) as response:
                            
                            if response.status == 200:
                                result = await response.json()
                                return result.get('text', '').strip()
                            else:
                                error_text = await response.text()
                                logger.error(f"STT 服務錯誤: {response.status} - {error_text}")
                                return None
                                
            finally:
                # 清理臨時文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"語音轉錄失敗: {str(e)}")
            return None
    
    def test_stt_connection(self) -> bool:
        """
        測試 STT 服務連接
        
        Returns:
            連接是否成功
        """
        try:
            import requests
            response = requests.get(f"{self.stt_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"STT 服務連接測試失敗: {str(e)}")
            return False
    
    async def test_stt_connection_async(self) -> bool:
        """
        異步測試 STT 服務連接
        
        Returns:
            連接是否成功
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.stt_url}/health", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"STT 服務連接測試失敗: {str(e)}")
            return False 