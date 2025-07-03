# -*- coding: utf-8 -*-
"""
Podri TTS Provider － Qwen2.5-Taiwan SoVITS
將小智 (py-xiaozhi) 的列印 CLI 封裝成標準介面，供 Podri 其餘模組呼叫。
"""
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import List

# -------------------------------------------------------------------
# ★ 可依實際環境調整 ★
# -------------------------------------------------------------------
_XIAOZHI_CLI = Path(__file__).parent.parent / "qwen_tts.py"    # 小智 CLI 執行檔
_MODEL_BASE  = Path(__file__).parent.parent / "models"         # SoVITS 模型資料夾
_VOICE_MAP = {                                                 # 語音 ID ↔︎ 子資料夾
    "podri_tw_female": "tw_female",
    "podri_tw_male"  : "tw_male",
}
# -------------------------------------------------------------------


class Qwen25TWProvider:
    """Podri 專用 Qwen2.5-TW 語音提供者"""

    # ------------------------------------------------------------ #
    #  公開介面
    # ------------------------------------------------------------ #
    @staticmethod
    def list_voices() -> List[str]:
        """回傳此 Provider 支援的語音清單（voice_id）"""
        return list(_VOICE_MAP.keys())

    def synthesize(self, text: str, voice_id: str) -> str:
        """
        將文字轉音（Base64 WAV），供前端直接播放。

        Args:
            text (str)     : 要朗讀的文字
            voice_id (str) : 語音 ID，需存在於 list_voices()

        Returns:
            str: base64 編碼後的 wav 聲音檔
        """
        if voice_id not in _VOICE_MAP:
            raise ValueError(f"未知的 voice_id: {voice_id}")

        # 取得模型路徑
        model_path = _MODEL_BASE / _VOICE_MAP[voice_id]
        if not model_path.exists():
            raise FileNotFoundError(f"模型資料夾不存在: {model_path}")

        # 使用系統暫存檔存放 wav
        tmp_wav = Path(tempfile.gettempdir()) / f"podri_{voice_id}.wav"

        # 執行 CLI（如參數不同請自行調整）
        cmd = [
            "python3", str(_XIAOZHI_CLI),
            "--text", text,
            "--speaker", _VOICE_MAP[voice_id],
            "--model_path", str(model_path),
            "--output", str(tmp_wav),
        ]
        subprocess.run(cmd, check=True)

        # 讀檔並轉 base64
        wav_bytes = tmp_wav.read_bytes()
        return base64.b64encode(wav_bytes).decode("utf-8")
