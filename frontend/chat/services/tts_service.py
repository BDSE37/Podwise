#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 服務模組
處理語音合成相關功能
"""

import asyncio
import aiohttp
import json
import base64
import io
import time
from typing import Dict, Any, List, Optional
import os


class TTSService:
    """TTS 服務類別"""
    
    def __init__(self):
        """初始化 TTS 服務"""
        # 服務端點配置
        self.k8s_tts_url = os.getenv("K8S_TTS_URL", "http://localhost:30001")
        self.tts_url = os.getenv("TTS_URL", "http://localhost:8001")
        self.container_tts_url = os.getenv("CONTAINER_TTS_URL", "http://tts:8001")
        
        # 預設語音選項
        self.voice_options = {
            "zh-TW-HsiaoChenNeural": "Podria (溫柔女聲)",
            "zh-TW-YunJheNeural": "Podrick (穩重男聲)",
            "zh-TW-HanHanNeural": "Podlisa (活潑女聲)",
            "zh-TW-ZhiYuanNeural": "Podvid (專業男聲)"
        }
        self.voice_categories = {
            "Edge TTS 語音": ["zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-TW-HanHanNeural", "zh-TW-ZhiYuanNeural"]
        }
    
    async def generate_speech(self, text: str, voice: str) -> Optional[Dict[str, Any]]:
        """生成語音"""
        try:
            # 嘗試從 TTS 服務生成語音
            tts_endpoints = [
                self.k8s_tts_url,      # K8s NodePort 服務
                self.tts_url,          # 本地開發
                self.container_tts_url # 容器環境
            ]
            
            for endpoint in tts_endpoints:
                try:
                    payload = {
                        "text": text,
                        "voice": voice,
                        "speed": 1.0,
                        "volume": 0.8
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{endpoint}/synthesize",
                            json=payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data.get("success"):
                                    audio_data = base64.b64decode(data.get("audio", ""))
                                    
                                    return {
                                        "success": True,
                                        "audio_data": audio_data,
                                        "duration": self._estimate_audio_duration(audio_data, text),
                                        "voice": voice,
                                        "text": text
                                    }
                                else:
                                    continue
                            else:
                                continue
                                
                except Exception as e:
                    continue
            
            # 如果所有服務都失敗，返回錯誤
            return {
                "success": False,
                "error": "所有 TTS 服務都無法連接"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"TTS 服務錯誤: {str(e)}"
            }
    
    def _estimate_audio_duration(self, audio_data: bytes, text: str) -> float:
        """估算音訊時長"""
        # 簡單的估算：每字約 0.3 秒
        char_count = len(text)
        estimated_duration = char_count * 0.3
        
        # 根據音訊檔案大小調整
        if audio_data:
            # 假設 16kHz, 16bit 音訊
            bytes_per_second = 16000 * 2  # 16kHz * 2 bytes
            actual_duration = len(audio_data) / bytes_per_second
            return min(estimated_duration, actual_duration)
        
        return estimated_duration
    
    def get_voice_list(self) -> List[Dict[str, Any]]:
        """獲取語音列表"""
        try:
            # 這裡會從 TTS 服務獲取語音列表
            # 目前返回預設語音
            voices = []
            for voice_id, voice_name in self.voice_options.items():
                voices.append({
                    "id": voice_id,
                    "name": voice_name,
                    "type": "edge_tts"
                })
            return voices
        except Exception as e:
            print(f"❌ 獲取語音列表失敗: {str(e)}")
            return []
    
    def check_service_status(self) -> Dict[str, Any]:
        """檢查服務狀態"""
        try:
            import requests
            
            # 嘗試從 TTS 服務獲取健康狀態
            tts_endpoints = [
                self.k8s_tts_url,      # K8s NodePort 服務
                self.tts_url,          # 本地開發
                self.container_tts_url # 容器環境
            ]
            
            for endpoint in tts_endpoints:
                try:
                    response = requests.get(f"{endpoint}/health", timeout=5)
                    if response.status_code == 200:
                        return {"status": "healthy", "endpoint": endpoint}
                except Exception as e:
                    continue
            
            return {"status": "unhealthy", "error": "無法連接到任何 TTS 服務"}
            
        except ImportError:
            return {"status": "unhealthy", "error": "缺少 requests 模組"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """獲取語音資訊"""
        voice_info_map = {
            "podri": {
                "name": "Podri (智能男聲)",
                "description": "智能男聲，適合一般對話和日常交流",
                "gender": "male",
                "language": "zh-TW",
                "style": "自然親切",
                "best_for": "一般對話、客服、導覽"
            },
            "podria": {
                "name": "Podria (溫柔女聲)",
                "description": "溫柔甜美的女聲，適合日常對話和情感表達",
                "gender": "female",
                "language": "zh-TW",
                "style": "溫柔甜美",
                "best_for": "日常對話、情感內容、兒童內容"
            },
            "podrick": {
                "name": "Podrick (穩重男聲)",
                "description": "穩重成熟的男聲，適合專業內容和正式場合",
                "gender": "male",
                "language": "zh-TW",
                "style": "穩重專業",
                "best_for": "專業內容、新聞播報、教育內容"
            },
            "podlisa": {
                "name": "Podlisa (活潑女聲)",
                "description": "活潑開朗的女聲，適合娛樂內容和輕鬆話題",
                "gender": "female",
                "language": "zh-TW",
                "style": "活潑開朗",
                "best_for": "娛樂內容、輕鬆話題、活動主持"
            },
            "podvid": {
                "name": "Podvid (專業男聲)",
                "description": "專業權威的男聲，適合新聞播報和正式場合",
                "gender": "male",
                "language": "zh-TW",
                "style": "專業權威",
                "best_for": "新聞播報、正式場合、權威內容"
            }
        }
        return voice_info_map.get(voice_id, {}) 