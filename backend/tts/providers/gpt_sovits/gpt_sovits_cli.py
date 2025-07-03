"""GPT‑SoVITS 離線推論 CLI

用法：
$ python backend/tts/providers/gpt_sovits/cli.py \
    --text "哈囉，Podri" \
    --config backend/tts/models/gpt_sovits/configs/config.json \
    --checkpoint backend/tts/models/gpt_sovits/pretrained/model.pth \
    --ref_wav backend/tts/models/gpt_sovits/reference/ref.wav \
    --ref_text backend/tts/models/gpt_sovits/reference/ref.txt \
    --output /tmp/output.wav
"""
from __future__ import annotations
import argparse, os, json
import soundfile as sf
from pathlib import Path
# ► 官方 GPT-SoVITS 庫（請先 `pip install GPT-SoVITS` 或相依套件）
from GPT_SoVITS.inference_webui import (
    change_gpt_weights,
    change_sovits_weights,
    get_tts_wav,
)

LANG_MAP = {
    "zh": "中文",
    "en": "英文",
    "ja": "日文",
}

def synthesize(text: str,
               config: Path,
               checkpoint: Path,
               ref_wav: Path,
               ref_txt: Path,
               language: str,
               output: Path):
    """核心推論流程 (封裝官方 API)"""
    # 讀參考文本
    prompt_text = ref_txt.read_text(encoding="utf-8")
    # 切換權重
    change_gpt_weights(gpt_path=str(checkpoint))
    change_sovits_weights(sovits_path=str(checkpoint))
    # 呼叫生成
    res_iter = get_tts_wav(
        ref_wav_path=str(ref_wav),
        prompt_text=prompt_text,
        prompt_language=LANG_MAP[language],
        text=text,
        text_language=LANG_MAP[language],
        top_p=1.0,
        temperature=1.0,
    )
    # 取最後一段結果
    sampling_rate, audio = list(res_iter)[-1]
    sf.write(output, audio, sampling_rate)
    return output


def main():
    ap = argparse.ArgumentParser(description="GPT‑SoVITS 離線 CLI")
    ap.add_argument('--text', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--ref_wav', required=True)
    ap.add_argument('--ref_text', required=True)
    ap.add_argument('--language', default='zh', choices=['zh','en','ja'])
    ap.add_argument('--output', default='/tmp/output.wav')
    args = ap.parse_args()

    out = synthesize(
        text=args.text,
        config=Path(args.config),
        checkpoint=Path(args.checkpoint),
        ref_wav=Path(args.ref_wav),
        ref_txt=Path(args.ref_text),
        language=args.language,
        output=Path(args.output),
    )
    print(f"✔ 已生成: {out}")

if __name__ == '__main__':
    main()