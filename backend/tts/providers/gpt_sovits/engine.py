"""SoVITSInferenceEngine
=======================
將官方 `inference_webui.py` 精簡為**離線推論引擎**。
僅保留：
  • 模型初始化 (`_load_models`)  
  • 語音合成 (`synthesize`)
供 Provider / CLI / 其他服務呼叫。

依賴：
```bash
pip install torch soundfile librosa transformers peft GPT-SoVITS
```
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
import torch
import os
import sys
import pathlib

# 找到 engine.py 所在的真正路徑（例如 backend/tts/providers/gpt_sovits）
CURRENT_FILE = pathlib.Path(__file__).resolve()

# 往上找直到遇到 models/gpt_sovits 為止
def find_gpt_sovits_dir(start: pathlib.Path) -> pathlib.Path:
    for parent in start.parents:
        gpt_dir = parent / "models" / "gpt_sovits"
        if gpt_dir.exists():
            return gpt_dir
    raise FileNotFoundError("❌ 找不到 models/gpt_sovits 資料夾")

GPT_SOVITS_DIR = find_gpt_sovits_dir(CURRENT_FILE)
sys.path.insert(0, str(GPT_SOVITS_DIR))

# 驗證是否成功
print("✅ GPT_SOVITS_DIR =", GPT_SOVITS_DIR)
print("📁 內容：", os.listdir(GPT_SOVITS_DIR))

# 匯入
from inference_webui import get_tts_wav



# === CLI 用法 ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    wav_data = get_tts_wav(args.text)  # ❗️這裡如果還需要 config 請補參數
    with open(args.out, "wb") as f:
        f.write(wav_data)

    print("✅ 音檔輸出完成:", args.out)

# wav_bytes = get_tts_wav(text="Podri TTS 測試", ...其他參數...)


__all__ = ["SoVITSInferenceEngine"]


class SoVITSInferenceEngine:
    """封裝 GPT‑SoVITS 推論流程。"""

    def __init__(self,
                 model_dir: Path | str,
                 device: str | None = None,
                 half: bool = True):
        self.model_dir = Path(model_dir)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.half = half and self.device == "cuda"

        # --- 權重路徑 ---
        self.cfg_path = self.model_dir / "configs/config.json"
        self.ckpt_path = self.model_dir / "pretrained/model.pth"
        self.ref_wav = self.model_dir / "reference/ref.wav"
        self.ref_txt = self.model_dir / "reference/ref.txt"
        for p in (self.cfg_path, self.ckpt_path, self.ref_wav, self.ref_txt):
            if not p.exists():
                raise FileNotFoundError(f"缺少檔案: {p}")

        # --- 模型初始化 ---
        self._load_models()

    # --------------------------------------------------
    def _load_models(self) -> None:
        """載入 GPT 與 SoVITS 權重。"""
        # 實際 change_weights 會把模型存到全域
        change_gpt_weights(str(self.ckpt_path))
        # 預設語言重設為中文
        for _ in change_sovits_weights(str(self.ckpt_path), "中文", "中文"):
            pass  # 其為 generator；需完全迭代以完成載入

    # --------------------------------------------------
    def synthesize(self,
                   text: str,
                   text_lang: str = "中文",
                   top_p: float = 0.6,
                   temperature: float = 0.6) -> Tuple[int, bytes]:
        """離線語音合成

        Args:
            text: 目標句子
            text_lang: 語種（中文/英文/日文…）
            top_p, temperature: 取樣參數
        Returns:
            (sr, wav_bytes)
        """
        # 呼叫官方 get_tts_wav (yield generator) 取得最後結果
        out_iter = get_tts_wav(
            str(self.ref_wav),                # 參考音頻
            self.ref_txt.read_text(),         # 參考文字
            text_lang,                        # 參考語言
            text,
            text_lang,
            top_p=top_p,
            temperature=temperature,
        )
        sr, audio_np = list(out_iter)[-1]  # (sr, np.int16)
        wav_bytes = self._numpy_to_bytes(audio_np, sr)
        return sr, wav_bytes

    # --------------------------------------------------
    @staticmethod
    def _numpy_to_bytes(audio: np.ndarray, sr: int) -> bytes:
        """將 numpy int16 轉 wav bytes。"""
        import io
        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    # --------------------------------------------------
    # 可再擴充 batch_synthesize、change_voice 等方法


# ---- CLI 測試 ----
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="SoVITS 引擎測試")
    ap.add_argument("--model_dir", default="backend/tts/models/gpt_sovits")
    ap.add_argument("--text", default="哈囉，Podri OOP 測試！")
    ap.add_argument("--out", default="demo_engine.wav")
    args = ap.parse_args()

    eng = SoVITSInferenceEngine(Path(args.model_dir))
    sr, wav_b = eng.synthesize(args.text)
    Path(args.out).write_bytes(wav_b)
    print(f"✔ 已輸出 {args.out} (sr={sr})")
