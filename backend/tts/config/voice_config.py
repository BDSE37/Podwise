#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri TTS 語音配置模組

定義四種台灣語音：
- Podrina (溫柔女聲)
- Podrisa (活潑女聲)
- Podrino (穩重男聲)
- Podriso (專業男聲)

Author: Podri Team
License: MIT
"""

import os
import sys
from typing import Dict, List, Any, Optional

# 添加 backend 路徑以引用共用工具
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from utils.logging_config import get_logger

logger = get_logger(__name__)


class VoiceConfig:
    """Edge TTS 語音配置管理類別
    
    管理四種台灣語音的配置信息，提供語音查詢和管理功能。
    """
    
    def __init__(self):
        """初始化語音配置管理器"""
        self._voices = self._initialize_voices()
        logger.info("Edge TTS 語音配置初始化完成")
    
    def _initialize_voices(self) -> Dict[str, List[Dict[str, Any]]]:
        """初始化四種台灣語音配置
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 語音配置字典
        """
        return {
            "edge_tts": [
                {
                    "id": "podrina",
                    "name": "Podrina (溫柔女聲)",
                    "voice_id": "zh-TW-HsiaoChenNeural",
                    "description": "溫柔親切的女聲，適合日常對話和情感表達",
                    "type": "edge_tts",
                    "language": "zh-TW",
                    "gender": "female",
                    "style": "friendly",
                    "rate": "+0%",
                    "volume": "+0%",
                    "pitch": "+0%"
                },
                {
                    "id": "podrisa",
                    "name": "Podrisa (活潑女聲)",
                    "voice_id": "zh-TW-HanHanNeural",
                    "description": "活潑開朗的女聲，適合娛樂內容和輕鬆話題",
                    "type": "edge_tts",
                    "language": "zh-TW",
                    "gender": "female",
                    "style": "cheerful",
                    "rate": "+0%",
                    "volume": "+0%",
                    "pitch": "+0%"
                },
                {
                    "id": "podrino",
                    "name": "Podrino (穩重男聲)",
                    "voice_id": "zh-TW-YunJheNeural",
                    "description": "穩重可靠的男聲，適合正式場合和專業內容",
                    "type": "edge_tts",
                    "language": "zh-TW",
                    "gender": "male",
                    "style": "serious",
                    "rate": "+0%",
                    "volume": "+0%",
                    "pitch": "+0%"
                },
                {
                    "id": "podriso",
                    "name": "Podriso (專業男聲)",
                    "voice_id": "zh-TW-ZhiYuanNeural",
                    "description": "專業權威的男聲，適合新聞播報和學術內容",
                    "type": "edge_tts",
                    "language": "zh-TW",
                    "gender": "male",
                    "style": "professional",
                    "rate": "+0%",
                    "volume": "+0%",
                    "pitch": "+0%"
                }
            ]
        }
    
    def get_all_voices(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取所有語音配置
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 所有語音配置
        """
        return self._voices.copy()
    
    def get_voices_by_type(self, voice_type: str) -> List[Dict[str, Any]]:
        """根據類型獲取語音配置
        
        Args:
            voice_type: 語音類型 (如 "edge_tts")
            
        Returns:
            List[Dict[str, Any]]: 指定類型的語音配置列表
        """
        return self._voices.get(voice_type, [])
    
    def get_voice_by_id(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取語音配置
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            Optional[Dict[str, Any]]: 語音配置，如果不存在則返回 None
        """
        for voice_type, voices in self._voices.items():
            for voice in voices:
                if voice["id"] == voice_id:
                    return voice
        return None
    
    def get_voice_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        """根據性別獲取語音配置
        
        Args:
            gender: 性別 ("male", "female")
            
        Returns:
            List[Dict[str, Any]]: 指定性別的語音配置
        """
        result = []
        for voice_type, voices in self._voices.items():
            for voice in voices:
                if voice.get("gender") == gender:
                    result.append(voice)
        return result
    
    def get_voice_by_language(self, language: str) -> List[Dict[str, Any]]:
        """根據語言獲取語音配置
        
        Args:
            language: 語言代碼 (如 "zh-TW")
            
        Returns:
            List[Dict[str, Any]]: 指定語言的語音配置
        """
        result = []
        for voice_type, voices in self._voices.items():
            for voice in voices:
                if voice.get("language") == language:
                    result.append(voice)
        return result
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """驗證語音 ID 是否有效
        
        Args:
            voice_id: 語音 ID
            
        Returns:
            bool: 是否有效
        """
        return self.get_voice_by_id(voice_id) is not None
    
    def get_voice_count(self) -> Dict[str, int]:
        """獲取各類型語音數量
        
        Returns:
            Dict[str, int]: 各類型語音數量
        """
        return {voice_type: len(voices) for voice_type, voices in self._voices.items()}
    
    def get_available_voice_types(self) -> List[str]:
        """獲取可用的語音類型
        
        Returns:
            List[str]: 可用的語音類型列表
        """
        return list(self._voices.keys())
    
    def get_voice_statistics(self) -> Dict[str, Any]:
        """獲取語音統計信息
        
        Returns:
            Dict[str, Any]: 語音統計信息
        """
        total_voices = sum(len(voices) for voices in self._voices.values())
        gender_stats = {
            "male": len(self.get_voice_by_gender("male")),
            "female": len(self.get_voice_by_gender("female"))
        }
        language_stats = {
            "zh-TW": len(self.get_voice_by_language("zh-TW"))
        }
        
        return {
            "total_voices": total_voices,
            "voice_types": self.get_voice_count(),
            "gender_distribution": gender_stats,
            "language_distribution": language_stats
        }


# 全局實例
voice_config = VoiceConfig()


def get_all_voices() -> Dict[str, List[Dict[str, Any]]]:
    """便捷函數：獲取所有語音配置
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: 所有語音配置
    """
    return voice_config.get_all_voices()


def get_voices_by_type(voice_type: str) -> List[Dict[str, Any]]:
    """便捷函數：根據類型獲取語音配置
    
    Args:
        voice_type: 語音類型
        
    Returns:
        List[Dict[str, Any]]: 指定類型的語音配置
    """
    return voice_config.get_voices_by_type(voice_type)


def get_voice_by_id(voice_id: str) -> Optional[Dict[str, Any]]:
    """便捷函數：根據 ID 獲取語音配置
    
    Args:
        voice_id: 語音 ID
        
    Returns:
        Optional[Dict[str, Any]]: 語音配置
    """
    return voice_config.get_voice_by_id(voice_id)


def validate_voice_id(voice_id: str) -> bool:
    """便捷函數：驗證語音 ID
    
    Args:
        voice_id: 語音 ID
        
    Returns:
        bool: 是否有效
    """
    return voice_config.validate_voice_id(voice_id) 