#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri TTS 服務模組

提供基於 Microsoft Edge TTS 的語音合成服務，支援三種台灣語音：
- Podrina (溫柔女聲)
- Podrisa (活潑女聲)
- Podrino (穩重男聲)

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

# 修正相對導入問題
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from providers.edge_tts_provider import EdgeTTSManager
from config.voice_config import VoiceConfig

# 使用相對路徑引用共用工具
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TTSService:
    """Podri TTS 服務類別
    
    提供統一的語音合成介面，支援多種台灣語音選項。
    遵循 Google Python Style Guide 的 OOP 原則。
    """
    
    def __init__(self):
        """初始化 TTS 服務
        
        Raises:
            ImportError: 當 Edge TTS 不可用時拋出
            RuntimeError: 當初始化失敗時拋出
        """
        self._edge_tts_manager: Optional[EdgeTTSManager] = None
        self._voice_config: VoiceConfig = VoiceConfig()
        self._default_voice: str = "podrina"
        
        # 初始化 Edge TTS 管理器
        try:
            self._edge_tts_manager = EdgeTTSManager()
            logger.info("Edge TTS Manager 初始化成功")
        except ImportError as e:
            logger.error(f"Edge TTS 不可用: {e}")
            raise ImportError("Edge TTS 未安裝，請執行: pip install edge-tts")
        except Exception as e:
            logger.error(f"Edge TTS Manager 初始化失敗: {e}")
            raise RuntimeError(f"TTS 服務初始化失敗: {e}")
    
    @property
    def edge_tts_manager(self) -> Optional[EdgeTTSManager]:
        """獲取 Edge TTS 管理器
        
        Returns:
            Optional[EdgeTTSManager]: Edge TTS 管理器實例
        """
        return self._edge_tts_manager
    
    @property
    def voice_config(self) -> VoiceConfig:
        """獲取語音配置管理器
        
        Returns:
            VoiceConfig: 語音配置管理器實例
        """
        return self._voice_config
    
    @property
    def default_voice(self) -> str:
        """獲取預設語音 ID
        
        Returns:
            str: 預設語音 ID
        """
        return self._default_voice
    
    def is_available(self) -> bool:
        """檢查 TTS 服務是否可用
        
        Returns:
            bool: 服務是否可用
        """
        return self._edge_tts_manager is not None and self._edge_tts_manager.is_available()
    
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
            RuntimeError: 當 TTS 服務不可用時
        """
        if not text or not text.strip():
            raise ValueError("文字內容不能為空")
        
        if not self.is_available():
            raise RuntimeError("TTS 服務不可用")
        
        try:
            # 使用預設語音如果未指定
            actual_voice_id = voice_id or self._default_voice
            
            # 驗證語音ID是否有效
            if not self._voice_config.validate_voice_id(actual_voice_id):
                logger.warning(f"無效的語音ID: {actual_voice_id}，使用預設語音: {self._default_voice}")
                actual_voice_id = self._default_voice
            
            # 執行語音合成
            if self._edge_tts_manager:
                result = await self._edge_tts_manager.synthesize_speech(
                    text=text,
                    voice_id=actual_voice_id,
                    rate=rate,
                    volume=volume,
                    pitch=pitch
                )
            else:
                return None
            
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
            List[Dict[str, str]]: 語音列表，每個語音包含 id、name、description、gender、style、voice_id
        """
        if not self.is_available():
            return []
        
        if self._edge_tts_manager:
            return self._edge_tts_manager.get_voices()
        
        return []
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """獲取特定語音信息
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            Optional[Dict[str, str]]: 語音信息，不存在時返回 None
        """
        if not self.is_available():
            return None
        
        if self._edge_tts_manager:
            return self._edge_tts_manager.get_voice_info(voice_id)
        return None
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """驗證語音 ID 是否有效
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            bool: 是否有效
        """
        if not self.is_available():
            return False
        
        if self._edge_tts_manager and self._edge_tts_manager.provider:
            return self._edge_tts_manager.provider.validate_voice_id(voice_id)
        return False
    
    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態
        
        Returns:
            Dict[str, Any]: 服務狀態信息
        """
        status = {
            "service_name": "Podri TTS Service",
            "version": "1.0.0",
            "status": "running" if self.is_available() else "unavailable",
            "edge_tts": {
                "available": self.is_available(),
                "default_voice": self._default_voice,
                "voice_count": len(self.get_available_voices())
            }
        }
        
        if self.is_available():
            status["edge_tts"]["voices"] = self.get_available_voices()
        
        return status
    
    def save_audio_to_file(self, audio_data: bytes, output_path: str) -> bool:
        """將音頻數據保存到文件
        
        Args:
            audio_data: 音頻數據
            output_path: 輸出文件路徑
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 確保目錄存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"音頻文件保存成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存音頻文件失敗: {e}")
            return False
    
    def create_wav_file(self, audio_data: bytes, sample_rate: int = 24000) -> bytes:
        """創建 WAV 格式的音頻文件
        
        Args:
            audio_data: 原始音頻數據
            sample_rate: 採樣率，預設 24000
            
        Returns:
            bytes: WAV 格式的音頻數據
        """
        try:
            # 創建 WAV 文件
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 單聲道
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                return wav_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"創建 WAV 文件失敗: {e}")
            return audio_data  # 返回原始數據
    
    def get_voice_statistics(self) -> Dict[str, Any]:
        """獲取語音統計信息
        
        Returns:
            Dict[str, Any]: 語音統計信息
        """
        voices = self.get_available_voices()
        
        gender_stats = {}
        style_stats = {}
        
        for voice in voices:
            gender = voice.get("gender", "unknown")
            style = voice.get("style", "unknown")
            
            gender_stats[gender] = gender_stats.get(gender, 0) + 1
            style_stats[style] = style_stats.get(style, 0) + 1
        
        return {
            "total_voices": len(voices),
            "gender_distribution": gender_stats,
            "style_distribution": style_stats,
            "default_voice": self._default_voice
        }