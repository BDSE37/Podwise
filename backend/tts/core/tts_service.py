#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri TTS 服務模組

提供基於 Microsoft Podri TTS 的語音合成服務，支援四種台灣語音：
- Podrina (溫柔女聲)
- Podrisa (活潑女聲)
- Podrino (穩重男聲)
- Podriso (專業男聲)

Author: Podri Team
License: MIT
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
import wave
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..providers.edge_tts_provider import EdgeTTSManager
from ..config.voice_config import VoiceConfig

# 使用相對路徑引用共用工具
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TTSService:
    """Podri TTS 服務類別
    
    提供統一的語音合成介面，支援多種台灣語音選項。
    """
    
    def __init__(self):
        """初始化 TTS 服務
        
        Raises:
            ImportError: 當 Edge TTS 不可用時拋出
        """
        self._podri_tts_manager = None
        self._voice_config = VoiceConfig()
        self._default_voice = "podrina"
        
        # 初始化 Podri TTS 管理器
        try:
            self._podri_tts_manager = EdgeTTSManager()
            logger.info("Podri TTS Manager 初始化成功")
        except ImportError as e:
            logger.error(f"Podri TTS 不可用: {e}")
            raise ImportError("Podri TTS 未安裝，請執行: pip install edge-tts")
        except Exception as e:
            logger.error(f"Podri TTS Manager 初始化失敗: {e}")
            raise
    
    @property
    def podri_tts_manager(self) -> Optional[EdgeTTSManager]:
        """獲取 Podri TTS 管理器
        
        Returns:
            Optional[PodriTTSManager]: Podri TTS 管理器實例
        """
        return self._podri_tts_manager
    
    @property
    def voice_config(self) -> VoiceConfig:
        """獲取語音配置管理器
        
        Returns:
            VoiceConfig: 語音配置管理器實例
        """
        return self._voice_config
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> Optional[bytes]:
        """語音合成主方法
        
        Args:
            text: 要合成的文字
            voice_id: 語音 ID，預設為 podrina
            rate: 語速調整，格式如 "+10%"
            volume: 音量調整，格式如 "+5%"
            pitch: 音調調整，格式如 "+2%"
            
        Returns:
            Optional[bytes]: 音頻數據，失敗時返回 None
            
        Raises:
            ValueError: 當文字為空或無效時
        """
        if not text or not text.strip():
            raise ValueError("文字內容不能為空")
        
        if not self._podri_tts_manager:
            logger.error("Podri TTS Manager 不可用")
            return None
        
        try:
            # 使用預設語音如果未指定
            actual_voice_id = voice_id or self._default_voice
            
            # 執行語音合成
            result = await self._podri_tts_manager.synthesize_speech(
                text=text,
                voice_id=actual_voice_id,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            if result["success"]:
                # 將 Base64 轉換回 bytes
                audio_data = base64.b64decode(result["audio_data"])
                logger.info(f"語音合成成功: {len(audio_data)} bytes, 語音: {actual_voice_id}")
                return audio_data
            else:
                logger.error(f"語音合成失敗: {result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"語音合成錯誤: {str(e)}")
            return None
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """獲取可用的語音列表
        
        Returns:
            List[Dict[str, str]]: 語音列表，每個語音包含 id、name、description
        """
        if not self._podri_tts_manager:
            return []
        
        return self._podri_tts_manager.get_voices()
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """獲取特定語音信息
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            Optional[Dict[str, str]]: 語音信息，不存在時返回 None
        """
        if not self._podri_tts_manager:
            return None
        
        return self._podri_tts_manager.get_voice_info(voice_id)
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """驗證語音 ID 是否有效
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            bool: 是否有效
        """
        if not self._podri_tts_manager:
            return False
        
        return self._podri_tts_manager.provider.validate_voice_id(voice_id)
    
    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態
        
        Returns:
            Dict[str, Any]: 服務狀態信息
        """
        return {
            "podri_tts": {
                "status": "available" if self._podri_tts_manager else "unavailable",
                "available_voices": len(self.get_available_voices()),
                "default_voice": self._default_voice
            }
        }
    
    def save_audio_to_file(self, audio_data: bytes, output_path: str) -> bool:
        """將音頻數據保存到文件
        
        Args:
            audio_data: 音頻數據
            output_path: 輸出文件路徑
            
        Returns:
            bool: 保存是否成功
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"音頻文件保存成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存音頻文件失敗: {e}")
            return False
    
    def create_wav_file(self, audio_data: bytes, sample_rate: int = 24000) -> bytes:
        """將原始音頻數據轉換為 WAV 格式
        
        Args:
            audio_data: 原始音頻數據
            sample_rate: 採樣率，預設 24000Hz
            
        Returns:
            bytes: WAV 格式的音頻數據
        """
        try:
            # 創建 WAV 文件
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 單聲道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"創建 WAV 文件失敗: {e}")
            return audio_data  # 返回原始數據
    
    # 中文介面方法
    async def 語音合成(
        self,
        text: str,
        語音: Optional[str] = None,
        語速: Optional[str] = None,
        音量: Optional[str] = None,
        音調: Optional[str] = None
    ) -> Optional[bytes]:
        """中文介面的語音合成方法
        
        Args:
            text: 要合成的文字
            語音: 語音 ID
            語速: 語速調整
            音量: 音量調整
            音調: 音調調整
            
        Returns:
            Optional[bytes]: 音頻數據
        """
        return await self.synthesize_speech(
            text=text,
            voice_id=語音,
            rate=語速,
            volume=音量,
            pitch=音調
        )
    
    def 獲取可用語音(self) -> List[Dict[str, str]]:
        """中文介面的獲取語音列表方法
        
        Returns:
            List[Dict[str, str]]: 語音列表
        """
        return self.get_available_voices()
    
    def 獲取語音信息(self, 語音_id: str) -> Optional[Dict[str, str]]:
        """中文介面的獲取語音信息方法
        
        Args:
            語音_id: 語音 ID
            
        Returns:
            Optional[Dict[str, str]]: 語音信息
        """
        return self.get_voice_info(語音_id)
    
    async def 獲取服務狀態(self) -> Dict[str, Any]:
        """中文介面的獲取服務狀態方法
        
        Returns:
            Dict[str, Any]: 服務狀態
        """
        return await self.get_service_status()