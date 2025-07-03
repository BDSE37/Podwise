#!/usr/bin/env python3
"""
STT (Speech-to-Text) 服務類別
提供語音轉文字功能，支援多種語音識別模型
"""

import os
import logging
import asyncio
import time
import wave
import numpy as np
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 導入基礎服務
from ..core.base_service import BaseService, ServiceConfig, ServiceResponse

# 嘗試導入語音處理庫
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper 未安裝，將使用備援方案")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("Speech Recognition 未安裝")

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """音頻配置資料結構"""
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"
    chunk_size: int = 1024
    language: str = "zh-TW"
    model_size: str = "base"

@dataclass
class TranscriptionRequest:
    """轉錄請求資料結構"""
    audio_data: Union[bytes, str, Path]  # 音頻數據或文件路徑
    language: Optional[str] = None
    model_size: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TranscriptionResponse:
    """轉錄回應資料結構"""
    text: str
    confidence: float
    language: str
    model_used: str
    processing_time: float
    segments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class WhisperSTTEngine:
    """Whisper STT 引擎"""
    
    def __init__(self, model_size: str = "base"):
        """
        初始化 Whisper 引擎
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.logger = logging.getLogger("WhisperSTT")
        
        if WHISPER_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """載入 Whisper 模型"""
        try:
            self.logger.info(f"載入 Whisper 模型: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            self.logger.info("Whisper 模型載入成功")
        except Exception as e:
            self.logger.error(f"載入 Whisper 模型失敗: {str(e)}")
            self.model = None
    
    def transcribe(self, audio_path: Union[str, Path], language: str = "zh") -> Dict[str, Any]:
        """
        轉錄音頻文件
        
        Args:
            audio_path: 音頻文件路徑
            language: 語言代碼
            
        Returns:
            Dict: 轉錄結果
        """
        if not self.model:
            raise Exception("Whisper 模型未載入")
        
        try:
            # 執行轉錄
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe"
            )
            
            return {
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", language)
            }
            
        except Exception as e:
            self.logger.error(f"Whisper 轉錄失敗: {str(e)}")
            raise
    
    def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        轉錄音頻數據
        
        Args:
            audio_data: 音頻數據
            sample_rate: 採樣率
            
        Returns:
            Dict: 轉錄結果
        """
        if not self.model:
            raise Exception("Whisper 模型未載入")
        
        try:
            # 將音頻數據轉換為 numpy 數組
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 執行轉錄
            result = self.model.transcribe(
                audio_array,
                language="zh",
                task="transcribe"
            )
            
            return {
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "zh")
            }
            
        except Exception as e:
            self.logger.error(f"Whisper 音頻數據轉錄失敗: {str(e)}")
            raise

class SpeechRecognitionEngine:
    """Speech Recognition 引擎"""
    
    def __init__(self):
        """初始化 Speech Recognition 引擎"""
        self.recognizer = None
        self.logger = logging.getLogger("SpeechRecognition")
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
    
    def transcribe_audio_data(self, audio_data: bytes, language: str = "zh-TW") -> Dict[str, Any]:
        """
        轉錄音頻數據
        
        Args:
            audio_data: 音頻數據
            language: 語言代碼
            
        Returns:
            Dict: 轉錄結果
        """
        if not self.recognizer:
            raise Exception("Speech Recognition 未初始化")
        
        try:
            # 創建音頻數據對象
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            
            # 執行轉錄
            text = self.recognizer.recognize_google(
                audio,
                language=language
            )
            
            return {
                "text": text,
                "segments": [],
                "language": language
            }
            
        except Exception as e:
            self.logger.error(f"Speech Recognition 轉錄失敗: {str(e)}")
            raise

class STTService(BaseService):
    """STT 服務類別"""
    
    def __init__(self, config: ServiceConfig):
        """
        初始化 STT 服務
        
        Args:
            config: 服務配置
        """
        super().__init__(config)
        
        # 音頻配置
        self.audio_config = AudioConfig()
        
        # 初始化 STT 引擎
        self.whisper_engine = None
        self.speech_recognition_engine = None
        
        # 載入引擎
        self._load_engines()
        
        self.logger.info("STT 服務初始化完成")
    
    def _load_engines(self):
        """載入 STT 引擎"""
        # 載入 Whisper 引擎（本地化）
        if WHISPER_AVAILABLE:
            self.whisper_engine = WhisperSTTEngine(self.audio_config.model_size)
            self.logger.info("Whisper STT 引擎載入成功")
        else:
            self.logger.error("Whisper 不可用，請安裝 whisper 套件")
        
        # 移除 Speech Recognition 引擎（雲端依賴）
        # if SPEECH_RECOGNITION_AVAILABLE:
        #     self.speech_recognition_engine = SpeechRecognitionEngine()
        
        if not self.whisper_engine:
            self.logger.warning("沒有可用的本地 STT 引擎")
    
    async def initialize(self) -> bool:
        """
        初始化服務
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 確保音頻處理目錄存在
            audio_dirs = ["audio_cache", "audio_temp", "audio_output"]
            for dir_name in audio_dirs:
                Path(dir_name).mkdir(parents=True, exist_ok=True)
            
            # 測試引擎可用性（只檢查本地引擎）
            if not self.whisper_engine:
                self.logger.error("沒有可用的本地 STT 引擎")
                return False
            
            self.logger.info("本地 STT 服務初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"STT 服務初始化失敗: {str(e)}")
            return False
    
    async def process_request(self, request_data: Any) -> ServiceResponse:
        """
        處理請求
        
        Args:
            request_data: 請求數據
            
        Returns:
            ServiceResponse: 服務回應
        """
        start_time = time.time()
        
        try:
            # 解析請求
            if isinstance(request_data, dict):
                request = TranscriptionRequest(**request_data)
            elif isinstance(request_data, TranscriptionRequest):
                request = request_data
            else:
                raise ValueError("無效的請求格式")
            
            # 執行轉錄
            response = await self.transcribe_audio(request)
            
            processing_time = time.time() - start_time
            
            return self._create_response(
                success=True,
                data=response,
                message="音頻轉錄成功",
                processing_time=processing_time,
                metadata={"model_used": response.model_used}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"處理請求失敗: {str(e)}")
            
            return self._create_response(
                success=False,
                data=None,
                message=f"處理失敗: {str(e)}",
                processing_time=processing_time
            )
    
    async def transcribe_audio(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """
        轉錄音頻
        
        Args:
            request: 轉錄請求
            
        Returns:
            TranscriptionResponse: 轉錄回應
        """
        start_time = time.time()
        
        # 確定語言和模型
        language = request.language or self.audio_config.language
        model_size = request.model_size or self.audio_config.model_size
        
        try:
            # 處理音頻數據
            if isinstance(request.audio_data, (str, Path)):
                # 文件路徑
                audio_path = Path(request.audio_data)
                if not audio_path.exists():
                    raise FileNotFoundError(f"音頻文件不存在: {audio_path}")
                
                result = await self._transcribe_file(audio_path, language)
                
            elif isinstance(request.audio_data, bytes):
                # 音頻數據
                result = await self._transcribe_data(request.audio_data, language)
                
            else:
                raise ValueError("不支援的音頻數據格式")
            
            processing_time = time.time() - start_time
            
            # 計算信心值
            confidence = self._calculate_confidence(result["text"], result.get("segments", []))
            
            return TranscriptionResponse(
                text=result["text"],
                confidence=confidence,
                language=result.get("language", language),
                model_used=result.get("model_used", "unknown"),
                processing_time=processing_time,
                segments=result.get("segments"),
                metadata={
                    "model_size": model_size,
                    "sample_rate": self.audio_config.sample_rate,
                    "channels": self.audio_config.channels
                }
            )
            
        except Exception as e:
            self.logger.error(f"音頻轉錄失敗: {str(e)}")
            raise
    
    async def _transcribe_file(self, audio_path: Path, language: str) -> Dict[str, Any]:
        """
        轉錄音頻文件
        
        Args:
            audio_path: 音頻文件路徑
            language: 語言代碼
            
        Returns:
            Dict: 轉錄結果
        """
        # 優先使用 Whisper
        if self.whisper_engine:
            try:
                result = self.whisper_engine.transcribe(audio_path, language)
                result["model_used"] = "whisper"
                return result
            except Exception as e:
                self.logger.warning(f"Whisper 轉錄失敗，嘗試備援方案: {str(e)}")
        
        # 備援方案：Speech Recognition
        if self.speech_recognition_engine:
            try:
                # 讀取音頻文件
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                
                result = self.speech_recognition_engine.transcribe_audio_data(audio_data, language)
                result["model_used"] = "speech_recognition"
                return result
                
            except Exception as e:
                self.logger.error(f"Speech Recognition 轉錄失敗: {str(e)}")
        
        raise Exception("所有 STT 引擎都無法使用")
    
    async def _transcribe_data(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """
        轉錄音頻數據
        
        Args:
            audio_data: 音頻數據
            language: 語言代碼
            
        Returns:
            Dict: 轉錄結果
        """
        try:
            # 只使用本地 Whisper 引擎
            if self.whisper_engine:
                result = self.whisper_engine.transcribe_audio_data(audio_data)
                result["model_used"] = "whisper"
                return result
            else:
                raise Exception("沒有可用的本地 STT 引擎")
                
        except Exception as e:
            self.logger.error(f"音頻數據轉錄失敗: {str(e)}")
            raise
    
    def _calculate_confidence(self, text: str, segments: List[Dict[str, Any]]) -> float:
        """
        計算信心值
        
        Args:
            text: 轉錄文本
            segments: 音頻片段
            
        Returns:
            float: 信心值 (0.0-1.0)
        """
        if not text:
            return 0.0
        
        # 基於文本長度的基礎信心值
        base_confidence = min(1.0, len(text) / 50)
        
        # 如果有片段信息，計算平均信心值
        if segments:
            segment_confidences = []
            for segment in segments:
                if "avg_logprob" in segment:
                    # Whisper 的 log probability 轉換為信心值
                    confidence = np.exp(segment["avg_logprob"])
                    segment_confidences.append(confidence)
            
            if segment_confidences:
                avg_confidence = np.mean(segment_confidences)
                return (base_confidence + avg_confidence) / 2
        
        return base_confidence
    
    async def get_supported_languages(self) -> List[str]:
        """
        獲取支援的語言列表
        
        Returns:
            List: 支援的語言列表
        """
        return [
            "zh-TW", "zh-CN", "en-US", "en-GB", "ja-JP", "ko-KR",
            "fr-FR", "de-DE", "es-ES", "it-IT", "pt-BR", "ru-RU"
        ]
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        獲取可用模型列表
        
        Returns:
            List: 可用模型列表
        """
        models = []
        
        if self.whisper_engine:
            models.append({
                "name": "whisper",
                "model_size": self.audio_config.model_size,
                "available": True
            })
        
        if self.speech_recognition_engine:
            models.append({
                "name": "speech_recognition",
                "model_size": "google",
                "available": True
            })
        
        return models
    
    async def cleanup(self) -> bool:
        """
        清理資源
        
        Returns:
            bool: 清理是否成功
        """
        try:
            # 清理臨時文件
            temp_dir = Path("audio_temp")
            if temp_dir.exists():
                for temp_file in temp_dir.glob("*"):
                    try:
                        temp_file.unlink()
                    except Exception as e:
                        self.logger.warning(f"清理臨時文件失敗: {str(e)}")
            
            self.logger.info("STT 服務資源清理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"STT 服務資源清理失敗: {str(e)}")
            return False

# 便捷函數
async def create_stt_service(host: str = "0.0.0.0", port: int = 8001) -> STTService:
    """
    創建 STT 服務實例
    
    Args:
        host: 服務主機
        port: 服務端口
        
    Returns:
        STTService: STT 服務實例
    """
    config = ServiceConfig(
        service_name="STT Service",
        service_version="1.0.0",
        host=host,
        port=port,
        debug=os.getenv("DEBUG", "False").lower() == "true",
        timeout=int(os.getenv("STT_TIMEOUT", "60"))
    )
    
    return STTService(config) 