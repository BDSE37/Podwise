# src/core/audio_handler.py
import io
from typing import Optional
import numpy as np
from pydub import AudioSegment

from models.voice_profile import VoiceProfile
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AudioHandler:
    """音頻處理器 - 處理音頻後製效果"""
    
    def __init__(self):
        self.sample_rate = 24000
        
    def process(self, audio_data: bytes, voice_profile: VoiceProfile) -> bytes:
        """
        處理音頻數據
        
        Args:
            audio_data: 原始音頻數據
            voice_profile: 語音配置
            
        Returns:
            處理後的音頻數據
        """
        try:
            # 如果不需要特殊處理，直接返回
            if voice_profile.rate == 1.0 and voice_profile.pitch == 0:
                return audio_data
            
            # 使用 pydub 處理音頻
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            
            # 調整音量（如需要）
            # audio = audio + 3  # 增加 3dB
            
            # 導出處理後的音頻
            output = io.BytesIO()
            audio.export(output, format="mp3")
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"音頻處理失敗，返回原始數據: {e}")
            return audio_data
