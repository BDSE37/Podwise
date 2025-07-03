"""
Whisper STT 模組
使用系統預設音頻輸入和 Whisper Medium 模型
"""

from typing import Dict, List, Optional, Any
import torch
import whisper
import numpy as np
import sounddevice as sd
import soundfile as sf
import asyncio
from datetime import datetime

class WhisperSTT:
    """Whisper STT 控制器"""

    def __init__(self, config: Dict):
        """
        初始化 Whisper STT
        
        Args:
            config: 配置參數
        """
        self.config = config
        self._init_whisper()
        self._init_audio_device()

    def _init_whisper(self):
        """初始化 Whisper 模型"""
        self.model = whisper.load_model(
            self.config["whisper_model"],
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def _init_audio_device(self):
        """初始化音頻設備"""
        try:
            # 獲取系統預設輸入設備
            devices = sd.query_devices()
            input_device = None
            
            # 尋找第一個輸入設備
            for device in devices:
                if device['max_input_channels'] > 0:
                    input_device = device['name']
                    break
            
            if input_device:
                self.input_device = input_device
                print(f"使用音頻輸入設備: {input_device}")
            else:
                print("未找到可用的音頻輸入設備")
                self.input_device = None

        except Exception as e:
            print(f"初始化音頻設備時發生錯誤: {str(e)}")
            self.input_device = None

    async def record_audio(
        self,
        duration: float = 5.0,
        sample_rate: int = 16000
    ) -> np.ndarray:
        """
        錄製音頻
        
        Args:
            duration: 錄製時長（秒）
            sample_rate: 採樣率
            
        Returns:
            np.ndarray: 音頻數據
        """
        try:
            if not self.input_device:
                raise Exception("未找到可用的音頻輸入設備")

            # 錄製音頻
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.input_device
            )
            sd.wait()

            return audio_data

        except Exception as e:
            print(f"錄製音頻時發生錯誤: {str(e)}")
            return np.array([])

    async def transcribe_audio(
        self,
        audio_data: np.ndarray,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        轉錄音頻
        
        Args:
            audio_data: 音頻數據
            language: 語言代碼
            
        Returns:
            Dict[str, Any]: 轉錄結果
        """
        try:
            # 轉錄音頻
            result = self.model.transcribe(
                audio_data,
                language=language,
                task="transcribe"
            )

            return {
                "text": result["text"],
                "segments": result["segments"],
                "language": result["language"]
            }

        except Exception as e:
            print(f"轉錄音頻時發生錯誤: {str(e)}")
            return {
                "text": "",
                "segments": [],
                "language": language
            }

    async def process_audio(self) -> Dict[str, Any]:
        """
        處理音頻
        
        Returns:
            Dict[str, Any]: 處理結果
        """
        try:
            # 錄製音頻
            audio_data = await self.record_audio()
            if len(audio_data) == 0:
                return {
                    "success": False,
                    "error": "無法錄製音頻"
                }

            # 轉錄音頻
            result = await self.transcribe_audio(audio_data)
            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            print(f"處理音頻時發生錯誤: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def save_audio(
        self,
        audio_data: np.ndarray,
        filename: str,
        sample_rate: int = 16000
    ):
        """
        保存音頻
        
        Args:
            audio_data: 音頻數據
            filename: 文件名
            sample_rate: 採樣率
        """
        try:
            sf.write(filename, audio_data, sample_rate)

        except Exception as e:
            print(f"保存音頻時發生錯誤: {str(e)}")

    def update_config(self, new_config: Dict):
        """
        更新配置
        
        Args:
            new_config: 新的配置參數
        """
        self.config.update(new_config)
        self._init_whisper()
        self._init_audio_device() 