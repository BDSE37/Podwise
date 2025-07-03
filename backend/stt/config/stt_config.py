"""
STT 配置檔案
"""

STT_CONFIG = {
    "whisper_model": "medium",  # Whisper 模型名稱 (medium 提供更好的識別效果)
    "model": {
        "name": "medium",
        "device": "cpu",
        "compute_type": "float32"
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "chunk_size": 1024,
        "format": "wav"
    },
    "processing": {
        "language": "zh",
        "task": "transcribe",
        "verbose": False,
        "temperature": 0.0
    },
    "output": {
        "save_audio": True,
        "output_dir": "/tmp/stt_output",
        "audio_format": "wav"
    },
    "vad": {
        "enabled": True,
        "threshold": 0.5,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": 30
    }
} 