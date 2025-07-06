"""
STTService - Whisper 語音轉文字服務
OOP 封裝，支援模組化調用，符合 Google Clean Code
"""

import logging
import tempfile
from typing import Dict, Any, Optional
from faster_whisper import WhisperModel

class STTService:
    """
    Whisper 語音轉文字服務
    封裝模型載入、音訊處理、轉錄邏輯，支援 OOP 調用
    """
    def __init__(self, model_name: str = "medium", device: str = "cpu", compute_type: str = "float32") -> None:
        """
        初始化 STT 服務
        Args:
            model_name: Whisper 模型名稱
            device: 運算裝置 (cpu/cuda)
            compute_type: 運算型態 (float32/float16)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self._load_model()

    def _load_model(self) -> None:
        """載入 Whisper 模型"""
        try:
            self.logger.info(f"正在載入 Whisper 模型: {self.model_name} ({self.device}, {self.compute_type})...")
            self.model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
            self.logger.info("✅ Whisper 模型載入成功")
        except Exception as e:
            self.logger.error(f"❌ Whisper 模型載入失敗: {e}")
            raise

    def transcribe(self, audio_bytes: bytes, language: str = "zh") -> Dict[str, Any]:
        """
        語音轉文字
        Args:
            audio_bytes: 音訊檔案位元組
            language: 語言代碼 (預設 zh)
        Returns:
            轉錄結果 dict
        """
        if not self.model:
            raise RuntimeError("STT 模型尚未載入")
        
        temp_file_path = None
        try:
            # 將音訊 bytes 寫入臨時檔
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # 進行轉錄
            segments, info = self.model.transcribe(
                temp_file_path,
                language=language,
                task="transcribe"
            )
            
            # 收集轉錄結果
            text_parts = []
            segments_list = []
            for segment in segments:
                text_parts.append(segment.text)
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": segment.words if hasattr(segment, 'words') else []
                })
            full_text = " ".join(text_parts).strip()
            result = {
                "text": full_text,
                "confidence": 0.95,  # Faster Whisper 不直接提供 confidence
                "language": info.language,
                "model_used": self.model_name,
                "processing_time": info.duration if hasattr(info, 'duration') else 0,
                "segments": segments_list,
                "language_probability": info.language_probability if hasattr(info, 'language_probability') else 0
            }
            return result
        except Exception as e:
            self.logger.error(f"轉錄失敗: {e}")
            raise
        finally:
            # 清理臨時檔案
            if temp_file_path:
                import os
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

    def close(self) -> None:
        """釋放資源（如有）"""
        self.model = None
        self.logger.info("STTService 已釋放資源") 