#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri TTS Provider for Podri TTS System

This module provides Podri TTS integration with four Taiwanese voices:
- Podrina (溫柔女聲)
- Podrisa (活潑女聲) 
- Podrina (穩重男聲)
- Podrisa (專業男聲)

Author: Podri Team
License: MIT
"""

import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles

# Edge TTS 導入處理
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("Edge TTS not installed. Please install with: pip install edge-tts")

logger = logging.getLogger(__name__)


class EdgeTTSVoice:
    """Edge TTS 語音配置類別"""
    
    def __init__(self, name: str, voice_id: str, description: str, 
                 rate: str = "+0%", volume: str = "+0%", 
                 pitch: str = "+0%", style: str = "general"):
        """
        初始化語音配置
        
        Args:
            name: 語音名稱
            voice_id: Edge TTS 語音 ID
            description: 語音描述
            rate: 語速調整
            volume: 音量調整
            pitch: 音調調整
            style: 語音風格
        """
        self.name = name
        self.voice_id = voice_id
        self.description = description
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.style = style
    
    def to_dict(self) -> Dict[str, str]:
        """轉換為字典格式"""
        return {
            "name": self.name,
            "voice_id": self.voice_id,
            "description": self.description,
            "rate": self.rate,
            "volume": self.volume,
            "pitch": self.pitch,
            "style": self.style
        }


class EdgeTTSProvider:
    """Edge TTS 提供者類別"""
    
    def __init__(self):
        """初始化 Edge TTS 提供者"""
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS is not available. Please install edge-tts package.")
        
        self.voices = self._initialize_voices()
        self.default_voice = "podrina"
        logger.info("Edge TTS Provider initialized successfully")
    
    def _initialize_voices(self) -> Dict[str, EdgeTTSVoice]:
        """初始化四種台灣語音"""
        voices = {
            "podrina": EdgeTTSVoice(
                name="Podrina (溫柔女聲)",
                voice_id="zh-TW-HsiaoChenNeural",
                description="溫柔親切的女聲，適合日常對話和情感表達",
                rate="+0%",
                volume="+0%",
                pitch="+0%",
                style="friendly"
            ),
            "podrisa": EdgeTTSVoice(
                name="Podrisa (活潑女聲)",
                voice_id="zh-TW-HsiaoYuNeural", 
                description="活潑開朗的女聲，適合娛樂內容和輕鬆話題",
                rate="+0%",
                volume="+0%",
                pitch="+0%",
                style="cheerful"
            ),
            "podrino": EdgeTTSVoice(
                name="Podrino (穩重男聲)",
                voice_id="zh-TW-YunJheNeural",
                description="穩重可靠的男聲，適合正式場合和專業內容",
                rate="+0%",
                volume="+0%",
                pitch="+0%",
                style="serious"
            ),
            "podriso": EdgeTTSVoice(
                name="Podriso (專業男聲)",
                voice_id="zh-TW-ZhiYuanNeural",
                description="專業權威的男聲，適合新聞播報和學術內容",
                rate="+0%",
                volume="+0%",
                pitch="+0%",
                style="professional"
            )
        }
        return voices
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        獲取可用的語音列表
        
        Returns:
            List[Dict[str, str]]: 語音列表
        """
        return [voice.to_dict() for voice in self.voices.values()]
    
    def get_voice(self, voice_id: str) -> Optional[EdgeTTSVoice]:
        """
        根據語音 ID 獲取語音配置
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            Optional[EdgeTTSVoice]: 語音配置，如果不存在則返回 None
        """
        return self.voices.get(voice_id)
    
    async def synthesize(self, text: str, voice_id: Optional[str] = None, 
                        rate: Optional[str] = None, volume: Optional[str] = None,
                        pitch: Optional[str] = None) -> Optional[bytes]:
        """
        使用 Edge TTS 合成語音
        
        Args:
            text: 要合成的文字
            voice_id: 語音 ID
            rate: 語速調整
            volume: 音量調整
            pitch: 音調調整
            
        Returns:
            Optional[bytes]: 音頻數據，如果失敗則返回 None
        """
        try:
            # 獲取語音配置
            actual_voice_id = voice_id or self.default_voice
            voice = self.get_voice(actual_voice_id)
            if not voice:
                logger.error(f"Unknown voice_id: {voice_id}")
                return None
            
            # 使用提供的參數或預設值
            actual_rate = rate or voice.rate
            actual_volume = volume or voice.volume
            actual_pitch = pitch or voice.pitch
            
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # 使用 Edge TTS 合成
                communicate = edge_tts.Communicate(
                    text, 
                    voice.voice_id,
                    rate=actual_rate,
                    volume=actual_volume,
                    pitch=actual_pitch
                )
                await communicate.save(temp_path)
                
                # 讀取音頻文件
                async with aiofiles.open(temp_path, 'rb') as f:
                    audio_data = await f.read()
                
                logger.info(f"Edge TTS synthesis successful: {len(audio_data)} bytes")
                return audio_data
                
            finally:
                # 清理臨時文件
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                    
        except Exception as e:
            logger.error(f"Edge TTS synthesis failed: {str(e)}")
            return None
    
    async def synthesize_to_base64(self, text: str, voice_id: Optional[str] = None,
                                  rate: Optional[str] = None, volume: Optional[str] = None,
                                  pitch: Optional[str] = None) -> Optional[str]:
        """
        合成語音並返回 Base64 編碼
        
        Args:
            text: 要合成的文字
            voice_id: 語音 ID
            rate: 語速調整
            volume: 音量調整
            pitch: 音調調整
            
        Returns:
            Optional[str]: Base64 編碼的音頻數據
        """
        audio_data = await self.synthesize(text, voice_id, rate, volume, pitch)
        if audio_data:
            return base64.b64encode(audio_data).decode('utf-8')
        return None
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """
        驗證語音 ID 是否有效
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            bool: 是否有效
        """
        return voice_id in self.voices
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """
        獲取語音信息
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            Optional[Dict[str, str]]: 語音信息
        """
        voice = self.get_voice(voice_id)
        return voice.to_dict() if voice else None


class EdgeTTSManager:
    """Edge TTS 管理器類別"""
    
    def __init__(self):
        """初始化 Edge TTS 管理器"""
        self.provider = EdgeTTSProvider()
        self._cache = {}
        logger.info("Edge TTS Manager initialized")
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """
        語音合成主方法
        
        Args:
            text: 要合成的文字
            voice_id: 語音 ID
            **kwargs: 其他參數
            
        Returns:
            Dict[str, Any]: 合成結果
        """
        try:
            # 驗證語音 ID
            if voice_id and not self.provider.validate_voice_id(voice_id):
                return {
                    "success": False,
                    "error": f"Invalid voice_id: {voice_id}",
                    "available_voices": self.provider.get_available_voices()
                }
            
            # 執行合成
            audio_data = await self.provider.synthesize(text, voice_id, **kwargs)
            
            if audio_data:
                return {
                    "success": True,
                    "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                    "text": text,
                    "voice_id": voice_id or self.provider.default_voice,
                    "provider": "edge_tts",
                    "audio_size": len(audio_data)
                }
            else:
                return {
                    "success": False,
                    "error": "Synthesis failed",
                    "text": text,
                    "voice_id": voice_id
                }
                
        except Exception as e:
            logger.error(f"Speech synthesis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": text,
                "voice_id": voice_id
            }
    
    def get_voices(self) -> List[Dict[str, str]]:
        """獲取所有可用語音"""
        return self.provider.get_available_voices()
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """獲取特定語音信息"""
        return self.provider.get_voice_info(voice_id)
    
    def is_available(self) -> bool:
        """檢查 Edge TTS 是否可用"""
        return EDGE_TTS_AVAILABLE


# 便捷函數
async def synthesize_text(text: str, voice_id: str = "podrina") -> Optional[str]:
    """
    便捷的語音合成函數
    
    Args:
        text: 要合成的文字
        voice_id: 語音 ID
        
    Returns:
        Optional[str]: Base64 編碼的音頻數據
    """
    manager = EdgeTTSManager()
    result = await manager.synthesize_speech(text, voice_id)
    return result.get("audio_data") if result["success"] else None


def list_voices() -> List[Dict[str, str]]:
    """
    便捷的語音列表函數
    
    Returns:
        List[Dict[str, str]]: 語音列表
    """
    manager = EdgeTTSManager()
    return manager.get_voices()


if __name__ == "__main__":
    # 測試代碼
    async def test():
        manager = EdgeTTSManager()
        
        # 測試語音列表
        voices = manager.get_voices()
        print("Available voices:")
        for voice in voices:
            print(f"  - {voice['name']}: {voice['description']}")
        
        # 測試語音合成
        text = "您好，我是 Podrina，您的智能語音助手。"
        result = await manager.synthesize_speech(text, "podrina")
        
        if result["success"]:
            print(f"Synthesis successful: {result['audio_size']} bytes")
        else:
            print(f"Synthesis failed: {result['error']}")
    
    asyncio.run(test()) 