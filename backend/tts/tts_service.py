#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合 TTS 服務和管理器
整合 GPT-SoVITS 和 Edge TTS 功能，提供統一的語音合成介面
"""

import asyncio
import aiohttp
import json
import base64
import os
import tempfile
from typing import Dict, Any, Optional, List
import logging
import requests
try:
    import edge_tts
except ImportError:
    edge_tts = None
import io
import wave
import numpy as np
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    """整合 TTS 服務和管理器類別"""
    
    def __init__(self):
        """初始化 TTS 服務"""
        # 服務 URL 配置
        self.gpt_sovits_url = os.getenv("GPT_SOVITS_URL", "http://127.0.0.1:9880")
        self.gpt_sovits_webui_url = os.getenv("GPT_SOVITS_WEBUI_URL", "http://127.0.0.1:7860")
        
        # 載入語音配置
        self.voice_config = self._load_voice_config()
        self.edge_tts_voices = self._get_edge_tts_voices()
        
        # 預設配置
        self.default_config = {
            "gpt_sovits": {
                "enabled": True,
                "top_k": 15,
                "top_p": 0.6,
                "temperature": 0.6,
                "speed": 1.0
            },
            "edge_tts": {
                "enabled": True,
                "voice": "zh-TW-HsiaoChenNeural",
                "rate": "+0%",
                "volume": "+0%"
            }
        }
    
        logger.info("TTS 服務初始化完成")
    
    def _load_voice_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """載入語音配置"""
        try:
            from config.voice_config import voice_config
            return voice_config.get_all_voices()
        except ImportError:
            logger.warning("無法載入語音配置，使用預設配置")
            return {
                "edge_tts": [
                    {"name": "Podria (溫柔女聲)", "id": "zh-TW-HsiaoChenNeural"},
                    {"name": "Podrick (穩重男聲)", "id": "zh-TW-YunJheNeural"},
                    {"name": "Podlisa (活潑女聲)", "id": "zh-TW-HanHanNeural"},
                    {"name": "Podvid (專業男聲)", "id": "zh-TW-ZhiYuanNeural"}
                ],
                "gpt_sovits": [
                    {"name": "Podri (訓練語音)", "id": "podri"},
                    {"name": "Podria (溫柔女聲)", "id": "podria"},
                    {"name": "Podrick (穩重男聲)", "id": "podrick"},
                    {"name": "Podlisa (活潑女聲)", "id": "podlisa"},
                    {"name": "Podvid (專業男聲)", "id": "podvid"}
                ]
            }
    
    def _get_edge_tts_voices(self) -> List[Dict[str, str]]:
        """獲取 Edge TTS 可用語音"""
        return [
            {"name": "Podria (溫柔女聲)", "id": "zh-TW-HsiaoChenNeural"},
            {"name": "Podrick (穩重男聲)", "id": "zh-TW-YunJheNeural"},
            {"name": "Podlisa (活潑女聲)", "id": "zh-TW-HanHanNeural"},
            {"name": "Podvid (專業男聲)", "id": "zh-TW-ZhiYuanNeural"}
        ]
    
    async def check_gpt_sovits_status(self) -> Dict[str, Any]:
        """檢查 GPT-SoVITS 服務狀態"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gpt_sovits_url}/", timeout=5) as response:
                    if response.status == 200:
                        return {"status": "running", "url": self.gpt_sovits_url}
                    else:
                        return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}
    
    async def check_gpt_sovits_webui_status(self) -> Dict[str, Any]:
        """檢查 GPT-SoVITS WebUI 狀態"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gpt_sovits_webui_url}/", timeout=5) as response:
                    if response.status == 200:
                        return {"status": "running", "url": self.gpt_sovits_webui_url}
                    else:
                        return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}
    
    async def synthesize_with_gpt_sovits(
        self, 
        text: str, 
        voice_id: str = "default",
        refer_wav_path: str = None,
        prompt_text: str = None,
        prompt_language: str = "zh",
        text_language: str = "zh",
        **kwargs
    ) -> Optional[bytes]:
        """使用 GPT-SoVITS 合成語音"""
        try:
            # 檢查服務狀態
            status = await self.check_gpt_sovits_status()
            if status["status"] != "running":
                logger.error(f"GPT-SoVITS 服務不可用: {status}")
                return None
            
            # 準備請求參數
            params = {
                "text": text,
                "text_lang": text_language,
                "top_k": kwargs.get("top_k", self.default_config["gpt_sovits"]["top_k"]),
                "top_p": kwargs.get("top_p", self.default_config["gpt_sovits"]["top_p"]),
                "temperature": kwargs.get("temperature", self.default_config["gpt_sovits"]["temperature"]),
                "speed_factor": kwargs.get("speed", self.default_config["gpt_sovits"]["speed"]),
                "text_split_method": "cut5",
                "batch_size": 1,
                "media_type": "wav",
                "streaming_mode": False
            }
            
            # 根據語音 ID 選擇參考音頻和提示文字
            if refer_wav_path and prompt_text:
                # 使用提供的參考音頻
                params.update({
                    "ref_audio_path": refer_wav_path,
                    "prompt_text": prompt_text,
                    "prompt_lang": prompt_language
                })
            else:
                # 根據語音 ID 選擇預設配置
                voice_configs = {
                    "podri": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podri_ref.wav",
                        "prompt_text": "您好，我是 Podri，您的智能語音助手。我會用溫暖自然的聲音，為您推薦最適合的內容，讓您的收聽體驗更加豐富。",
                        "prompt_lang": "zh"
                    },
                    "podria": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podria_ref.wav",
                        "prompt_text": "您好，我是 Podria，您的溫柔語音助手。我會用最溫暖的聲音，為您帶來最貼心的服務。",
                        "prompt_lang": "zh"
                    },
                    "podrick": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podrick_ref.wav",
                        "prompt_text": "您好，我是 Podrick，您的穩重語音助手。我會用最專業的聲音，為您提供最可靠的資訊。",
                        "prompt_lang": "zh"
                    },
                    "podlisa": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podlisa_ref.wav",
                        "prompt_text": "您好，我是 Podlisa，您的活潑語音助手。我會用最開朗的聲音，為您帶來最有趣的內容。",
                        "prompt_lang": "zh"
                    },
                    "podvid": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podvid_ref.wav",
                        "prompt_text": "您好，我是 Podvid，您的專業語音助手。我會用最權威的聲音，為您提供最準確的資訊。",
                        "prompt_lang": "zh"
                    },
                    "default": {
                        "ref_audio_path": "/app/GPT-SoVITS/raw/podri_ref.wav",
                        "prompt_text": "您好，我是 Podri，您的智能語音助手。我會用溫暖自然的聲音，為您推薦最適合的內容，讓您的收聽體驗更加豐富。",
                        "prompt_lang": "zh"
                    }
                }
                
                # 使用預設配置
                config = voice_configs.get(voice_id, voice_configs["default"])
                params.update(config)
            
            # 發送請求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gpt_sovits_url}/tts",
                    json=params,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"GPT-SoVITS 合成成功: {len(audio_data)} bytes")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"GPT-SoVITS 合成失敗: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"GPT-SoVITS 合成錯誤: {str(e)}")
            return None
    
    async def synthesize_with_edge_tts(
        self, 
        text: str, 
        voice: str = "",
        rate: str = "",
        volume: str = ""
    ) -> Optional[bytes]:
        """使用 Edge TTS 合成語音"""
        try:
            if edge_tts is None:
                logger.error("Edge TTS 未安裝")
                return None
            
            # 使用預設配置
            voice = voice or self.default_config["edge_tts"]["voice"]
            rate = rate or self.default_config["edge_tts"]["rate"]
            volume = volume or self.default_config["edge_tts"]["volume"]
            
            # 創建臨時檔案
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # 使用 Edge TTS 合成
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            await communicate.save(temp_path)
            
                # 讀取音頻檔案
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            logger.info(f"Edge TTS 合成成功: {len(audio_data)} bytes")
            return audio_data
                
            finally:
                # 清理臨時檔案
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Edge TTS 合成錯誤: {str(e)}")
            return None
    
    async def synthesize_speech(
        self, 
        text: str, 
        method: str = "auto",
        voice_id: str = "default",
        **kwargs
    ) -> Optional[bytes]:
        """
        智能語音合成
        
        Args:
            text: 要合成的文字
            method: 合成方法 ("auto", "gpt_sovits", "edge_tts")
            voice_id: 語音 ID
            **kwargs: 其他參數
            
        Returns:
            bytes: 音頻資料
        """
        try:
            if method == "auto":
                # 自動選擇最佳方法
                gpt_status = await self.check_gpt_sovits_status()
                if gpt_status["status"] == "running":
                    method = "gpt_sovits"
                else:
                    method = "edge_tts"
            
            if method == "gpt_sovits":
                return await self.synthesize_with_gpt_sovits(text, voice_id, **kwargs)
            elif method == "edge_tts":
                voice = self._get_voice_type(voice_id)
                return await self.synthesize_with_edge_tts(text, voice)
            else:
                logger.error(f"不支援的合成方法: {method}")
                return None
                
        except Exception as e:
            logger.error(f"語音合成失敗: {str(e)}")
            return None
    
    async def 語音合成(
        self, 
        text: str, 
        語音: str = "podri",
        語速: float = 1.0,
        音調: float = 1.0,
        音量: float = 1.0
    ) -> Dict[str, Any]:
        """
        中文介面的語音合成
        
        Args:
            text: 要合成的文字
            語音: 語音選擇
            語速: 語速倍數
            音調: 音調倍數
            音量: 音量倍數
            
        Returns:
            Dict[str, Any]: 合成結果
        """
        try:
            # 轉換參數
            voice_id = 語音
            speed = 語速
            
            # 執行合成
            audio_data = await self.synthesize_speech(
                    text=text,
                method="auto",
                voice_id=voice_id,
                speed=speed
                )
            
            if audio_data:
                return {
                    "成功": True,
                    "音訊檔案": base64.b64encode(audio_data).decode('utf-8'),
                    "文字": text,
                    "語音": 語音,
                    "方法": "auto"
                }
            else:
                return {
                    "成功": False,
                    "錯誤訊息": "語音合成失敗",
                    "文字": text,
                    "語音": 語音
                }
            
        except Exception as e:
            logger.error(f"語音合成錯誤: {str(e)}")
            return {
                "成功": False,
                "錯誤訊息": str(e),
                "文字": text,
                "語音": 語音
            }
    
    def _get_voice_type(self, voice_id: str) -> str:
        """根據語音 ID 獲取 Edge TTS 語音類型"""
        voice_mapping = {
            "podri": "zh-TW-YunJheNeural",      # 男聲
            "podria": "zh-TW-HsiaoChenNeural",  # 溫柔女聲
            "podrick": "zh-TW-YunJheNeural",    # 穩重男聲
            "podlisa": "zh-TW-HanHanNeural",    # 活潑女聲
            "podvid": "zh-TW-ZhiYuanNeural"     # 專業男聲
        }
        return voice_mapping.get(voice_id, "zh-TW-YunJheNeural")  # 預設使用男聲
    
    def 獲取可用語音(self) -> List[Dict[str, str]]:
        """獲取可用的語音列表"""
        voices = []
        
        # 添加 GPT-SoVITS 語音
        for voice in self.voice_config.get("gpt_sovits", []):
            voices.append({
                "name": voice["name"],
                "id": voice["id"],
                "type": "gpt_sovits"
            })
        
        # 添加 Edge TTS 語音
        for voice in self.edge_tts_voices:
            voices.append({
                "name": voice["name"],
                "id": voice["id"],
                "type": "edge_tts"
            })
        
        return voices
    
    def get_available_voices(self) -> Dict[str, List[Dict[str, str]]]:
        """獲取可用的語音列表（英文介面）"""
        return {
            "gpt_sovits": self.voice_config.get("gpt_sovits", []),
            "edge_tts": self.edge_tts_voices
        }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        gpt_status = await self.check_gpt_sovits_status()
        gpt_webui_status = await self.check_gpt_sovits_webui_status()
        
        return {
            "gpt_sovits": gpt_status,
            "gpt_sovits_webui": gpt_webui_status,
            "edge_tts": {
                "status": "available" if edge_tts else "unavailable",
                "error": "Edge TTS not installed" if not edge_tts else None
            }
        }
    
    def 獲取配置(self) -> Dict[str, Any]:
        """獲取當前配置"""
        return self.default_config.copy()
    
    def 更新配置(self, 新配置: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self.default_config.update(新配置)
            logger.info("配置更新成功")
            return True
        except Exception as e:
            logger.error(f"配置更新失敗: {str(e)}")
            return False
    
    def generate_mock_audio(self, text: str) -> bytes:
        """生成模擬音頻（用於測試）"""
        try:
            # 創建一個簡單的正弦波音頻
            sample_rate = 22050
            duration = 1.0  # 1 秒
            frequency = 440  # A4 音符
            
            # 生成正弦波
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = np.sin(2 * np.pi * frequency * t)
            
            # 轉換為 16-bit PCM
            audio = (audio * 32767).astype(np.int16)
            
            # 創建 WAV 檔案
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 單聲道
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio.tobytes())
                
                return wav_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"生成模擬音頻失敗: {str(e)}")
            return b""

# 向後相容性別名
TTSManager = TTSService