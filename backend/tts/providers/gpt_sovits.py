"""
GPT-SoVITS Provider  (離線)
-------------------------------------------------------------
* 直接呼叫 `models/gpt_sovits/gpt_sovits_cli.py`
* 回傳 wav bytes 供 TTSManager / Streamlit 使用
* OOP 實作、繁體中文註解
"""
from __future__ import annotations
import subprocess, tempfile
from pathlib import Path
from typing import List


class GPTSoVITSProvider:
    """Podri 離線 TTS Provider (GPT‑SoVITS)"""

    # 修正路徑
    _CLI_PATH = Path(__file__).parent / "gpt_sovits/gpt_sovits_cli.py"
    _MODEL_DIR = Path(__file__).parent.parent / "models/gpt_sovits"

    def __init__(self):
        # ------ 基本路徑檢查 ------
        if not self._CLI_PATH.exists():
            raise FileNotFoundError(f"找不到 CLI 腳本: {self._CLI_PATH}")
        if not self._MODEL_DIR.exists():
            raise FileNotFoundError(f"找不到模型資料夾: {self._MODEL_DIR}")
        # 固定引用 reference 資料
        self.ref_wav = self._MODEL_DIR / "reference/ref.wav"
        self.ref_txt = self._MODEL_DIR / "reference/ref.txt"
        self.config = self._MODEL_DIR / "configs/config.json"
        self.checkpoint = self._MODEL_DIR / "pretrained/model.pth"
        if not self.ref_wav.exists() or not self.ref_txt.exists():
            raise FileNotFoundError("請在 models/gpt_sovits/reference/ 放置 ref.wav 與 ref.txt")
        if not self.config.exists() or not self.checkpoint.exists():
            raise FileNotFoundError("請在 models/gpt_sovits/ 放置 config.json 與 model.pth")

    # ---------- Provider API ----------
    @staticmethod
    def list_voices() -> List[str]:
        """目前僅一個聲線，可回傳多個自定義 id"""
        return ["gpt_sovits_default"]

    def synthesize(self, text: str, voice_id: str = "gpt_sovits_default") -> bytes:
        """合成語音 → 以 wav bytes 回傳"""
        # 產生暫存輸出檔
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
            out_path = Path(fp.name)

        # ------- 組合 CLI 參數 -------
        cmd = [
            "python3", str(self._CLI_PATH),
            "--text", text,
            "--config", str(self.config),
            "--checkpoint", str(self.checkpoint),
            "--ref_wav", str(self.ref_wav),
            "--ref_text", str(self.ref_txt),
            "--language", "zh",
            "--output", str(out_path)
        ]
        # 執行離線推論
        subprocess.run(cmd, check=True)
        # 讀取 wav bytes
        wav_bytes = out_path.read_bytes()
        return wav_bytes